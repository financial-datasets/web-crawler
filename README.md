# Web Crawler

A minimal, real-time web search CLI that searches the internet for you. Enter a query and get search results as JSON (title, url, published_date), sorted by recency.

## Setup
- Prerequisites: Python 3.12+ and [uv](https://docs.astral.sh/uv/)

```bash
# Clone the repository
git clone https://github.com/financial-datasets/web-crawler.git

# Navigate into the project root:
cd web-crawler
```

## How to Run
- From the repo root, run:

```bash
# Run the program!
uv run web-crawler
```

- When prompted, enter your search (e.g., "AAPL latest earnings transcript").
- Results print as JSON. Enter another query to continue.
- Quit with `q`, `quit`, `exit`, or press Ctrl+C.
