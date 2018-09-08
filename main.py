from util.driver import MouseHuntDriver


def main():
    driver = None
    # automatically resets when an unknown error is encountered
    try:
        driver = MouseHuntDriver(headless=True)
        driver.login()
        while True:
            driver.sound_the_horn()
            if driver.is_empty('bait'):
                driver.change_setup("bait", "Gouda Cheese")            
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
