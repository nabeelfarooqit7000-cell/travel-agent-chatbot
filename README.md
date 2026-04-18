# Travel Agent Chatbot API

Python service for a travel website chatbot that answers customer questions and searches Sabre fares to help users finalize bookings.

## Features

- FastAPI API your website can call
- Chat endpoint for customer questions
- Sabre fare search endpoint for flight shopping
- Website FAQ support for policies and common service questions
- Ranking logic to surface the best fare options
- Environment-based Sabre configuration
- Basic tests for the response and ranking flow

## Endpoints

- `GET /health`
- `GET /demo`
- `POST /api/chat`
- `POST /api/fares/search`

## Quick Start

1. Create a virtual environment.
2. Install dependencies.
3. Copy `.env.example` to `.env` and fill in Sabre credentials.
4. Run the API.

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

The API will start at `http://127.0.0.1:8000`.

Open `http://127.0.0.1:8000/demo` in your browser to test the chatbot UI directly.

## Sabre Notes

This project uses OAuth client credentials and a configurable flight shopping path. You must provide working Sabre credentials and confirm the shopping endpoint used by your Sabre contract.

Default values target the Sabre cert environment. Adjust them in `.env` if your account uses different URLs or API versions.

## Next.js Widget

An installable Next.js widget package is included in `widget/travel-chat-widget`.

- Package entry: `widget/travel-chat-widget/index.ts`
- Docs: `widget/travel-chat-widget/README.md`
- Before using it from a separate frontend origin, set `CORS_ALLOW_ORIGINS` in your backend `.env` file.

## Example Requests

### Chatbot

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "I need the cheapest flight from JFK to LHR on 2026-06-14 for 1 adult",
    "trip": {
      "origin": "JFK",
      "destination": "LHR",
      "departure_date": "2026-06-14",
      "adults": 1,
      "currency": "USD"
    }
  }'
```

### Website Policy Question

```bash
curl -X POST http://127.0.0.1:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is your refund policy?"
  }'
```

### Fare Search

```bash
curl -X POST http://127.0.0.1:8000/api/fares/search \
  -H "Content-Type: application/json" \
  -d '{
    "origin": "JFK",
    "destination": "LHR",
    "departure_date": "2026-06-14",
    "return_date": "2026-06-21",
    "adults": 1,
    "currency": "USD",
    "max_results": 10
  }'
```

## Suggested Website Flow

1. Website sends the user's message to `POST /api/chat`.
2. If the user already selected dates and airports, include them in the `trip` object.
3. The API either answers a website question directly or searches Sabre and returns a natural-language summary plus structured fare options.
4. Your website presents the options and sends the selected fare to your booking flow.

## Local UI Testing

Use the built-in browser page at `/demo` to test the chatbot without a separate frontend project.

- Ask website questions such as refund policy, baggage, or booking changes.
- Ask fare-search questions such as `Cheapest JFK to JED on 2026-06-14 for 2 adults`.
- If your API runs on a different host, set the API base URL field at the top of the demo page.

## Website Knowledge

Built-in FAQ matching currently covers topics such as refund policy, booking changes, payment methods, baggage, and support questions. You can customize those answers in `app/data/site_content.py`.
