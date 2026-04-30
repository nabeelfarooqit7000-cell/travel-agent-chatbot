from app.services.knowledge import WebsiteKnowledgeService


def test_knowledge_service_uses_provided_entries() -> None:
    service = WebsiteKnowledgeService(
        faq_entries=[
            {
                "topic": "custom",
                "keywords": ["visa"],
                "answer": "Please check visa requirements before booking.",
            }
        ]
    )

    answer = service.answer("Do I need a visa?")
    assert answer is not None
    assert "visa requirements" in answer.lower()


def test_knowledge_service_falls_back_to_default_faqs_when_file_missing() -> None:
    service = WebsiteKnowledgeService()

    answer = service.answer("What is your refund policy?")
    assert answer is not None
    assert "refund policy" in answer.lower() or "refundable" in answer.lower()
