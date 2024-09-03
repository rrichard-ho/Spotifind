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
    return render_template('landing.html')

@app.route('/login')
def login():
    sp_oauth = create_spotify_oauth()
    auth_url = sp_oauth.get_authorize_url()
    return redirect(auth_url)

@app.route('/redirect')
def redirect_page():
    sp_oauth = create_spotify_oauth()
    session.clear()
    
    code = request.args.get('code')
    token_info = sp_oauth.get_access_token(code)
    session[TOKEN_INFO] = token_info
    
    return redirect(url_for('home_page', _external=True))

@app.route('/home')
def home_page():
    try:
        token_info = get_token()
    except:
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    current_user = sp.current_user()
    display_name = current_user.get('display_name')
    profile_pic = current_user.get('images')[0].get('url')
    print(profile_pic)
    greeting = get_greeting()

    return render_template('index.html', greeting = greeting, user_name=display_name, pfp_link=profile_pic)

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if request.method == 'POST':
        song_uri = request.form['song_uri']
        if not valid_track_uri(song_uri):
            return render_template('recommend.html', error_message="Invalid Spotify track URI. Please try again.")
        return redirect(url_for('recommend_success', uri=song_uri))
    else:
        return render_template('recommend.html')

@app.route('/<uri>', methods=['GET', 'POST'])
def recommend_success(uri):
    try:
        token_info = get_token()
    except:
        return redirect('/')
    
    sp = spotipy.Spotify(auth=token_info['access_token'])

    seed_track = sp.track(track_id=uri)
    recommendations = sp.recommendations(seed_tracks=[uri], limit=30)

    if request.method == 'POST':
        create_playlist(uri, recommendations)
        return redirect(f'/{uri}?playlist_created=true')

    return render_template('recommend-success.html', seed_track=seed_track,recommendations=recommendations)

def create_playlist(seed_track_uri, recommendations):
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
            print("WE FOUND IT")
            break
    
    uri_list = []
    for track in recommendations['tracks']:
        uri_list.append(track['uri'])
        
    print("URIs to be added to the playlist:", uri_list)
    print("USER ID: ", id)
    print("PLAYLIST ID: ", playlist_id)
    sp.user_playlist_add_tracks(user=id, playlist_id=playlist_id, tracks=uri_list, position=None)
    sp.user_playlist_change_details(user=id, playlist_id=playlist_id,public=False)

def get_playlist_rec_name(seed_track_name):
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
    return f"Songs similar to {seed_track_name} by {seed_track_artist}"


@app.route('/stats')
def stats():
    return 'Welcome to Page 2!'

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        redirect_uri = url_for('redirect_page', _external = True),
        scope = 'user-library-read user-top-read playlist-modify-private playlist-modify-public'
    )

def get_greeting():
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
    pattern = r'^spotify:track:[A-Za-z0-9]{22}$'
    return re.match(pattern, uri)

def valid_artist_uri(uri):
    pattern = r'^spotify:artist:[A-Za-z0-9]{22}$'
    return re.match(pattern, uri)


def get_token():
    token_info = session.get(TOKEN_INFO, None)
    if not token_info:
        redirect(url_for('login', external=False))

    now = int(time.time())

    is_expired = token_info['expires_at'] - now < 60
    if (is_expired):
        spotify_oauth = create_spotify_oauth()
        token_info = spotify_oauth.refresh_access_token(token_info['refresh_token'])
    return token_info