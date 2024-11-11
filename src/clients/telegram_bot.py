import telegram  # type: ignore


class TelegramBotClient:
    def __init__(self, token: str, chat_id: str):
        self._telebot = telegram.Bot(token=token)
        self._chat_id = chat_id

    def send_message(self, message: str):
        self._telebot.send_message(self._chat_id, message)
