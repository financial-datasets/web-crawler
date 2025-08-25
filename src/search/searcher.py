import asyncio
import aiohttp
import re
from datetime import datetime
from pydantic import BaseModel
from typing import List, Dict, Optional


class SearchResult(BaseModel):
    title: str
    url: str
    snippet: str
    published_date: Optional[datetime] = None
    source: str


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

    async def search_multiple_sources(self, query: str, max_results_per_source: int = 5, debug: bool = True) -> List[SearchResult]:
        """Search across multiple sources simultaneously"""
        if debug:
            print(f"Searching for: '{query}' across {len(self.site_configs)} sources...")
        
        tasks = []
        for domain in self.site_configs.keys():
            tasks.append(self.search_single_source(domain, query, max_results_per_source))
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Flatten and filter results
        all_results = []
        for i, result in enumerate(results):
            domain = list(self.site_configs.keys())[i]
            if isinstance(result, list):
                if debug:
                    print(f"✓ {domain}: {len(result)} results")
                all_results.extend(result)
            elif isinstance(result, Exception):
                if debug:
                    print(f"✗ {domain}: Error - {str(result)}")
            else:
                if debug:
                    print(f"✗ {domain}: No results")
        
        # Sort by recency
        all_results.sort(key=lambda x: (x.published_date or datetime.min), reverse=True)
        
        if debug:
            print(f"Total results found: {len(all_results)}")
        
        return all_results

    async def search_single_source(self, domain: str, query: str, max_results: int = 5) -> List[SearchResult]:
        """Search a single source for relevant content"""
        if domain not in self.site_configs:
            return []
        
        config = self.site_configs[domain]
        
        try:
            return await self.search_api_or_rss_based(domain, query, config, max_results)
        except Exception as e:
            print(f"Error searching {domain}: {str(e)}")
            return []

    async def search_api_or_rss_based(self, domain: str, query: str, config: Dict, max_results: int) -> List[SearchResult]:
        """Handle API-based and RSS-based searches"""
        search_url = config['search_url'].format(query=query.replace(' ', '%20'))
        
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
                results = self.parse_rss_content(xml_content, query, domain, config, max_results)
                
                # Resolve Google News URLs to get original article URLs
                if domain == 'news.google.com':
                    resolved_results = []
                    for result in results:
                        resolved_url = await self.resolve_google_news_url(result.url)
                        # Create new result with resolved URL
                        resolved_result = SearchResult(
                            title=result.title,
                            url=resolved_url,
                            snippet=result.snippet,
                            published_date=result.published_date,
                            source=result.source,
                        )
                        resolved_results.append(resolved_result)
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
            
            # Use googlenewsdecoder to decode the URL
            result = gnewsdecoder(google_url, interval=1)
            
            if result.get("status"):
                return result["decoded_url"]
            else:
                return google_url
                
        except Exception as e:
            print(f"Error resolving Google News URL: {str(e)}")
            # Fall back to original URL if decoding fails
            return google_url

    def parse_rss_content(self, xml_content: str, query: str, domain: str, config: Dict, max_results: int) -> List[SearchResult]:
        """Parse RSS feed content"""
        try:
            from xml.etree import ElementTree as ET
            root = ET.fromstring(xml_content)
            results = []
            
            # Find all item elements
            items = root.findall('.//item')[:max_results * 2]  # Get extra in case we need to filter
            
            for item in items:
                title_elem = item.find('title')
                link_elem = item.find('link')
                desc_elem = item.find('description')
                date_elem = item.find('pubDate')
                
                title = title_elem.text if title_elem is not None else "No title"
                url = link_elem.text if link_elem is not None else ""
                description = desc_elem.text if desc_elem is not None else "No description"
                pub_date = date_elem.text if date_elem is not None else ""
                
                
                
                if title and url:
                    result = SearchResult(
                        title=self.clean_text(title),
                        url=url,  # Will be resolved later in async context
                        snippet=self.clean_snippet(description),
                        published_date=self.parse_rss_date(pub_date),
                        source=domain.split('.')[0].title(),
                    )
                    results.append(result)
                
                if len(results) >= max_results:
                    break
            
            return results
            
        except ET.ParseError as e:
            print(f"XML parsing error for {domain}: {str(e)}")
            return []

    def parse_rss_date(self, date_str: str) -> Optional[datetime]:
        """Parse RSS date formats"""
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
        """Clean text by removing HTML entities, unicode, and extra whitespace"""
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
    
    def clean_snippet(self, snippet: str) -> str:
        """Clean and truncate snippet text"""
        snippet = self.clean_text(snippet)
        # Truncate to reasonable length
        if len(snippet) > 200:
            snippet = snippet[:200] + "..."
        return snippet

    def parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats"""
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