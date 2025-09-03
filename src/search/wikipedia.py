import aiohttp
from .base import BaseSearcher, SearchResult
from datetime import datetime

class WikipediaSearcher(BaseSearcher):
    """
    Searcher for Wikipedia using the MediaWiki search API.
    """

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    @property
    def searcher(self) -> str:
        return "Wikipedia"

    async def get_search_results(self, query: str, max_results: int) -> list[SearchResult]:
        encoded_query = query.replace(" ", "%20")
        search_url = (
            f"https://en.wikipedia.org/w/api.php"
            f"?action=query&list=search&srsearch={encoded_query}&utf8=&format=json&srlimit={max_results}"
        )

        async with self.session.get(search_url) as response:
            if response.status != 200:
                return []

            data = await response.json()
            results: list[SearchResult] = []

            for item in data.get("query", {}).get("search", []):
                title = item.get("title", "No title")
                page_id = item.get("pageid")
                url = f"https://en.wikipedia.org/?curid={page_id}"
                ts = item.get("timestamp")  # ISO8601 format
                published_date = None
                if ts:
                    try:
                        published_date = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    except Exception:
                        published_date = None

                results.append(
                    SearchResult(
                        title=self.clean_text(title),
                        url=url,
                        published_date=published_date,
                        searcher=self.searcher,
                    )
                )

            return results
