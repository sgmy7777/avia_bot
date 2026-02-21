import httpx

from app.publisher.telegram_client import TelegramPublisher


class _DummyResponse:
    def __init__(self, status_code: int, json_data: dict | None = None, text: str = "") -> None:
        self.status_code = status_code
        self._json_data = json_data
        self.text = text

    @property
    def is_success(self) -> bool:
        return 200 <= self.status_code < 300

    def json(self) -> dict:
        if self._json_data is None:
            raise ValueError("no json")
        return self._json_data


class _DummyClient:
    def __init__(self, response: _DummyResponse) -> None:
        self._response = response

    def __enter__(self) -> "_DummyClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url: str, json: dict) -> _DummyResponse:  # noqa: A002
        return self._response


def test_publish_raises_clear_error(monkeypatch) -> None:
    response = _DummyResponse(
        400,
        json_data={"ok": False, "description": "Bad Request: chat not found"},
    )
    monkeypatch.setattr(httpx, "Client", lambda timeout: _DummyClient(response))

    publisher = TelegramPublisher("token", "@bad_channel")

    try:
        publisher.publish("test")
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        message = str(exc)

    assert "status=400" in message
    assert "chat not found" in message


def test_publish_requires_channel() -> None:
    publisher = TelegramPublisher("token", "")

    try:
        publisher.publish("test")
        assert False, "Expected RuntimeError"
    except RuntimeError as exc:
        assert "TELEGRAM_CHANNEL is empty" in str(exc)
