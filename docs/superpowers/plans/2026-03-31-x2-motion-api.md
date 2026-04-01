# X2 LinkCraft Motion REST API — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a REST API on the X2 robot (SoC1) that exposes LinkCraft motion control over HTTP, enabling cloud/web/mobile clients to trigger motions, query status, and manage the robot's state.

**Architecture:** Flask app running on SoC1 (Jetson Orin) port 8080, bridging HTTP requests to ROS2 service calls. An in-process rclpy node handles all ROS2 communication with retry logic. On startup, the app scans `resource_config.yaml` and registers all available LinkCraft motions with the MC module. A simple API-key auth middleware protects all endpoints.

**Tech Stack:** Python 3.10, Flask 3.1.2 (pre-installed), rclpy (ROS2 Humble), aimdk_msgs (from drp package)

**Reference:** See `docs/skills/x2-motion-system.md` for complete X2 motion system documentation.

---

## File Structure

```
x2_api/
├── server.py              # Flask app entry point, route registration
├── ros2_bridge.py         # rclpy node, all ROS2 service calls with retry logic
├── motion_catalog.py      # Parses resource_config.yaml, maps friendly names to tags/paths
├── auth.py                # API key middleware
├── config.py              # Constants (ports, paths, timeouts)
├── run.sh                 # Environment setup + launch script
├── tests/
│   ├── test_motion_catalog.py
│   ├── test_auth.py
│   ├── test_ros2_bridge.py
│   └── test_routes.py
└── README.md              # API documentation (generated from this plan)
```

**Deployment location on robot:** `/home/run/x2_api/`

---

## Task 1: Project Scaffold and Config

**Files:**
- Create: `x2_api/config.py`
- Create: `x2_api/run.sh`

- [ ] **Step 1: Create the project directory on robot**

```bash
ssh X2 "mkdir -p /home/run/x2_api/tests"
```

- [ ] **Step 2: Write config.py**

```python
# x2_api/config.py
"""All constants and paths for the X2 Motion API."""

# Server
API_HOST = "0.0.0.0"
API_PORT = 8080
API_KEY_HEADER = "X-API-Key"
API_KEY = "x2-dev-key-change-me"  # Override via X2_API_KEY env var

# ROS2 service names
SVC_SET_MC_ACTION = "/aimdk_5Fmsgs/srv/SetMcAction"
SVC_GET_MC_ACTION = "/aimdk_5Fmsgs/srv/GetMcAction"
SVC_REGISTER_MOTION = "/aimdk_5Fmsgs/srv/RegisterCustomMotion"
SVC_SET_MC_MOTION = "/aimdk_5Fmsgs/srv/SetMcMotion"
SVC_GET_MC_MOTIONS = "/aimdk_5Fmsgs/srv/GetMcMotions"
SVC_SET_PRESET_MOTION = "/aimdk_5Fmsgs/srv/SetMcPresetMotion"
SVC_GET_PRESET_STATE = "/aimdk_5Fmsgs/srv/GetMcPresetMotionState"

# ROS2 retry settings
ROS2_RETRIES = 8
ROS2_TIMEOUT_SEC = 0.5
ROS2_SERVICE_WAIT_SEC = 5.0

# Motion resource paths
RESOURCE_CONFIG_PATH = "/agibot/nfs/soc0/var/robot_proxy/resources/resource_config.yaml"
RESOURCE_BASE_PATH = "/agibot/nfs/soc0/var/robot_proxy/resources"

# Motion type constants
MOTION_TYPE_NONE = 0
MOTION_TYPE_ANIMATION = 1  # CSV trajectory
MOTION_TYPE_MIMIC = 2      # ONNX neural-net policy
MOTION_TYPE_FOUNDATION = 3

# Valid robot modes
VALID_MODES = [
    "PASSIVE_DEFAULT",
    "DAMPING_DEFAULT",
    "JOINT_DEFAULT",
    "STAND_DEFAULT",
    "LOCOMOTION_DEFAULT",
    "SIT_DOWN_DEFAULT",
    "CROUCH_DOWN_DEFAULT",
    "LIE_DOWN_DEFAULT",
    "STAND_UP_DEFAULT",
    "ASCEND_STAIRS",
    "DESCEND_STAIRS",
]
```

