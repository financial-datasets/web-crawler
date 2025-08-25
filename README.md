# Web Crawler

A minimal, real-time web search CLI that searches the internet for you. Enter a query and get search results as JSON (title, url, published_date), sorted by recency.

<img width="1164" height="633" alt="Screenshot 2025-08-25 at 12 30 03 PM" src="https://github.com/user-attachments/assets/8c3cfab6-6f7a-4dd0-a14c-ad2893c09726" />


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
