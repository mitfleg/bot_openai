import asyncio
from datetime import datetime, timedelta
import uuid
from aiogram import types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from bot import dp, bot
from .keyboard import replenish_keyboard
from yookassa import Configuration, Payment
from .db import DataBase
from handlers.common import getConfig


Configuration.account_id = getConfig("yookassa")["account_id"]
Configuration.secret_key = getConfig("yookassa")["secret_key"]


async def payment_checker():
    while True:
        async with DataBase() as db:
            payments = await db.read("payment", where="status='pending'")
            current_time = datetime.now()
            new_time = current_time - timedelta(hours=1)
            for pay in payments:
                if pay["date_created"] < new_time:
                    await db.update(
                        "payment",
                        ["status"],
                        ["cancelled"],
                        where=f"pay_key='{pay['pay_key']}'",
                    )
                client = Payment().find_one(pay["pay_key"])
                if client.status == "succeeded":
                    await db.update(
                        "payment",
                        ["status"],
                        ["paid"],
                        where=f"pay_key='{pay['pay_key']}'",
                    )
                    await db.increment(
                        "users",
                        "balance",
                        pay["deposit_amount"],
                        f'user_id={pay["user_id"]}',
                    )
                    msg = "✅ <b>Зачисление средств</b>\n"
                    msg += f"<b>├ ID операции:</b> <code>{pay['pay_key']}</code>\n"
                    msg += f"<b>└ Сумма: </b> <code>{pay['deposit_amount']}₽</code>"
                    await bot.send_message(
                        pay["user_id"], msg, parse_mode=types.ParseMode.HTML
                    )
                    await bot.send_message(
                        getConfig("admin_id"), msg, parse_mode=types.ParseMode.HTML
                    )
        await asyncio.sleep(30)


async def payment_link(deposit_amount, user_id):
    payment = Payment.create(
        {
            "amount": {"value": deposit_amount, "currency": "RUB"},
            "confirmation": {
                "type": "redirect",
                "return_url": "https://t.me/wtwa_chatgpt_bot",
            },
            "capture": True,
            "description": "Пополнение баланса. ID пользователя: " + str(user_id),
        },
        uuid.uuid4(),
    )
    key = payment.id
    status = payment.status
    async with DataBase() as db:
        await db.create(
            "payment",
            ["pay_key", "user_id", "deposit_amount", "status"],
            [key, user_id, deposit_amount, status],
        )
    result = {"id": payment.id, "link": payment.confirmation.confirmation_url}
    return result


@dp.callback_query_handler(text="replenish")
async def replenish(call: types.CallbackQuery):
    await call.message.edit_text(
        "Выберите сумму пополнения:",
        reply_markup=replenish_keyboard(),
        parse_mode=types.ParseMode.HTML,
    )


@dp.callback_query_handler(text=["10", "50", "100", "500"])
async def replenish_add(call: types.CallbackQuery):
    user_id = call.message.chat.id
    deposit_amount = call.data
    message_id = call.message.message_id
    payment_info = await payment_link(deposit_amount, user_id)
    if payment_info["link"]:
        inline_btn_1 = InlineKeyboardButton(text="Оплатить", url=payment_info["link"])
        inline_kb1 = InlineKeyboardMarkup().add(inline_btn_1)
        msg = f"💳 Для пополнения счета на <code>{deposit_amount}₽</code> <b>перейдите по ссылке:</b>\n"
        msg += "Данное сообщение <b>автоматически</b> удалится через минуту"
        await call.message.answer(
            msg, reply_markup=inline_kb1, parse_mode=types.ParseMode.HTML
        )
        await asyncio.sleep(60)
        try:
            await bot.delete_message(user_id, message_id + 1)
        except:
            pass
