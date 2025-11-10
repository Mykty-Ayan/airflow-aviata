from typing import List, Optional
from pydantic import BaseModel


class NationalBankCurrency(BaseModel):
    full_name: str
    title: str
    description: float
    quantity: int
    index: Optional[str]
    change: float


class NationalBankRate(BaseModel):
    generator: str
    title: str
    description: str
    copyright: str
    date: str
    currencies: List[NationalBankCurrency]


class NationalBankResponse(BaseModel):
    rate: NationalBankRate
