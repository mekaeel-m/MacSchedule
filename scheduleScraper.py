import re
import cv2
import pytesseract
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image
import json
from flask import Flask, request, jsonify, session, url_for
from flask_session import Session
import os
import shutil
from flask_cors import CORS
from datetime import datetime
import pytz
from googleapiclient.discovery import build
import google.oauth2.credentials

local_url = "http://127.0.0.1:5000"
web_url = "http://127.0.0.1:8080"

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": [web_url,local_url]}})

app.config["SESSION_PERMANENT"] = False     # Sessions expire when the browser is closed
app.config["SESSION_TYPE"] = "filesystem"     # Store session data in files

# Initialize Flask-Session
Session(app)

UPLOAD_FOLDER = 'assets/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

#Flask Endpoints

@app.route('/upload', methods=['POST'])
def upload_file():
    erase_folder_contents('assets/')
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    file_path = os.path.join(UPLOAD_FOLDER, 'sched.png')
    file.save(file_path)

    return output()

# Google login

import google.oauth2.credentials
import google_auth_oauthlib.flow


@app.route('/authorizeurl')
def authorize():
    # Required, call the from_client_secrets_file method to retrieve the client ID from a
    # client_secret.json file. The client ID (from that file) and access scopes are required. (You can
    # also use the from_client_config method, which passes the client configuration as it originally
    # appeared in a client secrets file but doesn't access the file itself.)
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file('client_secret.json',
        scopes=['https://www.googleapis.com/auth/calendar'])

    # Required, indicate where the API server will redirect the user after the user completes
    # the authorization flow. The redirect URI is required. The value must exactly
    # match one of the authorized redirect URIs for the OAuth 2.0 client, which you
    # configured in the API Console. If this value doesn't match an authorized URI,
    # you will get a 'redirect_uri_mismatch' error.
    flow.redirect_uri = local_url + '/signon'

    # Generate URL for request to Google's OAuth 2.0 server.
    # Use kwargs to set optional request parameters.
    authorization_url, state = flow.authorization_url(
        # Recommended, enable offline access so that you can refresh an access token without
        # re-prompting the user for permission. Recommended for web server apps.
        access_type='offline',
        # Optional, enable incremental authorization. Recommended as a best practice.
        include_granted_scopes='true',
        # Optional, if your application knows which user is trying to authenticate, it can use this
        # parameter to provide a hint to the Google Authentication Server.
        #login_hint='hint@example.com',
        # Optional, set prompt to 'consent' will prompt the user for consent
        prompt='consent')

    return (authorization_url)

@app.route('/signon')
def signon():
    print(request.args.get('state'))
    # Allowing localhost HTTP for OAuthlib. In production, use HTTPS.
    os.environ['OAUTHLIB_INSECURE_TRANSPORT'] = '1'
    os.environ['OAUTHLIB_RELAX_TOKEN_SCOPE'] = '1'
    
    state = request.args.get('state')
    flow = google_auth_oauthlib.flow.Flow.from_client_secrets_file(
        'client_secret.json',
        scopes=['https://www.googleapis.com/auth/calendar'],
        state=state)
    flow.redirect_uri = url_for('signon', _external=True)

    authorization_response = request.url
    flow.fetch_token(authorization_response=authorization_response)

    # Store the credentials in browser session storage, but for security: client_id, client_secret,
    # and token_uri are instead stored only on the backend server.
    credentials = flow.credentials

    print(credentials.granted_scopes)

    session_credentials = {
        'token': credentials.token,
        'refresh_token': credentials.refresh_token,
        'granted_scopes': credentials.granted_scopes}
    
    with open('assets/parsed_class.json', 'r') as file:
        classlist = json.load(file)

    credentials = google.oauth2.credentials.Credentials(
        **session_credentials,
        client_id='YOUR_CLIENT_ID',
        client_secret='YOUR_CLIENT_SECRET',
        token_uri='https://oauth2.googleapis.com/token')

    service = build('calendar', 'v3', credentials=credentials)

    calendar_id = get_or_create_calendar(service, "McMaster Winter 2026")
    
    #test_add_events(session_credentials)
    for c in classlist:
        add_class(service, c, calendar_id)
    return "worked"