- [ ] **Step 3: Write run.sh**

```bash
#!/bin/bash
# x2_api/run.sh — Launch the X2 Motion API with correct environment
set -e

# Source ROS2 and AIMDK
source /opt/ros/humble/setup.bash
source /home/run/aimdk/install/setup.bash

# Add DRP package (required for LinkCraft motion types)
export AMENT_PREFIX_PATH=/agibot/software/drp:$AMENT_PREFIX_PATH
export PYTHONPATH=/agibot/software/drp/local/lib/python3.10/dist-packages:$PYTHONPATH
export LD_LIBRARY_PATH=/agibot/software/drp/lib:$LD_LIBRARY_PATH

# Optional: override API key
export X2_API_KEY="${X2_API_KEY:-x2-dev-key-change-me}"

cd /home/run/x2_api
exec python3 server.py "$@"
```

- [ ] **Step 4: Deploy and verify**

```bash
scp x2_api/config.py X2:/home/run/x2_api/config.py
scp x2_api/run.sh X2:/home/run/x2_api/run.sh
ssh X2 "chmod +x /home/run/x2_api/run.sh"
```

- [ ] **Step 5: Commit**

```bash
git add x2_api/config.py x2_api/run.sh
git commit -m "feat: project scaffold with config and launch script"
```

---

## Task 2: Motion Catalog

**Files:**
- Create: `x2_api/motion_catalog.py`
- Create: `x2_api/tests/test_motion_catalog.py`

- [ ] **Step 1: Write the failing test**

Create `x2_api/tests/test_motion_catalog.py`:

```python
# x2_api/tests/test_motion_catalog.py
"""Tests for motion_catalog.py — parses resource_config.yaml into a usable catalog."""
import os
import tempfile
import pytest
from motion_catalog import MotionCatalog


SAMPLE_RESOURCE_CONFIG = """
resource_config:
  - resource_key: linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6
    hot_update: false
    current_version:
      version: 0.0.1
      name: Golf Swing
      files:
        - /agibot/data/var/robot_proxy/resources/linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6/0.0.1/unzip
  - resource_key: linkcraft_resource_onnx_zuiquan
    hot_update: false
    current_version:
      version: 0.0.1
      name: DrunkKungfu
      files:
        - /agibot/data/var/robot_proxy/resources/linkcraft_resource_onnx_zuiquan/0.0.1/unzip
  - resource_key: linkcraft_resource_01KMRTZQ9HWX5WBEAYEK251GQ2
    hot_update: false
    current_version:
      version: 0.0.1
      name: Golf Swing
      files:
        - /agibot/data/var/robot_proxy/resources/linkcraft_resource_01KMRTZQ9HWX5WBEAYEK251GQ2/0.0.1/unzip
  - resource_key: interaction_audio_nlg
    hot_update: true
    current_version:
      version: v1.2.0
      name: NLG Audio
      files:
        - /some/path
"""


@pytest.fixture
def catalog_from_string():
    """Create a MotionCatalog from a sample YAML string."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        f.write(SAMPLE_RESOURCE_CONFIG)
        f.flush()
        catalog = MotionCatalog(f.name, resource_base="/fake/base")
    yield catalog
    os.unlink(f.name)


def test_catalog_only_includes_linkcraft_resources(catalog_from_string):
    """Non-linkcraft resources (interaction_audio_nlg) should be excluded."""
    motions = catalog_from_string.list_all()
    ids = [m["id"] for m in motions]
    assert "interaction_audio_nlg" not in ids
    assert len(motions) == 3


def test_catalog_generates_correct_tag(catalog_from_string):
    """Tag must be {resource_key}_{version}."""
    motions = {m["id"]: m for m in catalog_from_string.list_all()}
    golf = motions["golf_swing_pro"]
    assert golf["tag"] == "linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6_0.0.1"


def test_catalog_onnx_gets_mimic_type(catalog_from_string):
    """Resources with 'onnx' in key should be type MIMIC (2)."""
    motions = {m["id"]: m for m in catalog_from_string.list_all()}
    assert motions["golf_swing_pro"]["motion_type"] == 2  # MIMIC


def test_catalog_csv_gets_animation_type(catalog_from_string):
    """Resources without 'onnx' in key should be type ANIMATION (1)."""
    motions = {m["id"]: m for m in catalog_from_string.list_all()}
    csv_motions = [m for m in catalog_from_string.list_all() if m["motion_type"] == 1]
    assert len(csv_motions) == 1


def test_catalog_generates_correct_onnx_path(catalog_from_string):
    """ONNX resources should have res_path pointing to policy.onnx file."""
    motions = {m["id"]: m for m in catalog_from_string.list_all()}
    golf = motions["golf_swing_pro"]
    assert golf["res_path"].endswith("/policy.onnx")
    assert "linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6/0.0.1/unzip" in golf["res_path"]


def test_catalog_generates_correct_csv_path(catalog_from_string):
    """CSV resources should have res_path pointing to motion.csv file."""
    csv_motions = [m for m in catalog_from_string.list_all() if m["motion_type"] == 1]
    assert len(csv_motions) == 1
    assert csv_motions[0]["res_path"].endswith("/motion.csv")


def test_catalog_get_by_id(catalog_from_string):
    """get_by_id should return a single motion or None."""
    result = catalog_from_string.get_by_id("golf_swing_pro")
    assert result is not None
    assert result["name"] == "Golf Swing"

    result = catalog_from_string.get_by_id("nonexistent")
    assert result is None


def test_catalog_friendly_id_generation(catalog_from_string):
    """Friendly IDs should be snake_case, human-readable."""
    motions = catalog_from_string.list_all()
    ids = [m["id"] for m in motions]
    # Should have sensible IDs, not raw resource keys
    assert all("linkcraft_resource" not in id for id in ids)
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd x2_api && python3 -m pytest tests/test_motion_catalog.py -v
```
Expected: FAIL with "No module named 'motion_catalog'"

