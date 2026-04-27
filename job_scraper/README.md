# AI Job Scraper

A modular Python project that discovers job URLs, extracts structured fields using AI, filters/ranks positions, and exports a clean Excel spreadsheet.

## Features

- Hybrid pipeline:
  - **Traditional scraping** with Scrapy for job URL discovery.
  - **AI extraction** with ScrapeGraphAI, with **OpenAI fallback**.
- Data cleaning and normalization (salary/location/date, dedupe by URL).
- AI/heuristic enrichment (seniority, skill tags, relevance score).
- AI/keyword filtering for relevant entry-level ML/AI/Data roles in Europe or remote.
- Excel + CSV export and optional raw JSON snapshot.
- CLI support, logging, progress bars, daily output mode.

## Project layout

```text
job_scraper/
├── main.py
├── config.py
├── requirements.txt
├── .env.example
├── README.md
├── crawler/
│   ├── spider.py
│   └── playwright_helper.py
├── extractor/
│   ├── ai_extractor.py
│   └── schema.py
├── processor/
│   ├── cleaner.py
│   ├── filter.py
│   └── enrich.py
├── output/
│   └── export.py
└── data/
```

## Setup

1. Create environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python -m playwright install chromium
```

2. Configure secrets:

```bash
cp .env.example .env
# edit .env with API keys
```

> You can run extraction with ScrapeGraphAI key, OpenAI key, or both (ScrapeGraph first, OpenAI fallback).

## Usage

From the `job_scraper/` directory:

```bash
python main.py --query "machine learning engineer remote"
```

Useful flags:

- `--max-urls 80`
- `--profile "Junior data scientist with Python, NLP, LLM experience"`
- `--daily` (creates date-stamped outputs)
- `--verbose`

## Output

The pipeline writes files under `data/`:

- `jobs.xlsx`
- `jobs.csv`
- `jobs_raw.json`

Column format in spreadsheet:

| Title | Company | Location | Salary | Skills | Seniority | Remote | Score | URL |

## Notes

- Some job sites aggressively block bots; you may need proxies, headers, or authenticated sessions for high coverage.
- Respect website terms of service and robots policies for your usage context.
- For JS-heavy pages, you can call Playwright helper in a custom extraction flow.
