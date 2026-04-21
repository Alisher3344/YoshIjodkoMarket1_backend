from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.routes import auth, products, orders, custom_orders, users, contact


@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Database tayyor")
    yield   


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
         "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://yoshijodkor.uz",
    "https://www.yoshijodkor.uz",
    "*",
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