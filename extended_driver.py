from util.driver import MouseHuntDriver
from selenium.common.exceptions import NoSuchElementException
from util.telegram import notify_message


class ExtendedMouseHuntDriver(MouseHuntDriver):
    def get_latest_entry(self):
        text = super().get_latest_entry()
        # check journal entry for any trigger words
        with open('triggers.txt',  'r') as f:
            s = f.read()
        if s:
            triggers = s.strip().split('\n')
            for word in triggers:
                if word in text:
                    notify_message(text)
                    break
        self.check_labyrinth_entrance(text)
        return text

    def sound_the_horn(self):
        super().sound_the_horn()
        # check for empty bait
        if self.is_empty('bait'):
            self.change_setup('bait', 'Gouda Cheese')
            notify_message('Bait empty')

        self.check_warpath()
        self.check_bwrift()
        self.check_egg_charge()
    
    def check_labyrinth_entrance(self, text):
        if 'entrance' in text:
            self.change_setup('bait', 'Gouda Cheese')

    def check_warpath(self):
        try:
            elem = self.find_element_by_class_name('warpathHUD-streak-quantity')
        except NoSuchElementException:
            return

        # if charm is empty, just used a commander, replace with something
        if self.is_empty('trinket'):
            self.change_setup('trinket', 'Warpath Scout Charm')
            notify_message('charm empty')
        # if streak is high, switch to commander
        try:
            streak = int(elem.text)
        except ValueError:
            streak = 0
        if streak >= 6:
            # self.change_setup('trinket', "Super Warpath Commander's Charm")
            notify_message(streak)

    def check_bwrift(self):
        try:
            elem = self.find_element_by_class_name('riftBristleWoodsHUD-chamberProgressQuantity')
        except NoSuchElementException:
            return

        try:
            curr, total = elem.text.split('/')
            notify = int(curr) == 0
        except ValueError as e:
            print(elem.text, e)
            return

        if notify:
            portal_container = self.find_element_by_class_name('riftBristleWoodsHUD-portalContainer')
            portals = portal_container.find_elements_by_class_name('riftBristleWoodsHUD-portal')
            portal_names = [portal.find_element_by_class_name('riftBristleWoodsHUD-portal-name').text
                            for portal in portals]

            def enter_portal(portal):
                portal.click()
                action_buttons = self.find_elements_by_class_name('mousehuntActionButton')
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
                                    'Ancient Laboratory', 'Runic Laboratory',
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
            notify_message(message)

    def check_egg_charge(self):
        try:
            charge_qty_elem = self.find_element_by_class_name('springHuntHUD-charge-quantity')
        except NoSuchElementException:
            return

        charge = charge_qty_elem.find_element_by_tag_name('span').text
        charge = int(charge)

        curr_charm = self.get_setup('trinket')
        curr_state = 'Up' if 'Charge' in curr_charm else 'Down'

        print(curr_state, charge)
        if curr_state == 'Up':
            if charge == 20:
                print('Going down')
                self.change_setup('trinket', 'Eggstra Charm')
                self.change_setup('bait', 'Marshmallow Monterey')
        else:
            if charge <= 17:
                print('Going up')
                self.change_setup('trinket', 'Eggscavator Charge Charm')
                self.change_setup('bait', 'Gouda Cheese')

