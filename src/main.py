import asyncio
import json
import contextlib

from .search.engine import SearchEngine
from .summarizer.service import SummarizationService
from .utils import spinner


# Example usage
async def search(query: str, include_summaries: bool = False, max_summaries: int = 5):
    async with SearchEngine() as search_engine:
        spinner_task = asyncio.create_task(spinner("Searching the web..."))
        try:
            results = await search_engine.get_search_results(query)
        finally:
            spinner_task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await spinner_task
            print()

        # If user wants summaries, process them
        if include_summaries and results.get("results"):
            print("🤖 Generating AI summaries...")
            spinner_task = asyncio.create_task(spinner("Summarizing content..."))

            try:
                # Convert search results to format expected by SummarizationService
                search_results = []
                for result in results["results"]:
                    search_results.append({
                        "title": result["title"],
                        "url": result["url"],
                        "published_date": result["published_date"]
                    })

                # Create summarization service and process results
                summarization_service = SummarizationService()
                summarized_results = await summarization_service.summarize_search_results(
                    search_results,
                    max_summaries=max_summaries 
                )

                # Update results with summaries
                results["results"] = summarized_results

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

            # Ask user if they want summaries
            want_summaries = input("Include AI summaries? (y/n): ").strip().lower()
            include_summaries = want_summaries in {"y", "yes"}
            if include_summaries:
                max_summaries = input("Enter maximum number of summaries: ").strip()
                if max_summaries:
                    max_summaries = int(max_summaries)
                else:
                    max_summaries = 5

            asyncio.run(search(query, include_summaries, max_summaries))
    except KeyboardInterrupt:
        print()  # graceful newline on Ctrl+C


if __name__ == "__main__":
    main()