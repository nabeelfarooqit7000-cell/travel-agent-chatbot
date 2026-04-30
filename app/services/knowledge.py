from __future__ import annotations

import re
from typing import Any

from app.data.site_content import SITE_FAQS
from app.services.knowledge_store import KnowledgeStore


class WebsiteKnowledgeService:
    def __init__(self, faq_entries: list[dict[str, Any]] | None = None) -> None:
        if faq_entries is not None:
            self.faq_entries = faq_entries
            return

        store = KnowledgeStore()
        payload = store.load()
        policy_entries = self._policy_entries(payload.get("policies") or {})
        self.faq_entries = (payload.get("faqs") or SITE_FAQS) + policy_entries

    def answer(self, message: str) -> str | None:
        normalized_message = self._normalize_text(message)
        message_tokens = set(normalized_message.split())

        best_answer: str | None = None
        best_score = 0

        for entry in self.faq_entries:
            keywords = entry.get("keywords") or []
            score = self._score_keywords(normalized_message, message_tokens, keywords)
            if score > best_score:
                best_score = score
                best_answer = entry.get("answer")

        return best_answer if best_score > 0 else None

    def _score_keywords(self, message: str, message_tokens: set[str], keywords: list[str]) -> int:
        score = 0
        for keyword in keywords:
            normalized_keyword = self._normalize_text(keyword)
            if " " in normalized_keyword:
                if normalized_keyword in message:
                    score += 3
                continue

            if normalized_keyword in message_tokens:
                score += 2
        return score

    def _normalize_text(self, value: str) -> str:
        lowered = value.lower()
        lowered = re.sub(r"[^a-z0-9\s]", " ", lowered)
        return re.sub(r"\s+", " ", lowered).strip()

    def _policy_entries(self, policies: dict[str, Any]) -> list[dict[str, Any]]:
        return [
            {
                "topic": "terms_and_conditions",
                "keywords": ["terms", "terms and conditions", "conditions", "booking terms", "rules"],
                "answer": str(policies.get("terms_and_conditions", "")).strip(),
            },
            {
                "topic": "refund_policy",
                "keywords": ["refund policy", "refund", "refunds", "money back", "cancellation policy"],
                "answer": str(policies.get("refund_policy", "")).strip(),
            },
            {
                "topic": "exchange_charges",
                "keywords": ["exchange charges", "change charges", "reissue fee", "change fee"],
                "answer": str(policies.get("exchange_charges", "")).strip(),
            },
            {
                "topic": "refund_charges",
                "keywords": ["refund charges", "cancellation charges", "refund fee", "penalty"],
                "answer": str(policies.get("refund_charges", "")).strip(),
            },
        ]
