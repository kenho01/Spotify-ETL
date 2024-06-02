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
REDIRECT_URI = 'http://localhost:8888/callback'


def configure():
    load_dotenv()

def getAuthorization():
    configure()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    state = random.randint(0,16)
    scope = 'user-read-recently-played'
    
    query_params = {
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': REDIRECT_URI,
        'state': state
    }
    url = AUTH_URL + '?' + urlencode(query_params)
    print(url)
    return redirect(url)

def getToken():
    configure()
    client_id = os.getenv('CLIENT_ID')
    client_secret = os.getenv('CLIENT_SECRET')
    auth_options = {
        'url' : 'https://accounts.spotify.com/api/token',
        'data' : {
        'code' : os.getenv('CODE'),
        'redirect_uri' : REDIRECT_URI,
        'grant_type' : 'authorization_code'
    },
        'headers' : {
            'Content-Type' : 'application/x-www-form-urlencoded',
            'Authorization' : 'Basic ' + base64.b64encode((client_id + ':' + client_secret).encode()).decode('utf-8')
        }
    }
    response = requests.post(auth_options['url'], data=auth_options['data'], headers=auth_options['headers'])
    response_data = response.json()
    print("Response data" + str(response_data))

def main():
    getAuthorization()
    getToken()

if __name__ == '__main__':
    main()
    
