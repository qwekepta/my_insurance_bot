import asyncio
import logging
import os
from aiogram import Bot, Dispatcher, types
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import Command
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext

TOKEN = os.getenv("TOKEN")
if not TOKEN:
    raise ValueError("Переменная окружения TOKEN не установлена!")

ADMIN_IDS = [1259255945]

logging.basicConfig(level=logging.INFO)
storage = MemoryStorage()
bot = Bot(token=TOKEN, default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN))
dp = Dispatcher(storage=storage)

main_kb = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="Новая заявка")],
        [KeyboardButton(text="Частые вопросы")]
    ],
    resize_keyboard=True
)

client_type_kb = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Физическое лицо", callback_data="client_individual")],
    [InlineKeyboardButton(text="Юридическое лицо", callback_data="client_legal")]
])

class IndividualForm(StatesGroup):
    waiting_for_old_policy = State()
    waiting_for_sts = State()
    waiting_for_driver_license = State()
    waiting_for_passport_data = State()

class LegalForm(StatesGroup):
    waiting_for_company_file = State()

@dp.message(Command("start"))
async def start_cmd(message: types.Message):
    await message.answer(
        "Добро пожаловать! Я - бот страхового брокера БЛГС.\n"
        "Я помогу быстро отправить заявку на оформление ОСАГО или КАСКО.\n\n"
        "Просто нажмите на кнопку Новая заявка, чтобы начать.",
        reply_markup=main_kb
    )

@dp.message(lambda message: message.text == "Новая заявка")
async def new_order(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Выберите тип клиента:", reply_markup=client_type_kb)

@dp.callback_query(lambda c: c.data == "client_individual")
async def process_individual(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Отлично! Начинаем оформление для физического лица.\n\n"
                                     "1 Шаг 1 из 4: Старый полис ОСАГО\n"
                                     "Пожалуйста, отправьте фото старого полиса ОСАГО.")
    await state.set_state(IndividualForm.waiting_for_old_policy)
    await callback.answer()

@dp.callback_query(lambda c: c.data == "client_legal")
async def process_legal(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("Хорошо. Отправьте, пожалуйста, файл с данными для юридического лица.\n\n"
                                     "Ожидание файла...")
    await state.set_state(LegalForm.waiting_for_company_file)
    await callback.answer()

@dp.message(IndividualForm.waiting_for_old_policy)
async def process_old_policy(message: types.Message, state: FSMContext):
    if message.photo:
        await state.update_data(old_policy_photo=message.photo[-1].file_id)
        await message.answer("Фото старого полиса получено.\n\n"
                             "2 Шаг 2 из 4: СТС\n"
                             "Теперь отправьте, пожалуйста, фото СТС.")
        await state.set_state(IndividualForm.waiting_for_sts)
    else:
        await message.answer("Пожалуйста, отправьте фото старого полиса ОСАГО.")

@dp.message(IndividualForm.waiting_for_sts)
async def process_sts(message: types.Message, state: FSMContext):
    if message.photo:
        await state.update_data(sts_photo=message.photo[-1].file_id)
        await message.answer("Фото СТС получено.\n\n"
                             "3 Шаг 3 из 4: Водительское удостоверение\n"
                             "Отправьте фото ВУ.")
        await state.set_state(IndividualForm.waiting_for_driver_license)
    else:
        await message.answer("Пожалуйста, отправьте фото СТС.")

@dp.message(IndividualForm.waiting_for_driver_license)
async def process_driver_license(message: types.Message, state: FSMContext):
    if message.photo:
        await state.update_data(driver_license_photo=message.photo[-1].file_id)
        await message.answer("Фото ВУ получено.\n\n"
                             "4 Шаг 4 из 4: Паспортные данные\n"
                             "Напишите, пожалуйста, одним сообщением:\n"
                             "Серия и номер паспорта\n"
                             "Кем и когда выдан\n"
                             "Адрес регистрации\n"
                             "Дата рождения")
        await state.set_state(IndividualForm.waiting_for_passport_data)
    else:
        await message.answer("Пожалуйста, отправьте фото водительского удостоверения.")

@dp.message(IndividualForm.waiting_for_passport_data)
async def process_passport_data(message: types.Message, state: FSMContext):
    if message.text:
        await state.update_data(passport_data=message.text)
        user_data = await state.get_data()

        report = (
            f"НОВАЯ ЗАЯВКА ОТ ФИЗИЧЕСКОГО ЛИЦА\n\n"
            f"Клиент: {message.from_user.full_name}\n"
            f"User ID: {message.from_user.id}\n\n"
            f"Предоставленные данные:\n"
            f"Старый полис: фото получено.\n"
            f"СТС: фото получено.\n"
            f"ВУ: фото получено.\n"
            f"Паспортные данные: {user_data['passport_data']}\n"
        )

        for admin_id in ADMIN_IDS:
            await bot.send_photo(admin_id, user_data['old_policy_photo'], caption=report)
            await bot.send_photo(admin_id, user_data['sts_photo'])
            await bot.send_photo(admin_id, user_data['driver_license_photo'])

        await message.answer("Спасибо! Ваша заявка отправлена брокеру. Он свяжется с вами в ближайшее время.\n\n"
                             "Вернуться в главное меню: /start")
        await state.clear()
    else:
        await message.answer("Пожалуйста, напишите текстом паспортные данные.")

@dp.message(LegalForm.waiting_for_company_file)
async def process_company_file(message: types.Message, state: FSMContext):
    if message.document:
        file_id = message.document.file_id
        file_name = message.document.file_name

        report = (
            f"НОВАЯ ЗАЯВКА ОТ ЮРИДИЧЕСКОГО ЛИЦА\n\n"
            f"Клиент: {message.from_user.full_name}\n"
            f"User ID: {message.from_user.id}\n\n"
            f"Файл с данными: {file_name}"
        )

        for admin_id in ADMIN_IDS:
            await bot.send_document(admin_id, file_id, caption=report)

        await message.answer("Спасибо! Файл с данными вашей компании отправлен брокеру. Он свяжется с вами.\n\n"
                             "Вернуться в главное меню: /start")
        await state.clear()
    else:
        await message.answer("Пожалуйста, отправьте файл с данными компании.")

@dp.message(lambda message: message.text == "Частые вопросы")
async def faq(message: types.Message):
    await message.answer(
        "Частые вопросы:\n\n"
        "Какие документы нужны?\n"
        "Для физ. лиц: старый полис ОСАГО, СТС, ВУ, паспортные данные.\n"
        "Для юр. лиц: заполненный файл-шаблон.\n\n"
        "Сколько ждать ответа?\n"
        "Брокер свяжется с вами в течение 10 минут после отправки заявки.\n\n"
        "Есть ли скрытые комиссии?\n"
        "Нет, брокер называет полную стоимость до оплаты."
    )

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())