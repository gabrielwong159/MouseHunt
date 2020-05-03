import json
import telebot
from bs4 import BeautifulSoup
from bot import Bot


class BotPlus(Bot):
    def update_journal_entries(self):
        all_entries, new_entries = super().update_journal_entries()
        self.check_entries(new_entries)

        user_data = self.get_user_data()
        self.check_bait_empty(user_data)
        self.check_location_setup(user_data)
        self.check_queso_river(user_data)
        self.check_bwrift(user_data)

        return all_entries, new_entries

    def check_entries(self, new_entries):
        for entry in new_entries:
            print(entry, end='\n\n')

        for entry in new_entries[::-1]:
            for keyword in self.keywords:
                if keyword in entry:
                    telebot.send_message(entry)

    def check_bait_empty(self, user_data: dict):
        bait_qty = user_data['bait_quantity']
        if bait_qty > 0:
            return

        is_rift = user_data['environment_name'].endswith('Rift')
        if is_rift:
            self.change_trap('bait', 'brie_string_cheese')
        else:
            self.change_trap('bait', 'gouda_cheese')
        telebot.send_message('bait empty')

    def check_location_setup(self, user_data: dict):
        # iceberg, muridae, living garden
        location = user_data['environment_name']
        base = user_data['base_name']
        bait = user_data['bait_name']

        incorrect_queso = (location == 'Queso River' and
                           base != 'Overgrown Ember Stone Base' and
                           bait != 'Wildfire Queso')
        incorrect_frift = (location == 'Furoma Rift' and
                           base != 'Attuned Enerchi Induction Base')
        if any([incorrect_queso, incorrect_frift]):
            telebot.send_message(f'Not using {base} in {location}')

    def check_queso_river(self, user_data: dict):
        if self.get_location(user_data) != 'Queso River':
            return

        soup = self.get_environment_hud(user_data)
        is_tonic_active = soup.find('a', class_='quesoHUD-wildTonic-button selected') is not None
        if is_tonic_active:
            url = 'https://www.mousehuntgame.com/managers/ajax/environment/queso_canyon.php'
            data = {
                'action': 'toggle_wild_tonic',
                'uh': self.unique_hash,
                'last_read_journal_entry_id': self.last_read_journal_entry_id,
            }
            self.sess.post(url, data)

    def check_bwrift(self, user_data: dict):
        if self.get_location(user_data) != 'Bristle Woods Rift':
            return

        url = 'https://www.mousehuntgame.com/managers/ajax/environment/rift_bristle_woods.php'

        soup = self.get_environment_hud(user_data)
        is_bwrift_entrance = soup.find('div', class_='riftBristleWoodsHUD entrance_chamber open')
        if is_bwrift_entrance:
            data = {
                'action': 'enter_portal',
                'portal_type': 'basic_chamber',
                'uh': self.unique_hash,
                'last_read_journal_entry_id': self.last_read_journal_entry_id,
            }
            self.sess.post(url, data=data)
            return

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

    def get_location(self, user_data: dict) -> str:
        return user_data['environment_name']

    def get_environment_hud(self, user_data: dict) -> BeautifulSoup:
        hud = user_data['enviroment_atts']['environment_hud']
        return BeautifulSoup(hud, 'html.parser')
