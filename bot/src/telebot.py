import os
import telegram

token = os.environ.get('TELEGRAM_BOT_TOKEN')
chat_id = os.environ.get('TELEGRAM_CHAT_ID')

if token is not None and chat_id is not None:
    telebot = telegram.Bot(token=token)
else:
    telebot = None


def send_message(message: str):
    if telebot is None:
        return
    telebot.send_message(chat_id, message)
