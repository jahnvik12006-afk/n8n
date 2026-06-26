"""Local SEO engine — CTR scoring, title patterns, tag generation. No external APIs."""
import re
from typing import List

# Proven CTR boosters for Hindi audience
EMOTIONAL_TRIGGERS = [
    "shocking", "revealed", "secret", "untold", "truth", "real reason",
    "nobody told you", "dark secret", "insane", "overpowered",
]
HINDI_HOOKS = [
    "😱", "🔥", "💀", "⚡", "👑", "🗡️",
]
POWER_WORDS = [
    "most powerful", "strongest", "weakest", "betrayal", "return",
    "final form", "true identity", "hidden power", "shocking twist",
    "never seen before",
]
# Title structures that work for Manhwa recap channels
TITLE_PATTERNS = [
    "{trigger} {topic} - {power_word}! {emoji}",
    "{topic} ka {trigger} - {power_word} {emoji}",
    "{power_word} {topic} | Hindi Recap {emoji}",
    "{topic} - Jab {power_word} hua | {trigger} {emoji}",
    "क्या {topic} का {trigger} सच में हुआ? {emoji}",
]


def score_title(title: str) -> dict:
    """Score a title 0-100 with breakdown."""
    score = 0
    reasons = []

    length = len(title)
    if 40 <= length <= 70:
        score += 25
        reasons.append("ʟᴇɴɢᴛʜ OK")
    elif length < 40:
        reasons.append(f"! ᴛᴏᴏ sʜᴏʀᴛ ({length})")
    else:
        reasons.append(f"! ᴛᴏᴏ ʟᴏɴɢ ({length})")

    title_lower = title.lower()
    has_trigger = any(t in title_lower for t in EMOTIONAL_TRIGGERS)
    has_power = any(p in title_lower for p in POWER_WORDS)
    emoji_count = len(re.findall(r'[\U00010000-\U0010ffff\U00002600-\U000027ff]', title))

    if has_trigger:
        score += 20
        reasons.append("ᴇᴍᴏᴛɪᴏɴᴀʟ ᴛʀɪɢɢᴇʀ ✓")
    if has_power:
        score += 20
        reasons.append("ᴘᴏᴡᴇʀ ᴡᴏʀᴅ ✓")
    if 1 <= emoji_count <= 3:
        score += 15
        reasons.append("ᴇᴍᴏᴊɪ ✓")
    elif emoji_count == 0:
        reasons.append("! ɴᴏ ᴇᴍᴏᴊɪ")

    # Number in title boosts CTR
    if re.search(r'\d+', title):
        score += 10
        reasons.append("ɴᴜᴍʙᴇʀ ✓")

    # Question mark = curiosity gap
    if "?" in title:
        score += 10
        reasons.append("ǫᴜᴇsᴛɪᴏɴ ✓")

    return {"score": min(score, 100), "reasons": reasons}


def score_description(desc: str) -> dict:
    score = 0
    reasons = []
    length = len(desc)

    if length >= 500:
        score += 30
        reasons.append("ʟᴇɴɢᴛʜ OK")
    else:
        reasons.append(f"! ᴛᴏᴏ sʜᴏʀᴛ ({length})")

    if re.search(r'subscribe|bell|notification', desc, re.I):
        score += 20
        reasons.append("ᴄᴛᴀ ✓")
    if "#" in desc:
        score += 20
        reasons.append("ʜᴀsʜᴛᴀɢs ✓")
    if "http" in desc or "link" in desc.lower():
        score += 15
        reasons.append("ʟɪɴᴋ ✓")
    if re.search(r'\d+:\d+', desc):
        score += 15
        reasons.append("ᴛɪᴍᴇsᴛᴀᴍᴘs ✓")

    return {"score": min(score, 100), "reasons": reasons}


def score_tags(tags: List[str]) -> dict:
    score = 0
    reasons = []
    n = len(tags)

    if n >= 15:
        score += 40
        reasons.append(f"{n} ᴛᴀɢs ✓")
    elif n >= 8:
        score += 20
        reasons.append(f"{n} ᴛᴀɢs (ɴᴇᴇᴅ 15+)")
    else:
        reasons.append(f"! ᴏɴʟʏ {n} ᴛᴀɢs")

    has_long = any(len(t.split()) >= 3 for t in tags)
    has_short = any(len(t.split()) == 1 for t in tags)
    if has_long:
        score += 30
        reasons.append("ʟᴏɴɢ-ᴛᴀɪʟ ᴛᴀɢs ✓")
    if has_short:
        score += 30
        reasons.append("sʜᴏʀᴛ ᴛᴀɢs ✓")

    return {"score": min(score, 100), "reasons": reasons}


def generate_tags_for_topic(topic: str, extra: List[str] = None) -> List[str]:
    """Generate 25 SEO tags without any API."""
    base = topic.lower().strip()
    words = base.split()

    tags = [base]
    tags += words
    tags += [f"{base} hindi", f"{base} recap", f"{base} in hindi",
             f"{base} manga", f"{base} manhwa", f"{base} explained",
             f"hindi {base}", f"{base} full story", f"{base} all episodes"]

    generic = [
        "manhwa hindi", "manga hindi recap", "manhwa recap hindi",
        "hindi manga", "manhwa explained", "manga explained hindi",
        "best manhwa", "top manhwa", "manhwa in hindi",
    ]
    tags += generic
    if extra:
        tags += extra

    # Deduplicate, limit to 30
    seen = set()
    out = []
    for t in tags:
        if t not in seen and len(t) >= 2:
            seen.add(t)
            out.append(t)
    return out[:30]


def full_seo_audit(title: str, description: str, tags: List[str]) -> dict:
    """Complete SEO audit returning scores + overall grade."""
    t = score_title(title)
    d = score_description(description)
    tg = score_tags(tags)
    overall = int(t["score"] * 0.4 + d["score"] * 0.35 + tg["score"] * 0.25)
    grade = "A" if overall >= 80 else "B" if overall >= 60 else "C" if overall >= 40 else "D"
    return {
        "overall": overall,
        "grade": grade,
        "title": t,
        "description": d,
        "tags": tg,
    }
