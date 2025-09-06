# Web Crawler

A minimal, real-time web search CLI that searches the internet for you. Enter a query and get search results as JSON (title, url, published_date), sorted by recency.

<img width="1162" height="628" alt="Screenshot 2025-08-25 at 12 31 22 PM" src="https://github.com/user-attachments/assets/12e05c97-4e46-4fd3-a467-3276f290b63d" />


## Setup
**Prerequisites**: Python 3.12+ and [uv](https://docs.astral.sh/uv/)

```bash
# Clone the repository
git clone https://github.com/financial-datasets/web-crawler.git

# Navigate into the project root:
cd web-crawler
```

## How to Run
```bash
# From the repo root, run:
uv run web-crawler
```

- When prompted, enter your search (e.g., "AAPL latest earnings transcript").
- Results print as JSON. Enter another query to continue.
- Quit with `q`, `quit`, `exit`, or press Ctrl+C.

## Features
We currently have two features:
1. Search (see `/src/search`)
2. Parse (see `/src/parse`)

#### Search
Given a query (e.g. "Apple latest earnings"), search the internet for pages related to the query.

#### Parse
Given a URL, parse and extract the text content from the URL.

## Roadmap
We'd love to get help on:
- [ ] Parsing content from JavaScript-heavy pages (e.g. MSN, Bloomberg, etc.)
- [ ] Summarizing parsed content with LLMs
- [ ] Adding more sources (Reddit, Bloomberg, etc.)
- [ ] Parallelization for faster queries
