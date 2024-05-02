from aiogram import types
from bot import dp, bot
from aiogram.dispatcher.filters.builtin import CommandStart
from .db import DataBase
from .keyboard import main_keyboard
from handlers.common import getConfig

ADMIN_ID = getConfig("admin_id")


def start_msg():
    msg = "<b>Я ChatGPT, крупная языковая модель, разработанная OpenAI.\n\n"
    msg += "Я являюсь обученной языковой моделью OpenAI, умею генерировать тексты и отвечать на вопросы, основываясь на моей обученной информации (обучение было завершено в 2021 году).\n\n"
    msg += "Я также умею выполнять задачи по переводу, суммаризации, генерации последовательностей и многое другое.\n\n"
    msg += 'Перед началом работы, изучите документацию. Найти ее можно в разделе "О сервисе".\n\n'
    msg += "Чем я могу тебе помочь?</b>"
    return msg


@dp.message_handler(CommandStart())
async def cmdstart(message: types.Message):
    msg = "🙋 <b>Привет!</b>"
    msg += start_msg()
    user_name = message.from_user.username
    user_id = message.chat.id
    if user_name == None:
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
    async with DataBase() as db:
        await db.create("users", ["user_name", "user_id"], [user_name, user_id])
        try:
            msg_adm = "Новая регистрация\n"
            msg_adm += "Пользователь: <b>" + user_name + "</b>"
            await bot.send_message(ADMIN_ID, msg_adm, types.ParseMode.HTML)
        except:
            pass
    await message.answer(
        msg, reply_markup=main_keyboard(user_id), parse_mode=types.ParseMode.HTML
    )


@dp.message_handler(commands="menu")
async def cmdmenu(message: types.Message):
    msg = start_msg()
    await message.answer(
        msg,
        reply_markup=main_keyboard(message.chat.id),
        parse_mode=types.ParseMode.HTML,
    )
