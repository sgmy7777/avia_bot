from app.ai.validator import validate_rewrite


def test_validate_rewrite_success() -> None:
    body = " ".join(["слово"] * 170)
    text = f"{body}\nИсточник: https://example.com\n#авиация #происшествие"
    ok, reason = validate_rewrite(text)
    assert ok is True
    assert reason == "ok"


def test_validate_rewrite_too_short() -> None:
    text = "короткий текст\nИсточник: x\n#авиация #происшествие"
    ok, reason = validate_rewrite(text)
    assert ok is False
    assert reason == "too_short"
