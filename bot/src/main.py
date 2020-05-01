import os
import random
import sched
import time
from datetime import datetime, timedelta
from typing import List
from bot import Bot

MAX_DELAY = 200


def main():
    username = os.environ['MH_USERNAME']
    password = os.environ['MH_PASSWORD']
    bot = Bot(username, password, trap_check=45)

    s = sched.scheduler(time.time, time.sleep)
    s.enter(delay=0, priority=1, action=trap_check_loop, argument=(bot, s))
    s.enter(delay=0, priority=2, action=horn_loop, argument=(bot, s))
    s.run()


def horn_loop(bot: Bot, s: sched.scheduler):
    bot.refresh_sess()

    secs_to_next_hunt = bot.get_user_data()['next_activeturn_seconds']
    if secs_to_next_hunt > 0:
        arbitrary_delay = 5
        total_delay = secs_to_next_hunt + arbitrary_delay
    else:
        bot.horn()
        _, updated_entries = bot.update_journal_entries()
        print_entries(updated_entries)

        total_delay = 15*60 + random.randint(1, MAX_DELAY)

    next_hunt_dt = datetime.now() + timedelta(seconds=total_delay)
    print('time of next hunt:', next_hunt_dt.strftime('%Y-%m-%d %T'))

    s.enter(delay=total_delay, priority=2, action=horn_loop, argument=(bot, s))
    s.run()


def trap_check_loop(bot: Bot, s: sched.scheduler):
    bot.refresh_sess()

    curr_min = datetime.now().minute
    if curr_min == bot.trap_check:
        _, updated_entries = bot.update_journal_entries()
        print_entries(updated_entries)

    if curr_min >= bot.trap_check:
        next_check_hour = datetime.now() + timedelta(hours=1)
    else:
        next_check_hour = datetime.now()

    arbitrary_buffer = 5
    next_check_dt = next_check_hour.replace(minute=bot.trap_check, second=arbitrary_buffer, microsecond=0)
    print('time of next trap check:', next_check_dt.strftime('%Y-%m-%d %T'))

    secs_to_next_check = (next_check_dt - datetime.now()).total_seconds()
    s.enter(delay=secs_to_next_check, priority=1, action=trap_check_loop, argument=(bot, s))
    s.run()


def print_entries(entries: List[str]):
    for entry in entries:
        print(entry, end='\n\n')


if __name__ == '__main__':
    main()
