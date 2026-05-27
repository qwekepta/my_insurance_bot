import asyncio
import logging
import os  # <-- добавлен для работы с переменными окружения
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ===== БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ТОКЕНА =====
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения TOKEN не установлена! Добавьте её на Bothost.ru.")

ADMIN_IDS = [1259255945]   # можно оставить так или тоже вынести в окружение

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="📞 Связаться с агентом"),
        types.KeyboardButton(text="❓ Частые вопросы")
    )
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🚗 *Добро пожаловать!*\n\n"
        "Я помогаю связаться с брокером по автострахованию.\n"
        "Нажмите кнопку ниже, чтобы оставить заявку или задать вопрос.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "📞 Связаться с агентом")
async def contact_agent(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Позвонить мне", callback_data="call_me")],
        [InlineKeyboardButton(text="💬 Написать в чат", url="https://t.me/piroghotdog")],
        [InlineKeyboardButton(text="📱 Оставить заявку (ответим в Telegram)", callback_data="leave_request")]
    ])
    await message.answer(
        "Выберите удобный способ связи с нашим агентом:\n\n"
        "✅ *Звонок* — мы перезвоним за 2 минуты.\n"
        "✅ *Чат* — быстрый ответ в Telegram.\n"
        "✅ *Заявка* — заполните форму, и я всё передам.",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.callback_query(F.data == "call_me")
async def call_me(callback: types.CallbackQuery):
    await callback.message.answer(
        "📞 *Отправьте ваш номер телефона* кнопкой ниже, и специалист перезвонит в течение 10 минут.\n\n"
        "Или напишите номер вручную (например, +7 999 123-45-67).",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
            resize_keyboard=True
        )
    )
    await callback.answer()

@dp.callback_query(F.data == "leave_request")
async def leave_request(callback: types.CallbackQuery):
    await callback.message.answer(
        "✍️ *Короткая заявка*:\n\n"
        "Напишите в одном сообщении:\n"
        "• Ваше имя\n"
        "• Марку и год авто\n"
        "• Какую страховку хотите (ОСАГО / КАСКО)\n\n"
        "Пример: *Алексей, Kia Rio 2019, ОСАГО*\n\n"
        "Я передам заявку брокеру — он свяжется с вами в Telegram.",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(F.contact)
async def get_contact(message: types.Message):
    contact = message.contact
    phone = contact.phone_number
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"📞 *НОВАЯ ЗАЯВКА НА ЗВОНОК*\n\nКлиент: {user_name}\nТелефон: {phone}\nUser ID: {user_id}\nСсылка: tg://user?id={user_id}"
        )
    await message.answer(
        "✅ Спасибо! Ваш номер передан агенту. Ожидайте звонка в ближайшее время.\nВернуться в меню: /start"
    )

@dp.message(F.text & ~F.text.in_({"📞 Связаться с агентом", "❓ Частые вопросы", "/start"}))
async def text_request(message: types.Message):
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"✍️ *ТЕКСТОВАЯ ЗАЯВКА*\n\nОт: {message.from_user.full_name} (id: {message.from_user.id})\nТекст: {message.text}"
        )
    await message.answer(
        "✅ Заявка принята! Наш брокер свяжется с вами в Telegram в ближайшее время.\nЕсли хотите позвонить — нажмите «Связаться с агентом» и выберите звонок.",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "❓ Частые вопросы")
async def faq(message: types.Message):
    text = (
        "❓ *Частые вопросы*\n\n"
        "🔹 *Как быстро перезвонят?* — Обычно в течение 10 минут после отправки номера.\n"
        "🔹 *Есть ли скрытые комиссии?* — Нет, брокер называет полную стоимость.\n"
        "🔹 *Что делать, если не дозвонились?* — Напишите в чат по ссылке выше.\n"
        "🔹 *Можно оформить полис онлайн?* — Да, через брокера удалённо."
    )
    await message.answer(text, parse_mode="Markdown")

async def main():
    logging.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())import asyncio
import logging
import os  # <-- добавлен для работы с переменными окружения
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ===== БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ТОКЕНА =====
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения TOKEN не установлена! Добавьте её на Bothost.ru.")