def get_or_create_calendar(service, calendar_name="McMaster Winter 2026"):
    # 2. If not found, create a new one
    calendar = {
        'summary': calendar_name,
        'timeZone': 'Canada/Eastern'
    }
    created_calendar = service.calendars().insert(body=calendar).execute()
    print(f"Created new calendar: {calendar_name} (ID: {created_calendar['id']})")
    return created_calendar['id']


def test_add_events(session_credentials):

    credentials = google.oauth2.credentials.Credentials(
        **session_credentials,
        client_id='YOUR_CLIENT_ID',
        client_secret='YOUR_CLIENT_SECRET',
        token_uri='https://oauth2.googleapis.com/token')

    service = build('calendar', 'v3', credentials=credentials)

    event = {
      'summary': 'Test Event',
      'location': '800 Howard St., San Francisco, CA 94103',
      'description': 'A chance to hear more about Google\'s developer products.',
      'start': {
        'dateTime': '2024-07-01T09:00:00-07:00',
        'timeZone': 'America/Los_Angeles',
      },
      'end': {
        'dateTime': '2024-07-01T17:00:00-07:00',
        'timeZone': 'America/Los_Angeles',
      },
    }

    event = service.events().insert(calendarId='primary', body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))

def add_class(service, class_data, calendar_id):
    dateNumber = {
        'Mon': '05',
        'Tue': '06',
        'Wed': '07',
        'Thu': '08',
        'Fri': '09',
        'Sat': '10',
        'Sun': '11'}
    
    
    # Helper Function: Generate correct UTC EXDATE string
    def get_exdate(date_str, time_str, tz_name='Canada/Eastern'):
        # date_str: "YYYY-MM-DD" (e.g., "2026-02-16")
        # time_str: "HH:MM" 24-hour format (e.g., "14:30")
        
        local_tz = pytz.timezone(tz_name)
        local_dt = local_tz.localize(datetime.strptime(f"{date_str} {time_str}", "%Y-%m-%d %H:%M"))
        utc_dt = local_dt.astimezone(pytz.utc)
        return f"EXDATE:{utc_dt.strftime('%Y%m%dT%H%M%SZ')}"

    # --- Your Main Logic ---

    # 1. Convert start time once
    start_time_24 = convert_to_24h(class_data['start_time'])
    end_time_24 = convert_to_24h(class_data['end_time'])

    # 2. Define the days you want to skip (Reading Week + Holidays)
    # Note: You only need to exclude dates that actually match the class day (e.g., don't exclude Monday if the class is on Tuesday).
    # But Google Calendar is forgiving if you exclude a non-existent instance, so listing all is safe.
    holidays = [
        "2026-02-16", # Mon (Reading Week)
        "2026-02-17", # Tue
        "2026-02-18", # Wed
        "2026-02-19", # Thu
        "2026-02-20", # Fri
        "2026-04-03"  # Good Friday
    ]

    exdates = [get_exdate(day, start_time_24) for day in holidays]

    # Convert class_data to event format
    event = {
      'summary': f"{class_data['course']} {class_data['class_type']}",
      'location': class_data['location'],
      'description': f"Class Code: {class_data['class_code']}",
      'start': {
        'dateTime': f"2026-01-{dateNumber[class_data['day']]}T{convert_to_24h(class_data['start_time'])}:00",
        'timeZone': 'Canada/Eastern',
      },
      'end': {
        'dateTime': f"2026-01-{dateNumber[class_data['day']]}T{convert_to_24h(class_data['end_time'])}:00",
        'timeZone': 'Canada/Eastern',
      },
      'recurrence': [
        'RRULE:FREQ=WEEKLY;UNTIL=20260407T235959Z'] + exdates
    }

    event = service.events().insert(calendarId=calendar_id, body=event).execute()
    print('Event created: %s' % (event.get('htmlLink')))

