from app.collector.aviation_safety import AviationSafetyCollector


def test_parse_incident_table_extracts_rows() -> None:
    html = """
    <html><body>
      <table class="hp">
        <tr><th>D</th><th>L</th><th>A</th><th>T</th></tr>
        <tr>
          <td>2026-01-15</td>
          <td>Cairo</td>
          <td>Airbus A320-200</td>
          <td><a href="/wikibase/123">Engine issue after takeoff</a></td>
        </tr>
      </table>
    </body></html>
    """

    collector = AviationSafetyCollector("test-agent", ["https://example.com"])
    items = collector._parse_source(html)

    assert len(items) == 1
    assert items[0]["aircraft"] == "Airbus A320-200"
    assert items[0]["location"] == "Cairo"
    assert items[0]["source_url"] == "https://aviation-safety.net/wikibase/123"


def test_parse_incident_table_fallback_to_incident_links() -> None:
    html = """
    <html><body>
      <div>
        <a href="/database/record.php?id=20260115-0">Boeing 737 incident near Oslo</a>
      </div>
    </body></html>
    """

    collector = AviationSafetyCollector("test-agent", ["https://example.com"])
    items = collector._parse_source(html)

    assert len(items) == 1
    assert items[0]["title"] == "Boeing 737 incident near Oslo"
    assert items[0]["source_url"] == "https://aviation-safety.net/database/record.php?id=20260115-0"


def test_parse_incident_links_deduplicates_urls() -> None:
    html = """
    <html><body>
      <a href="/wikibase/999">First title</a>
      <a href="/wikibase/999">Second title duplicate link</a>
    </body></html>
    """

    collector = AviationSafetyCollector("test-agent", ["https://example.com"])
    items = collector._parse_source(html)

    assert len(items) == 1
    assert items[0]["source_url"] == "https://aviation-safety.net/wikibase/999"


def test_parse_rss_items() -> None:
    xml = """<?xml version="1.0" encoding="UTF-8"?>
    <rss><channel>
      <item>
        <title>Airbus A320 incident near Cairo</title>
        <link>https://aviation-safety.net/database/record.php?id=20260115-0</link>
        <pubDate>Sat, 15 Jan 2026 12:00:00 GMT</pubDate>
      </item>
    </channel></rss>
    """

    collector = AviationSafetyCollector("test-agent", ["https://example.com"])
    items = collector._parse_source(xml)

    assert len(items) == 1
    assert items[0]["title"] == "Airbus A320 incident near Cairo"
    assert items[0]["source_url"] == "https://aviation-safety.net/database/record.php?id=20260115-0"
    assert items[0]["date_utc"] == "Sat, 15 Jan 2026 12:00:00 GMT"
