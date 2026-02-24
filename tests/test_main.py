import pytest

pytest.importorskip("httpx")

from app.domain.models import Incident
from app.main import _merge_with_details


def test_merge_with_details_prefers_detail_values() -> None:
    incident = Incident(
        incident_id="i1",
        title="Old title",
        event_type="incident",
        date_utc="",
        location="",
        aircraft="",
        operator="",
        persons_onboard="",
        summary="short",
        source_url="https://x",
    )
    details = {
        "title": "New title",
        "date_utc": "2026-01-01",
        "location": "Cairo",
        "aircraft": "A320",
        "operator": "Air Test",
        "summary": "Long detailed text",
    }

    merged = _merge_with_details(incident, details)

    assert merged.title == "New title"
    assert merged.location == "Cairo"
    assert merged.summary == "Long detailed text"
