from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text
from app.core.database import engine, Base
from app.routes import auth, products, orders, custom_orders, users, contact, students


# Eski jadvallarga yangi ustunlarni avtomatik qo'shish (Postgres uchun)
MIGRATION_SQL = [
    # users — yangi ustunlar
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS full_name VARCHAR(300) DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS phone VARCHAR(50) DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS school VARCHAR(300) DEFAULT ''",
    "ALTER TABLE users ADD COLUMN IF NOT EXISTS avatar TEXT DEFAULT ''",
    # products — student_id ustun
    "ALTER TABLE products ADD COLUMN IF NOT EXISTS student_id INTEGER REFERENCES students(id) ON DELETE CASCADE",
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
        "http://localhost:5174",
        "https://yoshijodkor.uz",
        "https://www.yoshijodkor.uz",
    ],
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