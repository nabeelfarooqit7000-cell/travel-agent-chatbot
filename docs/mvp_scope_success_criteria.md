# MVP Scope and Success Criteria

## Locked MVP Features

- Flight search using Sabre shopping APIs
- Fare ranking and pricing display
- Booking handoff flow readiness (offer selection to external booking process)
- Itinerary support questions (changes, refunds, baggage guidance)
- General customer support Q&A from curated knowledge base

## Core User Journeys

1. Search -> compare -> select fare
2. Select fare -> booking handoff -> confirmation messaging
3. Post-booking support -> changes/refunds/baggage guidance

## Success KPIs (MVP Targets)

- Search latency (p95): <= 3.0s for fare search response
- Booking handoff success rate: >= 99.0%
- Support response accuracy (golden QA set): >= 90.0%
- Fallback response rate: <= 15.0%
- API uptime: >= 99.5%

## Instrumentation Requirements

- Every chat response should include route type (`sabre`, `knowledge`, `fallback`) for KPI aggregation.
- Fare search requests should emit latency and status counters.
- Knowledge-base answers should emit hit/miss counters.
