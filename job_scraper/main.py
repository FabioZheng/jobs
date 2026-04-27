"""Entry point for the AI job scraper pipeline."""

from __future__ import annotations

import argparse
import logging
from datetime import datetime
from pathlib import Path
from typing import List

from tqdm import tqdm

from config import AppConfig, DEFAULT_SEARCH_DOMAINS
from crawler.spider import CrawlerSettings, build_queries, collect_job_urls
from extractor.ai_extractor import AIExtractor
from extractor.schema import JobRecord
from output.export import save_outputs, save_raw_json, to_dataframe
from processor.cleaner import clean_records
from processor.enrich import enrich_records
from processor.filter import filter_relevant_jobs


def setup_logging(verbose: bool = False) -> None:
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format="%(asctime)s | %(levelname)s | %(name)s | %(message)s")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="AI-assisted job scraping pipeline")
    parser.add_argument("--query", required=True, help="Primary search query, e.g. 'machine learning engineer remote'")
    parser.add_argument("--max-urls", type=int, default=60, help="Maximum URLs to process")
    parser.add_argument("--profile", default="Python ML engineer seeking remote or Europe roles.")
    parser.add_argument("--daily", action="store_true", help="Store dated output files for daily runs")
    parser.add_argument("--verbose", action="store_true", help="Enable debug logs")
    return parser.parse_args()


def _dated(path: Path) -> Path:
    stamp = datetime.utcnow().strftime("%Y%m%d")
    return path.with_name(f"{path.stem}_{stamp}{path.suffix}")


def run_pipeline(args: argparse.Namespace) -> None:
    cfg = AppConfig(max_urls=args.max_urls).resolved_paths()
    logger = logging.getLogger("job_scraper")

    queries = build_queries(args.query, cfg.role_keywords)
    logger.info("Generated %s queries", len(queries))

    crawl_settings = CrawlerSettings(
        max_urls=cfg.max_urls,
        request_delay=cfg.request_delay,
        timeout_seconds=cfg.timeout_seconds,
    )
    urls = collect_job_urls(queries, DEFAULT_SEARCH_DOMAINS, crawl_settings)
    if not urls:
        logger.warning("No candidate job URLs found.")

    extractor = AIExtractor(cfg)
    extracted: List[JobRecord] = []
    for url in tqdm(urls, desc="Extracting job details"):
        extracted.append(extractor.extract_job(url))

    save_raw_json(extracted, _dated(cfg.raw_json_path) if args.daily else cfg.raw_json_path)

    cleaned = clean_records(extracted)
    enriched = enrich_records(cleaned, extractor=extractor, profile_text=args.profile)
    filtered = filter_relevant_jobs(enriched, cfg)

    df = to_dataframe(filtered)
    excel = _dated(cfg.output_excel) if args.daily else cfg.output_excel
    csv = _dated(cfg.output_csv) if args.daily else cfg.output_csv
    save_outputs(df, excel, csv)

    logger.info("Pipeline done: %s jobs exported to %s", len(df), excel)


if __name__ == "__main__":
    arguments = parse_args()
    setup_logging(arguments.verbose)
    run_pipeline(arguments)