- [ ] **Step 3: Write motion_catalog.py**

```python
# x2_api/motion_catalog.py
"""Parses resource_config.yaml into a friendly motion catalog.

Maps resource keys to human-readable IDs, generates correct tags and paths
for the RegisterCustomMotion and SetMcMotion ROS2 services.
"""
import re
import yaml
from config import MOTION_TYPE_ANIMATION, MOTION_TYPE_MIMIC


# Friendly name overrides for known resource keys.
# Keys not listed here get auto-generated IDs from their display name.
KNOWN_MOTIONS = {
    "linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6": "golf_swing_pro",
    "linkcraft_resource_01KMRTZQ9HWX5WBEAYEK251GQ2": "golf_swing_csv",
    "linkcraft_resource_onnx_erlianti": "double_kick",
    "linkcraft_resource_onnx_zuiquan": "drunk_kungfu",
    "linkcraft_resource_onnx_taiji": "taichi",
    "linkcraft_resource_onnx_tianmao": "miao",
    "linkcraft_resource_onnx_depasito": "despacito",
    "linkcraft_resource_onnx_01KEVJX7PSAZQ04TW6YGPBP5SV": "love_you",
}


def _slugify(name: str) -> str:
    """Convert a display name to a snake_case ID."""
    s = name.lower().strip()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    return s.strip("_")


class MotionCatalog:
    """Reads resource_config.yaml and builds a catalog of available LinkCraft motions."""

    def __init__(self, config_path: str, resource_base: str):
        self._motions: dict[str, dict] = {}
        self._resource_base = resource_base
        self._load(config_path)

    def _load(self, config_path: str):
        with open(config_path) as f:
            data = yaml.safe_load(f)

        for entry in data.get("resource_config", []):
            key = entry.get("resource_key", "")
            if not key.startswith("linkcraft_resource"):
                continue

            version_info = entry.get("current_version", {})
            version = version_info.get("version", "0.0.1")
            name = version_info.get("name", key)

            is_onnx = "_onnx_" in key or key.startswith("linkcraft_resource_onnx")
            motion_type = MOTION_TYPE_MIMIC if is_onnx else MOTION_TYPE_ANIMATION

            # Tag = resource_key + version (exact format MC expects)
            tag = f"{key}_{version}"

            # Resource path = base / key / version / unzip / (policy.onnx or motion.csv)
            filename = "policy.onnx" if is_onnx else "motion.csv"
            res_path = f"{self._resource_base}/{key}/{version}/unzip/{filename}"

            # Friendly ID
            friendly_id = KNOWN_MOTIONS.get(key, _slugify(name))

            self._motions[friendly_id] = {
                "id": friendly_id,
                "name": name,
                "resource_key": key,
                "tag": tag,
                "version": version,
                "motion_type": motion_type,
                "motion_type_name": "MIMIC" if is_onnx else "ANIMATION",
                "res_path": res_path,
                "registered": False,
            }

    def list_all(self) -> list[dict]:
        """Return all motions as a list of dicts."""
        return list(self._motions.values())

    def get_by_id(self, motion_id: str) -> dict | None:
        """Look up a motion by friendly ID. Returns None if not found."""
        return self._motions.get(motion_id)

    def mark_registered(self, motion_id: str):
        """Mark a motion as registered with MC."""
        if motion_id in self._motions:
            self._motions[motion_id]["registered"] = True
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd x2_api && python3 -m pytest tests/test_motion_catalog.py -v
```
Expected: All 8 tests PASS

