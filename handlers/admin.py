from aiogram import types
from bot import dp, bot
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.dispatcher import FSMContext
from .db import DataBase
from .paginator import Paginator


class UserName(StatesGroup):
    user_id = State()
    summ = State()
    name = State()


class MessageAll(StatesGroup):
    message = State()


@dp.callback_query_handler(lambda call: call.data == 'admin')
async def admin_main(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    inline_btn_1 = InlineKeyboardButton(
        '💵 Пополнить счет', callback_data='setbalance')
    message_admin = InlineKeyboardButton(
        '📨 Рассылка', callback_data='message_all')
    back = InlineKeyboardButton(
        '🔙 Назад', callback_data='back_main')
    inline_kb1 = InlineKeyboardMarkup().row(inline_btn_1, message_admin).add(back)
    msg = '<b>Функционал администратора</b>'
    await bot.edit_message_text(msg, chat_id, message_id, reply_markup=inline_kb1, parse_mode=types.ParseMode.HTML)


@dp.callback_query_handler(lambda call: call.data == 'setbalance')
async def setbalance(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    async with DataBase() as db:
        users = await db.read('users')
        kb = types.InlineKeyboardMarkup()
    for item in users:
        kb.add(types.InlineKeyboardButton(
            text=item['user_name']+f" ({str(item['balance'])})", callback_data='user_chat_id|'+str(item['user_id'])))
    paginator = Paginator(
        data=kb, size=5, dp=dp, cancel_text='❌ Закрыть', cancel_callback='cancel|admin')
    msg = 'Выберите имя пользователя'
    await bot.edit_message_text(msg, chat_id, message_id, reply_markup=paginator(), parse_mode=types.ParseMode.HTML)
    await UserName.user_id.set()


@dp.callback_query_handler(lambda call: call.data.split('|')[0] == 'user_chat_id', state=["*"])
async def user_chat_id(call: types.CallbackQuery, state: FSMContext):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    user_id = call.data.split('|')[1]
    await state.update_data(user_id=user_id)
    try:
        await bot.delete_message(chat_id, message_id-1)
        await bot.delete_message(chat_id, message_id)
    except:
        pass
    cancel = InlineKeyboardButton('❌ Закрыть', callback_data='cancel|admin')
    inline_kb1 = InlineKeyboardMarkup().add(cancel)
    await call.message.answer('Введите сумму', reply_markup=inline_kb1, parse_mode=types.ParseMode.HTML)
    await UserName.next()


@dp.message_handler(state=UserName.summ)
async def user_summ_set(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    message_id = message.message_id
    await state.update_data(summ=message.text)
    data = await state.get_data()
    try:
        await bot.delete_message(chat_id, message_id-1)
        await bot.delete_message(chat_id, message_id)
    except:
        pass
    async with DataBase() as db:
        info_user = await db.read('users', where=f"user_id={data['user_id']}")
        info_user = info_user[0]
    if info_user == None:
        back = InlineKeyboardButton(
            '🔙 Назад', callback_data='back_main')
        inline_kb1 = InlineKeyboardMarkup().row(back)
        await message.answer('Пользователь не найден', reply_markup=inline_kb1, parse_mode=types.ParseMode.HTML)
        await state.finish()
        return
    msg = f"Пользователь: <code>{info_user['user_name']}</code>\n"
    msg += f"Текущий баланс: <code>{str(info_user['balance'])}₽</code>\n"
    msg += f"Новый баланс: <code>{str(data['summ'])}₽</code>\n"
    yes = InlineKeyboardButton('✅ Да', callback_data='setbalance_yes')
    no = InlineKeyboardButton('❌ Нет', callback_data='setbalance_no')
    inline_kb1 = InlineKeyboardMarkup().row(yes, no)
    await message.answer(msg, reply_markup=inline_kb1, parse_mode=types.ParseMode.HTML)


@dp.callback_query_handler(lambda call: call.data == 'setbalance_yes', state=["*"])
async def setbalance_yes(call: types.CallbackQuery, state: FSMContext):
    data = await state.get_data()
    user_id = data['user_id']
    balance = data['summ']
    async with DataBase() as db:
        await db.update('users', ['balance'], [balance], where=f"user_id='{data['user_id']}'")
    await call.answer('Баланс успешно изменен', show_alert=True)
    await bot.send_message(user_id, '✅ Зачисление средств на сумму <code>'+balance+'₽</code>', parse_mode=types.ParseMode.HTML)
    await admin_main(call)
    await state.finish()


@dp.callback_query_handler(lambda call: call.data == 'setbalance_no', state=["*"])
async def setbalance_no(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    await admin_main(call)


@dp.callback_query_handler(lambda call: call.data.split('|')[0] == 'cancel', state=["*"])
async def cancel(call: types.CallbackQuery, state: FSMContext):
    await state.finish()
    url_back = call.data.split('|')[1]
    if url_back == 'admin':
        await admin_main(call)


@dp.callback_query_handler(lambda call: call.data == 'message_all')
async def message_all(call: types.CallbackQuery):
    chat_id = call.message.chat.id
    message_id = call.message.message_id
    await MessageAll.message.set()
    msg = '<b>Введите сообщение</b>\n'
    msg += 'После отправки сообщения в бота, это сообщение <b>увидят все.</b>\n'
    msg += 'Будьте предельно аккуратны\n'
    cancel = InlineKeyboardButton('❌ Отмена', callback_data='cancel|admin')
    inline_kb1 = InlineKeyboardMarkup().add(cancel)
    await bot.edit_message_text(msg, chat_id, message_id, reply_markup=inline_kb1, parse_mode=types.ParseMode.HTML)


@dp.message_handler(state=MessageAll.message)
async def MessageAll_send(message: types.Message, state: FSMContext):
    chat_id = message.chat.id
    message_id = message.message_id
    await state.update_data(message=message.text)
    data = await state.get_data()
    async with DataBase() as db:
        all_users = await db.read('users')
    try:
        await bot.delete_message(chat_id, message_id-1)
        await bot.delete_message(chat_id, message_id)
    except:
        pass
    for item in all_users:
        user_id = item['user_id']
        try:
            await bot.send_message(user_id, data['message'])
        except:
            pass
    await state.finish()
