// cloud/web/app.js — X2 Dance Kiosk SPA
(function () {
    "use strict";

    // ── Config ──────────────────────────────────────────
    // API_BASE is set during deployment (relative path works with API GW + CloudFront)
    const API_BASE = "/api";
    const POLL_INTERVAL_MS = 3000;

    // ── State ───────────────────────────────────────────
    let robotId = "";
    let currentState = "unknown";
    let pollTimer = null;

    // Dance catalog — hardcoded for now, matches motion_catalog.py KNOWN_MOTIONS
    const DANCES = [
        { id: "golf_swing_pro", name: "Golf Swing", emoji: "🏌️" },
        { id: "drunk_kungfu", name: "Drunk Kungfu", emoji: "🥋" },
        { id: "double_kick", name: "Double Kick", emoji: "🦵" },
        { id: "taichi", name: "Tai Chi", emoji: "☯️" },
        { id: "despacito", name: "Despacito", emoji: "💃" },
        { id: "love_you", name: "Love You", emoji: "❤️" },
        { id: "miao", name: "Miao", emoji: "🐱" },
        { id: "golf_swing_csv", name: "Golf (Classic)", emoji: "⛳" },
    ];

    // ── DOM ─────────────────────────────────────────────
    const $badge = document.getElementById("status-badge");
    const $menu = document.getElementById("dance-menu");
    const $danceList = document.getElementById("dance-list");
    const $dancing = document.getElementById("dancing-view");
    const $dancingName = document.getElementById("dancing-motion-name");
    const $offline = document.getElementById("offline-view");
    const $success = document.getElementById("success-view");
    const $cancelled = document.getElementById("cancelled-view");
    const $error = document.getElementById("error-view");
    const $errorMsg = document.getElementById("error-message");

    // ── Helpers ─────────────────────────────────────────

    function hideAll() {
        [$menu, $dancing, $offline, $success, $cancelled, $error].forEach(
            (el) => el.classList.add("hidden")
        );
    }

    function show(el) {
        hideAll();
        el.classList.remove("hidden");
    }

    function setBadge(state) {
        $badge.textContent = state.charAt(0).toUpperCase() + state.slice(1);
        $badge.className = "badge " + state;
    }

    async function api(method, path, body) {
        const opts = {
            method,
            headers: { "Content-Type": "application/json" },
        };
        if (body) opts.body = JSON.stringify(body);
        const res = await fetch(API_BASE + path, opts);
        const data = await res.json();
        if (!res.ok) throw { status: res.status, ...data };
        return data;
    }

    // ── Core ────────────────────────────────────────────

    async function fetchStatus() {
        try {
            const data = await api("GET", `/status/${robotId}`);
            currentState = data.state || "unknown";
            setBadge(currentState);
            return data;
        } catch (e) {
            currentState = "offline";
            setBadge("offline");
            return { state: "offline" };
        }
    }

    function renderDanceMenu() {
        $danceList.innerHTML = "";
        DANCES.forEach((dance) => {
            const card = document.createElement("div");
            card.className = "dance-card";
            card.innerHTML = `
                <div class="emoji">${dance.emoji}</div>
                <div class="name">${dance.name}</div>
                <div class="price">$2.00</div>
            `;
            card.addEventListener("click", () => startCheckout(dance));
            $danceList.appendChild(card);
        });
    }

    async function startCheckout(dance) {
        try {
            const data = await api("POST", "/checkout", {
                robot_id: robotId,
                motion_id: dance.id,
            });
            window.location.href = data.checkout_url;
        } catch (e) {
            if (e.status === 409) {
                await updateView();
            } else {
                $errorMsg.textContent = e.error || "Failed to start checkout";
                show($error);
            }
        }
    }

    async function updateView() {
        const data = await fetchStatus();

        if (currentState === "idle" || currentState === "unknown") {
            renderDanceMenu();
            show($menu);
        } else if (currentState === "dancing") {
            $dancingName.textContent = data.current_motion || "";
            show($dancing);
        } else if (currentState === "offline") {
            show($offline);
        }
    }

    function startPolling() {
        if (pollTimer) clearInterval(pollTimer);
        pollTimer = setInterval(updateView, POLL_INTERVAL_MS);
    }

    // ── Init ────────────────────────────────────────────

    function init() {
        const path = window.location.pathname.replace(/^\//, "").replace(/\/$/, "");
        robotId = path || "x2-001";

        const params = new URLSearchParams(window.location.search);

        if (params.get("success") === "true") {
            setBadge("dancing");
            show($success);
            setTimeout(updateView, 2000);
        } else if (params.get("cancelled") === "true") {
            show($cancelled);
            document.getElementById("back-to-menu").addEventListener("click", (e) => {
                e.preventDefault();
                window.history.replaceState({}, "", `/${robotId}`);
                updateView();
            });
        } else {
            updateView();
        }

        startPolling();
    }

    // ── Event listeners ─────────────────────────────────
    document.getElementById("retry-btn").addEventListener("click", updateView);

    init();
})();