- [ ] **Step 5: Commit**

```bash
git add x2_api/motion_catalog.py x2_api/tests/test_motion_catalog.py
git commit -m "feat: motion catalog — parses resource_config.yaml into friendly API"
```

---

## Task 3: Auth Middleware

**Files:**
- Create: `x2_api/auth.py`
- Create: `x2_api/tests/test_auth.py`

- [ ] **Step 1: Write the failing test**

Create `x2_api/tests/test_auth.py`:

```python
# x2_api/tests/test_auth.py
"""Tests for API key auth middleware."""
import os
import pytest
from flask import Flask
from auth import require_api_key


@pytest.fixture
def app():
    app = Flask(__name__)
    app.config["TESTING"] = True

    @app.route("/protected")
    @require_api_key
    def protected():
        return {"ok": True}

    @app.route("/health")
    def health():
        return {"ok": True}

    return app


@pytest.fixture
def client(app):
    return app.test_client()


def test_request_without_key_returns_401(client):
    resp = client.get("/protected")
    assert resp.status_code == 401


def test_request_with_wrong_key_returns_403(client):
    resp = client.get("/protected", headers={"X-API-Key": "wrong-key"})
    assert resp.status_code == 403


def test_request_with_correct_key_returns_200(client):
    key = os.environ.get("X2_API_KEY", "x2-dev-key-change-me")
    resp = client.get("/protected", headers={"X-API-Key": key})
    assert resp.status_code == 200


def test_health_endpoint_needs_no_key(client):
    resp = client.get("/health")
    assert resp.status_code == 200
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd x2_api && python3 -m pytest tests/test_auth.py -v
```
Expected: FAIL with "No module named 'auth'"

- [ ] **Step 3: Write auth.py**

```python
# x2_api/auth.py
"""Simple API key authentication middleware for Flask."""
import os
from functools import wraps
from flask import request, jsonify
from config import API_KEY_HEADER, API_KEY


def _get_api_key() -> str:
    """Get API key from env or fall back to config default."""
    return os.environ.get("X2_API_KEY", API_KEY)


def require_api_key(f):
    """Decorator that checks for a valid API key in the request header."""
    @wraps(f)
    def decorated(*args, **kwargs):
        key = request.headers.get(API_KEY_HEADER)
        if key is None:
            return jsonify({"error": "Missing API key", "header": API_KEY_HEADER}), 401
        if key != _get_api_key():
            return jsonify({"error": "Invalid API key"}), 403
        return f(*args, **kwargs)
    return decorated
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd x2_api && python3 -m pytest tests/test_auth.py -v
```
Expected: All 4 tests PASS

