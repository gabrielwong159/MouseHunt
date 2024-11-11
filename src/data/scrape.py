# type: ignore
import sys

sys.path.insert(0, "..")

import json
import os

from bot import Bot

bot = Bot(os.environ["MH_USERNAME"], os.environ["MH_PASSWORD"], 0)


def main():
    unique_hash = bot.get_user_data()["unique_hash"]
    print(unique_hash)

    for classification in ["trinket", "weapon", "base", "bait"]:
        components = get_trap_components(unique_hash, classification)
        print(classification, len(components))

        with open(f"{classification}.txt", "w") as f:
            for component in components:
                f.write(f"{component['type']},{component['name']}\n")


def get_trap_components(unique_hash: str, classification: str):
    assert classification in ["trinket", "weapon", "base", "bait", "skin"]
    data = {"unique_hash": unique_hash, "classification": classification}

    url = "https://www.mousehuntgame.com/managers/ajax/users/gettrapcomponents.php"
    res = bot.sess.post(url, data=data)
    assert res.ok, res.text

    d = json.loads(res.text)
    return d["components"]


if __name__ == "__main__":
    main()
