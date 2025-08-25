import asyncio
import json
import os
from search.engine import SearchEngine

# Example usage
async def search():
    search_engine = SearchEngine()
    
    # Example search
    results = await search_engine.search("AAPL latest earnings transcript", max_results=5)
    
    print("Search Results:")
    print(json.dumps(results, indent=2, default=str))

def main():
    """Entry point for the web-crawler command line tool."""
    asyncio.run(search())

if __name__ == "__main__":
    main()