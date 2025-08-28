# main.py
import os
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
from config import API_ID, API_HASH, ADMIN_ID, DATA_PATH, FREE_DAYS, TARIFFS, BANK_REQUISITES
from telethon import TelegramClient, events

# TelegramClient для личных чатов
client = TelegramClient("session", API_ID, API_HASH)

# aiogram Bot для сообщений и inline клавиатур
bot = Bot(token="8253356529:AAG5sClokG30SlhqpP3TNMdl6TajExIE7YU")
dp = Dispatcher(bot)

# Создаём папку для хранения данных, если нет
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

# Тарифы
def tariffs_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    for name, price in TARIFFS.items():
        kb.add(InlineKeyboardButton(f"{name} - {price}₽", callback_data=f"tariff_{name}"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="back_main"))
    return kb

# Рефералы
def referrals_menu(user_id):
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton(f"Ваша ссылка: https://t.me/Chat_ls_save_bot?start={user_id}", callback_data="ignore"))
    kb.add(InlineKeyboardButton("◀️ Назад", callback_data="back_main"))
    return kb

# Приветствие
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    kb = main_menu()
    text = (
        "✨ Добро пожаловать в ChatSaveBot!\n\n"
        "Этот бот сохраняет:\n"
        "• Удалённые сообщения\n"
        "• Однократные фото/видео/голосовые\n"
        "• Удалённые чаты\n\n"
        f"🎁 Бесплатный период: {FREE_DAYS} дней\n\n"
        "Выберите действие ниже:"
    )
    await message.answer(text, reply_markup=kb)

# Обработка нажатий кнопок
@dp.callback_query_handler(lambda c: True)
async def callbacks(call: types.CallbackQuery):
    data = call.data

    if data == "activate_free":
        # Включаем бесплатный период
        await call.message.answer("✅ Ваш бесплатный период активирован!\n\n"
                                  "Подробная инструкция по подключению бота:\n"
                                  "1. Включите бизнес-режим\n"
                                  "2. Добавьте бота в 'Чат-боты' в Telegram Business\n"
                                  "3. Бот начнёт сохранять все удалённые сообщения")
        return

    elif data == "tariffs":
        await call.message.answer("Выберите тариф:", reply_markup=tariffs_menu())

    elif data.startswith("tariff_"):
        tariff_name = data.replace("tariff_", "")
        price = TARIFFS[tariff_name]
        text = f"Вы выбрали тариф {tariff_name} за {price}₽\n\nРеквизиты для оплаты:\n{BANK_REQUISITES}\n\nПосле оплаты нажмите кнопку 'Оплатил(а)'"
        kb = InlineKeyboardMarkup()
        kb.add(InlineKeyboardButton("Оплатил(а)", callback_data=f"paid_{tariff_name}"))
        kb.add(InlineKeyboardButton("◀️ Назад", callback_data="tariffs"))
        await call.message.answer(text, reply_markup=kb)

    elif data.startswith("paid_"):
        tariff_name = data.replace("paid_", "")
        user = call.from_user
        await bot.send_message(ADMIN_ID,
                               f"Пользователь {user.full_name} ({user.id}) выбрал тариф {tariff_name}\n"
                               "Нажмите ✅ Подтвердить оплату",
                               reply_markup=InlineKeyboardMarkup().add(
                                   InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"confirm_{user.id}_{tariff_name}")
                               ))
        await call.message.answer("Ваша заявка отправлена на подтверждение администратору.")

    elif data.startswith("confirm_"):
        parts = data.split("_")
        user_id = int(parts[1])
        tariff_name = parts[2]
        await bot.send_message(user_id, f"🎉 Оплата подтверждена!\n\nВы подключили тариф: {tariff_name}\n\n"
                                        "Подробная инструкция по подключению бота:\n"
                                        "1. Включите бизнес-режим\n"
                                        "2. Добавьте бота в 'Чат-боты'\n"
                                        "3. Бот начнёт сохранять все удалённые сообщения\n"
                                        "4. Пользуйтесь всеми преимуществами!")
        await call.message.answer(f"Оплата пользователя {user_id} подтверждена ✅")

    elif data == "referrals":
        await call.message.answer("Ваша реферальная ссылка и статистика:", reply_markup=referrals_menu(call.from_user.id))

    elif data == "back_main":
        await call.message.answer("Главное меню:", reply_markup=main_menu())

    await call.answer()

# Запуск aiogram
async def start_aiogram():
    await dp.start_polling()

# Запуск Telethon для отслеживания удалений
@client.on(events.MessageDeleted())
async def handler(event):
    chat = await event.get_chat()
    for msg in event.deleted:
        sender = await msg.get_sender()
        text = msg.message or "<медиа/голосовое>"
        save_deleted_message(chat.id, sender.id, sender.first_name, text)
        await bot.send_message(ADMIN_ID, f"Удалено сообщение в {chat.title}:\n{text}")

@client.on(events.MessageDeletedEvent())  # Для удалённых чатов
async def deleted_chat(event):
    chat = await event.get_chat()
    save_deleted_chat(chat.id, getattr(chat, "title", "Чат"))
    await bot.send_message(ADMIN_ID, f"Удалён чат: {getattr(chat, 'title', 'Чат')} ({chat.id})")

async def main():
    await asyncio.gather(client.start(), start_aiogram())

if __name__ == "__main__":
    asyncio.run(main())
