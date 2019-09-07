import json
from os.path import abspath, dirname, join
cwd = abspath(dirname(__file__))


def get_login_config():
    config_file = join(cwd, '../config/login_config.json')
    with open(config_file, 'r') as f:
        config = json.loads(f.read())
    return config['username'], config['password']


def get_telegram_config():
    config_file = join(cwd, '../config/telegram_config.json')
    with open(config_file, 'r') as f:
        config = json.loads(f.read())
    return config['token'], config['chatid']
