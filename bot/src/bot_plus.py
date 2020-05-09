import json
import telebot
from bs4 import BeautifulSoup
from bot import Bot


class BotPlus(Bot):
    def horn(self):
        user_data = self.get_user_data()
        self.check_queso_river(user_data)
        self.check_vrift(user_data)
        return super().horn()

    def update_journal_entries(self):
        all_entries, new_entries = super().update_journal_entries()
        self.check_entries(new_entries)

        user_data = self.get_user_data()
        self.check_bait_empty(user_data)
        self.check_location_setup(user_data)
        self.check_bwrift(user_data)
        self.check_mountain(user_data)

        return all_entries, new_entries

    def check_entries(self, new_entries):
        for entry in new_entries[::-1]:
            print(entry, end='\n\n')
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
            message = f'Not using {base} in {location}'
            print(message)
            telebot.send_message(message)

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
            }
            self.sess.post(url, data)
            print('deactivated tonic in queso river')

    def check_bwrift(self, user_data: dict):
        if self.get_location(user_data) != 'Bristle Woods Rift':
            return

        soup = self.get_environment_hud(user_data)
        is_bwrift_entrance = soup.find('div', class_='riftBristleWoodsHUD entrance_chamber open') is not None
        if is_bwrift_entrance:
            url = 'https://www.mousehuntgame.com/managers/ajax/environment/rift_bristle_woods.php'
            data = {
                'action': 'enter_portal',
                'portal_type': 'basic_chamber',
                'uh': self.unique_hash,
            }
            self.sess.post(url, data=data)
            print('entered bwrift entrance')

    def check_vrift(self, user_data:dict):
        if self.get_location(user_data) != 'Valour Rift':
            return

        floor = int(user_data['enviroment_atts']['floor'])
        is_fire_active = user_data['enviroment_atts']['is_fuel_enabled']
        n_fire = user_data['enviroment_atts']['items']['rift_gauntlet_fuel_stat_item']['quantity']

        def toggle_fire():
            url = 'https://www.mousehuntgame.com/managers/ajax/environment/rift_valour.php'
            data = {
                'action': 'toggle_fuel',
                'uh': self.unique_hash,
            }
            self.sess.post(url, data=data)

        if floor % 8 != 0:
            if is_fire_active:
                toggle_fire()
                message = f'At floor {floor}, switching off fire'
            else:
                message = None
        else:
            if is_fire_active:
                message = f'At floor {floor}, fire already active'
            else:
                if n_fire == 0:
                    message = f'At floor {floor}, no fire to activate'
                else:
                    toggle_fire()
                    message = f'At floor {floor}, {n_fire} fire available, activating fire'

        if message is not None:
            print(message)
            telebot.send_message(message)

    def check_mountain(self, user_data: dict):
        if self.get_location(user_data) != 'Mountain':
            return

        soup = self.get_environment_hud(user_data)
        is_boulder_claimable = soup.find('div', class_='mountainHUD-boulderContainer can_claim') is not None
        if is_boulder_claimable:
            url = 'https://www.mousehuntgame.com/managers/ajax/environment/mountain.php'
            data = {
                'action': 'claim_reward',
                'uh': self.unique_hash,
            }
            self.sess.post(url, data=data)
            print('claimed boulder reward')

    def change_trap(self, classification: str, item_key: str):
        assert classification in ['weapon', 'base', 'trinket', 'bait', 'skin']

        url = f'{Bot.base_url}/managers/ajax/users/gettrapcomponents.php'
        data = {'unique_hash': self.unique_hash, 'classification': classification}
        res = self.sess.post(url, data=data)

        components = json.loads(res.text)['components']
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
