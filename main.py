# main.py
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from telethon import TelegramClient, events
from config import API_ID, API_HASH, ADMIN_ID, DATA_PATH, FREE_DAYS, TARIFFS, BANK_REQUISITES

# TelegramClient для личных чатов (Business)
client = TelegramClient("session", API_ID, API_HASH)

# aiogram Bot для меню и уведомлений
bot = Bot(token="8253356529:AAG5sClokG30SlhqpP3TNMdl6TajExIE7YU")
dp = Dispatcher(bot)

os.makedirs(DATA_PATH, exist_ok=True)

# Вспомогательные функции
def save_deleted_message(chat_id, user_id, user_name, message):
    path = os.path.join(DATA_PATH, f"{chat_id}.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {user_name} ({user_id}): {message}\n")

def save_deleted_chat(chat_id, chat_title):
    path = os.path.join(DATA_PATH, f"deleted_chats.txt")
    with open(path, "a", encoding="utf-8") as f:
        f.write(f"[{datetime.now()}] {chat_title} ({chat_id}) был удалён\n")

# Главное меню
def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🚀 Активировать 7 дней бесплатно", callback_data="activate_free"),
        InlineKeyboardButton("💳 Тарифы", callback_data="tariffs"),
        InlineKeyboardButton("🔗 Реферальная система", callback_data="referrals")
    )
    return kb

# Меню тарифов
def tariffs_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("14 дней — 49₽", callback_data="tariff_14"),
        InlineKeyboardButton("30 дней — 99₽", callback_data="tariff_30"),
        InlineKeyboardButton("60 дней — 149₽", callback_data="tariff_60"),
        InlineKeyboardButton("◀️ Назад", callback_data="back_main")
    )
    return kb

# Реферальное меню
def referrals_menu(user_id):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(f"Ваша ссылка: https://t.me/Chat_ls_save_bot?start={user_id}", callback_data="ignore"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="back_main"))
    return kb

# Приветствие
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    text = (
        "✨ Добро пожаловать в ChatSaveBot!\n\n"
        "Этот бот сохраняет:\n"
        "• Удалённые сообщения\n"
        "• Однократные фото/видео/голосовые\n"
        "• Удалённые чаты\n\n"
        f"🎁 Бесплатный период: {FREE_DAYS} дней\n\n"
        "Выберите действие ниже:"
    )
    await message.answer(text, reply_markup=main_menu())

# Обработка кнопок
@dp.callback_query_handler(lambda c: True)
async def callbacks(call: types.CallbackQuery):
    data = call.data
    user = call.from_user

    if data == "activate_free":
        await call.message.answer(
            "✅ Бесплатный период активирован!\n\n"
            "Подробная инструкция:\n"
            "1. Включите бизнес-режим\n"
            "2. Добавьте бота в 'Чат-боты' в Telegram Business\n"
            "3. Бот начнёт сохранять все удалённые сообщения"
        )

    elif data == "tariffs":
        await call.message.answer("Выберите тариф:", reply_markup=tariffs_menu())

    elif data.startswith("tariff_"):
        tariff_name = data.replace("tariff_", "")
        price_map = {"14": 49, "30": 99, "60": 149}
        price = price_map[tariff_name]
        text = f"Вы выбрали тариф {tariff_name} дней за {price}₽\n\nРеквизиты для оплаты:\n{BANK_REQUISITES}\n\nПосле оплаты нажмите кнопку 'Оплатил(а)'"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Оплатил(а)", callback_data=f"paid_{tariff_name}"))
        kb.add(InlineKeyboardButton("◀️ Назад", callback_data="tariffs"))
        await call.message.answer(text, reply_markup=kb)

    elif data.startswith("paid_"):
        tariff_name = data.replace("paid_", "")
        await bot.send_message(
            ADMIN_ID,
            f"Пользователь {user.full_name} ({user.id}) выбрал тариф {tariff_name}\nНажмите ✅ Подтвердить оплату",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"confirm_{user.id}_{tariff_name}")
            )
        )
        await call.message.answer("Ваша заявка отправлена на подтверждение администратору.")

    elif data.startswith("confirm_"):
        parts = data.split("_")
        user_id = int(parts[1])
        tariff_name = parts[2]
        await bot.send_message(
            user_id,
            f"🎉 Оплата подтверждена!\nВы подключили тариф: {tariff_name} дней\n\n"
            "Инструкция по подключению:\n"
            "1. Включите бизнес-режим\n"
            "2. Добавьте бота в 'Чат-боты'\n"
            "3. Бот начнёт сохранять удалённые сообщения и однократные медиа"
        )
        await call.message.answer(f"Оплата пользователя {user_id} подтверждена ✅")

    elif data == "referrals":
        await call.message.answer("Ваша реферальная ссылка и статистика:", reply_markup=referrals_menu(user.id))

    elif data == "back_main":
        await call.message.answer("Главное меню:", reply_markup=main_menu())

    await call.answer()

# Telethon: отслеживание удалённых сообщений
@client.on(events.MessageDeleted)
async def deleted_messages(event):
    chat = await event.get_chat()
    for msg in event.deleted:
        sender = await msg.get_sender()
        text = msg.message or "<медиа/голосовое>"
        save_deleted_message(chat.id, sender.id, sender.first_name, text)
        await bot.send_message(ADMIN_ID, f"Удалено сообщение в {chat.title}:\n{text}")

# Telethon: отслеживание удалённых чатов
@client.on(events.ChatAction)
async def deleted_chats(event):
    if event.user_left or event.user_kicked:
        chat = await event.get_chat()
        save_deleted_chat(chat.id, getattr(chat, "title", "Чат"))
        await bot.send_message(ADMIN_ID, f"Удалён чат: {getattr(chat, 'title', 'Чат')} ({chat.id})")

async def start_aiogram():
    await dp.start_polling()

async def main():
    await asyncio.gather(client.start(), start_aiogram())

if __name__ == "__main__":
    asyncio.run(main())
