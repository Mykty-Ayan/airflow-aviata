import logging

import fastapi

from src.api import dependencies


log = logging.getLogger("uvicorn.error")


async def refresh_exchange_rates_job(app: fastapi.FastAPI):
    log.info("SCHEDULER: Running scheduled job to refresh exchange rates.")

    try:
        config = dependencies.get_config()
        nb_client = dependencies.get_national_bank_client(config)
        log.info("SCHEDULER: National Bank Client initialized.")

        rates = nb_client.get_exchange_rates()
        rates_json = rates.model_dump_json()
        log.info("SCHEDULER: Fetched exchange rates from National Bank.")
        await app.state.redis.set("exchange_rates", rates_json)
        log.info("SCHEDULER: Updated exchange rates in Redis.")
    except Exception as e:
        log.error(f"SCHEDULER: Job failed: {e}")

    log.info("SCHEDULER: Job completed successfully.")