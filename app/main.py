from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.database import engine, Base, AsyncSessionLocal
from app.routes import auth, products, orders, custom_orders, users, contact, students, schools, telegram, regions
from app.seed_regions import seed_regions_if_empty


# Eski jadvallarga yangi ustunlarni avtomatik qo'shish (Postgres uchun)
MIGRATION_SQL = [
    # users — yangi ustunlar
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(300) DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50) DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS school VARCHAR(300) DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar TEXT DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS school_id INTEGER REFERENCES schools(id) ON DELETE SET NULL",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_id BIGINT UNIQUE",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS telegram_username VARCHAR(100) DEFAULT ''",
    # schools — hududiy ierarxiya (Respublika → Viloyat → Shahar/Tuman)
    "ALTER TABLE schools ADD COLUMN IF NOT EXISTS country VARCHAR(100) DEFAULT 'O''zbekiston'",
    "ALTER TABLE schools ADD COLUMN IF NOT EXISTS city VARCHAR(200) DEFAULT ''",
    # students — school_id ustun (bir maktabga 2+ admin ulansa, ular bir xil studentlarni ko'rishadi)
    "ALTER TABLE students ADD COLUMN IF NOT EXISTS school_id INTEGER REFERENCES schools(id) ON DELETE SET NULL",
    # students — Telegram orqali ro'yxatdan o'tish uchun ustunlar
    "ALTER TABLE students ADD COLUMN IF NOT EXISTS user_id INTEGER REFERENCES users(id) ON DELETE CASCADE",
    "ALTER TABLE students ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'approved'",
    "ALTER TABLE students ALTER COLUMN admin_id DROP NOT NULL",
    # products — student_id ustun
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS student_id INTEGER REFERENCES students(id) ON DELETE CASCADE",
    # products — Telegram orqali yuklangan mahsulotlarni tasdiqlash uchun
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS status VARCHAR(20) DEFAULT 'approved'",
]


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        for stmt in MIGRATION_SQL:
            try:
                await conn.execute(text(stmt))
                print(f"OK migration: {stmt[:80]}")
            except Exception as e:
                print(f"SKIP migration ({type(e).__name__}): {stmt[:80]}")
    print("Database tayyor")

    # Hududiy ma'lumotlarni seed qilish (jadval bo'sh bo'lsa)
    try:
        async with AsyncSessionLocal() as session:
            added = await seed_regions_if_empty(session)
            if added:
                print(f"OK seed: {added} ta region qo'shildi (shaharlar+tumanlar bilan)")
            else:
                print("SKIP seed: regions jadvali allaqachon to'la")
    except Exception as e:
        print(f"SKIP seed regions ({type(e).__name__}): {e}")

    print("=== Registered routes ===")
    for route in app.routes:
        if hasattr(route, "methods") and hasattr(route, "path"):
            for m in route.methods:
                print(f"  {m:7} {route.path}")
    print("=========================")
    yield


app = FastAPI(lifespan=lifespan, redirect_slashes=False)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:5174",      # Telegram Mini App lokal dev
        "http://127.0.0.1:5174",
        "https://yoshijodkor.uz",
        "https://www.yoshijodkor.uz",
        "https://t.yoshijodkor.uz",   # Mini App subdomeni (taklif)
        "https://miniapp.yoshijodkor.uz",
        "https://yosh-ijodko-market1.vercel.app",  # Vercel Mini App
    ],
    allow_origin_regex=r"https://yosh-ijodko-market1-.*\.vercel\.app",  # Vercel preview deploylari
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router,          prefix="/api/auth",          tags=["Auth"])
app.include_router(products.router,      prefix="/api/products",      tags=["Mahsulotlar"])
app.include_router(orders.router,        prefix="/api/orders",        tags=["Buyurtmalar"])
app.include_router(custom_orders.router, prefix="/api/custom-orders", tags=["Maxsus buyurtmalar"])
app.include_router(users.router,         prefix="/api/users",         tags=["Foydalanuvchilar"])
app.include_router(contact.router,       prefix="/api/contact",       tags=["Aloqa"])
app.include_router(students.router,      prefix="/api/students",      tags=["O'quvchilar"])
app.include_router(schools.router,       prefix="/api/schools",       tags=["Maktablar"])
app.include_router(telegram.router,      prefix="/api/telegram",      tags=["Telegram"])
app.include_router(regions.router,       prefix="/api/regions",       tags=["Hududlar"])