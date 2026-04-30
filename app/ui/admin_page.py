ADMIN_PAGE_HTML = r"""<!DOCTYPE html>
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

    function baseUrl() {
      const v = document.getElementById("apiBaseUrl").value.trim();
      return v ? v.replace(/\/$/, "") : window.location.origin;
    }
    function key() {
      return document.getElementById("adminKey").value.trim();
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
        if (!response.ok) throw new Error(data.detail || "Setup failed");
        statusEl.textContent = "Initial setup completed.";
        termsEl.value = data.policies.terms_and_conditions || "";
        refundPolicyEl.value = data.policies.refund_policy || "";
        exchangeChargesEl.value = data.policies.exchange_charges || "";
        refundChargesEl.value = data.policies.refund_charges || "";
        faqsJsonEl.value = JSON.stringify(data.faqs || [], null, 2);
      } catch (error) {
        statusEl.textContent = `Setup failed: ${error.message}`;
      }
    });

    document.getElementById("saveButton").addEventListener("click", async () => {
      statusEl.textContent = "Saving knowledge...";
      try {
        const payload = {
          faqs: faqsJsonEl.value.trim() ? JSON.parse(faqsJsonEl.value) : [],
          terms_and_conditions: termsEl.value,
          refund_policy: refundPolicyEl.value,
          exchange_charges: exchangeChargesEl.value,
          refund_charges: refundChargesEl.value,
        };
        const response = await fetch(`${baseUrl()}/api/admin/knowledge/update`, {
          method: "POST",
          headers: { "Content-Type": "application/json", "X-Admin-Key": key() },
          body: JSON.stringify(payload),
        });
        const data = await response.json();
        if (!response.ok) throw new Error(data.detail || "Save failed");
        statusEl.textContent = `Knowledge updated at ${data.updated_at}.`;
      } catch (error) {
        statusEl.textContent = `Save failed: ${error.message}`;
      }
    });

    loadStatus();
  </script>
</body>
</html>
"""
