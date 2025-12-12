// frontend-widget/widget.js
(function () {
  // Expose global JohnWidget
  window.JohnWidget = {
    init: init
  };

  function createRoot(containerId, title) {
    const container = document.getElementById(containerId);
    if (!container) throw new Error("Container not found: " + containerId);
    const root = document.createElement("div");
    root.className = "john-widget";
    root.innerHTML = `
      <div class="john-title">
        <svg width="40" height="40" viewBox="0 0 24 24" style="flex:0 0 40px">
          <circle cx="12" cy="12" r="10" fill="#06b6d4"></circle>
          <path d="M8 9h8M8 13h6" stroke="#012" stroke-width="1.2" stroke-linecap="round"/>
        </svg>
        <div><h2>${title}</h2><div class="john-footer">Ask John — professional support AI. Attach replies to tickets.</div></div>
      </div>

      <div>
        <label style="display:block; margin-bottom:8px; color:var(--muted)">Attach to ticket</label>
        <select id="john-ticket" class="john-input" style="padding:10px"></select>
      </div>

      <div style="margin-top:12px;">
        <input id="john-input" class="john-input" placeholder="Type your message (press Enter to send)" />
        <textarea id="john-system" class="john-textarea" placeholder="Optional system instruction or extra context"></textarea>
        <button id="john-send" class="john-send">Send</button>
      </div>

      <div id="john-alert" style="display:none; margin-top:12px"></div>
      <div class="john-history" id="john-history" style="margin-top:18px"></div>

      <div style="margin-top:10px; text-align:center; color:var(--muted); font-size:12px;">John agent · business edition</div>
    `;
    container.appendChild(root);
    return root;
  }

  function setAlert(root, text) {
    const el = root.querySelector("#john-alert");
    if (!text) { el.style.display="none"; el.innerText=""; return; }
    el.style.display = "block";
    el.innerHTML = `<div class="john-alert">${text}</div>`;
  }

  function appendMsg(root, role, text) {
    const hist = root.querySelector("#john-history");
    const el = document.createElement("div");
    el.className = "john-bubble " + (role == "user" ? "user" : "assistant");
    el.innerText = (role == "user" ? "You: " : "John: ") + text;
    hist.appendChild(el);
    hist.scrollTop = hist.scrollHeight;
  }

  async function fetchTickets(backendUrl) {
    try {
      const res = await fetch(new URL("/tickets", backendUrl).toString());
      if (!res.ok) return [];
      return await res.json();
    } catch (e) { return []; }
  }

  async function sendChat(backendUrl, message, ticket_id, history, system_prompt) {
    const payload = { message, ticket_id, history, system_prompt };
    const res = await fetch(new URL("/chat", backendUrl).toString(), {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload)
    });
    if (!res.ok) {
      const err = await res.json().catch(()=>null);
      throw new Error(err?.detail || res.statusText || "Unknown error");
    }
    return await res.json();
  }

  function loadHistory(storageKey) {
    try {
      const raw = localStorage.getItem(storageKey);
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  }
  function saveHistory(storageKey, history) {
    localStorage.setItem(storageKey, JSON.stringify(history));
  }

  async function init(opts) {
    if (!opts || !opts.containerId || !opts.backendUrl) throw new Error("init requires containerId and backendUrl");
    const root = createRoot(opts.containerId, opts.title || "John — Chat Support");
    const ticketSelect = root.querySelector("#john-ticket");
    const input = root.querySelector("#john-input");
    const system = root.querySelector("#john-system");
    const sendBtn = root.querySelector("#john-send");
    const historyKey = "john_widget_history_v1";
    const history = loadHistory(historyKey);

    // show prior history
    history.forEach(h => appendMsg(root, h.role, h.content));

    // load tickets into dropdown (option "No ticket" by default)
    ticketSelect.innerHTML = `<option value="">No ticket (single chat)</option>`;
    (await fetchTickets(opts.backendUrl)).forEach(t => {
      const o = document.createElement("option");
      o.value = t.id;
      o.text = `#${t.id} — ${t.title} (${t.status})`;
      ticketSelect.appendChild(o);
    });

    function lockUI(lock=true) {
      sendBtn.disabled = lock;
      input.disabled = lock;
      system.disabled = lock;
      sendBtn.innerText = lock ? "Thinking…" : "Send";
    }

    sendBtn.addEventListener("click", async () => {
      const text = input.value.trim();
      if (!text) return;
      setAlert(root, null);
      appendMsg(root, "user", text);
      history.push({ role: "user", content: text });
      saveHistory(historyKey, history);
      lockUI(true);

      try {
        const ticketId = ticketSelect.value ? Number(ticketSelect.value) : undefined;
        const response = await sendChat(opts.backendUrl, text, ticketId, history, system.value || undefined);
        appendMsg(root, "assistant", response.reply);
        history.push({ role: "assistant", content: response.reply });
        saveHistory(historyKey, history);
        input.value = "";
        system.value = "";
      } catch (e) {
        setAlert(root, e.message);
      } finally {
        lockUI(false);
      }
    });

    input.addEventListener("keydown", (e) => {
      if (e.key === "Enter" && !e.shiftKey) {
        e.preventDefault();
        sendBtn.click();
      }
    });

    return {
      send: async (text, ticket_id, system_prompt) => {
        // programmatic send
        try {
          const res = await sendChat(opts.backendUrl, text, ticket_id, history, system_prompt);
          appendMsg(root, "assistant", res.reply);
          history.push({role: "assistant", content: res.reply});
          saveHistory(historyKey, history);
          return res.reply;
        } catch (e) {
          setAlert(root, e.message);
          throw e;
        }
      }
    };
  }

  // end IIFE
})();

