import sys

# Read current main.py
with open('main.py', 'r') as f:
    content = f.read()

# Find the old calendar function and replace it
old_function_start = content.find('def get_google_calendar_events(')
if old_function_start == -1:
    print("❌ Could not find get_google_calendar_events function")
    sys.exit(1)

# Find where this function ends (next def at same indent level)
lines = content[old_function_start:].split('\n')
function_lines = []
indent_level = None
for line in lines:
    if indent_level is None and line.strip():
        indent_level = len(line) - len(line.lstrip())
    if line.strip() and not line.strip().startswith('#'):
        current_indent = len(line) - len(line.lstrip())
        if current_indent == indent_level and function_lines:
            break
    function_lines.append(line)

old_function = '\n'.join(function_lines)

# New improved function
new_function = '''def get_google_calendar_events():
    """Get today's events from Google Calendar with proper error handling"""
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from datetime import datetime
        import pytz
        
        SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
        creds = None
        
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                if not os.path.exists('credentials.json'):
                    return []
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        service = build('calendar', 'v3', credentials=creds)
        
        # Get today's events
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
        
        return events_result.get('items', [])
    
    except Exception as e:
        print(f"Calendar error: {e}")
        return []'''

# Replace in content
new_content = content.replace(old_function, new_function)

# Write backup and new file
with open('main.py.backup', 'w') as f:
    f.write(content)
    print("✅ Backup saved to main.py.backup")

with open('main.py', 'w') as f:
    f.write(new_content)
    print("✅ main.py updated with improved calendar function")

print("\nUpdate complete! Restart your app to see changes.")
