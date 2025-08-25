import os
import sys
import re
import json
import pathlib
import pytest

# Ensure src is on sys.path for direct imports when running from repo root
REPO_ROOT = pathlib.Path(__file__).resolve().parents[1]
SRC_DIR = REPO_ROOT / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from crawler.parser import PageParser

URL = "https://www.cnbc.com/2025/07/31/apple-aapl-q3-earnings-report-2025.html"

def test_pageparser_get_links_with_playwright_real_site(tmp_path):
    parser = PageParser()

    result = parser.get_links(URL)

    assert isinstance(result, dict)
    assert result.get("url") == URL
    links = result.get("internal_links")
    assert isinstance(links, list)
    # Should find at least some links on a long article page
    assert len(links) > 5

def test_pageparser_get_content_with_playwright_real_site(tmp_path):
    parser = PageParser()

    result = parser.get_content(URL)

    assert isinstance(result, dict)
    assert result.get("url") == URL
    assert result.get("title") is not None
    assert result.get("content") is not None
    assert result.get("content_length") > 0