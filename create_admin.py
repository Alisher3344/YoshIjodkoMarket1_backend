import asyncio
from app.core.database import AsyncSessionLocal, engine, Base
from app.models.user import User
from app.core.security import hash_password
from sqlalchemy import select


async def main():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(User).where(User.username == "admin"))
        if result.scalar_one_or_none():
            print("⚠️  'admin' allaqachon mavjud!")
            return

        db.add(User(
            name="Bosh Admin",
            username="admin",
            password=hash_password("admin123"),
            email="admin@yoshijodkor.uz",
            role="superadmin",
            active=True,
        ))
        await db.commit()

    print("✅ Admin yaratildi!")
    print("   Username : admin")
    print("   Parol    : admin123")


if __name__ == "__main__":
    asyncio.run(main())