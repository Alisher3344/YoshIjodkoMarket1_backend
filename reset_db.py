import asyncio
from app.core.database import engine, Base
from app.models import User, Product, Order, OrderItem, Student


async def reset():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    print("Baza qaytadan yaratildi")


if __name__ == "__main__":
    asyncio.run(reset())