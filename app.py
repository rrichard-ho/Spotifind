import spotipy
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
    user = 'Richard'
    return render_template('index.html')

@app.route('/page1')
def page1():
    return 'Welcome to Page 1!'

@app.route('/page2')
def page2():
    return 'Welcome to Page 2!'

def create_spotify_oauth():
    return SpotifyOAuth(
        client_id = CLIENT_ID,
        client_secret = CLIENT_SECRET,
        redirect_uri = url_for('redirect_page', _external = True),
        scope = 'user-library-read user-top-read playlist-modify-private playlist-modify-public'
    )