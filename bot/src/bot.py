import logging
from datetime import datetime
from typing import List, Tuple

import requests
from bs4 import BeautifulSoup
from requests import Response, Session

from settings import Settings

logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    datefmt="%Y-%m-%d %T",
)
logging.getLogger("urllib3").setLevel(logging.WARNING)


class Bot(object):
    base_url = "https://www.mousehuntgame.com"

    def __init__(self, settings: Settings):
        self.logger = logging.getLogger(__name__)
        self.settings = settings
        self.username = settings.username
        self.password = settings.password
        self.trap_check = settings.trap_check
        self.captcha_solver_url = settings.get_captcha_url()
        self.keywords = settings.get_keywords()

        self.sess = requests.Session()
        user_data = self.refresh_sess()
        self.name = user_data["username"]
        self.unique_hash = user_data["unique_hash"]
        self.user_id = user_data["user_id"]

        self.journal_entries = None
        self.update_journal_entries()

    def refresh_sess(self) -> dict:
        self.sess = requests.Session()
        user_url = f"{Bot.base_url}/managers/ajax/users/session.php"
        form_data = {
            "action": "loginHitGrab",
            "username": self.username,
            "password": self.password,
        }
        response = self.sess.post(user_url, form_data)
        if not response.ok:
            self.raise_res_error(response)
        return response.json()["user"]

    def get_user_data(self) -> dict:
        url = f"{self.base_url}/managers/ajax/pages/page.php"
        data = {
            "page_class": "Camp",
            "page_arguments[show_loading]": False,
            "last_read_journal_entry": 0,
            "uh": self.unique_hash,
        }
        response = self.sess.post(url, data)
        if not response.ok:
            self.raise_res_error(response)
        return response.json()["user"]

    def horn(self):
        horn_url = f"{Bot.base_url}/turn.php"
        res = self.sess.get(horn_url)
        if not res.ok:
            self.raise_res_error(res)
        self.logger.info("Horn")

    def get_page_soup(self) -> BeautifulSoup:
        home_url = Bot.base_url
        res = self.sess.get(home_url)
        if not res.ok:
            self.raise_res_error(res)
        return BeautifulSoup(res.text, "html.parser")

    def update_journal_entries(self) -> Tuple[List[str], List[str]]:
        curr = self.journal_entries
        new = self.get_journal_entries()

        if curr is None:  # skip diff check at initial startup
            diff = []
        else:
            ptr = 0
            while ptr < len(new) and new[ptr] not in curr:
                ptr += 1
            diff = new[:ptr]

        self.journal_entries = new
        return new, diff

    def get_journal_entries(self) -> List[str]:
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
        answer = requests.get(self.captcha_solver_url, params={"url": captcha_url}).text
        self.logger.info(f"captcha attempt: {captcha_url=} {answer=}")

        url = f"{Bot.base_url}/managers/ajax/users/puzzle.php"
        if len(answer) != 5:
            data = {"action": "request_new_code", "uh": self.unique_hash}
            self.logger.info("requesting new captcha")
            self.sess.post(url, data)
            return self.solve_captcha()

        data = {
            "action": "solve",
            "code": answer,
            "uh": self.unique_hash,
        }
        self.sess.post(url, data)

    def get_captcha_url(self) -> str:
        epoch = datetime.utcfromtimestamp(0)
        milliseconds_since_epoch = int((datetime.now() - epoch).total_seconds() * 1000)
        return f"{self.base_url}/images/puzzleimage.php?t={milliseconds_since_epoch}&user_id={self.user_id}"

    def raise_res_error(self, res: Response):
        raise Exception(res.text)
