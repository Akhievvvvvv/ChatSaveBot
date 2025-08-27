import json
import os
import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

from config import TOKEN, ADMIN_ID, TARIFFS, BANK_REQUISITES, FREE_DAYS, DATA_PATH

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Папка для хранения сообщений
if not os.path.exists(DATA_PATH):
    os.makedirs(DATA_PATH)

MESSAGES_FILE = os.path.join(DATA_PATH, "messages.json")
USERS_FILE = os.path.join(DATA_PATH, "users.json")

# Загрузка данных
def load_json(path):
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}

messages_data = load_json(MESSAGES_FILE)
users_data = load_json(USERS_FILE)

# Сохранение данных
def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# Главное меню
def main_menu():
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("⚡ Активировать 7 дней бесплатно", callback_data="free_7days"))
    kb.add(InlineKeyboardButton("👥 Рефералы", callback_data="referrals"))
    kb.add(InlineKeyboardButton("💳 Тарифы", callback_data="tariffs"))
    return kb

# Подменю тарифов
def tariffs_menu():
    kb = InlineKeyboardMarkup()
    for name, price in TARIFFS.items():
        kb.add(InlineKeyboardButton(f"{name} — {price}₽", callback_data=f"buy_{name}"))
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return kb

# Подменю рефералов
def referrals_menu(user_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("🔙 Назад", callback_data="back_main"))
    return kb

# Приветственное сообщение
WELCOME_TEXT = (
    "✨ Привет! Я бот ChatSaver 🤖\n\n"
    "Я умею сохранять удалённые и одноразовые сообщения!\n\n"
    f"💎 Бесплатный период: {FREE_DAYS} дней\n"
    "📌 После окончания бесплатного периода бот будет работать только после оплаты.\n\n"
    "Нажмите кнопку ниже, чтобы активировать бесплатный период!"
)

# Инструкция после активации
INSTRUCTION_TEXT = (
    "🎉 Поздравляем! Бот активирован на 7 дней бесплатно.\n\n"
    "📌 Инструкция по подключению:\n"
    "1️⃣ Перейдите в 'Настройки'\n"
    "2️⃣ Откройте 'Telegram для бизнеса'\n"
    "3️⃣ Нажмите 'Чат-боты'\n"
    "4️⃣ Добавьте бота @Chat_ls_save_bot\n\n"
    "Бот теперь будет сохранять удалённые сообщения в ваших чатах."
)

# Проверка оплаты
def is_paid(user_id):
    user = users_data.get(str(user_id), {})
    return user.get("paid", False)

# Событие нажатия кнопок
@dp.callback_query_handler(lambda c: True)
async def callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id

    if call.data == "free_7days":
        users_data[str(user_id)] = {"paid": True, "free": True, "days_left": FREE_DAYS}
        save_json(USERS_FILE, users_data)
        await bot.send_message(user_id, INSTRUCTION_TEXT)
        await call.answer()

    elif call.data == "tariffs":
        await bot.send_message(user_id, "Выберите тариф:", reply_markup=tariffs_menu())
        await call.answer()

    elif call.data.startswith("buy_"):
        name = call.data.split("_")[1]
        price = TARIFFS.get(name, 0)
        text = f"💳 Вы выбрали тариф {name} — {price}₽\nРеквизиты для оплаты: {BANK_REQUISITES}\n\nПосле оплаты нажмите 'Оплатил(а)' в боте."
        await bot.send_message(user_id, text)
        await call.answer()

    elif call.data == "referrals":
        await bot.send_message(user_id, f"Ваша реферальная ссылка: https://t.me/Chat_ls_save_bot?start={user_id}")
        await call.answer()

    elif call.data == "back_main":
        await bot.send_message(user_id, WELCOME_TEXT, reply_markup=main_menu())
        await call.answer()

# Сохранение сообщений
@dp.message_handler(content_types=types.ContentTypes.ANY)
async def handle_messages(message: types.Message):
    user_id = message.from_user.id
    if not is_paid(user_id):
        return
    msg_id = str(message.message_id)
    messages_data[msg_id] = {
        "user": user_id,
        "chat": message.chat.id,
        "text": message.text,
        "type": message.content_type
    }
    save_json(MESSAGES_FILE, messages_data)

# Запуск бота
async def main():
    for user_id, data in users_data.items():
        if data.get("free", False):
            # Можно уменьшать days_left каждый день через scheduler
            pass
    await bot.send_message(ADMIN_ID, "Бот запущен!")
    await dp.start_polling()

if __name__ == "__main__":
    asyncio.run(main())
