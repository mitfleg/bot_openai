import asyncio
import json
import logging
from aiogram import Bot, Dispatcher, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage

with open('./config.json') as f:
    config = json.load(f)
    TOKEN = config['token']
    DISCORD_TOKEN = config['discord']['DAVINCI_TOKEN']

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO,
    handlers=[logging.FileHandler("gpt.log")]
)

bot = Bot(TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())
tasks = []


async def on_startup(dp):
    task1 = asyncio.create_task(payment_checker())
    tasks.extend([task1])


async def on_shutdown(dp):
    await bot.close()
    for task in tasks:
        if not task.done():
            task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)

if __name__ == '__main__':
    from handlers import dp
    from handlers.replenish import payment_checker
    executor.start_polling(dp, on_startup=on_startup,
                           on_shutdown=on_shutdown, skip_updates=True)
