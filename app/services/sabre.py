from __future__ import annotations

import base64
from dataclasses import dataclass
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
        headers = {
            "Authorization": f"{token.token_type} {token.access_token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        cpa_id = self._effective_cpa_id()
        if cpa_id:
            headers["X-CPAID"] = cpa_id

        async with httpx.AsyncClient(timeout=self.settings.sabre_timeout_seconds) as client:
            response = await client.post(
                f"{self.settings.sabre_base_url}{self.settings.sabre_flight_shop_path}",
                json=payload,
                headers=headers,
            )

        if response.status_code >= 400:
            raise SabreAPIError(f"Sabre fare search failed with status {response.status_code}: {response.text}")

        data = response.json()
        offers = data.get("data") or data.get("offers") or self._extract_grouped_itinerary_offers(data)
        if not isinstance(offers, list):
            raise SabreAPIError("Sabre response did not contain a valid offers list.")

        return offers

    async def _get_token(self) -> SabreToken:
        async with httpx.AsyncClient(timeout=self.settings.sabre_timeout_seconds) as client:
            basic = self._build_nested_basic_token(
                self.settings.sabre_client_id,
                self.settings.sabre_client_secret,
            )
            response = await client.post(
                self.settings.sabre_auth_url,
                data={"grant_type": "client_credentials"},
                headers={
                    "Authorization": f"Basic {basic}",
                    "Content-Type": "application/x-www-form-urlencoded",
                },
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
        pcc = self._effective_pcc()
        segments = [
            self._build_origin_destination_segment(
                request.origin,
                request.destination,
                request.departure_date.isoformat(),
                "1",
            )
        ]

        if request.return_date:
            segments.append(
                self._build_origin_destination_segment(
                    request.destination,
                    request.origin,
                    request.return_date.isoformat(),
                    "2",
                )
            )

        payload: dict[str, Any] = {
            "OTA_AirLowFareSearchRQ": {
                "Version": "5",
                "AvailableFlightsOnly": True,
                "ResponseType": "OTA",
                "OriginDestinationInformation": segments,
                "POS": {
                    "Source": [
                        {
                            "PseudoCityCode": pcc,
                            "RequestorID": {
                                "CompanyName": {"Code": self.settings.sabre_requestor_company_code},
                                "ID": "1",
                                "Type": "1",
                            },
                            "ISOCountry": self.settings.sabre_iso_country,
                            "ISOCurrency": request.currency,
                        }
                    ]
                },
                "TravelPreferences": {
                    "ETicketDesired": True,
                    "ValidInterlineTicket": True,
                    "MaxStopsQuantity": 2,
                    "TPA_Extensions": {
                        "DataSources": {
                            "ATPCO": "Enable",
                            "LCC": "Enable",
                            "NDC": "Disable",
                        },
                        "TripType": {"Value": "Return" if request.return_date else "OneWay"},
                    },
                },
                "TravelerInfoSummary": {
                    "AirTravelerAvail": [{"PassengerTypeQuantity": self._build_passenger_type_quantities(request)}],
                    "PriceRequestInformation": {
                        "CurrencyCode": request.currency,
                        "NegotiatedFaresOnly": False,
                        "ProcessThruFaresOnly": True,
                    },
                    "SpecificPTC_Indicator": True,
                    "SeatsRequested": [request.adults + request.children + request.infants],
                },
                "TPA_Extensions": {
                    "IntelliSellTransaction": {"RequestType": {"Name": "200ITINS"}},
                },
            },
        }
        return payload

    def _build_nested_basic_token(self, client_id: str, client_secret: str) -> str:
        encoded_id = base64.b64encode(client_id.encode("utf-8")).decode("utf-8")
        encoded_secret = base64.b64encode(client_secret.encode("utf-8")).decode("utf-8")
        return base64.b64encode(f"{encoded_id}:{encoded_secret}".encode("utf-8")).decode("utf-8")

    def _effective_cpa_id(self) -> str:
        return self.settings.sabre_cpa_id or self.settings.sabre_client_id

    def _effective_pcc(self) -> str:
        if self.settings.sabre_pcc:
            return self.settings.sabre_pcc
        parts = self.settings.sabre_client_id.split(":")
        return parts[2] if len(parts) >= 3 else ""

    def _build_origin_destination_segment(self, origin: str, destination: str, departure_date: str, rph: str) -> dict[str, Any]:
        return {
            "DepartureDateTime": f"{departure_date}T00:00:00",
            "DepartureWindow": "00002359",
            "OriginLocation": {"LocationCode": origin},
            "DestinationLocation": {"LocationCode": destination},
            "RPH": rph,
            "TPA_Extensions": {
                "SegmentType": {"Code": "O"},
            },
        }

    def _build_passenger_type_quantities(self, request: FareSearchRequest) -> list[dict[str, Any]]:
        passenger_quantities = [
            {"Code": "ADT", "Quantity": request.adults},
            {"Code": "CNN", "Quantity": request.children},
            {"Code": "INF", "Quantity": request.infants},
        ]
        return [item for item in passenger_quantities if item["Quantity"] > 0]

    def _extract_grouped_itinerary_offers(self, data: dict[str, Any]) -> list[dict[str, Any]]:
        grouped = data.get("groupedItineraryResponse") or {}
        leg_descs = {leg.get("id"): leg for leg in grouped.get("legDescs") or []}
        schedule_descs = {schedule.get("id"): schedule for schedule in grouped.get("scheduleDescs") or []}

        offers: list[dict[str, Any]] = []
        for group in grouped.get("itineraryGroups") or []:
            for itinerary in group.get("itineraries") or []:
                pricing_info = (itinerary.get("pricingInformation") or [{}])[0]
                fare = pricing_info.get("fare") or {}
                total_fare = fare.get("totalFare") or {}
                total_price = total_fare.get("totalPrice")
                if not total_price:
                    continue

                segments: list[dict[str, Any]] = []
                for leg_ref in itinerary.get("legs") or []:
                    leg = leg_descs.get(leg_ref.get("ref")) or {}
                    for sched_ref in leg.get("schedules") or []:
                        sched = schedule_descs.get(sched_ref.get("ref")) or {}
                        segments.append(
                            {
                                "departure": {
                                    "iataCode": (sched.get("departure") or {}).get("airport"),
                                    "at": (sched.get("departure") or {}).get("time"),
                                },
                                "arrival": {
                                    "iataCode": (sched.get("arrival") or {}).get("airport"),
                                    "at": (sched.get("arrival") or {}).get("time"),
                                },
                            }
                        )

                offers.append(
                    {
                        "id": f"grouped-{len(offers) + 1}",
                        "price": {"total": str(total_price), "currency": total_fare.get("currency") or "USD"},
                        "validatingAirlineCodes": [],
                        "itineraries": [{"segments": segments}] if segments else [],
                        "travelerPricings": [],
                    }
                )
        return offers

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
