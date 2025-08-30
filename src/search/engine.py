import asyncio
from datetime import datetime, timedelta
from typing import Dict
from .searcher import WebSearcher

class SearchEngine:
    def __init__(self):
        self.rate_limiter = asyncio.Semaphore(10)  # Max 10 concurrent requests
        self.cache = {}
        self.cache_ttl = timedelta(minutes=15)  # Cache for 15 minutes

    async def search(self, query: str, max_results: int = 20) -> Dict:
        """Main search function with caching and rate limiting"""
        cache_key = f"{query}:{max_results}"
        
        # Check cache first
        if cache_key in self.cache:
            cached_result, timestamp = self.cache[cache_key]
            if datetime.now() - timestamp < self.cache_ttl:
                return cached_result

        async with self.rate_limiter:
            async with WebSearcher() as searcher:
                results = await searcher.search(query, max_results // len(searcher.site_configs))

                # Sort results by published date descending
                results.sort(key=lambda x: (x.published_date or datetime.min), reverse=True)
                
                # Format response similar to Tavily
                response = {
                    "query": query,
                    "results": [
                        {
                            "title": result.title,
                            "url": result.url,
                            "published_date": result.published_date.isoformat() if result.published_date else None,
                        }
                        for result in results[:max_results]
                    ],
                }
                
                # Cache the result
                self.cache[cache_key] = (response, datetime.now())
                return response
