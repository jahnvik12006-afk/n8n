from fastapi import APIRouter
from app.report_engine import generate_report
from app.config import TELEGRAM_ADMIN_ID
import app.main as main_module

router = APIRouter(tags=["reports"])


@router.get("/reports")
async def trigger_report():
    """No auth — for external cron triggers."""
    report = await generate_report()
    try:
        if main_module._tg_app:
            await main_module._tg_app.bot.send_message(chat_id=TELEGRAM_ADMIN_ID, text=report)
    except Exception:
        pass
    return {"success": True}
