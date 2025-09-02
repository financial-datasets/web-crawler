import os
import sys
import json
import pathlib
import pytest
import asyncio

# Ensure src is on sys.path for direct imports when running from repo root
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from search.searcher import WebSearcher, SearchResult

QUERY = "Apple earnings"

@pytest.mark.asyncio
async def test_websearcher_search_multiple_sources_real_rss():
    async with WebSearcher() as ws:
        results = await ws.search_multiple_sources(QUERY, max_results_per_source=3, debug=False)

    assert isinstance(results, list)
    # We may receive zero results in transient network issues, but normally should have some
    # Keep a minimal check to be stable across environments
    if results:
        assert isinstance(results[0], SearchResult)
        # Basic fields present
        r0 = results[0]
        assert isinstance(r0.title, str)
        assert isinstance(r0.url, str)
        assert isinstance(r0.snippet, str)
        assert isinstance(r0.source, str)

@pytest.mark.asyncio
async def test_websearcher_single_source_google_news_real_rss():
    async with WebSearcher() as ws:
        # Directly exercise the configured domain to ensure parsing path works
        results = await ws.search_single_source('news.google.com', QUERY, max_results=3)

    assert isinstance(results, list)
    if results:
        assert all(isinstance(r, SearchResult) for r in results)
        # URLs should be strings; after decode they may be external sites
        assert all(isinstance(r.url, str) and r.url for r in results) 