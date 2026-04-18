from fastapi import APIRouter, HTTPException
from fastapi.responses import HTMLResponse

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.fares import FareSearchRequest, FareSearchResponse
from app.services.chatbot import TravelChatbotService
from app.services.sabre import SabreAPIError, SabreTravelService
from app.ui.demo_page import DEMO_PAGE_HTML

router = APIRouter()


@router.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/demo", response_class=HTMLResponse)
async def demo() -> HTMLResponse:
    return HTMLResponse(content=DEMO_PAGE_HTML)


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
