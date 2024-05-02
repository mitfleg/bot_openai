from bot import dp
from aiogram import types
from .db import DataBase
from datetime import datetime, timedelta


@dp.callback_query_handler(lambda call: call.data.split('_')[0] == 'loging')
async def loging(call: types.CallbackQuery):
    type_log = call.data.split('_')[1]
    user_id = call.message.chat.id
    if type_log == 'yes':
        async with DataBase() as db:
            await db.update('users', ['is_authenticated'], [1], where=f"user_id={user_id}")
            await call.message.delete()
    if type_log == 'no':
        await call.message.delete()
