import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import init_db, cleanup_old_memory
from app.routers import analyze, update, reports
from app.telegram_bot import build_application
from app.config import PORT
import os

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_tg_app = None

WEBHOOK_URL = os.getenv("WEBHOOK_URL", os.getenv("RENDER_EXTERNAL_URL", "")).rstrip("/")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tg_app
    await init_db()

    scheduler.add_job(cleanup_old_memory, "interval", hours=1)
    scheduler.start()

    _tg_app = build_application()
    await _tg_app.initialize()
    await _tg_app.start()

    if WEBHOOK_URL:
        webhook = f"{WEBHOOK_URL}/webhook"
        await _tg_app.bot.set_webhook(webhook, drop_pending_updates=False)
        logger.info(f"Webhook set: {webhook}")
    else:
        # Local: polling mode
        if _tg_app.updater:
            await _tg_app.updater.start_polling()
        logger.info("Polling started (local mode)")

    logger.info("HisuClaw started")
    yield

    if _tg_app.updater:
        await _tg_app.updater.stop()

    await _tg_app.stop()
    await _tg_app.shutdown()
    scheduler.shutdown()


app = FastAPI(title="HisuClaw", version="2.0", lifespan=lifespan)

app.include_router(analyze.router)
app.include_router(update.router)
app.include_router(reports.router)


@app.post("/webhook")
async def telegram_webhook(request: Request):
    data = await request.json()
    from telegram import Update
    update_obj = Update.de_json(data, _tg_app.bot)
    await _tg_app.process_update(update_obj)
    return {"ok": True}


@app.get("/health")
async def health():
    return {"status": "ok"}
