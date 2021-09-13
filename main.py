import spotipy
from spotipy.oauth2 import SpotifyOAuth
import typer


def flatten(t):
    return [item for sublist in t for item in sublist]


def init_spotify_client(client_id, client_secret, scope):
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        scope=scope, 
        client_secret=client_secret, 
        client_id=client_id,
        redirect_uri="http://localhost:8080/"
    ))


def get_user_liked_playlist(sp):
    step_size = 20
    all_tracks = []

    saved_tracks = sp.current_user_saved_tracks(limit=step_size)

    n_tracks = saved_tracks["total"]

    all_tracks.append(saved_tracks["items"])

    for offset in range(0, n_tracks, step_size):
        saved_tracks = sp.current_user_saved_tracks(limit=step_size, offset=offset)
        all_tracks.append(saved_tracks["items"])

    return flatten(all_tracks)


def get_tracks_from_playlist(sp, playlist_id):
    step_size = 20
    all_tracks = []

    saved_tracks = sp.playlist_items(playlist_id, limit=step_size)

    n_tracks = saved_tracks["total"]

    all_tracks.append(saved_tracks["items"])

    for offset in range(0, n_tracks, step_size):
        saved_tracks = sp.playlist_items(playlist_id, limit=step_size, offset=offset)
        all_tracks.append(saved_tracks["items"])

    return flatten(all_tracks)

def get_tracks_and_metadata(sp, track_list):
    audio_feature_step = 5

    all_tracks = track_list
    all_ids = [track["track"]["id"] for track in all_tracks]
    all_features = []


    for fetch_range in range(0, len(all_tracks), audio_feature_step):
        all_features.append(sp.audio_features(all_ids[fetch_range:fetch_range + audio_feature_step]))

    all_features = flatten(all_features)

    track_data = {}
    for id in all_ids:
        track_data[id] = {
            "info": {},
            "features": {}
        }

    for feature in all_features:
        track_data[feature["id"]]["features"] = feature

    for track in all_tracks:
        track_data[track["track"]["id"]]["info"] = track

    return track_data    


def filter_tracks_by_tempo(track_data, tempo_filter, allowed_variation = 5):
    tracks_to_be_added = []
    for track_id in track_data:
        if "tempo" in track_data[track_id]["features"]:
            tempo = track_data[track_id]["features"]["tempo"]
            if tempo > (tempo_filter - allowed_variation) and tempo < (tempo_filter + allowed_variation):
                tracks_to_be_added.append(track_id)

    return tracks_to_be_added    


def create_and_populate_playlist(sp, user_id, playlist_name, tracks_to_be_added):
    new_list = sp.user_playlist_create(user_id, playlist_name, public=False)

    track_add_step = 50

    for track_offset in range(0, len(tracks_to_be_added), track_add_step):
        sp.user_playlist_add_tracks(user_id, new_list["id"], tracks_to_be_added[track_offset:track_offset+track_add_step])


def main(client_id, client_secret, playlist_id):
    sp = init_spotify_client(client_id, client_secret, "playlist-modify-private")
    filter_bpm = 150
    current_user = sp.current_user()

    if playlist_id == "user_liked":
        playlist_items = get_user_liked_playlist(sp)
    else:
        playlist_items = get_tracks_from_playlist(sp, playlist_id)

    track_data = get_tracks_and_metadata(sp, playlist_items)
    tracks_to_be_added = filter_tracks_by_tempo(track_data, filter_bpm, 4)
    create_and_populate_playlist(sp, current_user["id"], f"{filter_bpm}BPM playlist", tracks_to_be_added)


if __name__ == "__main__":
    typer.run(main)
