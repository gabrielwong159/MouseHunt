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
    bot.refresh()

    curr_min = datetime.now().minute
    if curr_min == bot.trap_check:
        bot.update_journal_entries()

    if curr_min >= bot.trap_check:
        next_check_hour = datetime.now() + timedelta(hours=1)
    else:
        next_check_hour = datetime.now()

    arbitrary_buffer = 5
    next_check_dt = next_check_hour.replace(
        minute=bot.trap_check, second=arbitrary_buffer, microsecond=0
    )
    bot.logger.info(f'time of next trap check: {next_check_dt.strftime("%Y-%m-%d %T")}')

    secs_to_next_check = (next_check_dt - datetime.now()).total_seconds()
    await asyncio.sleep(secs_to_next_check)


if __name__ == "__main__":
    asyncio.run(main())
