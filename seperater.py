import cv2
import numpy as np
from PIL import Image

# Load original
img = cv2.imread('sched.png')

# Convert to HSV to isolate the green course blocks
hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)

# Tune these bounds if your green shade is different
lower_green = np.array([35, 40, 40])   # H,S,V lower
upper_green = np.array([85, 255, 255]) # H,S,V upper

mask = cv2.inRange(hsv, lower_green, upper_green)

# Find contours (each contour should correspond to one block)
contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL,
                               cv2.CHAIN_APPROX_SIMPLE)

def get_day_index(c):
    x, y, w, h = cv2.boundingRect(c)
    # Divide image width into 7 equal columns (Mon=0, Tue=1, ..., Sun=6)
    col_index = int(x / (img.shape[1] / 7))


    return min(col_index, 6)  # Clamp to 0-6

def contour_key(c):
    x, y, w, h = cv2.boundingRect(c)
    return (x // 10, y)  # Column first, then row

days = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

contours = sorted(contours, key=contour_key)

first = True
for i, c in enumerate(contours, start=1):
    x, y, w, h = cv2.boundingRect(c)

    if first:
        if (250 < x ):
            day = 1
        else:
            day = 0
        first = False
        prev_x = x
    else:
        if (prev_x < x):
            day += 1
        prev_x = x

    # Crop block
    pad = 3
    x0, y0 = max(x - pad, 0), max(y - pad, 0)
    x1, y1 = min(x + w + pad, img.shape[1]), min(y + h + pad, img.shape[0]) 
    block = img[y0:y1, x0:x1]

    cv2.imwrite(f'output/block_{i:02d}_{days[day]}.png', block)