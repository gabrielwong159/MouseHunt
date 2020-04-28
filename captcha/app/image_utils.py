import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image


def download_image(url: str) -> Image:
    response = requests.get(url)
    image_bytes = BytesIO(response.content)
    return Image.open(image_bytes)


def preprocess_image(image: Image) -> Image:
    def kernel(*size):
        return np.ones(size, np.uint8)

    image_arr = np.asarray(image)

    _, binarized = cv2.threshold(image_arr, 200, 255, cv2.THRESH_BINARY)
    inverted = cv2.bitwise_not(binarized)
    enlarged = cv2.resize(inverted, (0, 0), fx=2, fy=2)
    eroded = cv2.erode(enlarged, kernel(3, 3), iterations=2)
    dilated = cv2.dilate(eroded, kernel(2, 2), iterations=1)
    shrunk = cv2.resize(dilated, (0, 0), fx=0.5, fy=0.5)

    return Image.fromarray(shrunk)
