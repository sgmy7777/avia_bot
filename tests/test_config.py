from app.config import _parse_bool, _parse_csv


def test_parse_bool_true_values(monkeypatch) -> None:
    monkeypatch.setenv("FLAG", "yes")
    assert _parse_bool("FLAG", False) is True


def test_parse_bool_default(monkeypatch) -> None:
    monkeypatch.delenv("FLAG", raising=False)
    assert _parse_bool("FLAG", True) is True


def test_parse_csv(monkeypatch) -> None:
    monkeypatch.setenv("CSV", "a, b, ,c")
    assert _parse_csv("CSV", "x") == ["a", "b", "c"]
