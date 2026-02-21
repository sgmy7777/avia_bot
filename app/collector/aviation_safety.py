from __future__ import annotations

from bs4 import BeautifulSoup
import httpx

ASN_RECENT_URL = "https://aviation-safety.net/wikibase/dblist.php?Country=N"


class AviationSafetyCollector:
    def __init__(self, user_agent: str) -> None:
        self._headers = {"User-Agent": user_agent}

    def fetch_recent_incidents(self) -> list[dict[str, str]]:
        with httpx.Client(headers=self._headers, timeout=20.0, follow_redirects=True) as client:
            response = client.get(ASN_RECENT_URL)
            response.raise_for_status()

        return self._parse_incident_table(response.text)

    def _parse_incident_table(self, html: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(html, "lxml")
        rows = soup.select("table.hp tr")
        incidents: list[dict[str, str]] = []

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            anchor = row.find("a", href=True)
            source_url = ""
            if anchor:
                href = anchor.get("href", "")
                source_url = href if href.startswith("http") else f"https://aviation-safety.net/{href.lstrip('/')}"

            title = " ".join(cols[3].get_text(" ", strip=True).split())
            date_text = cols[0].get_text(" ", strip=True)
            location = cols[1].get_text(" ", strip=True)
            aircraft = cols[2].get_text(" ", strip=True)

            incidents.append(
                {
                    "title": title,
                    "event_type": "incident",
                    "date_utc": date_text,
                    "location": location,
                    "aircraft": aircraft,
                    "operator": "",
                    "persons_onboard": "",
                    "summary": title,
                    "source_url": source_url,
                }
            )

        return incidents
