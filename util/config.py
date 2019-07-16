import os


def get_login_config():
    username = os.environ['MH_USERNAME']
    password = os.environ['MH_PASSWORD']
    return username, password


def get_telegram_config():
    token = os.environ['TELEGRAM_TOKEN']
    chat_id = os.environ['TELEGRAM_CHATID']
    return token, chat_id
