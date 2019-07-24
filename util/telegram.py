from telegram.ext import Updater
from . import config


bot = None
telegram_token, chat_id = config.get_telegram()
if telegram_token is None:
    print('Telegram token not found in config, will not use Telegram bot')
elif chat_id is None:
    print('Telegram chat ID not found in config, will not use Telegram bot')
else:
    updater = Updater(token=telegram_token)
    bot = updater.dispatcher.bot


def notify_message(message: str):
    if bot is None:
        return

    bot.send_message(chat_id, message)


def notify_messages(messages: list):
    for message in messages:
        notify_message(message)
