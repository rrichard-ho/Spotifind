import spotipy, time
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
    greeting = get_greeting()

    return render_template('index.html', greeting = greeting, user_name=display_name)

@app.route('/recommend', methods=['GET', 'POST'])
def recommend():
    if request.method == 'POST':
        song_uri = request.form['song_uri']
        return redirect(url_for('recommend_success', uri=song_uri))
    else:
        return render_template('recommend.html')

@app.route('/<uri>')
def recommend_success(uri):
    return f"<h1>{uri}</h1>"

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