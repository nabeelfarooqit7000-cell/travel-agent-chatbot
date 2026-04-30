from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from app.config import get_settings
from app.data.site_content import SITE_FAQS


DEFAULT_TERMS = (
    "All bookings are subject to airline fare rules, supplier policies, and applicable taxes. "
    "Prices can change until ticketing is completed."
)
DEFAULT_REFUND_POLICY = (
    "Refund eligibility depends on fare conditions. Non-refundable fares may only return unused taxes, "
    "while refundable fares may include cancellation fees."
)
DEFAULT_EXCHANGE_CHARGES = (
    "Exchange charges include airline change fees plus any fare difference at the time of reissue."
)
DEFAULT_REFUND_CHARGES = (
    "Refund charges can include supplier cancellation penalties and service fees based on fare rules."
)


class KnowledgeStore:
    def __init__(self) -> None:
        self.settings = get_settings()
        self.path = Path(self.settings.knowledge_json_path)

    def load(self) -> dict[str, Any]:
        if not self.path.exists():
            return self._default_payload(initialized=False)
        with self.path.open("r", encoding="utf-8") as handle:
            data = json.load(handle)
        return self._normalize_payload(data)

    def save(self, payload: dict[str, Any]) -> dict[str, Any]:
        normalized = self._normalize_payload(payload)
        normalized["updated_at"] = self._timestamp()
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_path = self.path.with_suffix(".tmp")
        with tmp_path.open("w", encoding="utf-8") as handle:
            json.dump(normalized, handle, indent=2)
        tmp_path.replace(self.path)
        return normalized

    def initialize(self, company_name: str, admin_email: str | None = None) -> dict[str, Any]:
        payload = self._default_payload(initialized=True)
        payload["company"] = {"name": company_name.strip(), "admin_email": (admin_email or "").strip()}
        return self.save(payload)

    def update_content(
        self,
        faqs: list[dict[str, Any]],
        terms_and_conditions: str,
        refund_policy: str,
        exchange_charges: str,
        refund_charges: str,
    ) -> dict[str, Any]:
        current = self.load()
        current["initialized"] = True
        current["faqs"] = self._normalize_faqs(faqs)
        current["policies"] = {
            "terms_and_conditions": terms_and_conditions.strip(),
            "refund_policy": refund_policy.strip(),
            "exchange_charges": exchange_charges.strip(),
            "refund_charges": refund_charges.strip(),
        }
        return self.save(current)

    def _normalize_payload(self, payload: dict[str, Any]) -> dict[str, Any]:
        base = self._default_payload(initialized=bool(payload.get("initialized")))
        base["company"] = {
            "name": str(payload.get("company", {}).get("name", "")).strip(),
            "admin_email": str(payload.get("company", {}).get("admin_email", "")).strip(),
        }
        base["faqs"] = self._normalize_faqs(payload.get("faqs") or [])
        policies = payload.get("policies") or {}
        base["policies"] = {
            "terms_and_conditions": str(policies.get("terms_and_conditions", DEFAULT_TERMS)).strip(),
            "refund_policy": str(policies.get("refund_policy", DEFAULT_REFUND_POLICY)).strip(),
            "exchange_charges": str(policies.get("exchange_charges", DEFAULT_EXCHANGE_CHARGES)).strip(),
            "refund_charges": str(policies.get("refund_charges", DEFAULT_REFUND_CHARGES)).strip(),
        }
        base["updated_at"] = str(payload.get("updated_at") or self._timestamp())
        return base

    def _normalize_faqs(self, faqs: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for item in faqs:
            answer = str(item.get("answer", "")).strip()
            if not answer:
                continue
            keywords = item.get("keywords") or []
            normalized_keywords = [str(keyword).strip() for keyword in keywords if str(keyword).strip()]
            normalized.append(
                {
                    "topic": str(item.get("topic", "general")).strip() or "general",
                    "keywords": normalized_keywords,
                    "answer": answer,
                }
            )
        return normalized or SITE_FAQS

    def _default_payload(self, initialized: bool) -> dict[str, Any]:
        return {
            "initialized": initialized,
            "company": {"name": "", "admin_email": ""},
            "faqs": SITE_FAQS,
            "policies": {
                "terms_and_conditions": DEFAULT_TERMS,
                "refund_policy": DEFAULT_REFUND_POLICY,
                "exchange_charges": DEFAULT_EXCHANGE_CHARGES,
                "refund_charges": DEFAULT_REFUND_CHARGES,
            },
            "updated_at": self._timestamp(),
        }

    def _timestamp(self) -> str:
        return datetime.now(timezone.utc).isoformat()
