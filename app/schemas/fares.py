from datetime import date

from pydantic import BaseModel, Field, field_validator


class FareSearchRequest(BaseModel):
    origin: str = Field(min_length=3, max_length=3)
    destination: str = Field(min_length=3, max_length=3)
    departure_date: date
    return_date: date | None = None
    adults: int = Field(default=1, ge=1, le=9)
    children: int = Field(default=0, ge=0, le=9)
    infants: int = Field(default=0, ge=0, le=9)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    max_results: int = Field(default=10, ge=1, le=50)

    @field_validator("origin", "destination", "currency")
    @classmethod
    def normalize_code(cls, value: str) -> str:
        return value.upper()


class FareOption(BaseModel):
    rank: int
    total_price: float
    currency: str
    validating_carrier: str | None = None
    cabin: str | None = None
    number_of_stops: int | None = None
    departure_airport: str | None = None
    arrival_airport: str | None = None
    departure_time: str | None = None
    arrival_time: str | None = None
    booking_link_hint: str | None = None
    raw_offer_id: str | None = None


class FareSearchResponse(BaseModel):
    query: FareSearchRequest
    options: list[FareOption]
    message: str
