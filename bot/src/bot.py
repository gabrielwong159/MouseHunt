import json
import re
import requests
from requests import Session, Response
from bs4 import BeautifulSoup
from typing import List, Tuple


class Bot(object):
    base_url = 'https://www.mousehuntgame.com'

    def __init__(self, username: str, password: str, trap_check: int, keywords: List[str] = None):
        self.username = username
        self.password = password
        self.trap_check = trap_check
        self.journal_entries = []

        self.sess = None
        self.refresh_sess()
        self.update_journal_entries()

        self.keywords = [] if keywords is None else keywords

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

    def refresh_sess(self):
        self.sess = self.login()
        self.get_user_data()

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

    def horn(self):
        horn_url = f'{Bot.base_url}/turn.php'
        res = self.sess.get(horn_url)
        if not res.ok:
            self.raise_res_error(res)

    def get_page_html(self) -> BeautifulSoup:
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

    def check_and_solve_captcha(self):
        user_data = self.get_user_data()
        has_captcha = user_data['has_puzzle']
        if not has_captcha:
            return

        unique_hash = user_data['unique_hash']
        self.solve_captcha(unique_hash)
        self.check_and_solve_captcha()  # if wrong answer, image will change, solve again

    def solve_captcha(self, unique_hash: str):
        captcha_url = self.get_captcha_url()
        answer = requests.get('http://localhost:8080', params={'url': captcha_url}).text
        print('captcha', answer)

        url = f'{Bot.base_url}/managers/ajax/users/solvePuzzle.php'
        if len(answer) != 5:
            data = {'newpuzzle': True, 'uh': unique_hash}
            self.sess.post(url, data)
            return self.solve_captcha(unique_hash)

        data = {'puzzle_answer': answer, 'uh': unique_hash}
        self.sess.post(url, data)

    def get_captcha_url(self) -> str:
        soup = self.get_page_html()
        elem = soup.find('div', class_='mousehuntPage-puzzle-form-captcha-image')

        pattern = r"background-image:url\('(.*?)'\);"
        match = re.match(pattern, elem['style'])
        return match.group(1)

    def raise_res_error(self, res: Response):
        raise Exception(res.text)
