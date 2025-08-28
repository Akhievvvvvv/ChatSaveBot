# main.py
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient, events
import json
from config import API_ID, API_HASH, ADMIN_ID, DATA_PATH, FREE_DAYS, TARIFFS, BANK_REQUISITES

# TelegramClient для личных чатов (Business)
client = TelegramClient("session", API_ID, API_HASH)

# aiogram Bot для меню и уведомлений
bot = Bot(token="8253356529:AAG5sClokG30SlhqpP3TNMdl6TajExIE7YU")
dp = Dispatcher(bot)

os.makedirs(DATA_PATH, exist_ok=True)
USER_DATA_FILE = os.path.join(DATA_PATH, "users.json")

# Загрузка данных пользователей
if os.path.exists(USER_DATA_FILE):
    with open(USER_DATA_FILE, "r", encoding="utf-8") as f:
        users = json.load(f)
else:
    users = {}

def save_users():
    with open(USER_DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=4)

# Вспомогательные функции
def save_deleted_message(chat_id, user_id, user_name, message):
    path = os.path.join(DATA_PATH, f"{chat_id}.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {user_name} ({user_id}): {message}\n")

def save_deleted_chat(chat_id, chat_title):
    path = os.path.join(DATA_PATH, "deleted_chats.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {chat_title} ({chat_id}) был удалён\n")

def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🚀 Активировать 7 дней бесплатно", callback_data="activate_free"),
        InlineKeyboardButton("💳 Тарифы", callback_data="tariffs"),
        InlineKeyboardButton("🔗 Реферальная система", callback_data="referrals"),
        InlineKeyboardButton("📊 Статистика", callback_data="stats")
    )
    return kb

def tariffs_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("14 дней — 49₽", callback_data="tariff_14"),
        InlineKeyboardButton("30 дней — 99₽", callback_data="tariff_30"),
        InlineKeyboardButton("60 дней — 149₽", callback_data="tariff_60"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_main")
    )
    return kb

def referrals_menu(user_id):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton(f"🔗 Ваша личная ссылка", url=f"https://t.me/Chat_ls_save_bot?start={user_id}")
    )
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="back_main"))
    return kb

def format_stats(user_id):
    user = users.get(str(user_id), {})
    end_date = datetime.fromisoformat(user.get("end_date", datetime.now().isoformat()))
    days_left = (end_date - datetime.now()).days
    referrals = user.get("referrals", [])
    activated = sum(1 for r in referrals if users.get(str(r), {}).get("active"))
    return f"📊 *Статистика:*\n\n" \
           f"⏳ Осталось дней: {days_left}\n" \
           f"🔗 Рефералов перешло: {len(referrals)}\n" \
           f"✅ Активировали бота: {activated}"

# Приветствие
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = str(message.from_user.id)
    if user_id not in users:
        users[user_id] = {"active": False, "end_date": (datetime.now() + timedelta(days=FREE_DAYS)).isoformat(), "referrals": []}
        save_users()
    text = (
        "✨ *Добро пожаловать в ChatSaveBot!*\n\n"
        "Этот бот сохраняет:\n"
        "• 📝 Удалённые сообщения\n"
        "• 📸 Однократные фото/видео/голосовые\n"
        "• ❌ Удалённые чаты\n\n"
        f"🎁 *Бесплатный период:* {FREE_DAYS} дней\n\n"
        "Выберите действие ниже:"
    )
    await message.answer(text, reply_markup=main_menu(), parse_mode="Markdown")

