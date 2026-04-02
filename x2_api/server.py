# x2_api/server.py
"""X2 Motion REST API — Flask application entry point."""
import os
import sys
import logging
import atexit
from flask import Flask, request, jsonify
from flask_cors import CORS

from config import (
    API_HOST,
    API_PORT,
    RESOURCE_CONFIG_PATH,
    RESOURCE_BASE_PATH,
    VALID_MODES,
)
from auth import require_api_key
from motion_catalog import MotionCatalog
from ros2_bridge import ROS2Bridge

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("x2_api")

# ── Initialize components ─────────────────────────────────────

app = Flask(__name__)
CORS(app)

catalog = MotionCatalog(RESOURCE_CONFIG_PATH, RESOURCE_BASE_PATH)
bridge = ROS2Bridge()


def startup():
    """Initialize ROS2 and register all motions."""
    import time
    bridge.init()

    # Wait for MC to be fully ready — at boot, agibot_software and this
    # service start simultaneously.  The MC's motion subsystem needs time.
    logger.info("Waiting for MC motion subsystem to be ready...")
    for attempt in range(10):
        mode = bridge.get_mode()
        if mode["mode"] != "UNKNOWN" and mode["status_code"] >= 0:
            logger.info("MC is ready (mode=%s, attempt=%d).", mode["mode"], attempt + 1)
            break
        logger.info("  MC not ready yet (attempt %d/10), waiting 3s...", attempt + 1)
        time.sleep(3)

    logger.info("Registering %d LinkCraft motions with MC...", len(catalog.list_all()))
    for motion in catalog.list_all():
        result = bridge.register_motion(
            tag=motion["tag"],
            motion_type=motion["motion_type"],
            res_path=motion["res_path"],
        )
        if result["success"]:
            catalog.mark_registered(motion["id"])
            logger.info("  Registered: %s (%s) — %s", motion["id"], motion["tag"], result["message"])
        else:
            logger.error("  FAILED: %s — %s", motion["id"], result["message"])

    logger.info("Startup complete. %d motions available.", len(catalog.list_all()))


@atexit.register
def shutdown():
    bridge.shutdown()


# ── Health ────────────────────────────────────────────────────

@app.route("/api/v1/health", methods=["GET"])
def health():
    """Health check — no auth required."""
    return jsonify({"status": "ok", "service": "x2-motion-api"})


# ── Robot State ───────────────────────────────────────────────

@app.route("/api/v1/robot/state", methods=["GET"])
@require_api_key
def get_robot_state():
    """Get current robot mode and status."""
    return jsonify(bridge.get_mode())


@app.route("/api/v1/robot/mode", methods=["POST"])
@require_api_key
def set_robot_mode():
    """Switch robot mode. Body: {"mode": "STAND_DEFAULT"}"""
    data = request.get_json(silent=True) or {}
    mode = data.get("mode", "")
    if mode not in VALID_MODES:
        return jsonify({"error": f"Invalid mode. Valid: {VALID_MODES}"}), 400
    return jsonify(bridge.set_mode(mode))


# ── LinkCraft Motions ─────────────────────────────────────────

@app.route("/api/v1/motions", methods=["GET"])
@require_api_key
def list_motions():
    """List all available LinkCraft motions."""
    motions = []
    for m in catalog.list_all():
        motions.append({
            "id": m["id"],
            "name": m["name"],
            "type": m["motion_type_name"],
            "registered": m["registered"],
        })
    return jsonify({"motions": motions})


@app.route("/api/v1/motions/<motion_id>", methods=["GET"])
@require_api_key
def get_motion(motion_id: str):
    """Get details for a specific motion."""
    motion = catalog.get_by_id(motion_id)
    if motion is None:
        return jsonify({"error": f"Motion '{motion_id}' not found"}), 404
    return jsonify(motion)


@app.route("/api/v1/motions/play", methods=["POST"])
@require_api_key
def play_motion():
    """Play a LinkCraft motion. Body: {"motion_id": "golf_swing_pro", "interrupt": false, "auto_stand": false}"""
    data = request.get_json(silent=True) or {}
    motion_id = data.get("motion_id", "")
    interrupt = data.get("interrupt", False)
    auto_stand = data.get("auto_stand", False)

    motion = catalog.get_by_id(motion_id)
    if motion is None:
        available = [m["id"] for m in catalog.list_all()]
        return jsonify({"error": f"Motion '{motion_id}' not found", "available": available}), 404

    # Safety check: must be in STAND_DEFAULT
    state = bridge.get_mode()
    if state["mode"] != "STAND_DEFAULT":
        if auto_stand:
            result = bridge.set_mode("STAND_DEFAULT")
            if not result["success"]:
                return jsonify({"error": "Failed to auto-stand", "detail": result["message"]}), 500
            # Note: caller should wait a few seconds before the motion actually executes well
        else:
            return jsonify({
                "error": f"Robot must be in STAND_DEFAULT (currently: {state['mode']})",
                "hint": "Set auto_stand=true to auto-switch, or POST /api/v1/robot/mode first",
            }), 409

    # Always re-register before play — registration is idempotent and cheap.
    # At boot the MC may not be ready, causing silent registration failures
    # (status=UNKNOWN instead of SUCCESS).  Re-registering here ensures the
    # motion is loaded before we try to play it.
    reg = bridge.register_motion(motion["tag"], motion["motion_type"], motion["res_path"])
    if reg["success"]:
        catalog.mark_registered(motion_id)
    else:
        return jsonify({"error": "Failed to register motion", "detail": reg["message"]}), 500

    result = bridge.play_motion(motion["tag"], motion["motion_type"], interrupt)
    result["motion_id"] = motion_id
    result["motion_name"] = motion["name"]
    return jsonify(result)


@app.route("/api/v1/motions/stop", methods=["POST"])
@require_api_key
def stop_motion():
    """Stop current motion by switching back to STAND_DEFAULT."""
    result = bridge.set_mode("STAND_DEFAULT")
    return jsonify(result)


# ── Preset Gestures ───────────────────────────────────────────

@app.route("/api/v1/presets/play", methods=["POST"])
@require_api_key
def play_preset():
    """Play a preset gesture. Body: {"motion_id": 1002, "area": 2, "interrupt": false}"""
    data = request.get_json(silent=True) or {}
    motion_id = data.get("motion_id")
    area = data.get("area", 2)
    interrupt = data.get("interrupt", False)

    if motion_id is None:
        return jsonify({"error": "motion_id required (e.g. 1002 for wave)"}), 400

    result = bridge.play_preset(int(motion_id), int(area), interrupt)
    return jsonify(result)


# ── Main ──────────────────────────────────────────────────────

if __name__ == "__main__":
    startup()
    app.run(host=API_HOST, port=API_PORT, debug=False, threaded=True)
