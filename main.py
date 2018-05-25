from util.driver import MouseHuntDriver

def main():
    # automatically resets when an unknown error is encountered
    try:
        driver = MouseHuntDriver(headless=True)
        driver.login()
        while True:
            driver.sound_the_horn()
            if driver.is_bait_empty():
                driver.change_setup("bait", "Gouda Cheese")            
            driver.wait_for_next_horn()
    except KeyboardInterrupt as e:
        print(e)
    except Exception as e:
        print(e)
        driver.close()
        main()

if __name__ == "__main__":
    main()
