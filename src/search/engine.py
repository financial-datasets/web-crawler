import asyncio
import aiohttp
from datetime import datetime

from .base import BaseSearcher, SearchResult
from .bing import BingNewsSearcher
from .google import GoogleNewsSearcher
from .wikipedia import WikipediaSearcher

class SearchEngine:
    def __init__(self):
        # Initialize searcher classes, but don't create session yet
        self._session = None
        self._timeout = aiohttp.ClientTimeout(total=30, connect=10)
        self._connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
        self._headers = self._get_headers()

    async def get_search_results(self, query: str, max_results_per_source: int = 5) -> dict:
        """Main search function with rate limiting and orchestration across searchers."""
        if not self._session or self._session.closed:
            raise RuntimeError("SearchEngine must be used as an async context manager")

        # Kick off all searchers in parallel and flatten results
        tasks = [self._run_searcher(searcher, query, max_results_per_source) for searcher in self.searchers]
        search_results: list[SearchResult] = [
            result for results in await asyncio.gather(*tasks, return_exceptions=True) 
            for result in results
        ]
        
        # Sort results by published date (normalize timezone-aware dates to naive for comparison)
        search_results.sort(key=lambda x: self._datetime_sort_key(x.published_date), reverse=True)

        # Format results for response
        response = {
            "query": query,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "published_date": r.published_date.isoformat() if r.published_date else None,
                    "searcher": r.searcher,
                }
                for r in search_results
            ],
        }

        # Don't close session here - let context manager handle it
        return response

    async def _run_searcher(self, searcher: BaseSearcher, query: str, max_results: int) -> list[SearchResult]:
        # small delay to avoid rate limiting bursts
        await asyncio.sleep(0.5)
        try:
            return await searcher.get_search_results(query, max_results)
        except asyncio.TimeoutError:
            print(f"Timeout when searching with {searcher.__class__.__name__}")
            return []
        except Exception as e:
            print(f"Exception when searching with {searcher.__class__.__name__}: {str(e)}")
            return []
        
    
    def _get_headers(self) -> dict[str, str]:
        return {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
        }
            
    async def __aenter__(self):
        # Create session when entering context
        self._session = aiohttp.ClientSession(
            headers=self._headers, 
            timeout=self._timeout, 
            connector=self._connector
        )
        # Initialize searchers with session
        self.searchers = [
            BingNewsSearcher(self._session), 
            GoogleNewsSearcher(self._session), 
            WikipediaSearcher(self._session),
        ]
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Ensure session is properly closed when exiting context
        if self._session and not self._session.closed:
            await self._session.close()

    def _datetime_sort_key(dt: datetime | None) -> datetime:
      """
      Normalize datetime objects for sorting by converting timezone-aware dates to naive.
      Returns datetime.min for None values to sort them last when reverse=True.
      """
      if dt is None:
          return datetime.min
      # Convert timezone-aware to naive by replacing tzinfo
      return dt.replace(tzinfo=None) if dt.tzinfo is not None else dt 

async def main():
    async with SearchEngine() as search_engine:
        results = await search_engine.get_search_results("Apple earnings")
        print(results)

if __name__ == "__main__":
    asyncio.run(main())