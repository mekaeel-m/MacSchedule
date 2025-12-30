import cv2
import pytesseract
from matplotlib import pyplot as plt

# Ensure the image path is correct and the file exists
image_path = "sched.png"  # Update to the correct path if needed

# Load the image
image = cv2.imread(image_path)
if image is None:
    raise FileNotFoundError(f"Image not found at path: {image_path}")

# Convert the image to RGB format
image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
print("Grayscale Image:")
cv2.imshow('image', gray)

extracted_text = pytesseract.image_to_string(gray)
print(" Extracted Text:\n")
print(extracted_text)