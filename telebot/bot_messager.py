from telegram.ext import Updater


class BotMessager(object):
    def __init__(self, token, chat_id):
        updater = Updater(token=token)
        self.bot = updater.dispatcher.bot
        self.chat_id = chat_id

    def notify_message(self, message: str):
        self.bot.send_message(self.chat_id, message)
