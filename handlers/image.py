import traceback
import discord
from discord.ext import commands
import requests
from aiogram import types
from bot import bot, dp
from handlers.common import (
    enough_funds,
    getBalance,
    getConfig,
    insufficient_funds_message,
)
from .slai import Upscale
from .allmessages import mainImageMessage
from .db import DataBase
from .keyboard import image_option_keyboard, image_upscale_keyboard, no_money_keyboard

targetID = ""
targetHash = ""

variable = getConfig("discord")

intents = discord.Intents.default()
intents.members = True

bot_discord = commands.Bot(command_prefix="/", intents=intents)


async def send_msg(user_id, url, description, message_id, row_id, upscale=False):
    try:
        await bot.delete_message(user_id, message_id)
    except:
        pass
    image = requests.get(url).content
    price_img = variable["price_requests"]
    async with DataBase() as db:
        await db.increment("users", "count_requests_img", 1, where=f"user_id={user_id}")
        await db.decrement("users", "balance", price_img, where=f"user_id={user_id}")
    if not upscale:
        await bot.send_photo(
            user_id, image, description, reply_markup=image_option_keyboard(row_id)
        )
        return
    await bot.send_photo(
        user_id, image, description, reply_markup=image_upscale_keyboard()
    )


@bot_discord.event
async def on_message(message):
    discord_message_id = int(message.id)
    target_message = await message.channel.fetch_message(discord_message_id)
    try:
        if not "(fast)" in target_message.content:
            return
        try:
            request = target_message.content.split("**")[1]
        except IndexError:
            return
        async with DataBase() as db:
            query = await db.read("images", where=f"request='{request}'")
            row_id = query[0]["id"]
            user_id = query[0]["user_id"]
            message_id = query[0]["message_id"]
            if target_message.attachments:
                attachment_url = target_message.attachments[0].url
                if attachment_url:
                    discord_message_hash = attachment_url.split("_")[-1].split(".")[0]
                    if not "Upscaled" in target_message.content:
                        await db.update(
                            "images",
                            ["discord_message_id", "discord_message_hash"],
                            [discord_message_id, discord_message_hash],
                            where=f"id={row_id}",
                        )
                        await send_msg(
                            user_id, attachment_url, request, message_id, row_id
                        )
                    else:
                        await send_msg(
                            user_id,
                            attachment_url,
                            request,
                            message_id,
                            row_id,
                            upscale=True,
                        )
    except Exception as e:
        print(traceback.format_exc())


@dp.callback_query_handler(text="update")
async def choose_img(call: types.CallbackQuery):
    value = call.message.caption
    await mainImageMessage(call.message, value)


@dp.callback_query_handler(lambda call: call.data.split("_")[0] == "option")
async def option_img(call: types.CallbackQuery):
    row_id = call.data.split("_")[2]
    img_id = call.data.split("_")[1]
    user_id = call.message.chat.id
    price_img = float(getConfig("discord")["price_requests"])
    async with DataBase() as db:
        balance = await getBalance(user_id, db)
        if not enough_funds(balance, price_img):
            msg = insufficient_funds_message(balance, price_img)
            await call.message.answer(
                msg, reply_markup=no_money_keyboard(), parse_mode=types.ParseMode.HTML
            )
            return
        query = await db.read("images", where=f"id={row_id}")
        response = Upscale(
            img_id, query[0]["discord_message_id"], query[0]["discord_message_hash"]
        )
        if response.status_code >= 400:
            await call.message.answer("Ошибка запроса, попробуйте снова")
        else:
            await call.message.answer(
                "Ваше изображение готовится, пожалуйста, подождите минутку..."
            )
