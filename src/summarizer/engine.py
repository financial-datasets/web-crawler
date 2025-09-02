"""LLM-powered content summarization engine using litellm abstraction."""

import asyncio
import os
import logging
from typing import Optional, Dict, List, Literal
from dataclasses import dataclass
from enum import Enum
import litellm
from litellm import completion

# Configure logging - reduce verbosity
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

# Reduce litellm logging verbosity
litellm.set_verbose = False
litellm.logging_level = logging.WARNING


class SummaryLength(Enum):
    """Summary length options."""
    SHORT = "short"      # 1-2 sentences
    MEDIUM = "medium"    # 1 paragraph
    LONG = "long"        # 2-3 paragraphs


@dataclass
class SummaryConfig:
    """Configuration for summarization."""
    provider: str = "openai"
    model: str = "gpt-4o-mini"  # Better quality, more efficient
    max_tokens: int = 4096        # Increased for better summaries
    temperature: float = 0.3
    summary_length: SummaryLength = SummaryLength.MEDIUM
    max_content_length: int = 51200  # Maximum content length to process


class ContentSummarizer:
    """Robust content summarization using litellm."""
    
    def __init__(self, config: Optional[SummaryConfig] = None):
        self.config = config or SummaryConfig()
        self._validate_environment()
        self._setup_litellm()
        
    def _validate_environment(self):
        """Validate that required environment variables are set."""
        provider = self.config.provider.lower()
        if provider == "openai":
            if not os.getenv("OPENAI_API_KEY"):
                raise ValueError("OPENAI_API_KEY environment variable is required for OpenAI provider")
        elif provider == "anthropic":
            if not os.getenv("ANTHROPIC_API_KEY"):
                raise ValueError("ANTHROPIC_API_KEY environment variable is required for Anthropic provider")
        elif provider == "azure":
            if not os.getenv("AZURE_API_KEY"):
                raise ValueError("AZURE_API_KEY environment variable is required for Azure provider")
        elif provider == "local":
            logger.info("Using local model - no API key required")
        else:
            # For other providers, check if they have a custom API key
            custom_key = os.getenv(f"{provider.upper()}_API_KEY")
            if not custom_key:
                logger.warning(f"No API key found for {provider} provider")
    
    def _setup_litellm(self):
        """Configure litellm with provider settings."""
        try:
            # Set provider-specific configurations
            if self.config.provider == "openai":
                litellm.api_key = os.getenv("OPENAI_API_KEY")
            elif self.config.provider == "anthropic":
                litellm.api_key = os.getenv("ANTHROPIC_API_KEY")
            elif self.config.provider == "azure":
                litellm.api_key = os.getenv("AZURE_API_KEY")
                litellm.api_base = os.getenv("AZURE_API_BASE")
                litellm.api_version = os.getenv("AZURE_API_VERSION", "2024-02-15-preview")
            
            # Only log essential setup info
            print(f"✓ Using {self.config.provider} with {self.config.model}")
        except Exception as e:
            logger.error(f"Failed to configure litellm: {e}")
            raise
    
    async def summarize_content(
        self, 
        content: str, 
        title: Optional[str] = None,
        url: Optional[str] = None
    ) -> Optional[str]:
        """Summarize content using LLM in one shot."""
        if not content or not content.strip():
            logger.warning("Empty content provided for summarization")
            return None
        
        # Truncate content if it's too long to avoid token limits
        if len(content) > self.config.max_content_length:
            logger.info(f"Content too long ({len(content)} chars), truncating to {self.config.max_content_length}")
            content = content[:self.config.max_content_length] + "\n\n[Content truncated for summarization]"
        
        try:
            return await self._summarize_content_directly(content, title, url)
        except Exception as e:
            logger.error(f"Summarization failed: {e}")
            return None
    
    async def _summarize_content_directly(
        self, 
        content: str, 
        title: Optional[str] = None,
        url: Optional[str] = None
    ) -> str:
        """Summarize content directly without chunking."""
        prompt = self._build_summary_prompt(content, title, url)
        
        try:
            response = await asyncio.to_thread(
                completion,
                model=self.config.model,
                messages=[{"role": "user", "content": prompt}],
                max_tokens=self.config.max_tokens,
                temperature=self.config.temperature,
                timeout=60  # Increased timeout for longer content
            )
            
            summary = response.choices[0].message.content.strip()
            if summary:
                return summary
            else:
                raise ValueError("Empty response from LLM")
                
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            raise
    
    def _build_summary_prompt(
        self, 
        content: str, 
        title: Optional[str] = None,
        url: Optional[str] = None
    ) -> str:
        """Build a comprehensive prompt for summarization."""
        length_instructions = {
            SummaryLength.SHORT: "Provide a concise summary in 1-2 sentences.",
            SummaryLength.MEDIUM: "Provide a comprehensive summary in 1-2 paragraphs.",
            SummaryLength.LONG: "Provide a detailed summary in 2-3 paragraphs."
        }
        
        prompt = f"""Please summarize the following content. {length_instructions[self.config.summary_length]}

Focus on:
- Key facts and main points
- Important insights or conclusions
- Actionable information if present
- Most relevant details for the reader

Content to summarize:
"""
        
        if title:
            prompt += f"Title: {title}\n\n"
        if url:
            prompt += f"Source: {url}\n\n"
        
        prompt += f"Content:\n{content}\n\nSummary:"
        
        return prompt
    
