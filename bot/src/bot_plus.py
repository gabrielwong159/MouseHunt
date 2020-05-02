import json
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

    def check_bait_empty(self):
        user_data = self.get_user_data()
        bait_qty = user_data['bait_quantity']
        if bait_qty > 0:
            return

        is_rift = user_data['environment_name'].endswith('Rift')
        if is_rift:
            self.change_trap('bait', 'brie_string_cheese')
        else:
            self.change_trap('bait', 'gouda_cheese')
        telebot.send_message('bait empty')

    def change_trap(self, classification: str, item_key: str):
        assert classification in ['weapon', 'base', 'trinket', 'bait', 'skin']

        url = f'{Bot.base_url}/managers/ajax/users/gettrapcomponents.php'
        data = {'unique_hash': self.unique_hash, 'classification': classification}
        res = self.sess.post(url, data=data)

        components = json.loads(res)['components']
        available_components = [component['type'] for component in components]
        if item_key not in available_components:
            telebot.send_message(f'cannot find {classification}: {item_key}')
            return

        url = f'{Bot.base_url}/managers/ajax/users/changetrap.php'
        data = {'uh': self.unique_hash, classification: item_key}
        self.sess.post(url, data=data)
