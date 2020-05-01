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

    def login(self) -> Session:
        form_data = {
            'action': 'loginHitGrab',
            'username': self.username,
            'password': self.password,
        }

        login_url = f'{Bot.base_url}/managers/ajax/pages/login.php'
        sess = requests.Session()
        res = sess.post(login_url, form_data)

        if not res.ok:
            self.raise_res_error(res)

        return sess

    def get_user_data(self, sess: Session) -> dict:
        form_data = {
            'action': 'loginHitGrab',
            'username': self.username,
            'password': self.password,
        }

        user_url = f'{Bot.base_url}/managers/ajax/users/session.php'
        res = sess.post(user_url, form_data)

        if not res.ok:
            self.raise_res_error(res)

        user_data = json.loads(res.text)['user']
        return user_data

    def home(self, sess: Session) -> Tuple[Session, Response]:
        home_url = Bot.base_url
        req = sess.get(home_url)
        print('home', req.status_code)
        return sess, req

    def horn(self, sess: Session) -> Tuple[Session, Response]:
        horn_url = f'{Bot.base_url}/turn.php'
        req = sess.get(horn_url)
        print('horn', req.status_code)
        return sess, req

    def get_new_entries(self, text: str) -> List[str]:
        soup = BeautifulSoup(text, 'html.parser')
        new_entries = soup.find_all('div', class_='entry')

        entries = []
        for elem in new_entries:
            journal_date = elem.find('div', class_='journaldate').text

            journal_text_elem = elem.find('div', class_='journaltext')
            journal_text = BeautifulSoup(str(journal_text_elem).replace('<br/>', '\n'), 'html.parser').text

            entries.append('\n'.join((journal_date, journal_text)))
        return entries

    def get_captcha_url(self, text: str) -> Optional[str]:
        soup = BeautifulSoup(text, 'html.parser')
        elem = soup.find('div', class_='mousehuntPage-puzzle-form-captcha-image')
        if elem is None:
            return

        pattern = r"background-image:url\('(.*?)'\);"
        match = re.match(pattern, elem['style'])
        try:
            return match.group(1)
        except IndexError:
            return

    def solve_captcha(self, sess: Session, captcha_url: str) -> Tuple[Session, Response]:
        pattern = r'.*?hash=(.*)'
        match = re.match(pattern, captcha_url)
        try:
            unique_hash = match.group(1)
        except IndexError:
            assert False, captcha_url

        answer = requests.get('http://localhost:8080', params={'url': captcha_url}).text
        print('captcha', answer)

        url = 'https://www.mousehuntgame.com/managers/ajax/users/solvePuzzle.php'

        if len(answer) != 5:
            data = {'newpuzzle': True, 'uh': unique_hash}
            sess.post(url, data)
            return self.solve_captcha(sess, captcha_url)
        else:
            data = {'puzzle_answer': answer, 'uh': unique_hash}
            sess.post(url, data)
            return self.home(sess)

    def raise_res_error(self, res: Response):
        raise Exception(res.text)
