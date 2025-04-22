from datetime import datetime

import cloudscraper  # type: ignore
from requests import Session

from src.clients.captcha import CaptchaClient
from src.models.game import UserData
from src.settings import Settings


class GameClient:
    _BASE_URL = "https://www.mousehuntgame.com"
    _LOGIN_URL = f"{_BASE_URL}/managers/ajax/users/session.php"
    _CAPTCHA_URL = f"{_BASE_URL}/managers/ajax/users/puzzle.php"
    _PAGE_URL = f"{_BASE_URL}/managers/ajax/pages/page.php"
    _HORN_URL = f"{_BASE_URL}/turn.php"
    _CAPTCHA_IMAGE_URL = f"{_BASE_URL}/images/puzzleimage.php"

    def __init__(self, settings: Settings, captcha_client: CaptchaClient):
        self._captcha_client = captcha_client
        self._session, self._user_data = self._login(
            settings.mh_username, settings.mh_password
        )

    def refresh_user_data(self) -> None:
        response = self._session.post(
            self._PAGE_URL,
            data={
                "page_class": "Camp",
                "page_arguments[show_loading]": False,
                "last_read_journal_entry": 0,
                "uh": self._unique_hash,
            },
        )
        response.raise_for_status()
        data = response.json()["user"]
        self._user_data = UserData.model_validate(data)

    def horn(self) -> None:
        response = self._session.get(self._HORN_URL)
        response.raise_for_status()

    def request_new_captcha(self) -> None:
        response = self._session.post(
            self._CAPTCHA_URL,
            data={"action": "request_new_code", "uh": self._unique_hash},
        )
        response.raise_for_status()

    def solve_captcha(self, answer: str) -> None:
        response = self._session.post(
            self._CAPTCHA_URL,
            data={"action": "solve", "code": answer, "uh": self._unique_hash},
        )
        response.raise_for_status()

    def get_captcha_image_content(self) -> bytes:
        epoch = datetime.utcfromtimestamp(0)
        milliseconds_since_epoch = int((datetime.now() - epoch).total_seconds() * 1000)
        user_id = self._user_data.user_id
        response = self._session.get(
            self._CAPTCHA_IMAGE_URL,
            params={
                "t": milliseconds_since_epoch,
                "user_id": user_id,
            },
        )
        response.raise_for_status()
        return response.content

    def has_captcha(self) -> bool:
        return self._user_data.has_puzzle

    def _login(self, username: str, password: str) -> tuple[Session, UserData]:
        session = cloudscraper.create_scraper()
        response = session.post(
            self._LOGIN_URL,
            data={
                "action": "loginHitGrab",
                "username": username,
                "password": password,
            },
        )
        response.raise_for_status()
        # we need to return the user_data here too, because we use the info in
        # it for all subsequent calls, including refreshing the user_data
        data = response.json()["user"]
        return session, UserData.model_validate(data)

    @property
    def _unique_hash(self) -> str:
        return self._user_data.unique_hash
