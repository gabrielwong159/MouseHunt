import datetime
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
        return text

    def sound_the_horn(self):
        super().sound_the_horn()
        # check for empty bait
        if self.is_empty('bait'):
            self.change_setup('bait', 'Gouda Cheese')
            notify_message('Bait empty')

        self.check_warpath()
        self.check_egg_charge()

    def check_warpath(self):
        try:
            elem = self.find_element_by_class_name('warpathHUD-streak-quantity')
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
                # self.change_setup('trinket', "Super Warpath Commander's C...")
                notify_message(streak)
        except NoSuchElementException:
            pass


    def check_egg_charge(self):
        charge_qty_elem = self.find_element_by_class_name('springHuntHUD-charge-quantity')
        charge = charge_qty_elem.find_element_by_tag_name('span').text
        charge = int(charge)

        curr_charm = self.get_setup('trinket')
        curr_state = 'Up' if 'Charge' in curr_charm else 'Down'

        print(curr_state, charge)
        if curr_state == 'Up':
            if charge == 20:
                print('Going down')
                self.change_setup('trinket', 'Eggstra Charm')
        else:
            if charge <= 13:
                print('Going up')
                self.change_setup('trinket', 'Eggscavator Charge Charm')

