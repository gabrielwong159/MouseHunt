import os
import random
import sched
import time
from datetime import datetime, timedelta
from bot import Bot


def main():
    username = os.environ['MH_USERNAME']
    password = os.environ['MH_PASSWORD']

    bot = Bot(username, password, trap_check=45)

    s = sched.scheduler(time.time, time.sleep)
    s.enter(delay=0, priority=2, action=horn_loop, argument=(bot, s))

    if datetime.now().minute >= bot.trap_check:
        dt = datetime.now() + timedelta(hours=1)
    else:
        dt = datetime.now()
    dt = dt.replace(minute=bot.trap_check, second=15, microsecond=0)
    print('initial trap check', dt.strftime('%Y-%m-%d %T'))
    time_to_next_trap_check = (dt - datetime.now()).total_seconds()
    s.enter(delay=time_to_next_trap_check, priority=1, action=trap_check_loop, argument=(bot, s))

    s.run()


def horn_loop(bot: Bot, s: sched.scheduler):
    sess, user = bot.login()

    has_captcha = user['has_puzzle']
    if has_captcha:
        sess, req = bot.home(sess)
        captcha_url = bot.get_captcha_url(req.text)
        bot.solve_captcha(sess, captcha_url)
        return horn_loop(bot, s)

    secs_to_next_hunt = user['next_activeturn_seconds']
    if secs_to_next_hunt > 0:
        arbitrary_delay = 5
        next_hunt_dt = datetime.now() + timedelta(seconds=secs_to_next_hunt + arbitrary_delay)
        print('waiting for next hunt', next_hunt_dt.strftime('%Y-%m-%d %T'))
        time.sleep(secs_to_next_hunt + arbitrary_delay)

    sess, req = bot.horn(sess)
    journal_entries = bot.get_new_entries(req.text)
    if len(journal_entries) > 0:
        print(journal_entries[0])

    random_delay = random.randint(1, 200)
    print('random delay', random_delay)
    next_hunt_dt = datetime.now() + timedelta(seconds=15*60 + random_delay)
    print('time of next hunt', next_hunt_dt.strftime('%Y-%m-%d %T'))
    s.enter(delay=15*60 + random_delay, priority=2, action=horn_loop, argument=(bot, s))

    s.run()


def trap_check_loop(bot: Bot, s: sched.scheduler):
    sess, user = bot.login()
    sess, req = bot.home(sess)
    for entry in bot.get_new_entries(req.text):
        if 'checked my trap' not in entry and 'check my trap' not in entry:
            continue
        print(entry)
        break

    dt = datetime.now() + timedelta(hours=1)
    dt = dt.replace(minute=bot.trap_check, second=15, microsecond=0)
    print('next trap check', dt.strftime('%Y-%m-%d %T'))

    secs_to_next_trap_check = (dt - datetime.now()).total_seconds()
    s.enterabs(time=time.time() + secs_to_next_trap_check, priority=1, action=trap_check_loop, argument=(bot, s))


if __name__ == '__main__':
    main()