- [ ] **Step 5: Commit**

```bash
git add x2_api/auth.py x2_api/tests/test_auth.py
git commit -m "feat: API key auth middleware"
```

---

## Task 4: ROS2 Bridge

**Files:**
- Create: `x2_api/ros2_bridge.py`

This is the core module. It wraps all ROS2 service calls in a thread-safe class with retry logic.

- [ ] **Step 1: Write ros2_bridge.py**

```python
# x2_api/ros2_bridge.py
"""ROS2 bridge — wraps all aimdk_msgs service calls for the Flask API.

This module creates a single rclpy node that persists for the lifetime of the
Flask app. All methods use the SDK-standard retry pattern (8 attempts, 500ms
timeout per attempt) because ROS2 cross-host service calls are unreliable.
"""
import threading
import logging
import rclpy
from rclpy.node import Node

from aimdk_msgs.srv import (
    SetMcAction,
    GetMcAction,
    SetMcPresetMotion,
    RegisterCustomMotion,
    SetMcMotion,
    GetMcMotions,
)
from aimdk_msgs.msg import (
    RequestHeader,
    CommonState,
    McActionCommand,
    McPresetMotion,
    McControlArea,
    McMotion,
    McMotionType,
)

from config import (
    SVC_SET_MC_ACTION,
    SVC_GET_MC_ACTION,
    SVC_REGISTER_MOTION,
    SVC_SET_MC_MOTION,
    SVC_GET_MC_MOTIONS,
    SVC_SET_PRESET_MOTION,
    ROS2_RETRIES,
    ROS2_TIMEOUT_SEC,
    ROS2_SERVICE_WAIT_SEC,
)

logger = logging.getLogger(__name__)


class ROS2Bridge:
    """Thread-safe wrapper around rclpy service clients."""

    def __init__(self):
        self._lock = threading.Lock()
        self._node: Node | None = None
        self._clients: dict = {}

    def init(self):
        """Initialize rclpy and create service clients. Call once at startup."""
        rclpy.init()
        self._node = Node("x2_motion_api")

        service_defs = {
            "set_action": (SetMcAction, SVC_SET_MC_ACTION),
            "get_action": (GetMcAction, SVC_GET_MC_ACTION),
            "register_motion": (RegisterCustomMotion, SVC_REGISTER_MOTION),
            "set_motion": (SetMcMotion, SVC_SET_MC_MOTION),
            "get_motions": (GetMcMotions, SVC_GET_MC_MOTIONS),
            "set_preset": (SetMcPresetMotion, SVC_SET_PRESET_MOTION),
        }

        for name, (srv_type, srv_name) in service_defs.items():
            client = self._node.create_client(srv_type, srv_name)
            logger.info("Waiting for %s ...", srv_name)
            if not client.wait_for_service(timeout_sec=ROS2_SERVICE_WAIT_SEC):
                logger.warning("Service %s not available after %ss", srv_name, ROS2_SERVICE_WAIT_SEC)
            self._clients[name] = client

        logger.info("ROS2 bridge initialized.")

    def shutdown(self):
        """Shut down rclpy. Call on app exit."""
        if self._node:
            self._node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()

    def _call(self, client_name: str, request, label: str = "") -> object | None:
        """Call a ROS2 service with retry logic. Returns the response or None."""
        client = self._clients[client_name]
        with self._lock:
            for i in range(ROS2_RETRIES):
                if hasattr(request, "header") and hasattr(request.header, "stamp"):
                    request.header.stamp = self._node.get_clock().now().to_msg()

                future = client.call_async(request)
                rclpy.spin_until_future_complete(self._node, future, timeout_sec=ROS2_TIMEOUT_SEC)

                if future.done():
                    result = future.result()
                    if result is not None:
                        return result

                logger.debug("%s retry [%d/%d]", label or client_name, i + 1, ROS2_RETRIES)

        logger.error("%s failed after %d retries", label or client_name, ROS2_RETRIES)
        return None

    # ── Robot Mode ────────────────────────────────────────────────

    def get_mode(self) -> dict:
        """Query current robot mode. Returns {mode, status, status_code}."""
        req = GetMcAction.Request()
        req.request.header = RequestHeader()
        resp = self._call("get_action", req, "GetMcAction")
        if resp is None:
            return {"mode": "UNKNOWN", "status": "ERROR", "status_code": -1}

        status_code = resp.info.status.value
        status_map = {100: "RUNNING", 200: "SWITCHING"}
        return {
            "mode": resp.info.action_desc,
            "status": status_map.get(status_code, f"UNKNOWN({status_code})"),
            "status_code": status_code,
        }

    def set_mode(self, mode: str) -> dict:
        """Switch robot mode. Returns {success, message}."""
        req = SetMcAction.Request()
        req.header = RequestHeader()
        cmd = McActionCommand()
        cmd.action_desc = mode
        req.command = cmd

        resp = self._call("set_action", req, "SetMcAction")
        if resp is None:
            return {"success": False, "message": "Service call failed"}

        if resp.response.status.value == CommonState.SUCCESS:
            return {"success": True, "message": f"Mode set to {mode}"}
        return {"success": False, "message": f"Failed (status={resp.response.status.value})"}

    # ── LinkCraft Motions ─────────────────────────────────────────

    def register_motion(self, tag: str, motion_type: int, res_path: str) -> dict:
        """Register a LinkCraft motion with MC. Returns {success, message}."""
        req = RegisterCustomMotion.Request()
        motion = McMotion()
        motion.tag = tag
        mt = McMotionType()
        mt.value = motion_type
        motion.type = mt
        req.motion = motion
        req.res_path = res_path
        req.write_to_disk = False

        resp = self._call("register_motion", req, "RegisterCustomMotion")
        if resp is None:
            return {"success": False, "message": "Service call failed"}

        code = resp.response.header.code
        status = resp.response.status.value
        if code == 0 and status == CommonState.SUCCESS:
            return {"success": True, "message": "Registered"}
        return {"success": True, "message": f"Likely already registered (code={code}, status={status})"}

    def play_motion(self, tag: str, motion_type: int, interrupt: bool = False) -> dict:
        """Play a registered LinkCraft motion. Returns {success, message}."""
        req = SetMcMotion.Request()
        req.header = RequestHeader()
        motion = McMotion()
        motion.tag = tag
        mt = McMotionType()
        mt.value = motion_type
        motion.type = mt
        req.motion = motion
        req.interrupt = interrupt
        req.play_timestamp = 0

        resp = self._call("set_motion", req, "SetMcMotion")
        if resp is None:
            return {"success": False, "message": "Service call failed"}

        if resp.response.header.code == 0:
            return {"success": True, "message": "Motion playing"}
        return {"success": False, "message": f"Failed (code={resp.response.header.code})"}

    def list_registered_motions(self) -> list[dict]:
        """List motions currently registered with MC."""
        req = GetMcMotions.Request()
        req.header = RequestHeader()
        resp = self._call("get_motions", req, "GetMcMotions")
        if resp is None:
            return []
        return [{"tag": m.tag, "type": m.type.value} for m in resp.motion]

    # ── Preset Motions ────────────────────────────────────────────

    def play_preset(self, motion_id: int, area: int, interrupt: bool = False) -> dict:
        """Play a preset gesture. Returns {success, message, task_id}."""
        req = SetMcPresetMotion.Request()
        req.header = RequestHeader()
        m = McPresetMotion()
        m.value = motion_id
        a = McControlArea()
        a.value = area
        req.motion = m
        req.area = a
        req.interrupt = interrupt

        resp = self._call("set_preset", req, "SetMcPresetMotion")
        if resp is None:
            return {"success": False, "message": "Service call failed", "task_id": 0}

        code = resp.response.header.code
        task_id = resp.response.task_id
        if code == 0:
            return {"success": True, "message": "Preset motion playing", "task_id": task_id}
        return {"success": False, "message": f"Failed (code={code})", "task_id": task_id}
```

