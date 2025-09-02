import asyncio
import json
import contextlib

from src.search.engine import SearchEngine
from src.utils import spinner


# Example usage
async def search(query: str):
    async with SearchEngine() as search_engine:
        spinner_task = asyncio.create_task(spinner("Searching the web..."))
        try:
            results = await search_engine.get_search_results(query)
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
        print()


if __name__ == "__main__":
    main()