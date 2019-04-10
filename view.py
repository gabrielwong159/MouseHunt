from util.driver import MouseHuntDriver
from util.config import get_login_config


if __name__ == "__main__":
    username, password = get_login_config()
    
    driver = MouseHuntDriver(headless=False)
    driver.login(username, password)
