"""Orchestrator: fetch → analyze → return stats."""
from dotenv import load_dotenv

load_dotenv()

from agents.fetcher_agent import fetch
from agents.analyzer_agent import analyze_and_save


def run(keywords: list[str]) -> dict:
    """Run the full monitoring pipeline.

    Returns:
        {"fetched": int, "added": int, "skipped": int}
    """
    articles = fetch(keywords)
    fetched = len(articles)

    added = analyze_and_save(articles)

    return {"fetched": fetched, "added": added, "skipped": fetched - added}


if __name__ == "__main__":
    keywords = ["SEC", "ETF", "bitcoin", "ethereum", "regulation"]
    stats = run(keywords)
    print(f"Fetched: {stats['fetched']}, Added: {stats['added']}, Skipped: {stats['skipped']}")
