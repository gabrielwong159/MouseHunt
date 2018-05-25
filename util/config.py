import json
from os.path import abspath, dirname, join
cwd = abspath(dirname(__file__))

def get_facebook_config():
    config_file = join(cwd, '../config/facebook_config.json')
    with open(config_file, 'r') as f:
        config = json.loads(f.read())
    return config['email'], config['password']

def get_telegram_config():
    config_file = join(cwd, '../config/telegram_config.json')
    with open(config_file, 'r') as f:
        config = json.loads(f.read())
    return config['token'], config['chatid']
