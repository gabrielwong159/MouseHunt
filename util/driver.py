import datetime
import random
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from util.config import get_facebook_config
from util.cv import read_captcha
from util.exception import InvalidCaptchaException
from util.telegram import notify_message


class MouseHuntDriver(webdriver.Chrome):
    login_url = "https://www.facebook.com/login.php"
    game_url = "https://apps.facebook.com/mousehunt/"
    horn_url = "https://apps.facebook.com/mousehunt/turn.php"
    travel_url = "https://apps.facebook.com/mousehunt/travel.php"

    def __init__(self, headless=True):
        options = webdriver.ChromeOptions()
        options.add_argument("log-level=2")
        options.add_argument("disable-notifications")
        options.add_argument("disable-gpu")
        if headless:
            options.add_argument("headless")
        super().__init__(chrome_options=options)
        self.delete_all_cookies()
        self._email, self._password = get_facebook_config()
        
    def login(self):
        self.get(self.login_url)
        self.find_element_by_id("email").send_keys(self._email)
        self.find_element_by_id("pass").send_keys(self._password)
        self.find_element_by_id("loginbutton").click()
        print("Logged in")
        self.get(self.game_url)
        print("Ready")

    def switch_to_iframe(self):
        try:
            iframe = self.find_element_by_id("iframe_canvas")
            self.switch_to.frame(iframe)
        except NoSuchElementException:
            pass

    def get_latest_entry(self):
        self.switch_to_iframe()

        # avoid halting the entire process when no journal entry is found
        try:
            text = self.find_element_by_id("journallatestentry").text

            with open('triggers.txt', 'r') as f:
                s = f.read()
            if s:
                triggers = s.strip().split('\n')
                for word in triggers:
                    if word in text:
                        notify_message(text)
                        break

            return text
        except NoSuchElementException:
            return "Could not find journal entry"
        finally:
            self.switch_to.default_content()

    def wait_for_next_horn(self):
        offset = random.randint(0, 200)
        offset_per_min = round(offset/15, 2)
        print("Additional offset:", offset, "dt:", offset_per_min)
        for i in range(15):
            time.sleep(60 + offset_per_min)
            print(i+1, end=" ", flush=True)

            minute = datetime.datetime.now().minute
            if minute == 45:
                self.get(self.game_url)
                print("\n" + self.get_latest_entry())
        print()
        
    def sound_the_horn(self):
        self.get(self.horn_url)
        self.check_captcha()

    def check_captcha(self, n=0):
        try:
            if n > 0: self.change_captcha() # if previously failed, change captcha first
            
            self.switch_to_iframe()
            captcha = self.find_element_by_class_name("mousehuntPage-puzzle-form-captcha-image")
            image_url = captcha.value_of_css_property("background-image")[5:-2] # url("____")
            text = read_captcha(image_url)
            if len(text) != 5:
                raise InvalidCaptchaException()

            self.find_element_by_class_name("mousehuntPage-puzzle-form-code").send_keys(text)
            self.find_element_by_class_name("mousehuntPage-puzzle-form-code-button").click()
            self.switch_to.default_content()

            print("Captcha at:", datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "-", text)
            self.sound_the_horn()
        except NoSuchElementException:
            print("Buwuu")
            print(self.get_latest_entry())
        except WebDriverException as e:
            # sometimes encounter the issue where the captcha button was an unclickable element
            self.get(self.game_url)
            self.check_captcha(n+1)
        except InvalidCaptchaException: # enter 
            self.check_captcha(n+1)

    def change_captcha(self):
        self.get(self.game_url)
        self.switch_to_iframe()
        
        new_captcha = self.find_element_by_class_name("mousehuntPage-puzzle-form-newCode")
        new_captcha.find_element_by_tag_name("a").click()

        self.switch_to.default_content()
        self.get(self.game_url)

    def list_locations(self):
        self.get(self.travel_url)
        self.switch_to_iframe()

        map_regions = self.find_elements_by_class_name("travelPage-map-region-name")
        for region in map_regions:
            region.click()
            map_locations = self.find_elements_by_class_name("travelPage-map-region-environment-link")
            for element in map_locations:
                text = element.text.strip()
                if text: print(text)

    def travel(self, location):
        self.get(self.travel_url)
        self.switch_to_iframe()

        map_regions = self.find_elements_by_class_name("travelPage-map-region-name")
        for region in map_regions:
            region.click()
            map_locations = self.find_elements_by_class_name("travelPage-map-region-environment-link")
            
            for element in map_locations:
                if element.text == location:
                    element.click()
                    travel_buttons = self.find_elements_by_class_name("travelPage-map-image-environment-button")
                    
                    for element in travel_buttons:
                        if element.is_displayed():
                            element.click()
                            self.switch_to.default_content()
                            return

    def is_empty(self, target_class):
        data_classifications = 'base weapon trinket bait'.split()
        if target_class not in data_classifications:
            print("Error changing setup: Target class not found")
            return

        self.switch_to_iframe()
        target = self.find_element_by_class_name(target_class)
        target_empty = "empty" in target.get_attribute("class").split()
        self.switch_to.default_content()
        return target_empty

    def get_setup(self, target_class):
        data_classifications = 'base weapon trinket bait'.split()
        if target_class not in data_classifications:
            print("Error changing setup: Target class not found")
            return

        self.get(self.game_url)
        self.switch_to_iframe()

        trap_controls = self.find_elements_by_class_name("trapControlThumb")
        for element in trap_controls:
            if element.get_attribute("data-classification") == target_class:
                element.click()

        WebDriverWait(self, 60).until(EC.presence_of_element_located((By.CLASS_NAME, "trapComponentRow")))
        components = self.find_elements_by_class_name("trapComponentRow")

        for element in components:
            if "selected" in element.get_attribute("class"):
                name = element.find_element_by_class_name("name").text
                if "not armed" in name:
                    setup = None
                else:
                    setup = name
                break

        self.switch_to.default_content()
        self.get(self.game_url)
        return setup

    def change_setup(self, target_class, target_name):
        print('Change', target_class, target_name)
        data_classifications = 'base weapon trinket bait'.split()
        if target_class not in data_classifications:
            print("Error changing setup: Target class not found")
            return
        
        self.get(self.game_url)
        self.switch_to_iframe()

        trap_controls = self.find_elements_by_class_name("trapControlThumb")
        for element in trap_controls:
            if element.get_attribute("data-classification") == target_class:
                element.click()

        WebDriverWait(self, 60).until(EC.presence_of_element_located((By.CLASS_NAME, "trapComponentRow")))
        components = self.find_elements_by_class_name("trapComponentRow")

        if target_name.lower() == "disarm":
            for element in components:
                if "selected" in element.get_attribute("class"):
                    if element.text != "Charm not armed.":
                        element.find_element_by_class_name("action").click()
        else:
            for element in components:
                if "selected" in element.get_attribute("class"): continue
                name = element.find_element_by_class_name("name").text
                if name == target_name:
                    element.click()
                    break
                
        self.get(self.game_url)
