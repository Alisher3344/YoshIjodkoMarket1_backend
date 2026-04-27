import base64
import hashlib
import hmac
import json
import time
from urllib.parse import parse_qsl

import httpx

from ..core.config import settings


# ─── Telegram Mini App initData verifikatsiyasi ─────────────────────────────
# https://core.telegram.org/bots/webapps#validating-data-received-via-the-mini-app

def verify_webapp_init_data(init_data: str, max_age_sec: int = 86400):
    """Telegram Mini App'dan kelgan initData ni HMAC-SHA256 bilan tekshiradi.
    Muvaffaqiyatli bo'lsa parsed dict qaytaradi, aks holda None.

    init_data — query-string format: "auth_date=...&hash=...&user=..."
    """
    if not init_data or not settings.TELEGRAM_BOT_TOKEN:
        return None

    try:
        parsed = dict(parse_qsl(init_data, strict_parsing=True))
    except Exception:
        return None

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        return None

    # Hashni hisoblash uchun stringni yaratish
    data_check_string = "\n".join(
        f"{k}={v}" for k, v in sorted(parsed.items())
    )

    secret_key = hmac.new(
        b"WebAppData",
        settings.TELEGRAM_BOT_TOKEN.encode(),
        hashlib.sha256,
    ).digest()

    calculated_hash = hmac.new(
        secret_key, data_check_string.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(calculated_hash, received_hash):
        return None

    # Eskirgan initData rad etiladi (default — 24 soat)
    auth_date = int(parsed.get("auth_date", "0") or 0)
    if auth_date <= 0 or (time.time() - auth_date) > max_age_sec:
        return None

    user_json = parsed.get("user")
    user = None
    if user_json:
        try:
            user = json.loads(user_json)
        except Exception:
            user = None

    return {
        "user": user,
        "auth_date": auth_date,
        "raw": parsed,
    }


async def send_telegram(
    message: str,
    image_base64: str = None,
    image_type: str = None
) -> bool:
    """Telegram'ga xabar yoki rasm+xabar yuborish"""
    if not settings.TELEGRAM_TOKEN or not settings.TELEGRAM_CHAT_ID:
        print("⚠️  Telegram token yoki chat_id yo'q")
        return False

    token   = settings.TELEGRAM_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if image_base64:
                # Base64 dan rasmni olish
                if "," in image_base64:
                    # "data:image/jpeg;base64,xxxx" formatdan tozalash
                    header, raw = image_base64.split(",", 1)
                    if not image_type and "image/" in header:
                        image_type = header.split(":")[1].split(";")[0]
                else:
                    raw = image_base64

                if not image_type:
                    image_type = "image/jpeg"

                try:
                    data = base64.b64decode(raw)
                except Exception as e:
                    print(f"[Telegram] Base64 xato: {e}")
                    return False

                ext = image_type.split("/")[-1] if "/" in image_type else "jpg"

                response = await client.post(
                    f"https://api.telegram.org/bot{token}/sendPhoto",
                    data={
                        "chat_id":    chat_id,
                        "caption":    message[:1024],  # Telegram limit
                        "parse_mode": "HTML",
                    },
                    files={"photo": (f"image.{ext}", data, image_type)},
                )
            else:
                response = await client.post(
                    f"https://api.telegram.org/bot{token}/sendMessage",
                    json={
                        "chat_id":    chat_id,
                        "text":       message[:4096],
                        "parse_mode": "HTML",
                    },
                )

            if response.status_code == 200:
                print("✅ Telegram: xabar yuborildi")
                return True
            else:
                print(f"❌ Telegram xato: {response.status_code} — {response.text}")
                return False

    except Exception as e:
        print(f"❌ Telegram exception: {e}")
        return False


async def send_telegram_dm(telegram_id: int, text: str) -> bool:
    """Bot orqali muayyan foydalanuvchiga (telegram_id) shaxsiy xabar yuborish.
    TELEGRAM_BOT_TOKEN ishlatadi (Mini App / Bot tokeni)."""
    if not settings.TELEGRAM_BOT_TOKEN or not telegram_id:
        return False
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(
                f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage",
                json={
                    "chat_id":    telegram_id,
                    "text":       text,
                    "parse_mode": "HTML",
                },
            )
            if r.status_code == 200:
                print(f"✅ Telegram DM → {telegram_id}")
                return True
            print(f"❌ Telegram DM → {telegram_id}: {r.status_code} {r.text[:200]}")
            return False
    except Exception as e:
        print(f"❌ Telegram DM exception ({telegram_id}): {e}")
        return False