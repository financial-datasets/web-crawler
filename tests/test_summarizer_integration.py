"""Integration tests for the summarization feature."""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from src.summarizer.engine import ContentSummarizer, SummaryConfig, SummaryLength
from src.summarizer.service import SummarizationService


class TestContentSummarizer:
    """Test the core summarization engine."""
    
    def test_summarizer_initialization(self):
        """Test summarizer can be initialized with default config."""
        config = SummaryConfig()
        summarizer = ContentSummarizer(config)
        assert summarizer.config == config
        assert summarizer.config.model == "gpt-4o-mini"
        assert summarizer.config.max_tokens == 4096
    
    def test_summarizer_initialization_with_custom_config(self):
        """Test summarizer can be initialized with custom config."""
        config = SummaryConfig(
            provider="anthropic",
            model="claude-3-haiku",
            max_tokens=1000,
            temperature=0.1
        )
        summarizer = ContentSummarizer(config)
        assert summarizer.config.provider == "anthropic"
        assert summarizer.config.model == "claude-3-haiku"
        assert summarizer.config.max_tokens == 1000
        assert summarizer.config.temperature == 0.1
    
    def test_content_truncation(self):
        """Test content is properly truncated when too long."""
        config = SummaryConfig(max_content_length=100)
        summarizer = ContentSummarizer(config)
        
        # Create content longer than max length
        long_content = "This is a test sentence. " * 10  # ~250 characters
        
        # Mock the summarization method to test truncation
        with patch.object(summarizer, '_summarize_content_directly', new_callable=AsyncMock) as mock_summarize:
            mock_summarize.return_value = "Test summary"
            
            # This should trigger truncation
            result = asyncio.run(summarizer.summarize_content(long_content))
            
            # Check that content was truncated
            call_args = mock_summarize.call_args
            truncated_content = call_args[0][0]  # First argument is content
            assert len(truncated_content) <= 100
            assert "[Content truncated for summarization]" in truncated_content
    
    def test_content_no_truncation(self):
        """Test short content is not truncated."""
        config = SummaryConfig(max_content_length=1000)
        summarizer = ContentSummarizer(config)
        
        short_content = "This is a short test."
        
        with patch.object(summarizer, '_summarize_content_directly', new_callable=AsyncMock) as mock_summarize:
            mock_summarize.return_value = "Test summary"
            
            result = asyncio.run(summarizer.summarize_content(short_content))
            
            # Check that content was not truncated
            call_args = mock_summarize.call_args
            content = call_args[0][0]
            assert content == short_content
    
    def test_prompt_building(self):
        """Test summary prompts are built correctly."""
        config = SummaryConfig(summary_length=SummaryLength.MEDIUM)
        summarizer = ContentSummarizer(config)
        
        content = "Test content here."
        title = "Test Title"
        url = "https://example.com"
        
        prompt = summarizer._build_summary_prompt(content, title, url)
        
        assert "Test content here." in prompt
        assert "Test Title" in prompt
        assert "https://example.com" in prompt
        assert "1-2 paragraphs" in prompt
        assert "Most relevant details for the reader" in prompt


class TestSummarizationService:
    """Test the summarization service integration."""
    
    @pytest.fixture
    def mock_summarizer(self):
        """Create a mock summarizer for testing."""
        mock = Mock(spec=ContentSummarizer)
        mock.summarize_content = AsyncMock(return_value="Test summary")
        return mock
    
    @pytest.fixture
    def mock_parser(self):
        """Create a mock parser for testing."""
        mock = Mock()
        mock.get_content = Mock(return_value={
            "content": "Test content",
            "title": "Test Title",
            "content_length": 100
        })
        return mock
    
    @pytest.mark.asyncio
    async def test_service_initialization(self):
        """Test service can be initialized."""
        service = SummarizationService()
        assert service.summarizer is not None
        assert service.parser is not None
    
    @pytest.mark.asyncio
    async def test_summarize_single_url_success(self, mock_summarizer, mock_parser):
        """Test successful URL summarization."""
        with patch('src.summarizer.service.PageParser', return_value=mock_parser):
            with patch('src.summarizer.service.ContentSummarizer', return_value=mock_summarizer):
                service = SummarizationService()
                
                result = await service.summarize_single_url(
                    "https://example.com",
                    "Test Title"
                )
                
                assert result == "Test summary"
                mock_parser.get_content.assert_called_once_with("https://example.com")
                mock_summarizer.summarize_content.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_summarize_single_url_no_content(self, mock_summarizer, mock_parser):
        """Test URL summarization when no content is extracted."""
        mock_parser.get_content.return_value = {"content": "", "title": "Test"}
        
        with patch('src.summarizer.service.PageParser', return_value=mock_parser):
            with patch('src.summarizer.service.ContentSummarizer', return_value=mock_summarizer):
                service = SummarizationService()
                
                result = await service.summarize_single_url("https://example.com")
                
                assert result is None
                mock_summarizer.summarize_content.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_summarize_search_results(self, mock_summarizer, mock_parser):
        """Test search results summarization."""
        search_results = [
            {"title": "Result 1", "url": "https://example1.com"},
            {"title": "Result 2", "url": "https://example2.com"},
            {"title": "Result 3", "url": "https://example3.com"}
        ]
        
        with patch('src.summarizer.service.PageParser', return_value=mock_parser):
            with patch('src.summarizer.service.ContentSummarizer', return_value=mock_summarizer):
                service = SummarizationService()
                
                results = await service.summarize_search_results(
                    search_results,
                    max_summaries=2
                )
                
                # Should have 2 summarized results and 1 without summary
                assert len(results) == 3
                assert "summary" in results[0]
                assert "summary" in results[1]
                assert "summary" not in results[2]
                assert results[0]["summary"] == "Test summary"
                assert results[1]["summary"] == "Test summary"


if __name__ == "__main__":
    pytest.main([__file__])
