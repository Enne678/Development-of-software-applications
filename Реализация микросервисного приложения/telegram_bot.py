import os
import asyncio
import logging
from dotenv import load_dotenv
from decimal import Decimal, InvalidOperation

from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, BotCommand

import httpx

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Загрузка переменных окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
CURRENCY_MANAGER_URL = os.getenv("CURRENCY_MANAGER_URL", "http://localhost:5001")
DATA_MANAGER_URL = os.getenv("DATA_MANAGER_URL", "http://localhost:5002")

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN не найден в переменных окружения")


# FSM состояния
class CurrencyManagementStates(StatesGroup):
    choosing_action = State()
    entering_name = State()
    entering_rate = State()


class ConversionStates(StatesGroup):
    entering_currency_name = State()
    entering_amount = State()


# Инициализация бота
bot = Bot(token=BOT_TOKEN)
storage = MemoryStorage()
dp = Dispatcher(storage=storage)

# Клавиатуры
main_menu_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="💰 Управление валютами")],
        [KeyboardButton(text="📋 Список валют"), KeyboardButton(text="🔄 Конвертация")]
    ],
    resize_keyboard=True
)

manage_currency_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить валюту")],
        [KeyboardButton(text="✏️ Изменить курс валюты")],
        [KeyboardButton(text="❌ Удалить валюту")],
        [KeyboardButton(text="🔙 Назад")]
    ],
    resize_keyboard=True
)


# Команда /start
@dp.message(Command("start"))
async def cmd_start(message: types.Message, state: FSMContext):
    await state.clear()
    welcome_text = (
        "🤖 <b>Добро пожаловать в бот для работы с курсами валют!</b>\n\n"
        "Доступные функции:\n"
        "💰 Управление валютами\n"
        "📋 Просмотр списка валют\n"
        "🔄 Конвертация валют\n"
    )
    await message.answer(welcome_text, reply_markup=main_menu_keyboard, parse_mode="HTML")


# Команда /manage_currency
@dp.message(F.text == "💰 Управление валютами")
async def manage_currencies_start(message: types.Message, state: FSMContext):
    await message.answer("Выберите действие:", reply_markup=manage_currency_keyboard)
    await state.set_state(CurrencyManagementStates.choosing_action)


@dp.message(F.text == "🔙 Назад")
async def back_to_main_menu(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Главное меню", reply_markup=main_menu_keyboard)


# Обработка действий управления валютами
@dp.message(CurrencyManagementStates.choosing_action)
async def process_manage_action_choice(message: types.Message, state: FSMContext):
    action_text = message.text

    if action_text == "🔙 Назад":
        await back_to_main_menu(message, state)
        return

    actions_map = {
        "➕ Добавить валюту": "add",
        "✏️ Изменить курс валюты": "update",
        "❌ Удалить валюту": "delete"
    }

    if action_text not in actions_map:
        await message.answer("Выберите действие с помощью кнопок", reply_markup=manage_currency_keyboard)
        return

    await state.update_data(action=actions_map[action_text])
    await message.answer("Введите название валюты:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(CurrencyManagementStates.entering_name)


# Ввод названия валюты
@dp.message(CurrencyManagementStates.entering_name)
async def process_currency_name_input(message: types.Message, state: FSMContext):
    currency_name = message.text.strip().upper()

    if not currency_name.isalpha():
        await message.answer("⚠️ Введите корректное название валюты")
        return

    await state.update_data(currency_name=currency_name)
    data = await state.get_data()
    action = data.get("action")

    if action == "delete":
        await attempt_delete_currency(message, state, currency_name)
    elif action in ["add", "update"]:
        await message.answer("Введите курс к рублю:")
        await state.set_state(CurrencyManagementStates.entering_rate)


# Ввод курса валюты
@dp.message(CurrencyManagementStates.entering_rate)
async def process_currency_rate_input(message: types.Message, state: FSMContext):
    try:
        rate_str = message.text.replace(",", ".")
        rate = float(rate_str)
        if rate <= 0:
            raise ValueError("Курс должен быть положительным")
    except ValueError:
        await message.answer("⚠️ Введите корректное значение курса")
        return

    data = await state.get_data()
    currency_name = data.get("currency_name")
    action = data.get("action")

    if action == "add":
        await attempt_add_currency(message, state, currency_name, rate)
    elif action == "update":
        await attempt_update_currency(message, state, currency_name, rate)


# Функции для работы с API
async def attempt_add_currency(message: types.Message, state: FSMContext, currency_name: str, rate: float):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{CURRENCY_MANAGER_URL}/load",
                                         json={"currency_name": currency_name, "rate": rate})

            if response.status_code == 200:
                await message.answer(f"✅ Валюта <b>{currency_name}</b> успешно добавлена",
                                     parse_mode="HTML", reply_markup=main_menu_keyboard)
            elif response.status_code == 400:
                await message.answer(f"⚠️ Данная валюта уже существует",
                                     reply_markup=main_menu_keyboard)
            else:
                await message.answer("❌ Ошибка при добавлении валюты",
                                     reply_markup=main_menu_keyboard)
    except Exception as e:
        logger.error(f"Error adding currency: {e}")
        await message.answer("❌ Ошибка соединения с сервисом", reply_markup=main_menu_keyboard)
    finally:
        await state.clear()


async def attempt_update_currency(message: types.Message, state: FSMContext, currency_name: str, rate: float):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{CURRENCY_MANAGER_URL}/update_currency",
                                         json={"currency_name": currency_name, "rate": rate})

            if response.status_code == 200:
                await message.answer(f"✅ Курс валюты <b>{currency_name}</b> обновлен",
                                     parse_mode="HTML", reply_markup=main_menu_keyboard)
            elif response.status_code == 404:
                await message.answer(f"⚠️ Валюта <b>{currency_name}</b> не найдена",
                                     parse_mode="HTML", reply_markup=main_menu_keyboard)
            else:
                await message.answer("❌ Ошибка при обновлении курса",
                                     reply_markup=main_menu_keyboard)
    except Exception as e:
        logger.error(f"Error updating currency: {e}")
        await message.answer("❌ Ошибка соединения с сервисом", reply_markup=main_menu_keyboard)
    finally:
        await state.clear()


