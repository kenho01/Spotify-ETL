import urllib.parse
from flask import Flask, redirect, request, jsonify, session
from datetime import datetime
import requests
import os
from dotenv import load_dotenv

app = Flask(__name__)
app.secret_key = 'Sa2BKQUhHyJ0lNYcBs7FZgU3VVMj7hVZ'
REDIRECT_URI = 'http://localhost:5000/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'

def configure():
    load_dotenv()

@app.route('/')
def index():
    return "Hi! <a href='/login'> Login with Spotify </a>"

@app.route('/login')
def login():
    configure()
    client_id = os.getenv('CLIENT_ID')
    scope = 'user-read-recently-played'
    params = {
        'client_id' : client_id,
        'response_type' : 'code',
        'scope' : scope,
        'redirect_uri' : REDIRECT_URI,
        # For debugging, force user to login everytime
        'show_dialog' : True
    }
    auth_url = f"{AUTH_URL}?{urllib.parse.urlencode(params)}"
    return redirect(auth_url)

@app.route('/callback')
def callback():
    configure()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    if 'error' in request.args:
        return jsonify({"error" : request.args['error']})
    if 'code' in request.args:
        req_body = {
            'code' : request.args['code'],
            'grant_type' : 'authorization_code',
            'redirect_uri' : REDIRECT_URI,
            'client_id' : client_id,
            'client_secret' : client_secret
        }
    response = requests.post(TOKEN_URL, data=req_body)
    token_info = response.json()

    session['access_token'] = token_info['access_token']
    session['refresh_token'] = token_info['refresh_token'] 
    session['expires_at'] = datetime.now().timestamp() + token_info['expires_in']

    return redirect('/recentlyplayed')

@app.route('/recentlyplayed')
def recentlyplayed():
    if 'access_token' not in session:
        return redirect('login')
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    headers = {
        'Authorization' : f"Bearer {session['access_token']}"
    }

    response = requests.get(API_BASE_URL + 'me/player/recently-played', headers=headers)
    recentlyplayed = response.json()
    return jsonify(recentlyplayed)

@app.route('/refresh-token')
def refresh_token():
    if 'refresh_token' not in session:
        return redirect('/login')
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type' : 'refresh_token',
            'refresh_token' : session['refresh_token'],
            'client_id' : CLIENT_ID,
            'client_secret' : CLIENT_SECRET
        }
    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()
    session['access_token']  = new_token_info['access_token']
    session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

    return redirect('/recentlyplayed')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)