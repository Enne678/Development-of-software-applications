import os
import asyncio
from dotenv import load_dotenv

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

import asyncpg
from db import init_db, get_pool

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

class CurrencyStates(StatesGroup):
    action = State()
    add_name = State()
    add_rate = State()
    del_name = State()
    upd_name = State()
    upd_rate = State()

class ConvertStates(StatesGroup):
    name = State()
    amount = State()

storage = MemoryStorage()
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher(storage=storage)

manage_kb = types.ReplyKeyboardMarkup(
    keyboard=[[
        types.KeyboardButton(text="Добавить валюту"),
        types.KeyboardButton(text="Удалить валюту"),
        types.KeyboardButton(text="Изменить курс валюты"),
    ]],
    resize_keyboard=True,
    one_time_keyboard=True
)

pool: asyncpg.Pool

async def is_admin(chat_id: str) -> bool:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT 1 FROM admins WHERE chat_id = $1", chat_id)
    return row is not None

@dp.startup()
async def on_startup():
    global pool
    pool = await get_pool()
    await init_db()

@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    uid = str(message.from_user.id)
    if await is_admin(uid):
        commands = ["/start", "/manage_currency", "/get_currencies", "/convert"]
    else:
        commands = ["/start", "/get_currencies", "/convert"]
    await message.reply("Доступные команды:\n" + "\n".join(commands))

@dp.message(Command("manage_currency"))
async def cmd_manage(message: types.Message, state: FSMContext):
    uid = str(message.from_user.id)
    if not await is_admin(uid):
        await message.reply("Нет доступа к команде")
        return
    await message.reply("Выберите действие:", reply_markup=manage_kb)
    await state.set_state(CurrencyStates.action)

@dp.message(StateFilter(CurrencyStates.action))
async def process_action(message: types.Message, state: FSMContext):
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
    name = message.text.strip().upper()
    async with pool.acquire() as conn:
        exists = await conn.fetchval("SELECT 1 FROM currencies WHERE currency_name = $1", name)
    if exists:
        await message.reply("Данная валюта уже существует")
        await state.clear()
        return
    await state.update_data(currency_name=name)
    await message.reply("Введите курс к рублю")
    await state.set_state(CurrencyStates.add_rate)

@dp.message(StateFilter(CurrencyStates.add_rate))
async def add_rate(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data["currency_name"]
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.reply("Неверный формат. Введите число.")
        return
    async with pool.acquire() as conn:
        await conn.execute(
            "INSERT INTO currencies(currency_name, rate) VALUES($1, $2)",
            name, rate
        )
    await message.reply(f"Валюта {name} успешно добавлена")
    await state.clear()

@dp.message(StateFilter(CurrencyStates.del_name))
async def del_name(message: types.Message, state: FSMContext):
    name = message.text.strip().upper()
    async with pool.acquire() as conn:
        await conn.execute("DELETE FROM currencies WHERE currency_name = $1", name)
    await message.reply(f"Валюта {name} удалена (если была).")
    await state.clear()

@dp.message(StateFilter(CurrencyStates.upd_name))
async def upd_name(message: types.Message, state: FSMContext):
    name = message.text.strip().upper()
    await state.update_data(currency_name=name)
    await message.reply("Введите новый курс к рублю")
    await state.set_state(CurrencyStates.upd_rate)

@dp.message(StateFilter(CurrencyStates.upd_rate))
async def upd_rate(message: types.Message, state: FSMContext):
    data = await state.get_data()
    name = data["currency_name"]
    try:
        rate = float(message.text.replace(",", "."))
    except ValueError:
        await message.reply("Неверный формат. Введите число.")
        return
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE currencies SET rate = $1 WHERE currency_name = $2",
            rate, name
        )
    await message.reply(f"Курс валюты {name} обновлён.")
    await state.clear()

@dp.message(Command("get_currencies"))
async def cmd_get_currencies(message: types.Message):
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT currency_name, rate FROM currencies")
    if not rows:
        await message.reply("Нет сохранённых валют.")
        return
    text = "\n".join(f"{r['currency_name']}: {r['rate']}" for r in rows)
    await message.reply(text)

@dp.message(Command("convert"))
async def cmd_convert(message: types.Message, state: FSMContext):
    await message.reply("Введите название валюты")
    await state.set_state(ConvertStates.name)

@dp.message(StateFilter(ConvertStates.name))
async def conv_name(message: types.Message, state: FSMContext):
    name = message.text.strip().upper()
    async with pool.acquire() as conn:
        rate = await conn.fetchval("SELECT rate FROM currencies WHERE currency_name = $1", name)
    if rate is None:
        await message.reply("Валюта не найдена.")
        await state.clear()
        return
    await state.update_data(rate=rate)
    await message.reply("Введите сумму")
    await state.set_state(ConvertStates.amount)

@dp.message(StateFilter(ConvertStates.amount))
async def conv_amount(message: types.Message, state: FSMContext):
    data = await state.get_data()
    try:
        amt = float(message.text.replace(",", "."))
    except ValueError:
        await message.reply("Неверный формат. Введите число.")
        return
    rub = amt * data["rate"]
    await message.reply(f"{amt} × {data['rate']} = {rub:.2f} ₽")
    await state.clear()

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
