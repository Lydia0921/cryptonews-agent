from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
import httpx

from database import get_db
from models import NewsArticle

router = APIRouter(prefix="/api", tags=["prices"])

DEFAULTS = ["BTC", "ETH", "SOL", "XRP"]

# CoinGecko ID mapping — add more as needed
SYMBOL_TO_ID = {
    "BTC": "bitcoin",
    "ETH": "ethereum",
    "SOL": "solana",
    "XRP": "ripple",
    "DOGE": "dogecoin",
    "BNB": "binancecoin",
    "ADA": "cardano",
    "ONDO": "ondo-finance",
    "ELON": "dogelon-mars",
    "AVAX": "avalanche-2",
    "LINK": "chainlink",
    "DOT": "polkadot",
    "MATIC": "matic-network",
    "LTC": "litecoin",
    "UNI": "uniswap",
}


@router.get("/prices")
def get_prices(db: Session = Depends(get_db)):
    rows = (
        db.query(NewsArticle.coin_symbol)
        .filter(NewsArticle.coin_symbol.isnot(None))
        .distinct()
        .all()
    )
    db_symbols = {r[0].upper() for r in rows}
    symbols = list(dict.fromkeys(DEFAULTS + sorted(db_symbols - set(DEFAULTS))))

    # only fetch symbols we have a CoinGecko ID for
    known = [(s, SYMBOL_TO_ID[s]) for s in symbols if s in SYMBOL_TO_ID]
    if not known:
        return []

    ids = ",".join(cg_id for _, cg_id in known)
    try:
        res = httpx.get(
            "https://api.coingecko.com/api/v3/simple/price",
            params={"ids": ids, "vs_currencies": "usd", "include_24hr_change": "true"},
            timeout=10,
        )
        res.raise_for_status()
        data = res.json()
    except Exception:
        return []

    result = []
    for symbol, cg_id in known:
        if cg_id not in data:
            continue
        entry = data[cg_id]
        result.append({
            "symbol": symbol,
            "price_usd": entry.get("usd"),
            "change_24h": entry.get("usd_24h_change"),
        })

    return result
