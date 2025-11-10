

import os
from functools import lru_cache

from dotenv import dotenv_values
from fastapi import Depends
import fastapi
import redis.asyncio as redis

from src.client.nationalbank.client import NationalBankClient
from src.client.alpha.client import AlphaClient

@lru_cache
def get_config() -> dict[str, str]:
    file_config = dotenv_values(".env")
    return {**file_config, **os.environ}


def get_national_bank_client(config: dict[str, str] = Depends(get_config)) -> "NationalBankClient":
    return NationalBankClient(config)

def get_redis_client(request: fastapi.Request) -> redis.Redis:
    return request.app.state.redis

def get_provider_alpha_client(request: fastapi.Request) -> "AlphaClient":
    return request.app.state.alpha_client