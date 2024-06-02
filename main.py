import urllib.parse
from flask import Flask, redirect, request, jsonify, session
from datetime import datetime, timedelta
import requests
import os
from dotenv import load_dotenv

import pandas as pd
import sqlalchemy
from sqlalchemy.orm import sessionmaker
import sqlite3

app = Flask(__name__)
app.secret_key = 'Sa2BKQUhHyJ0lNYcBs7FZgU3VVMj7hVZ'
REDIRECT_URI = 'http://localhost:5000/callback'
AUTH_URL = 'https://accounts.spotify.com/authorize'
TOKEN_URL = 'https://accounts.spotify.com/api/token'
API_BASE_URL = 'https://api.spotify.com/v1/'
DATABASE_LOCATION = "sqlite:///history.sqlite"

def configure():
    load_dotenv()

def dataValidity(df: pd.DataFrame) -> bool:
    if df.empty:
        print("Dataframe is empty")
        return False
    if pd.Series(df['played_at']).is_unique:
        pass
    else:
        raise Exception("Primary key violation")
    if df.isnull().values.any():
        raise Exception("Null values exist")
    yesterday = datetime.now() - timedelta(days=1)
    yesterday = yesterday.replace(hour=0, minute=0, second=0, microsecond=0)
    timestamps = df["timestamp"].tolist()
    for timestamp in timestamps:
        if datetime.strptime(timestamp, "%Y-%m-%d") != yesterday:
            raise Exception("There are songs that are not within the past day")
    return True

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
        # 'show_dialog' : True
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
    yesterday = datetime.now() - timedelta(days=1)
    yesterday_unix = int(yesterday.timestamp()) * 1000
    if 'access_token' not in session:
        return redirect('login')
    if datetime.now().timestamp() > session['expires_at']:
        return redirect('/refresh-token')
    headers = {
        'Authorization' : f"Bearer {session['access_token']}"
    }

    url = f'{API_BASE_URL}me/player/recently-played?after={yesterday_unix}'
    response = requests.get(url, headers=headers)
    recentlyplayed = response.json()

    # Extracting from json
    data = recentlyplayed
    song_names = []
    artist_names = []
    played_at_list = []
    timestamps = []

    for song in data["items"]:
        song_names.append(song["track"]["name"])
        artist_names.append(song["track"]["album"]["artists"][0]["name"])
        played_at_list.append(song["played_at"])
        timestamps.append(song["played_at"][0:10])

    song_dict = {
        "song_name" : song_names,
        "artist_name" : artist_names,
        "played_at" : played_at_list,
        "timestamp" : timestamps
    }

    song_df = pd.DataFrame(song_dict, columns=["song_name", "artist_name", "played_at", "timestamp"])
    
    if dataValidity(song_df):
        print("Data received is valid")
    else:
        print("Data is invalid")

    engine = sqlalchemy.create_engine(DATABASE_LOCATION)
    connection = sqlite3.connect("history.sqlite")
    cursor = connection.cursor()

    sql_query = """
    CREATE TABLE IF NOT EXISTS history(
        song_name VARCHAR(200),
        artist_name VARCHAR(200),
        played_at VARCHAR(200),
        timestamp VARCHAR(200),
        CONSTRAINT primary_key_constraint PRIMARY KEY (played_at)
    )
    """
    cursor.execute(sql_query)
    print("Database initialized")

    try:
        song_df.to_sql("history", engine, index=False, if_exists="append")
    except:
        print("Data already exists")
    connection.close()
    print("Closing database")
    
    return jsonify(recentlyplayed)

@app.route('/refresh-token')
def refresh_token():
    configure()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    if 'refresh_token' not in session:
        return redirect('/login')
    if datetime.now().timestamp() > session['expires_at']:
        req_body = {
            'grant_type' : 'refresh_token',
            'refresh_token' : session['refresh_token'],
            'client_id' : client_id,
            'client_secret' : client_secret
        }
    response = requests.post(TOKEN_URL, data=req_body)
    new_token_info = response.json()
    session['access_token']  = new_token_info['access_token']
    session['expires_at'] = datetime.now().timestamp() + new_token_info['expires_in']

    return redirect('/recentlyplayed')

if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)