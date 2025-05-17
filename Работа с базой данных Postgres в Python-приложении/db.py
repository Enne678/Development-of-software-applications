import os
import asyncpg
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")


async def init_db():
    """
    Создаёт таблицы currencies и admins в PostgreSQL.
    """
    conn = await asyncpg.connect(DATABASE_URL)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS currencies (
            id SERIAL PRIMARY KEY,
            currency_name TEXT NOT NULL UNIQUE,
            rate NUMERIC NOT NULL
        );
    """)

    await conn.execute("""
        CREATE TABLE IF NOT EXISTS admins (
            id SERIAL PRIMARY KEY,
            chat_id TEXT NOT NULL UNIQUE
        );
    """)

    await conn.close()


async def get_pool():
    """
    Создаёт и возвращает пул соединений.
    """
    return await asyncpg.create_pool(DATABASE_URL)
