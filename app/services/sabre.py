from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any

import httpx

from app.config import get_settings
from app.schemas.fares import FareOption, FareSearchRequest, FareSearchResponse


class SabreAPIError(Exception):
    pass


@dataclass
class SabreToken:
    access_token: str
    token_type: str = "Bearer"


class SabreTravelService:
    def __init__(self) -> None:
        self.settings = get_settings()

    async def search_best_fares(self, request: FareSearchRequest) -> FareSearchResponse:
        offers = await self._search_offers(request)
        options = self._rank_offers(offers, limit=request.max_results)

        if not options:
            message = (
                f"No fares were returned by Sabre for {request.origin} to {request.destination} on "
                f"{request.departure_date.isoformat()}."
            )
        else:
            best = options[0]
            message = (
                f"Found {len(options)} fare option(s). Best current fare starts at "
                f"{best.total_price:.2f} {best.currency}."
            )

        return FareSearchResponse(query=request, options=options, message=message)

    async def _search_offers(self, request: FareSearchRequest) -> list[dict[str, Any]]:
        if not self.settings.sabre_client_id or not self.settings.sabre_client_secret:
            raise SabreAPIError("Sabre credentials are missing. Configure SABRE_CLIENT_ID and SABRE_CLIENT_SECRET.")

        token = await self._get_token()
        payload = self._build_search_payload(request)

        async with httpx.AsyncClient(timeout=self.settings.sabre_timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.sabre_base_url}{self.settings.sabre_flight_shop_path}",
                json=payload,
                headers={
                    "Authorization": f"{token.token_type} {token.access_token}",
                    "Content-Type": "application/json",
                },
            )

        if response.status_code >= 400:
            raise SabreAPIError(f"Sabre fare search failed with status {response.status_code}: {response.text}")

        data = response.json()
        offers = data.get("data") or data.get("offers") or []
        if not isinstance(offers, list):
            raise SabreAPIError("Sabre response did not contain a valid offers list.")

        return offers

    async def _get_token(self) -> SabreToken:
        async with httpx.AsyncClient(timeout=self.settings.sabre_timeout_seconds) as client:
            response = await client.post(
                self.settings.sabre_auth_url,
                data={"grant_type": "client_credentials"},
                auth=(self.settings.sabre_client_id, self.settings.sabre_client_secret),
                headers={"Content-Type": "application/x-www-form-urlencoded"},
            )

        if response.status_code >= 400:
            raise SabreAPIError(f"Sabre token request failed with status {response.status_code}: {response.text}")

        data = response.json()
        access_token = data.get("access_token")
        token_type = data.get("token_type", "Bearer")
        if not access_token:
            raise SabreAPIError("Sabre token response did not include access_token.")

        return SabreToken(access_token=access_token, token_type=token_type)

    def _build_search_payload(self, request: FareSearchRequest) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "originDestinations": [
                {
                    "id": "1",
                    "originLocationCode": request.origin,
                    "destinationLocationCode": request.destination,
                    "departureDateTimeRange": {"date": request.departure_date.isoformat()},
                }
            ],
            "travelers": self._build_travelers(request),
            "sources": ["GDS"],
            "searchCriteria": {
                "maxFlightOffers": request.max_results,
                "pricingOptions": {"currencyCode": request.currency},
            },
        }

        if request.return_date:
            payload["originDestinations"].append(
                {
                    "id": "2",
                    "originLocationCode": request.destination,
                    "destinationLocationCode": request.origin,
                    "departureDateTimeRange": {"date": request.return_date.isoformat()},
                }
            )

        return payload

    def _build_travelers(self, request: FareSearchRequest) -> list[dict[str, Any]]:
        travelers: list[dict[str, Any]] = []
        traveler_id = 1

        traveler_id = self._append_travelers(travelers, traveler_id, request.adults, "ADULT")
        traveler_id = self._append_travelers(travelers, traveler_id, request.children, "CHILD")
        self._append_travelers(travelers, traveler_id, request.infants, "HELD_INFANT")

        return travelers

    def _append_travelers(
        self,
        travelers: list[dict[str, Any]],
        start_id: int,
        count: int,
        traveler_type: str,
    ) -> int:
        current_id = start_id
        for _ in range(count):
            travelers.append({"id": str(current_id), "travelerType": traveler_type})
            current_id += 1
        return current_id

    def _rank_offers(self, offers: list[dict[str, Any]], limit: int) -> list[FareOption]:
        normalized = [self._normalize_offer(offer) for offer in offers]
        filtered = [offer for offer in normalized if offer is not None]
        filtered.sort(key=lambda offer: (offer.total_price, offer.number_of_stops or 99))

        ranked: list[FareOption] = []
        for index, offer in enumerate(filtered[:limit], start=1):
            ranked.append(offer.model_copy(update={"rank": index}))

        return ranked

    def _normalize_offer(self, offer: dict[str, Any]) -> FareOption | None:
        price_data = offer.get("price") or {}
        total = price_data.get("total")
        currency = price_data.get("currency") or "USD"

        if total is None:
            return None

        itineraries = offer.get("itineraries") or []
        first_segment = self._extract_first_segment(itineraries)
        last_segment = self._extract_last_segment(itineraries)
        segments = self._flatten_segments(itineraries)
        number_of_stops = max(len(segments) - 1, 0) if segments else None

        traveler_pricings = offer.get("travelerPricings") or []
        fare_details = traveler_pricings[0].get("fareDetailsBySegment") if traveler_pricings else []
        cabin = fare_details[0].get("cabin") if fare_details else None

        return FareOption(
            rank=0,
            total_price=float(total),
            currency=currency,
            validating_carrier=(offer.get("validatingAirlineCodes") or [None])[0],
            cabin=cabin,
            number_of_stops=number_of_stops,
            departure_airport=self._lookup_code(first_segment, "departure"),
            arrival_airport=self._lookup_code(last_segment, "arrival"),
            departure_time=self._lookup_time(first_segment, "departure"),
            arrival_time=self._lookup_time(last_segment, "arrival"),
            booking_link_hint="Pass raw_offer_id into your booking flow or store the mapped Sabre offer payload.",
            raw_offer_id=offer.get("id"),
        )

    def _flatten_segments(self, itineraries: list[dict[str, Any]]) -> list[dict[str, Any]]:
        segments: list[dict[str, Any]] = []
        for itinerary in itineraries:
            segments.extend(itinerary.get("segments") or [])
        return segments

    def _extract_first_segment(self, itineraries: list[dict[str, Any]]) -> dict[str, Any] | None:
        for itinerary in itineraries:
            segments = itinerary.get("segments") or []
            if segments:
                return segments[0]
        return None

    def _extract_last_segment(self, itineraries: list[dict[str, Any]]) -> dict[str, Any] | None:
        for itinerary in reversed(itineraries):
            segments = itinerary.get("segments") or []
            if segments:
                return segments[-1]
        return None

    def _lookup_code(self, segment: dict[str, Any] | None, field_name: str) -> str | None:
        if not segment:
            return None
        point = segment.get(field_name) or {}
        return point.get("iataCode")

    def _lookup_time(self, segment: dict[str, Any] | None, field_name: str) -> str | None:
        if not segment:
            return None
        point = segment.get(field_name) or {}
        return point.get("at")
