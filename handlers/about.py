import json
from aiogram import types
from bot import dp
from .keyboard import back


@dp.callback_query_handler(text='about')
async def about(call: types.CallbackQuery):
    with open('config.json', "r", encoding="utf8") as f:
        about = json.load(f)['about_page']
    msg = 'ℹ️ <b>Полезная информация</b>\n\n'
    for i in about:
        msg += f"<b>{i['descr']}</b>:\n{i['link']}\n\n"

    await call.message.edit_text(msg, reply_markup=back('main'), parse_mode=types.ParseMode.HTML, disable_web_page_preview=True)
