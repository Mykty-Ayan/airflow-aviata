import logging

import fastapi

from src.reqresp import search
from src.api import dependencies

log = logging.getLogger("uvicorn.error")





async def search_tickets_job(app: fastapi.FastAPI):
    log.info("SCHEDULER: Running scheduled job to search tickets.")

    try:
        alpha_client = dependencies.get_provider_alpha_client(app)
        log.info("SCHEDULER: Alpha Client initialized.")

        search_response: search.AlphaSearchResponse = await alpha_client.search()
        log.info(f"SCHEDULER: Fetched {len(search_response.root)} tickets from Alpha provider.")
        
        # Here you can add code to process/store the search_response as needed

    except Exception as e:
        log.error(f"SCHEDULER: Ticket search job failed: {e}")

    log.info("SCHEDULER: Ticket search job completed successfully.")