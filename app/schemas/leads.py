from pydantic import BaseModel, Field

from app.schemas.fares import FareOption, FareSearchRequest


class LeadCreateRequest(BaseModel):
    trip: FareSearchRequest
    fare: FareOption
    source: str = Field(default="travel_chat", max_length=120)
    contact_email: str | None = Field(default=None, max_length=320)
    notes: str | None = Field(default=None, max_length=2000)


class LeadCreateResponse(BaseModel):
    status: str = "forwarded"
    downstream_status_code: int | None = None


class BookingLeadConfigResponse(BaseModel):
    lead_delivery_enabled: bool