@dp.callback_query_handler(lambda c: True)
async def callbacks(call: types.CallbackQuery):
    data = call.data
    user_id = str(call.from_user.id)
    user = users.get(user_id, {})

    if data == "activate_free":
        users[user_id]["active"] = True
        users[user_id]["end_date"] = (datetime.now() + timedelta(days=FREE_DAYS)).isoformat()
        save_users()
        await call.message.answer(
            "✅ *Ваш бесплатный период активирован!* 🎉\n\n"
            "📌 *Инструкция по подключению:*\n"
            "1️⃣ Включите бизнес-режим\n"
            "2️⃣ Добавьте бота в 'Чат-боты' в Telegram Business\n"
            "3️⃣ Бот начнёт сохранять все удалённые сообщения и медиа",
            parse_mode="Markdown"
        )

    elif data == "tariffs":
        await call.message.answer("💳 *Выберите тариф:*",
                                  reply_markup=tariffs_menu(), parse_mode="Markdown")

    elif data.startswith("tariff_"):
        t_name = data.replace("tariff_", "")
        price_map = {"14": 49, "30": 99, "60": 149}
        price = price_map[t_name]
        text = (
            f"💳 Вы выбрали тариф *{t_name} дней* за *{price}₽*\n\n"
            f"🏦 *Реквизиты для оплаты:*\n{BANK_REQUISITES}\n\n"
            "После оплаты нажмите кнопку 'Оплатил(а)'"
        )
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("✅ Оплатил(а)", callback_data=f"paid_{t_name}"))
        kb.add(InlineKeyboardButton("◀️ Назад", callback_data="tariffs"))
        await call.message.answer(text, reply_markup=kb, parse_mode="Markdown")

    elif data.startswith("paid_"):
        t_name = data.replace("paid_", "")
        await bot.send_message(
            ADMIN_ID,
            f"👤 Пользователь *{call.from_user.full_name}* ({user_id}) выбрал тариф {t_name}\nНажмите ✅ Подтвердить оплату",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"confirm_{user_id}_{t_name}")
            )
        )
        await call.message.answer("⏳ Ваша заявка отправлена на подтверждение администратору.", parse_mode="Markdown")

    elif data.startswith("confirm_"):
        parts = data.split("_")
        u_id, t_name = parts[1], parts[2]
        users[u_id]["active"] = True
        users[u_id]["end_date"] = (datetime.now() + timedelta(days=int(t_name))).isoformat()
        save_users()
        await bot.send_message(
            u_id,
            f"🎉 *Оплата подтверждена!*\nВы подключили тариф: *{t_name} дней*\n\n"
            "📌 *Инструкция по подключению:*\n"
            "1️⃣ Включите бизнес-режим\n"
            "2️⃣ Добавьте бота в 'Чат-боты'\n"
            "3️⃣ Бот начнёт сохранять удалённые сообщения и однократные медиа",
            parse_mode="Markdown"
        )
        await call.message.answer(f"✅ Оплата пользователя {u_id} подтверждена", parse_mode="Markdown")

    elif data == "referrals":
        await call.message.answer("🔗 *Ваша реферальная ссылка и статистика:*",
                                  reply_markup=referrals_menu(user_id), parse_mode="Markdown")

    elif data == "stats":
        await call.message.answer(format_stats(user_id), parse_mode="Markdown")

    elif data == "back_main":
        await call.message.answer("🏠 Главное меню:", reply_markup=main_menu())

    await call.answer()

# Отслеживание удалённых сообщений
@client.on(events.MessageDeleted)
async def deleted_messages(event):
    chat = await event.get_chat()
    for msg_id in event.deleted_ids:
        try:
            msg = await client.get_messages(chat, ids=msg_id)
            text = msg.text if msg else "<медиа/голосовое или удалённое>"
            sender = await msg.get_sender() if msg else None
            user_name = sender.first_name if sender else "Неизвестный"
            user_id = sender.id if sender else 0
        except:
            text = "<удалённое сообщение>"
            user_name = "Неизвестный"
            user_id = 0

        save_deleted_message(chat.id, user_id, user_name, text)
        # Отправка пользователю
        if str(user_id) in users and users[str(user_id)]["active"]:
            await bot.send_message(user_id, f"📝 Удалено сообщение в {chat.title}:\n{text}")

# Отслеживание удалённых чатов
@client.on(events.ChatAction)
async def deleted_chats(event):
    if event.user_left or event.user_kicked:
        chat = await event.get_chat()
        save_deleted_chat(chat.id, getattr(chat, "title", "Чат"))
        for u_id, u_data in users.items():
            if u_data.get("active"):
                await bot.send_message(int(u_id), f"❌ Удалён чат: {getattr(chat, 'title', 'Чат')} ({chat.id})")

async def start_aiogram():
    await dp.start_polling()

async def main():
    await asyncio.gather(client.start(), start_aiogram())

if __name__ == "__main__":
    asyncio.run(main())
