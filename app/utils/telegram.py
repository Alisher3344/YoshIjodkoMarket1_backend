import base64
import httpx
from ..core.config import settings


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