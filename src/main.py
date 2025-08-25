import asyncio
import json
from search.engine import SearchEngine
import contextlib
from utils import spinner

# Example usage
async def search(query: str, max_results: int = 5):
    search_engine = SearchEngine()
    spinner_task = asyncio.create_task(spinner("Searching the web..."))
    try:
        results = await search_engine.search(query, max_results=max_results)
    finally:
        spinner_task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await spinner_task
        print()
    print("Search Results:")
    print(json.dumps(results, indent=2, default=str))


def main():
    """Entry point for the web-crawler command line tool."""
    try:
        while True:
            query = input("Enter search query: ").strip()
            if not query:
                print("No query entered. Try again or type 'q' to quit.")
                continue
            if query.lower() in {"q", "quit", "exit"}:
                print("Goodbye.")
                return
            asyncio.run(search(query))
    except KeyboardInterrupt:
        print()  # graceful newline on Ctrl+C


if __name__ == "__main__":
    main()