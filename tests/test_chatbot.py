from datetime import date

import pytest

from app.schemas.chat import ChatRequest
from app.schemas.fares import FareOption, FareSearchRequest, FareSearchResponse
from app.services.chatbot import TravelChatbotService


class FakeSabreService:
    async def search_best_fares(self, request: FareSearchRequest) -> FareSearchResponse:
        return FareSearchResponse(
            query=request,
            message="Found fares",
            options=[
                FareOption(
                    rank=1,
                    total_price=499.99,
                    currency="USD",
                    validating_carrier="BA",
                    cabin="ECONOMY",
                    number_of_stops=0,
                    departure_airport=request.origin,
                    arrival_airport=request.destination,
                    departure_time="2026-06-14T09:00:00",
                    arrival_time="2026-06-14T21:00:00",
                    raw_offer_id="offer-1",
                )
            ],
        )


@pytest.mark.asyncio
async def test_chatbot_returns_ranked_fares() -> None:
    service = TravelChatbotService(sabre_service=FakeSabreService())
    request = ChatRequest(
        message="Find cheapest fare from JFK to LHR on 2026-06-14 for 1 adult",
        trip=FareSearchRequest(
            origin="JFK",
            destination="LHR",
            departure_date=date(2026, 6, 14),
            adults=1,
            currency="USD",
        ),
    )

    response = await service.reply(request)

    assert response.detected_trip is not None
    assert response.fares
    assert response.fares[0].total_price == 499.99
    assert "best fare" in response.answer.lower()
    assert response.route_type == "sabre"


def test_chatbot_extracts_trip_from_message() -> None:
    service = TravelChatbotService(sabre_service=FakeSabreService())

    trip = service._extract_trip_from_message(
        "Need a flight from JFK to LHR on 2026-06-14 returning 2026-06-21 for 2 adults in USD"
    )

    assert trip is not None
    assert trip.origin == "JFK"
    assert trip.destination == "LHR"
    assert trip.departure_date == date(2026, 6, 14)
    assert trip.return_date == date(2026, 6, 21)
    assert trip.currency == "USD"


@pytest.mark.asyncio
async def test_chatbot_answers_refund_policy_questions() -> None:
    service = TravelChatbotService(sabre_service=FakeSabreService())

    response = await service.reply(ChatRequest(message="What is your refund policy for cancelled tickets?"))

    assert response.detected_trip is None
    assert response.fares == []
    assert "refund policy" in response.answer.lower() or "refundable" in response.answer.lower()
    assert response.route_type == "knowledge"


@pytest.mark.asyncio
async def test_chatbot_returns_general_fallback_for_unknown_question() -> None:
    service = TravelChatbotService(sabre_service=FakeSabreService())

    response = await service.reply(ChatRequest(message="Tell me something interesting"))

    assert response.detected_trip is None
    assert response.fares == []
    assert "website questions" in response.answer.lower()
    assert response.route_type == "fallback"
