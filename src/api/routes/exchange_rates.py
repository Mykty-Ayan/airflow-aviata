import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from datetime import date
from typing import Optional
from dotenv import dotenv_values
import redis.asyncio as redis

from src.reqresp.national_bank import NationalBankResponse
from src.client.nationalbank import client
from src.api.dependencies import get_national_bank_client, get_redis_client

log = logging.getLogger("uvicorn.error")

router = APIRouter()


@router.get("/currencies")
async def list_available_currencies(
    nb_client: client.NationalBankClient = Depends(get_national_bank_client),
    redis_client: redis.Redis = Depends(get_redis_client),
):
    """
    Get list of all available currencies
    """
    try:
        cached_rates = await redis_client.get("exchange_rates")
        log.info("Fetched exchange rates from Redis cache.")
    
        if not cached_rates:
            log.info("No cached rates found in Redis. Fetching from National Bank.")
            rates_response = nb_client.get_exchange_rates()  # Fetch and cache if not present
            cached_rates = rates_response.model_dump_json()
            await redis_client.set("exchange_rates", cached_rates)
            log.info("Stored fetched exchange rates in Redis cache.")

        rates_response = NationalBankResponse.model_validate_json(cached_rates)

        currencies = [
            {
                "code": curr.title,
                "name": curr.full_name
            }
            for curr in rates_response.rate.currencies
        ]
        
        return {"currencies": currencies, "count": len(currencies)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching currencies: {str(e)}")
