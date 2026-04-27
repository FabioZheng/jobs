"""Typed schema objects for extracted job records."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class JobRecord:
    """Canonical structure for one job post in the pipeline."""

    title: str = ""
    company: str = ""
    location: str = ""
    salary: str = ""
    salary_min: Optional[float] = None
    salary_max: Optional[float] = None
    currency: str = ""
    description: str = ""
    skills: List[str] = field(default_factory=list)
    experience_level: str = ""
    seniority: str = ""
    remote: str = "Unknown"
    posted_date: str = ""
    relevance_score: float = 0.0
    url: str = ""
    source: str = ""
    extracted_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())

    def to_dict(self) -> Dict[str, Any]:
        """Convert dataclass to serializable dictionary."""
        return asdict(self)


OUTPUT_COLUMNS = [
    "title",
    "company",
    "location",
    "salary",
    "skills",
    "seniority",
    "remote",
    "relevance_score",
    "url",
]
