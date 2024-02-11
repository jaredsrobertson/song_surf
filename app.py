import requests
from flask import Flask, request, Response, jsonify
from flask_cors import CORS
import spotipy
from spotipy.oauth2 import SpotifyClientCredentials
from dotenv import dotenv_values
import yt_dlp

app = Flask(__name__)
CORS(app)

# Load environment variables from a .env file
CONFIG = dotenv_values(".env")

SPOTIFY_CLIENT_ID = CONFIG.get("SPOTIFY_CLIENT_ID")
SPOTIFY_CLIENT_SECRET = CONFIG.get("SPOTIFY_CLIENT_SECRET")

# Initialize Spotipy with your Spotify API credentials
sp = spotipy.Spotify(
    client_credentials_manager=SpotifyClientCredentials(
        client_id=SPOTIFY_CLIENT_ID, client_secret=SPOTIFY_CLIENT_SECRET
    )
)


@app.route("/search", methods=["POST"])
def search():
    data = request.json
    search_query = data.get("search_term")
    if not search_query:
        return jsonify({"error": "Missing search term"}), 400

    # Use Spotipy to search for the track on Spotify
    results = sp.search(q=search_query, type="track", limit=1)
    if not results["tracks"]["items"]:
        return jsonify({"error": "No results found on Spotify"}), 404

    track = results["tracks"]["items"][0]
    track_name = track["name"]
    # artist_id = track["artists"][0]["id"]  # Fetch the artist's ID
    # artist_info = sp.artist(artist_id)  # Fetch the artist's information using their ID
    artist_name = track["artists"][0]["name"]
    album_name = track["album"]["name"]
    release_year = track["album"]["release_date"][
        :4
    ]  # Assuming release_date is in the format YYYY-MM-DD

    # Select the best quality album art
    album_art_url = (
        track["album"]["images"][0]["url"] if track["album"]["images"] else None
    )

    youtube_search_query = f"{track_name} {artist_name}"

    # Use yt_dlp to search for the YouTube video and get the best audio URL
    ydl_opts = {
        "format": "bestaudio",
        "quiet": True,
        "no_warnings": True,
        "default_search": "ytsearch1:",
        "noplaylist": True,
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        info_dict = ydl.extract_info(youtube_search_query, download=False)
        video_url = info_dict["entries"][0]["url"] if info_dict["entries"] else None

    return jsonify(
        {
            "audio_url": video_url,
            "track_name": track_name,
            "artist_name": artist_name,
            "album_name": album_name,
            "release_year": release_year,
            "album_art_url": album_art_url,
        }
    )


@app.route("/stream")
def stream_audio():
    """
    Proxies the audio stream from YouTube to the client.
    This endpoint expects a 'url' query parameter with the direct URL to the audio stream.
    """
    video_url = request.args.get("url")
    if not video_url:
        return "Missing URL", 400

    # Fetch the audio content from the URL and stream it back to the client
    req = requests.get(video_url, stream=True)
    return Response(
        req.iter_content(chunk_size=10 * 1024), content_type=req.headers["Content-Type"]
    )


if __name__ == "__main__":
    # Run the Flask app
    app.run(debug=True)
