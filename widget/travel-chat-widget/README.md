# Next.js Travel Chat Widget

Reusable client-side widget for a Next.js website that talks to the Travel Agent Chatbot API.

## Install in a Next.js app

You can copy this folder into your Next.js repository or install it from a local path.

### Option 1: local package install

```bash
npm install /absolute/path/to/travel-agent-chatbot/widget/travel-chat-widget
```

Then import it in your app:

```tsx
"use client";

import { TravelChatWidget } from "travel-chat-widget";

export function TravelAssistant() {
  return (
    <TravelChatWidget
      apiBaseUrl="http://127.0.0.1:8000"
      accentColor="#bb5a04"
      onFareSelect={(fare) => {
        console.log("Selected fare", fare);
      }}
    />
  );
}
```

### Option 2: copy the package into your app

Copy `travel-chat-widget` into your Next.js project, for example under `components/travel-chat-widget`, then import from that local folder.

## Example usage in App Router

```tsx
import { TravelChatWidget } from "travel-chat-widget";

export default function Page() {
  return (
    <main>
      <h1>Travel deals</h1>
      <TravelChatWidget apiBaseUrl="http://127.0.0.1:8000" defaultOpen />
    </main>
  );
}
```

## Required backend setup

- Run the Python API from this repository.
- Set `CORS_ALLOW_ORIGINS` in the backend `.env` file to your Next.js origin, for example `http://localhost:3000`.
- Ensure the browser can reach `POST /api/chat` on your API host.

## Props

- `apiBaseUrl`: Base URL of the Python API, such as `http://127.0.0.1:8000`
- `accentColor`: Brand color for the widget launcher and highlights
- `defaultOpen`: Opens the widget immediately on page load
- `greeting`: Overrides the default first assistant message
- `maxVisibleFares`: Limits how many fares render inside the widget
- `onFareSelect`: Callback when the user clicks a fare card

## Notes

- This is a client component and should be rendered from client-capable code.
- The widget currently calls `POST /api/chat` with the user message only.
- When a fare is selected, pass the returned `raw_offer_id` into your booking flow or map it to a stored Sabre payload on your side.