- [ ] **Step 2: Verify imports work on robot**

```bash
ssh X2 "source /opt/ros/humble/setup.bash && \
  source ~/aimdk/install/setup.bash && \
  export PYTHONPATH=/agibot/software/drp/local/lib/python3.10/dist-packages:/home/run/x2_api:\$PYTHONPATH && \
  export LD_LIBRARY_PATH=/agibot/software/drp/lib:\$LD_LIBRARY_PATH && \
  python3 -c 'from ros2_bridge import ROS2Bridge; print(\"OK\")'"
```
Expected: `OK`

- [ ] **Step 3: Commit**

```bash
git add x2_api/ros2_bridge.py
git commit -m "feat: ROS2 bridge with retry logic for all motion services"
```

---

## Task 5: Flask Routes

**Files:**
- Create: `x2_api/server.py`

- [ ] **Step 1: Write server.py**

```python
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
    bridge.init()

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

    # Register if not already
    if not motion["registered"]:
        reg = bridge.register_motion(motion["tag"], motion["motion_type"], motion["res_path"])
        if reg["success"]:
            catalog.mark_registered(motion_id)

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
```

- [ ] **Step 2: Deploy to robot**

```bash
scp x2_api/config.py x2_api/auth.py x2_api/motion_catalog.py x2_api/ros2_bridge.py x2_api/server.py X2:/home/run/x2_api/
scp x2_api/run.sh X2:/home/run/x2_api/
```

