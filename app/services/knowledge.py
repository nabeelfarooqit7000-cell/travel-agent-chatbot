from __future__ import annotations

import re
from typing import Any

from app.data.site_content import SITE_FAQS


class WebsiteKnowledgeService:
    def __init__(self, faq_entries: list[dict[str, Any]] | None = None) -> None:
        self.faq_entries = faq_entries or SITE_FAQS

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
