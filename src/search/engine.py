import asyncio
from datetime import datetime, timedelta
from typing import List, Dict
from .searcher import SearchResult, WebSearcher

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
                results = await searcher.search_multiple_sources(query, max_results // len(searcher.site_configs), debug=True)

                # Sort results by published date descending
                results.sort(key=lambda x: (x.published_date or datetime.min), reverse=True)
                
                # Format response similar to Tavily
                response = {
                    "query": query,
                    "summary": self.generate_summary(query, results),
                    "results": [
                        {
                            "title": result.title,
                            "url": result.url,
                            "source": result.source,
                            "published_date": result.published_date.isoformat() if result.published_date else None,
                        }
                        for result in results[:max_results]
                    ],
                    "response_time": 0  # Would measure actual response time
                }
                
                # Cache the result
                self.cache[cache_key] = (response, datetime.now())
                return response

    def generate_summary(self, query: str, results: List[SearchResult]) -> str:
        """Generate a summary answer from search results"""
        if not results:
            return f"No recent information found for '{query}'."
        
        # Simple summary generation
        # In practice, this would use an LLM
        top_snippets = [result.snippet for result in results[:3]]
        return f"Based on recent sources: {' '.join(top_snippets[:200])}..."
