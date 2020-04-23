import time
from extended_driver import ExtendedMouseHuntDriver
from config import get_login_config


def main():
    username, password = get_login_config()
    driver = None
    # automatically resets when an unknown error is encountered
    try:
        driver = ExtendedMouseHuntDriver(headless=True, trap_check=45)
        driver.login(username, password)

        s = driver.execute_script('return user')['next_activeturn_seconds']
        time.sleep(s + 5)

        while True:
            driver.sound_the_horn()
            driver.wait_for_next_horn()
    except KeyboardInterrupt as e:
        print(e)
    except Exception as e:
        print(e)
        if driver is not None:
            driver.close()
        main()


if __name__ == "__main__":
    main()