def convert_to_24h(time_str):
    # 1. Normalize: remove spaces and make uppercase for consistency
    s = time_str.strip().upper()
    
    # 2. Check if it's 12-hour format (contains AM or PM)
    if "AM" in s or "PM" in s:
        is_pm = "PM" in s
        
        # Remove "AM"/"PM" to get raw numbers
        clean_s = s.replace("AM", "").replace("PM", "").strip()
        
        # Split into hour and minute
        parts = clean_s.split(":")
        hour = int(parts[0])
        minute = int(parts[1])
        
        # Apply 12-hour to 24-hour conversion rules
        if is_pm and hour != 12:
            hour += 12
        elif not is_pm and hour == 12:
            hour = 0
            
    # 3. Handle cases that are already 24-hour (no suffix)
    else:
        parts = s.split(":")
        hour = int(parts[0])
        minute = int(parts[1])

    # 4. Return formatted with leading zeros (e.g., 9 -> 09)
    return f"{hour:02d}:{minute:02d}"

# Image Processing and OCR

def extract_text_from_image(image_path):
    # Load original
    img = cv2.imread(image_path)

    # Convert to HSV to isolate the green course blocks
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # target = np.array([40, 46, 214])

    # sensitivity = np.array([10, 12, 20])

    # # Tune these bounds if your green shade is different
    # lower_green = target - sensitivity
    # upper_green = target + sensitivity

    lower_green = np.array([38, 45, 205])
    upper_green = np.array([52, 80, 255])
    

    mask = cv2.inRange(hsv, lower_green, upper_green)
    cv2.imwrite('assets/mask.png', mask)

    # --- NEW STEP: Make black lines bigger ---
    # We create a 3x3 kernel and "erode" the mask.
    # iterations=2 means we peel off 2 layers of pixels from every block edge.
    # This turns a tiny 1px gap into a ~5px gap.
    kernel = np.ones((3,2), np.uint8)
    mask = cv2.erode(mask, kernel, iterations=1)
    # -----------------------------------------
    cv2.imwrite('assets/mask_eroded.png', mask)

    # Find contours (each contour should correspond to one block)
    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                                cv2.CHAIN_APPROX_SIMPLE)

    def contour_key(c):
        x, y, w, h = cv2.boundingRect(c)
        return (x // 10, y)  # Column first, then row

    days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

    # Sorting contours by columns then rows
    contours = sorted(contours, key=contour_key)

    def ocr_perfect(block):
        # 1. Grayscale
        img = cv2.resize(block, None, fx=4, fy=4, interpolation=cv2.INTER_CUBIC)
    
        # Convert to grayscale
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        return gray

    classes = []

    first = True
    for i, c in enumerate(contours, start=1):
        x, y, w, h = cv2.boundingRect(c)

        if w < 60 or h < 30:
            continue  # Skip small noise contours

        if first:
            if (250 < x ):
                day = 1
            else:
                day = 0
            first = False
            prev_x = x
        else:
            if (200 < x - prev_x):
                day += 2
            elif (prev_x < x - 75) and (day < 6):
                day += 1
            prev_x = x

        # Crop block
        pad = 3
        x0, y0 = max(x - pad, 0), max(y - pad, 0)
        x1, y1 = min(x + w + pad, img.shape[1]), min(y + h + pad, img.shape[0]) 
        block = img[y0:y1, x0:x1]

        cv2.imwrite(f'pre/block_{i:02d}_{days[day]}.png', block)

        block_bw = ocr_perfect(block)

        cv2.imwrite(f'post/block_{i:02d}_{days[day]}.png', block_bw)


        extracted_text = pytesseract.image_to_string(block_bw)
        classes.append(days[day] + " " + extracted_text )

    return classes

def parse_class(text):
    # Clean and normalize
    text = re.sub(r'\s+', ' ', text.strip())
    
    result = {key: '' for key in ['day', 'course', 'class_code', 'class_type', 'start_time', 'end_time', 'location']}
    
    # 1. DAY: First 3-letter at start
    day_match = re.search(r'^(Mon|Tue|Wed|Thu|Fri|Sat|Sun)', text)
    if day_match:
        result['day'] = day_match.group(1)
    
    # 2. COURSE: Letters+digits pattern
    course_match = re.search(r'([A-Z]{4,}\s*[0-9A-Z]{4})', text)
    if course_match:
        result['course'] = course_match.group(1)

    raw_code = None

    weird_code_match = re.search(r'-?\s*(C|T|L|c)[oO0]{2}\d', text)
    if weird_code_match:
        double = re.search(r'[oO0]{2}', text)
        
        raw_code = re.search(r'-?\s*(C|T|L|c)[oO0]{2}\d', text).group(0).replace(double.group(0), '0', 1)
    
    # 3. CLASS_CODE: -C01, -T02, TO2
    if not raw_code:
        code_match = re.search(r'-?\s*(C|T|L|c)\d{2}|-?\s*TO\d|-?\s*(C|T|L|c)*(O|o|0)\d{1}|-?\s*(C|T|L|c)*(O|0|o)*(t|a)', text)
        
        if code_match:
            result['class_code'] = code_match.group(0).strip('- ').replace('t', '1').replace('a', '4').upper().replace('O', '0')
    else:
        result['class_code'] = raw_code.strip('- ').replace('t', '1').replace('a', '4').upper().replace('O', '0')
        
    # 4. CLASS_TYPE: Known types
    for typ in ['Lecture', 'Tutorial', 'Laboratory', 'Lab']:
        if typ in text and result['class_type'] == '':
            result['class_type'] = typ
            break
    
    # 5. TIMES: Extract start and end times, even if split across lines
    time_matches = re.findall(r'(\d{1,2}:\d{2}\s*(?:AM|PM)?)', text)
    if len(time_matches) >= 2:
        result['start_time'], result['end_time'] = time_matches[:2]
    elif len(time_matches) == 1:
        result['start_time'] = time_matches[0]
    
    # 6. LOCATION: Everything AFTER last time that looks like a room/building
    # Find last time position
    last_time_pos = 0
    for time_match in re.finditer(r'\d{1,2}:\d{2}\s*(?:AM|PM)?', text):
        last_time_pos = time_match.end()
    
    # Take text after last time + has building/room indicators
    if last_time_pos > 0:
        after_times = text[last_time_pos:].strip()
        # Room indicators: 3-digit numbers, Bldg, Centre, Hall, etc.
        if re.search(r'\d{3}|[A-Z]{4,}|\bBldg?\b|\bCentre?\b|\bHall?\b|\bRm?\b|SEE_NOTES|T13|L.R.', after_times):
            result['location'] = after_times.strip()[:50]

    return result

def erase_folder_contents(folder_path):
    for filename in os.listdir(folder_path):
        file_path = os.path.join(folder_path, filename)
        try:
            if os.path.isfile(file_path) or os.path.islink(file_path):
                os.unlink(file_path)
            elif os.path.isdir(file_path):
                shutil.rmtree(file_path)
        except Exception as e:
            print('Failed to delete %s. Reason: %s' % (file_path, e))

def output():

    erase_folder_contents('pre/')
    erase_folder_contents('post/')

    image_path = 'assets/sched.png'
    raw_classes = extract_text_from_image(image_path)

    classes = []

    for cls in raw_classes:
        temp = parse_class(cls)
        if is_class_data_complete(temp):
            classes.append(temp)

    with open('assets/parsed_class.json', 'w') as file:
        json.dump(classes, file, indent=4)

    with open('assets/raw_class.json', 'w') as file:
        json.dump(raw_classes, file, indent=4)
    
    print("completed")
    return classes

def is_class_data_complete(class_data):
    """
    Check if a class has all the important data before adding it.

    Args:
        class_data (dict): A dictionary containing class information.

    Returns:
        bool: True if the class has all required fields, False otherwise.
    """
    required_fields = ['day', 'course', 'class_type', 'start_time', 'end_time', 'location']
    
    for field in required_fields:
        if not class_data.get(field):
            return False

    return True

if __name__=="__main__":
    app.run(debug=True)