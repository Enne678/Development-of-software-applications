import aiosqlite
import asyncio
from db import DB_PATH

async def add_admin(chat_id: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR IGNORE INTO admins(chat_id) VALUES(?)",
            (chat_id,)
        )
        await db.commit()
        print(f"Added admin {chat_id}")

if __name__ == "__main__":
    chat_id = input("Введите ваш chat_id: ").strip()
    asyncio.run(add_admin(chat_id))