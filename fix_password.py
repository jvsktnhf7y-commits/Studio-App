import json
import hashlib
import os

# Create password file if it doesn't exist
PASSWORD_FILE = "admin_password.json"

# Hash the default password
default_password = "studio2025"
password_hash = hashlib.sha256(default_password.encode()).hexdigest()

# Save to file
with open(PASSWORD_FILE, 'w') as f:
    json.dump({"password_hash": password_hash}, f)

print(f"✅ Password file created with default password: {default_password}")
print("   You can now change passwords through the web interface")
