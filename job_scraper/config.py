"""Application configuration for the AI job scraper project."""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import List

from dotenv import load_dotenv

load_dotenv()


@dataclass
class AppConfig:
    """Holds runtime configuration loaded from environment variables."""

    data_dir: Path = Path(__file__).resolve().parent / "data"
    output_excel: Path = field(default_factory=lambda: Path("jobs.xlsx"))
    output_csv: Path = field(default_factory=lambda: Path("jobs.csv"))
    raw_json_path: Path = field(default_factory=lambda: Path("jobs_raw.json"))

    openai_api_key: str = field(default_factory=lambda: os.getenv("OPENAI_API_KEY", ""))
    openai_model: str = field(default_factory=lambda: os.getenv("OPENAI_MODEL", "gpt-4.1-mini"))
    scrapegraph_api_key: str = field(default_factory=lambda: os.getenv("SCRAPEGRAPH_API_KEY", ""))

    # Crawler controls
    max_urls: int = field(default_factory=lambda: int(os.getenv("MAX_URLS", "100")))
    request_delay: float = field(default_factory=lambda: float(os.getenv("REQUEST_DELAY", "0.4")))
    timeout_seconds: int = field(default_factory=lambda: int(os.getenv("TIMEOUT_SECONDS", "30")))
    use_playwright: bool = field(default_factory=lambda: os.getenv("USE_PLAYWRIGHT", "false").lower() == "true")

    # Filtering controls
    allowed_regions: List[str] = field(
        default_factory=lambda: [x.strip() for x in os.getenv("ALLOWED_REGIONS", "europe,remote").split(",") if x.strip()]
    )
    role_keywords: List[str] = field(
        default_factory=lambda: [x.strip() for x in os.getenv("ROLE_KEYWORDS", "ml,ai,data,machine learning").split(",") if x.strip()]
    )
    exclude_seniority: List[str] = field(
        default_factory=lambda: [x.strip().lower() for x in os.getenv("EXCLUDE_SENIORITY", "staff,principal,lead,head").split(",") if x.strip()]
    )

    def resolved_paths(self) -> "AppConfig":
        """Resolve output files into the data directory and ensure directory exists."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.output_excel = self.data_dir / self.output_excel
        self.output_csv = self.data_dir / self.output_csv
        self.raw_json_path = self.data_dir / self.raw_json_path
        return self


DEFAULT_SEARCH_DOMAINS = [
    "linkedin.com/jobs",
    "indeed.com/viewjob",
    "glassdoor.com/job-listing",
    "lever.co",
    "greenhouse.io",
    "workdayjobs.com",
]
