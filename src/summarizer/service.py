"""Summarization service for web crawler search results."""

import asyncio
import logging
from typing import List, Dict, Optional
from .engine import ContentSummarizer, SummaryConfig, SummaryLength
from ..crawler.parser import PageParser

logger = logging.getLogger(__name__)


class SummarizationService:
    """Service for summarizing web content from search results."""
    
    def __init__(self, config: Optional[SummaryConfig] = None):
        self.summarizer = ContentSummarizer(config)
        self.parser = PageParser()
    
    async def summarize_search_results(
        self, 
        search_results: List[Dict], 
        max_summaries: int = 3,
        summary_length: SummaryLength = SummaryLength.MEDIUM
    ) -> List[Dict]:
        """
        Summarize search results by extracting content and generating summaries.
        
        Args:
            search_results: List of search result dictionaries with 'title', 'url', 'published_date'
            max_summaries: Maximum number of results to summarize
            summary_length: Length of summaries to generate
            
        Returns:
            List of search results with added 'summary' field
        """
        if not search_results:
            return []
        
        # Limit the number of summaries to avoid excessive API calls
        results_to_summarize = search_results[:max_summaries]
        
        # Create tasks for parallel processing
        tasks = []
        for result in results_to_summarize:
            task = self._summarize_single_result(result, summary_length)
            tasks.append(task)
        
        # Execute all summarization tasks concurrently with overall timeout
        try:
            summarized_results = await asyncio.wait_for(
                asyncio.gather(*tasks, return_exceptions=True),
                timeout=300  # 5 minute overall timeout for all summarization tasks
            )
            
            # Process results and handle any errors
            final_results = []
            for i, result in enumerate(summarized_results):
                if isinstance(result, Exception):
                    logger.warning(f"Failed to summarize result {i}: {result}")
                    # Keep original result without summary
                    final_results.append(results_to_summarize[i])
                else:
                    final_results.append(result)
            
            # Add remaining results without summaries
            final_results.extend(search_results[max_summaries:])
            
            return final_results

        except asyncio.TimeoutError:
            print(f"⚠️ Summarization service timed out after 5 minutes")
            # Return partial results - some may have completed successfully
            return search_results
        except Exception as e:
            logger.error(f"Summarization service failed: {e}")
            return search_results
    
    async def _summarize_single_result(
        self,
        result: Dict,
        summary_length: SummaryLength
    ) -> Dict:
        """Summarize a single search result."""
        try:
            url = result.get('url')
            title = result.get('title')

            if not url:
                print(f"⚠️ No URL found in result: {result}")
                return result

            # Extract content from the URL with timeout
            print(f"📄 Extracting content from: {title[:50]}...")
            try:
                content_data = await asyncio.wait_for(
                    asyncio.to_thread(self.parser.get_content, url),
                    timeout=120  # 2 minute timeout for content extraction
                )
            except asyncio.TimeoutError:
                print(f"⚠️ Content extraction timeout for: {url}")
                return result
            
            if not content_data or not content_data.get('content'):
                print(f"⚠️ No content extracted from: {url}")
                return result
            
            content = content_data['content']

            # Generate summary with timeout
            print(f"🤖 Generating summary...")
            try:
                summary = await asyncio.wait_for(
                    self.summarizer.summarize_content(
                        content=content,
                        title=title,
                        url=url
                    ),
                    timeout=180  # 3 minute timeout for LLM summarization
                )
            except asyncio.TimeoutError:
                print(f"⚠️ LLM summarization timeout for: {url}")
                return result
            
            if summary:
                result['summary'] = summary
                result['content_length'] = content_data.get('content_length', 0)
                print(f"✅ Summary complete")
            else:
                print(f"⚠️ Failed to generate summary for: {url}")
            
            return result
            
        except Exception as e:
            print(f"⚠️ Error summarizing result {result.get('url', 'unknown')}: {e}")
            return result
    
    async def summarize_single_url(
        self, 
        url: str, 
        title: Optional[str] = None,
        summary_length: SummaryLength = SummaryLength.MEDIUM
    ) -> Optional[str]:
        """
        Summarize content from a single URL.
        
        Args:
            url: URL to summarize
            title: Optional title for context
            summary_length: Length of summary to generate
            
        Returns:
            Summary text or None if failed
        """
        try:
            # Extract content
            content_data = await asyncio.to_thread(
                self.parser.get_content, url
            )
            
            if not content_data or not content_data.get('content'):
                logger.warning(f"No content extracted from: {url}")
                return None
            
            content = content_data['content']
            
            # Generate summary
            summary = await self.summarizer.summarize_content(
                content=content,
                title=title,
                url=url
            )
            
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing URL {url}: {e}")
            return None
