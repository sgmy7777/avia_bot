import pytest

httpx = pytest.importorskip("httpx")

from app.ai.deepseek_client import DeepSeekClient
from app.domain.models import Incident


class _DummyResponse:
    def __init__(self, status_code: int, payload: dict | None = None) -> None:
        self.status_code = status_code
        self._payload = payload or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise httpx.HTTPStatusError(
                message=f"status={self.status_code}",
                request=httpx.Request("POST", "https://api.deepseek.com/chat/completions"),
                response=httpx.Response(self.status_code),
            )

    def json(self) -> dict:
        return self._payload


class _DummyClient:
    def __init__(self, response: _DummyResponse) -> None:
        self._response = response

    def __enter__(self) -> "_DummyClient":
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        return None

    def post(self, url: str, headers: dict, json: dict) -> _DummyResponse:  # noqa: A002
        return self._response


def _incident() -> Incident:
    return Incident(
        incident_id="abc",
        title="Test incident",
        event_type="incident",
        date_utc="2026-01-01",
        location="Cairo",
        aircraft="Airbus A320",
        operator="Air Test",
        persons_onboard="150",
        summary="Engine issue",
        source_url="https://aviation-safety.net/database/record.php?id=1",
    )


def test_rewrite_uses_fallback_on_402(monkeypatch) -> None:
    monkeypatch.setattr(httpx, "Client", lambda timeout: _DummyClient(_DummyResponse(402)))
    client = DeepSeekClient("key", "deepseek-chat")

    text = client.rewrite_incident(_incident())

    assert "Источник:" in text
    assert "#авиация #происшествие" in text
    assert "✈️" in text
    assert "📍" in text


def test_rewrite_uses_api_when_success(monkeypatch) -> None:
    payload = {"choices": [{"message": {"content": "ok rewrite"}}]}
    monkeypatch.setattr(httpx, "Client", lambda timeout: _DummyClient(_DummyResponse(200, payload)))
    client = DeepSeekClient("key", "deepseek-chat")

    text = client.rewrite_incident(_incident())

    assert text == "ok rewrite"
