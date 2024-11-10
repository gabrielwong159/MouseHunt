import re

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    username: str
    password: str
    trap_check: int
    keywords: str = ""

    model_config = SettingsConfigDict(env_prefix="mh_")

    def get_keywords(self) -> list[str]:
        pattern = r",\s*"
        return re.split(pattern, self.keywords)
