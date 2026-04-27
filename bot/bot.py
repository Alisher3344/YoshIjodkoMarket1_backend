"""
Yoshijodkor Telegram Bot.

Oqim:
  /start  →  "Telefon raqamingizni ulashing" tugmasi (request_contact)
  Contact yuborilgach  →  Backend'ga POST /api/telegram/bot-auth
  Muvaffaqiyatli  →  WebApp tugmasi bilan Mini App ochiladi

Ishga tushirish (lokal):
  cd ijodkor_Backend
  set TELEGRAM_BOT_TOKEN=...           (Windows)
  set BACKEND_URL=http://localhost:8000
  set TELEGRAM_MINIAPP_URL=https://t.yoshijodkor.uz
  python -m bot.bot
"""
import asyncio
import logging
import os
import sys

import httpx
from dotenv import load_dotenv

load_dotenv()

from aiogram import Bot, Dispatcher, F
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.filters import CommandStart
from aiogram.types import (
    KeyboardButton,
    Message,
    ReplyKeyboardMarkup,
    ReplyKeyboardRemove,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    WebAppInfo,
)

# Konfiguratsiya .env yoki environment'dan
BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000").rstrip("/")
MINIAPP_URL = os.getenv(
    "TELEGRAM_MINIAPP_URL", "https://yoshijodkor.uz"
).rstrip("/")

if not BOT_TOKEN:
    print("❌ TELEGRAM_BOT_TOKEN environment variable not set")
    sys.exit(1)

logging.basicConfig(level=logging.INFO)

bot = Bot(
    token=BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher()


def contact_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(
                    text="📱 Telefon raqamni ulashish",
                    request_contact=True,
                )
            ]
        ],
        resize_keyboard=True,
        one_time_keyboard=True,
    )


def webapp_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="🚀 YoshIjodkor Mini App",
                    web_app=WebAppInfo(url=MINIAPP_URL),
                )
            ]
        ]
    )


@dp.message(CommandStart())
async def on_start(message: Message):
    await message.answer(
        "👋 Assalomu alaykum!\n\n"
        "<b>YoshIjodkor</b> botiga xush kelibsiz.\n\n"
        "Davom etish uchun telefon raqamingizni ulashing 👇",
        reply_markup=contact_keyboard(),
    )


@dp.message(F.contact)
async def on_contact(message: Message):
    contact = message.contact
    if not contact:
        return

    # Faqat o'zining kontaktini qabul qilamiz
    if contact.user_id != message.from_user.id:
        await message.answer(
            "⚠️ Iltimos o'zingizning telefon raqamingizni yuboring.",
            reply_markup=contact_keyboard(),
        )
        return

    payload = {
        "telegram_id": message.from_user.id,
        "phone":       contact.phone_number,
        "first_name":  contact.first_name or message.from_user.first_name or "",
        "last_name":   contact.last_name or message.from_user.last_name or "",
        "username":    message.from_user.username,
    }

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.post(
                f"{BACKEND_URL}/api/telegram/bot-auth",
                json=payload,
                headers={"X-Bot-Token": BOT_TOKEN},
            )
        if resp.status_code != 200:
            await message.answer(
                f"❌ Server xatosi: <code>{resp.status_code}</code>\n"
                f"<code>{resp.text[:200]}</code>",
                reply_markup=ReplyKeyboardRemove(),
            )
            return
    except Exception as e:
        await message.answer(
            f"❌ Server bilan ulanib bo'lmadi:\n<code>{e}</code>",
            reply_markup=ReplyKeyboardRemove(),
        )
        return

    await message.answer(
        "✅ Rahmat! Endi sizni ro'yxatga oldik.\n\n"
        "Saytga kirish uchun pastdagi tugmani bosing 👇",
        reply_markup=ReplyKeyboardRemove(),
    )
    await message.answer(
        "🎨 <b>YoshIjodkor</b> — yosh ijodkorlar mahsulotlari.",
        reply_markup=webapp_keyboard(),
    )


@dp.message()
async def on_other(message: Message):
    await message.answer(
        "Buyruqlar:\n\n"
        "/start — Boshlash va telefon ulashish",
        reply_markup=contact_keyboard(),
    )


async def main():
    print(f"🤖 Bot polling started.  backend={BACKEND_URL}  miniapp={MINIAPP_URL}")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
