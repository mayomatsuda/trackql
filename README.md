# trackql
Query your Spotify playlists using SQLite.

## Setup
Set up a Spotify API account at https://developer.spotify.com/documentation/web-api. In a .env file:

```
CLIENT_ID=<client id>
CLIENT_SECRET=<client secret>
```

Add `http://localhost:5000/callback` to the callback URLs on your Spotify dev dashboard.

## Usage
Run the Flask backend and go to `localhost:5000/`. It might take a minute for your playlists to load. The right column of the first table are the names of the SQL tables that correspond to each playlist in the left column. You can write SQLite queries in the input box using these tables.

htps://fakeurldfsjnk.com/
https://fakeurldfsjnk.com/