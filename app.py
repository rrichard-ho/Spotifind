import spotipy, time, re
from spotipy.oauth2 import SpotifyOAuth

from flask import Flask, request, url_for, session, redirect, render_template

app = Flask(__name__)

app.config['SESSION_COOKIE_NAME'] = 'cookie'
app.secret_key = '{/FMO@^fUwD}ZMuA&DgV^lt}r+":#%'
TOKEN_INFO = 'token_info'
CLIENT_ID = '527201037c544da2886c1a92b00bfb3d'
CLIENT_SECRET = 'c33daf1b48d147c1b503dcb98b6c454f'

@app.route('/')
def index():
    """This is the landing page.

    The first page the user sees.
    Prompts the user to allow access to Spotify authorization.
    """
    return render_template('landing.html')

@app.route('/login')
def login():
    """This is the login page.

    Redirects the user to the external Spotify authorization page.
    """
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirect_page():
    """This is the redirect page.

    This gets the access token from the code returned upon successful authorization with Spotify.
    """
    sp_oauth = create_spotify_oauth()
    session.clear()
    
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    
    return redirect(url_for('home_page', _external=True))

@app.route('/home')
def home_page():
    """This is the home page.

    Provides general access to the functions of Spotifind.
    """
    try:
        token_info = get_token()
    except:
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    current_user = sp.current_user()
    display_name = current_user.get('display_name')
    profile_pic = current_user.get('images')[0].get('url')
    greeting = get_greeting()

    return render_template('index.html', greeting = greeting, user_name=display_name, pfp_link=profile_pic)

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    """This is the default recommendations page.

    Gets a track URI from the user and redirect to the success page if it is a valid track URI.
    """
    if request.method == 'POST':
        song_uri = request.form['song_uri']
        if not valid_track_uri(song_uri):
            return render_template('recommend.html', error_message="Invalid Spotify track URI. Please try again.")
        return redirect(url_for('recommend_success', uri=song_uri))
    else:
        return render_template('recommend.html')

@app.route('/<uri>', methods=['GET', 'POST'])
def recommend_success(uri):
    """This is the success page for successful recommendations.

    Use the provided seed track to get recommendations and create a Spotify playlist to put them in.
    """
    try:
        token_info = get_token()
    except:
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    seed_track = sp.track(track_id=uri)
    seed_track_cover = seed_track['album']['images'][0]['url']
    recommendations = sp.recommendations(seed_tracks=[uri], limit=30)

    if request.method == 'POST':
        create_playlist(uri, recommendations)
        return redirect(f'/{uri}?playlist_created=true')

    return render_template('recommend-success.html', seed_track=seed_track,recommendations=recommendations, seed_track_cover=seed_track_cover)

def create_playlist(seed_track_uri, recommendations):
    """Creates a Spotify playlist for the recommended songs to be put in.

    Uses user data and the two playlist helper methods to create a Spotify playlist.
    Finds the playlist id for this new playlist.
    Adds all of the recommended songs into the new playlist.
    """
    try:
        token_info = get_token()
    except:
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    id = sp.current_user()['id']

    seed_track = sp.track(seed_track_uri)
    playlist_name = get_playlist_rec_name(seed_track['name'])
    playlist_desc = get_playlist_rec_desc(seed_track['name'], seed_track['artists'][0]['name'])
    sp.user_playlist_create(id,name=playlist_name,public=True,description=playlist_desc)

    current_playlists = sp.current_user_playlists()['items']
    playlist_id = None
    for playlist in current_playlists:
        print(playlist['name'])
        if playlist['name'] == playlist_name:
            playlist_id = playlist['id']
            break
    
    uri_list = []
    for track in recommendations['tracks']:
        uri_list.append(track['uri'])
    
    sp.user_playlist_add_tracks(user=id, playlist_id=playlist_id, tracks=uri_list, position=None)
    sp.user_playlist_change_details(user=id, playlist_id=playlist_id,public=False)

def get_playlist_rec_name(seed_track_name):
    """Returns the playlist name for the new recommendations playlist.

    Loops through all of the current user's public playlists to ensure no duplicate playlist name is used.
    """
    try:
        token_info = get_token()
    except:
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])
    count = 2

    base_name = "Spotifind " + seed_track_name.strip()
    playlist_name = base_name

    current_playlists = sp.current_user_playlists()['items']

    existing_names = set()
    for playlist in current_playlists:
        existing_names.add(playlist['name'].strip())

    while playlist_name in existing_names:
        playlist_name = f"{base_name} #{count}"
        count += 1
    
    return playlist_name

def get_playlist_rec_desc(seed_track_name, seed_track_artist):
    """Returns a hard-coded string with the provided parameters filled in.
    """
    return f"Songs similar to {seed_track_name} by {seed_track_artist}"


@app.route('/stats')
def stats():
    return 'Welcome to Page 2!'

def create_spotify_oauth():
    """Redirects the user to the external Spotify authorization page.

    Establishes the scopes of the data retrieved.
    """
    return SpotifyOAuth(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        redirect_uri = url_for('redirect_page', _external = True),
        scope = 'user-library-read user-top-read playlist-modify-private playlist-modify-public'
    )

def get_greeting():
    """returns the time of day it is.

    Uses the Python time library to get the current local time.
    Depending on what the current hour is, return it's corresponding time of day.
    """
    current_hour = time.localtime().tm_hour
    if (current_hour < 4):
        return 'night'
    elif (current_hour < 12):
        return 'morning'
    elif (current_hour < 17):
        return 'afternoon'
    elif (current_hour < 20):
        return 'evening'
    else: 
        return 'night'
    
def valid_track_uri(uri):
    """Returns whether or not the provided track URI is valid.

    Uses the regex library to ensure that the provided track URI matches the spotify URI pattern.
    """
    pattern = r'^spotify:track:[A-Za-z0-9]{22}$'
    return re.match(pattern, uri)

def valid_artist_uri(uri):
    """Returns whether or not the provided artist URI is valid.

    Uses the regex library to ensure that the provided artist URI matches the spotify artist URI pattern.
    """
    pattern = r'^spotify:artist:[A-Za-z0-9]{22}$'
    return re.match(pattern, uri)


def get_token():
    """Returns the access token to make requests with.

    Find out if the current access token is expired or not.
    If it is expired, refresh it.
    """
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', external=False))

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info