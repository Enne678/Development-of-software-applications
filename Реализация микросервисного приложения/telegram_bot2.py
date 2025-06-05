import asyncio
import logging
import aiohttp
import os
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

# Загружаем переменные из .env файла
load_dotenv()

# Настройки
BOT_TOKEN = os.getenv("BOT_TOKEN2")
MICROSERVICE_A_URL = "http://localhost:5001/power"
MICROSERVICE_B_URL = "http://localhost:5002/square"

if not BOT_TOKEN:
    raise ValueError("BOT_TOKEN2 не найден в .env файле!")

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Инициализация бота и диспетчера
bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()


async def call_microservice_a(value):
    """Вызов микросервиса A для возведения 2 в степень"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"value": value}
            async with session.post(MICROSERVICE_A_URL, json=payload) as response:
                data = await response.json()
                if response.status == 200:
                    return data
                else:
                    return {"error": data.get("error", "Неизвестная ошибка")}
    except Exception as e:
        logger.error(f"Ошибка при вызове микросервиса A: {e}")
        return {"error": f"Ошибка соединения с микросервисом A: {str(e)}"}


async def call_microservice_b(value):
    """Вызов микросервиса B для возведения в квадрат"""
    try:
        async with aiohttp.ClientSession() as session:
            payload = {"value": value}
            async with session.post(MICROSERVICE_B_URL, json=payload) as response:
                data = await response.json()
                if response.status == 200:
                    return data
                else:
                    return {"error": data.get("error", "Неизвестная ошибка")}
    except Exception as e:
        logger.error(f"Ошибка при вызове микросервиса B: {e}")
        return {"error": f"Ошибка соединения с микросервисом B: {str(e)}"}


@dp.message(Command("start"))
async def cmd_start(message: Message):
    """Обработчик команды /start"""
    welcome_text = """
🤖 Добро пожаловать в бот математических вычислений!

Используйте команду /calc для выполнения вычислений.

Формат: /calc <число1> <число2>

Например: /calc 3 5

Бот отправит:
• Первое число на микросервис A (вычислит 2^число1)
• Второе число на микросервис B (вычислит число2^2)

Доступные команды:
/start - показать это сообщение
/calc - выполнить вычисления
/help - помощь
    """
    await message.answer(welcome_text)


@dp.message(Command("help"))
async def cmd_help(message: Message):
    """Обработчик команды /help"""
    help_text = """
ℹ️ Справка по использованию бота:

Команда: /calc <число1> <число2>

Что происходит:
1️⃣ Первое число отправляется на микросервис A
   → Вычисляется 2^число1

2️⃣ Второе число отправляется на микросервис B
   → Вычисляется число2^2

Примеры:
• /calc 3 4
  Результат: 2^3 = 8, 4^2 = 16

• /calc 5 7
  Результат: 2^5 = 32, 7^2 = 49

Ограничения:
• Для микросервиса A: степень ≤ 1000
• Для микросервиса B: число ≤ ±100000
    """
    await message.answer(help_text)


@dp.message(Command("calc"))
async def cmd_calc(message: Message):
    """Обработчик команды /calc"""
    try:
        # Получаем аргументы команды
        args = message.text.split()[1:]  # Убираем саму команду

        if len(args) != 2:
            await message.answer(
                "❌ Неверный формат команды!\n\n"
                "Используйте: /calc <число1> <число2>\n"
                "Например: /calc 3 5"
            )
            return

        # Парсим числа
        try:
            value1 = float(args[0])
            value2 = float(args[1])
        except ValueError:
            await message.answer(
                "❌ Оба аргумента должны быть числами!\n\n"
                "Например: /calc 3 5 или /calc 2.5 4.7"
            )
            return

        # Отправляем уведомление о начале обработки
        processing_msg = await message.answer("⏳ Обрабатываю запрос...")

        # Вызываем микросервисы параллельно
        tasks = [
            call_microservice_a(value1),
            call_microservice_b(value2)
        ]

        results = await asyncio.gather(*tasks)
        result_a, result_b = results

        # Формируем ответ
        response_lines = []
        response_lines.append("📊 Результаты вычислений:")
        response_lines.append("")

        if "error" not in result_a:
            response_lines.append(f"🔸 Микросервис A: 2^{value1} = {result_a['result']}")
        else:
            response_lines.append(f"❌ Ошибка микросервиса A: {result_a['error']}")

        if "error" not in result_b:
            response_lines.append(f"🔸 Микросервис B: {value2}^2 = {result_b['result']}")
        else:
            response_lines.append(f"❌ Ошибка микросервиса B: {result_b['error']}")

        # Удаляем сообщение о обработке и отправляем результат
        await processing_msg.delete()
        await message.answer("\n".join(response_lines))

    except Exception as e:
        logger.error(f"Ошибка в обработчике calc: {e}")
        await message.answer(
            f"❌ Произошла ошибка при обработке команды: {str(e)}"
        )


@dp.message()
async def handle_unknown(message: Message):
    """Обработчик неизвестных сообщений"""
    await message.answer(
        "❓ Неизвестная команда.\n\n"
        "Используйте:\n"
        "• /start - начать работу\n"
        "• /calc <число1> <число2> - выполнить вычисления\n"
        "• /help - получить справку"
    )


async def main():
    """Главная функция запуска бота"""
    logger.info("Запускается телеграм бот...")

    # Проверяем доступность микросервисов
    try:
        async with aiohttp.ClientSession() as session:
            # Проверка микросервиса A
            try:
                async with session.get("http://localhost:5001/health") as response:
                    if response.status == 200:
                        logger.info("✅ Микросервис A доступен")
                    else:
                        logger.warning(f"⚠️ Микросервис A недоступен (статус: {response.status})")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка подключения к микросервису A: {e}")

            # Проверка микросервиса B
            try:
                async with session.get("http://localhost:5002/health") as response:
                    if response.status == 200:
                        logger.info("✅ Микросервис B доступен")
                    else:
                        logger.warning(f"⚠️ Микросервис B недоступен (статус: {response.status})")
            except Exception as e:
                logger.warning(f"⚠️ Ошибка подключения к микросервису B: {e}")
    except Exception as e:
        logger.warning(f"⚠️ Не удалось проверить микросервисы: {e}")

    # Запускаем бота
    await dp.start_polling(bot)


if __name__ == '__main__':
    asyncio.run(main())