window.addEventListener("DOMContentLoaded", () => {
    const body = document.body;
    const conversation = document.getElementById("conversation");
    const composer = document.getElementById("composer");
    const modeButton = document.getElementById("modeButton");
    const modeMenu = document.getElementById("modeMenu");
    const modeLabel = document.getElementById("modeLabel");
    const promptInput = document.getElementById("promptInput");
    const sendButton = document.getElementById("sendButton");

    const userTemplate = document.getElementById("userMessageTemplate");
    const assistantTemplate = document.getElementById("assistantMessageTemplate");

    let currentMode = "auto";
    const securities = ["SPX Index"];

    function autosize() {
        promptInput.style.height = "0px";
        promptInput.style.height = Math.min(promptInput.scrollHeight, 220) + "px";
    }

    function closeMenu() {
        modeMenu.classList.add("hidden");
    }

    function activateChatLayout() {
        if (!body.classList.contains("chat-started")) {
            body.classList.add("chat-started");
        }
    }

    function escapeHtml(value) {
        return String(value)
            .replaceAll("&", "&amp;")
            .replaceAll("<", "&lt;")
            .replaceAll(">", "&gt;")
            .replaceAll('"', "&quot;")
            .replaceAll("'", "&#039;");
    }

    function cardHTML(title, meta, text) {
        return `
      <div class="card">
        <div class="title">${escapeHtml(title)}</div>
        <div class="meta">${escapeHtml(meta)}</div>
        <div class="text">${escapeHtml(text)}</div>
      </div>
    `;
    }

    function buildMessage(role, text) {
        const tpl = role === "user" ? userTemplate : assistantTemplate;
        const node = tpl.content.firstElementChild.cloneNode(true);
        node.querySelector(".message-inner").textContent = text;
        return node;
    }

    function renderDetails(node, result) {
        const details = node.querySelector(".details");
        const detailsBody = node.querySelector(".details-body");
        const fusion = result.fusion_hits || [];
        const sources = result.sources || [];

        let html = "";

        fusion.slice(0, 6).forEach((hit) => {
            const meta = hit.metadata || {};
            let metaLine = `${hit.source_type || hit.source_kind || "unknown"} | score=${Number(hit.score || 0).toFixed(4)}`;
            if (meta.security) metaLine += ` | ${meta.security}`;
            if (meta.note_type) metaLine += ` | ${meta.note_type}`;
            const text = ((hit.excerpt || hit.context_text || "") + "").replace(/\s+/g, " ").slice(0, 500);
            html += cardHTML(hit.title || "Fusion hit", metaLine, text);
        });

        sources.slice(0, 8).forEach((hit) => {
            const metaLine = `page ${hit.page_no ?? "?"} | chunk ${hit.chunk_no ?? "?"} | score=${Number(hit.score || 0).toFixed(4)}`;
            const text = ((hit.text || "") + "").replace(/\s+/g, " ").slice(0, 500);
            html += cardHTML(hit.file_name || "Source", metaLine, text);
        });

        if (!html) return;

        details.classList.remove("hidden");
        detailsBody.innerHTML = html;
    }

    async function submitQuery(query) {
        const userNode = buildMessage("user", query);
        conversation.appendChild(userNode);

        const assistantNode = buildMessage("assistant", "Thinking…");
        conversation.appendChild(assistantNode);

        activateChatLayout();
        window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
        sendButton.disabled = true;

        try {
            const response = await fetch("/api/query", {
                method: "POST",
                headers: {
                    "Content-Type": "application/json"
                },
                body: JSON.stringify({
                    query,
                    mode: currentMode,
                    securities
                })
            });

            const payload = await response.json();
            if (!response.ok) {
                throw new Error(payload.detail || "Request failed.");
            }

            assistantNode.querySelector(".message-inner").textContent =
                payload.response || "No response produced.";
            renderDetails(assistantNode, payload);
        } catch (err) {
            const message = err && err.message ? err.message : String(err);
            assistantNode.querySelector(".message-inner").textContent = `Error: ${message}`;
        } finally {
            sendButton.disabled = false;
            window.scrollTo({ top: document.body.scrollHeight, behavior: "smooth" });
        }
    }

    async function handleSubmit() {
        const query = promptInput.value.trim();
        if (!query) return;

        promptInput.value = "";
        autosize();
        await submitQuery(query);
    }

    modeButton.addEventListener("click", (e) => {
        e.preventDefault();
        const hidden = modeMenu.classList.contains("hidden");
        closeMenu();
        if (hidden) modeMenu.classList.remove("hidden");
    });

    modeMenu.querySelectorAll("button").forEach((btn) => {
        btn.addEventListener("click", () => {
            currentMode = btn.dataset.mode;
            modeLabel.textContent = btn.textContent.trim();
            closeMenu();
        });
    });

    document.addEventListener("click", (e) => {
        if (!modeMenu.contains(e.target) && !modeButton.contains(e.target)) {
            closeMenu();
        }
    });

    composer.addEventListener("submit", async (e) => {
        e.preventDefault();
        await handleSubmit();
    });

    sendButton.addEventListener("click", async (e) => {
        e.preventDefault();
        await handleSubmit();
    });

    promptInput.addEventListener("input", autosize);

    promptInput.addEventListener("keydown", async (e) => {
        if (e.key === "Enter" && !e.shiftKey) {
            e.preventDefault();
            await handleSubmit();
        }
    });

    autosize();
});
