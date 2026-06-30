import json


def build_inline_keyboard(buttons: list[list[dict]]) -> str:
    return json.dumps({"inline_keyboard": buttons})


def build_button(text: str, callback_data: str) -> str:
    return build_inline_keyboard([[[
        {"text": text, "callback_data": callback_data},
    ]]])