async def attempt_delete_currency(message: types.Message, state: FSMContext, currency_name: str):
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(f"{CURRENCY_MANAGER_URL}/delete",
                                         json={"currency_name": currency_name})

            if response.status_code == 200:
                await message.answer(f"✅ Валюта <b>{currency_name}</b> успешно удалена",
                                     parse_mode="HTML", reply_markup=main_menu_keyboard)
            elif response.status_code == 404:
                await message.answer(f"⚠️ Валюта <b>{currency_name}</b> не найдена",
                                     parse_mode="HTML", reply_markup=main_menu_keyboard)
            else:
                await message.answer("❌ Ошибка при удалении валюты",
                                     reply_markup=main_menu_keyboard)
    except Exception as e:
        logger.error(f"Error deleting currency: {e}")
        await message.answer("❌ Ошибка соединения с сервисом", reply_markup=main_menu_keyboard)
    finally:
        await state.clear()


# Команда /get_currencies
@dp.message(F.text.in_(["📋 Список валют", "/get_currencies"]))
async def get_all_currencies(message: types.Message, state: FSMContext):
    await state.clear()
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{DATA_MANAGER_URL}/currencies")

            if response.status_code == 200:
                currencies_data = response.json()
                if not currencies_data:
                    await message.answer("ℹ️ Список валют пуст")
                    return

                text = "📊 <b>Список валют:</b>\n\n"
                for currency_item in currencies_data:
                    rate = Decimal(str(currency_item['rate'])).quantize(Decimal('0.01'))
                    text += f"<b>{currency_item['currency_name']}</b>: {rate} ₽\n"

                await message.answer(text, parse_mode="HTML")
            else:
                await message.answer("❌ Ошибка при получении списка валют")
    except Exception as e:
        logger.error(f"Error getting currencies: {e}")
        await message.answer("❌ Ошибка соединения с сервисом")


# Команда /convert
@dp.message(F.text.in_(["🔄 Конвертация", "/convert"]))
async def start_conversion_process(message: types.Message, state: FSMContext):
    await state.clear()
    await message.answer("Введите название валюты:", reply_markup=ReplyKeyboardRemove())
    await state.set_state(ConversionStates.entering_currency_name)


@dp.message(ConversionStates.entering_currency_name)
async def process_conversion_currency_name(message: types.Message, state: FSMContext):
    currency_name = message.text.strip().upper()

    if not currency_name.isalpha():
        await message.answer("⚠️ Введите корректное название валюты")
        return

    await state.update_data(currency_name_to_convert=currency_name)
    await message.answer("Введите сумму:")
    await state.set_state(ConversionStates.entering_amount)


@dp.message(ConversionStates.entering_amount)
async def process_conversion_amount(message: types.Message, state: FSMContext):
    try:
        amount_str = message.text.replace(",", ".")
        amount = float(amount_str)
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
    except ValueError:
        await message.answer("⚠️ Введите корректную сумму")
        return

    data = await state.get_data()
    currency_name = data.get("currency_name_to_convert")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{DATA_MANAGER_URL}/convert",
                                        params={"currency_name": currency_name, "amount": amount})

            if response.status_code == 200:
                result_data = response.json()
                converted_amount = Decimal(str(result_data.get("result"))).quantize(Decimal('0.01'))

                await message.answer(f"💰 Результат: <b>{converted_amount} ₽</b>",
                                     parse_mode="HTML", reply_markup=main_menu_keyboard)
            elif response.status_code == 404:
                await message.answer(f"⚠️ Валюта {currency_name} не найдена",
                                     reply_markup=main_menu_keyboard)
            else:
                await message.answer("❌ Ошибка при конвертации",
                                     reply_markup=main_menu_keyboard)
    except Exception as e:
        logger.error(f"Error converting currency: {e}")
        await message.answer("❌ Ошибка соединения с сервисом", reply_markup=main_menu_keyboard)
    finally:
        await state.clear()


# Запуск бота
async def main():
    logger.info("Запуск бота...")

    # Установка команд меню
    commands_for_bot = [
        BotCommand(command="/start", description="Запустить бота"),
        BotCommand(command="/get_currencies", description="Список валют"),
        BotCommand(command="/convert", description="Конвертация валют")
    ]
    await bot.set_my_commands(commands_for_bot)

    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.critical(f"Ошибка при запуске: {e}")
    finally:
        await bot.session.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Бот остановлен")