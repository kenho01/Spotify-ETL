import sqlalchemy
import pandas as pd
from sqlalchemy.orm import sessionmaker
import requests
from flask import Flask, request, redirect, jsonify
from requests.auth import HTTPBasicAuth
import json
import string
import random
import datetime
import os
from dotenv import load_dotenv
from datetime import timedelta
from urllib.parse import urlencode
import sqlite3
import base64
import string
import base64

DATABASE_LOCATION = "sqlite://spotify_tracks.sqlite"
REDIRECT_URI = "http://localhost:8888/callback"
AUTH_URL = "https://accounts.spotify.com/authorize"


def configure():
    load_dotenv()

app = Flask(__name__)

client_id = 'CLIENT_ID'
client_secret = 'CLIENT_SECRET'
redirect_uri = 'http://localhost:8888/callback'


@app.route('/login')
def login():
    configure()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    state = random.randint(0,16)
    scope = 'user-read-recently-played'
    
    query_params = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': redirect_uri,
        'state': state
    }
    url = 'https://accounts.spotify.com/authorize?' + '&'.join([f'{key}={value}' for key, value in query_params.items()])
    print(url)
    return redirect(url)

@app.route('/callback')
def callback():
    code = request.args.get('code')
    state = request.args.get('state')
    print(code)
    print(state)

    if state is None:
        return redirect('/#?error=state_mismatch')
    
    auth_options = {
        'url': 'https://accounts.spotify.com/api/token',
        'data': {
            'code': code,
            'redirect_uri': redirect_uri,
            'grant_type': 'authorization_code'
        },
        'headers': {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Authorization': 'Basic ' + base64.b64encode(f'{client_id}:{client_secret}'.encode()).decode()
        }
    }
    
    response = requests.post(auth_options['url'], data=auth_options['data'], headers=auth_options['headers'])
    token_info = response.json()
    
    return jsonify(token_info)

if __name__ == '__main__':
    app.run(port=8888)
