ADMIN_PAGE_HTML = """<!DOCTYPE html>
<html lang=\"en\">
<head>
  <meta charset=\"UTF-8\" />
  <meta name=\"viewport\" content=\"width=device-width, initial-scale=1.0\" />
  <title>Travel Chatbot Admin Setup</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 24px; background: #f6f7fb; color: #1f2937; }
    .card { max-width: 900px; margin: 0 auto; background: #fff; border: 1px solid #e5e7eb; border-radius: 12px; padding: 20px; }
    h1 { margin-top: 0; }
    label { display: block; margin: 12px 0 6px; font-weight: 600; }
    input, textarea { width: 100%; padding: 10px; border: 1px solid #d1d5db; border-radius: 8px; }
    textarea { min-height: 90px; resize: vertical; }
    button { margin-top: 14px; padding: 10px 16px; border: 0; border-radius: 8px; background: #2563eb; color: white; font-weight: 700; cursor: pointer; }
    .status { margin-top: 10px; color: #475569; }
  </style>
</head>
<body>
  <div class=\"card\">
    <h1>Initial Chatbot Setup</h1>
    <p>Use this page for first-time setup and updates of FAQ + policies JSON knowledge base.</p>

    <label for=\"apiBaseUrl\">API base URL</label>
    <input id=\"apiBaseUrl\" value=\"\" placeholder=\"Leave blank to use this server\" />

    <label for=\"adminKey\">Admin key</label>
    <input id=\"adminKey\" type=\"password\" placeholder=\"Enter X-Admin-Key\" />

    <label for=\"companyName\">Company name</label>
    <input id=\"companyName\" placeholder=\"Your company\" />

    <label for=\"adminEmail\">Admin email (optional)</label>
    <input id=\"adminEmail\" placeholder=\"admin@company.com\" />

    <button id=\"initButton\" type=\"button\">Run Initial Setup</button>
    <hr style=\"margin:20px 0;border:0;border-top:1px solid #e5e7eb\" />

    <h2>Knowledge Content</h2>
    <label for=\"terms\">Terms and conditions</label>
    <textarea id=\"terms\"></textarea>
    <label for=\"refundPolicy\">Refund policy</label>
    <textarea id=\"refundPolicy\"></textarea>
    <label for=\"exchangeCharges\">Exchange charges</label>
    <textarea id=\"exchangeCharges\"></textarea>
    <label for=\"refundCharges\">Refund charges</label>
    <textarea id=\"refundCharges\"></textarea>
    <label for=\"faqsJson\">FAQs JSON (array)</label>
    <textarea id=\"faqsJson\" placeholder='[{"topic":"baggage","keywords":["baggage"],"answer":"..."}]'></textarea>

    <label for=\"bookingLeadUrl\">Booking lead webhook URL (optional)</label>
    <input id=\"bookingLeadUrl\" type=\"url\" placeholder=\"https://your-site.com/api/booking-requests\" />
    <p style=\"margin:6px 0 0;font-size:0.92rem;color:#64748b\">
      When travelers select a fare in chat, the API POSTs JSON to this URL. Leave blank to clear. You can also set <code>BOOKING_LEAD_URL</code> on the server (overrides this value when set).
    </p>

    <button id=\"loadKnowledgeButton\" type=\"button\">Load knowledge from server</button>
    <button id=\"saveButton\" type=\"button\">Save Knowledge</button>
    <div class=\"status\" id=\"status\"></div>
  </div>
  <script>
    const statusEl = document.getElementById("status");
    const termsEl = document.getElementById("terms");
    const refundPolicyEl = document.getElementById("refundPolicy");
    const exchangeChargesEl = document.getElementById("exchangeCharges");
    const refundChargesEl = document.getElementById("refundCharges");
    const faqsJsonEl = document.getElementById("faqsJson");
    const bookingLeadUrlEl = document.getElementById("bookingLeadUrl");

    function baseUrl() {
      const v = document.getElementById("apiBaseUrl").value.trim();
      return v ? v.replace(/\\/$/, "") : window.location.origin;
    }
    function key() {
      return document.getElementById("adminKey").value.trim();
    }

    function parseApiError(data, fallbackMessage) {
      if (!data) return fallbackMessage;
      if (typeof data.detail === "string") return data.detail;
      if (Array.isArray(data.detail) && data.detail.length > 0) {
        const first = data.detail[0];
        if (first && typeof first === "object") {
          const location = Array.isArray(first.loc) ? first.loc.join(".") : "field";
          const message = first.msg || "Invalid value";
          return `${location}: ${message}`;
        }
      }
      return fallbackMessage;
    }

    function validateRequiredBeforeSave() {
      if (!key()) {
        statusEl.textContent = "Save failed: Admin key is required.";
        return false;
      }
      if (!termsEl.value.trim() || !refundPolicyEl.value.trim() || !exchangeChargesEl.value.trim() || !refundChargesEl.value.trim()) {
        statusEl.textContent = "Save failed: All policy fields are required.";
        return false;
      }
      return true;
    }

    async function loadStatus() {
      try {
        const response = await fetch(`${baseUrl()}/api/admin/setup/status`);
        const data = await response.json();
        if (response.ok) {
          statusEl.textContent = data.initialized
            ? `Initialized for ${data.company_name || "company"} (updated ${data.updated_at}).`
            : "Not initialized yet. Run Initial Setup first.";
        }
      } catch (error) {
        statusEl.textContent = "Unable to load setup status.";
      }
    }

    document.getElementById("initButton").addEventListener("click", async () => {
      statusEl.textContent = "Running initial setup...";
      const payload = {
        company_name: document.getElementById("companyName").value.trim(),
        admin_email: document.getElementById("adminEmail").value.trim() || null,
      };
      try {
        const response = await fetch(`${baseUrl()}/api/admin/setup/initialize`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Admin-Key": key() },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(parseApiError(data, "Setup failed"));
        statusEl.textContent = "Initial setup completed.";
        termsEl.value = data.policies.terms_and_conditions || "";
        refundPolicyEl.value = data.policies.refund_policy || "";
        exchangeChargesEl.value = data.policies.exchange_charges || "";
        refundChargesEl.value = data.policies.refund_charges || "";
        faqsJsonEl.value = JSON.stringify(data.faqs || [], null, 2);
        bookingLeadUrlEl.value = (data.integrations && data.integrations.booking_lead_url) || "";
      } catch (error) {
        statusEl.textContent = `Setup failed: ${error.message}`;
      }
    });

    document.getElementById("saveButton").addEventListener("click", async () => {
      if (!validateRequiredBeforeSave()) {
        return;
      }

      statusEl.textContent = "Saving knowledge...";
      try {
        let parsedFaqs = [];
        if (faqsJsonEl.value.trim()) {
          try {
            parsedFaqs = JSON.parse(faqsJsonEl.value);
            if (!Array.isArray(parsedFaqs)) {
              throw new Error("FAQs JSON must be an array.");
            }
          } catch (jsonError) {
            statusEl.textContent = `Save failed: Invalid FAQs JSON. ${jsonError.message || ""}`.trim();
            return;
          }
        }

        const payload = {
          faqs: parsedFaqs,
          terms_and_conditions: termsEl.value,
          refund_policy: refundPolicyEl.value,
          exchange_charges: exchangeChargesEl.value,
          refund_charges: refundChargesEl.value,
          booking_lead_url: bookingLeadUrlEl.value.trim(),
        };
        const response = await fetch(`${baseUrl()}/api/admin/knowledge/update`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Admin-Key": key() },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(parseApiError(data, "Save failed"));
        statusEl.textContent = `Knowledge updated at ${data.updated_at}.`;
      } catch (error) {
        statusEl.textContent = `Save failed: ${error.message}`;
      }
    });

    document.getElementById("loadKnowledgeButton").addEventListener("click", async () => {
      if (!key()) {
        statusEl.textContent = "Load failed: Admin key is required.";
        return;
      }
      statusEl.textContent = "Loading knowledge...";
      try {
        const response = await fetch(`${baseUrl()}/api/admin/knowledge`, {
          headers: { "X-Admin-Key": key() },
        });
        const data = await response.json();
        if (!response.ok) throw new Error(parseApiError(data, "Load failed"));
        termsEl.value = data.policies.terms_and_conditions || "";
        refundPolicyEl.value = data.policies.refund_policy || "";
        exchangeChargesEl.value = data.policies.exchange_charges || "";
        refundChargesEl.value = data.policies.refund_charges || "";
        faqsJsonEl.value = JSON.stringify(data.faqs || [], null, 2);
        bookingLeadUrlEl.value = (data.integrations && data.integrations.booking_lead_url) || "";
        statusEl.textContent = `Loaded knowledge (updated ${data.updated_at}).`;
      } catch (error) {
        statusEl.textContent = `Load failed: ${error.message}`;
      }
    });

    loadStatus();
  </script>
</body>
</html>
"""
