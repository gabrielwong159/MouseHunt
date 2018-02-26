import datetime
import json
import os
import random
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.remote.remote_connection import LOGGER
from dotenv import find_dotenv, load_dotenv
from cv import read_captcha
from exception import InvalidCaptchaException

class MouseHuntDriver(object):
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
            
        driver = webdriver.Chrome(chrome_options=options)
        driver.delete_all_cookies()
        self._driver = driver

        load_dotenv(find_dotenv())
        self._email, self._password = os.environ.get("email"), os.environ.get("password")

    def login(self):
        driver = self._driver

        driver.get(self.login_url)
        driver.find_element_by_id("email").send_keys(self._email)
        driver.find_element_by_id("pass").send_keys(self._password)
        driver.find_element_by_id("loginbutton").click()
        print("Logged in")

        driver.get(self.game_url)
        print("Ready")

    def wait_for_next_horn(self):
        offset = random.randint(0, 200)
        offset_per_min = round(offset/15, 2)
        print("Additional offset:", offset)
        for i in range(15):
            time.sleep(60 + offset_per_min)
            print(i+1, end=" ", flush=True)

            minute = datetime.datetime.now().minute
            if minute == 45 or minute == 46:
                self._driver.get(self.game_url)
                print("\n" + self.get_latest_entry())
        print()
        
    def sound_the_horn(self):
        self._driver.get(self.horn_url)
        self.check_captcha()

    def check_captcha(self, n=0):
        driver = self._driver
        try:
            if n > 0: self.change_captcha() # if previously failed, change captcha first
            
            self.switch_to_iframe()
            captcha = driver.find_element_by_class_name("mousehuntPage-puzzle-form-captcha-image")
            image_url = captcha.value_of_css_property("background-image")[5:-2] # url("____")
            text = read_captcha(image_url)
            if (len(text) != 5):
                raise InvalidCaptchaException()

            driver.find_element_by_class_name("mousehuntPage-puzzle-form-code").send_keys(text)
            driver.find_element_by_class_name("mousehuntPage-puzzle-form-code-button").click()
            self.switch_to_default_content()

            print("Captcha at:", datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "-", text)
            self.sound_the_horn()
        except NoSuchElementException:
            print("Buwuu")
            print(self.get_latest_entry())
        except WebDriverException as e:
            # sometimes encounter the issue where the captcha button was an unclickable element
            driver.get(self.game_url)
            self.check_captcha(n+1)
        except InvalidCaptchaException: # enter 
            self.check_captcha(n+1)

    def change_captcha(self):
        driver = self._driver
        
        driver.get(self.game_url)
        self.switch_to_iframe()
        
        new_captcha = driver.find_element_by_class_name("mousehuntPage-puzzle-form-newCode")
        new_captcha.find_element_by_tag_name("a").click()

        self.switch_to_default_content()
        driver.get(self.game_url)

    def get_latest_entry(self):
        driver = self._driver
        
        # switch to iframe if available - not available when captcha
        try:
            self.switch_to_iframe()
        except NoSuchElementException:
            pass

        # avoid halting the entire process when no journal entry is found
        try:
            text = driver.find_element_by_id("journallatestentry").text
            return text
        except NoSuchElementException:
            return "Could not find journal entry"
        finally:
            self.switch_to_default_content()

    def travel(self, region, location):
        driver = self._driver
        driver.get(self.travel_url)
        self.switch_to_iframe()

        map_regions = driver.find_elements_by_class_name("travelPage-map-region-name")
        for element in map_regions:
            if element.text == region: element.click()

        map_locations = driver.find_elements_by_class_name("travelPage-map-region-environment-link")
        for element in map_locations:
            if element.text == location: element.click()

        travel_buttons = driver.find_elements_by_class_name("travelPage-map-image-environment-button")
        for element in travel_buttons:
            if element.is_displayed(): element.click()

        self.switch_to_default_content()

    def is_bait_empty(self):
        self.switch_to_iframe()
        bait = self._driver.find_element_by_class_name("bait")
        bait_empty = "empty" in bait.get_attribute("class").split()
        self.switch_to_default_content()
        return bait_empty

    def change_bait(self, bait_name):
        driver = self._driver
        self.switch_to_iframe()

        trap_controls = driver.find_elements_by_class_name("trapControlThumb")
        for element in trap_controls:
            if element.get_attribute("data-classification") == "bait": element.click()

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.CLASS_NAME, "trapComponentRow")))
        baits = driver.find_elements_by_class_name("trapComponentRow")
        for element in baits:
            if "selected" in element.get_attribute("class"): continue
            cheese = element.find_element_by_class_name("name").text
            if cheese == bait_name:
                element.click()
                break

        self.switch_to_default_content()

    def switch_to_iframe(self):
        iframe = self._driver.find_element_by_id("iframe_canvas")
        self._driver.switch_to_frame(iframe)

    def switch_to_default_content(self):
        self._driver.switch_to_default_content()

    def close(self):
        self._driver.close()
