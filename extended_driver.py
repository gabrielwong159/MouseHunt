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

        # check for warpath
        try:
            elem = self.find_element_by_class_name('warpathHUD-streak-quantity')
            # if charm is empty, just used a commander, replace with something
            if self.is_empty('trinket'):
                self.change_setup('trinket', 'Warpath Scout Charm')
                notify_message('charm empty')
            # if streak is high, switch to commander
            streak = int(elem.text)
            if streak >= 5:
                self.change_setup('trinket', "Super Warpath Commander's C...")
                notify_message(streak)
        except NoSuchElementException:
            pass
