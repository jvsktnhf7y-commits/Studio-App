# Authentication module for Studio App
from passlib.context import CryptContext
from fastapi import HTTPException, status
from fastapi import Request
from fastapi.responses import RedirectResponse
import os
import json

# Password hashing setup with bcrypt (max 72 chars)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Users file - stores hashed passwords
USERS_FILE = "users.json"

# Default admin user (you should change this password after first login)
DEFAULT_ADMIN = {
    "username": "admin",
    "password_hash": pwd_context.hash("studio2025")  # Change this password!
}

def truncate_password(password: str, max_length: int = 72) -> str:
    """Truncate password to bcrypt's max length"""
    return password[:max_length] if len(password) > max_length else password

def init_users():
    """Initialize users file with default admin if it doesn't exist"""
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({"users": [DEFAULT_ADMIN]}, f, indent=2)
        print("✅ Created users.json with default admin account")
        print("   Username: admin")
        print("   Password: studio2025")
        print("   PLEASE CHANGE THIS PASSWORD AFTER FIRST LOGIN!")

def verify_password(plain_password, hashed_password):
    """Verify a password against its hash with truncation"""
    truncated_password = truncate_password(plain_password)
    return pwd_context.verify(truncated_password, hashed_password)

def get_user(username: str):
    """Get user from users file"""
    if not os.path.exists(USERS_FILE):
        init_users()
    
    with open(USERS_FILE, 'r') as f:
        data = json.load(f)
    
    for user in data.get("users", []):
        if user["username"] == username:
            return user
    return None

def authenticate_user(username: str, password: str):
    """Authenticate a user"""
    user = get_user(username)
    if not user:
        return False
    if not verify_password(password, user["password_hash"]):
        return False
    return True

def change_password(username: str, old_password: str, new_password: str):
    """Change user's password"""
    if not authenticate_user(username, old_password):
        return False
    
    # Truncate new password if needed
    new_password = truncate_password(new_password)
    
    # Load users
    with open(USERS_FILE, 'r') as f:
        data = json.load(f)
    
    # Find and update user
    for user in data["users"]:
        if user["username"] == username:
            user["password_hash"] = pwd_context.hash(new_password)
            break
    
    # Save back
    with open(USERS_FILE, 'w') as f:
        json.dump(data, f, indent=2)
    
    return True

def create_login_middleware(app):
    """Add login requirement to all routes except login page"""
    
    @app.middleware("http")
    async def check_login(request: Request, call_next):
        # Skip login check for these paths
        public_paths = ["/login", "/logout", "/static"]
        
        # Check if path is public
        if any(request.url.path.startswith(path) for path in public_paths):
            return await call_next(request)
        
        # Check if user is logged in
        session = request.cookies.get("studio_session")
        if not session or session != "authenticated":
            # Redirect to login page
            return RedirectResponse(url="/login", status_code=303)
        
        return await call_next(request)
    
    return check_login

def get_login_page():
    """Return the login page HTML"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Studio Login</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
            }
            
            .login-container {
                background: white;
                padding: 40px;
                border-radius: 20px;
                box-shadow: 0 10px 40px rgba(0,0,0,0.1);
                width: 100%;
                max-width: 400px;
            }
            
            h1 {
                text-align: center;
                color: #333;
                margin-bottom: 10px;
                font-size: 28px;
            }
            
            .subtitle {
                text-align: center;
                color: #666;
                margin-bottom: 30px;
                font-size: 14px;
            }
            
            .form-group {
                margin-bottom: 20px;
            }
            
            label {
                display: block;
                margin-bottom: 8px;
                color: #333;
                font-weight: 600;
            }
            
            input {
                width: 100%;
                padding: 12px;
                border: 2px solid #e0e0e0;
                border-radius: 8px;
                font-size: 16px;
                transition: border-color 0.3s;
            }
            
            input:focus {
                outline: none;
                border-color: #667eea;
            }
            
            button {
                width: 100%;
                padding: 12px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 8px;
                font-size: 16px;
                font-weight: 600;
                cursor: pointer;
                transition: transform 0.2s;
            }
            
            button:hover {
                transform: translateY(-2px);
            }
            
            .error {
                background: #fee;
                color: #c33;
                padding: 10px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
                font-size: 14px;
            }
            
            .info {
                background: #e3f2fd;
                color: #1976d2;
                padding: 10px;
                border-radius: 8px;
                margin-bottom: 20px;
                text-align: center;
                font-size: 12px;
            }
        </style>
    </head>
    <body>
        <div class="login-container">
            <h1>🎵 Studio Console</h1>
            <div class="subtitle">Please log in to continue</div>
            
            {error_message}
            
            <form action="/login" method="post">
                <div class="form-group">
                    <label>Username</label>
                    <input type="text" name="username" required autofocus>
                </div>
                
                <div class="form-group">
                    <label>Password</label>
                    <input type="password" name="password" required>
                </div>
                
                <button type="submit">Login</button>
            </form>
            
            <div class="info" style="margin-top: 20px;">
                🔐 Default: admin / studio2025<br>
                Change password after first login
            </div>
        </div>
    </body>
    </html>
    '''
