"""AI-powered extraction and enrichment using ScrapeGraphAI or OpenAI."""

from __future__ import annotations

import json
import logging
import time
from dataclasses import asdict
from typing import Any, Dict, List, Optional

import requests
from bs4 import BeautifulSoup
from openai import OpenAI
from pydantic import BaseModel, Field

from config import AppConfig
from extractor.schema import JobRecord

logger = logging.getLogger(__name__)


class ExtractedPayload(BaseModel):
    """Schema for extraction output expected from LLM."""

    title: str = ""
    company: str = ""
    location: str = ""
    salary: str = ""
    description: str = ""
    skills: List[str] = Field(default_factory=list)
    experience_level: str = ""
    remote: str = "Unknown"
    posted_date: str = ""


class AIExtractor:
    """Wraps extraction using ScrapeGraphAI first and OpenAI fallback."""

    def __init__(self, config: AppConfig):
        self.config = config
        self.client: Optional[OpenAI] = OpenAI(api_key=config.openai_api_key) if config.openai_api_key else None

    def extract_job(self, url: str, retries: int = 2) -> JobRecord:
        """Extract one job record with retry logic and graceful degradation."""
        for attempt in range(retries + 1):
            try:
                payload = self._try_scrapegraph(url) or self._try_openai(url)
                if payload:
                    return self._to_record(payload, url)
            except Exception as exc:
                logger.warning("Extraction attempt %s failed for %s: %s", attempt + 1, url, exc)
            time.sleep(1.0 + attempt)

        logger.error("Failed extraction for URL after retries: %s", url)
        return JobRecord(url=url, source=self._detect_source(url), title="Extraction failed")

    def _try_scrapegraph(self, url: str) -> Optional[Dict[str, Any]]:
        """Use ScrapeGraphAI Extract API when available."""
        if not self.config.scrapegraph_api_key:
            return None

        try:
            from scrapegraph_py import ExtractRequest, ScrapeGraphAI
        except ImportError:
            logger.info("scrapegraph_py not installed; skipping ScrapeGraphAI")
            return None

        sgai = ScrapeGraphAI(api_key=self.config.scrapegraph_api_key)
        result = sgai.extract(
            ExtractRequest(
                url=url,
                prompt=(
                    "Extract structured job information including title, company, "
                    "location, salary, job_description, required_skills, "
                    "experience_level, remote_or_onsite, and posted_date. "
                    "Return strict JSON keys: title, company, location, salary, "
                    "description, skills, experience_level, remote, posted_date"
                ),
            )
        )

        # Compatible handling for dict/object outputs.
        if isinstance(result, dict):
            return result
        if hasattr(result, "dict"):
            return result.dict()
        if hasattr(result, "model_dump"):
            return result.model_dump()
        return json.loads(str(result))

    def _try_openai(self, url: str) -> Optional[Dict[str, Any]]:
        """Fallback extraction with OpenAI from fetched HTML text."""
        if not self.client:
            return None

        text = self._fetch_page_text(url)
        if not text:
            return None

        prompt = (
            "Extract structured job information including title, company, location, salary, "
            "skills, seniority and work mode from the content below. "
            "Return valid JSON with keys: title, company, location, salary, description, "
            "skills (array), experience_level, remote, posted_date."
        )

        response = self.client.responses.parse(
            model=self.config.openai_model,
            input=[
                {"role": "system", "content": "You are an expert information extraction model."},
                {"role": "user", "content": f"{prompt}\n\nURL: {url}\n\nCONTENT:\n{text[:12000]}"},
            ],
            text_format=ExtractedPayload,
        )
        parsed = response.output_parsed
        if isinstance(parsed, BaseModel):
            return parsed.model_dump()
        if isinstance(parsed, dict):
            return parsed
        return None

    @staticmethod
    def _fetch_page_text(url: str) -> str:
        """Fetch URL and convert HTML to compact text."""
        try:
            resp = requests.get(url, timeout=20, headers={"User-Agent": "Mozilla/5.0"})
            resp.raise_for_status()
            soup = BeautifulSoup(resp.text, "html.parser")
            for script in soup(["script", "style", "noscript"]):
                script.extract()
            text = " ".join(soup.stripped_strings)
            return text[:40000]
        except Exception:
            return ""

    @staticmethod
    def _detect_source(url: str) -> str:
        """Infer source provider from URL."""
        for source in ["linkedin", "indeed", "glassdoor", "lever", "greenhouse", "workday"]:
            if source in url.lower():
                return source
        return "other"

    def _to_record(self, payload: Dict[str, Any], url: str) -> JobRecord:
        data = ExtractedPayload.model_validate(payload)
        return JobRecord(
            title=data.title,
            company=data.company,
            location=data.location,
            salary=data.salary,
            description=data.description,
            skills=data.skills,
            experience_level=data.experience_level,
            remote=data.remote,
            posted_date=data.posted_date,
            url=url,
            source=self._detect_source(url),
        )

    def enrich_record(self, record: JobRecord, profile_text: str) -> JobRecord:
        """Add seniority, skill tags, and relevance score."""
        if not self.client:
            record.seniority = _heuristic_seniority(record)
            record.relevance_score = _heuristic_score(record, profile_text)
            return record

        prompt = (
            "Given a job and candidate profile, return JSON with keys: "
            "seniority (Junior/Mid/Senior), skills (array enriched), relevance_score (1-10)."
        )
        resp = self.client.responses.create(
            model=self.config.openai_model,
            input=[
                {"role": "system", "content": "You rank jobs for candidates."},
                {
                    "role": "user",
                    "content": f"{prompt}\nPROFILE:\n{profile_text}\nJOB:\n{json.dumps(asdict(record), ensure_ascii=False)}",
                },
            ],
        )
        text = resp.output_text
        try:
            parsed = json.loads(text)
            record.seniority = parsed.get("seniority", _heuristic_seniority(record))
            record.skills = parsed.get("skills", record.skills)
            record.relevance_score = float(parsed.get("relevance_score", _heuristic_score(record, profile_text)))
        except Exception:
            record.seniority = _heuristic_seniority(record)
            record.relevance_score = _heuristic_score(record, profile_text)
        return record


def _heuristic_seniority(record: JobRecord) -> str:
    text = f"{record.title} {record.experience_level}".lower()
    if any(x in text for x in ["junior", "entry", "graduate", "intern"]):
        return "Junior"
    if any(x in text for x in ["senior", "staff", "principal", "lead", "head"]):
        return "Senior"
    return "Mid"


def _heuristic_score(record: JobRecord, profile_text: str) -> float:
    profile = profile_text.lower()
    tokens = [record.title, record.description, " ".join(record.skills)]
    haystack = " ".join(tokens).lower()
    score = 1.0
    for kw in ["python", "machine learning", "llm", "pytorch", "data", "nlp"]:
        if kw in haystack and kw in profile:
            score += 1.5
    if "remote" in (record.remote or "").lower():
        score += 1
    return min(10.0, round(score, 2))
