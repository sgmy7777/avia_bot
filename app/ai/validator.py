from __future__ import annotations


def validate_rewrite(text: str) -> tuple[bool, str]:
    words = text.split()
    if len(words) < 150:
        return False, "too_short"
    if len(words) > 300:
        return False, "too_long"
    if "#авиация" not in text or "#происшествие" not in text:
        return False, "missing_required_hashtags"
    if "Источник" not in text and "source" not in text.lower():
        return False, "missing_source"
    return True, "ok"
