"""Enrichment orchestration layer."""

from __future__ import annotations

from typing import Iterable, List

from extractor.ai_extractor import AIExtractor
from extractor.schema import JobRecord


def enrich_records(records: Iterable[JobRecord], extractor: AIExtractor, profile_text: str) -> List[JobRecord]:
    """Apply AI/heuristic enrichment to all records."""
    return [extractor.enrich_record(record, profile_text=profile_text) for record in records]
