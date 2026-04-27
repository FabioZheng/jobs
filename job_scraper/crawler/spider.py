"""Scrapy components for collecting job URLs from search pages."""

from __future__ import annotations

import logging
import urllib.parse
from dataclasses import dataclass
from typing import Iterable, List, Sequence, Set

import scrapy
from scrapy.crawler import CrawlerProcess

SEARCH_ENGINES = [
    "https://duckduckgo.com/html/?q={query}",
    "https://www.bing.com/search?q={query}",
]


@dataclass
class CrawlerSettings:
    """Config passed from main pipeline into crawler runner."""

    max_urls: int = 100
    request_delay: float = 0.4
    timeout_seconds: int = 30


class JobUrlSpider(scrapy.Spider):
    """Collects job listing URLs from search results."""

    name = "job_url_spider"

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
        "LOG_LEVEL": "ERROR",
    }

    def __init__(self, queries: Sequence[str], domains: Sequence[str], max_urls: int = 100, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.queries = list(queries)
        self.allowed_domain_patterns = [d.lower() for d in domains]
        self.max_urls = max_urls
        self.collected_urls: Set[str] = set()

    def start_requests(self) -> Iterable[scrapy.Request]:
        for query in self.queries:
            encoded = urllib.parse.quote_plus(query)
            for template in SEARCH_ENGINES:
                yield scrapy.Request(template.format(query=encoded), callback=self.parse)

    def parse(self, response: scrapy.http.Response):
        for href in response.css("a::attr(href)").getall():
            normalized = response.urljoin(href)
            if self._is_job_url(normalized):
                self.collected_urls.add(normalized)
                if len(self.collected_urls) >= self.max_urls:
                    raise scrapy.exceptions.CloseSpider("max_urls_reached")

    def _is_job_url(self, url: str) -> bool:
        lowered = url.lower()
        if not lowered.startswith("http"):
            return False
        if any(domain in lowered for domain in self.allowed_domain_patterns):
            return True
        return any(x in lowered for x in ["/jobs/", "viewjob", "job-listing", "careers/"])


def build_queries(seed_query: str, role_keywords: List[str]) -> List[str]:
    """Generate multiple search queries from one user query."""
    base = seed_query.strip()
    variations = [
        base,
        f"site:linkedin.com/jobs {base}",
        f"site:indeed.com {base}",
        f"site:glassdoor.com {base}",
    ]
    for keyword in role_keywords[:3]:
        variations.append(f"{base} {keyword} jobs")

    # preserve order while deduplicating
    deduped = list(dict.fromkeys(v for v in variations if v))
    return deduped


def collect_job_urls(queries: Sequence[str], domains: Sequence[str], settings: CrawlerSettings) -> List[str]:
    """Run scrapy spider and return a de-duplicated URL list."""
    from scrapy import signals

    logger = logging.getLogger(__name__)
    spider_holder: dict[str, list[str]] = {"urls": []}

    process = CrawlerProcess(
        {
            "DOWNLOAD_DELAY": settings.request_delay,
            "DOWNLOAD_TIMEOUT": settings.timeout_seconds,
            "TELNETCONSOLE_ENABLED": False,
        }
    )
    crawler = process.create_crawler(JobUrlSpider)

    def _on_spider_closed(spider: JobUrlSpider, reason: str):
        spider_holder["urls"] = list(spider.collected_urls)

    crawler.signals.connect(_on_spider_closed, signal=signals.spider_closed)
    process.crawl(crawler, queries=queries, domains=domains, max_urls=settings.max_urls)
    process.start(stop_after_crawl=True)

    urls = spider_holder.get("urls", [])
    logger.info("Collected %s candidate URLs", len(urls))
    return urls[: settings.max_urls]
