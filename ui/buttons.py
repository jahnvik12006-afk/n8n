from ui.html_builder import build_inline_keyboard


def language_selector(slug: str, languages: list[str]) -> str:
    buttons = []
    for lang in languages:
        buttons.append([{"text": lang, "callback_data": f"lang:{slug}:{lang}"}])
    return build_inline_keyboard(buttons)


def upload_mode_selector(slug: str, language: str) -> str:
    return build_inline_keyboard([
        [{"text": "Single Upload", "callback_data": f"mode:single:{slug}:{language}"}],
        [{"text": "Multiple Upload", "callback_data": f"mode:multi:{slug}:{language}"}],
    ])


def channel_selector(slug: str, language: str, mode: str, channels: list[dict]) -> str:
    buttons = []
    for ch in channels:
        label = ch.get("name", ch.get("channel_id", ""))
        cb = f"channel:{slug}:{language}:{mode}:{ch.get('channel_id', '')}:{label}"
        buttons.append([{"text": label, "callback_data": cb}])
    return build_inline_keyboard(buttons)


def episode_selector(slug: str, language: str, total_episodes: int) -> str:
    from ui.theme import tag_code
    return ""  # Episodes handled via dialog flow, not inline buttons


def cancel_button(job_id: str) -> str:
    from ui.html_builder import build_button
    return build_button("Cancel", f"cancel:{job_id}")


def view_detail_buttons(slug: str) -> str:
    return build_inline_keyboard([
        [{"text": "View Episodes", "callback_data": f"view:{slug}"}],
    ])
