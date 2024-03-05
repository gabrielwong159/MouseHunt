import json
import os
import telebot
from bs4 import BeautifulSoup
from requests import Response
from requests.exceptions import JSONDecodeError
from bot import Bot


class BotPlus(Bot):
    def __init__(self, *args, **kwargs):
        self.warpath_gargantua = os.environ.get('MH_WARPATH_GARGANTUA', 'true').lower() == 'true'
        self.warpath_wave_charm = True

        self.vrift_fire = os.environ.get('MH_VRIFT_FIRE', 'true').lower() == 'true'

        self.king_grub = os.environ.get("MH_KING_GRUB", "true").lower() == "true"
        self.king_grub_threshold = int(os.environ.get("MH_KING_GRUB_THRESHOLD", 0))

        print('Warpath mode:', 'Gargantua' if self.warpath_gargantua else 'Commander')
        print('Vrift auto toggle fire:', self.vrift_fire)

        super().__init__(*args, **kwargs)

    def update_journal_entries(self):
        all_entries, new_entries = super().update_journal_entries()
        self.check_entries(new_entries)

        user_data = self.get_user_data()
        self.check_bait_empty(user_data)
        self.check_location_setup(user_data)
        self.check_queso_river(user_data)
        self.check_bwrift(user_data)
        self.check_vrift(user_data)
        self.check_mountain(user_data)
        self.check_warpath(user_data)
        self.check_cursed_city(user_data)
        self.check_lost_city(user_data)
        self.check_sand_dunes(user_data)
        self.check_sb_factory(user_data)
        self.check_halloween(user_data)
        self.check_winter_hunt(user_data)

        return all_entries, new_entries

    def check_entries(self, new_entries):
        for entry in new_entries[::-1]:
            self.logger.info(f'\n{entry}\n')
            for keyword in self.keywords:
                if keyword in entry:
                    telebot.send_message(f"{self.name}\n{entry}")
                    break

    def check_bait_empty(self, user_data: dict):
        bait_qty = user_data['bait_quantity']
        if bait_qty > 0:
            return

        is_rift = user_data['environment_name'].endswith('Rift')
        is_queso = user_data['environment_name'] in ['Prickly Plains', 'Cantera Quarry', 'Queso Geyser']
        if is_rift:
            cheese = 'brie_string_cheese'
        elif is_queso:
            cheese = 'bland_queso_cheese'
        else:
            cheese = 'gouda_cheese'

        self.change_trap('bait', cheese)
        telebot.send_message(f'{self.name}\nbait empty, now using {cheese}')

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
            message = f'Unexpected setup in {location}'
            telebot.send_message(f"{self.name}\n{message}")

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
            return

        quest_data = user_data['quests']['QuestRiftBristleWoods']
        if quest_data['chamber_status'] != 'open':
            return
        portal_names = ', '.join(portal['name'] for portal in quest_data['portals'])
        telebot.send_message(f'{self.name}\nPortals: {portal_names}')

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

        if floor % 8 == 0:
            message = f"At floor {floor}"
            telebot.send_message(f"{self.name}\n{message}")

        if not self.vrift_fire:
            return

        message = None
        if floor % 8 != 0:
            if is_fire_active:
                toggle_fire()
                message = f'At floor {floor}, switching off fire'
        else:
            if is_fire_active:
                message = f'At floor {floor}, fire already active'
            elif n_fire == 0:
                message = f'At floor {floor}, no fire to activate'
            else:
                toggle_fire()
                message = f'At floor {floor}, {n_fire} fire available, activating fire'

        if message is not None:
            print(message)
            telebot.send_message(f"{self.name}\n{message}")

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

    def check_town_of_gnawnia(self, user_data: dict):
        if self.get_location(user_data) != 'Town of Gnawnia':
            return

        soup = self.get_environment_hud(user_data)
        url = 'https://www.mousehuntgame.com/managers/ajax/users/town_of_gnawnia.php'

        is_reward_claimable = soup.find('a', class_='townOfGnawniaHUD-actionButton claim active') is not None
        if is_reward_claimable:
            data = {
                'action': 'claim_reward',
                'uh': self.unique_hash,
            }
            self.sess.post(url, data=data)

        is_bounty_acceptable = soup.find('a', 'townOfGnawniaHUD-actionButton reveal active') is not None
        if is_bounty_acceptable:
            data = {
                'action': 'accept_bounty',
                'uh': self.unique_hash,
            }
            self.sess.post(url, data=data)

    def check_warpath(self, user_data: dict):
        if self.get_location(user_data) != 'Fiery Warpath':
            return

        soup = self.get_environment_hud(user_data)

        main_hud_div = soup.find('div', class_='warpathHUD')
        for wave in ['wave_1', 'wave_2', 'wave_3']:
            if wave in main_hud_div['class']:
                break
        else:
            return

        if wave == 'wave_1':
            suffix = '_weak'
        elif wave == 'wave_2':
            suffix = ''
        elif wave == 'wave_3':
            suffix = '_epic'
        popn_class = 'warpathHUD-wave-mouse-population'
        desert_types = ['warrior', 'scout', 'archer']
        n_desert = {t: int(soup
                           .find('div', class_=f'warpathHUD-wave {wave}')
                           .find('div', class_=f'desert_{t}{suffix}')
                           .find('div', class_=popn_class)
                           .text)
                    for t in desert_types}
        remaining_types = [_ for _ in n_desert.items() if _[1] > 0]

        streak = int(soup.find('div', class_='warpathHUD-streak-quantity').text)
        if streak >= 7 and self.warpath_gargantua:
            telebot.send_message(f'{self.name}\nStreak {streak}, Gargantua mode')
        elif streak >= 6 and not self.warpath_gargantua and len(remaining_types) > 1:
            self.change_trap('trinket', 'flame_march_general_trinket')
            telebot.send_message(f'{self.name}\nStreak {streak}, arming Warpath Commander\'s charm')
        elif streak == 0 and self.warpath_wave_charm:
            if len(remaining_types) == 0:
                return
            if len(remaining_types) == 1:
                self.change_trap('trinket', 'disarm')
                return
            target_type = min(remaining_types, key=lambda _: _[1])[0]
            if user_data['trinket_name'] is None or target_type not in user_data['trinket_name'].lower():
                self.change_trap('trinket', f'flame_march_{target_type}_trinket')
                telebot.send_message(f'{self.name}\nchanging trinket: {target_type}')

    def check_cursed_city(self, user_data: dict):
        if self.get_location(user_data) != 'Cursed City':
            return
        if 'QuestLostCity' not in user_data['quests']:
            return  # TODO - raise appropriate alert

        minigame = user_data['quests']['QuestLostCity']['minigame']
        if not minigame['is_cursed']:
            is_equipping_minigame_charm = any(curse['charm']['equipped'] for curse in minigame['curses'])
            if is_equipping_minigame_charm:
                self.change_trap('trinket', 'disarm')
            return

        for curse in minigame['curses']:
            if not curse['active']:  # curse already cleared
                continue
            if curse['charm']['equipped']:  # active and correctly armed
                break

            if curse['charm']['name'] == 'Bravery Charm':
                trinket_key = 'bravery_trinket'
            elif curse['charm']['name'] == 'Shine Charm':
                trinket_key = 'shine_trinket'
            else:
                trinket_key = 'clarity_trinket'
            self.arm_or_purchase_trinket(trinket_key)
            break

    def check_lost_city(self, user_data: dict):
        if self.get_location(user_data) != 'Lost City':
            return
        if 'QuestLostCity' not in user_data['quests']:
            return

        minigame = user_data['quests']['QuestLostCity']['minigame']
        if not minigame['is_cursed']:
            return
        if minigame['curses'][0]['charm']['equipped']:
            return

        trinket_key = 'searcher_trinket'
        self.arm_or_purchase_trinket(trinket_key)

    def check_sand_dunes(self, user_data: dict):
        if self.get_location(user_data) != "Sand Crypts":
            return
        if not self.king_grub:
            return

        sand = user_data["quests"]["QuestSandDunes"]["minigame"]["salt_charms_used"]
        print(f"Sand level: {sand}")

        is_trinket_armed = user_data["trinket_quantity"] > 0
        armed_trinket = user_data["trinket_name"]

        if sand >= self.king_grub_threshold:
            # equip grub scent charm
            if is_trinket_armed and armed_trinket == "Grub Scent Charm":
                return
            self.arm_or_purchase_trinket(trinket_key="grub_scent_trinket")
            self.change_trap("base", "living_base")
            return

        # try to equip super salt charm
        if is_trinket_armed and armed_trinket == "Super Salt Charm":
            return
        self.change_trap("trinket", "disarm")
        trinket_key = "super_salt_trinket"
        if trinket_key not in self.get_trap_components("trinket"):
            is_crafting_successful = self.craft_item(
                crafting_items={
                    "parts[extra_coarse_salt_crafting_item]": 1,
                    "parts[essence_b_crafting_item]": 2,
                    "parts[perfect_orb]": 1,
                },
                quantity=1,
            )
            if is_crafting_successful:
                self.change_trap("trinket", trinket_key)
                self.change_trap("base", "smelly_sodium_base")
                return

        # try to equip grub salt charm
        self.arm_or_purchase_trinket("grub_salt_trinket")
        self.change_trap("base", "smelly_sodium_base")

    def check_sb_factory(self, user_data: dict):
        if self.get_location(user_data) != 'SUPER|brie+ Factory':
            return

        is_crate_claimable = user_data['quests']['QuestSuperBrieFactory']['factory_atts']['can_claim']
        if is_crate_claimable:
            url = 'https://www.mousehuntgame.com/managers/ajax/events/birthday_factory.php'
            data = {
                'uh': self.unique_hash,
                'action': 'claim_reward',
            }
            self.sess.post(url, data=data)

    def check_halloween(self, user_data: dict):
        if self.get_location(user_data) != "Gloomy Greenwood":
            return

        quest_data = user_data["quests"]["QuestHalloweenBoilingCauldron"]
        for idx, cauldron in enumerate(quest_data["cauldrons"]):
            if cauldron["is_brewing"]:
                continue

            # run this in the loop to check quantity again after each brew attempt
            cheeses = quest_data["recipes"]["cheese"][::-1]  # reverse order to brew most valuable first
            chosen_recipe = None
            for cheese in cheeses:
                if cheese["cost"][0]["num_owned"] >= cheese["cost"][0]["quantity"]:
                    chosen_recipe = cheese["type"]
                    break
            if chosen_recipe is None:
                return  # insufficient ingredients to brew - abort altogether

            url = "https://www.mousehuntgame.com/managers/ajax/events/halloween_boiling_cauldron.php"
            data = {
                "uh": self.unique_hash,
                "action": "brew_recipe",
                "slot": idx,
                "recipe_type": chosen_recipe,
            }
            self.sess.post(url, data=data)

    def check_winter_hunt(self, user_data: dict):
        location = self.get_location(user_data)
        if location not in {"Cinnamon Hill", "Golem Workshop", "Ice Fortress"}:
            return

        if location == "Cinnamon Hill":
            quest_key = "QuestCinnamonTreeGrove"
        elif location == "Golem Workshop":
            quest_key = "QuestGolemWorkshop"
        else:
            quest_key = "QuestIceFortress"
        quest_data = user_data["quests"][quest_key]

        claimable_slots = []
        for idx, golem in enumerate(quest_data["golems"]):
            if golem["can_claim"]:
                claimable_slots.append(golem["slot"])

        if len(claimable_slots) == 0:
            return
        telebot.send_message(f"Claimable golems: {claimable_slots}")

    def change_trap(self, classification: str, item_key: str):
        assert classification in ['weapon', 'base', 'trinket', 'bait', 'skin']

        if item_key not in 'disarm':
            available_components = self.get_trap_components(classification)
            if item_key not in available_components:
                telebot.send_message(f'{self.name}\ncannot find {classification}: {item_key}')
                return

        url = f'{Bot.base_url}/managers/ajax/users/changetrap.php'
        data = {'uh': self.unique_hash, classification: item_key}
        self.sess.post(url, data=data)

    def purchase_item(self, item_key: str, quantity: int):
        url = f'{self.base_url}/managers/ajax/purchases/itempurchase.php'
        data = {
            'uh': self.unique_hash,
            'type': item_key,
            'quantity': quantity,
            'buy': 1,
            'is_kings_cart_item': 0,
        }
        self.sess.post(url, data=data)

    def arm_or_purchase_trinket(self, trinket_key: str):
        if trinket_key not in self.get_trap_components('trinket'):
            self.purchase_item(trinket_key, 1)
        self.change_trap('trinket', trinket_key)

    def craft_item(self, crafting_items: dict, quantity: int) -> bool:
        url = f"{self.base_url}/managers/ajax/users/crafting.php"
        data = {
            "uh": self.unique_hash,
            **crafting_items,
            "craftQty": quantity,
        }
        response = self.sess.post(url, data=data)
        if not response.ok:
            return False
        try:
            return response.json()["success"] == 1
        except JSONDecodeError:
            return False
        except KeyError:
            return False

    def get_trap_components(self, classification: str) -> set:
        assert classification in ['weapon', 'base', 'trinket', 'bait', 'skin']

        url = f'{Bot.base_url}/managers/ajax/users/gettrapcomponents.php'
        data = {'uh': self.unique_hash, 'classification': classification}
        res = self.sess.post(url, data=data)

        components = json.loads(res.text)['components']
        return {component['type'] for component in components}

    def get_location(self, user_data: dict) -> str:
        return user_data['environment_name']

    def get_environment_hud(self, user_data: dict) -> BeautifulSoup:
        hud = user_data['enviroment_atts']['environment_hud']
        return BeautifulSoup(hud, 'html.parser')

    def raise_res_error(self, res: Response):
        self.logger.error(res.text)
        telebot.send_message(f'{self.name}\nERROR: {res.text}')
        super().raise_res_error(res)
