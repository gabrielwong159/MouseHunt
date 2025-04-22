import logging
from datetime import datetime
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
        user_data = self.get_user_data()
        has_captcha = user_data["has_puzzle"]
        if not has_captcha:
            return

        self.solve_captcha()
        self.check_and_solve_captcha()  # if wrong answer, image will change, solve again

    def solve_captcha(self):
        captcha_url = self.get_captcha_url()
        response = self._game_client._session.get(captcha_url)
        if not response.ok:
            self.raise_res_error(response)

        image = Image.open(BytesIO(response.content))
        answer = self._captcha_client.solve_captcha(image)
        self.logger.info(f"captcha attempt: {captcha_url=} {answer=}")

        url = f"{Bot.base_url}/managers/ajax/users/puzzle.php"
        if len(answer) != 5:
            data = {"action": "request_new_code", "uh": self.unique_hash}
            self.logger.info("requesting new captcha")
            self._game_client._session.post(url, data)
            return self.solve_captcha()

        data = {
            "action": "solve",
            "code": answer,
            "uh": self.unique_hash,
        }
        self._game_client._session.post(url, data)

    def get_captcha_url(self) -> str:
        epoch = datetime.utcfromtimestamp(0)
        milliseconds_since_epoch = int((datetime.now() - epoch).total_seconds() * 1000)
        return f"{self.base_url}/images/puzzleimage.php?t={milliseconds_since_epoch}&user_id={self.user_id}"

    def raise_res_error(self, res: Response):
        raise Exception(res.text)
