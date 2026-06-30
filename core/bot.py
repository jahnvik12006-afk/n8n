from core.config import config
from core.http_client import HttpClient


class Bot:
    _instance = None

    def __init__(self):
        self.token = config.BOT_TOKEN
        self.api_base = f"https://api.telegram.org/bot{self.token}"

    @classmethod
    def get(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    async def request(self, method: str, json_data: dict | None = None) -> dict:
        client = HttpClient.get()
        url = f"{self.api_base}/{method}"
        resp = await client.post(url, json=json_data)
        resp.raise_for_status()
        return resp.json()

    async def send_message(self, chat_id: int | str, text: str, **kwargs) -> dict:
        return await self.request("sendMessage", {
            "chat_id": chat_id,
            "text": text,
            "parse_mode": "HTML",
            **kwargs,
        })

    async def edit_message_text(self, chat_id: int | str, message_id: int, text: str, **kwargs) -> dict:
        return await self.request("editMessageText", {
            "chat_id": chat_id,
            "message_id": message_id,
            "text": text,
            "parse_mode": "HTML",
            **kwargs,
        })

    async def answer_callback_query(self, callback_query_id: str, text: str | None = None, **kwargs) -> dict:
        return await self.request("answerCallbackQuery", {
            "callback_query_id": callback_query_id,
            "text": text,
            **kwargs,
        })

    async def send_photo(self, chat_id: int | str, photo: str, caption: str = "", **kwargs) -> dict:
        return await self.request("sendPhoto", {
            "chat_id": chat_id,
            "photo": photo,
            "caption": caption,
            "parse_mode": "HTML",
            **kwargs,
        })

    async def send_video(self, chat_id: int | str, video: str, caption: str = "", **kwargs) -> dict:
        return await self.request("sendVideo", {
            "chat_id": chat_id,
            "video": video,
            "caption": caption,
            "parse_mode": "HTML",
            **kwargs,
        })

    async def send_document(self, chat_id: int | str, document: str, caption: str = "", **kwargs) -> dict:
        return await self.request("sendDocument", {
            "chat_id": chat_id,
            "document": document,
            "caption": caption,
            "parse_mode": "HTML",
            **kwargs,
        })

    async def set_webhook(self, url: str, secret_token: str | None = None) -> dict:
        data = {"url": url}
        if secret_token:
            data["secret_token"] = secret_token
        return await self.request("setWebhook", data)

    async def delete_webhook(self) -> dict:
        return await self.request("deleteWebhook")

    async def get_webhook_info(self) -> dict:
        return await self.request("getWebhookInfo")
