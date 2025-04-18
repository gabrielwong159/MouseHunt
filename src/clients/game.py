import cloudscraper  # type: ignore
from requests import Session

from src.clients.captcha import CaptchaClient
from src.models.game import UserData
from src.settings import Settings


class GameClient:
    _BASE_URL = "https://www.mousehuntgame.com"
    _LOGIN_URL = f"{_BASE_URL}/managers/ajax/users/session.php"
    _PAGE_URL = f"{_BASE_URL}/managers/ajax/pages/page.php"

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
