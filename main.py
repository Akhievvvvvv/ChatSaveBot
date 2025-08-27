import os, json, datetime
from aiogram import Bot, Dispatcher, types, executor
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from config import TOKEN, ADMIN_ID, TARIFFS, BANK_REQUISITES, FREE_DAYS, DATA_PATH, USERS_FILE

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

# Проверка и создание папки и файла для пользователей
os.makedirs(DATA_PATH, exist_ok=True)
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump({}, f)

def load_users():
    with open(USERS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, ensure_ascii=False, indent=2)

def is_active(user_id):
    users = load_users()
    if str(user_id) not in users:
        return False
    start = datetime.datetime.fromisoformat(users[str(user_id)]["free_start"])
    return (datetime.datetime.now() - start).days < FREE_DAYS or users[str(user_id)].get("paid", False)

def activate_free(user_id):
    users = load_users()
    users[str(user_id)] = {"free_start": datetime.datetime.now().isoformat(), "paid": False}
    save_users(users)

def activate_paid(user_id):
    users = load_users()
    users[str(user_id)] = {"free_start": datetime.datetime.now().isoformat(), "paid": True}
    save_users(users)

# Приветствие
@dp.message_handler(commands=["start"])
async def welcome(message: types.Message):
    text = (
        "🌟 Добро пожаловать в ChatSaveBot! 🌟\n\n"
        "Ваши преимущества:\n"
        "✅ Сохраняем удалённые и исчезающие сообщения\n"
        "✅ Поддержка фото, видео, голосовых сообщений\n"
        "✅ Бесплатный пробный период — 7 дней!\n"
        "✅ Красивый и удобный интерфейс\n\n"
        "Нажмите кнопку ниже, чтобы активировать бесплатный период:"
    )
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("🚀 Активировать 7 дней бесплатно", callback_data="activate_free")
    )
    await message.answer(text, reply_markup=kb)

# Активация бесплатного периода
@dp.callback_query_handler(lambda c: c.data == "activate_free")
async def free_period(call: types.CallbackQuery):
    user_id = call.from_user.id
    activate_free(user_id)
    await call.answer("🎉 Бесплатный период активирован!")
    text = (
        "Поздравляем! Ваш бот активирован.\n\n"
        "🔹 Инструкция по подключению:\n"
        "1️⃣ Добавьте бота в Telegram Business.\n"
        "2️⃣ Включите его в нужных чатах через 'Чат-боты'.\n\n"
        "Теперь бот будет сохранять все удалённые и исчезающие сообщения.\n"
        f"💡 После окончания {FREE_DAYS} дней бот остановится и будет требовать оплату."
    )
    await call.message.answer(text)
    await show_tariffs(call.message)

# Меню тарифов
async def show_tariffs(message):
    kb = InlineKeyboardMarkup()
    for key, price in TARIFFS.items():
        if key == "2_weeks": name = "2 недели"
        elif key == "1_month": name = "1 месяц"
        elif key == "2_months": name = "2 месяца"
        kb.add(InlineKeyboardButton(f"{name} — {price}₽", callback_data=f"tariff_{key}"))
    await message.answer("Выберите тариф для оплаты:", reply_markup=kb)

# Выбор тарифа
@dp.callback_query_handler(lambda c: c.data.startswith("tariff_"))
async def select_tariff(call: types.CallbackQuery):
    user_id = call.from_user.id
    tariff_key = call.data.split("_")[1]
    await call.message.answer(
        f"Вы выбрали тариф.\n{BANK_REQUISITES}\n\n"
        "После оплаты администратор подтвердит подписку и бот станет активным."
    )
    # Отправляем уведомление в группу админа
    kb = InlineKeyboardMarkup().add(
        InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"confirm_{user_id}")
    )
    await bot.send_message(ADMIN_ID,
        f"Пользователь {call.from_user.full_name} ({user_id}) выбрал тариф {tariff_key}.",
        reply_markup=kb
    )

# Подтверждение оплаты админом
@dp.callback_query_handler(lambda c: c.data.startswith("confirm_"))
async def confirm_payment(call: types.CallbackQuery):
    user_id = int(call.data.split("_")[1])
    activate_paid(user_id)
    await call.answer("Оплата подтверждена!")
    await bot.send_message(user_id,
        "🎉 Ваша подписка подтверждена!\n\n"
        "Теперь бот снова активен.\n"
        "🔹 Все функции бота доступны."
    )
    await call.message.edit_text("Оплата подтверждена ✅")

# Проверка перед сохранением сообщений (пример)
@dp.message_handler()
async def handle_messages(message: types.Message):
    if not is_active(message.from_user.id):
        return  # бот не работает для этого пользователя
    # Здесь сохраняем сообщения в JSON/БД
    # Пример:
    users = load_users()
    users[str(message.from_user.id)]["last_msg"] = message.text
    save_users(users)
    await message.reply("Сообщение сохранено ✅")

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
