import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.filters.state import StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import aiosqlite
from db import init_db, DB_PATH

# Загружаем BOT_TOKEN из .env
load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

# FSM‑состояния для /manage_currency
class CurrencyStates(StatesGroup):
    action = State()
    add_name = State()
    add_rate = State()
    del_name = State()
    upd_name = State()
    upd_rate = State()

# FSM‑состояния для /convert
class ConvertStates(StatesGroup):
    name = State()
    amount = State()

# Инициализируем бота и диспетчер с хранилищем FSM
storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

# Клавиатура для админского меню
manage_kb = types.ReplyKeyboardMarkup(
    keyboard=[[
        types.KeyboardButton(text="Добавить валюту"),
        types.KeyboardButton(text="Удалить валюту"),
        types.KeyboardButton(text="Изменить курс валюты"),
    ]],
    resize_keyboard=True,
    one_time_keyboard=True
)

async def is_admin(chat_id: str) -> bool:
    """
    Проверяем, есть ли chat_id в таблице admins.
    Открываем соединение к SQLite по DB_PATH.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM admins WHERE chat_id = ?", (chat_id,)
        )
        row = await cursor.fetchone()
    return row is not None

@dp.startup()
async def on_startup():
    """
    При старте:
    1) Инициализируем схему (создаём таблицы)
    2) Ничего больше не сохраняем — будем каждый раз открывать соединение
    """
    await init_db()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    """
    /start — показываем список команд в зависимости от прав.
    """
    uid = str(message.from_user.id)
    if await is_admin(uid):
        text = (
            "/start\n"
            "/manage_currency\n"
            "/get_currencies\n"
            "/convert"
        )
    else:
        text = (
            "/start\n"
            "/get_currencies\n"
            "/convert"
        )
    await message.reply("Доступные команды:\n" + text)

@dp.message(Command("manage_currency"))
async def cmd_manage(message: types.Message, state: FSMContext):
    """
    /manage_currency — только для админов.
    Показываем кнопки: добавить, удалить, изменить курс.
    """
    uid = str(message.from_user.id)
    if not await is_admin(uid):
        await message.reply("Нет доступа к команде")
        return
    await message.reply("Выберите действие:", reply_markup=manage_kb)
    await state.set_state(CurrencyStates.action)

@dp.message(StateFilter(CurrencyStates.action))
async def process_action(message: types.Message, state: FSMContext):
    """
    Обработка выбора в админ‑меню.
    """
    text = message.text
    if text == "Добавить валюту":
        await message.reply("Введите название валюты")
        await state.set_state(CurrencyStates.add_name)
    elif text == "Удалить валюту":
        await message.reply("Введите название валюты")
        await state.set_state(CurrencyStates.del_name)
    elif text == "Изменить курс валюты":
        await message.reply("Введите название валюты")
        await state.set_state(CurrencyStates.upd_name)
    else:
        await message.reply("Операция отменена")
        await state.clear()

@dp.message(StateFilter(CurrencyStates.add_name))
async def add_name(message: types.Message, state: FSMContext):
    """
    Шаг 1 добавления: получаем имя валюты, проверяем дубли.
    """
    name = message.text.strip().upper()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT 1 FROM currencies WHERE currency_name = ?", (name,)
        )
        exists = await cursor.fetchone()
    if exists:
        await message.reply("Данная валюта уже существует")
        await state.clear()
        return
    await state.update_data(currency_name=name)
    await message.reply("Введите курс к рублю")
    await state.set_state(CurrencyStates.add_rate)

@dp.message(StateFilter(CurrencyStates.add_rate))
async def add_rate(message: types.Message, state: FSMContext):
    """
    Шаг 2 добавления: получаем курс и сохраняем валюту.
    """
    data = await state.get_data()
    name = data["currency_name"]
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.reply("Неверный формат. Введите число.")
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO currencies(currency_name, rate) VALUES(?, ?)",
            (name, rate)
        )
        await db.commit()
    await message.reply(f"Валюта: {name} успешно добавлена")
    await state.clear()

@dp.message(StateFilter(CurrencyStates.del_name))
async def del_name(message: types.Message, state: FSMContext):
    """
    Удаляем валюту по имени.
    """
    name = message.text.strip().upper()
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "DELETE FROM currencies WHERE currency_name = ?",
            (name,)
        )
        await db.commit()
    await message.reply(f"Валюта {name} удалена (если была).")
    await state.clear()

@dp.message(StateFilter(CurrencyStates.upd_name))
async def upd_name(message: types.Message, state: FSMContext):
    """
    Шаг 1 изменения курса: сохраняем имя валюты.
    """
    name = message.text.strip().upper()
    await state.update_data(currency_name=name)
    await message.reply("Введите новый курс к рублю")
    await state.set_state(CurrencyStates.upd_rate)

@dp.message(StateFilter(CurrencyStates.upd_rate))
async def upd_rate(message: types.Message, state: FSMContext):
    """
    Шаг 2 изменения курса: получаем курс и обновляем запись.
    """
    data = await state.get_data()
    name = data["currency_name"]
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.reply("Неверный формат. Введите число.")
        return
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE currencies SET rate = ? WHERE currency_name = ?",
            (rate, name)
        )
        await db.commit()
    await message.reply(f"Курс валюты {name} обновлён.")
    await state.clear()

@dp.message(Command("get_currencies"))
async def cmd_get_currencies(message: types.Message):
    """
    /get_currencies — выводим все валюты и их курсы.
    """
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute("SELECT currency_name, rate FROM currencies")
        rows = await cursor.fetchall()
    if not rows:
        await message.reply("Нет сохранённых валют.")
        return
    text = "\n".join(f"{name}: {rate}" for name, rate in rows)
    await message.reply(text)

@dp.message(Command("convert"))
async def cmd_convert(message: types.Message, state: FSMContext):
    """
    /convert — запрашиваем валюту для конвертации.
    """
    await message.reply("Введите название валюты")
    await state.set_state(ConvertStates.name)

@dp.message(StateFilter(ConvertStates.name))
async def conv_name(message: types.Message, state: FSMContext):
    """
    Шаг 1 конвертации: читаем курс из БД.
    """
    name = message.text.strip().upper()
    async with aiosqlite.connect(DB_PATH) as db:
        cursor = await db.execute(
            "SELECT rate FROM currencies WHERE currency_name = ?",
            (name,)
        )
        row = await cursor.fetchone()
    if row is None:
        await message.reply("Валюта не найдена.")
        await state.clear()
        return
    rate = row[0]
    await state.update_data(rate=rate)
    await message.reply("Введите сумму")
    await state.set_state(ConvertStates.amount)

@dp.message(StateFilter(ConvertStates.amount))
async def conv_amount(message: types.Message, state: FSMContext):
    """
    Шаг 2 конвертации: получаем сумму, считаем и выводим результат.
    """
    data = await state.get_data()
    try:
        amt = float(message.text.replace(",", "."))
    except ValueError:
        await message.reply("Неверный формат. Введите число.")
        return
    rub = amt * data["rate"]
    await message.reply(f"{amt} × {data['rate']} = {rub:.2f} ₽")
    await state.clear()

# Запуск поллинга
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())