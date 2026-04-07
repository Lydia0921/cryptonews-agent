import logging
import os
import threading
from contextlib import asynccontextmanager

from apscheduler.schedulers.background import BackgroundScheduler
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

logger = logging.getLogger(__name__)

load_dotenv()

from database import init_db
from routers.news import router as news_router
from routers.qa import router as qa_router
from routers.prices import router as prices_router

MONITOR_INTERVAL = int(os.getenv("MONITOR_INTERVAL", "30"))
DEFAULT_KEYWORDS = ["SEC", "ETF", "bitcoin", "ethereum", "regulation"]

scheduler = BackgroundScheduler()


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()

    import agents.monitor_agent as monitor_agent
    scheduler.add_job(
        monitor_agent.run,
        "interval",
        minutes=MONITOR_INTERVAL,
        args=[DEFAULT_KEYWORDS],
        id="news_monitor",
    )
    scheduler.start()

    next_run = scheduler.get_job("news_monitor").next_run_time
    logger.info("Next scheduled run: %s", next_run)

    def _initial_fetch():
        logger.info("Running initial news fetch in background...")
        stats = monitor_agent.run(DEFAULT_KEYWORDS)
        logger.info("Initial fetch done: %s", stats)

    threading.Thread(target=_initial_fetch, daemon=True).start()

    yield

    scheduler.shutdown()


app = FastAPI(title="Crypto News Monitor", lifespan=lifespan)

app.include_router(news_router)
app.include_router(qa_router)
app.include_router(prices_router)

app.mount("/", StaticFiles(directory="static", html=True), name="static")
