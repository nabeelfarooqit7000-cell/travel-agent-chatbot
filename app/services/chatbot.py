from __future__ import annotations

import re
from datetime import date

from app.schemas.chat import ChatRequest, ChatResponse
from app.schemas.fares import FareOption, FareSearchRequest
from app.services.knowledge import WebsiteKnowledgeService
from app.services.sabre import SabreTravelService


class TravelChatbotService:
    def __init__(
        self,
        sabre_service: SabreTravelService,
        knowledge_service: WebsiteKnowledgeService | None = None,
    ) -> None:
        self.sabre_service = sabre_service
        self.knowledge_service = knowledge_service or WebsiteKnowledgeService()

    async def reply(self, request: ChatRequest) -> ChatResponse:
        trip = request.trip or self._extract_trip_from_message(request.message)

        if trip:
            fare_response = await self.sabre_service.search_best_fares(trip)
            answer = self._build_answer(trip, fare_response.options)
            return ChatResponse(answer=answer, detected_trip=trip, fares=fare_response.options)

        knowledge_answer = self.knowledge_service.answer(request.message)
        if knowledge_answer:
            return ChatResponse(answer=knowledge_answer, detected_trip=None, fares=[])

        if not trip:
            return ChatResponse(
                answer=(
                    "I can help with Sabre fare searches and common website questions such as refund policy, "
                    "changes, baggage, payments, and support details. For fare shopping, please share origin, "
                    "destination, departure date, and passenger count."
                ),
                detected_trip=None,
                fares=[],
            )

    def _build_answer(self, trip: FareSearchRequest, fares: list[FareOption]) -> str:
        if not fares:
            return (
                f"I could not find fares from {trip.origin} to {trip.destination} for "
                f"{trip.departure_date.isoformat()}. Try different dates or nearby airports."
            )

        top = fares[0]
        return (
            f"The best fare I found from {trip.origin} to {trip.destination} starts at "
            f"{top.total_price:.2f} {top.currency}. I also returned {len(fares)} ranked option(s) "
            f"so your booking team can finalize the reservation."
        )

    def _extract_trip_from_message(self, message: str) -> FareSearchRequest | None:
        upper_message = message.upper()
        airports = re.findall(r"\b[A-Z]{3}\b", upper_message)
        dates = re.findall(r"\b\d{4}-\d{2}-\d{2}\b", message)
        adults_match = re.search(r"(\d+)\s+ADULT", upper_message)
        currency_match = re.search(r"\b(USD|EUR|GBP|SAR|AED|PKR)\b", upper_message)

        if len(airports) < 2 or not dates:
            return None

        departure_date = date.fromisoformat(dates[0])
        return_date = date.fromisoformat(dates[1]) if len(dates) > 1 else None
        adults = int(adults_match.group(1)) if adults_match else 1
        currency = currency_match.group(1) if currency_match else "USD"

        return FareSearchRequest(
            origin=airports[0],
            destination=airports[1],
            departure_date=departure_date,
            return_date=return_date,
            adults=adults,
            currency=currency,
        )
