from datetime import datetime

import cloudscraper  # type: ignore
from requests import Session
from requests.exceptions import JSONDecodeError

from src.clients.captcha import CaptchaClient
from src.models.game import UserData
from src.settings import Settings


class GameClient:
    _BASE_URL = "https://www.mousehuntgame.com"
    _LOGIN_URL = f"{_BASE_URL}/managers/ajax/users/session.php"
    _CAPTCHA_URL = f"{_BASE_URL}/managers/ajax/users/puzzle.php"
    _GET_TRAP_COMPONENTS_URL = f"{_BASE_URL}/managers/ajax/users/gettrapcomponents.php"
    _CHANGE_TRAP_URL = f"{_BASE_URL}/managers/ajax/users/changetrap.php"
    _CRAFTING_URL = f"{_BASE_URL}/managers/ajax/users/crafting.php"
    _PURCHASE_ITEM_URL = f"{_BASE_URL}/managers/ajax/purchases/itempurchase.php"
    _PAGE_URL = f"{_BASE_URL}/managers/ajax/pages/page.php"
    _BWRIFT_URL = f"{_BASE_URL}/managers/ajax/environment/rift_bristle_woods.php"
    _VRIFT_URL = f"{_BASE_URL}/managers/ajax/environment/rift_valour.php"
    _MOUNTAIN_URL = f"{_BASE_URL}/managers/ajax/environment/mountain.php"
    _SB_FACTORY_URL = f"{_BASE_URL}/managers/ajax/events/birthday_factory.php"
    _HALLOWEEN_URL = f"{_BASE_URL}/managers/ajax/events/halloween_boiling_cauldron.php"
    _ADVENT_CALENDAR_URL = f"{_BASE_URL}/managers/ajax/events/advent_calendar.php"
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

    def get_trap_components(self, classification_type: str) -> set[str]:
        response = self._session.post(
            self._GET_TRAP_COMPONENTS_URL,
            data={"classification": classification_type, "uh": self._unique_hash},
        )
        components = response.json()["components"]
        return {component["type"] for component in components}

    def change_trap(self, classification_type: str, item_key: str) -> None:
        response = self._session.post(
            self._CHANGE_TRAP_URL,
            data={classification_type: item_key, "uh": self._unique_hash},
        )
        response.raise_for_status()

    def purchase_item(self, item_key: str, quantity: int) -> None:
        response = self._session.post(
            self._PURCHASE_ITEM_URL,
            data={
                "buy": 1,
                "type": item_key,
                "quantity": quantity,
                "is_kings_cart_item": 0,
                "uh": self._unique_hash,
            },
        )
        response.raise_for_status()

    def try_craft_item(self, crafting_items: dict, quantity: int) -> bool:
        response = self._session.post(
            self._CRAFTING_URL,
            data={**crafting_items, "craftQty": quantity, "uh": self._unique_hash},
        )
        if not response.ok:
            return False
        try:
            return response.json()["success"] == 1
        except JSONDecodeError:
            return False
        except KeyError:
            return False

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

    def enter_bwrift(self) -> None:
        response = self._session.post(
            self._BWRIFT_URL,
            data={
                "action": "enter_portal",
                "portal_type": "basic_chamber",
                "uh": self._unique_hash,
            },
        )
        response.raise_for_status()

    def toggle_vrift_fire(self) -> None:
        response = self._session.post(
            self._VRIFT_URL,
            data={"action": "toggle_fuel", "uh": self._unique_hash},
        )
        response.raise_for_status()

    def claim_mountain_boulder(self) -> None:
        response = self._session.post(
            self._MOUNTAIN_URL,
            data={"action": "claim_reward", "uh": self._unique_hash},
        )
        response.raise_for_status()

    def claim_sb_factory_crate(self) -> None:
        response = self._session.post(
            self._SB_FACTORY_URL,
            data={"action": "claim_reward", "uh": self._unique_hash},
        )
        response.raise_for_status()

    def change_sb_factory_room(self, room: str) -> None:
        response = self._session.post(
            self._SB_FACTORY_URL,
            data={"action": "pick_room", "room": room, "uh": self._unique_hash},
        )
        response.raise_for_status()

    def upgrade_sb_factory_room(self, room: str) -> None:
        response = self._session.post(
            self._SB_FACTORY_URL,
            data={"action": "upgrade_room", "room": room, "uh": self._unique_hash},
        )
        response.raise_for_status()

    def brew_halloween_recipe(self, recipe_type: str, slot: int) -> None:
        response = self._session.post(
            self._HALLOWEEN_URL,
            data={
                "action": "brew_recipe",
                "recipe_type": recipe_type,
                "slot": slot,
                "uh": self._unique_hash,
            },
        )
        response.raise_for_status()

    # TODO: not sure what the data type of `gift` is
    def claim_advent_calendar_gift(self, gift) -> None:
        response = self._session.post(
            self._ADVENT_CALENDAR_URL,
            data={"action": "claim", "gift": gift, "uh": self._unique_hash},
        )
        response.raise_for_status()

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
