"""Data normalization utilities."""

from __future__ import annotations

import re
from datetime import datetime
from typing import Iterable, List

from dateutil import parser as date_parser

from extractor.schema import JobRecord


def normalize_salary(record: JobRecord) -> JobRecord:
    """Extract salary range as numeric values when present."""
    text = (record.salary or "").replace(",", "")
    matches = re.findall(r"(?:\$|€|£)?\s?(\d{2,6})", text)
    if matches:
        nums = [float(x) for x in matches]
        record.salary_min = min(nums)
        record.salary_max = max(nums)
    return record


def normalize_location(record: JobRecord) -> JobRecord:
    """Standardize location formatting."""
    value = (record.location or "").strip()
    value = re.sub(r"\s+", " ", value)
    record.location = value.title()
    return record


def normalize_date(record: JobRecord) -> JobRecord:
    """Normalize date to ISO format when parseable."""
    if not record.posted_date:
        return record
    try:
        dt = date_parser.parse(record.posted_date)
        record.posted_date = dt.date().isoformat()
    except Exception:
        try:
            record.posted_date = datetime.fromisoformat(record.posted_date).date().isoformat()
        except Exception:
            pass
    return record


def deduplicate(records: Iterable[JobRecord]) -> List[JobRecord]:
    """Drop duplicates by URL preserving original order."""
    seen = set()
    output: List[JobRecord] = []
    for row in records:
        if row.url in seen:
            continue
        seen.add(row.url)
        output.append(row)
    return output


def clean_records(records: Iterable[JobRecord]) -> List[JobRecord]:
    """Apply full cleaning chain."""
    cleaned = []
    for record in records:
        record = normalize_salary(record)
        record = normalize_location(record)
        record = normalize_date(record)
        cleaned.append(record)
    return deduplicate(cleaned)
