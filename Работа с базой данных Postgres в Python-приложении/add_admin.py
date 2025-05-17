import os
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

async def add_admin(chat_id: str):
    conn = await asyncpg.connect(DATABASE_URL)
    await conn.execute("""
        INSERT INTO admins(chat_id)
        VALUES($1)
        ON CONFLICT (chat_id) DO NOTHING
    """, chat_id)
    await conn.close()
    print(f"Администратор {chat_id} добавлен (или уже существует).")

if __name__ == "__main__":
    chat_id = input("Введите ваш chat_id: ").strip()
    asyncio.run(add_admin(chat_id))
