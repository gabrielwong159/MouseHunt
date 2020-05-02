import os
import random
import re
import sched
import time
from datetime import datetime, timedelta
from bot_plus import BotPlus as Bot

MAX_DELAY = 200
TRAP_CHECK_PRIORITY = 1
HORN_PRIORITY = 2


def main():
    username = os.environ['MH_USERNAME']
    password = os.environ['MH_PASSWORD']
    trap_check = int(os.environ['MH_TRAP_CHECK'])
    keywords = os.environ.get('KEYWORDS')

    if keywords is None:
        bot = Bot(username, password, trap_check)
    else:
        pattern = r',\s*'
        keywords = [t for s in keywords.split('\n') for t in re.split(pattern, s)]
        bot = Bot(username, password, trap_check, keywords)

    s = sched.scheduler(time.time, time.sleep)
    s.enter(delay=0, priority=TRAP_CHECK_PRIORITY, action=trap_check_loop, argument=(bot, s))
    s.enter(delay=0, priority=HORN_PRIORITY, action=horn_loop, argument=(bot, s))
    s.run()


def horn_loop(bot: Bot, s: sched.scheduler):
    bot.refresh_sess()
    bot.check_and_solve_captcha()

    secs_to_next_hunt = bot.get_user_data()['next_activeturn_seconds']
    if secs_to_next_hunt > 0:
        arbitrary_delay = 5
        total_delay = secs_to_next_hunt + arbitrary_delay
    else:
        bot.horn()
        bot.update_journal_entries()

        total_delay = 15*60 + random.randint(1, MAX_DELAY)

    next_hunt_dt = datetime.now() + timedelta(seconds=total_delay)
    print('time of next hunt:', next_hunt_dt.strftime('%Y-%m-%d %T'))

    s.enter(delay=total_delay, priority=HORN_PRIORITY, action=horn_loop, argument=(bot, s))
    s.run()


def trap_check_loop(bot: Bot, s: sched.scheduler):
    bot.refresh_sess()
    bot.check_and_solve_captcha()

    curr_min = datetime.now().minute
    if curr_min == bot.trap_check:
        bot.update_journal_entries()

    if curr_min >= bot.trap_check:
        next_check_hour = datetime.now() + timedelta(hours=1)
    else:
        next_check_hour = datetime.now()

    arbitrary_buffer = 5
    next_check_dt = next_check_hour.replace(minute=bot.trap_check, second=arbitrary_buffer, microsecond=0)
    print('time of next trap check:', next_check_dt.strftime('%Y-%m-%d %T'))

    secs_to_next_check = (next_check_dt - datetime.now()).total_seconds()
    s.enter(delay=secs_to_next_check, priority=TRAP_CHECK_PRIORITY, action=trap_check_loop, argument=(bot, s))
    s.run()


if __name__ == '__main__':
    main()
