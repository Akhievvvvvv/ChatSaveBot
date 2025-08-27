import json, os, asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from config import TOKEN, ADMIN_ID, TARIFFS, BANK_REQUISITES, FREE_DAYS

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

DATA_PATH = "data"
USERS_FILE = os.path.join(DATA_PATH, "users.json")
MESSAGES_FILE = os.path.join(DATA_PATH, "messages.json")
REFERRALS_FILE = os.path.join(DATA_PATH, "referrals.json")

# ============ UTILS ============
def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r", encoding="utf-8") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def save_message(user_id, message):
    data = load_json(MESSAGES_FILE)
    if str(user_id) not in data:
        data[str(user_id)] = []
    data[str(user_id)].append({
        "text": message.text,
        "from": message.from_user.full_name,
        "date": str(message.date)
    })
    save_json(MESSAGES_FILE, data)

def activate_free_period(user_id):
    users = load_json(USERS_FILE)
    users[str(user_id)] = {
        "free_until": str(datetime.now() + timedelta(days=FREE_DAYS)),
        "paid": False
    }
    save_json(USERS_FILE, users)

def check_access(user_id):
    users = load_json(USERS_FILE)
    u = users.get(str(user_id))
    if not u:
        return False
    if u.get("paid"):
        return True
    free_until = datetime.fromisoformat(u.get("free_until"))
    return datetime.now() <= free_until

# ============ KEYBOARDS ============
def main_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("🚀 Активировать 7 дней бесплатно", callback_data="free_week"),
        types.InlineKeyboardButton("💰 Тарифы", callback_data="tariffs"),
        types.InlineKeyboardButton("🎁 Рефералы", callback_data="referrals")
    )
    return kb

def tariffs_menu():
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("2 недели — 49₽", callback_data="tariff_2weeks"),
        types.InlineKeyboardButton("1 месяц — 89₽", callback_data="tariff_1month"),
        types.InlineKeyboardButton("2 месяца — 149₽", callback_data="tariff_2months"),
        types.InlineKeyboardButton("⬅ Назад", callback_data="back_main")
    )
    return kb

def referrals_menu(user_id):
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton("⬅ Назад", callback_data="back_main")
    )
    return kb

WELCOME_TEXT = (
    "🌟 Добро пожаловать в ChatSaveBot!\n\n"
    "С этим ботом вы сможете:\n"
    "✅ Сохранять удалённые сообщения\n"
    "✅ Сохранять одноразовые сообщения\n"
    "✅ Получать уведомления о новых сообщениях\n\n"
    "Начните с бесплатного пробного периода — 7 дней полностью бесплатно!"
)

FREE_TEXT = (
    "🎉 Ваш бесплатный период активирован!\n\n"
    "Вот как подключить бота к Telegram Business и начать сохранять сообщения:\n"
    "1️⃣ Перейдите в 'Настройки' → 'Telegram для бизнеса'\n"
    "2️⃣ Нажмите 'Чат-боты' и добавьте ChatSaveBot\n"
    "3️⃣ Всё готово, бот теперь сохраняет ваши сообщения!"
)

# ============ HANDLERS ============
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    await message.answer(WELCOME_TEXT, reply_markup=main_menu())

@dp.callback_query_handler(lambda c: True)
async def callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id
    if call.data == "free_week":
        activate_free_period(user_id)
        await bot.send_message(user_id, FREE_TEXT)
        await call.answer()
    elif call.data == "tariffs":
        await bot.send_message(user_id, "Выберите тариф:", reply_markup=tariffs_menu())
        await call.answer()
    elif call.data == "referrals":
        await bot.send_message(user_id, "Ваша реферальная ссылка:\n"
                                         f"https://t.me/Chat_ls_save_bot?start={user_id}",
                               reply_markup=referrals_menu(user_id))
        await call.answer()
    elif call.data == "back_main":
        await bot.send_message(user_id, WELCOME_TEXT, reply_markup=main_menu())
        await call.answer()

# ============ BUSINESS MESSAGE HANDLER ============
@dp.message_handler(content_types=types.ContentTypes.ANY)
async def save_all_messages(message: types.Message):
    if check_access(message.from_user.id):
        save_message(message.from_user.id, message)
    else:
        await message.answer("⚠ Ваш пробный период закончился. Пожалуйста, выберите тариф для продолжения.")

# ============ START BOT ============
if __name__ == "__main__":
    if not os.path.exists(DATA_PATH):
        os.makedirs(DATA_PATH)
    executor.start_polling(dp, skip_updates=True)
