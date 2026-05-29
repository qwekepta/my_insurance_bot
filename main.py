```python
import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

# --- НАСТРОЙКИ ---
TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения TOKEN не установлена!")

# ID администратора, кому будут приходить заявки.
# Узнать свой ID: напишите боту @userinfobot
ADMIN_IDS = [1259255945]  # ЗАМЕНИТЕ НА СВОЙ TELEGRAM ID

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=TOKEN)
dp = Dispatcher(storage=storage)

# --- КНОПКИ ---
main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="🆕 Новая заявка")],
        [KeyboardButton(text="❓ Частые вопросы")]
    ],
    resize_keyboard=True
)

client_type_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="🧑‍💼 Физическое лицо", callback_data="client_individual")],
    [InlineKeyboardButton(text="🏢 Юридическое лицо", callback_data="client_legal")]
])

# --- СОСТОЯНИЯ ДЛЯ ФИЗ. ЛИЦ ---
class IndividualForm(StatesGroup):
    waiting_for_old_policy = State()
    waiting_for_sts = State()
    waiting_for_driver_license = State()
    waiting_for_passport_data = State()

# --- СОСТОЯНИЯ ДЛЯ ЮР. ЛИЦ ---
class LegalForm(StatesGroup):
    waiting_for_company_file = State()

# --- КОМАНДА START ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Добро пожаловать! Я — бот страхового брокера «БЛГС».\n"
        "Я помогу быстро отправить заявку на оформление ОСАГО или КАСКО.\n\n"
        "Просто нажмите на кнопку «🆕 Новая заявка», чтобы начать.",
        reply_markup=main_kb
    )

# --- НОВАЯ ЗАЯВКА ---
@dp.message(F.text == "🆕 Новая заявка")
async def new_order(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите тип клиента:", reply_markup=client_type_kb)

# --- ВЫБОР ТИПА КЛИЕНТА ---
@dp.callback_query(F.data == "client_individual")
async def process_individual(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отлично! Начинаем оформление для физического лица.\n\n"
                                     "1️⃣ **Шаг 1 из 4: Старый полис ОСАГО**\n"
                                     "Пожалуйста, отправьте фото старого полиса ОСАГО.")
    await state.set_state(IndividualForm.waiting_for_old_policy)
    await callback.answer()

@dp.callback_query(F.data == "client_legal")
async def process_legal(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Хорошо. Отправьте, пожалуйста, файл с данными для юридического лица.\n\n"
                                     "📎 **Ожидание файла...**")
    await state.set_state(LegalForm.waiting_for_company_file)
    await callback.answer()

# --- ОБРАБОТКА ДАННЫХ ДЛЯ ФИЗИЧЕСКИХ ЛИЦ ---
@dp.message(IndividualForm.waiting_for_old_policy, F.photo)
async def process_old_policy(message: types.Message, state: FSMContext):
    await state.update_data(old_policy_photo=message.photo[-1].file_id)
    await message.answer("✅ Фото старого полиса получено.\n\n"
                         "2️⃣ **Шаг 2 из 4: СТС (Свидетельство о регистрации ТС)**\n"
                         "Теперь отправьте, пожалуйста, фото СТС (лицевая и оборотная стороны).")
    await state.set_state(IndividualForm.waiting_for_sts)

@dp.message(IndividualForm.waiting_for_sts, F.photo)
async def process_sts(message: types.Message, state: FSMContext):
    await state.update_data(sts_photo=message.photo[-1].file_id)
    await message.answer("✅ Фото СТС получено.\n\n"
                         "3️⃣ **Шаг 3 из 4: Водительское удостоверение**\n"
                         "Отправьте фото ВУ (лицевая и оборотная стороны).")
    await state.set_state(IndividualForm.waiting_for_driver_license)

@dp.message(IndividualForm.waiting_for_driver_license, F.photo)
async def process_driver_license(message: types.Message, state: FSMContext):
    await state.update_data(driver_license_photo=message.photo[-1].file_id)
    await message.answer("✅ Фото ВУ получено.\n\n"
                         "4️⃣ **Шаг 4 из 4: Паспортные данные**\n"
                         "Напишите, пожалуйста, одним сообщением:\n"
                         "• Серия и номер паспорта\n"
                         "• Кем и когда выдан\n"
                         "• Адрес регистрации\n"
                         "• Дата рождения")
    await state.set_state(IndividualForm.waiting_for_passport_data)

@dp.message(IndividualForm.waiting_for_passport_data, F.text)
async def process_passport_data(message: types.Message, state: FSMContext):
    await state.update_data(passport_data=message.text)
    user_data = await state.get_data()

    # Формируем сообщение для админа
    report = (
        f"🟢 **НОВАЯ ЗАЯВКА ОТ ФИЗИЧЕСКОГО ЛИЦА**\n\n"
        f"👤 **Клиент:** {message.from_user.full_name}\n"
        f"🆔 **User ID:** `{message.from_user.id}`\n\n"
        f"**Предоставленные данные:**\n"
        f"📄 Старый полис: фото получено.\n"
        f"📑 СТС: фото получено.\n"
        f"🚗 ВУ: фото получено.\n"
        f"📋 Паспортные данные: {user_data['passport_data']}\n"
    )

    for admin_id in ADMIN_IDS:
        await bot.send_photo(admin_id, user_data['old_policy_photo'], caption=report)
        await bot.send_photo(admin_id, user_data['sts_photo'])
        await bot.send_photo(admin_id, user_data['driver_license_photo'])

    await message.answer("✅ **Спасибо!** Ваша заявка отправлена брокеру. Он свяжется с вами в ближайшее время.\n\n"
                         "Вернуться в главное меню: /start")
    await state.clear()

# --- ОБРАБОТКА ДАННЫХ ДЛЯ ЮРИДИЧЕСКИХ ЛИЦ ---
@dp.message(LegalForm.waiting_for_company_file, F.document)
async def process_company_file(message: types.Message, state: FSMContext):
    file_id = message.document.file_id
    file_name = message.document.file_name

    report = (
        f"🏢 **НОВАЯ ЗАЯВКА ОТ ЮРИДИЧЕСКОГО ЛИЦА**\n\n"
        f"👤 **Клиент:** {message.from_user.full_name}\n"
        f"🆔 **User ID:** `{message.from_user.id}`\n\n"
        f"📎 **Файл с данными:** `{file_name}`"
    )

    for admin_id in ADMIN_IDS:
        await bot.send_document(admin_id, file_id, caption=report)

    await message.answer("✅ **Спасибо!** Файл с данными вашей компании отправлен брокеру. Он свяжется с вами.\n\n"
                         "Вернуться в главное меню: /start")
    await state.clear()

# --- ОБРАБОТЧИК ОШИБОК НА ЭТАПЕ ЗАГРУЗКИ ФОТО (ФИЗ. ЛИЦА)---
@dp.message(IndividualForm.waiting_for_old_policy)
async def incorrect_old_policy(message: types.Message):
    await message.answer("Пожалуйста, отправьте **фото** старого полиса ОСАГО.")

@dp.message(IndividualForm.waiting_for_sts)
async def incorrect_sts(message: types.Message):
    await message.answer("Пожалуйста, отправьте **фото** СТС (Свидетельства о регистрации ТС).")

@dp.message(IndividualForm.waiting_for_driver_license)
async def incorrect_driver_license(message: types.Message):
    await message.answer("Пожалуйста, отправьте **фото** водительского удостоверения.")

# --- ЧАСТЫЕ ВОПРОСЫ ---
@dp.message(F.text == "❓ Частые вопросы")
async def faq(message: types.Message):
    await message.answer(
        "❓ *Частые вопросы:*\n\n"
        "🔹 **Какие документы нужны?**\n"
        "   Для физ. лиц: старый полис ОСАГО, СТС, ВУ, паспортные данные.\n"
        "   Для юр. лиц: заполненный файл-шаблон.\n\n"
        "🔹 **Сколько ждать ответа?**\n"
        "   Брокер свяжется с вами в течение 10 минут после отправки заявки.\n\n"
        "🔹 **Есть ли скрытые комиссии?**\n"
        "   Нет, брокер называет полную стоимость до оплаты.",
        parse_mode="Markdown"
    )

# --- ЗАПУСК БОТА ---
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
```