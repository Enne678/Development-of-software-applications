import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext

import httpx

# Загрузка переменных окружения и инициализация URL сервисов
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")
CM_URL = os.getenv("CURRENCY_MANAGER_URL", "http://127.0.0.1:5001")
DM_URL = os.getenv("DATA_MANAGER_URL", "http://127.0.0.1:5002")

# FSM‑состояния для управления валютами
class CurrencyStates(StatesGroup):
    action = State()
    name = State()
    rate = State()

# FSM‑состояния для конвертации
class ConvertStates(StatesGroup):
    name = State()
    amount = State()

# Инициализация бота и диспетчера с памятью состояний
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=MemoryStorage())

# Главное меню с тремя кнопками
main_kb = types.ReplyKeyboardMarkup(
    keyboard=[[
        types.KeyboardButton(text="Управление валютами"),
        types.KeyboardButton(text="Список валют"),
        types.KeyboardButton(text="Конвертация"),
    ]],
    resize_keyboard=True
)

# Меню управления валютами с тремя кнопками
manage_kb = types.ReplyKeyboardMarkup(
    keyboard=[[
        types.KeyboardButton(text="Добавить валюту"),
        types.KeyboardButton(text="Удалить валюту"),
        types.KeyboardButton(text="Изменить курс валюты"),
    ]],
    resize_keyboard=True,
    one_time_keyboard=True
)

# Обработчик команды /start — показываем главное меню
@dp.message(Command("start"))
async def cmd_start(message: types.Message):
    await message.answer("Выберите команду:", reply_markup=main_kb)

# Обработчик выбора "Управление валютами" — показываем подменю и устанавливаем состояние
@dp.message(lambda m: m.text == "Управление валютами")
async def manage_menu(message: types.Message, state: FSMContext):
    await message.answer("Выберите действие:", reply_markup=manage_kb)
    await state.set_state(CurrencyStates.action)

# Обработка выбранного действия — сохраняем его и запрашиваем название валюты
@dp.message(StateFilter(CurrencyStates.action))
async def on_action(message: types.Message, state: FSMContext):
    await state.update_data(action=message.text)
    await message.answer("Введите название валюты:")
    await state.set_state(CurrencyStates.name)

# Обработка ввода названия валюты — в зависимости от действия либо переходим к курсу, либо удаляем
@dp.message(StateFilter(CurrencyStates.name))
async def got_name(message: types.Message, state: FSMContext):
    name = message.text.strip().upper()
    await state.update_data(name=name)
    data = await state.get_data()
    if data["action"] in ("Добавить валюту", "Изменить курс валюты"):
        await message.answer("Введите курс к рублю:")
        await state.set_state(CurrencyStates.rate)
    else:
        async with httpx.AsyncClient() as client:
            await client.post(f"{CM_URL}/delete", json={"currency_name": name})
        await message.answer(f"Валюта {name} удалена")
        await state.clear()

# Обработка ввода курса — выполняем add или update и завершаем FSM
@dp.message(StateFilter(CurrencyStates.rate))
async def got_rate(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    rate = float(message.text.replace(",", "."))
    action = data["action"]
    endpoint = "/load" if action == "Добавить валюту" else "/update_currency"

    async with httpx.AsyncClient() as client:
        resp = await client.post(f"{CM_URL}{endpoint}", json={"currency_name": name, "rate": rate})

    if resp.status_code == 200:
        verb = "добавлена" if action == "Добавить валюту" else "обновлён"
        await message.answer(f"Валюта {name} {verb} на {rate}")
    else:
        await message.answer(f"Ошибка: {resp.status_code}")

    await state.clear()

# Обработчик вывода списка валют — отправляем GET запрос на data-manager
@dp.message(lambda m: m.text in ("Список валют", "/get_currencies"))
async def list_currencies(message: types.Message):
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{DM_URL}/currencies")
    if resp.status_code == 200:
        lst = resp.json()
        text = "\n".join(f"{c['currency_name']}: {c['rate']}" for c in lst) or "Список пуст"
    else:
        text = f"Ошибка: {resp.status_code}"
    await message.answer(text)

# Обработчик начала конвертации — запрашиваем название валюты и устанавливаем состояние
@dp.message(lambda m: m.text in ("Конвертация", "/convert"))
async def conv_start(message: types.Message, state: FSMContext):
    await message.answer("Введите название валюты:")
    await state.set_state(ConvertStates.name)

# Обработка ввода названия в конвертации — запрашиваем сумму и устанавливаем состояние
@dp.message(StateFilter(ConvertStates.name))
async def conv_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text.strip().upper())
    await message.answer("Введите сумму:")
    await state.set_state(ConvertStates.amount)

# Обработка ввода суммы — выполняем конвертацию через data-manager и завершаем FSM
@dp.message(StateFilter(ConvertStates.amount))
async def conv_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data["name"]
    amt = float(message.text.replace(",", "."))
    async with httpx.AsyncClient() as client:
        resp = await client.get(f"{DM_URL}/convert", params={"currency_name": name, "amount": amt})
    if resp.status_code == 200:
        result = resp.json()["result"]
        await message.answer(f"{amt} × курс {name} = {result:.2f} ₽")
    else:
        await message.answer("Валюта не найдена")
    await state.clear()

# Основная функция — запуск поллинга бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())