from __future__ import annotations

import logging

from bs4 import BeautifulSoup
import httpx

logger = logging.getLogger(__name__)


class AviationSafetyCollector:
    def __init__(self, user_agent: str, feed_urls: list[str]) -> None:
        self._headers = {"User-Agent": user_agent}
        self._feed_urls = feed_urls

    def fetch_recent_incidents(self) -> list[dict[str, str]]:
        errors: list[str] = []
        had_success_response = False

        with httpx.Client(headers=self._headers, timeout=20.0, follow_redirects=True) as client:
            for url in self._feed_urls:
                try:
                    response = client.get(url)
                    response.raise_for_status()
                    had_success_response = True

                    incidents = self._parse_source(response.text)
                    if incidents:
                        logger.info("collector fetched %d rows from %s", len(incidents), url)
                        return incidents

                    errors.append(f"{url}: parsed 0 incidents")
                except Exception as exc:  # noqa: BLE001
                    errors.append(f"{url}: {exc}")

        if had_success_response:
            logger.warning("ASN source returned no parseable incidents. %s", " | ".join(errors))
            return []

        raise RuntimeError("ASN source unavailable. " + " | ".join(errors))

    def _parse_source(self, body: str) -> list[dict[str, str]]:
        payload = body.lstrip()
        if payload.startswith("<?xml") or "<rss" in payload[:300].lower():
            return self._parse_rss(payload)

        return self._parse_incident_table(payload)

    def _parse_rss(self, xml_text: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(xml_text, "xml")
        incidents: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        for item in soup.find_all("item"):
            link_node = item.find("link")
            title_node = item.find("title")
            date_node = item.find("pubDate")

            link = (link_node.get_text(strip=True) if link_node else "").strip()
            title = " ".join((title_node.get_text(" ", strip=True) if title_node else "").split())
            pub_date = " ".join((date_node.get_text(" ", strip=True) if date_node else "").split())

            if not link or not title:
                continue
            if link in seen_urls:
                continue
            seen_urls.add(link)

            incidents.append(
                {
                    "title": title,
                    "event_type": "incident",
                    "date_utc": pub_date,
                    "location": "",
                    "aircraft": "",
                    "operator": "",
                    "persons_onboard": "",
                    "summary": title,
                    "source_url": link,
                }
            )

        return incidents

    def _parse_incident_table(self, html: str) -> list[dict[str, str]]:
        soup = BeautifulSoup(html, "lxml")

        incidents = self._parse_table_rows(soup)
        if incidents:
            return incidents

        return self._parse_incident_links(soup)

    def _parse_table_rows(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        incidents: list[dict[str, str]] = []
        rows = soup.select("table.hp tr") or soup.select("table.list tr") or soup.select("table tr")

        for row in rows:
            cols = row.find_all("td")
            if len(cols) < 4:
                continue

            anchor = row.find("a", href=True)
            if not anchor:
                continue

            href = anchor.get("href", "")
            source_url = href if href.startswith("http") else f"https://aviation-safety.net/{href.lstrip('/')}"

            title = " ".join(cols[3].get_text(" ", strip=True).split())
            date_text = cols[0].get_text(" ", strip=True)
            location = cols[1].get_text(" ", strip=True)
            aircraft = cols[2].get_text(" ", strip=True)

            if not any([title, date_text, location, aircraft]):
                continue

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

    def _parse_incident_links(self, soup: BeautifulSoup) -> list[dict[str, str]]:
        incidents: list[dict[str, str]] = []
        seen_urls: set[str] = set()

        for anchor in soup.find_all("a", href=True):
            href = anchor.get("href", "")
            if not self._is_incident_link(href):
                continue

            source_url = href if href.startswith("http") else f"https://aviation-safety.net/{href.lstrip('/')}"
            if source_url in seen_urls:
                continue
            seen_urls.add(source_url)

            title = " ".join(anchor.get_text(" ", strip=True).split())
            if not title:
                continue

            incidents.append(
                {
                    "title": title,
                    "event_type": "incident",
                    "date_utc": "",
                    "location": "",
                    "aircraft": "",
                    "operator": "",
                    "persons_onboard": "",
                    "summary": title,
                    "source_url": source_url,
                }
            )

        return incidents

    @staticmethod
    def _is_incident_link(href: str) -> bool:
        lowered = href.lower()
        return (
            "/wikibase/" in lowered
            or "/database/record.php" in lowered
            or "/database/db" in lowered
            or "/asndb/" in lowered
        )
