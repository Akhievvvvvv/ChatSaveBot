import asyncio
from aiogram import Bot, Dispatcher, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from datetime import datetime, timedelta
import json, os

from config import TOKEN, ADMIN_ID, TARIFFS, BANK_REQUISITES, FREE_DAYS
from utils import load_users, save_users, add_message

bot = Bot(token=TOKEN)
dp = Dispatcher(bot)

users = load_users()

# ====== Helpers ======
def get_user_data(user_id):
    return users.get(str(user_id), {"sub_end": None, "referrals": [], "bonus_active": False})

def save_user_data(user_id, data):
    users[str(user_id)] = data
    save_users(users)

# ====== Inline menus ======
def menu_main():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(
        InlineKeyboardButton("📜 Посмотреть тарифы", callback_data="tariffs"),
        InlineKeyboardButton("👥 Моя реферальная ссылка", callback_data="referral")
    )
    return kb

def menu_tariffs():
    kb = InlineKeyboardMarkup(row_width=1)
    russian_names = {
        "2_weeks": "2 недели",
        "1_month": "1 месяц",
        "2_months": "2 месяца"
    }
    for name, price in TARIFFS.items():
        kb.add(InlineKeyboardButton(f"{russian_names.get(name, name)} — {price}₽", callback_data=f"buy_{name}"))
    return kb

def menu_paid():
    kb = InlineKeyboardMarkup(row_width=1)
    kb.add(InlineKeyboardButton("✅ Оплатил(а)", callback_data="paid"))
    return kb

# ====== Handlers ======
@dp.message_handler(commands=["start"])
async def start(message: types.Message):
    user_id = message.from_user.id
    data = get_user_data(user_id)
    # если первый раз — даём бонус
    if data["sub_end"] is None:
        data["sub_end"] = (datetime.now() + timedelta(days=FREE_DAYS)).timestamp()
        save_user_data(user_id, data)
    text = (
        f"🌟 Привет, {message.from_user.full_name}! 👋\n\n"
        "Я — ваш личный помощник для сохранения сообщений в Telegram Business.\n\n"
        "✨ Что я умею:\n"
        "• Сохраняю удалённые сообщения\n"
        "• Сохраняю исчезающие сообщения (фото, видео, гс)\n"
        "• Подписка с бонусными днями и рефералами\n\n"
        "Для начала выберите опцию в меню ниже ⬇️"
    )
    await message.answer(text, reply_markup=menu_main())

@dp.callback_query_handler(lambda c: c.data)
async def callbacks(call: types.CallbackQuery):
    user_id = call.from_user.id
    data = get_user_data(user_id)

    if call.data == "tariffs":
        await call.message.edit_text("💰 Выберите тариф:", reply_markup=menu_tariffs())
    elif call.data.startswith("buy_"):
        tariff = call.data[4:]
        price = TARIFFS.get(tariff)
        # Красочный текст реквизитов
        text = (
            f"💳 Вы выбрали тариф: **{tariff.replace('_', ' ')}**\n\n"
            f"💰 Сумма к оплате: **{price}₽**\n"
            f"🏦 Реквизиты для оплаты:\n"
            f"🔹 Номер карты: **89322229930**\n"
            f"🔹 Банк: **Ozon Bank**\n\n"
            "После оплаты нажмите кнопку ниже, чтобы подтвердить оплату."
        )
        await call.message.edit_text(text, reply_markup=menu_paid())
    elif call.data == "paid":
        # уведомляем админа
        await bot.send_message(ADMIN_ID, f"Пользователь {call.from_user.full_name} ({user_id}) оплатил подписку.")
        await call.message.answer("✅ Спасибо! После проверки подписка активирована.")
    elif call.data == "referral":
        ref_link = f"https://t.me/Chat_ls_save_bot?start={user_id}"
        await call.message.answer(f"👥 Ваша реферальная ссылка:\n{ref_link}\nБонус +7 дней после активации новым пользователем.")

# ====== Business messages ======
@dp.message_handler(content_types=types.ContentTypes.ANY)
async def handle_business(message: types.Message):
    # сохраняем все сообщения
    user_id = message.from_user.id
    chat_id = message.chat.id
    msg_data = {
        "message_id": message.message_id,
        "date": str(message.date),
        "type": message.content_type,
        "text": getattr(message, "text", None)
    }
    add_message(user_id, chat_id, msg_data)

if __name__ == "__main__":
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
