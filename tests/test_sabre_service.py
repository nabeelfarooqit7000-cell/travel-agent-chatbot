from datetime import date

from app.schemas.fares import FareSearchRequest
from app.services.sabre import SabreTravelService


def test_build_search_payload_round_trip() -> None:
    service = SabreTravelService()
    request = FareSearchRequest(
        origin="JFK",
        destination="LHR",
        departure_date=date(2026, 6, 14),
        return_date=date(2026, 6, 21),
        adults=1,
        children=1,
        currency="USD",
        max_results=5,
    )

    payload = service._build_search_payload(request)

    assert len(payload["originDestinations"]) == 2
    assert payload["searchCriteria"]["maxFlightOffers"] == 5
    assert payload["travelers"][0]["travelerType"] == "ADULT"
    assert payload["travelers"][1]["travelerType"] == "CHILD"


def test_rank_offers_sorts_by_price_then_stops() -> None:
    service = SabreTravelService()

    offers = [
        {
            "id": "offer-2",
            "price": {"total": "650.00", "currency": "USD"},
            "validatingAirlineCodes": ["SV"],
            "itineraries": [{"segments": [{"departure": {"iataCode": "JFK", "at": "2026-06-14T12:00:00"}, "arrival": {"iataCode": "LHR", "at": "2026-06-14T21:00:00"}}]}],
            "travelerPricings": [{"fareDetailsBySegment": [{"cabin": "ECONOMY"}]}],
        },
        {
            "id": "offer-1",
            "price": {"total": "500.00", "currency": "USD"},
            "validatingAirlineCodes": ["BA"],
            "itineraries": [{"segments": [{"departure": {"iataCode": "JFK", "at": "2026-06-14T10:00:00"}, "arrival": {"iataCode": "LHR", "at": "2026-06-14T20:00:00"}}]}],
            "travelerPricings": [{"fareDetailsBySegment": [{"cabin": "ECONOMY"}]}],
        },
    ]

    ranked = service._rank_offers(offers, limit=10)

    assert ranked[0].raw_offer_id == "offer-1"
    assert ranked[0].rank == 1
    assert ranked[1].rank == 2
