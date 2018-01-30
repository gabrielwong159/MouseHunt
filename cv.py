import os
import string
import time
import requests
import cv2
import numpy as np
import pytesseract
from io import BytesIO
from PIL import Image

temp_file = "captcha.png"

def process_captcha():
    image = cv2.imread(temp_file, 0)
    
    cv2.imwrite(temp_file, process(image))

def process(image):
    def kernel(size): return np.ones(size, np.uint8)
    
    _, threshold = cv2.threshold(image, 200, 255, cv2.THRESH_BINARY)
    threshold = cv2.bitwise_not(threshold)
    enlarged = cv2.resize(threshold, (0,0), fx=2, fy=2)

    eroded = cv2.erode(enlarged, kernel((3,3)), iterations=2)
    dilated = cv2.dilate(eroded, kernel((2,2)), iterations=1)

    shrunk = cv2.resize(dilated, (0,0), fx=0.5, fy=0.5)
    
    return shrunk

def sanitize(s):
    allowed_characters = string.ascii_letters + string.digits
    l = filter(lambda c: c in allowed_characters, list(s))
    return "".join(l)

def read_captcha(url):
    # fetch image from url and save it to file
    response = requests.get(url)
    image = Image.open(BytesIO(response.content))
    image.save(temp_file)

    process_captcha() # image preprocessing with opencv
    
    # ocr with tesseract
    text = pytesseract.image_to_string(Image.open(temp_file))
    
    os.remove(temp_file)
    return sanitize(text) 

if __name__ == "__main__":
    folder_name = "captcha/sample"
    for file in os.listdir(folder_name):
        file_name = os.path.join(folder_name, file)
        image = cv2.imread(file_name, 0)
        cv2.imwrite(temp_file, image)

        process_captcha()
        text = pytesseract.image_to_string(Image.open(temp_file))
        print(sanitize(text))
