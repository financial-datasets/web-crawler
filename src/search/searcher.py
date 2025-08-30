import asyncio
import aiohttp
import re
from datetime import datetime
from pydantic import BaseModel


class SearchResult(BaseModel):
    title: str
    url: str
    published_date: datetime | None = None


class WebSearcher:
    def __init__(self):
        self.session = None
        # Rotate user agents to avoid detection
        self.user_agents = [
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15'
        ]
        self.current_ua_index = 0
        
        # Simplified site configurations for 3 sources only
        self.site_configs = {
            'news.google.com': {
                'search_url': 'https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en',
                'api_based': False,
                'method': 'GET',
                'is_rss': True
            }
        }

    async def __aenter__(self):
        # Get rotating headers
        headers = self.get_headers()
        # Add random delay and timeout
        timeout = aiohttp.ClientTimeout(total=30, connect=10)
        connector = aiohttp.TCPConnector(limit=50, limit_per_host=10)
        self.session = aiohttp.ClientSession(headers=headers, timeout=timeout, connector=connector)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def get_headers(self):
        """Get headers with rotating user agent"""
        ua = self.user_agents[self.current_ua_index]
        self.current_ua_index = (self.current_ua_index + 1) % len(self.user_agents)
        
        return {
            'User-Agent': ua,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        }

    async def search(self, query: str, max_results_per_source: int = 5) -> list[SearchResult]:
        """Search across multiple sources simultaneously"""
        tasks = []
        for domain in self.site_configs.keys():
            tasks.append(self.get_search_results(domain, query, max_results_per_source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and filter results
        all_results = []
        for i, result in enumerate(results):
            domain = list(self.site_configs.keys())[i]
            if isinstance(result, list):
                all_results.extend(result)
            elif isinstance(result, Exception):
                print(f"✗ {domain}: Error - {str(result)}")
            else:
                print(f"✗ {domain}: No results")
        
        # Sort by recency
        all_results.sort(key=lambda x: (x.published_date or datetime.min), reverse=True)
        
        print(f"Total results found: {len(all_results)}")
        
        return all_results

    async def get_search_results(self, domain: str, query: str, max_results: int) -> list[SearchResult]:
        """Handle API-based and RSS-based searches"""
        search_url = self.site_configs[domain]['search_url'].format(query=query.replace(' ', '%20'))
        
        # Add delay to avoid rate limiting
        await asyncio.sleep(0.5)
        
        try:
            async with self.session.get(search_url) as response:
                if response.status != 200:
                    print(f"HTTP {response.status} from {domain}")
                    return []
                
                results = []
                
                # Handle RSS feeds
                xml_content = await response.text()
                results = self.parse_rss_content(xml_content, domain, max_results)
                
                # Resolve Google News URLs to get original article URLs
                if domain == 'news.google.com':
                    resolved_urls = await asyncio.gather(
                        *(self.resolve_google_news_url(r.url) for r in results)
                    )
                    resolved_results = []
                    for r, resolved_url in zip(results, resolved_urls):
                        resolved_results.append(SearchResult(
                            title=r.title,
                            url=resolved_url,
                            published_date=r.published_date,
                        ))
                    results = resolved_results
            
                return results
                
        except asyncio.TimeoutError:
            print(f"Timeout when searching {domain}")
            return []
        except Exception as e:
            print(f"Exception when searching {domain}: {str(e)}")
            return []

    async def resolve_google_news_url(self, google_url: str) -> str:
        """Resolve the original article URL from a Google News redirect URL"""
        if not google_url or 'news.google.com' not in google_url:
            return google_url
        
        try:
            from googlenewsdecoder import gnewsdecoder
            
            # Offload synchronous decoder to a thread to avoid blocking event loop
            result = await asyncio.to_thread(gnewsdecoder, google_url, interval=1)
            
            if result.get("status"):
                return result["decoded_url"]
            else:
                return google_url
                
        except Exception as e:
            print(f"Error resolving Google News URL: {str(e)}")
            # Fall back to original URL if decoding fails
            return google_url

    def parse_rss_content(self, xml_content: str, domain: str, max_results: int) -> list[SearchResult]:
        """Common function to parse RSS feed content"""
        try:
            from xml.etree import ElementTree as ET
            root = ET.fromstring(xml_content)
            results = []
            
            # Find all item elements
            items = root.findall('.//item')[:max_results * 2]  # Get extra in case we need to filter
            
            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                date_elem = item.find('pubDate')
                
                title = title_elem.text if title_elem is not None else "No title"
                url = link_elem.text if link_elem is not None else ""
                pub_date = date_elem.text if date_elem is not None else ""
                
                results.append(
                    SearchResult(
                      title=self.clean_text(title),
                      url=url,
                      published_date=self.parse_rss_date(pub_date),
                  )
                )
                
                if len(results) >= max_results:
                    break
            
            return results
            
        except ET.ParseError as e:
            print(f"XML parsing error for {domain}: {str(e)}")
            return []

    def parse_rss_date(self, date_str: str) -> datetime | None:
        """Common function to parse RSS date formats"""
        if not date_str:
            return None
        
        # Common RSS date format: "Wed, 02 Oct 2024 14:30:00 GMT"
        try:
            # Remove timezone info and parse
            date_str = date_str.replace(' GMT', '').replace(' +0000', '')
            return datetime.strptime(date_str, '%a, %d %b %Y %H:%M:%S')
        except:
            return self.parse_date(date_str)

    def clean_text(self, text: str) -> str:
        """Common function to clean text by removing HTML entities, unicode, and extra whitespace"""
        if not text:
            return text
            
        # Remove HTML tags if any
        text = re.sub(r'<[^>]+>', '', text)
        
        # Remove HTML entities
        import html
        text = html.unescape(text)
        
        # Replace common unicode characters
        unicode_replacements = {
            '\u2018': "'",  # Left single quotation mark
            '\u2019': "'",  # Right single quotation mark
            '\u201c': '"',  # Left double quotation mark
            '\u201d': '"',  # Right double quotation mark
            '\u2013': '-',  # En dash
            '\u2014': '-',  # Em dash
            '\u2026': '...',  # Horizontal ellipsis
            '\u00a0': ' ',  # Non-breaking space
            '\u00ae': '(R)',  # Registered trademark
            '\u2122': '(TM)',  # Trademark
        }
        
        for unicode_char, replacement in unicode_replacements.items():
            text = text.replace(unicode_char, replacement)
        
        # Remove any remaining non-ASCII characters
        text = text.encode('ascii', 'ignore').decode('ascii')
        
        # Remove extra whitespace
        text = ' '.join(text.split())
        
        return text

    def parse_date(self, date_str: str) -> datetime | None:
        """Common function to parse various date formats"""
        if not date_str:
            return None
        
        # Common date patterns
        patterns = [
            r'(\d{4}-\d{2}-\d{2})',  # YYYY-MM-DD
            r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
            r'(\w+ \d{1,2}, \d{4})',  # Month DD, YYYY
        ]
        
        for pattern in patterns:
            match = re.search(pattern, date_str)
            if match:
                try:
                    date_part = match.group(1)
                    # Try different parsing approaches
                    for fmt in ['%Y-%m-%d', '%m/%d/%Y', '%B %d, %Y']:
                        try:
                            return datetime.strptime(date_part, fmt)
                        except ValueError:
                            continue
                except:
                    pass
        
        return None
    

if __name__ == "__main__":
    async def main():
        async with WebSearcher() as searcher:
          results = await searcher.search("Python programming", 5)
          print(results)

    asyncio.run(main())