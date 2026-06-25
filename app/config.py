import os
from dotenv import load_dotenv

load_dotenv()

YOUTUBE_CLIENT_ID = os.getenv("YOUTUBE_CLIENT_ID", "")
YOUTUBE_CLIENT_SECRET = os.getenv("YOUTUBE_CLIENT_SECRET", "")
YOUTUBE_REFRESH_TOKEN = os.getenv("YOUTUBE_REFRESH_TOKEN", "")
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_ADMIN_ID = int(os.getenv("TELEGRAM_ADMIN_ID", "0"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_BASE_URL = os.getenv("GROQ_BASE_URL", "https://api.groq.com/openai/v1")
AUTHORIZATION_TOKEN = os.getenv("AUTHORIZATION_TOKEN", "")
PORT = int(os.getenv("PORT", "8000"))
MEMORY_RETENTION_HOURS = int(os.getenv("MEMORY_RETENTION_HOURS", "24"))

GROQ_MODELS = [
    "deepseek-r1-distill-llama-70b",
    "qwen-qwq-32b",
    "llama-3.3-70b-versatile",
]
