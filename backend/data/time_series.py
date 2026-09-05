from __future__ import annotations

import csv
import hashlib
import io
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Callable

from backend.domain.models import DataSnapshot, RunMode


Fetcher = Callable[[str], str]


def http_text(url: str, timeout: float = 20.0) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "one-person-fund/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8")


@dataclass(frozen=True)
class TimeSeriesPoint:
    series: str
    observation_date: date
    value: Decimal
    source_url: str
    source_available_at: datetime | None
    vintage: str | None = None


class FredGraphCsvSource:
    """Read FRED graph CSV. This source is not vintage-aware by itself."""

    def __init__(self, fetcher: Fetcher = http_text):
        self.fetcher = fetcher

    def fetch(self, series_id: str, start: date | None = None, end: date | None = None) -> list[TimeSeriesPoint]:
        url = f"https://fred.stlouisfed.org/graph/fredgraph.csv?id={series_id}"
        if start:
            url += f"&cosd={start.isoformat()}"
        if end:
            url += f"&coed={end.isoformat()}"
        rows = csv.DictReader(io.StringIO(self.fetcher(url)))
        result: list[TimeSeriesPoint] = []
        value_key = "value" if "value" in (rows.fieldnames or []) else series_id
        for row in rows:
            raw = (row.get(value_key) or "").strip()
            if not raw or raw == ".":
                continue
            result.append(TimeSeriesPoint(series=series_id, observation_date=date.fromisoformat(row["observation_date"]), value=Decimal(raw), source_url=url, source_available_at=None, vintage=None))
        return result


class TreasuryXmlSource:
    """Parse the Treasury daily par-yield XML without claiming trade prices."""

    def __init__(self, fetcher: Fetcher = http_text):
        self.fetcher = fetcher

    @staticmethod
    def _local(tag: str) -> str:
        return tag.rsplit("}", 1)[-1].split(":")[-1]

    def fetch_year(self, year: int) -> list[dict[str, str]]:
        url = f"https://home.treasury.gov/resource-center/data-chart-center/interest-rates/pages/xml?data=daily_treasury_yield_curve&field_tdr_date_value={year}"
        root = ET.fromstring(self.fetcher(url))
        records: list[dict[str, str]] = []
        for entry in root.iter():
            if self._local(entry.tag) != "entry":
                continue
            record: dict[str, str] = {}
            for child in entry.iter():
                key = self._local(child.tag)
                if child is entry or child.text is None:
                    continue
                if key in {"NEW_DATE", "BC_2YEAR", "BC_5YEAR", "BC_10YEAR", "BC_30YEAR"}:
                    record[key] = child.text.strip()
            if "NEW_DATE" in record and "BC_2YEAR" in record and "BC_10YEAR" in record:
                records.append(record)
        return records

    def snapshot(self, record: dict[str, str], available_at: datetime, mode: RunMode = RunMode.REPLAY) -> DataSnapshot:
        if available_at.tzinfo is None:
            raise ValueError("available_at must include a timezone")
        observed = date.fromisoformat(record["NEW_DATE"])
        y2 = Decimal(record["BC_2YEAR"])
        y10 = Decimal(record["BC_10YEAR"])
        records = {"2s10s_bp": (y10 - y2) * Decimal("100"), "DGS2": y2, "DGS10": y10}
        content_hash = hashlib.sha256("|".join(f"{key}={value}" for key, value in sorted(record.items())).encode()).hexdigest()[:16]
        return DataSnapshot(snapshot_id=f"treasury-{observed.isoformat()}", mode=mode, as_of=datetime(observed.year, observed.month, observed.day, tzinfo=timezone.utc), available_at=available_at, source="treasury.gov:daily_treasury_yield_curve", records=records, content_hash=content_hash)


def eligible(points: list[TimeSeriesPoint], as_of: datetime) -> list[TimeSeriesPoint]:
    """Return only points whose explicit availability is known and has passed."""
    if as_of.tzinfo is None:
        raise ValueError("as_of must include a timezone")
    return [point for point in points if point.source_available_at is not None and point.source_available_at <= as_of]
