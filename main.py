import config
from extended_driver import ExtendedMouseHuntDriver


def main():
    username, password = config.get_login()
    if username is None:
        print('Username not found in config, use env variable MH_USERNAME')
        return
    elif password is None:
        print('Password not found in config, use env variable MH_PASSWORD')
        return

    trap_check = config.get_trap_check_timing()
    if trap_check < -1:
        print('Trap check timing not found in config, will not perform trap check')

    driver = None
    # automatically resets when an unknown error is encountered
    try:
        driver = ExtendedMouseHuntDriver(headless=False, trap_check=trap_check)
        driver.login(username, password)
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
