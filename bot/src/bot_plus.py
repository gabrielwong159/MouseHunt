import telebot
from bot import Bot


class BotPlus(Bot):
    def update_journal_entries(self):
        all_entries, new_entries = super().update_journal_entries()

        self.check_entries(new_entries)

        return all_entries, new_entries

    def check_entries(self, new_entries):
        for entry in new_entries:
            print(entry, end='\n\n')

        for entry in new_entries[::-1]:
            for keyword in self.keywords:
                if keyword in entry:
                    telebot.send_message(entry)

