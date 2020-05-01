import json
import re
import requests
from requests import Session, Response
from bs4 import BeautifulSoup
from typing import Optional, List, Tuple


class Bot(object):
    base_url = 'https://www.mousehuntgame.com'

    def __init__(self, username: str, password: str, trap_check: int):
        self.username = username
        self.password = password
        self.trap_check = trap_check
        self.journal_entries = []

        self.sess = self.login()
        self.get_user_data()  # required after every login
        self.update_journal_entries()

    def login(self) -> Session:
        login_url = f'{Bot.base_url}/managers/ajax/pages/login.php'
        form_data = {
            'action': 'loginHitGrab',
            'username': self.username,
            'password': self.password,
        }

        sess = requests.Session()
        res = sess.post(login_url, form_data)
        if not res.ok:
            self.raise_res_error(res)
        return sess

    def get_user_data(self) -> dict:
        user_url = f'{Bot.base_url}/managers/ajax/users/session.php'
        form_data = {
            'action': 'loginHitGrab',
            'username': self.username,
            'password': self.password,
        }
        res = self.sess.post(user_url, form_data)
        if not res.ok:
            self.raise_res_error(res)
        user_data = json.loads(res.text)['user']
        return user_data

    def horn(self) -> Response:
        horn_url = f'{Bot.base_url}/turn.php'
        res = self.sess.get(horn_url)
        if not res.ok:
            self.raise_res_error(res)
        return res

    def get_page_html(self) -> BeautifulSoup:
        self.check_and_solve_captcha()

        home_url = Bot.base_url
        res = self.sess.get(home_url)
        if not res.ok:
            self.raise_res_error(res)
        return BeautifulSoup(res.text, 'html.parser')

    def update_journal_entries(self) -> Tuple[List[str], List[str]]:
        curr = self.journal_entries
        new = self.get_journal_entries()

        ptr = 0
        while ptr < len(new) and new[ptr] not in curr:
            ptr += 1
        diff = new[:ptr]

        self.journal_entries = new
        return new, diff

    def get_journal_entries(self) -> List[str]:
        soup = self.get_page_html()
        journal_entries = soup.find_all('div', class_='entry')

        entries = []
        for elem in journal_entries:
            journal_date = elem.find('div', class_='journaldate').text

            journal_text_elem = elem.find('div', class_='journaltext')
            journal_text = BeautifulSoup(str(journal_text_elem).replace('<br/>', '\n'), 'html.parser').text

            entries.append('\n'.join((journal_date, journal_text)))
        return entries

    def check_and_solve_captcha(self) -> bool:
        user_data = self.get_user_data()
        has_captcha = user_data['has_puzzle']
        if not has_captcha:
            return False

        captcha_url = self.get_captcha_url()
        if captcha_url is None:
            return False

        unique_hash = user_data['unique_hash']
        self.solve_captcha(captcha_url, unique_hash)
        self.check_and_solve_captcha()  # if wrong answer, image will change, solve again

    def get_captcha_url(self) -> Optional[str]:
        soup = self.get_page_html()
        elem = soup.find('div', class_='mousehuntPage-puzzle-form-captcha-image')
        if elem is None:
            return

        pattern = r"background-image:url\('(.*?)'\);"
        match = re.match(pattern, elem['style'])
        try:
            return match.group(1)
        except IndexError:
            return

    def solve_captcha(self, captcha_url: str, unique_hash: str) -> Response:
        answer = requests.get('http://localhost:8080', params={'url': captcha_url}).text
        print('captcha', answer)

        url = f'{Bot.base_url}/managers/ajax/users/solvepuzzle.php'

        if len(answer) != 5:  # if bad solution, change image and solve again
            data = {'newpuzzle': True, 'uh': unique_hash}
            self.sess.post(url, data)
            return self.solve_captcha(captcha_url, unique_hash)
        else:
            data = {'puzzle_answer': answer, 'uh': unique_hash}
            res = self.sess.post(url, data)
            return res

    def raise_res_error(self, res: Response):
        raise Exception(res.text)
