# Web Crawler

A minimal, real-time web search CLI. Enter a query and get structured JSON output with a brief summary and recent links.

## Setup
- Prereqs: Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- Clone the repository and navigate into the project root:

```bash
git clone https://github.com/financial-datasets/web-crawler.git
cd web-crawler
```

## How to Run
- From the repo root, run:

```bash
uv run web-crawler
```

- When prompted, enter your search (e.g., "AAPL latest earnings transcript").
- Results print as JSON. Enter another query to continue.
- Quit with `q`, `quit`, `exit`, or press Ctrl+C.
