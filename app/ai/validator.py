from __future__ import annotations


def validate_rewrite(text: str) -> tuple[bool, str]:
    words = text.split()
    if len(words) < 80:
        return False, "too_short"
    if len(words) > 350:
        return False, "too_long"
    required_hashtags = ("#авиация", "#происшествие", "#небонаграни", "#авиабезопасность")
    if any(tag not in text for tag in required_hashtags):
        return False, "missing_required_hashtags"
    if "✈️" not in text or "📍" not in text:
        return False, "missing_format_markers"
    return True, "ok"
