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
        driver.check_triggers(text)
        return text

    def check_triggers(driver, text):
        # check journal entry for any trigger words
        if 'TRIGGERS' in os.environ:
            triggers = os.environ['TRIGGERS'].split(',')
            for word in triggers:
                if word in text:
                    driver.messager.notify_message(text)
                    break
        driver.check_labyrinth_entrance(text)
        return text

    def sound_the_horn(driver):
        super().sound_the_horn()

        driver.check_bait()
        driver.check_warpath()
        driver.check_bwrift()
        driver.check_egg_charge()

    def check_bait(driver):
        if driver.is_empty('bait'):
            driver.messager.notify_message('Bait empty')

            curr_location = driver.get_current_location()
            rift_locations = ['Gnawnia Rift', 'Burroughs Rift', ' Whisker Wood...',
                              'Furoma Rift', 'Bristle Woods...']
            if curr_location in rift_locations:
                driver.change_setup('bait', 'Brie String Cheese')
            else:
                driver.change_setup('bait', 'Gouda Cheese')

    def check_labyrinth_entrance(driver, text):
        if 'entrance' in text:
            driver.change_setup('bait', 'Gouda Cheese')

    def check_warpath(driver):
        try:
            elem = driver.find_element_by_class_name('warpathHUD-streak-quantity')
        except NoSuchElementException:
            return

        # if charm is empty, just used a commander, replace with something
        if driver.is_empty('trinket'):
            driver.change_setup('trinket', 'Warpath Scout Charm')
            driver.messager.notify_message('charm empty')
        # if streak is high, switch to commander
        try:
            streak = int(elem.text)
        except ValueError:
            streak = 0
        if streak >= 6:
            # driver.change_setup('trinket', "Super Warpath Commander's Charm")
            driver.messager.notify_message(streak)

    def check_bwrift(driver):
        try:
            elem = driver.find_element_by_class_name('riftBristleWoodsHUD-chamberProgressQuantity')
        except NoSuchElementException:
            return

        try:
            curr, total = elem.text.split('/')
            notify = int(curr) == 0
        except ValueError as e:
            print(elem.text, e)
            return

        if notify:
            portal_container = driver.find_element_by_class_name('riftBristleWoodsHUD-portalContainer')
            portals = portal_container.find_elements_by_class_name('riftBristleWoodsHUD-portal')
            portal_names = [portal.find_element_by_class_name('riftBristleWoodsHUD-portal-name').text
                            for portal in portals]

            def enter_portal(portal):
                portal.click()
                action_buttons = driver.find_elements_by_class_name('mousehuntActionButton')
                for button in action_buttons:
                    if button.text == 'Enter Portal':
                        button.click()
                        break

            important_portals = ['Guard Barracks', 'Security Chamber',
                                 'Frozen Alcove', 'Furnace Room',
                                 'Ingress Chamber', 'Pursuer Mousoleum',
                                 'Acolyte Chamber']
            chosen_portal = None
            if all(portal not in portal_names for portal in important_portals):
                portal_priority = ['Lucky Tower', 'Hidden Treasury',
                                   'Timewarp Chamber',
                                   'Ancient Lab', 'Runic Laboratory',
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

    def check_egg_charge(driver):
        try:
            charge_qty_elem = driver.find_element_by_class_name('springHuntHUD-charge-quantity')
        except NoSuchElementException:
            return

        charge = charge_qty_elem.find_element_by_tag_name('span').text
        charge = int(charge)

        curr_charm = driver.get_setup('trinket')
        curr_state = 'Up' if 'Charge' in curr_charm else 'Down'

        print(curr_state, charge)
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

