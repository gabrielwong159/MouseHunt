import re

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    mh_username: str
    mh_password: str
    mh_trap_check: int
    mh_keywords: str = ""

    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    def get_keywords(self) -> list[str]:
        pattern = r",\s*"
        return re.split(pattern, self.mh_keywords)
