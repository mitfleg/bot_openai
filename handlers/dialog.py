from datetime import datetime
import logging
import traceback
import openai
from aiogram import types
from bot import dp, bot
from handlers.common import (
    enough_funds,
    getBalance,
    getConfig,
    insufficient_funds_message,
)
from handlers.start import ADMIN_ID
from .db import DataBase


openai.api_key = getConfig("openai")
price_per_request = float(getConfig("price_requests"))


async def getText(value):
    try:
        response = openai.ChatCompletion.create(model="gpt-3.5-turbo", messages=value)
    except Exception as e:
        return "Error generating text: {}".format(str(e))
    response = response["choices"][0]["message"]["content"]
    if response[:1] == ":":
        response = response[1:]
    return response.strip()


@dp.message_handler(commands="dialog")
async def createdialog(message: types.Message):
    user_id = message.chat.id
    async with DataBase() as db:
        dialogs = await db.read(
            "dialogs", where="user_id={} AND is_active=1".format(user_id)
        )
        for item in dialogs:
            await db.update("dialogs", ["is_active"], [0], where=f"id={item['id']}")
        await db.insert("dialogs", ["user_id"], [user_id])
        await message.answer(
            "✅ Диалог создан! Напишите что-нибудь, чтобы начать общение. Чтобы закрыть диалог, выберите соответствующий пункт в меню",
            reply=False,
            parse_mode=types.ParseMode.HTML,
        )



async def dialogMain(message):
    user_id = message.chat.id
    message_id = message.message_id
    username = message.from_user.username
    if username == None:
        msg = "🤔 <b>Имя пользователя не найдено.</b>\n\n "
        msg += "Ниже приведены шаги для создания username в приложении Telegram\n"
        msg += "1)Настройки\n"
        msg += "2)Изменить\n"
        msg += "3)Имя пользователя\n"
        msg += '4)"Введите имя"\n'
        msg += "5)Готово\n"
        msg += "После повторите команду /start\n "
        await message.answer(msg, parse_mode=types.ParseMode.HTML)
        return
    try:
        async with DataBase() as db:
            await db.create("users", ["user_name", "user_id"], [username, user_id])
            balance = await getBalance(user_id, db)

            if not enough_funds(balance, price_per_request):
                msg = insufficient_funds_message(balance, price_per_request)
                await message.answer(msg, reply=False, parse_mode=types.ParseMode.HTML)
                return

            dialogs = await db.read("dialogs", where=f"user_id={user_id} AND is_active=1")
            dialog_id = dialogs[0]["id"]
            await db.insert("messages",["dialog_id", "role", "message"],[dialog_id, "user", message.text])
            messages = await db.read("messages", where=f"dialog_id={dialog_id}")
            query = [{"role": item["role"], "content": item["message"]} for item in messages]
            await message.answer("⌛️<b>Генерация текста...</b>",reply=False,parse_mode=types.ParseMode.HTML)
            text = await getText(query)

            if text:
                await db.insert( "messages", ["dialog_id", "role", "message"], [dialog_id, "system", text])
                await db.update("users", ["last_login"], [datetime.now()], where=f"user_id={user_id}")
                await db.increment("users", "count_requests", 1, where=f"user_id={user_id}")
                await db.decrement("users", "balance", price_per_request, where=f"user_id={user_id}")
                try:
                    await bot.edit_message_text(text, user_id, message_id + 1)
                except:
                    await bot.delete_message(user_id, message_id + 1)
                    await message.answer(text)
            else:
                await message.answer("Ошибка генерации текста")
    except Exception as e:
        logging.error(traceback.format_exc())
        await bot.send_message(ADMIN_ID, traceback.format_exc())
        await message.answer(
            "Произошла ошибка, попробуйте повторить запрос.\nРазработчик уже в курсе ошибки, и скоро она будет исправлена.\nСпасибо за понимание."
        )


@dp.message_handler(commands="close")
async def closeDialog(message: types.Message):
    user_id = message.chat.id
    async with DataBase() as db:
        dialogs = await db.read("dialogs", where="user_id={} AND is_active=1".format(user_id))
        for item in dialogs:
            await db.update("dialogs", ["is_active"], [0], where="id={}".format(item['id']))
        await message.answer(
            "❌ Диалог закрыт", reply=False, parse_mode=types.ParseMode.HTML
        )
