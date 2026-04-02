// cloud/web/app.js — X2 Dance Kiosk SPA
(function () {
    "use strict";

    // ── Config ──────────────────────────────────────────
    const API_BASE = "https://x37qk3dqwc.execute-api.us-east-2.amazonaws.com/prod/api";
    const POLL_INTERVAL_MS = 3000;

    // ── State ───────────────────────────────────────────
    let robotId = "";
    let currentState = "unknown";
    let pollTimer = null;
    let expandedCategory = null;
    let pendingGesture = null;

    // ── Dance catalog (paid) ────────────────────────────
    const DANCES = [
        { id: "golf_swing_pro", name: "Golf Swing", emoji: "\u{1F3CC}\u{FE0F}" },
        { id: "drunk_kungfu", name: "Drunk Kungfu", emoji: "\u{1F94B}" },
        { id: "double_kick", name: "Double Kick", emoji: "\u{1F9B5}" },
        { id: "taichi", name: "Tai Chi", emoji: "\u{262F}\u{FE0F}" },
        { id: "despacito", name: "Despacito", emoji: "\u{1F483}" },
        { id: "love_you", name: "Love You", emoji: "\u{2764}\u{FE0F}" },
        { id: "miao", name: "Miao", emoji: "\u{1F431}" },
        { id: "golf_swing_csv", name: "Golf (Classic)", emoji: "\u{26F3}" },
    ];

    // ── Gesture catalog (free, grouped) ─────────────────
    // Each category has an emoji, name, and variants array.
    // Variant: { label, motion_id, area }
    // area: 1=left, 2=right, 3=both arms, 11=full body
    const GESTURE_CATEGORIES = [
        { name: "Wave", emoji: "\u{1F44B}", variants: [
            { label: "Right", motion_id: 1002, area: 2 },
            { label: "Left", motion_id: 1002, area: 1 },
        ]},
        { name: "Handshake", emoji: "\u{1F91D}", variants: [
            { label: "Right", motion_id: 1003, area: 2 },
            { label: "Left", motion_id: 1003, area: 1 },
        ]},
        { name: "Raise Hand", emoji: "\u{270B}", variants: [
            { label: "Right", motion_id: 1001, area: 2 },
            { label: "Left", motion_id: 1001, area: 1 },
            { label: "Both", motion_id: 1010, area: 3 },
        ]},
        { name: "Blow a Kiss", emoji: "\u{1F48B}", variants: [
            { label: "Right", motion_id: 1004, area: 2 },
            { label: "Left", motion_id: 1004, area: 1 },
        ]},
        { name: "Salute", emoji: "\u{1FAE1}", variants: [
            { label: "Right", motion_id: 1013, area: 2 },
            { label: "Left", motion_id: 1013, area: 1 },
        ]},
        { name: "Heart", emoji: "\u{1F49C}", variants: [
            { label: "Both", motion_id: 1007, area: 3 },
            { label: "Right", motion_id: 1007, area: 2 },
            { label: "Left", motion_id: 1007, area: 1 },
        ]},
        { name: "High Five", emoji: "\u{1F590}\u{FE0F}", variants: [
            { label: "Right", motion_id: 1008, area: 2 },
            { label: "Left", motion_id: 1008, area: 1 },
        ]},
        { name: "Wave at Chest", emoji: "\u{1F44B}", variants: [
            { label: "Right", motion_id: 1011, area: 2 },
            { label: "Left", motion_id: 1011, area: 1 },
        ]},
        { name: "Clap", emoji: "\u{1F44F}", variants: [
            { label: "Clap", motion_id: 3017, area: 11 },
        ]},
        { name: "Hug", emoji: "\u{1FAC2}", variants: [
            { label: "Hug", motion_id: 3008, area: 11 },
        ]},
        { name: "Cheer", emoji: "\u{1F389}", variants: [
            { label: "Cheer", motion_id: 3011, area: 11 },
        ]},
        { name: "Wave Goodbye", emoji: "\u{1F44B}", variants: [
            { label: "Goodbye", motion_id: 3031, area: 11 },
        ]},
        { name: "Light Wave", emoji: "\u{2728}", variants: [
            { label: "Light Wave", motion_id: 3007, area: 11 },
        ]},
        { name: "Cross Arms", emoji: "\u{1F645}", variants: [
            { label: "Cross Arms", motion_id: 3009, area: 11 },
        ]},
        { name: "Bow", emoji: "\u{1F647}", variants: [
            { label: "Bow", motion_id: 3001, area: 11 },
        ]},
        { name: "Scratch Head", emoji: "\u{1F914}", variants: [
            { label: "Scratch Head", motion_id: 3024, area: 11 },
        ]},
        { name: "Grab Buttocks", emoji: "\u{1F351}", variants: [
            { label: "Grab Buttocks", motion_id: 3025, area: 11 },
        ]},
    ];

    // ── DOM ─────────────────────────────────────────────
    const $badge = document.getElementById("status-badge");
    const $menu = document.getElementById("dance-menu");
    const $danceList = document.getElementById("dance-list");
    const $gestureList = document.getElementById("gesture-list");
    const $dancing = document.getElementById("dancing-view");
    const $dancingName = document.getElementById("dancing-motion-name");
    const $offline = document.getElementById("offline-view");
    const $success = document.getElementById("success-view");
    const $cancelled = document.getElementById("cancelled-view");
    const $error = document.getElementById("error-view");
    const $errorMsg = document.getElementById("error-message");
    const $modal = document.getElementById("confirm-modal");
    const $confirmText = document.getElementById("confirm-text");
    const $confirmYes = document.getElementById("confirm-yes");
    const $confirmNo = document.getElementById("confirm-no");

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

    // ── Dance cards (paid) ──────────────────────────────

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

        renderGestureGrid();
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

    // ── Gesture tiles (free) ────────────────────────────

    function renderGestureGrid() {
        $gestureList.innerHTML = "";
        expandedCategory = null;

        GESTURE_CATEGORIES.forEach((cat, idx) => {
            const tile = document.createElement("div");
            tile.className = "gesture-tile";
            tile.dataset.idx = idx;

            tile.innerHTML = `
                <div class="gesture-emoji">${cat.emoji}</div>
                <div class="gesture-name">${cat.name}</div>
            `;

            if (cat.variants.length === 1) {
                // Single variant — tap goes straight to confirm
                tile.addEventListener("click", () => {
                    confirmGesture(cat.name, cat.variants[0]);
                });
            } else {
                // Multiple variants — tap toggles expansion
                tile.addEventListener("click", () => {
                    toggleExpand(idx);
                });
            }

            // Variant chips container (hidden by default)
            if (cat.variants.length > 1) {
                const chips = document.createElement("div");
                chips.className = "variant-chips";
                cat.variants.forEach((v) => {
                    const chip = document.createElement("button");
                    chip.className = "variant-chip";
                    chip.textContent = v.label;
                    chip.addEventListener("click", (e) => {
                        e.stopPropagation();
                        confirmGesture(cat.name + " (" + v.label + ")", v);
                    });
                    chips.appendChild(chip);
                });
                tile.appendChild(chips);
            }

            $gestureList.appendChild(tile);
        });
    }

    function toggleExpand(idx) {
        const tiles = $gestureList.querySelectorAll(".gesture-tile");

        if (expandedCategory === idx) {
            // Collapse
            tiles[idx].classList.remove("expanded");
            expandedCategory = null;
        } else {
            // Collapse previous
            if (expandedCategory !== null && tiles[expandedCategory]) {
                tiles[expandedCategory].classList.remove("expanded");
            }
            // Expand new
            tiles[idx].classList.add("expanded");
            expandedCategory = idx;
        }
    }

    // ── Confirm modal ───────────────────────────────────

    function confirmGesture(displayName, variant) {
        pendingGesture = variant;
        $confirmText.textContent = `Perform "${displayName}"?`;
        $modal.classList.remove("hidden");
    }

    function closeModal() {
        $modal.classList.add("hidden");
        pendingGesture = null;
    }

    async function sendGesture(variant) {
        closeModal();
        try {
            await api("POST", "/command", {
                robot_id: robotId,
                action: "play_preset",
                motion_id: variant.motion_id,
                area: variant.area,
            });
        } catch (e) {
            if (e.status === 409) {
                await updateView();
            } else {
                $errorMsg.textContent = e.error || "Failed to send gesture";
                show($error);
            }
        }
    }

    $confirmYes.addEventListener("click", () => {
        if (pendingGesture) sendGesture(pendingGesture);
    });
    $confirmNo.addEventListener("click", closeModal);
    $modal.addEventListener("click", (e) => {
        if (e.target === $modal) closeModal();
    });

    // ── View management ─────────────────────────────────

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
