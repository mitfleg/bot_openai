import json
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

def getConfig(key):
    with open('./config.json') as f:
        return json.load(f)[f'{key}']

def main_keyboard(user_id=None):
    markup = InlineKeyboardMarkup(row_width=2)
    button_account = InlineKeyboardButton(
        '⚙️ Аккаунт', callback_data='account')
    button_replenish = InlineKeyboardButton(
        '💰 Пополнить счет', callback_data='replenish')
    button_about = InlineKeyboardButton(
        'ℹ️ О сервисе', callback_data='about')
    markup.add(button_account, button_replenish, button_about)
    if int(user_id) == int(getConfig('admin_id')):
        button_adm = InlineKeyboardButton('Админ', callback_data='admin')
        markup.add(button_adm)
    return markup

def no_money_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    button_replenish = InlineKeyboardButton(
        '💰 Пополнить счет', callback_data='replenish')
    back = InlineKeyboardButton(
        '🔙 Назад', callback_data=f'back_main')
    markup.add(button_replenish, back)
    return markup


def back(page):
    markup = InlineKeyboardMarkup(row_width=1)
    back = InlineKeyboardButton(
        '🔙 Назад', callback_data=f'back_{page}')
    markup.add(back)
    return markup


def replenish_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    button_1 = InlineKeyboardButton("10", callback_data="10")
    button_2 = InlineKeyboardButton("50", callback_data="50")
    button_3 = InlineKeyboardButton("100", callback_data="100")
    button_4 = InlineKeyboardButton("500", callback_data="500")
    markup.add(button_1, button_2, button_3, button_4)
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup


def account_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    button_1 = InlineKeyboardButton("🧾 Операции", callback_data="operations")
    markup.add(button_1)
    markup.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return markup


def image_option_keyboard(row_id):
    markup = InlineKeyboardMarkup(row_width=2)
    button_1 = InlineKeyboardButton(
        "1️⃣", callback_data=f"option_1_{row_id}")
    button_2 = InlineKeyboardButton(
        "2️⃣", callback_data=f"option_2_{row_id}")
    button_3 = InlineKeyboardButton(
        "3️⃣", callback_data=f"option_3_{row_id}")
    button_4 = InlineKeyboardButton(
        "4️⃣", callback_data=f"option_4_{row_id}")
    update = InlineKeyboardButton("🔄 Получить еще", callback_data="update")
    markup.add(button_1, button_2, button_3, button_4, update)
    return markup


def image_upscale_keyboard():
    markup = InlineKeyboardMarkup(row_width=2)
    update = InlineKeyboardButton("🔄 Получить еще", callback_data="update")
    markup.add(update)
    return markup
