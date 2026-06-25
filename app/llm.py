import json
from groq import Groq
from app.config import GROQ_API_KEY, GROQ_BASE_URL, GROQ_MODELS

_client = Groq(api_key=GROQ_API_KEY, base_url=GROQ_BASE_URL)


def chat(system: str, user: str, model_index: int = 0) -> str:
    if model_index >= len(GROQ_MODELS):
        raise RuntimeError("All Groq models failed")
    try:
        response = _client.chat.completions.create(
            model=GROQ_MODELS[model_index],
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0.7,
            max_tokens=4096,
        )
        return response.choices[0].message.content
    except Exception:
        return chat(system, user, model_index + 1)
