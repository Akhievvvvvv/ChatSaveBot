import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils import executor
import json
import os
from config import TOKEN, ADMIN_ID, TARIFFS, BANK_REQUISITES, FREE_DAYS, DATA_PATH

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Проверка и создание папки для данных
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

# Загружаем или создаём файл с пользователями
users_file = os.path.join(DATA_PATH, "users.json")
if os.path.exists(users_file):
    with open(users_file, "r") as f:
        users = json.load(f)
else:
    users = {}

# --- Кнопки ---
def main_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("🎁 7 дней бесплатно", callback_data="free_week"),
        InlineKeyboardButton("💰 Тарифы", callback_data="tariffs"),
        InlineKeyboardButton("🤝 Рефералы", callback_data="referrals")
    )
    return kb

def back_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    return kb

def tariffs_menu():
    kb = InlineKeyboardMarkup(row_width=1)
    for name, price in TARIFFS.items():
        # Название тарифов на русском
        if name == "2_weeks":
            title = "2 недели"
        elif name == "1_month":
            title = "1 месяц"
        elif name == "2_months":
            title = "2 месяца"
        else:
            title = name
        kb.add(InlineKeyboardButton(f"{title} — {price}₽", callback_data=f"tariff_{name}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back"))
    return kb

# --- Старт ---
@dp.message_handler(commands=["start"])
async def start_command(message: types.Message):
    user_id = str(message.from_user.id)
    # Добавляем пользователя если новый
    if user_id not in users:
        users[user_id] = {"active": False, "paid": False, "referrals": []}
        with open(users_file, "w") as f:
            json.dump(users, f, indent=4)

    text = (
        f"✨ Привет, {message.from_user.full_name}!\n\n"
        "Я бот ChatSaver 🤖 — сохраняю удалённые и одноразовые сообщения.\n\n"
        f"💎 Бесплатный период: {FREE_DAYS} дней\n"
        "📌 После окончания бесплатного периода бот будет работать только после оплаты.\n\n"
        "Выберите действие ниже:"
    )
    await message.answer(text, reply_markup=main_menu())

# --- Callback ---
@dp.callback_query_handler(lambda c: True)
async def callbacks(call: types.CallbackQuery):
    user_id = str(call.from_user.id)
    data = call.data

    if data == "back":
        await call.message.edit_text(
            f"✨ Главное меню, {call.from_user.full_name}:", reply_markup=main_menu()
        )
        return

    if data == "free_week":
        users[user_id]["active"] = True
        users[user_id]["free"] = True
        with open(users_file, "w") as f:
            json.dump(users, f, indent=4)

        await call.message.edit_text(
            "🎉 Бесплатный период активирован!\n\n"
            "📌 Инструкция по подключению бота:\n"
            "1. Добавьте меня в Telegram Business\n"
            "2. Разрешите доступ к вашим чатам\n"
            "3. Все удалённые сообщения теперь будут сохраняться!\n\n"
            "📝 Используйте главное меню для управления ботом.",
            reply_markup=back_menu()
        )
        return

    if data.startswith("tariff_"):
        name = data.split("_")[1]
        price = TARIFFS[name]
        await call.message.edit_text(
            f"💳 Тариф: {name.replace('_', ' ')}\n"
            f"Стоимость: {price}₽\n"
            f"Реквизиты для оплаты: {BANK_REQUISITES}\n\n"
            "После оплаты сообщите в группу для подтверждения.",
            reply_markup=back_menu()
        )
        return

    if data == "tariffs":
        await call.message.edit_text(
            "Выберите тариф:", reply_markup=tariffs_menu()
        )
        return

    if data == "referrals":
        ref_link = f"https://t.me/Chat_ls_save_bot?start={user_id}"
        count = len(users[user_id].get("referrals", []))
        await call.message.edit_text(
            f"🤝 Ваша реферальная ссылка:\n{ref_link}\n"
            f"Количество рефералов: {count}\n"
            "Бонусы начисляются после оплаты рефералов.",
            reply_markup=back_menu()
        )
        return

# --- Запуск ---
if __name__ == "__main__":
    print("Бот запущен...")
    executor.start_polling(dp, skip_updates=True)
