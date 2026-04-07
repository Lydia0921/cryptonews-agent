"""Orchestrator: fetch → analyze → return stats."""
from dotenv import load_dotenv

load_dotenv()

from agents.fetcher_agent import fetch
from agents.analyzer_agent import analyze_and_save

BTC_MONITOR_CONFIG = {
    "topic": "Bitcoin (BTC)",
    "primary_keywords": ["Bitcoin", "BTC", "比特幣"],
    "secondary_keywords": [
        "ETF", "halving", "whale", "on-chain", "Lightning Network",
        "mining", "hash rate", "礦工", "閃電網路", "Satoshi", "UTXO",
    ],
    "exclude_keywords": ["giveaway", "airdrop scam", "sponsored", "advertisement"],
    "language": "both",
    "min_relevance_score": 0.5,
}


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
    keywords = BTC_MONITOR_CONFIG["primary_keywords"]
    stats = run(keywords)
    print(f"Fetched: {stats['fetched']}, Added: {stats['added']}, Skipped: {stats['skipped']}")
