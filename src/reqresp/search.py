import enum
from typing import Optional, List
from uuid import UUID
from datetime import datetime
import uuid
from pydantic import BaseModel, Field, RootModel


class SearchStatus(str, enum.Enum):
    PENDING = "pending"
    COMPLETED = "completed"
    ERROR = "error"


class RedisSearchRequest(BaseModel):
    search_id: str = Field(..., description="Unique identifier for the search request")


class SearchResponse(BaseModel):
    search_id: UUID = Field(default_factory=uuid.uuid4, description="Unique identifier for the search request", )
    status: SearchStatus = Field(SearchStatus.PENDING, description="Status of the search operation")
    message: Optional[str] = Field(default=None, description="Additional message or details", exclude_if=lambda value: value is None or value == "")
    items: Optional[List["SearchResult"]] = Field(default_factory=list, description="List of search result items", exclude_if=lambda value: value is None or len(value) == 0)


class RedisSearchResponse(RootModel[List[SearchResponse]]):
    root : List[SearchResponse]

    def __iter__(self):
        return iter(self.root)
    
    def __getitem__(self, item):
        return self.root[item]
    

class AirportInfo(BaseModel):
    at: datetime = Field(..., description="Departure or arrival time")
    airport: str = Field(..., description="Airport code")


class Segment(BaseModel):
    operating_airline: str = Field(..., description="Operating airline code")
    marketing_airline: str = Field(..., description="Marketing airline code")
    flight_number: str = Field(..., description="Flight number")
    equipment: Optional[str] = Field(None, description="Aircraft equipment")
    dep: AirportInfo = Field(..., description="Departure information")
    arr: AirportInfo = Field(..., description="Arrival information")
    baggage: Optional[str] = Field(None, description="Baggage allowance")


class Flight(BaseModel):
    duration: int = Field(..., description="Flight duration in seconds")
    segments: List[Segment] = Field(..., description="Flight segments")


class Pricing(BaseModel):
    total: float = Field(..., description="Total price")
    base: float = Field(..., description="Base price")
    taxes: float = Field(..., description="Taxes amount")
    currency: str = Field(..., description="Currency code")


class Price(BaseModel):
    amount: float = Field(..., description="Price amount")
    currency: str = Field(..., description="Currency code")


class SearchResult(BaseModel):
    flights: List[Flight] = Field(..., description="List of flights")
    refundable: bool = Field(..., description="Whether the ticket is refundable")
    validating_airline: str = Field(..., description="Validating airline code")
    pricing: Pricing = Field(..., description="Pricing information")
    price: Optional[Price] = Field(None, description="Price information", exclude_if=lambda value: value is None)


class AlphaSearchResponse(RootModel[List[SearchResult]]):
    root: List[SearchResult]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]
    

class BettaSearchResponse(RootModel[List[SearchResult]]):
    root: List[SearchResult]

    def __iter__(self):
        return iter(self.root)

    def __getitem__(self, item):
        return self.root[item]