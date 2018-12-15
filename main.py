from extended_driver import ExtendedMouseHuntDriver


def main():
    driver = None
    # automatically resets when an unknown error is encountered
    try:
        driver = ExtendedMouseHuntDriver(headless=False)
        driver.login()
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
