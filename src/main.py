import asyncio
import random
from datetime import datetime, timedelta

from src.bot_plus import BotPlus as Bot
from src.clients.telegram_bot import TelegramBotClient
from src.settings import Settings

MAX_DELAY = 200
TRAP_CHECK_PRIORITY = 1
HORN_PRIORITY = 2


async def main():
    settings = Settings()
    if settings.telegram_bot_token != "" and settings.telegram_chat_id != "":
        telegram_bot_client = TelegramBotClient(
            token=settings.telegram_bot_token,
            chat_id=settings.telegram_chat_id,
        )
    else:
        telegram_bot_client = None
    bot = Bot(settings, telegram_bot_client)

    await asyncio.gather(
        asyncio.create_task(horn_loop(bot)),
        asyncio.create_task(trap_check_loop(bot)),
    )


async def horn_loop(bot: Bot):
    while True:
        bot.refresh()
        secs_to_next_hunt = bot.get_user_data()["next_activeturn_seconds"]
        if secs_to_next_hunt > 0:
            # Something hunted without us; the horn branch notifies for itself.
            bot.notify_missed_hunts()
            arbitrary_delay = 5
            total_delay = secs_to_next_hunt + arbitrary_delay
        else:
            bot.check_and_solve_captcha()
            bot.horn()
            total_delay = 15 * 60 + random.randint(1, MAX_DELAY)

        bot.update_journal_entries()

        next_hunt_dt = datetime.now() + timedelta(seconds=total_delay)
        bot.logger.info(f'time of next hunt: {next_hunt_dt.strftime("%Y-%m-%d %T")}')
        await asyncio.sleep(total_delay)


async def trap_check_loop(bot: Bot):
    while True:
        next_check_dt = get_next_trap_check_dt(bot.trap_check)
        bot.logger.info(
            f'time of next trap check: {next_check_dt.strftime("%Y-%m-%d %T")}'
        )
        await asyncio.sleep((next_check_dt - datetime.now()).total_seconds())

        bot.refresh()
        bot.post_trap_check()


def get_next_trap_check_dt(trap_check_min: int) -> datetime:
    # Fire just after the minute starts, so the game has processed the check by
    # the time we notify.
    arbitrary_buffer = 5
    now = datetime.now()
    next_check_dt = now.replace(
        minute=trap_check_min, second=arbitrary_buffer, microsecond=0
    )
    if next_check_dt <= now:
        next_check_dt += timedelta(hours=1)
    return next_check_dt


if __name__ == "__main__":
    asyncio.run(main())
