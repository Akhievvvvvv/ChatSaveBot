import asyncio, json, random
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from config import TOKEN, ADMIN_ID, TARIFFS, BANK_REQUISITES
from utils import load_users, save_users, save_message

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

users = load_users()

# -------------------- Вспомогательные функции --------------------

def get_referral_link(user_id):
    return f"https://t.me/Chat_ls_save_bot?start=ref{user_id}"

def user_active(user_id):
    return users.get(str(user_id), {}).get("active", False)

def add_referral(user_id, ref_id):
    user_data = users.get(str(user_id), {})
    if "referrals" not in user_data:
        user_data["referrals"] = []
    if ref_id not in user_data["referrals"]:
        user_data["referrals"].append(ref_id)
    users[str(user_id)] = user_data
    save_users(users)

# -------------------- Хэндлеры --------------------

@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    users.setdefault(str(user_id), {"active": False, "referrals": []})
    
    # Проверка на рефералку
    if message.get_args().startswith("ref"):
        ref_id = message.get_args()[3:]
        if ref_id != str(user_id):
            add_referral(ref_id, user_id)
    
    if not user_active(user_id):
        kb = InlineKeyboardMarkup().add(InlineKeyboardButton("Выбрать тариф 💳", callback_data="tariffs"))
        await message.answer(
            "Привет! 👋\n\n"
            "Бот ChatSave — сохраняет удалённые и исчезающие сообщения, 🔒 защищает вашу переписку.\n\n"
            "Чтобы активировать бота, выберите тариф ниже:",
            reply_markup=kb
        )
    else:
        await send_welcome(user_id)

async def send_welcome(user_id):
    kb = InlineKeyboardMarkup()
    kb.add(InlineKeyboardButton("Моя реферальная ссылка 🔗", callback_data="myref"))
    kb.add(InlineKeyboardButton("Мои сообщения 💾", callback_data="mymessages"))
    await bot.send_message(user_id,
        "🎉 Поздравляем! Ваша подписка активирована.\n\n"
        "Что умеет бот:\n"
        "• Сохраняет удалённые сообщения\n"
        "• Сохраняет исчезающие фото, видео и голосовые\n"
        "• Показывает историю переписки в удобном формате\n\n"
        "Используйте кнопки ниже для управления:", reply_markup=kb)

# -------------------- Callback Query --------------------

@dp.callback_query_handler(lambda c: True)
async def callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id
    data = call.data

    if data == "tariffs":
        kb = InlineKeyboardMarkup()
        for name, price in TARIFFS.items():
            kb.add(InlineKeyboardButton(f"{name} — {price}₽", callback_data=f"pay_{name}"))
        await call.message.edit_text("Выберите тариф для оплаты:", reply_markup=kb)

    elif data.startswith("pay_"):
        plan = data[4:]
        await bot.send_message(ADMIN_ID,
            f"Пользователь {call.from_user.full_name} ({user_id}) хочет оплатить тариф {plan}.\n"
            f"Реквизиты для оплаты: {REKVIZITY}",
            reply_markup=InlineKeyboardMarkup().add(
                InlineKeyboardButton("✅ Подтвердить оплату", callback_data=f"confirm_{user_id}")
            )
        )
        await call.message.answer("Запрос на оплату отправлен админу. Ожидайте подтверждения ✅")

    elif data.startswith("confirm_") and user_id == ADMIN_ID:
        uid = int(data.split("_")[1])
        users.setdefault(str(uid), {})["active"] = True
        save_users(users)
        await bot.send_message(uid, "Оплата подтверждена! 🎉")
        await send_welcome(uid)
        await call.answer("Подписка подтверждена ✅")

    elif data == "myref":
        user_data = users.get(str(user_id), {})
        referrals = user_data.get("referrals", [])
        text = f"Ваша реферальная ссылка: {get_referral_link(user_id)}\n\n"
        text += f"Всего перешло по ссылке: {len(referrals)}\n"
        text += "Активировавшие подписку:\n"
        active_refs = [r for r in referrals if users.get(str(r), {}).get("active")]
        for r in active_refs:
            text += f"• {r}\n"
        await call.message.answer(text)

    elif data == "mymessages":
        path = f"data/{user_id}_messages.json"
        if not os.path.exists(path):
            await call.message.answer("У вас пока нет сохранённых сообщений.")
            return
        with open(path, "r", encoding="utf-8") as f:
            msgs = json.load(f)
        for m in msgs[-10:]:
            await call.message.answer(str(m))  # Показываем последние 10 сообщений

# -------------------- Сохраняем сообщения --------------------

@dp.message_handler(content_types=types.ContentType.ANY)
async def save_all(message: types.Message):
    user_id = message.from_user.id
    if user_active(user_id):
        msg = {
            "type": message.content_type,
            "text": message.text or "",
            "date": str(message.date)
        }
        save_message(user_id, msg)

# -------------------- Запуск бота --------------------

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
