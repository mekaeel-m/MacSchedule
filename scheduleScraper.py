import re
import cv2
import pytesseract
from matplotlib import pyplot as plt
import numpy as np
from PIL import Image
import json
from flask import Flask, request, jsonify
import os
import shutil
from flask_cors import CORS

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "http://127.0.0.1:5500"}})

UPLOAD_FOLDER = 'assets/'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def extract_text_from_image(image_path):
    # Load original
    img = cv2.imread(image_path)

    # Convert to HSV to isolate the green course blocks
    hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

    # Tune these bounds if your green shade is different
    lower_green = np.array([41, 75, 190])
    upper_green = np.array([50, 140, 255])

    mask = cv2.inRange(hsv, lower_green, upper_green)

    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1,1))
    mask = cv2.morphologyEx(mask, cv2.MORPH_OPEN, kernel, iterations=1)
    mask = cv2.morphologyEx(mask, cv2.MORPH_CLOSE, kernel, iterations=2)


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

        if w < 50 or h < 50:
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
    
    # 3. CLASS_CODE: -C01, -T02, TO2
    code_match = re.search(r'-?\s*(C|T|L|c)\d{2}|-?\s*TO\d|-?\s*(C|T|L|c)*(O|o|0)\d{1}|-?\s*(C|T|L|c)*(O|0|o)*(t|a)', text)
    # code_match = re.search(r'-?\s*(C|T|L|c)\d{2}|-?\s*TO\d|-?\s*(C|T|L|c)O\d{1}|-?\s*(C|T|L|c)Ot|-?\s*(C|T|L|c)0t', text)
    if code_match:
        result['class_code'] = code_match.group(0).strip('- ').replace('t', '1').replace('a', '4').upper().replace('O', '0')
    
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
        # Room indicators: 3-digit numbers, BLDG, CENTRE, HALL, etc.
        if re.search(r'\d{3}|[A-Z]{4,}|\bBLDG?\b|\bCENTRE?\b|\bHALL?\b|\bRM?\b', after_times):
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