ADMIN_IDS = [1259255945]   # можно оставить так или тоже вынести в окружение

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="📞 Связаться с агентом"),
        types.KeyboardButton(text="❓ Частые вопросы")
    )
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🚗 *Добро пожаловать!*\n\n"
        "Я помогаю связаться с брокером по автострахованию.\n"
        "Нажмите кнопку ниже, чтобы оставить заявку или задать вопрос.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "📞 Связаться с агентом")
async def contact_agent(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Позвонить мне", callback_data="call_me")],
        [InlineKeyboardButton(text="💬 Написать в чат", url="https://t.me/piroghotdog")],
        [InlineKeyboardButton(text="📱 Оставить заявку (ответим в Telegram)", callback_data="leave_request")]
    ])
    await message.answer(
        "Выберите удобный способ связи с нашим агентом:\n\n"
        "✅ *Звонок* — мы перезвоним за 2 минуты.\n"
        "✅ *Чат* — быстрый ответ в Telegram.\n"
        "✅ *Заявка* — заполните форму, и я всё передам.",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.callback_query(F.data == "call_me")
async def call_me(callback: types.CallbackQuery):
    await callback.message.answer(
        "📞 *Отправьте ваш номер телефона* кнопкой ниже, и специалист перезвонит в течение 10 минут.\n\n"
        "Или напишите номер вручную (например, +7 999 123-45-67).",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
            resize_keyboard=True
        )
    )
    await callback.answer()

@dp.callback_query(F.data == "leave_request")
async def leave_request(callback: types.CallbackQuery):
    await callback.message.answer(
        "✍️ *Короткая заявка*:\n\n"
        "Напишите в одном сообщении:\n"
        "• Ваше имя\n"
        "• Марку и год авто\n"
        "• Какую страховку хотите (ОСАГО / КАСКО)\n\n"
        "Пример: *Алексей, Kia Rio 2019, ОСАГО*\n\n"
        "Я передам заявку брокеру — он свяжется с вами в Telegram.",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(F.contact)
async def get_contact(message: types.Message):
    contact = message.contact
    phone = contact.phone_number
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"📞 *НОВАЯ ЗАЯВКА НА ЗВОНОК*\n\nКлиент: {user_name}\nТелефон: {phone}\nUser ID: {user_id}\nСсылка: tg://user?id={user_id}"
        )
    await message.answer(
        "✅ Спасибо! Ваш номер передан агенту. Ожидайте звонка в ближайшее время.\nВернуться в меню: /start"
    )

@dp.message(F.text & ~F.text.in_({"📞 Связаться с агентом", "❓ Частые вопросы", "/start"}))
async def text_request(message: types.Message):
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"✍️ *ТЕКСТОВАЯ ЗАЯВКА*\n\nОт: {message.from_user.full_name} (id: {message.from_user.id})\nТекст: {message.text}"
        )
    await message.answer(
        "✅ Заявка принята! Наш брокер свяжется с вами в Telegram в ближайшее время.\nЕсли хотите позвонить — нажмите «Связаться с агентом» и выберите звонок.",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "❓ Частые вопросы")
async def faq(message: types.Message):
    text = (
        "❓ *Частые вопросы*\n\n"
        "🔹 *Как быстро перезвонят?* — Обычно в течение 10 минут после отправки номера.\n"
        "🔹 *Есть ли скрытые комиссии?* — Нет, брокер называет полную стоимость.\n"
        "🔹 *Что делать, если не дозвонились?* — Напишите в чат по ссылке выше.\n"
        "🔹 *Можно оформить полис онлайн?* — Да, через брокера удалённо."
    )
    await message.answer(text, parse_mode="Markdown")

async def main():
    logging.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())import asyncio
import logging
import os  # <-- добавлен для работы с переменными окружения
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import ReplyKeyboardBuilder

# ===== БЕЗОПАСНОЕ ПОЛУЧЕНИЕ ТОКЕНА =====
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения TOKEN не установлена! Добавьте её на Bothost.ru.")

ADMIN_IDS = [1259255945]   # можно оставить так или тоже вынести в окружение

logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)
dp = Dispatcher()

