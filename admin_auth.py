import hashlib
import secrets
import json
import os
from datetime import datetime, timedelta

# Admin credentials file
ADMIN_CREDS_FILE = 'admin_data/admin_credentials.json'
SESSIONS_FILE = 'admin_data/admin_sessions.json'

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def generate_token():
    """Generate secure random token"""
    return secrets.token_urlsafe(32)

def init_admin_credentials():
    """Initialize admin credentials if not exists"""
    os.makedirs('admin_data', exist_ok=True)
    
    if not os.path.exists(ADMIN_CREDS_FILE):
        # Default credentials - user should change after first login
        default_creds = {
            'username': 'admin',
            'password_hash': hash_password('admin2026!'),  # Secure default password
            'created_at': datetime.now().isoformat()
        }
        
        with open(ADMIN_CREDS_FILE, 'w') as f:
            json.dump(default_creds, f, indent=2)
        
        print("=" * 60)
        print("ADMIN CREDENTIALS INITIALIZED")
        print("=" * 60)
        print(f"Username: admin")
        print(f"Password: admin2026!")
        print("=" * 60)
        print("IMPORTANT: Change these credentials immediately after first login!")
        print("=" * 60)

def verify_login(username, password):
    """Verify login credentials"""
    if not os.path.exists(ADMIN_CREDS_FILE):
        init_admin_credentials()
    
    with open(ADMIN_CREDS_FILE, 'r') as f:
        creds = json.load(f)
    
    if username == creds['username'] and hash_password(password) == creds['password_hash']:
        return True
    return False

def create_session(username):
    """Create new admin session"""
    token = generate_token()
    
    # Load existing sessions
    sessions = {}
    if os.path.exists(SESSIONS_FILE):
        with open(SESSIONS_FILE, 'r') as f:
            sessions = json.load(f)
    
    # Add new session
    sessions[token] = {
        'username': username,
        'created_at': datetime.now().isoformat(),
        'expires_at': (datetime.now() + timedelta(hours=24)).isoformat()
    }
    
    # Save sessions
    with open(SESSIONS_FILE, 'w') as f:
        json.dump(sessions, f, indent=2)
    
    return token

def verify_session(token):
    """Verify if session token is valid"""
    if not token or not os.path.exists(SESSIONS_FILE):
        return False
    
    with open(SESSIONS_FILE, 'r') as f:
        sessions = json.load(f)
    
    if token not in sessions:
        return False
    
    session = sessions[token]
    expires_at = datetime.fromisoformat(session['expires_at'])
    
    if datetime.now() > expires_at:
        # Session expired
        del sessions[token]
        with open(SESSIONS_FILE, 'w') as f:
            json.dump(sessions, f, indent=2)
        return False
    
    return True

def change_password(username, old_password, new_password):
    """Change admin password"""
    if not verify_login(username, old_password):
        return False
    
    with open(ADMIN_CREDS_FILE, 'r') as f:
        creds = json.load(f)
    
    creds['password_hash'] = hash_password(new_password)
    creds['updated_at'] = datetime.now().isoformat()
    
    with open(ADMIN_CREDS_FILE, 'w') as f:
        json.dump(creds, f, indent=2)
    
    return True

# Initialize on import
init_admin_credentials()
