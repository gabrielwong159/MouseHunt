import os
from typing import Tuple


def get_login() -> Tuple[str, str]:
    try:
        username = os.environ['MH_USERNAME']
    except KeyError:
        username = None

    try:
        password = os.environ['MH_PASSWORD']
    except KeyError:
        password = None

    return username, password


def get_telegram() -> Tuple[str, str]:
    try:
        token = os.environ['TELEGRAM_TOKEN']
    except KeyError:
        token = None

    try:
        chat_id = os.environ['TELEGRAM_CHATID']
    except KeyError:
        chat_id = None

    return token, chat_id


def get_trap_check_timing() -> int:
    try:
        timing = os.environ['TRAP_CHECK']
        return int(timing)
    except (KeyError, ValueError):
        return -1
