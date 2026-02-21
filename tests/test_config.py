from app.config import _parse_bool


def test_parse_bool_true_values(monkeypatch) -> None:
    monkeypatch.setenv("FLAG", "yes")
    assert _parse_bool("FLAG", False) is True


def test_parse_bool_default(monkeypatch) -> None:
    monkeypatch.delenv("FLAG", raising=False)
    assert _parse_bool("FLAG", True) is True
