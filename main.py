import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor

# === НАСТРОЙКИ ===
TOKEN = "8253356529:AAG5sClokG30SlhqpP3TNMdl6TajExIE7YU"
ADMIN_GROUP_ID = -1002593269045  # твоя админ-группа
TRIAL_DAYS = 7
SUB_PRICE = "99₽ / месяц"
PAY_DETAILS = "💳 89322229930\n🏦 Ozon Банк\n💰 99₽/мес"

bot = Bot(token=TOKEN, parse_mode="HTML")
dp = Dispatcher(bot)

# Словарь для хранения пользователей
users = {}  # user_id: {trial_end, sub_end, referred_by, referrals, active}

# === ЛОГИ ===
logging.basicConfig(level=logging.INFO)


# === КНОПКИ ===
def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⚙️ Активировать бота", callback_data="activate"))
    return kb


def pay_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("👀 Посмотреть реквизиты", callback_data="pay_info"))
    return kb


def paid_button(user_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("✅ Оплатил(а)", callback_data=f"paid_{user_id}"))
    return kb


# === СТАРТ ===
@dp.message_handler(commands=["start"])
async def start_cmd(message: types.Message):
    user_id = message.from_user.id
    username = message.from_user.username or message.from_user.full_name

    if user_id not in users:
        users[user_id] = {
            "trial_end": datetime.now() + timedelta(days=TRIAL_DAYS),
            "sub_end": None,
            "referred_by": None,
            "referrals": [],
            "active": True
        }

    text = (
        f"👋 Привет, <b>{username}</b>!\n\n"
        "✨ Я — <b>Chat Save Bot</b>.\n"
        "Я умею сохранять 🗑️ удалённые и ⏳ одноразовые сообщения в чатах и диалогах!\n\n"
        f"🔥 Твой бесплатный пробный период: <b>{TRIAL_DAYS} дней</b>.\n\n"
        "Чтобы бот работал — нажми ниже 👇"
    )
    await message.answer(text, reply_markup=main_menu())


# === АКТИВАЦИЯ ===
@dp.callback_query_handler(lambda c: c.data == "activate")
async def activate_bot(call: types.CallbackQuery):
    text = (
        "⚡ Чтобы бот работал в личных чатах:\n\n"
        "1️⃣ Перейди в <b>Настройки</b>\n"
        "2️⃣ Открой <b>Telegram для бизнеса</b>\n"
        "3️⃣ Выбери <b>Чат-боты</b>\n"
        "4️⃣ Добавь меня: <b>@Chat_ls_save_bot</b>\n\n"
        "✅ Всё! Теперь я буду сохранять удалённые сообщения 🔥"
    )
    await call.message.edit_text(text)


# === ПОКАЗАТЬ РЕКВИЗИТЫ ===
@dp.callback_query_handler(lambda c: c.data == "pay_info")
async def show_payment(call: types.CallbackQuery):
    user_id = call.from_user.id
    text = (
        "💳 Для продления подписки оплати по реквизитам:\n\n"
        f"{PAY_DETAILS}\n\n"
        "После оплаты нажми кнопку ⬇️"
    )
    await call.message.edit_text(text, reply_markup=paid_button(user_id))


# === КНОПКА "ОПЛАТИЛ(А)" ===
@dp.callback_query_handler(lambda c: c.data.startswith("paid_"))
async def paid_request(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    username = call.from_user.username or call.from_user.full_name

    await bot.send_message(
        ADMIN_GROUP_ID,
        f"💸 Пользователь @{username} (ID: {user_id}) нажал 'Оплатил(а)'.\n"
        f"Сумма: {SUB_PRICE}\n⏰ {datetime.now().strftime('%d.%m.%Y %H:%M')}\n\n"
        f"Подтвердить оплату?",
        reply_markup=InlineKeyboardMarkup().add(
            InlineKeyboardButton("✅ Подтвердить", callback_data=f"confirm_{user_id}")
        )
    )
    await call.message.edit_text("⏳ Ожидается подтверждение оплаты администратором...")


# === АДМИН ПОДТВЕРЖДАЕТ ===
@dp.callback_query_handler(lambda c: c.data.startswith("confirm_"))
async def confirm_payment(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    if user_id in users:
        users[user_id]["sub_end"] = datetime.now() + timedelta(days=30)
        users[user_id]["active"] = True

    await bot.send_message(user_id, "🎉 Оплата подтверждена! Подписка активна ещё на 30 дней 🔥")
    await call.message.edit_text(f"✅ Оплата подтверждена для ID {user_id}")


# === НАПОМИНАЛКА ===
async def check_subscriptions():
    while True:
        now = datetime.now()
        for user_id, data in list(users.items()):
            # пробный период
            if data["trial_end"] and now > data["trial_end"] and not data["sub_end"]:
                await bot.send_message(
                    user_id,
                    "⏳ Твой бесплатный период закончился!\nПродли подписку, чтобы продолжить пользоваться ботом 🔥",
                    reply_markup=pay_menu()
                )
                users[user_id]["trial_end"] = None

            # подписка подходит к концу
            if data["sub_end"]:
                days_left = (data["sub_end"] - now).days
                if days_left in [3, 2, 1]:
                    await bot.send_message(
                        user_id,
                        f"⚠️ Ваша подписка закончится через <b>{days_left} дн.</b>!\n"
                        "Продли её заранее, чтобы не потерять доступ 🔥",
                        reply_markup=pay_menu()
                    )

                if now > data["sub_end"]:
                    users[user_id]["active"] = False
                    await bot.send_message(
                        user_id,
                        "❌ Подписка закончилась!\nПродли её, чтобы я снова работал 🙌",
                        reply_markup=pay_menu()
                    )
        await asyncio.sleep(3600)  # проверка раз в час


# === СТАРТ ПОЛЛИНГА ===
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(check_subscriptions())
    executor.start_polling(dp, skip_updates=True)
