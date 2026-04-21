from fastapi import APIRouter, BackgroundTasks
from pydantic import BaseModel
from ..utils.telegram import send_telegram

router = APIRouter()


class ContactMessage(BaseModel):
    name:    str
    phone:   str
    message: str


async def notify_contact(data: ContactMessage):
    """Background: aloqa xabarini Telegram'ga yuborish"""
    try:
        text = (
            "📩 <b>YANGI XABAR (Aloqa sahifasidan)</b>\n"
            "\n"
            f"👤 <b>Ism:</b> {data.name}\n"
            f"📞 <b>Telefon:</b> <code>{data.phone}</code>\n"
            "\n"
            f"💬 <b>Xabar:</b>\n{data.message}\n"
        )
        await send_telegram(text)
    except Exception as e:
        print(f"❌ Contact telegram xato: {e}")


@router.post("/")
async def send_contact(data: ContactMessage, background_tasks: BackgroundTasks):
    """Aloqa formasidan yuborilgan xabarni qabul qilish"""
    # Validatsiya
    if not data.name.strip():
        return {"success": False, "error": "Ism majburiy"}
    if not data.phone.strip():
        return {"success": False, "error": "Telefon majburiy"}
    if not data.message.strip():
        return {"success": False, "error": "Xabar matnini kiriting"}

    # Background'da Telegram'ga yuborish
    background_tasks.add_task(notify_contact, data)

    return {"success": True}