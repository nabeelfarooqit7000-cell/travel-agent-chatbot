import secrets

from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import HTMLResponse

from app.config import get_settings
from app.schemas.admin import (
    AdminInitializeRequest,
    AdminSetupStatusResponse,
    KnowledgePayloadResponse,
    KnowledgeUpdateRequest,
)
from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.fares import FareSearchRequest, FareSearchResponse
from app.services.chatbot import TravelChatbotService
from app.services.admin_security import AdminRateLimiter
from app.services.knowledge_store import KnowledgeStore
from app.services.sabre import SabreAPIError, SabreTravelService
from app.ui.admin_page import ADMIN_PAGE_HTML
from app.ui.demo_page import DEMO_PAGE_HTML

router = APIRouter()
admin_rate_limiter = AdminRateLimiter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/demo", response_class=HTMLResponse)
async def demo() -> HTMLResponse:
    return HTMLResponse(content=DEMO_PAGE_HTML)


@router.get("/admin", response_class=HTMLResponse)
async def admin() -> HTMLResponse:
    return HTMLResponse(content=ADMIN_PAGE_HTML)


@router.get("/api/admin/setup/status", response_model=AdminSetupStatusResponse)
async def admin_setup_status() -> AdminSetupStatusResponse:
    payload = KnowledgeStore().load()
    company = payload.get("company") or {}
    return AdminSetupStatusResponse(
        initialized=bool(payload.get("initialized")),
        company_name=str(company.get("name", "")),
        updated_at=str(payload.get("updated_at", "")),
    )


@router.post("/api/admin/setup/initialize", response_model=KnowledgePayloadResponse)
async def admin_initialize(
    payload: AdminInitializeRequest,
    request: Request,
    x_admin_key: str = Header(default="", alias="X-Admin-Key"),
) -> KnowledgePayloadResponse:
    _verify_admin_access(request, x_admin_key)
    store = KnowledgeStore()
    data = store.initialize(company_name=payload.company_name, admin_email=payload.admin_email)
    return KnowledgePayloadResponse(**data)


@router.post("/api/admin/knowledge/update", response_model=KnowledgePayloadResponse)
async def admin_update_knowledge(
    payload: KnowledgeUpdateRequest,
    request: Request,
    x_admin_key: str = Header(default="", alias="X-Admin-Key"),
) -> KnowledgePayloadResponse:
    _verify_admin_access(request, x_admin_key)
    store = KnowledgeStore()
    data = store.update_content(
        faqs=payload.faqs,
        terms_and_conditions=payload.terms_and_conditions,
        refund_policy=payload.refund_policy,
        exchange_charges=payload.exchange_charges,
        refund_charges=payload.refund_charges,
    )
    return KnowledgePayloadResponse(**data)


@router.post("/api/fares/search", response_model=FareSearchResponse)
async def search_fares(payload: FareSearchRequest) -> FareSearchResponse:
    service = SabreTravelService()

    try:
        return await service.search_best_fares(payload)
    except SabreAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


@router.post("/api/chat", response_model=ChatResponse)
async def chat(payload: ChatRequest) -> ChatResponse:
    service = TravelChatbotService(sabre_service=SabreTravelService())

    try:
        return await service.reply(payload)
    except SabreAPIError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc


def _verify_admin_access(request: Request, x_admin_key: str) -> None:
    settings = get_settings()
    client_key = request.client.host if request.client else "unknown"
    if not admin_rate_limiter.check(client_key=client_key, limit_per_minute=settings.admin_rate_limit_per_minute):
        raise HTTPException(status_code=429, detail="Too many admin requests. Try again later.")
    if not settings.admin_setup_key:
        raise HTTPException(status_code=500, detail="ADMIN_SETUP_KEY is not configured.")
    if not secrets.compare_digest(x_admin_key, settings.admin_setup_key):
        raise HTTPException(status_code=401, detail="Invalid admin key.")
