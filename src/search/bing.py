import aiohttp
from .base import BaseSearcher, SearchResult

class BingNewsSearcher(BaseSearcher):
    """
    RSS-based searcher for Bing News.
    """

    def __init__(self, session: aiohttp.ClientSession):
        self.session = session

    @property
    def searcher(self) -> str:
        return "Bing News"

    async def get_search_results(self, query: str, max_results: int) -> list[SearchResult]:
        # Build Bing News RSS URL
        encoded_query = query.replace(" ", "+")
        search_url = f"https://www.bing.com/news/search?q={encoded_query}&format=RSS"

        async with self.session.get(search_url) as response:
            if response.status != 200:
                return []
            xml_content = await response.text()

            # Reuse shared RSS parsing logic from BaseSearcher
            results = self.parse_rss_content(xml_content, max_results)

            # Bing doesn’t use redirect wrappers like Google News,
            # so we can return results directly.
            final: list[SearchResult] = []
            for r in results:
                final.append(
                    SearchResult(
                        title=r.title,
                        url=r.url,
                        published_date=r.published_date,
                        searcher=self.searcher,
                    )
                )
            return final
    
