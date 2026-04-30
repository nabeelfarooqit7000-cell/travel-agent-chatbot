from pydantic import BaseModel, Field


class AdminSetupStatusResponse(BaseModel):
    initialized: bool
    company_name: str = ""
    updated_at: str = ""


class AdminInitializeRequest(BaseModel):
    company_name: str = Field(min_length=2)
    admin_email: str | None = None


class KnowledgeUpdateRequest(BaseModel):
    faqs: list[dict] = Field(default_factory=list)
    terms_and_conditions: str = Field(min_length=4)
    refund_policy: str = Field(min_length=4)
    exchange_charges: str = Field(min_length=4)
    refund_charges: str = Field(min_length=4)


class KnowledgePayloadResponse(BaseModel):
    initialized: bool
    company: dict
    faqs: list[dict]
    policies: dict
    updated_at: str
