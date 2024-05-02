from bot import dp
from aiogram import types
from .keyboard import main_keyboard
from .account import cmdaccount
from .start import start_msg


@dp.callback_query_handler(lambda c: c.data.split('_')[0] == 'back')
async def back(call: types.CallbackQuery):
    page = call.data.split('_')[1]
    if page == 'main':
        msg = start_msg()
        await call.message.edit_text(msg, reply_markup=main_keyboard(call.message.chat.id), parse_mode=types.ParseMode.HTML)
    elif page == 'account':
        await cmdaccount(call)
