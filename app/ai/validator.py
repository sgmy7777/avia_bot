from __future__ import annotations


def validate_rewrite(text: str) -> tuple[bool, str]:
    words = text.split()
    if len(words) < 80:
        return False, "too_short"
    if len(words) > 350:
        return False, "too_long"
    if "#авиация" not in text or "#происшествие" not in text:
        return False, "missing_required_hashtags"
    if "Источник" not in text and "source" not in text.lower():
        return False, "missing_source"
    if "✈️" not in text or "📍" not in text:
        return False, "missing_format_markers"
    return True, "ok"
