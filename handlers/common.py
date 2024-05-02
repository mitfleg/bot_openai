import json


async def getBalance(user_id, db):
    balance = await db.read("users", ["balance"], where=f"user_id={user_id}")
    return balance[0]["balance"]


def enough_funds(balance, price_per_request):
    return balance >= price_per_request


def insufficient_funds_message(balance, price_per_request):
    msg = "❌ Недостаточно средств!\n"
    msg += "- - - - - - - - - - - - - -\n"
    msg += f"<b>Баланс:</b> <code>{balance:.2f}₽</code>\n"
    msg += f"<b>Стоимость запроса:</b> <code>{price_per_request:.2f}₽</code>"
    return msg


def getConfig(key):
    with open("./config.json") as f:
        return json.load(f)[f"{key}"]
