import string
import requests
import cv2
import numpy as np
import pytesseract
from io import BytesIO
from PIL import Image


def read_captcha(url: str) -> str:
    response = requests.get(url)
    image_bytes = BytesIO(response.content)

    image = Image.open(image_bytes)
    image = process(image)

    text = pytesseract.image_to_string(image)
    return sanitize(text)


def process(image: Image) -> Image:
    def kernel(size):
        return np.ones(size, np.uint8)

    image_arr = np.asarray(image)

    _, threshold = cv2.threshold(image_arr, 200, 255, cv2.THRESH_BINARY)
    inv = cv2.bitwise_not(threshold)

    enlarged = cv2.resize(inv, (0, 0), fx=2, fy=2)

    eroded = cv2.erode(enlarged, kernel([3, 3]), iterations=2)
    dilated = cv2.dilate(eroded, kernel([2, 2]), iterations=1)

    shrunk = cv2.resize(dilated, (0, 0), fx=0.5, fy=0.5)
    return Image.fromarray(shrunk)


def sanitize(s: str) -> str:
    allowed_characters = string.ascii_letters + string.digits
    filtered_characters = [char for char in s if char in allowed_characters]
    return ''.join(filtered_characters)
