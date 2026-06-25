import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from app.database import init_db, cleanup_old_memory
from app.routers import analyze, update, reports
from app.telegram_bot import build_application

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

scheduler = AsyncIOScheduler()
_tg_app = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global _tg_app
    await init_db()

    # Memory cleanup every hour
    scheduler.add_job(cleanup_old_memory, "interval", hours=1)
    scheduler.start()

    # Start Telegram bot
    _tg_app = build_application()
    await _tg_app.initialize()
    await _tg_app.start()
    await _tg_app.updater.start_polling()

    logger.info("HisuClaw started")
    yield

    await _tg_app.updater.stop()
    await _tg_app.stop()
    await _tg_app.shutdown()
    scheduler.shutdown()


app = FastAPI(title="HisuClaw", version="2.0", lifespan=lifespan)

app.include_router(analyze.router)
app.include_router(update.router)
app.include_router(reports.router)


@app.get("/health")
async def health():
    return {"status": "ok"}