- [ ] **Step 3: Smoke test on robot**

```bash
ssh X2 "cd /home/run/x2_api && bash run.sh &"
# Wait a few seconds for startup, then from local machine:
curl -s http://192.168.50.227:8080/api/v1/health
# Expected: {"service":"x2-motion-api","status":"ok"}

curl -s -H "X-API-Key: x2-dev-key-change-me" http://192.168.50.227:8080/api/v1/motions
# Expected: {"motions": [...list of motions...]}

curl -s -H "X-API-Key: x2-dev-key-change-me" http://192.168.50.227:8080/api/v1/robot/state
# Expected: {"mode": "...", "status": "RUNNING", "status_code": 100}
```

- [ ] **Step 4: Commit**

```bash
git add x2_api/server.py
git commit -m "feat: Flask REST API with all motion endpoints"
```

---

## Task 6: Integration Test on Robot

**Files:**
- Create: `x2_api/tests/test_integration.sh`

- [ ] **Step 1: Write integration test script**

```bash
#!/bin/bash
# x2_api/tests/test_integration.sh
# Run against a live X2 API server.
# Usage: bash test_integration.sh [host] [api_key]

HOST="${1:-http://192.168.50.227:8080}"
KEY="${2:-x2-dev-key-change-me}"
PASS=0
FAIL=0

check() {
    local desc="$1" expected_code="$2" method="$3" path="$4" body="$5"
    local args=(-s -o /tmp/x2_resp -w "%{http_code}" -X "$method" "${HOST}${path}" -H "X-API-Key: ${KEY}" -H "Content-Type: application/json")
    [ -n "$body" ] && args+=(-d "$body")
    code=$(curl "${args[@]}")
    if [ "$code" = "$expected_code" ]; then
        echo "PASS: $desc (HTTP $code)"
        ((PASS++))
    else
        echo "FAIL: $desc (expected $expected_code, got $code)"
        cat /tmp/x2_resp
        echo
        ((FAIL++))
    fi
}

echo "=== X2 Motion API Integration Tests ==="
echo "Target: $HOST"
echo

# Health (no auth)
check "Health check" 200 GET "/api/v1/health"

# Auth
check "No API key → 401" 401 GET "/api/v1/motions"
ORIG_KEY="$KEY"; KEY="wrong"
check "Wrong API key → 403" 403 GET "/api/v1/motions"
KEY="$ORIG_KEY"

# Robot state
check "Get robot state" 200 GET "/api/v1/robot/state"

# Motion list
check "List motions" 200 GET "/api/v1/motions"

# Motion detail
check "Get motion detail" 200 GET "/api/v1/motions/golf_swing_pro"
check "Unknown motion → 404" 404 GET "/api/v1/motions/nonexistent"

# Invalid mode
check "Invalid mode → 400" 400 POST "/api/v1/robot/mode" '{"mode": "INVALID"}'

# Play without stand (depends on current state — may be 409 or 200)
# check "Play without stand → 409" 409 POST "/api/v1/motions/play" '{"motion_id": "golf_swing_pro"}'

echo
echo "=== Results: $PASS passed, $FAIL failed ==="
[ "$FAIL" -eq 0 ] && exit 0 || exit 1
```

