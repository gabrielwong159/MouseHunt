import pytesseract
import string
from image_utils import download_image, preprocess_image


def solve_captcha(url: str) -> str:
    image = download_image(url)
    image = preprocess_image(image)

    solution = pytesseract.image_to_string(image, config='--psm 6')
    return sanitize_solution(solution)


def sanitize_solution(solution: str) -> str:
    allowed_characters = string.ascii_letters + string.digits
    filtered_characters = (char for char in solution if char in allowed_characters)
    return ''.join(filtered_characters)
