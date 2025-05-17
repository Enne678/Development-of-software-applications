import aiosqlite
import os
from dotenv import load_dotenv

# Загружаем .env (нужен только для любого будущего расширения)
load_dotenv()
# Путь к файлу базы (он создастся рядом с этим скриптом)
DB_PATH = os.path.join(os.path.dirname(__file__), "database.db")


async def init_db():
    """
    Создаёт файл SQLite (если нет) и две таблицы:
    - currencies(id, currency_name, rate)
    - admins(id, chat_id)
    """
    # Открываем соединение с базой
    async with aiosqlite.connect(DB_PATH) as db:
        # Всегда приводим имена валют к верхнему регистру при сравнении
        await db.execute("""
            CREATE TABLE IF NOT EXISTS currencies (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                currency_name TEXT NOT NULL UNIQUE,
                rate REAL NOT NULL
            );
        """)
        await db.execute("""
            CREATE TABLE IF NOT EXISTS admins (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id TEXT NOT NULL UNIQUE
            );
        """)
        # Фиксируем изменения на диске
        await db.commit()