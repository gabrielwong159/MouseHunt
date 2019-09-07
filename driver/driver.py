import datetime
import random
import time
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException, WebDriverException
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait

from .cv import read_captcha
from .exception import InvalidCaptchaException


class MouseHuntDriver(webdriver.Chrome):
    login_url = "https://www.mousehuntgame.com/login.php"
    game_url = "https://www.mousehuntgame.com/"
    horn_url = "https://www.mousehuntgame.com/turn.php"
    travel_url = "https://www.mousehuntgame.com/travel.php?tab=map"

    def __init__(driver, headless=True, trap_check=45):
        options = webdriver.ChromeOptions()
        options.add_argument("log-level=2")
        options.add_argument("disable-notifications")  # disable popup notifications
        options.add_argument("disable-gpu")  # enabling gpu results in non-critical warnings
        if headless:
            options.add_argument("headless")
        super().__init__(chrome_options=options)
        driver.delete_all_cookies()
        driver.trap_check = trap_check
        
    def login(driver, username, password):
        driver.get(driver.login_url)
        driver.find_element_by_class_name("signInText").click()
        time.sleep(0.1)
        
        login_div = driver.find_elements_by_class_name("login")[-1]
        login_div.find_element_by_name("username").send_keys(username)
        login_div.find_element_by_name("password").send_keys(password)
        login_div.find_element_by_class_name("actionButton").click()
        print("Logged in")
        driver.get(driver.game_url)
        print("Ready")

    def sound_the_horn(driver):
        driver.get(driver.horn_url)
        driver.check_captcha()

    def check_captcha(driver, n=0):
        try:
            if n > 0:
                driver.change_captcha()  # if previously failed, change captcha first

            captcha = driver.find_element_by_class_name("mousehuntPage-puzzle-form-captcha-image")
            image_url = captcha.value_of_css_property("background-image")[5:-2]  # url("____")
            text = read_captcha(image_url)
            if len(text) != 5:  # all captchas are always 5 characters
                raise InvalidCaptchaException()

            driver.find_element_by_class_name("mousehuntPage-puzzle-form-code").send_keys(text)
            driver.find_element_by_class_name("mousehuntPage-puzzle-form-code-button").click()
            print("Captcha at:", datetime.datetime.now().strftime("%d-%m-%Y %H:%M:%S"), "-", text)
            driver.sound_the_horn()
        except NoSuchElementException:  # no captcha element found
            print("Buwuu")  # continue without doing anything else
            print(driver.get_latest_entry())
        except WebDriverException:
            # sometimes encounter the issue where the captcha button was an unclickable element
            driver.get(driver.game_url)
            driver.check_captcha(n + 1)
        except InvalidCaptchaException:  # enter
            driver.check_captcha(n + 1)

    def change_captcha(driver):
        driver.get(driver.game_url)
        new_captcha = driver.find_element_by_class_name("mousehuntPage-puzzle-form-newCode")
        new_captcha.find_element_by_tag_name("a").click()
        driver.get(driver.game_url)

    def get_latest_entry(driver):
        # avoid halting the entire process when no journal entry is found
        try:
            text = driver.find_element_by_id("journallatestentry").text
            return text
        except NoSuchElementException:
            return "Could not find journal entry"

    def wait_for_next_horn(driver):
        offset = random.randint(0, 200)
        offset_per_min = round(offset/15, 2)
        print("Additional offset:", offset, "dt:", offset_per_min)
        for i in range(15):
            time.sleep(60 + offset_per_min)
            print(i+1, end=" ", flush=True)

            minute = datetime.datetime.now().minute
            if minute == driver.trap_check:
                driver.get(driver.game_url)
                print("\n" + driver.get_latest_entry())
        print()

    def list_locations(driver):
        driver.get(driver.travel_url)
        map_regions = driver.find_elements_by_class_name("travelPage-map-region-name")
        for region in map_regions:
            if not region.is_displayed():  # ignore when location is not accessible
                continue
            region.click()
            map_locations = driver.find_elements_by_class_name("travelPage-map-region-environment-link")
            for element in map_locations:
                text = element.text.strip()
                if text: print(text)

    def travel(driver, location):
        driver.get(driver.travel_url)
        map_regions = driver.find_elements_by_class_name("travelPage-map-region-name")
        for region in map_regions:
            if not region.is_displayed():  # ignore when location is not accessible
                continue
            region.click()

            map_locations = driver.find_elements_by_class_name("travelPage-map-region-environment-link")
            for element in map_locations:
                if element.text == location:
                    element.click()
                    travel_buttons = driver.find_elements_by_class_name("travelPage-map-image-environment-button")
                    for element in travel_buttons:  # search through all element buttons
                        if element.is_displayed():  # the one displayed is the one corresponding to location
                            element.click()
                            driver.get(driver.game_url)
                            return
        driver.get(driver.game_url)  # fallback when not found (or already at location)

    def is_empty(driver, target_class):
        data_classifications = 'base weapon trinket bait'.split()
        if target_class not in data_classifications:
            print(f"Error changing setup - target class not found: <{target_class}>")
            return

        target = driver.find_element_by_class_name(target_class)
        target_empty = "empty" in target.get_attribute("class").split()
        return target_empty

    def get_setup(driver, target_class):
        data_classifications = 'base weapon trinket bait'.split()
        assert target_class in data_classifications, f'Error changing setup - target class not found: <{target_class}>'

        css_class = f'.campPage-trap-armedItem.{target_class}'
        item_image = driver.find_element_by_css_selector(css_class)
        item_image.click()

        item_class = 'campPage-trap-itemBrowser-item-name'
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, item_class))
        )
        item_name = driver.find_element_by_class_name(item_class).text

        driver.get(driver.game_url)
        return item_name

    def change_setup(driver, target_class, target_name):
        print('Change setup', target_class, target_name)

        data_classifications = 'base weapon trinket bait'.split()
        assert target_class in data_classifications, f'Error changing setup - target class not found: <{target_class}>'

        css_class = f'.campPage-trap-armedItem.{target_class}'
        item_image = driver.find_element_by_css_selector(css_class)
        item_image.click()

        item_class = 'campPage-trap-itemBrowser-item-name'
        WebDriverWait(driver, 60).until(
            EC.presence_of_element_located((By.CLASS_NAME, item_class))
        )
        armed_item = driver.find_element_by_class_name('campPage-trap-itemBrowser-armed')
        armed_item_name = armed_item.find_element_by_class_name(item_class).text
        if armed_item_name == target_name:
            driver.get(driver.game_url)
            return

        all_items = driver.find_elements_by_class_name('campPage-trap-itemBrowser-item')
        for item in all_items:
            item_name = item.find_element_by_class_name(item_class).text
            if item_name == target_name:
                item.find_element_by_tag_name('a').click()
                break

        driver.get(driver.game_url)

