import json
from telegram.ext import Updater

with open("telegram_config.json", "r") as f:
    telegram_config = json.loads(f.read())
    telegram_token = telegram_config["token"]
    chat_id = telegram_config["chatid"]

updater = Updater(token=telegram_token)
bot = updater.dispatcher.bot

def notify_message(message:str):
    bot.send_message(chat_id, message)

def notify_messages(messages:list):
    for message in messages: notify_message(message)
