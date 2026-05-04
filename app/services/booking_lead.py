from __future__ import annotations

from datetime import datetime, timezone

import httpx

from app.config import get_settings
from app.schemas.leads import LeadCreateRequest
from app.services.knowledge_store import KnowledgeStore


class BookingLeadNotConfiguredError(Exception):
    pass


class BookingLeadForwardingError(Exception):
    pass


def resolve_booking_lead_url() -> str:
    settings = get_settings()
    if settings.booking_lead_url.strip():
        return settings.booking_lead_url.strip()
    store = KnowledgeStore()
    data = store.load()
    return str((data.get("integrations") or {}).get("booking_lead_url") or "").strip()


async def forward_booking_lead(request: LeadCreateRequest) -> int:
    url = resolve_booking_lead_url()
    if not url:
        raise BookingLeadNotConfiguredError(
            "Booking lead URL is not configured. Set BOOKING_LEAD_URL or admin integrations.booking_lead_url."
        )

    settings = get_settings()
    payload = {
        "source": request.source,
        "trip": request.trip.model_dump(mode="json"),
        "fare": request.fare.model_dump(mode="json"),
        "contact_email": request.contact_email,
        "notes": request.notes,
        "requested_at": datetime.now(timezone.utc).isoformat(),
    }

    headers: dict[str, str] = {"Content-Type": "application/json", "Accept": "application/json"}
    secret = settings.booking_lead_secret.strip()
    if secret:
        headers["Authorization"] = f"Bearer {secret}"

    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(url, json=payload, headers=headers)
    except httpx.RequestError as exc:
        raise BookingLeadForwardingError(f"Could not reach booking lead URL: {exc}") from exc

    if response.status_code >= 400:
        raise BookingLeadForwardingError(
            f"Booking lead endpoint returned {response.status_code}: {response.text[:800]}"
        )

    return response.status_code
