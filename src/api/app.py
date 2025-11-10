from contextlib import asynccontextmanager
import contextlib
import logging
import asyncio

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import redis.asyncio as redis
from apscheduler.schedulers import asyncio as apscheduler

from src.api.routes import search
from src.worker import scheduler as scheduler_worker
from src.worker import worker
from src.api.routes import exchange_rates
from src.api import dependencies
from src.client.alpha import client as alpha_client
from src.client.betta import client as betta_client

log = logging.getLogger("uvicorn.error")


@asynccontextmanager
async def lifespan(app: FastAPI):
    config = dependencies.get_config()
    app.state.config = config
    # On startup: Create Redis connection pool
    redis_pool = redis.ConnectionPool.from_url(
        config.get("REDIS_URL", "redis://localhost:6379/0"),
        decode_responses=True
    )
    app.state.redis = redis.Redis(connection_pool=redis_pool)
    log.info("Redis connection pool created.")

    nb_client = dependencies.get_national_bank_client(config)
    app.state.alpha_client = alpha_client.AlphaClient(config)
    app.state.betta_client = betta_client.BettaClient(config)
    log.info("National Bank Client initialized.")

    try:
        rates = nb_client.get_exchange_rates()
        rates_json = rates.model_dump_json()
        log.info("Fetched initial exchange rates from National Bank.")
        await app.state.redis.set("exchange_rates", rates_json)
        log.info("Initial exchange rates stored in Redis.")

    except Exception as e:
        log.error(f"Error fetching initial exchange rates: {str(e)}")   


    scheduler = apscheduler.AsyncIOScheduler()
    scheduler.start()
    log.info("Scheduler started.")

    scheduler.add_job(
        scheduler_worker.refresh_exchange_rates_job, 
        "cron", 
        hour=12,
        minute=0,
        args=[app]
    )

    app.state.scheduler = scheduler

    app.state.search_consumer = asyncio.create_task(
        worker.search_requests_consumer(
            redis_client=app.state.redis,
            alpha_client=app.state.alpha_client,
            betta_client=app.state.betta_client,
        )
    )
    log.info("Search request consumer task started.")


    yield  # The application is now running
    

    # On shutdown: stop background workers first
    app.state.search_consumer.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await app.state.search_consumer
    log.info("Search request consumer stopped.")

    await app.state.alpha_client.close()
    await app.state.betta_client.close()
    log.info("Provider clients closed.")
    
    await app.state.redis.aclose()
    log.info("Redis connection pool closed.")

    app.state.scheduler.shutdown()
    log.info("Scheduler shut down.")



def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Ticket Search API",
        description="API for exchange rates and ticket search functionality",
        version="0.1.0",
        lifespan=lifespan
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(exchange_rates.router, prefix="/api/v1", tags=["exchange-rates"])
    app.include_router(search.router, prefix="/api/v1")


    @app.get("/")
    async def root():
        return {
            "message": "Welcome to Ticket Search API",
            "version": "0.1.0",
            "docs": "/docs"
        }

    @app.get("/health")
    async def health_check():
        return {"status": "healthy"}

    return app


app = create_app()
