import asyncio
from aiogram import Bot, Dispatcher, F, types
from aiogram.filters import CommandStart
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove

TOKEN = "8268270956:AAGOewY2bnx8u8llRYJDJ3L9uF5zeeK5ZNA"
ADMIN_ID = 76351075

bot = Bot(TOKEN)
dp = Dispatcher()

PRIZE_TEXT = "🎁 Сертификат на 300 ₽ на мои услуги"
LINK = "https://dikidi.net/263095"

already_played = set()
waiting_phone = set()
user_choice = {}  # user_id -> option_number

OPTIONS = {
    1: "Оформление бровей (Коррекция+окрашивание) 1300 вместо 1600",
    2: "Долговременная укладка бровей (ламинирование+окрашивание+уход) 1500 вместо 1800",
    3: "Ламинирование верхних ресниц (ламинирование+окрашивание+уход) 1700 вместо 2000",
    4: "Ламинирование верхних нижних ресниц (ламинирование+окрашивание+уход) 2700 вместо 3000",
}

def kb_roll_inline():
    kb = InlineKeyboardBuilder()
    kb.button(text="🎲 Бросить кубик", callback_data="roll")
    kb.adjust(1)
    return kb.as_markup()

def kb_options_inline():
    kb = InlineKeyboardBuilder()
    kb.button(text="1", callback_data="opt:1")
    kb.button(text="2", callback_data="opt:2")
    kb.button(text="3", callback_data="opt:3")
    kb.button(text="4", callback_data="opt:4")
    kb.adjust(4)
    return kb.as_markup()

def kb_share_phone():
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="📱 Отправить телефон", request_contact=True)]],
        resize_keyboard=True,
        one_time_keyboard=True
    )

def options_text():
    return (
        "Вот варианты, как его потратить:\n\n"
        f"1) {OPTIONS[1]}\n"
        f"2) {OPTIONS[2]}\n"
        f"3) {OPTIONS[3]}\n"
        f"4) {OPTIONS[4]}"
    )

@dp.message(CommandStart())
async def start(message: types.Message):
    await message.answer(
        "Привет! 🎉\n"
        "Нажми кнопку ниже — я брошу кубик и покажу твой выигрыш 👇",
        reply_markup=kb_roll_inline()
    )

@dp.callback_query(F.data == "roll")
async def roll(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    if user_id in already_played:
        await callback.answer("Ты уже бросал(а) кубик 🙂", show_alert=True)
        return

    already_played.add(user_id)
    await callback.answer()

    await bot.send_dice(chat_id=callback.message.chat.id, emoji="🎲")

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            "✅ Готово!\n\n"
            f"Твой приз: {PRIZE_TEXT}\n\n"
            f"{options_text()}\n\n"
            "Выбери вариант (1–4) кнопкой ниже 👇"
        ),
        reply_markup=kb_options_inline()
    )

@dp.callback_query(F.data.startswith("opt:"))
async def option_chosen(callback: types.CallbackQuery):
    user_id = callback.from_user.id

    try:
        opt = int(callback.data.split(":", 1)[1])
    except Exception:
        await callback.answer("Не получилось распознать выбор. Попробуй ещё раз.", show_alert=True)
        return

    if opt not in OPTIONS:
        await callback.answer("Выбери вариант 1–4 🙂", show_alert=True)
        return

    user_choice[user_id] = opt
    waiting_phone.add(user_id)

    await callback.answer("Отлично! Теперь отправь номер телефона 🙂")

    await bot.send_message(
        chat_id=callback.message.chat.id,
        text=(
            "✅ Выбор принят!\n\n"
            f"Ты выбрала: {OPTIONS[opt]}\n\n"
            "Чтобы зафиксировать приз за тобой — нажми кнопку и отправь номер телефона 👇"
        ),
        parse_mode="Markdown",
        reply_markup=kb_share_phone()
    )

@dp.message(F.contact)
async def got_contact(message: types.Message):
    user_id = message.from_user.id

    if user_id not in waiting_phone:
        await message.answer("Спасибо! Если хочешь участвовать — нажми /start 🙂")
        return

    waiting_phone.discard(user_id)

    phone = message.contact.phone_number
    opt = user_choice.get(user_id, None)
    opt_text = OPTIONS.get(opt, "Не выбран")

# --- УВЕДОМЛЕНИЕ ТЕБЕ ---
    username = f"@{message.from_user.username}" if message.from_user.username else "(нет username)"
    full_name = (message.from_user.full_name or "").strip()

    await bot.send_message(
        chat_id=ADMIN_ID,
        text=(
            "📩 Новый участник (листовка)\n\n"
            f"👤 {full_name} {username}\n"
            f"🆔 user_id: {user_id}\n"
            f"📱 телефон: {phone}\n"
            f"✅ выбрал вариант: {opt} — {opt_text}\n"
            f"🎁 приз: {PRIZE_TEXT}"
        )
    )

    # --- ФИНАЛ ДЛЯ КЛИЕНТА ---
    await message.answer(
        text=(
            "✅ Готово! Данные сохранены.\n\n"
            f"Твой выбор: {opt_text}\n"
            f"Твой приз: {PRIZE_TEXT}\n\n"
            "Я работаю каждый день, с 9.00 до 22.00.\n"
            "Сегодня я свяжусь с тобой и мы подберем удобное время.\n\n"
            "Или можно не ждать, а записаться самостоятельно:\n"
            f"{LINK}"
        ),
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardRemove()
    )

@dp.message()
async def fallback(message: types.Message):
    user_id = message.from_user.id
    if user_id in waiting_phone:
        await message.answer(
            "Нажми кнопку 📱 Отправить телефон, чтобы я зафиксировал(а) приз 👇",
            parse_mode="Markdown",
            reply_markup=kb_share_phone()
        )
    else:
        await message.answer("Нажми /start, чтобы начать 🙂")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())