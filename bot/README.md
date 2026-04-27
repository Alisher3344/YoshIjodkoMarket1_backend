# YoshIjodkor Telegram Bot

`/start` → telefon raqamni ulashish → backend'ga POST → user yaratiladi → Mini App tugmasi.

## 1. Dependencies

```bash
cd ijodkor_Backend
venv\Scripts\activate    # Windows
pip install -r requirements.txt
```

`aiogram==3.4.1` allaqachon `requirements.txt`'da bor.

## 2. Environment variables

`.env` faylga (yoki shellda `set ...`):

```
TELEGRAM_BOT_TOKEN=<BotFather'dan olgan token>
BACKEND_URL=http://localhost:8000
TELEGRAM_MINIAPP_URL=https://miniapp.yoshijodkor.uz
```

> ⚠️ **Token maxfiyligi**: bot tokenini hech qachon git'ga qo'shmang.
> Faqat `.env` (gitignore'da) yoki Railway env variables'da saqlang.

## 3. Lokal ishga tushirish

Terminal 1 — backend:
```bash
cd ijodkor_Backend
venv\Scripts\activate
uvicorn app.main:app --reload --port 8000
```

Terminal 2 — bot:
```bash
cd ijodkor_Backend
venv\Scripts\activate
python -m bot.bot
```

Telegram'da botingizga `/start` yuboring → telefon raqamni ulashing.

## 4. Production'da (Railway)

Bot uchun **alohida service** qo'shing:
1. Railway dashboard → New Service → "Deploy from GitHub" (xuddi backend kabi)
2. **Start command**: `python -m bot.bot`
3. **Environment variables**:
   - `TELEGRAM_BOT_TOKEN`
   - `BACKEND_URL=https://web-production-c57d3.up.railway.app`
   - `TELEGRAM_MINIAPP_URL=https://miniapp.yoshijodkor.uz`

Bot polling rejimida ishlaydi (webhook kerak emas) — har doim 1 ta replica yetarli.
