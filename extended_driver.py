import os
from selenium.common.exceptions import NoSuchElementException

import config
from driver import MouseHuntDriver
from telebot import BotMessager


class ExtendedMouseHuntDriver(MouseHuntDriver):
    def __init__(driver, *args, **kwargs):
        super().__init__(*args, **kwargs)
        driver.messager = BotMessager(*config.get_telegram())

    def get_latest_entry(driver):
        text = super().get_latest_entry()
        driver.check_all(text)
        return text

    def check_all(driver, text):
        driver.check_triggers(text)
        driver.check_bait(text)
        driver.check_setup(text)

        driver.check_labyrinth_entrance(text)
        driver.check_warpath(text)
        driver.check_bwrift(text)
        driver.check_egg_charge(text)
        driver.check_winter_hunt_2019(text)

    def check_triggers(driver, text):
        # check journal entry for any trigger words
        if 'TRIGGERS' in os.environ:
            triggers = os.environ['TRIGGERS'].split(',')
            for word in triggers:
                if word in text:
                    driver.messager.notify_message(text)
                    break
        return text

    def check_bait(driver, text):
        if driver.is_empty('bait'):
            driver.messager.notify_message('Bait empty')

            curr_location = driver.get_current_location()
            rift_locations = ['Gnawnia Rift', 'Burroughs Rift', ' Whisker Wood...',
                              'Furoma Rift', 'Bristle Woods...', 'Valour Rift']
            if curr_location in rift_locations or 'Rift' in curr_location:  # for forward compatibility
                driver.change_setup('bait', 'Brie String Cheese')
            else:
                driver.change_setup('bait', 'Gouda Cheese')

    def check_setup(driver, text):
        location = driver.get_current_location()
        base = driver.get_setup('base')
        message = f'Check trap: {location}, {base}'

        if location == 'Queso River':
            if not base.startswith('Overgrown Ember'):
                driver.messager.notify_message(message)
        elif location == 'Iceberg':
            possible_bases = [
                'Ultimate Iceberg',
                'Deep Freeze',
                'Magnet Base',
                'Spiked Base',
                'Remote Deto',
                'Hearthstone'
            ]
            if not any(base.startswith(s) for s in possible_bases):
                driver.messager.notify_message(message)
        elif location == 'Furoma Rift':
            if not base.startswith('Attuned Enerchi'):
                driver.messager.notify_message(message)
        elif location in ['Muridae Market', 'Fiery Warpath']:
            if not base == 'Desert Heater Base':
                driver.messager.notify_message(message)
        elif location in ['Twisted Garden', 'Sand Crypts', 'Cursed City']:
            charm = driver.get_setup('trinket')
            boss = charm in ['Shattering Charm', 'Grub Scent Charm']
            if not boss and not base in ['Living Base', 'Hothouse Base', 'Desert Heater Base']:
                driver.messager.notify_message(message)

    def check_labyrinth_entrance(driver, text):
        if 'entrance' in text:
            print('Labyrinth entrance detected')
            driver.change_setup('bait', 'Gouda Cheese')

    def check_warpath(driver, text):
        try:
            elem = driver.find_element_by_class_name('warpathHUD-streak-quantity')
        except NoSuchElementException:
            print('Warpath check failed')
            return

        # if charm is empty, just used a commander, replace with something
        if driver.is_empty('trinket'):
            driver.change_setup('trinket', 'Warpath Scout Charm')
            driver.messager.notify_message('charm empty')
        # if streak is high, switch to commander
        try:
            streak = int(elem.text)
            print(f'Warpath streak found: {streak}')
        except ValueError:
            streak = 0
        if streak >= 6:
            # driver.change_setup('trinket', "Super Warpath Commander's Charm")
            driver.messager.notify_message(streak)

    def check_bwrift(driver, text):
        def enter_portal(portal):
            portal.click()
            action_buttons = driver.find_elements_by_class_name('mousehuntActionButton')
            for button in action_buttons:
                if button.text == 'Enter Portal':
                    button.click()
                    break

        try:
            entrance_chamber_css = ('.riftBristleWoodsHUD-portal'
                                    '.riftBristleWoodsHUD-chamberSpecificTextContainer'
                                    '.entrance_chamber')
            elem = driver.find_element_by_css_selector(entrance_chamber_css)
            enter_portal(elem)
            return
        except NoSuchElementException:
            pass

        try:
            chamber_progress_hud_css = 'riftBristleWoodsHUD-chamberProgressQuantity'
            elem = driver.find_element_by_class_name(chamber_progress_hud_css)
        except NoSuchElementException:
            print('BW rift check failed')
            return

        try:
            curr, total = elem.text.split('/')
            print(f'BW rift check: {curr}/{total}')
            notify = int(curr) == 0
        except ValueError as e:
            print(elem.text, e)
            return

        if notify:
            portal_container = driver.find_element_by_class_name('riftBristleWoodsHUD-portalContainer')
            portals = portal_container.find_elements_by_class_name('riftBristleWoodsHUD-portal')
            portal_names = [portal.find_element_by_class_name('riftBristleWoodsHUD-portal-name').text
                            for portal in portals]
            print('BW rift all portals:', portal_names)

            important_portals = ['Guard Barracks', 'Security Chamber',
                                 'Frozen Alcove', 'Furnace Room',
                                 'Ingress Chamber', 'Pursuer Mousoleum',
                                 'Acolyte Chamber']
            chosen_portal = None
            if all(portal not in portal_names for portal in important_portals):
                portal_priority = ['Lucky Tower', 'Hidden Treasury',
                                   'Timewarp Chamber',
                                   'Runic Laboratory', 'Ancient Lab',
                                   'Gearworks']
                for chosen_portal in portal_priority:
                    try:
                        idx = portal_names.index(chosen_portal)
                        print('BW rift target portal found:', chosen_portal, idx)
                        enter_portal(portals[idx])
                        break
                    except ValueError:
                        continue

            message = f'BW rift \n' \
                      f'Portals found: {portal_names} \n' \
                      f'Chosen portal: {chosen_portal}'
            driver.messager.notify_message(message)

    def check_egg_charge(driver, text):
        try:
            charge_qty_elem = driver.find_element_by_class_name('springHuntHUD-charge-quantity')
        except NoSuchElementException:
            print('Egg hunt check failed')
            return

        charge = charge_qty_elem.find_element_by_tag_name('span').text
        charge = int(charge)

        curr_charm = driver.get_setup('trinket')
        curr_state = 'Up' if 'Charge' in curr_charm else 'Down'

        print('Egg hunt status:', curr_state, charge)
        if curr_state == 'Up':
            if charge == 20:
                print('Going down')
                driver.change_setup('trinket', 'Eggstra Charm')
                driver.change_setup('bait', 'Marshmallow Monterey')
        else:
            if charge <= 17:
                print('Going up')
                driver.change_setup('trinket', 'Eggscavator Charge Charm')
                driver.change_setup('bait', 'Gouda Cheese')

    def check_winter_hunt_2019(driver, text: str) -> None:
        hud_name = 'winterHunt2019HUD'
        try:
            hud = driver.find_element_by_class_name(hud_name)
        except NoSuchElementException:
            return

        golem_builders = hud.find_elements_by_class_name(f'{hud_name}-golemBuilder')

        claimable = ['canClaim' in elem.get_attribute('class') for elem in golem_builders]
        for elem, is_claimable in zip(golem_builders, claimable):
            print(elem.find_element_by_class_name(f'{hud_name}-golemBuilder-golemButton'))

        buildable = ['canBuild' in elem.get_attribute('class') for elem in golem_builders]

        hud_parts = hud.find_element_by_css_selector(f'.{hud_name}-itemGroup.parts')
        n_head, n_torso, n_limb = (int(elem.text) for elem in
                                   hud_parts.find_elements_by_class_name(f'{hud_name}-itemGroup-item'))

        n_snow = int(hud.find_element_by_css_selector(f'.{hud_name}-itemGroup.recycle').text)

        print(f'GWH check <canClaim: {sum(claimable)}, canBuild: {sum(buildable)}, '
              f'head: {n_head}, torso: {n_torso}, limb: {n_limb}>')

        message = ''
        if any(claimable):
            message += f'Golem claimable: {claimable}\n'
        if len(message) > 0:
            driver.messager.notify_message(message)
