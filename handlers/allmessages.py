from datetime import datetime
import logging
import os
import re
import traceback
import speech_recognition as sr
import openai
from aiogram import types
from bot import dp, bot
from handlers.common import (
    enough_funds,
    getBalance,
    getConfig,
    insufficient_funds_message,
)
from handlers.dialog import dialogMain
from .slai import PassPromptToSelfBot
from .db import DataBase
from pydub import AudioSegment
from speech_recognition import UnknownValueError
from .keyboard import no_money_keyboard
import requests


openai.api_key = getConfig("openai")
ADMIN_ID = getConfig("admin_id")
commands = getConfig("commands")


async def getText(value):
    try:
        # response = openai.ChatCompletion.create(
        #    model="gpt-3.5-turbo",
        #    prompt=value,
        #    temperature=1,
        #    max_tokens=2000,
        #    top_p=0,
        #    frequency_penalty=0,
        #    presence_penalty=0.6,
        # )
        messages = []
        messages.append({"role": "user", "content": value})
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo", messages=messages
        )
    except Exception as e:
        return "Error generating text: {}".format(str(e))
    response = response["choices"][0]["message"]["content"]
    if response[:1] == ":":
        response = response[1:]
    return response.strip()


async def is_image(url):
    response = requests.get(url)
    return response.headers.get("Content-Type").startswith("image/")


async def mainMessage(message, value):
    user_id = message.chat.id
    message_id = message.message_id
    username = message.from_user.username
    price_per_request = float(getConfig("price_requests"))
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

            await message.answer(
                "⌛️<b>Генерация текста...</b>",
                reply=False,
                parse_mode=types.ParseMode.HTML,
            )
            text = await getText(value)

            if text:
                await db.update("users", ["last_login"], [datetime.now()], where=f"user_id={user_id}")
                await db.increment( "users", "count_requests", 1, where=f"user_id={user_id}")
                await db.decrement("users", "balance", price_per_request, where=f"user_id={user_id}")
                try:
                    await bot.edit_message_text(text, user_id, message_id + 1)
                except:
                    await bot.delete_message(user_id, message_id + 1)
                    print(text)
                    await message.answer(text)
            else:
                await message.answer("Ошибка генерации текста")
    except Exception as e:
        logging.error(traceback.format_exc())
        await bot.send_message(ADMIN_ID, traceback.format_exc())
        await message.answer("Произошла ошибка, попробуйте повторить запрос.\nРазработчик уже в курсе ошибки, и скоро она будет исправлена.\nСпасибо за понимание." )


async def mainImageMessage(message, value=""):
    user_id = message.chat.id
    price_img = float(getConfig("discord")["price_requests"])
    async with DataBase() as db:
        balance = await getBalance(user_id, db)
    if not enough_funds(balance, price_img):
        msg = insufficient_funds_message(balance, price_img)
        await message.answer(
            msg, reply_markup=no_money_keyboard(), parse_mode=types.ParseMode.HTML
        )
        return
    if not value:
        value = re.sub(" +", " ", message.text[5:])
        if re.search("(?P<url>https?://[^\s]+)", value):
            await message.answer(
                "Работа с ссылками на данный момент не поддерживается.\nОжидайте анонса функции.."
            )
            return
        value = await getText("Переведи на Английский: " + value)
        while "Error generating text" in value:
            value = await getText("Переведи на Английский: " + value)
    prompt = f"prompt:{value}"
    response = PassPromptToSelfBot(prompt)
    if response.status_code >= 400:
        await message.answer("Ошибка запроса, попробуйте снова")
    else:
        async with DataBase() as db:
            await db.delete("images", where=f"request='{value}'")
            await db.create(
                "images",
                ["message_id", "request", "user_id"],
                [message.message_id + 1, value, message.chat.id],
            )
        await message.answer(
            "Ваше изображение готовится, пожалуйста, подождите минутку..."
        )


@dp.message_handler(lambda msg: msg.text[:4] == "/img")
async def start_img(message: types.Message):
    return
    await mainImageMessage(message)


@dp.message_handler(lambda message: message.text not in commands)
async def allmessages(message: types.Message):
    user_id = message.chat.id
    async with DataBase() as db:
        dialogs = await db.read(
            "dialogs", where="user_id={} AND is_active=1".format(user_id)
        )
        if dialogs:
            await dialogMain(message)
            return
    await mainMessage(message, message.text)


@dp.message_handler(content_types=["voice"])
async def process_voice_message(message: types.Message):
    file = await bot.get_file(message.voice.file_id)
    await file.download(destination_file="voice.ogg")
    given_audio = AudioSegment.from_file("voice.ogg", format="ogg")
    given_audio.export("voice.wav", format="wav")
    r = sr.Recognizer()
    with sr.AudioFile("voice.wav") as source:
        audio_data = r.record(source)
        try:
            text = r.recognize_google(audio_data, language="RU-ru")
            await mainMessage(message, text)
        except UnknownValueError:
            await message.answer("Сообщение не распознанно")
    os.remove("voice.wav")
    os.remove("voice.ogg")
