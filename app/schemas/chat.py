from typing import Literal

from pydantic import BaseModel, Field

from app.schemas.fares import FareOption, FareSearchRequest


class ChatRequest(BaseModel):
    message: str = Field(min_length=2)
    trip: FareSearchRequest | None = None


class ChatResponse(BaseModel):
    answer: str
    detected_trip: FareSearchRequest | None = None
    fares: list[FareOption] = Field(default_factory=list)
    route_type: Literal["sabre", "knowledge", "fallback"] = "fallback"
