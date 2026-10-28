import re
import traceback

import spotipy
from spotipy.oauth2 import SpotifyClientCredentials

from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET
from logs import logger

from .ytdlp import YoutubeSearch


class SpotifyAPI:
    def __init__(self):
        self.regex = r"^(https:\/\/open.spotify.com\/)(.*)$"
        self.client_id = SPOTIFY_CLIENT_ID
        self.client_secret = SPOTIFY_CLIENT_SECRET
        if SPOTIFY_CLIENT_ID and SPOTIFY_CLIENT_SECRET:
            self.client_credentials_manager = SpotifyClientCredentials(
                self.client_id, self.client_secret
            )
            self.spotify = spotipy.Spotify(
                client_credentials_manager=self.client_credentials_manager
            )
        else:
            self.spotify = None

    async def valid(self, link: str):
        if re.search(self.regex, link):
            return True
        else:
            return False

    async def track(self, link: str):
        try:
            track = self.spotify.track(link)
            artist_names = [artist["name"] for artist in track["artists"]]
            album_name = track["album"]["name"]
            release_date = track["album"]["release_date"]
            track_duration = track["duration_ms"] / 1000

            yt_results = YoutubeSearch(
                f"{track['name']} - {', '.join(artist_names)}", max_results=1
            )
            await yt_results.fetch_results()

            return {
                "title": yt_results.get_title(),
                "file_path": yt_results.get_link(),
                "vidid": yt_results.get_id(),
                "duration": yt_results.get_duration(),
                "thumbs": yt_results.get_thumbnail(),
                "uploader": artist_names,
                "album_name": album_name,
                "release_date": release_date,
                "track_duration": track_duration,
                "url": track["id"],
            }
        except Exception:
            logger.error(f"Error in track: {traceback.format_exc()}")
            return None

    async def playlist(self, link: str):
        try:
            playlist = self.spotify.playlist(link)
            tracks = []
            for item in playlist["tracks"]["items"]:
                track = item["track"]
                artist_names = [artist["name"] for artist in track["artists"]]
                album_name = track["album"]["name"]
                release_date = track["album"]["release_date"]
                track_duration = track["duration_ms"] / 1000
                track_info = {
                    "title": track["name"],
                    "artists": artist_names,
                    "album_name": album_name,
                    "release_date": release_date,
                    "track_duration": track_duration,
                    "track_id": track["id"],
                }
                tracks.append(track_info)
            return tracks
        except Exception:
            logger.error(f"Error in playlist: {traceback.format_exc()}")
            return None

    async def album(self, link: str):
        try:
            album = self.spotify.album(link)
            tracks = []
            for item in album["tracks"]["items"]:
                artist_names = [artist["name"] for artist in item["artists"]]
                album_name = item["album"]["name"]
                release_date = item["album"]["release_date"]
                track_duration = item["duration_ms"] / 1000
                track_info = {
                    "title": item["name"],
                    "artists": artist_names,
                    "album_name": album_name,
                    "release_date": release_date,
                    "track_duration": track_duration,
                    "track_id": item["id"],
                }
                tracks.append(track_info)
            return tracks
        except Exception:
            logger.error(f"Error in album: {traceback.format_exc()}")
            return None

    async def artist(self, link: str):
        try:
            artist_top_tracks = self.spotify.artist_top_tracks(link)
            tracks = []
            for track in artist_top_tracks["tracks"]:
                artist_names = [artist["name"] for artist in track["artists"]]
                album_name = track["album"]["name"]
                release_date = track["album"]["release_date"]
                track_duration = track["duration_ms"] / 1000
                track_info = {
                    "title": track["name"],
                    "artists": artist_names,
                    "album_name": album_name,
                    "release_date": release_date,
                    "track_duration": track_duration,
                    "track_id": track["id"],
                }
                tracks.append(track_info)
            return tracks
        except Exception:
            logger.error(f"Error in artist: {traceback.format_exc()}")
            return None


Spotify = SpotifyAPI()
