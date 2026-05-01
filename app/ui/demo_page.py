DEMO_PAGE_HTML = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Travel Agent Chatbot Demo</title>
  <style>
    :root {
      --bg: #f6efe5;
      --panel: rgba(255, 252, 247, 0.9);
      --border: rgba(76, 49, 20, 0.12);
      --text: #2b2117;
      --muted: #6c5a49;
      --accent: #b96216;
      --accent-dark: #8a4512;
    }

    * {
      box-sizing: border-box;
    }

    body {
      margin: 0;
      min-height: 100vh;
      font-family: \"DM Sans\", \"Segoe UI\", sans-serif;
      color: var(--text);
      background:
        radial-gradient(circle at top left, rgba(255, 240, 214, 0.95), transparent 32%),
        linear-gradient(180deg, #f8f2e9 0%, #efe5d7 100%);
      display: grid;
      place-items: center;
      padding: 24px;
    }

    .demo-shell {
      width: min(960px, 100%);
      display: grid;
      grid-template-columns: 320px 1fr;
      gap: 20px;
    }

    .demo-card,
    .chat-card {
      border: 1px solid var(--border);
      border-radius: 28px;
      background: var(--panel);
      box-shadow: 0 28px 60px rgba(58, 34, 13, 0.12);
      backdrop-filter: blur(10px);
    }

    .demo-card {
      padding: 24px;
    }

    .eyebrow {
      margin: 0 0 10px;
      text-transform: uppercase;
      letter-spacing: 0.14em;
      font-size: 0.74rem;
      font-weight: 700;
      color: var(--accent);
    }

    h1 {
      margin: 0 0 12px;
      font-size: 2rem;
      line-height: 1.05;
    }

    p,
    li,
    label,
    small {
      color: var(--muted);
      line-height: 1.5;
    }

    ul {
      padding-left: 20px;
      margin: 10px 0 0;
    }

    .chat-card {
      display: grid;
      grid-template-rows: auto 1fr auto;
      min-height: 720px;
      overflow: hidden;
    }

    .chat-header {
      padding: 24px 24px 18px;
      border-bottom: 1px solid var(--border);
      background:
        radial-gradient(circle at top left, rgba(255, 245, 227, 0.95), transparent 45%),
        linear-gradient(135deg, rgba(185, 98, 22, 0.14), rgba(138, 69, 18, 0.03));
    }

    .chat-header h2 {
      margin: 4px 0 8px;
      font-size: 1.3rem;
    }

    .message-list {
      padding: 20px;
      overflow-y: auto;
      display: flex;
      flex-direction: column;
      gap: 12px;
    }

    .message {
      max-width: 82%;
      padding: 14px 16px;
      border-radius: 20px;
      white-space: pre-wrap;
    }

    .message.user {
      margin-left: auto;
      background: linear-gradient(135deg, rgba(185, 98, 22, 0.16), rgba(138, 69, 18, 0.08));
    }

    .message.assistant {
      background: rgba(255, 250, 244, 0.96);
      border: 1px solid rgba(76, 49, 20, 0.08);
    }

    .fare-list {
      display: grid;
      gap: 10px;
      margin-top: 12px;
    }

    .fare-card {
      border: 1px solid rgba(185, 98, 22, 0.14);
      border-radius: 16px;
      padding: 12px 14px;
      background: rgba(255, 255, 255, 0.84);
    }

    .fare-card strong {
      display: block;
      font-size: 1rem;
      color: var(--text);
      margin: 4px 0;
    }

    .composer {
      border-top: 1px solid var(--border);
      padding: 18px 20px 20px;
      background: rgba(255, 250, 241, 0.7);
    }

    .composer textarea,
    .composer input {
      width: 100%;
      border: 1px solid rgba(76, 49, 20, 0.12);
      border-radius: 16px;
      padding: 12px 14px;
      font: inherit;
      color: var(--text);
      background: rgba(255, 255, 255, 0.86);
    }

    .composer textarea {
      min-height: 90px;
      resize: vertical;
      margin-top: 10px;
    }

    .composer-row {
      display: grid;
      grid-template-columns: 1fr auto;
      gap: 12px;
      align-items: end;
      margin-top: 14px;
    }

    button {
      border: 0;
      border-radius: 999px;
      padding: 12px 18px;
      background: linear-gradient(135deg, var(--accent), var(--accent-dark));
      color: #fff7f0;
      font-weight: 700;
      cursor: pointer;
    }

    button:disabled {
      opacity: 0.55;
      cursor: not-allowed;
    }

    .status {
      font-size: 0.9rem;
      margin-top: 10px;
      min-height: 20px;
    }

    .examples {
      display: grid;
      gap: 10px;
      margin-top: 18px;
    }

    .example {
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 10px 12px;
      background: rgba(255, 255, 255, 0.62);
      text-align: left;
      color: var(--text);
    }

    @media (max-width: 880px) {
      .demo-shell {
        grid-template-columns: 1fr;
      }

      .chat-card {
        min-height: 640px;
      }
    }
  </style>
</head>
<body>
  <div class=\"demo-shell\">
    <aside class=\"demo-card\">
      <p class=\"eyebrow\">Browser test UI</p>
      <h1>Test the chatbot directly</h1>
      <p>
        This page talks to <strong>/api/chat</strong> on the same FastAPI service, so you can test fare
        searches and website questions without building a separate frontend first.
      </p>
      <ul>
        <li>Ask about fares, routes, and travel dates.</li>
        <li>Ask website questions such as refund policy or baggage rules.</li>
        <li>See structured fare options when Sabre returns offers.</li>
      </ul>
      <div class=\"examples\">
        <button class=\"example\" type=\"button\" data-example=\"What is your refund policy?\">What is your refund policy?</button>
        <button class=\"example\" type=\"button\" data-example=\"Need cheapest fare from JFK to JED on 2026-06-14 for 2 adults\">Need cheapest fare from JFK to JED on 2026-06-14 for 2 adults</button>
        <button class=\"example\" type=\"button\" data-example=\"Can I change my booking date after ticketing?\">Can I change my booking date after ticketing?</button>
      </div>
    </aside>

    <section class=\"chat-card\">
      <header class=\"chat-header\">
        <p class=\"eyebrow\">Travel agent assistant</p>
        <h2>Live chatbot demo</h2>
        <p>Default API target is the current server origin. Change it only if your API runs elsewhere.</p>
      </header>

      <div class=\"message-list\" id=\"messageList\">
        <div class=\"message assistant\">I can help with Sabre fare searches and common website questions. Try asking about refund policy or a route with travel dates.</div>
      </div>

      <form class=\"composer\" id=\"chatForm\">
        <label for=\"apiBaseUrl\">API base URL</label>
        <input id=\"apiBaseUrl\" name=\"apiBaseUrl\" value=\"\" placeholder=\"Leave blank to use this server\" />
        <label for=\"message\" style=\"display:block;margin-top:12px;\">Message</label>
        <textarea id=\"message\" name=\"message\" placeholder=\"Ask about fares or website policies\"></textarea>
        <div class=\"composer-row\">
          <div class=\"status\" id=\"status\"></div>
          <button id=\"submitButton\" type=\"submit\">Send</button>
        </div>
      </form>
    </section>
  </div>

  <script>
    const form = document.getElementById("chatForm");
    const messageInput = document.getElementById("message");
    const apiBaseUrlInput = document.getElementById("apiBaseUrl");
    const messageList = document.getElementById("messageList");
    const status = document.getElementById("status");
    const submitButton = document.getElementById("submitButton");

    function getApiBaseUrl() {
      const value = apiBaseUrlInput.value.trim();
      return value ? value.replace(/\\/$/, "") : window.location.origin;
    }

    function appendMessage(role, text, fares) {
      const wrapper = document.createElement("div");
      wrapper.className = `message ${role}`;
      wrapper.textContent = text;

      if (Array.isArray(fares) && fares.length > 0) {
        const fareList = document.createElement("div");
        fareList.className = "fare-list";

        fares.forEach((fare) => {
          const card = document.createElement("div");
          card.className = "fare-card";
          card.innerHTML = `
            <small>Option ${fare.rank}${fare.validating_carrier ? ` · ${fare.validating_carrier}` : ""}</small>
            <strong>${Number(fare.total_price).toFixed(2)} ${fare.currency}</strong>
            <small>${fare.departure_airport ?? "Origin"} to ${fare.arrival_airport ?? "Destination"}</small><br />
            <small>${fare.number_of_stops === 0 ? "Non-stop" : `${fare.number_of_stops ?? "Unknown"} stop(s)`}</small>
          `;
          fareList.appendChild(card);
        });

        wrapper.appendChild(fareList);
      }

      messageList.appendChild(wrapper);
      messageList.scrollTop = messageList.scrollHeight;
    }

    async function sendMessage(message) {
      appendMessage("user", message);
      status.textContent = "Waiting for chatbot response...";
      submitButton.disabled = true;

      try {
        const response = await fetch(`${getApiBaseUrl()}/api/chat`, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ message }),
        });

        const data = await response.json();
        if (!response.ok) {
          throw new Error(data.detail || `Request failed with status ${response.status}`);
        }

        appendMessage("assistant", data.answer, data.fares || []);
        status.textContent = "";
      } catch (error) {
        appendMessage("assistant", `Request failed. ${error.message || "Unknown error."}`);
        status.textContent = "The request failed. Check API URL or backend credentials.";
      } finally {
        submitButton.disabled = false;
      }
    }

    form.addEventListener("submit", async (event) => {
      event.preventDefault();
      const message = messageInput.value.trim();
      if (!message) {
        return;
      }

      messageInput.value = "";
      await sendMessage(message);
    });

    document.querySelectorAll("[data-example]").forEach((button) => {
      button.addEventListener("click", async () => {
        const message = button.getAttribute("data-example") || "";
        messageInput.value = message;
        await sendMessage(message);
      });
    });
  </script>
</body>
</html>
"""
