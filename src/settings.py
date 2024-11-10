import re

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    captcha_host: str = Field(default="localhost", alias="captcha_host")
    captcha_port: str = Field(default="8080", alias="captcha_port")

    username: str
    password: str
    trap_check: int
    keywords: str = ""

    model_config = SettingsConfigDict(env_prefix="mh_")

    def get_keywords(self) -> list[str]:
        pattern = r",\s*"
        return re.split(pattern, self.keywords)

    def get_captcha_url(self) -> str:
        return f"http://{self.captcha_host}:{self.captcha_port}"
