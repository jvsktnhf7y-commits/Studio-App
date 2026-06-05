import os
import sys

# Try to import and run calendar auth
try:
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    from datetime import datetime
    import pytz
    
    SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
    
    print("1. Checking for token.json...")
    if os.path.exists('token.json'):
        print("   ✅ token.json found")
        creds = Credentials.from_authorized_user_file('token.json', SCOPES)
    else:
        print("   ❌ token.json not found")
        creds = None
    
    print("2. Checking credentials validity...")
    if creds and creds.valid:
        print("   ✅ Token is valid")
    elif creds and creds.expired and creds.refresh_token:
        print("   🔄 Token expired, refreshing...")
        creds.refresh(Request())
        print("   ✅ Token refreshed")
    else:
        print("   🔐 Need new authentication")
        if os.path.exists('credentials.json'):
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
            print("   ✅ New token created")
        else:
            print("   ❌ credentials.json not found")
            sys.exit(1)
    
    print("3. Building calendar service...")
    service = build('calendar', 'v3', credentials=creds)
    
    print("4. Fetching today's events...")
    local_tz = pytz.timezone('America/New_York')
    now = datetime.now(local_tz)
    start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
    end_of_day = now.replace(hour=23, minute=59, second=59, microsecond=0)
    
    start_utc = start_of_day.astimezone(pytz.UTC).isoformat()
    end_utc = end_of_day.astimezone(pytz.UTC).isoformat()
    
    events_result = service.events().list(
        calendarId='primary',
        timeMin=start_utc,
        timeMax=end_utc,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    events = events_result.get('items', [])
    
    if events:
        print(f"\n✅ Found {len(events)} event(s) for today:")
        for event in events:
            summary = event.get('summary', 'No title')
            start = event.get('start', {}).get('dateTime', 'All day')
            print(f"   📅 {summary} at {start}")
    else:
        print("\n📭 No events found for today")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
