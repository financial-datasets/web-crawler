# Web Crawler

A minimal, real-time web search CLI that searches the internet for you. Enter a query and get search results as JSON (title, url, published_date), sorted by recency. Now with **LLM-powered content summarization** using GPT-4o-mini!

<img width="1162" height="628" alt="Screenshot 2025-08-25 at 12 31 22 PM" src="https://github.com/user-attachments/assets/12e05c97-4e46-4fd3-a467-3f290b63d" />

## Features

- 🔍 **Real-time web search** across multiple sources
- 📰 **Content extraction** from JavaScript-heavy pages using Playwright
- 🤖 **High-quality LLM summarization** using GPT-4o-mini (one-shot processing)
- ⚡ **Fast and efficient** with caching and rate limiting
- 🎯 **Production-ready** with robust error handling

## Setup
**Prerequisites**: Python 3.12+ and [uv](https://docs.astral.sh/uv/)

```bash
# Clone the repository
git clone https://github.com/financial-datasets/web-crawler.git

# Navigate into the project root:
cd web-crawler
```

### LLM Configuration (Optional)

To enable content summarization, you'll need an LLM API key:

1. **Copy the example config:**
   ```bash
   cp config.env.example .env
   ```

2. **Edit `.env` and add your API key:**
   ```bash
   # For OpenAI (default)
   OPENAI_API_KEY=your_actual_api_key_here
   
   # Or for Anthropic
   # ANTHROPIC_API_KEY=your_actual_api_key_here
   # LLM_PROVIDER=anthropic
   ```

3. **Load the environment variables:**
   ```bash
   source .env
   ```

## How to Run
```bash
# From the repo root, run:
uv run web-crawler
```

- When prompted, enter your search (e.g., "AAPL latest earnings transcript").
- If you have an LLM API key configured, you'll be asked if you want summaries.
- Results print as JSON with optional summaries. Enter another query to continue.
- Quit with `q`, `quit`, `exit`, or press Ctrl+C.

### Example Output with Summaries

```json
{
  "query": "AAPL latest earnings transcript",
  "summaries_generated": true,
  "results": [
    {
      "title": "Apple Q4 2024 Earnings Call Transcript",
      "url": "https://example.com/apple-earnings",
      "published_date": "2024-10-28T20:00:00",
      "summary": "Apple reported strong Q4 2024 results with revenue of $89.5 billion, up 8% year-over-year. iPhone sales grew 6% to $43.8 billion, while services revenue increased 16% to $22.3 billion. The company highlighted strong performance in emerging markets and continued growth in its services ecosystem.",
      "content_length": 15420
    }
  ]
}
```

## Roadmap
We'd love to get help on:
- [x] **Summarizing parsed content with LLMs** ✅
- [ ] Parsing content from JavaScript-heavy pages (e.g. MSN, Bloomberg, etc.)
- [ ] Adding more sources (Bing, Reddit, etc.)
- [ ] Parallelization for faster queries

## Architecture

The summarization feature works as follows:

1. **Search**: Query multiple web sources simultaneously
2. **Extract**: Use Playwright to extract readable content from URLs
3. **Summarize**: Send entire content to GPT-4o-mini via litellm for high-quality summaries
4. **Return**: Enhanced search results with AI-generated summaries

### Key Components

- **`ContentSummarizer`**: Core LLM integration using litellm with GPT-4o-mini
- **`SummarizationService`**: Orchestrates content extraction and summarization
- **`PageParser`**: Extracts readable content from web pages
- **`SearchEngine`**: Integrates search and summarization workflows

### Supported LLM Providers

- **OpenAI**: GPT-4o-mini (default), GPT-4, GPT-3.5-turbo
- **Anthropic**: Claude-3-Haiku, Claude-3-Sonnet
- **Azure OpenAI**: GPT-4o-mini, GPT-4, GPT-3.5-turbo
- **Local Models**: Via litellm's local model support

## Production Considerations

- **Rate Limiting**: Built-in semaphore-based concurrency control
- **Error Handling**: Graceful degradation when summarization fails
- **Caching**: 15-minute cache for search results
- **Timeout Management**: 60-second timeout for LLM calls
- **Content Processing**: One-shot summarization with smart content truncation (50K char limit)
- **Model Selection**: GPT-4o-mini for optimal quality/speed balance
