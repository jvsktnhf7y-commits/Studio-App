import re

with open('main.py', 'r') as f:
    content = f.read()

# Check if schedule feature already exists
if '@app.get("/schedule")' in content:
    print("Schedule feature already exists!")
    exit(0)

# The new schedule form and endpoint
new_code = '''

@app.get("/schedule", response_class=HTMLResponse)
def schedule_form():
    """Display the create lesson form"""
    students = get_all_profiles()
    student_options = ""
    for name in students.keys():
        student_options += f'<option value="{name}">{name}</option>'
    
    if not student_options:
        student_options = '<option value="">No students yet - create one first</option>'
    
    form_html = f'''
    <h1>📅 Schedule New Lesson</h1>
    <div class="form-panel">
        <form action="/create-lesson" method="post">
            <div class="form-group">
                <label>Student Name</label>
                <select name="student_name" class="form-control" required>
                    <option value="">Select a student</option>
                    {student_options}
                </select>
            </div>
            
            <div class="form-group">
                <label>Date</label>
                <input type="date" name="date" class="form-control" required>
            </div>
            
            <div class="form-group">
                <label>Time</label>
                <input type="time" name="time" class="form-control" required>
            </div>
            
            <div class="form-group">
                <label>Duration (minutes)</label>
                <select name="duration" class="form-control">
                    <option value="30">30 minutes</option>
                    <option value="45">45 minutes</option>
                    <option value="60" selected>60 minutes</option>
                    <option value="90">90 minutes</option>
                </select>
            </div>
            
            <button type="submit" class="btn-submit">✨ Create Lesson & Add to Calendar</button>
        </form>
    </div>
    <p style="margin-top: 20px;"><a href="/">← Back to Dashboard</a></p>
    '''
    
    return get_shared_html_layout("schedule", form_html)

@app.post("/create-lesson")
def create_lesson_endpoint(
    student_name: str = Form(...),
    date: str = Form(...),
    time: str = Form(...),
    duration: int = Form(60)
):
    """Create a new lesson and add to Google Calendar"""
    from datetime import datetime, timedelta
    import pytz
    from google.auth.transport.requests import Request as GoogleRequest
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow
    from googleapiclient.discovery import build
    
    try:
        lesson_datetime = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        tz = pytz.timezone('America/New_York')
        lesson_datetime = tz.localize(lesson_datetime)
        
        SCOPES = ['https://www.googleapis.com/auth/calendar']
        creds = None
        
        if os.path.exists('token.json'):
            creds = Credentials.from_authorized_user_file('token.json', SCOPES)
        
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(GoogleRequest())
            else:
                flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
                creds = flow.run_local_server(port=0)
            with open('token.json', 'w') as token:
                token.write(creds.to_json())
        
        service = build('calendar', 'v3', credentials=creds)
        end_time = lesson_datetime + timedelta(minutes=duration)
        
        events_result = service.events().list(
            calendarId='primary',
            timeMin=lesson_datetime.isoformat(),
            timeMax=end_time.isoformat(),
            singleEvents=True
        ).execute()
        
        conflicts = events_result.get('items', [])
        
        if conflicts:
            conflict_names = [e.get('summary', 'Unknown') for e in conflicts]
            return HTMLResponse(f"""
            <div style="max-width:800px;margin:50px auto;text-align:center">
                <h2>⚠️ Time Slot Conflict</h2>
                <p>Conflicts with: {', '.join(conflict_names)}</p>
                <p><a href="/schedule">← Try another time</a></p>
            </div>
            """)
        
        event = {
            'summary': f'Private Lesson - {student_name}',
            'description': f'Music lesson with {student_name}',
            'start': {'dateTime': lesson_datetime.isoformat(), 'timeZone': 'America/New_York'},
            'end': {'dateTime': end_time.isoformat(), 'timeZone': 'America/New_York'},
            'reminders': {'useDefault': True},
        }
        
        service.events().insert(calendarId='primary', body=event).execute()
        
        return HTMLResponse(f"""
        <div style="max-width:800px;margin:50px auto;text-align:center">
            <h2>✅ Lesson Created!</h2>
            <p><strong>{student_name}</strong> on {lesson_datetime.strftime('%B %d at %I:%M %p')}</p>
            <p><a href="/">← Back to Dashboard</a> | <a href="/schedule">Schedule Another →</a></p>
        </div>
        """)
    
    except Exception as e:
        return HTMLResponse(f"""
        <div style="max-width:800px;margin:50px auto;text-align:center">
            <h2>❌ Error: {str(e)}</h2>
            <p><a href="/schedule">← Try Again</a></p>
        </div>
        """)
'''

# Insert before the last line
lines = content.split('\n')
insert_pos = len(lines) - 1
for i, line in enumerate(reversed(lines)):
    if 'if __name__ == "__main__":' in line:
        insert_pos = len(lines) - i - 1
        break

lines.insert(insert_pos, new_code)
content = '\n'.join(lines)

with open('main.py', 'w') as f:
    f.write(content)

print("✅ Schedule feature added successfully!")
