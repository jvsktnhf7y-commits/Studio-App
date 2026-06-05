# Script to add login functionality to main.py
import re

# Read the current main.py
with open('main.py', 'r') as f:
    content = f.read()

# Check if login already exists
if "/login" in content:
    print("Login already exists in main.py")
    exit(0)

# The login routes to add
login_routes = '''

# Login Routes
@app.get("/login", response_class=HTMLResponse)
def login_page(error: str = None):
    """Display login page"""
    error_html = f'<div class="error">{error}</div>' if error else ''
    login_html = get_login_page().replace("{error_message}", error_html)
    return HTMLResponse(content=login_html, status_code=200)

@app.post("/login")
def login(username: str = Form(...), password: str = Form(...)):
    """Handle login"""
    if authenticate_user(username, password):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="studio_session", value="authenticated", httponly=True, max_age=86400)
        return response
    else:
        return RedirectResponse(url="/login?error=Invalid username or password", status_code=303)

@app.get("/logout")
def logout():
    """Handle logout"""
    response = RedirectResponse(url="/login", status_code=303)
    response.delete_cookie("studio_session")
    return response

@app.get("/change-password", response_class=HTMLResponse)
def change_password_form():
    """Display change password form"""
    return HTMLResponse("""
    <div style="max-width:500px;margin:50px auto;padding:30px;background:white;border-radius:16px">
        <h2>Change Password</h2>
        <form action="/change-password" method="post">
            <div class="form-group">
                <label>Current Password</label>
                <input type="password" name="old_password" class="form-control" required>
            </div>
            <div class="form-group">
                <label>New Password</label>
                <input type="password" name="new_password" class="form-control" required>
            </div>
            <div class="form-group">
                <label>Confirm New Password</label>
                <input type="password" name="confirm_password" class="form-control" required>
            </div>
            <button type="submit" class="btn-submit">Update Password</button>
        </form>
        <p style="margin-top:20px"><a href="/">Back to Dashboard</a></p>
    </div>
    """)

@app.post("/change-password")
def change_password(
    old_password: str = Form(...),
    new_password: str = Form(...),
    confirm_password: str = Form(...)
):
    """Handle password change"""
    if new_password != confirm_password:
        return RedirectResponse(url="/change-password?error=Passwords don't match", status_code=303)
    
    from auth import change_password
    if change_password("admin", old_password, new_password):
        response = RedirectResponse(url="/", status_code=303)
        response.set_cookie(key="studio_session", value="authenticated", httponly=True, max_age=86400)
        return response
    else:
        return RedirectResponse(url="/change-password?error=Current password is incorrect", status_code=303)

# Initialize auth middleware
create_login_middleware(app)
'''

# First, add the auth imports at the top if not present
auth_imports = """
# Authentication
from auth import init_users, authenticate_user, create_login_middleware, get_login_page
from fastapi import Cookie
import json

# Initialize users file
init_users()
"""

# Add imports after existing imports
if "from auth import" not in content:
    lines = content.split('\n')
    insert_pos = 0
    for i, line in enumerate(lines):
        if line.startswith('from ') or line.startswith('import '):
            insert_pos = i + 1
    lines.insert(insert_pos, auth_imports)
    content = '\n'.join(lines)
    print("Added auth imports")

# Add the login routes before the if __name__ line
if 'if __name__ == "__main__":' in content:
    content = content.replace('if __name__ == "__main__":', login_routes + '\n\nif __name__ == "__main__":')
    print("Added login routes")

# Save the updated file
with open('main.py', 'w') as f:
    f.write(content)

print("Login system successfully added to main.py")