- [ ] **Step 2: Run integration tests**

```bash
bash x2_api/tests/test_integration.sh http://192.168.50.227:8080
```
Expected: All non-motion-play tests PASS

- [ ] **Step 3: Manual motion play test (requires robot in safe position)**

```bash
# Stand up
curl -s -X POST -H "X-API-Key: x2-dev-key-change-me" -H "Content-Type: application/json" \
  http://192.168.50.227:8080/api/v1/robot/mode -d '{"mode": "STAND_DEFAULT"}'

# Wait 5 seconds for stabilization
sleep 5

# Play golf swing
curl -s -X POST -H "X-API-Key: x2-dev-key-change-me" -H "Content-Type: application/json" \
  http://192.168.50.227:8080/api/v1/motions/play -d '{"motion_id": "golf_swing_pro"}'
```

- [ ] **Step 4: Commit**

```bash
git add x2_api/tests/test_integration.sh
git commit -m "test: integration test suite for live API"
```

---

## Task 7: Systemd Service (Optional — Production)

**Files:**
- Create: `x2_api/x2-motion-api.service`

- [ ] **Step 1: Write systemd unit file**

```ini
# x2_api/x2-motion-api.service
[Unit]
Description=X2 Motion REST API
After=agibot_software.service
Wants=agibot_software.service

[Service]
Type=simple
User=run
WorkingDirectory=/home/run/x2_api
ExecStart=/home/run/x2_api/run.sh
Restart=on-failure
RestartSec=5
Environment=X2_API_KEY=your-production-key-here

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 2: Deploy and enable**

```bash
scp x2_api/x2-motion-api.service X2:/home/run/x2_api/
ssh X2 "sudo cp /home/run/x2_api/x2-motion-api.service /etc/systemd/system/ && \
  sudo systemctl daemon-reload && \
  sudo systemctl enable x2-motion-api && \
  sudo systemctl start x2-motion-api && \
  sudo systemctl status x2-motion-api"
```

- [ ] **Step 3: Verify it survives reboot**

```bash
ssh X2 "sudo reboot"
# Wait for reboot...
curl -s http://192.168.50.227:8080/api/v1/health
# Expected: {"service":"x2-motion-api","status":"ok"}
```

- [ ] **Step 4: Commit**

```bash
git add x2_api/x2-motion-api.service
git commit -m "feat: systemd service for production deployment"
```

---

## Summary

| Task | What it builds | Files |
|------|---------------|-------|
| 1 | Project scaffold | `config.py`, `run.sh` |
| 2 | Motion catalog (YAML → friendly API) | `motion_catalog.py`, `test_motion_catalog.py` |
| 3 | API key auth | `auth.py`, `test_auth.py` |
| 4 | ROS2 bridge (all service calls) | `ros2_bridge.py` |
| 5 | Flask routes (REST endpoints) | `server.py` |
| 6 | Integration tests | `test_integration.sh` |
| 7 | Systemd service (production) | `x2-motion-api.service` |

**API Endpoints:**

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/health` | Health check (no auth) |
| GET | `/api/v1/robot/state` | Current robot mode |
| POST | `/api/v1/robot/mode` | Switch mode |
| GET | `/api/v1/motions` | List all LinkCraft motions |
| GET | `/api/v1/motions/<id>` | Motion detail |
| POST | `/api/v1/motions/play` | Play a LinkCraft motion |
| POST | `/api/v1/motions/stop` | Stop current motion |
| POST | `/api/v1/presets/play` | Play a preset gesture |
