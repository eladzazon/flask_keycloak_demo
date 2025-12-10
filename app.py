from flask import Flask, url_for, session, redirect, render_template, abort
from authlib.integrations.flask_client import OAuth
from dotenv import load_dotenv
import os
import json

# Load environment variables
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY')

# OIDC Configuration
OIDC_ISSUER = os.getenv('OIDC_ISSUER')
OIDC_CLIENT_ID = os.getenv('OIDC_CLIENT_ID')
OIDC_CLIENT_SECRET = os.getenv('OIDC_CLIENT_SECRET')

oauth = OAuth(app)
oauth.register(
    name='keycloak',
    client_id=OIDC_CLIENT_ID,
    client_secret=OIDC_CLIENT_SECRET,
    server_metadata_url=f'{OIDC_ISSUER}/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid profile email roles',  # Request roles scope if available
        'code_challenge_method': 'S256'  # Use PKCE
    }
)

@app.route('/')
def index():
    user = session.get('user')
    return render_template('home.html', user=user)

@app.route('/login')
def login():
    redirect_uri = url_for('callback', _external=True)
    return oauth.keycloak.authorize_redirect(redirect_uri)

@app.route('/callback')
def callback():
    try:
        token = oauth.keycloak.authorize_access_token()
        session['user'] = token
        return redirect(url_for('profile'))
    except Exception as e:
        # In a real app, you'd handle this more gracefully
        return f"Authentication failed: {e}", 400

@app.route('/profile')
def profile():
    token = session.get('user')
    if not token:
        return redirect(url_for('login'))
    
    # Authlib automatically parses the id_token if present, or we can use userinfo
    user_info = token.get('userinfo')
    if not user_info:
        # Sometimes userinfo is not in the token response immediately or depends on config
        # Let's try to fetch it if not present, though authorize_access_token usually handles it
        # based on id_token.
        # Fallback to fetching userinfo endpoint if needed, but often it's in 'userinfo' key 
        # of the token dict if parsed, or we can parse 'id_token' JWT.
        # For simplicity with Authlib, let's assume it's there or part of the parsed token.
        pass

    # Inspect the full token to find roles
    # Keycloak usually puts roles in 'realm_access' -> 'roles' and 'resource_access' -> client -> 'roles'
    # These might be in the access_token or id_token. 
    # Validating the access_token is complex, but for display we can decode it (unverified) 
    # or rely on what Authlib gives us if it parsed the ID token.
    
    # Let's display the whole user info for debugging and pick out specific fields
    
    return render_template('profile.html', user=user_info, token=token)

@app.route('/logout')
def logout():
    token = session.get('user')
    id_token = token.get('id_token') if token else None
    
    session.pop('user', None)
    
    # Keycloak OIDC logout endpoint
    logout_url = f"{OIDC_ISSUER}/protocol/openid-connect/logout"
    
    # Construct logout redirect with id_token_hint
    from urllib.parse import urlencode
    params = {'post_logout_redirect_uri': url_for('index', _external=True)}
    if id_token:
        params['id_token_hint'] = id_token
        
    return redirect(f"{logout_url}?{urlencode(params)}")

if __name__ == '__main__':
    app.run(debug=True)
