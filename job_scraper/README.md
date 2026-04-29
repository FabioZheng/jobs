# AI Job Scraper

A modular Python project that discovers job URLs, extracts structured fields using AI, filters/ranks positions, and exports a clean Excel spreadsheet.

## What this project does

1. **Discover URLs** with Scrapy from search engine results (LinkedIn, Indeed, Glassdoor, and career-site patterns).
2. **Extract structured fields** from each job page with:
   - **Primary:** ScrapeGraphAI (`SCRAPEGRAPH_API_KEY`)
   - **Fallback:** OpenAI (`OPENAI_API_KEY`)
3. **Clean & normalize** records (salary/location/date, dedupe by URL).
4. **Enrich & rank** jobs (seniority, skill tags, relevance score).
5. **Filter** to relevant ML/AI/Data opportunities and export Excel + CSV.

## Features

- Hybrid pipeline: traditional crawling + AI extraction.
- CLI interface (`--query`, `--max-urls`, `--profile`, `--daily`, `--verbose`).
- Configurable `.env` settings for filters and crawler behavior.
- Progress bar and structured logs.
- Raw JSON snapshot for audit/debug (`jobs_raw.json`).

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

---

## How to run and use this

### 1) Prerequisites

- Python **3.10+**
- macOS/Linux shell (Windows works with PowerShell equivalents)

### 2) Install

From repository root (`/workspace/jobs`):

```bash
cd job_scraper
python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

(Optional, only needed if you plan to use Playwright rendering helper):

```bash
python -m playwright install chromium
```

### 3) Configure API keys

```bash
cp .env.example .env
```

Then edit `.env` and set at least one provider:

- `SCRAPEGRAPH_API_KEY=...` (preferred primary extractor)
- `OPENAI_API_KEY=...` (fallback extractor + enrichment)

You can set both. If ScrapeGraph fails, fallback will use OpenAI.

### 4) Run the pipeline

Basic run:

```bash
python main.py --query "machine learning engineer remote"
```

With additional options:

```bash
python main.py \
  --query "junior ai engineer" \
  --max-urls 80 \
  --profile "Junior ML engineer with Python, NLP, LLM, PyTorch" \
  --verbose
```

Daily date-stamped outputs:

```bash
python main.py --query "data scientist remote europe" --daily
```

### 5) Find outputs

Generated files are saved to:

- `job_scraper/data/jobs.xlsx`
- `job_scraper/data/jobs.csv`
- `job_scraper/data/jobs_raw.json`

When using `--daily`, names include date suffixes (for example `jobs_20260429.xlsx`).

---

## CLI reference

```bash
python main.py --help
```

Arguments:

- `--query` (required): base search query, e.g. `"ml engineer remote"`
- `--max-urls` (default: `60`): limit of discovered URLs to process
- `--profile` (default included): profile text used for relevance scoring
- `--daily`: save date-stamped output files
- `--verbose`: debug-level logging

---

## Spreadsheet columns

Final Excel/CSV uses:

| Title | Company | Location | Salary | Skills | Seniority | Remote | Score | URL |

---

## Troubleshooting

- **No jobs found**
  - Try broader query terms (e.g., `"machine learning remote"`).
  - Increase `--max-urls`.
  - Search engines may throttle/limit scraping.

- **Extraction failed rows**
  - Check API keys in `.env`.
  - Ensure at least one provider is set.
  - Some job pages block bots or require authentication.

- **Excel not generated**
  - Ensure `openpyxl` is installed (`pip install -r requirements.txt`).

---

## Notes

- Respect website terms of service and legal policies in your jurisdiction.
- Some job boards aggressively block automated traffic; consider proxy/session hardening for production usage.
