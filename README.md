# Web Crawler

## Overview
A minimal, real-time web search CLI. Enter a query and get structured JSON output with a brief summary and recent links.

## How to Run
- Prereqs: Python 3.12+ and [uv](https://docs.astral.sh/uv/)
- From the repo root, run:

```bash
uv run web-crawler
```

- When prompted, enter your search (e.g., "AAPL latest earnings transcript").
- Results print as JSON. Enter another query to continue.
- Quit with `q`, `quit`, `exit`, or press Ctrl+C.
