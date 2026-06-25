import os
import aiosqlite
import asyncio
from datetime import datetime, timedelta
from app.config import MEMORY_RETENTION_HOURS

DB_PATH = os.environ.get("DB_PATH", "/data/hisuclaw.db" if os.path.isdir("/data") else "hisuclaw.db")

CREATE_TABLES = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    telegram_id INTEGER UNIQUE NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    content TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS tool_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tool_name TEXT NOT NULL,
    input TEXT,
    output TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS execution_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    action TEXT NOT NULL,
    video_id TEXT,
    field TEXT,
    old_value TEXT,
    new_value TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS memory (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    key TEXT NOT NULL,
    value TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS competitors (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    channel_id TEXT NOT NULL,
    data TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS video_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT UNIQUE NOT NULL,
    data TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
CREATE TABLE IF NOT EXISTS channel_cache (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    data TEXT NOT NULL,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""


async def init_db():
    async with aiosqlite.connect(DB_PATH) as db:
        for stmt in CREATE_TABLES.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                await db.execute(stmt)
        await db.commit()


async def cleanup_old_memory():
    cutoff = datetime.utcnow() - timedelta(hours=MEMORY_RETENTION_HOURS)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM memory WHERE created_at < ?", (cutoff,))
        await db.execute("DELETE FROM reports WHERE created_at < ?", (cutoff,))
        await db.commit()


async def save_memory(key: str, value: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO memory (key, value) VALUES (?, ?)", (key, value))
        await db.commit()


async def get_recent_memory(limit: int = 20) -> list[dict]:
    cutoff = datetime.utcnow() - timedelta(hours=MEMORY_RETENTION_HOURS)
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute(
            "SELECT key, value, created_at FROM memory WHERE created_at >= ? ORDER BY created_at DESC LIMIT ?",
            (cutoff, limit),
        ) as cursor:
            rows = await cursor.fetchall()
    return [{"key": r[0], "value": r[1], "created_at": r[2]} for r in rows]


async def log_tool(tool_name: str, input_data: str, output_data: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO tool_logs (tool_name, input, output) VALUES (?, ?, ?)",
            (tool_name, input_data, output_data),
        )
        await db.commit()


async def log_execution(action: str, video_id: str, field: str, old_val: str, new_val: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT INTO execution_logs (action, video_id, field, old_value, new_value) VALUES (?, ?, ?, ?, ?)",
            (action, video_id, field, old_val, new_val),
        )
        await db.commit()


async def save_report(content: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("INSERT INTO reports (content) VALUES (?)", (content,))
        await db.commit()


async def cache_channel(data: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM channel_cache")
        await db.execute("INSERT INTO channel_cache (data) VALUES (?)", (data,))
        await db.commit()


async def get_channel_cache() -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT data FROM channel_cache ORDER BY updated_at DESC LIMIT 1") as cur:
            row = await cur.fetchone()
    return row[0] if row else None


async def cache_video(video_id: str, data: str):
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "INSERT OR REPLACE INTO video_cache (video_id, data) VALUES (?, ?)",
            (video_id, data),
        )
        await db.commit()


async def get_video_cache(video_id: str) -> str | None:
    async with aiosqlite.connect(DB_PATH) as db:
        async with db.execute("SELECT data FROM video_cache WHERE video_id = ?", (video_id,)) as cur:
            row = await cur.fetchone()
    return row[0] if row else None