def main_keyboard():
    builder = ReplyKeyboardBuilder()
    builder.row(
        types.KeyboardButton(text="📞 Связаться с агентом"),
        types.KeyboardButton(text="❓ Частые вопросы")
    )
    return builder.as_markup(resize_keyboard=True)

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer(
        "🚗 *Добро пожаловать!*\n\n"
        "Я помогаю связаться с брокером по автострахованию.\n"
        "Нажмите кнопку ниже, чтобы оставить заявку или задать вопрос.",
        parse_mode="Markdown",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "📞 Связаться с агентом")
async def contact_agent(message: types.Message):
    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📞 Позвонить мне", callback_data="call_me")],
        [InlineKeyboardButton(text="💬 Написать в чат", url="https://t.me/piroghotdog")],
        [InlineKeyboardButton(text="📱 Оставить заявку (ответим в Telegram)", callback_data="leave_request")]
    ])
    await message.answer(
        "Выберите удобный способ связи с нашим агентом:\n\n"
        "✅ *Звонок* — мы перезвоним за 2 минуты.\n"
        "✅ *Чат* — быстрый ответ в Telegram.\n"
        "✅ *Заявка* — заполните форму, и я всё передам.",
        parse_mode="Markdown",
        reply_markup=kb
    )

@dp.callback_query(F.data == "call_me")
async def call_me(callback: types.CallbackQuery):
    await callback.message.answer(
        "📞 *Отправьте ваш номер телефона* кнопкой ниже, и специалист перезвонит в течение 10 минут.\n\n"
        "Или напишите номер вручную (например, +7 999 123-45-67).",
        parse_mode="Markdown",
        reply_markup=ReplyKeyboardMarkup(
            keyboard=[[KeyboardButton(text="📱 Отправить номер", request_contact=True)]],
            resize_keyboard=True
        )
    )
    await callback.answer()

@dp.callback_query(F.data == "leave_request")
async def leave_request(callback: types.CallbackQuery):
    await callback.message.answer(
        "✍️ *Короткая заявка*:\n\n"
        "Напишите в одном сообщении:\n"
        "• Ваше имя\n"
        "• Марку и год авто\n"
        "• Какую страховку хотите (ОСАГО / КАСКО)\n\n"
        "Пример: *Алексей, Kia Rio 2019, ОСАГО*\n\n"
        "Я передам заявку брокеру — он свяжется с вами в Telegram.",
        parse_mode="Markdown"
    )
    await callback.answer()

@dp.message(F.contact)
async def get_contact(message: types.Message):
    contact = message.contact
    phone = contact.phone_number
    user_name = message.from_user.full_name
    user_id = message.from_user.id
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"📞 *НОВАЯ ЗАЯВКА НА ЗВОНОК*\n\nКлиент: {user_name}\nТелефон: {phone}\nUser ID: {user_id}\nСсылка: tg://user?id={user_id}"
        )
    await message.answer(
        "✅ Спасибо! Ваш номер передан агенту. Ожидайте звонка в ближайшее время.\nВернуться в меню: /start"
    )

@dp.message(F.text & ~F.text.in_({"📞 Связаться с агентом", "❓ Частые вопросы", "/start"}))
async def text_request(message: types.Message):
    for admin_id in ADMIN_IDS:
        await bot.send_message(
            admin_id,
            f"✍️ *ТЕКСТОВАЯ ЗАЯВКА*\n\nОт: {message.from_user.full_name} (id: {message.from_user.id})\nТекст: {message.text}"
        )
    await message.answer(
        "✅ Заявка принята! Наш брокер свяжется с вами в Telegram в ближайшее время.\nЕсли хотите позвонить — нажмите «Связаться с агентом» и выберите звонок.",
        reply_markup=main_keyboard()
    )

@dp.message(F.text == "❓ Частые вопросы")
async def faq(message: types.Message):
    text = (
        "❓ *Частые вопросы*\n\n"
        "🔹 *Как быстро перезвонят?* — Обычно в течение 10 минут после отправки номера.\n"
        "🔹 *Есть ли скрытые комиссии?* — Нет, брокер называет полную стоимость.\n"
        "🔹 *Что делать, если не дозвонились?* — Напишите в чат по ссылке выше.\n"
        "🔹 *Можно оформить полис онлайн?* — Да, через брокера удалённо."
    )
    await message.answer(text, parse_mode="Markdown")

async def main():
    logging.info("Бот запущен")
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())