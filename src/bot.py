import logging
import uuid
from io import BytesIO
from typing import Optional

from PIL import Image
from bs4 import BeautifulSoup
from requests import Response

from src.clients.captcha import CaptchaClient
from src.clients.game import GameClient
from src.clients.webhook import WebhookClient
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

        self._webhook_client: Optional[WebhookClient]
        if settings.mousehunt_webhook_url and settings.mousehunt_webhook_secret:
            self._webhook_client = WebhookClient(
                url=settings.mousehunt_webhook_url,
                secret=settings.mousehunt_webhook_secret,
            )
        else:
            self._webhook_client = None
            self.logger.warning(
                "MOUSEHUNT_WEBHOOK_URL or MOUSEHUNT_WEBHOOK_SECRET unset; "
                "skipping post-horn webhook"
            )

        user_data = self.get_user_data()
        self.name = user_data["username"]
        self.unique_hash = user_data["unique_hash"]
        self.user_id = user_data["user_id"]

        # Hunts the game has recorded for us as of the last event we sent. Any
        # advance past this is a hunt no notification accounted for.
        self._notified_active_turns: int = user_data["num_active_turns"]

        self.journal_entries: list[str] = []
        self.update_journal_entries()

        self._notify(event_id=f"startup-{uuid.uuid4()}")

    def refresh(self) -> None:
        self._game_client.refresh()

    def get_user_data(self) -> dict:
        self._game_client.refresh_user_data()
        return self._game_client._user_data.model_dump()

    def _notify(self, event_id: str) -> None:
        if self._webhook_client is not None:
            self._webhook_client.notify_horn(event_id=event_id)

    def horn(self):
        self._game_client.horn()
        self._notify(event_id=f"horn-{uuid.uuid4()}")
        self._sync_active_turns()

    def post_trap_check(self):
        # Notify first: the webhook marks the trap check itself, and shouldn't be
        # held up (or suppressed on failure) by the journal update behind it.
        self._notify(event_id=f"trap-{uuid.uuid4()}")
        self._sync_active_turns()
        self.update_journal_entries()

    def notify_missed_hunts(self) -> None:
        """Notify for hunts neither horn() nor post_trap_check() accounted for.

        The game checks the trap on its own schedule, and hunts also come from
        the browser and app, so a hunt lands without the bot causing one. Those
        reach the journal but nothing tells the webhook, so compare the game's
        hunt counter against the last one we sent an event for.

        Reads the counter the caller last fetched rather than refreshing, so
        the decision uses the same state the caller acted on.
        """
        current = self._game_client._user_data.num_active_turns
        missed = current - self._notified_active_turns
        if missed <= 0:
            return

        self.logger.info("%d hunt(s) since the last notification", missed)
        # One event for the whole gap: the receiver re-reads full game state, so
        # a run per missed hunt would repeat the same work.
        self._notify(event_id=f"hunt-{current}")
        self._notified_active_turns = current

    def _sync_active_turns(self) -> None:
        # Re-read after a hunt we notified for, so notify_missed_hunts does not
        # report it a second time.
        self._game_client.refresh_user_data()
        self._notified_active_turns = self._game_client._user_data.num_active_turns

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
        self._game_client.request_new_captcha()
        image = Image.open(BytesIO(self._game_client.get_captcha_image_content()))
        answer = self._captcha_client.solve_captcha(image)
        if len(answer) == 5:
            self._game_client.solve_captcha(answer)

    def raise_res_error(self, res: Response):
        raise Exception(res.text)
