import logging
from io import BytesIO

from PIL import Image
from bs4 import BeautifulSoup
from requests import Response

from src.clients.captcha import CaptchaClient
from src.clients.game import GameClient
from src.settings import Settings

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %T",
)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class Bot(object):
    _MAX_CAPTCHA_ATTEMPTS = 5

    base_url = "https://www.mousehuntgame.com"

    def __init__(self, settings: Settings):
        self._captcha_client = CaptchaClient()
        self._game_client = GameClient(settings, self._captcha_client)
        self.logger = logging.getLogger(__name__)
        self.username = settings.mh_username
        self.password = settings.mh_password
        self.trap_check = settings.mh_trap_check
        self.keywords = settings.get_keywords()

        user_data = self.get_user_data()
        self.name = user_data["username"]
        self.unique_hash = user_data["unique_hash"]
        self.user_id = user_data["user_id"]

        self.journal_entries: list[str] = []
        self.update_journal_entries()

    def get_user_data(self) -> dict:
        self._game_client.refresh_user_data()
        return self._game_client._user_data.model_dump()

    def horn(self):
        self._game_client.horn()

    def get_page_soup(self) -> BeautifulSoup:
        home_url = Bot.base_url
        res = self._game_client._session.get(home_url)
        if not res.ok:
            self.raise_res_error(res)
        return BeautifulSoup(res.text, "html.parser")

    def update_journal_entries(self) -> tuple[list[str], list[str]]:
        curr = self.journal_entries
        new = self.get_journal_entries()

        if curr is None:  # skip diff check at initial startup
            diff: list[str] = []
        else:
            ptr = 0
            while ptr < len(new) and new[ptr] not in curr:
                ptr += 1
            diff = new[:ptr]

        self.journal_entries = new
        return new, diff

    def get_journal_entries(self) -> list[str]:
        self.check_and_solve_captcha()
        soup = self.get_page_soup()
        journal_entries = soup.find_all("div", class_="entry")

        entries = []
        for elem in journal_entries:
            journal_date = elem.find("div", class_="journaldate").text

            journal_text_elem = elem.find("div", class_="journaltext")
            journal_text = BeautifulSoup(
                str(journal_text_elem).replace("<br/>", "\n"), "html.parser"
            ).text

            entries.append("\n".join((journal_date, journal_text)))
        return entries

    def check_and_solve_captcha(self):
        for _ in range(self._MAX_CAPTCHA_ATTEMPTS):
            self._game_client.refresh_user_data()
            if self._game_client.has_captcha():
                self._solve_captcha()
            else:
                break
        else:
            raise Exception("Exceeded number of captcha attempts")

    def _solve_captcha(self):
        image = Image.open(BytesIO(self._game_client.get_captcha_image_content()))
        answer = self._captcha_client.solve_captcha(image)
        if len(answer) != 5:
            self._game_client.request_new_captcha()
        else:
            self._game_client.solve_captcha(answer)

    def raise_res_error(self, res: Response):
        raise Exception(res.text)
