import datetime
import json
import os
import random
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.remote_connection import LOGGER
from dotenv import find_dotenv, load_dotenv
from cv import read_captcha
from exception import InvalidCaptchaException

class MouseHuntDriver(object):
    login_url = "https://www.facebook.com/login.php"
    game_url = "https://apps.facebook.com/mousehunt/"
    horn_url = "https://apps.facebook.com/mousehunt/turn.php"

    iframe_id = "iframe_canvas"
    captcha_image_class_name = "mousehuntPage-puzzle-form-captcha-image"
    captcha_input_class_name = "mousehuntPage-puzzle-form-code"
    captcha_button_class_name = "mousehuntPage-puzzle-form-code-button"
    new_code_class_name = "mousehuntPage-puzzle-form-newCode"
    journal_entry_id = "journallatestentry"
        
    def __init__(self):
        driver = webdriver.Firefox()
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
        for i in range(15):
            time.sleep(60 + random.randint(0, 15))
            print(i+1, end=" ", flush=True)
        print()
        
    def sound_the_horn(self):
        self._driver.get(self.horn_url)
        self.check_captcha()

    def check_captcha(self, n=0):
        driver = self._driver
        try:
            if n > 0: self.change_captcha() # if previously failed, change captcha first
            
            iframe = driver.find_element_by_id(self.iframe_id)
            driver.switch_to_frame(iframe)

            captcha = driver.find_element_by_class_name(self.captcha_image_class_name)
            image_url = captcha.value_of_css_property("background-image")[5:-2] # url("____")
            text = read_captcha(image_url)
            if (len(text) != 5):
                raise InvalidCaptchaException()

            driver.find_element_by_class_name(self.captcha_input_class_name).send_keys(text)
            driver.find_element_by_class_name(self.captcha_button_class_name).click()
            driver.switch_to_default_content()

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
        iframe = driver.find_element_by_id(self.iframe_id)
        driver.switch_to_frame(iframe)
        
        new_captcha = driver.find_element_by_class_name(self.new_code_class_name)
        new_captcha.find_element_by_tag_name("a").click()

        driver.switch_to_default_content()
        driver.get(self.game_url)

    def get_latest_entry(self):
        driver = self._driver
        
        # switch to iframe if available - not available when captcha
        try:
            iframe = driver.find_element_by_id(self.iframe_id)
            driver.switch_to_frame(iframe)
        except NoSuchElementException:
            pass

        # avoid halting the entire process when no journal entry is found
        try:
            text = driver.find_element_by_id(self.journal_entry_id).text
            driver.switch_to_default_content()
            return text
        except NoSuchElementException:
            return "Could not find journal entry"

    def quit(self):
        self._driver.quit()
