from datetime import datetime
import os
from aiogram import types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from bot import dp, bot
from .keyboard import account_keyboard
from .db import DataBase
from .savehtml import save_html


def decline_word(n):
    days = ['день', 'дня', 'дней']

    if n % 10 == 1 and n % 100 != 11:
        p = 0
    elif 2 <= n % 10 <= 4 and (n % 100 < 10 or n % 100 >= 20):
        p = 1
    else:
        p = 2
    return str(n) + ' ' + days[p]


def get_month(n):
    month = [
        'января',
        'февраля',
        'марта',
        'апреля',
        'мая',
        'июня',
        'июля',
        'августа',
        'сентября',
        'октября',
        'ноября',
        'декабря',
    ]
    return month[n]


@dp.callback_query_handler(text='account')
async def cmdaccount(call: types.CallbackQuery):
    user_id = call.message.chat.id
    async with DataBase() as db:
        user = await db.read('users', where=f'user_id={user_id}')
        user = user[0]
    date_created = user['date_created'].strftime('%d.%m.%Y')
    now_date = datetime.now()
    date_diff = now_date - user['date_created']
    date_diff = date_diff.days if date_diff.days > 0 else 1
    balance = user['balance']
    count_requests = user['count_requests']
    msg = '<b>Мой аккаунт</b>\n'
    msg += '<i>Вся необходимая информация о вашем профиле</i>\n\n'
    msg += f'👁‍🗨 <b>ID</b>: <code> {user_id}</code>\n'
    msg += f'👁‍🗨 <b>Регистрация</b>: <code> {date_created} ({decline_word(date_diff)})</code>\n\n'

    msg += f'💶 <b>Мой кошелёк</b>: <code> {balance}₽</code>\n\n'

    msg += f'🔎 <b>Моя статистика запросов</b>:\n'
    msg += f'<b>└ Всего запросов:</b> <code> {count_requests}</code>\n'

    await call.message.edit_text(msg, reply_markup=account_keyboard(), parse_mode=types.ParseMode.HTML)


@dp.callback_query_handler(text="operations")
async def operations(call: types.CallbackQuery):
    user_id = call.message.chat.id
    message_id = call.message.message_id
    async with DataBase() as db:
        operations = await db.read('payment', where=f'user_id={user_id}')

    if not operations:
        await call.answer('⛔️ Операции не найдены', show_alert=True)
        return

    grouped_items = {}
    for item in operations:
        date = item['date_created'].strftime('%d.%m.%Y')
        if date in grouped_items:
            grouped_items[date].append(item)
        else:
            grouped_items[date] = [item]

    msg = '<b>Последние операции</b>\n'
    msg += '<i>Вы можете просмотреть список совершенных Вами операций</i>\n'
    msg += '<i>Подробности доступны при нажатии кнопки "Показать все операции"</i>\n\n'
    count = 0
    for item_date in grouped_items:
        if count == 10:
            break
        msg += '<b>{}</b>\n'.format(item_date)
        for item in grouped_items[item_date]:
            if count == 10:
                break
            status_map = {
                'paid': '<b>Пополнение счета</b>',
                'pending': '<b>Ожидание оплаты</b>',
                'cancelled': '<b>Отмена</b>'
            }
            status = 'Статус: {}'.format(status_map.get(item['status'], ''))
            time = item['date_created'].strftime('%H:%M')
            msg += '[{}] {}\n'.format(time, status)
            count += 1
        msg += '\n'
    inline_btn_1 = InlineKeyboardButton(
        'Показать все операции', callback_data='all_operations')
    back = InlineKeyboardButton(
        '🔙 Назад', callback_data='back_account')
    inline_kb1 = InlineKeyboardMarkup().row(inline_btn_1).add(back)
    await bot.edit_message_text(msg, call.message.chat.id, message_id, reply_markup=inline_kb1, parse_mode=types.ParseMode.HTML)


@dp.callback_query_handler(text="all_operations")
async def all_operations(call: types.CallbackQuery):
    user_id = call.message.chat.id
    async with DataBase() as db:
        operations = await db.read('payment', where=f'user_id={user_id}')

    if not operations:
        await call.answer('⛔️ Операции не найдены', show_alert=True)
        return

    grouped_items = {}
    for item in operations:
        date_str = item["date_created"].strftime("%d.%m.%Y")
        if date_str not in grouped_items:
            grouped_items[date_str] = []
        grouped_items[date_str].append(item)

    doc = save_html(grouped_items)
    cancel = InlineKeyboardButton('❌ Закрыть', callback_data='cancel')
    inline_kb1 = InlineKeyboardMarkup().row(cancel)

    await call.message.delete()
    await bot.send_document(
        user_id,
        open(doc, 'rb'),
        caption='📁 Ответ на <b>Ваш запрос</b> в виде файла HTML',
        reply_markup=inline_kb1,
        parse_mode=types.ParseMode.HTML
    )
    os.remove(doc)


@dp.callback_query_handler(text="cancel")
async def cancel(call: types.CallbackQuery):
    await call.message.delete()
