import asyncio
import aiohttp
from datetime import datetime
from .base import BaseSearcher, SearchResult
from .google import GoogleNewsSearcher

class SearchEngine:
    def __init__(self):
        # Create session once for better connection pooling
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
        headers = self._get_headers()
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout, connector=connector)
        
        # Initialize searchers with shared session
        self.searchers = [GoogleNewsSearcher(self.session)]

    async def get_search_results(self, query: str, max_results_per_source: int = 5) -> dict:
        """Main search function with rate limiting and orchestration across searchers."""

        # Kick off all searchers in parallel and flatten results
        tasks = [self._run_searcher(searcher, query, max_results_per_source) for searcher in self.searchers]
        search_results: list[SearchResult] = [
            result for results in await asyncio.gather(*tasks, return_exceptions=True) 
            for result in results
        ]
        
        # Sort results by published date
        search_results.sort(key=lambda x: (x.published_date or datetime.min), reverse=True)

        # Format results for response
        response = {
            "query": query,
            "results": [
                {
                    "title": r.title,
                    "url": r.url,
                    "published_date": r.published_date.isoformat() if r.published_date else None,
                }
                for r in search_results
            ],
        }

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
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        }
    

if __name__ == "__main__":
    asyncio.run(SearchEngine().get_search_results("Apple earnings"))