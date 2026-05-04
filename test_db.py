import os
import asyncio
import asyncpg
from dotenv import load_dotenv

load_dotenv()

async def test():
    dsn = os.getenv("DATABASE_URL")
    print(f"Connecting to: {dsn[:30]}...")  # print partial for security
    conn = await asyncpg.connect(dsn)
    version = await conn.fetchval("SELECT version();")
    print(f"PostgreSQL version: {version}")
    count = await conn.fetchval("SELECT COUNT(*) FROM sensor_data;")
    print(f"Rows in sensor_data: {count}")
    await conn.close()

asyncio.run(test())