"""Job filtering logic for relevance constraints."""

from __future__ import annotations

from typing import Iterable, List

from config import AppConfig
from extractor.schema import JobRecord


def _contains_keywords(text: str, keywords: List[str]) -> bool:
    lowered = text.lower()
    return any(kw.lower() in lowered for kw in keywords)


def filter_relevant_jobs(records: Iterable[JobRecord], config: AppConfig) -> List[JobRecord]:
    """Filter records by role relevance, seniority exclusions, and location preference."""
    kept: List[JobRecord] = []
    for record in records:
        searchable = f"{record.title} {record.description} {' '.join(record.skills)}"
        if not _contains_keywords(searchable, config.role_keywords):
            continue

        senior_text = f"{record.seniority} {record.experience_level} {record.title}".lower()
        if any(tag in senior_text for tag in config.exclude_seniority):
            continue

        location_text = f"{record.location} {record.remote}".lower()
        if not any(region.lower() in location_text for region in config.allowed_regions):
            continue

        kept.append(record)
    return kept
