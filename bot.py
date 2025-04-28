import os
import logging
import asyncio

from dotenv import load_dotenv
from aiogram import Bot, Dispatcher, F
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

# Загрузка переменных окружения из .env и из системных переменных
load_dotenv()
TOKEN = os.environ.get("BOT_TOKEN")
if not TOKEN:
    logging.error("Не задан BOT_TOKEN! Проверьте .env или переменные окружения.")
    exit(1)

# Настройка базового логирования уровня INFO для aiogram
logging.basicConfig(level=logging.INFO)

# Создание объекта бота и диспетчера для регистрации хендлеров
bot = Bot(token=TOKEN)
dp = Dispatcher()

# Определение состояний для команды /save_currency: сначала вводим код валюты, затем её курс
class SaveCurrency(StatesGroup):
    currency = State()
    rate = State()

# Определение состояний для команды /convert: сначала вводим код валюты, затем сумму
class ConvertCurrency(StatesGroup):
    currency = State()
    amount = State()

# Глобальный словарь для хранения курсов валют в формате {'USD': 75.0, ...}
exchange_rates: dict[str, float] = {}

# Обработчик старта (/start) — чтобы бот отвечал на команду и не игнорировал обновления
@dp.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer(
        "Привет! Я бот-конвертер валют.\n"
        "Сначала задайте курс: /save_currency\n"
        "Потом конвертируйте: /convert"
    )

# Обработчик команды /save_currency — запрашиваем код валюты
@dp.message(Command("save_currency"))
async def cmd_save_currency(message: Message, state: FSMContext):
    await message.answer("Введите код валюты (например, USD):")
    await state.set_state(SaveCurrency.currency)

# Обработчик получения кода валюты — запоминаем и запрашиваем курс
@dp.message(SaveCurrency.currency, F.text)
async def process_currency_name(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.update_data(currency=code)
    await message.answer(f"Введите курс {code} к RUB:")
    await state.set_state(SaveCurrency.rate)

# Обработчик получения курса — сохраняем в словарь и завершаем FSM
@dp.message(SaveCurrency.rate, F.text)
async def process_currency_rate(message: Message, state: FSMContext):
    data = await state.get_data()
    code = data["currency"]
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Нужно число, например: 74.5")
        return
    exchange_rates[code] = rate
    await message.answer(f"Сохранено: 1 {code} = {rate:.2f} RUB")
    await state.clear()

# Обработчик команды /convert — запрашиваем код валюты для конвертации
@dp.message(Command("convert"))
async def cmd_convert(message: Message, state: FSMContext):
    await message.answer("Введите код валюты для конвертации:")
    await state.set_state(ConvertCurrency.currency)

# Обработчик получения кода валюты при конвертации — запоминаем и запрашиваем сумму
@dp.message(ConvertCurrency.currency, F.text)
async def process_convert_currency(message: Message, state: FSMContext):
    code = message.text.strip().upper()
    await state.update_data(currency=code)
    await message.answer(f"Введите сумму в {code}:")
    await state.set_state(ConvertCurrency.amount)

# Обработчик получения суммы — выполняем конвертацию по сохранённому курсу
@dp.message(ConvertCurrency.amount, F.text)
async def process_convert_amount(message: Message, state: FSMContext):
    data = await state.get_data()
    code = data["currency"]
    try:
        amount = float(message.text.replace(",", "."))
    except ValueError:
        await message.answer("Нужно число.")
        return
    rate = exchange_rates.get(code)
    if rate is None:
        await message.answer("Курс не задан. Сначала /save_currency.")
    else:
        await message.answer(f"{amount:.2f} {code} = {amount*rate:.2f} RUB")
    await state.clear()

# Удаляем возможный вебхук и запускаем долгий опрос (polling) обновлений
async def main():
    await dp.start_polling(bot)  # aiogram 3: рекомендуемый запуск 6

if __name__ == "__main__":
    asyncio.run(main())