from telegram.ext import Updater
from . import config

telegram_token, chat_id = config.get_telegram_config()
updater = Updater(token=telegram_token)
bot = updater.dispatcher.bot


def notify_message(message: str):
    bot.send_message(chat_id, message)


def notify_messages(messages: list):
    for message in messages:
        notify_message(message)
