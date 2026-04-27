"""Export helpers for DataFrame and spreadsheet outputs."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import pandas as pd

from extractor.schema import JobRecord, OUTPUT_COLUMNS


DISPLAY_RENAME = {
    "title": "Title",
    "company": "Company",
    "location": "Location",
    "salary": "Salary",
    "skills": "Skills",
    "seniority": "Seniority",
    "remote": "Remote",
    "relevance_score": "Score",
    "url": "URL",
}


def to_dataframe(records: Iterable[JobRecord]) -> pd.DataFrame:
    """Convert records to DataFrame with user-facing columns."""
    rows = [r.to_dict() for r in records]
    df = pd.DataFrame(rows)
    if df.empty:
        df = pd.DataFrame(columns=OUTPUT_COLUMNS)
    else:
        df["skills"] = df["skills"].apply(lambda x: ", ".join(x) if isinstance(x, list) else x)
    df = df.reindex(columns=OUTPUT_COLUMNS)
    return df.rename(columns=DISPLAY_RENAME)


def save_outputs(df: pd.DataFrame, excel_path: Path, csv_path: Path) -> None:
    """Write Excel and CSV outputs."""
    df.to_excel(excel_path, index=False)
    df.to_csv(csv_path, index=False)


def save_raw_json(records: Iterable[JobRecord], path: Path) -> None:
    """Persist raw extracted records for debugging and audit."""
    path.write_text(json.dumps([r.to_dict() for r in records], indent=2, ensure_ascii=False))
