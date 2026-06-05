from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
import os

SCOPES = ['https://www.googleapis.com/auth/calendar']

def test_google_auth():
    creds = None
    token_file = 'token.json'
    
    # Check if we already have a token
    if os.path.exists(token_file):
        print("✅ Found existing token.json")
        creds = Credentials.from_authorized_user_file(token_file, SCOPES)
    
    # If no valid credentials, authenticate
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            print("🔄 Refreshing expired token...")
            creds.refresh(Request())
        else:
            print("🔐 Starting OAuth flow...")
            if not os.path.exists('credentials.json'):
                print("❌ credentials.json not found!")
                return False
            
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            
            # Save token for next time
            with open(token_file, 'w') as token:
                token.write(creds.to_json())
            print(f"✅ Token saved to {token_file}")
    
    print("✅ Authentication successful!")
    print(f"Token expires at: {creds.expiry}")
    return True

if __name__ == "__main__":
    test_google_auth()
