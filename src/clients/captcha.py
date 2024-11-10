import string

import cv2
import numpy as np
import pytesseract
from PIL import Image


class CaptchaClient:
    def solve_captcha(self, image: Image.Image) -> str:
        preprocessed_image = self._preprocess_image(image)
        solution = pytesseract.image_to_string(preprocessed_image, config="--psm 6")
        return self._sanitize_solution(solution)

    def _preprocess_image(self, image: Image.Image) -> Image.Image:
        def kernel(size: int) -> np.ndarray:
            return np.ones((size, size), np.uint8)

        image_arr = np.asarray(image)

        _, binarized = cv2.threshold(image_arr, 200, 255, cv2.THRESH_BINARY)
        inverted = cv2.bitwise_not(binarized)
        enlarged = cv2.resize(inverted, (0, 0), fx=2, fy=2)
        eroded = cv2.erode(enlarged, kernel(3), iterations=2)
        dilated = cv2.dilate(eroded, kernel(2), iterations=1)
        shrunk = cv2.resize(dilated, (0, 0), fx=0.5, fy=0.5)

        return Image.fromarray(shrunk)

    def _sanitize_solution(self, solution: str) -> str:
        allowed_characters = set(string.ascii_letters + string.digits)
        filtered_characters = (char for char in solution if char in allowed_characters)
        return "".join(filtered_characters)
