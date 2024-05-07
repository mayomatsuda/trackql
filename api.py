import requests
import base64
import webbrowser
from flask import Flask, redirect, request, make_response, render_template, g
from flask_cors import CORS
import uuid
import sqlite3
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)

base = 'https://api.spotify.com/v1'

client_id = os.getenv('CLIENT_ID')
client_secret = os.getenv('CLIENT_SECRET')

global tkn
tkn = None

global generated
generated = False

global LIMIT
LIMIT = -1

app.db = sqlite3.connect('file:memdb1?mode=memory&cache=shared', uri=True, check_same_thread=False)

def get_db():
    """Open a new database connection if there is none yet for the
    current application context."""
    if 'db' not in g:
        g.db = sqlite3.connect(':memory:')
    return g.db

@app.route('/')
def main():
    global tkn
    if tkn == None:
        return redirect('/login')
    return render_template('home.html')

@app.route('/login')
def login():
    # get user auth
    scope = "playlist-read-private"
    redirect_uri = "http://localhost:5000/callback"
    response = make_response(redirect(f'https://accounts.spotify.com/authorize?client_id={client_id}&response_type=code&redirect_uri={redirect_uri}&scope={scope}'))
    return response

@app.route('/build', methods=['GET'])
def build():
    global generated

    if not generated:
        global tkn
        global LIMIT

        # get user info
        headers = {
            'Authorization': f'Bearer {tkn}'
        }
        url = f'{base}/me/playlists'
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            playlist_data = response.json()
        else:
            return("Failed to retrieve user playlists, status code:", response.status_code)

        cur = app.db.cursor()

        cur.execute(f'CREATE TABLE name(id, name);')

        playlist_names = {}
        c = 0

        for playlist_item in playlist_data["items"]:
            cur.execute(f'CREATE TABLE t_{playlist_item["id"]}(name, artist, album);')
            cur.execute(f'INSERT INTO name VALUES (\'{playlist_item["id"]}\', \'{playlist_item["name"]}\');')

            url_tracks = f'{base}/playlists/{playlist_item["id"]}/tracks'
            response_tracks = requests.get(url_tracks, headers=headers)

            if response.status_code == 200:
                playlist_tracks = response_tracks.json()
            else:
                return("Failed to retrieve playlist items, status code:", response.status_code)
            
            for track in playlist_tracks["items"]:
                try:
                    track_name = track["track"]["name"].replace("'", "''")
                    track_artist = track["track"]["artists"][0]["name"].replace("'", "''")
                    track_album = track["track"]["album"]["name"].replace("'", "''")

                    cur.execute(f'INSERT INTO t_{playlist_item["id"]} VALUES (\'{track_name}\', \'{track_artist}\', \'{track_album}\');')
                except Exception as e:
                    print(e)

            playlist_names[playlist_item["name"]] = "t_" + playlist_item["id"]
            c += 1
            if c == LIMIT:
                break
        
        generated = True

    return playlist_names

@app.route('/query', methods=['POST'])
def query():
    data = request.json
    cur = app.db.cursor()
    cur.execute("SELECT name FROM sqlite_master WHERE type='table';")
    try:
        cur.execute(data["query"])
        r = cur.fetchall()
        return r
    except Exception as e:
        return f'Error: {e}'

@app.route('/callback')
def callback():
    global tkn
    code = request.args.get('code')
    client = client_id + ":" + client_secret

    # get token
    headers_tkn = {
        "Content-Type": "application/x-www-form-urlencoded",
        'Authorization': 'Basic ' + base64.b64encode(client.encode()).decode()
    }
    data_tkn = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": "http://localhost:5000/callback"
    }
    url_tkn = "https://accounts.spotify.com/api/token"

    response_tkn = requests.post(url_tkn, headers=headers_tkn, data=data_tkn)
    if response_tkn.status_code == 200:
        token_data = response_tkn.json()
        tkn = token_data['access_token']
        return redirect('/')
    else:
        return("Failed to retrieve token, status code:", response_tkn.status_code)

if __name__ == '__main__':
    app.run(debug=True)