# X2 Dance Kiosk — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a pay-to-dance kiosk system: QR code → mobile web page → Stripe payment → AWS IoT Core MQTT → robot performs the dance.

**Architecture:** Serverless cloud (API Gateway + Lambda + IoT Core + DynamoDB) handles payment and command routing. Robot runs an MQTT client alongside the existing REST API, both sharing `ros2_bridge.py` and `motion_catalog.py`. Static mobile web page on S3/CloudFront.

**Tech Stack:** Python 3.10, awsiotsdk, boto3, stripe (Python), AWS SAM (CloudFormation), vanilla HTML/CSS/JS

**Reference:** See `docs/superpowers/specs/2026-03-31-aws-dance-kiosk-design.md` for the full design spec.

---

## File Structure

```
AGIBOT/
├── x2_api/                          # Robot-side (existing + new)
│   ├── config.py                    # MODIFY — add MQTT settings
│   ├── mqtt_client.py               # CREATE — MQTT client for IoT Core
│   ├── mqtt_run.sh                  # CREATE — MQTT client launcher
│   ├── x2-mqtt-client.service       # CREATE — systemd unit
│   └── tests/
│       └── test_mqtt_client.py      # CREATE — MQTT client tests
│
├── cloud/                           # Cloud-side (all new)
│   ├── lambdas/
│   │   ├── create_checkout.py       # CREATE — Stripe checkout session
│   │   ├── handle_webhook.py        # CREATE — Stripe webhook → MQTT
│   │   ├── get_status.py            # CREATE — robot status query
│   │   └── requirements.txt         # CREATE — Lambda dependencies
│   ├── web/
│   │   ├── index.html               # CREATE — mobile SPA
│   │   ├── style.css                # CREATE — mobile styles
│   │   └── app.js                   # CREATE — SPA logic
│   ├── infra/
│   │   └── template.yaml            # CREATE — SAM/CloudFormation
│   └── scripts/
│       └── provision_robot.py       # CREATE — IoT Thing provisioning
│
└── .gitignore                       # MODIFY — add certs/, .env
```

---

## Task 1: MQTT Config and .gitignore Update

**Files:**
- Modify: `x2_api/config.py`
- Modify: `.gitignore`

- [ ] **Step 1: Add MQTT settings to config.py**

Add the following block at the end of `x2_api/config.py`:

```python
# MQTT / AWS IoT Core
MQTT_ROBOT_ID = "x2-001"  # Override via X2_ROBOT_ID env var
MQTT_IOT_ENDPOINT = ""     # Override via X2_IOT_ENDPOINT env var (required)
MQTT_CERT_PATH = "/home/run/x2_api/certs"  # Override via X2_CERT_PATH env var
MQTT_HEARTBEAT_INTERVAL_SEC = 30
MQTT_COMMAND_TOPIC_PREFIX = "x2/{robot_id}/command"
MQTT_STATUS_TOPIC = "x2/{robot_id}/status"
MQTT_HEARTBEAT_TOPIC = "x2/{robot_id}/status/heartbeat"
```

- [ ] **Step 2: Update .gitignore**

Add these lines to `.gitignore`:

```
# AWS IoT certs (never commit)
x2_api/certs/
certs/

# Environment files
.env
.env.*

# SAM build artifacts
cloud/infra/.aws-sam/
```

- [ ] **Step 3: Commit**

```bash
git add x2_api/config.py .gitignore
git commit -m "feat: add MQTT config constants and gitignore certs"
```

---

## Task 2: Robot MQTT Client — Tests

**Files:**
- Create: `x2_api/tests/test_mqtt_client.py`

These tests mock awsiotsdk and ros2_bridge to test the MQTT client's message handling logic without needing a real AWS connection or ROS2 environment.

- [ ] **Step 1: Write the test file**

Create `x2_api/tests/test_mqtt_client.py`:

```python
# x2_api/tests/test_mqtt_client.py
"""Tests for MQTT client message handling logic."""
import json
import pytest
from unittest.mock import MagicMock, patch

# We test the message handler functions in isolation.
# The actual MQTT connection and ROS2 bridge are mocked.


# ── Helpers ──────────────────────────────────────────────────

def make_command(action, payload=None, request_id="test-req-001"):
    """Build a command message dict."""
    return {
        "request_id": request_id,
        "action": action,
        "payload": payload or {},
        "timestamp": "2026-03-31T12:00:00Z",
    }


# ── Import with mocks ───────────────────────────────────────

@pytest.fixture
def mqtt_handler():
    """Import MqttCommandHandler with mocked dependencies."""
    mock_bridge = MagicMock()
    mock_catalog = MagicMock()
    mock_publish = MagicMock()

    # Mock the catalog to return a known motion
    mock_catalog.get_by_id.return_value = {
        "id": "golf_swing_pro",
        "name": "Golf Swing",
        "tag": "linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6_0.0.1",
        "motion_type": 2,
        "res_path": "/fake/path/policy.onnx",
        "registered": True,
    }
    mock_catalog.list_all.return_value = [mock_catalog.get_by_id.return_value]

    # We need to import after setting up sys.path
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
    from mqtt_client import MqttCommandHandler

    handler = MqttCommandHandler(
        bridge=mock_bridge,
        catalog=mock_catalog,
        publish_fn=mock_publish,
        robot_id="x2-001",
    )
    return handler, mock_bridge, mock_catalog, mock_publish


def test_play_motion_calls_bridge(mqtt_handler):
    """play_motion command should call bridge.play_motion with correct args."""
    handler, bridge, catalog, publish = mqtt_handler
    bridge.get_mode.return_value = {"mode": "STAND_DEFAULT", "status": "RUNNING", "status_code": 100}
    bridge.play_motion.return_value = {"success": True, "message": "Motion playing"}

    cmd = make_command("play_motion", {"motion_id": "golf_swing_pro", "auto_stand": False})
    handler.handle_command(cmd)

    bridge.play_motion.assert_called_once_with(
        "linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6_0.0.1", 2, False
    )


def test_play_motion_publishes_status(mqtt_handler):
    """After playing a motion, handler should publish dancing status."""
    handler, bridge, catalog, publish = mqtt_handler
    bridge.get_mode.return_value = {"mode": "STAND_DEFAULT", "status": "RUNNING", "status_code": 100}
    bridge.play_motion.return_value = {"success": True, "message": "Motion playing"}

    cmd = make_command("play_motion", {"motion_id": "golf_swing_pro"})
    handler.handle_command(cmd)

    publish.assert_called()
    status_msg = json.loads(publish.call_args[0][1])
    assert status_msg["state"] == "dancing"
    assert status_msg["current_motion"] == "golf_swing_pro"


def test_play_motion_rejects_when_busy(mqtt_handler):
    """If already dancing, handler should publish rejection."""
    handler, bridge, catalog, publish = mqtt_handler
    handler._state = "dancing"

    cmd = make_command("play_motion", {"motion_id": "golf_swing_pro"})
    handler.handle_command(cmd)

    bridge.play_motion.assert_not_called()
    publish.assert_called()
    status_msg = json.loads(publish.call_args[0][1])
    assert status_msg["state"] == "dancing"


def test_play_motion_unknown_motion(mqtt_handler):
    """Unknown motion_id should publish error status."""
    handler, bridge, catalog, publish = mqtt_handler
    catalog.get_by_id.return_value = None

    cmd = make_command("play_motion", {"motion_id": "nonexistent"})
    handler.handle_command(cmd)

    bridge.play_motion.assert_not_called()
    publish.assert_called()
    status_msg = json.loads(publish.call_args[0][1])
    assert "error" in status_msg


def test_play_motion_auto_stand(mqtt_handler):
    """auto_stand=true should call set_mode before playing."""
    handler, bridge, catalog, publish = mqtt_handler
    bridge.get_mode.return_value = {"mode": "LOCOMOTION_DEFAULT", "status": "RUNNING", "status_code": 100}
    bridge.set_mode.return_value = {"success": True, "message": "Mode set"}
    bridge.play_motion.return_value = {"success": True, "message": "Motion playing"}

    cmd = make_command("play_motion", {"motion_id": "golf_swing_pro", "auto_stand": True})
    handler.handle_command(cmd)

    bridge.set_mode.assert_called_once_with("STAND_DEFAULT")
    bridge.play_motion.assert_called_once()


def test_stop_motion_switches_to_stand(mqtt_handler):
    """stop_motion should call set_mode(STAND_DEFAULT) and reset state."""
    handler, bridge, catalog, publish = mqtt_handler
    handler._state = "dancing"
    bridge.set_mode.return_value = {"success": True, "message": "Mode set"}

    cmd = make_command("stop_motion")
    handler.handle_command(cmd)

    bridge.set_mode.assert_called_once_with("STAND_DEFAULT")
    publish.assert_called()
    status_msg = json.loads(publish.call_args[0][1])
    assert status_msg["state"] == "idle"


def test_set_mode_calls_bridge(mqtt_handler):
    """set_mode command should call bridge.set_mode."""
    handler, bridge, catalog, publish = mqtt_handler
    bridge.set_mode.return_value = {"success": True, "message": "Mode set"}

    cmd = make_command("set_mode", {"mode": "STAND_DEFAULT"})
    handler.handle_command(cmd)

    bridge.set_mode.assert_called_once_with("STAND_DEFAULT")


def test_invalid_action_publishes_error(mqtt_handler):
    """Unknown action should publish error."""
    handler, bridge, catalog, publish = mqtt_handler

    cmd = make_command("do_a_backflip")
    handler.handle_command(cmd)

    publish.assert_called()
    status_msg = json.loads(publish.call_args[0][1])
    assert "error" in status_msg


def test_malformed_message_publishes_error(mqtt_handler):
    """Missing required fields should publish error."""
    handler, bridge, catalog, publish = mqtt_handler

    handler.handle_command({"garbage": True})

    publish.assert_called()
    status_msg = json.loads(publish.call_args[0][1])
    assert "error" in status_msg
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd x2_api && python3 -m pytest tests/test_mqtt_client.py -v
```
Expected: FAIL with `ModuleNotFoundError: No module named 'mqtt_client'`

- [ ] **Step 3: Commit**

```bash
git add x2_api/tests/test_mqtt_client.py
git commit -m "test: MQTT client command handler tests (red)"
```

---

## Task 3: Robot MQTT Client — Implementation

**Files:**
- Create: `x2_api/mqtt_client.py`
- Create: `x2_api/mqtt_run.sh`
- Create: `x2_api/x2-mqtt-client.service`

- [ ] **Step 1: Write mqtt_client.py**

```python
# x2_api/mqtt_client.py
"""MQTT client for AWS IoT Core — receives dance commands, controls robot.

Runs as a standalone process alongside the Flask REST API.
Both share ros2_bridge.py and motion_catalog.py.
"""
import os
import sys
import json
import time
import logging
import threading
from datetime import datetime, timezone

from awscrt import io, mqtt
from awsiot import mqtt_connection_builder

from config import (
    MQTT_ROBOT_ID,
    MQTT_IOT_ENDPOINT,
    MQTT_CERT_PATH,
    MQTT_HEARTBEAT_INTERVAL_SEC,
    MQTT_COMMAND_TOPIC_PREFIX,
    MQTT_STATUS_TOPIC,
    MQTT_HEARTBEAT_TOPIC,
    RESOURCE_CONFIG_PATH,
    RESOURCE_BASE_PATH,
    VALID_MODES,
)
from ros2_bridge import ROS2Bridge
from motion_catalog import MotionCatalog

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("x2_mqtt")


class MqttCommandHandler:
    """Handles incoming MQTT commands and dispatches to ros2_bridge."""

    VALID_ACTIONS = {"play_motion", "stop_motion", "set_mode", "play_preset"}

    def __init__(self, bridge, catalog, publish_fn, robot_id: str):
        self._bridge = bridge
        self._catalog = catalog
        self._publish = publish_fn
        self._robot_id = robot_id
        self._state = "idle"
        self._current_motion = None

    def _now(self) -> str:
        return datetime.now(timezone.utc).isoformat()

    def _publish_status(self, extra: dict | None = None):
        """Publish current state to the status topic."""
        topic = MQTT_STATUS_TOPIC.format(robot_id=self._robot_id)
        msg = {
            "robot_id": self._robot_id,
            "state": self._state,
            "current_motion": self._current_motion,
            "mode": self._bridge.get_mode().get("mode", "UNKNOWN") if self._state != "offline" else "UNKNOWN",
            "timestamp": self._now(),
        }
        if extra:
            msg.update(extra)
        self._publish(topic, json.dumps(msg))

    def _publish_error(self, request_id: str, error: str):
        """Publish an error response to the status topic."""
        topic = MQTT_STATUS_TOPIC.format(robot_id=self._robot_id)
        msg = {
            "robot_id": self._robot_id,
            "state": self._state,
            "current_motion": self._current_motion,
            "error": error,
            "request_id": request_id,
            "timestamp": self._now(),
        }
        self._publish(topic, json.dumps(msg))

    def handle_command(self, cmd: dict):
        """Process a single command message."""
        action = cmd.get("action")
        request_id = cmd.get("request_id", "unknown")
        payload = cmd.get("payload", {})

        if not action:
            self._publish_error(request_id, "Missing 'action' field")
            return

        if action not in self.VALID_ACTIONS:
            self._publish_error(request_id, f"Unknown action: {action}")
            return

        if action == "play_motion":
            self._handle_play_motion(request_id, payload)
        elif action == "stop_motion":
            self._handle_stop_motion(request_id)
        elif action == "set_mode":
            self._handle_set_mode(request_id, payload)
        elif action == "play_preset":
            self._handle_play_preset(request_id, payload)

    def _handle_play_motion(self, request_id: str, payload: dict):
        motion_id = payload.get("motion_id", "")
        interrupt = payload.get("interrupt", False)
        auto_stand = payload.get("auto_stand", False)

        # Reject if busy
        if self._state == "dancing":
            self._publish_status()
            return

        # Look up motion
        motion = self._catalog.get_by_id(motion_id)
        if motion is None:
            available = [m["id"] for m in self._catalog.list_all()]
            self._publish_error(request_id, f"Unknown motion '{motion_id}'. Available: {available}")
            return

        # Auto-stand if needed
        mode = self._bridge.get_mode()
        if mode.get("mode") != "STAND_DEFAULT":
            if auto_stand:
                result = self._bridge.set_mode("STAND_DEFAULT")
                if not result["success"]:
                    self._publish_error(request_id, f"Auto-stand failed: {result['message']}")
                    return
                time.sleep(3)  # Wait for stabilization
            else:
                self._publish_error(request_id, f"Robot not standing (mode={mode.get('mode')}). Set auto_stand=true.")
                return

        # Register if needed
        if not motion["registered"]:
            reg = self._bridge.register_motion(motion["tag"], motion["motion_type"], motion["res_path"])
            if reg["success"]:
                self._catalog.mark_registered(motion_id)

        # Play
        result = self._bridge.play_motion(motion["tag"], motion["motion_type"], interrupt)
        if result["success"]:
            self._state = "dancing"
            self._current_motion = motion_id
        self._publish_status()

    def _handle_stop_motion(self, request_id: str):
        self._bridge.set_mode("STAND_DEFAULT")
        self._state = "idle"
        self._current_motion = None
        self._publish_status()

    def _handle_set_mode(self, request_id: str, payload: dict):
        mode = payload.get("mode", "")
        if mode not in VALID_MODES:
            self._publish_error(request_id, f"Invalid mode: {mode}")
            return
        result = self._bridge.set_mode(mode)
        if not result["success"]:
            self._publish_error(request_id, f"set_mode failed: {result['message']}")
            return
        self._publish_status()

    def _handle_play_preset(self, request_id: str, payload: dict):
        motion_id = payload.get("motion_id")
        area = payload.get("area", 2)
        interrupt = payload.get("interrupt", False)
        if motion_id is None:
            self._publish_error(request_id, "motion_id required for preset")
            return
        result = self._bridge.play_preset(int(motion_id), int(area), interrupt)
        self._publish_status()


def _build_lwt_message(robot_id: str) -> dict:
    """Build the Last Will and Testament payload."""
    return json.dumps({
        "robot_id": robot_id,
        "state": "offline",
        "current_motion": None,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    })


def main():
    robot_id = os.environ.get("X2_ROBOT_ID", MQTT_ROBOT_ID)
    endpoint = os.environ.get("X2_IOT_ENDPOINT", MQTT_IOT_ENDPOINT)
    cert_path = os.environ.get("X2_CERT_PATH", MQTT_CERT_PATH)

    if not endpoint:
        logger.error("X2_IOT_ENDPOINT is required. Run: aws iot describe-endpoint --endpoint-type iot:Data-ATS")
        sys.exit(1)

    cert_file = os.path.join(cert_path, "cert.pem")
    key_file = os.path.join(cert_path, "private.key")
    ca_file = os.path.join(cert_path, "AmazonRootCA1.pem")

    for f in [cert_file, key_file, ca_file]:
        if not os.path.exists(f):
            logger.error("Missing cert file: %s", f)
            sys.exit(1)

    # ── ROS2 + Catalog ───────────────────────────────────────
    bridge = ROS2Bridge()
    bridge.init()
    catalog = MotionCatalog(RESOURCE_CONFIG_PATH, RESOURCE_BASE_PATH)

    # Register all motions at startup
    for motion in catalog.list_all():
        result = bridge.register_motion(motion["tag"], motion["motion_type"], motion["res_path"])
        if result["success"]:
            catalog.mark_registered(motion["id"])
            logger.info("Registered: %s", motion["id"])

    # ── MQTT Connection ──────────────────────────────────────
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)

    lwt_topic = MQTT_STATUS_TOPIC.format(robot_id=robot_id)
    lwt_payload = _build_lwt_message(robot_id)

    mqtt_connection = mqtt_connection_builder.mtls_from_path(
        endpoint=endpoint,
        cert_filepath=cert_file,
        pri_key_filepath=key_file,
        ca_filepath=ca_file,
        client_bootstrap=client_bootstrap,
        client_id=robot_id,
        clean_session=False,
        keep_alive_secs=30,
        will=mqtt.Will(
            topic=lwt_topic,
            payload=lwt_payload.encode("utf-8"),
            qos=mqtt.QoS.AT_LEAST_ONCE,
        ),
    )

    logger.info("Connecting to %s as %s ...", endpoint, robot_id)
    connect_future = mqtt_connection.connect()
    connect_future.result()
    logger.info("Connected.")

    # ── Publish helper ───────────────────────────────────────
    def publish(topic: str, payload: str):
        mqtt_connection.publish(
            topic=topic,
            payload=payload.encode("utf-8"),
            qos=mqtt.QoS.AT_LEAST_ONCE,
        )
        logger.debug("Published to %s: %s", topic, payload[:200])

    # ── Handler ──────────────────────────────────────────────
    handler = MqttCommandHandler(bridge, catalog, publish, robot_id)

    # ── Subscribe to commands ────────────────────────────────
    command_topic = MQTT_COMMAND_TOPIC_PREFIX.format(robot_id=robot_id) + "/#"

    def on_message(topic, payload, **kwargs):
        try:
            cmd = json.loads(payload)
            logger.info("Received on %s: %s", topic, json.dumps(cmd)[:200])
            handler.handle_command(cmd)
        except json.JSONDecodeError:
            logger.error("Invalid JSON on %s: %s", topic, payload[:200])
        except Exception:
            logger.exception("Error handling command on %s", topic)

    subscribe_future, _ = mqtt_connection.subscribe(
        topic=command_topic,
        qos=mqtt.QoS.AT_LEAST_ONCE,
        callback=on_message,
    )
    subscribe_future.result()
    logger.info("Subscribed to %s", command_topic)

    # ── Publish initial status ───────────────────────────────
    handler._publish_status()
    logger.info("Published initial status (idle).")

    # ── Heartbeat loop ───────────────────────────────────────
    heartbeat_topic = MQTT_HEARTBEAT_TOPIC.format(robot_id=robot_id)

    def heartbeat_loop():
        while True:
            time.sleep(MQTT_HEARTBEAT_INTERVAL_SEC)
            msg = json.dumps({
                "robot_id": robot_id,
                "state": handler._state,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            })
            try:
                publish(heartbeat_topic, msg)
            except Exception:
                logger.exception("Heartbeat publish failed")

    heartbeat_thread = threading.Thread(target=heartbeat_loop, daemon=True)
    heartbeat_thread.start()

    # ── Run forever ──────────────────────────────────────────
    logger.info("MQTT client running. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Disconnecting...")
        mqtt_connection.disconnect().result()
        bridge.shutdown()
        logger.info("Done.")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the tests**

```bash
cd x2_api && python3 -m pytest tests/test_mqtt_client.py -v
```
Expected: All 9 tests PASS

- [ ] **Step 3: Write mqtt_run.sh**

Create `x2_api/mqtt_run.sh`:

```bash
#!/bin/bash
# x2_api/mqtt_run.sh — Launch the X2 MQTT client with correct environment
set -e

# Source ROS2 and AIMDK
source /opt/ros/humble/setup.bash
source /home/run/aimdk/install/setup.bash

# Add DRP package
export AMENT_PREFIX_PATH=/agibot/software/drp:$AMENT_PREFIX_PATH
export PYTHONPATH=/agibot/software/drp/local/lib/python3.10/dist-packages:$PYTHONPATH
export LD_LIBRARY_PATH=/agibot/software/drp/lib:$LD_LIBRARY_PATH

# MQTT config (override these per robot)
export X2_ROBOT_ID="${X2_ROBOT_ID:-x2-001}"
export X2_IOT_ENDPOINT="${X2_IOT_ENDPOINT:?Set X2_IOT_ENDPOINT to your AWS IoT endpoint}"
export X2_CERT_PATH="${X2_CERT_PATH:-/home/run/x2_api/certs}"

cd /home/run/x2_api
exec python3 mqtt_client.py "$@"
```

- [ ] **Step 4: Write x2-mqtt-client.service**

Create `x2_api/x2-mqtt-client.service`:

```ini
[Unit]
Description=X2 MQTT Client (AWS IoT Core)
After=agibot_software.service
Wants=agibot_software.service

[Service]
Type=simple
User=run
WorkingDirectory=/home/run/x2_api
ExecStart=/home/run/x2_api/mqtt_run.sh
Restart=on-failure
RestartSec=5
Environment=X2_ROBOT_ID=x2-001
Environment=X2_IOT_ENDPOINT=your-iot-endpoint.iot.us-east-1.amazonaws.com
Environment=X2_CERT_PATH=/home/run/x2_api/certs

[Install]
WantedBy=multi-user.target
```

- [ ] **Step 5: Make scripts executable**

```bash
chmod +x x2_api/mqtt_run.sh
```

- [ ] **Step 6: Commit**

```bash
git add x2_api/mqtt_client.py x2_api/mqtt_run.sh x2_api/x2-mqtt-client.service
git commit -m "feat: robot MQTT client for AWS IoT Core with command handler"
```

---

## Task 4: AWS SAM Template — Infrastructure

**Files:**
- Create: `cloud/infra/template.yaml`

This SAM template defines all AWS resources: API Gateway, 3 Lambdas, 2 DynamoDB tables, IoT Core rule, IAM roles, S3 bucket, and CloudFront distribution.

- [ ] **Step 1: Create cloud directory structure**

```bash
mkdir -p cloud/lambdas cloud/web cloud/infra cloud/scripts
```

- [ ] **Step 2: Write template.yaml**

Create `cloud/infra/template.yaml`:

```yaml
AWSTemplateFormatVersion: '2010-09-09'
Transform: AWS::Serverless-2016-10-31
Description: X2 Dance Kiosk — serverless cloud infrastructure

Parameters:
  StripeSecretKey:
    Type: String
    NoEcho: true
    Description: Stripe secret API key
  StripeWebhookSecret:
    Type: String
    NoEcho: true
    Description: Stripe webhook signing secret
  StripePriceCents:
    Type: Number
    Default: 200
    Description: Fixed price per dance in cents (200 = $2.00)
  DomainName:
    Type: String
    Description: Custom domain (e.g. dance.example.com)
  IoTEndpoint:
    Type: String
    Description: "AWS IoT Core endpoint (run: aws iot describe-endpoint --endpoint-type iot:Data-ATS)"

Globals:
  Function:
    Runtime: python3.10
    Timeout: 10
    MemorySize: 128
    Environment:
      Variables:
        ROBOT_STATE_TABLE: !Ref RobotStateTable
        TRANSACTIONS_TABLE: !Ref TransactionsTable
        IOT_ENDPOINT: !Ref IoTEndpoint

Resources:

  # ── DynamoDB Tables ──────────────────────────────────────

  RobotStateTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: X2DanceKiosk-RobotState
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: robot_id
          AttributeType: S
      KeySchema:
        - AttributeName: robot_id
          KeyType: HASH

  TransactionsTable:
    Type: AWS::DynamoDB::Table
    Properties:
      TableName: X2DanceKiosk-Transactions
      BillingMode: PAY_PER_REQUEST
      AttributeDefinitions:
        - AttributeName: transaction_id
          AttributeType: S
        - AttributeName: robot_id
          AttributeType: S
      KeySchema:
        - AttributeName: transaction_id
          KeyType: HASH
      GlobalSecondaryIndexes:
        - IndexName: robot_id-index
          KeySchema:
            - AttributeName: robot_id
              KeyType: HASH
          Projection:
            ProjectionType: ALL

  # ── Lambda Functions ─────────────────────────────────────

  CreateCheckoutFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: X2DanceKiosk-CreateCheckout
      Handler: create_checkout.lambda_handler
      CodeUri: ../lambdas/
      Environment:
        Variables:
          STRIPE_SECRET_KEY: !Ref StripeSecretKey
          STRIPE_PRICE_CENTS: !Ref StripePriceCents
          DOMAIN_NAME: !Ref DomainName
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref RobotStateTable
      Events:
        Api:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /api/checkout
            Method: POST

  HandleWebhookFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: X2DanceKiosk-HandleWebhook
      Handler: handle_webhook.lambda_handler
      CodeUri: ../lambdas/
      Environment:
        Variables:
          STRIPE_SECRET_KEY: !Ref StripeSecretKey
          STRIPE_WEBHOOK_SECRET: !Ref StripeWebhookSecret
      Policies:
        - DynamoDBCrudPolicy:
            TableName: !Ref RobotStateTable
        - DynamoDBCrudPolicy:
            TableName: !Ref TransactionsTable
        - Statement:
            - Effect: Allow
              Action: iot:Publish
              Resource: !Sub "arn:aws:iot:${AWS::Region}:${AWS::AccountId}:topic/x2/*/command/*"
      Events:
        Api:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /api/webhook/stripe
            Method: POST

  GetStatusFunction:
    Type: AWS::Serverless::Function
    Properties:
      FunctionName: X2DanceKiosk-GetStatus
      Handler: get_status.lambda_handler
      CodeUri: ../lambdas/
      Policies:
        - DynamoDBReadPolicy:
            TableName: !Ref RobotStateTable
      Events:
        Api:
          Type: HttpApi
          Properties:
            ApiId: !Ref HttpApi
            Path: /api/status/{robot_id}
            Method: GET

  # ── API Gateway ──────────────────────────────────────────

  HttpApi:
    Type: AWS::Serverless::HttpApi
    Properties:
      StageName: prod
      CorsConfiguration:
        AllowOrigins:
          - "*"
        AllowMethods:
          - GET
          - POST
          - OPTIONS
        AllowHeaders:
          - Content-Type

  # ── IoT Rule: Status → DynamoDB ──────────────────────────

  IoTStatusRule:
    Type: AWS::IoT::TopicRule
    Properties:
      RuleName: X2DanceKioskStatusToDynamo
      TopicRulePayload:
        Sql: "SELECT * FROM 'x2/+/status'"
        Actions:
          - DynamoDBv2:
              PutItem:
                TableName: !Ref RobotStateTable
              RoleArn: !GetAtt IoTRuleRole.Arn
        RuleDisabled: false

  IoTRuleRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Effect: Allow
            Principal:
              Service: iot.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: IoTDynamoDBWrite
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - dynamodb:PutItem
                  - dynamodb:UpdateItem
                Resource: !GetAtt RobotStateTable.Arn

  # ── S3 Bucket for Web SPA ───────────────────────────────

  WebBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub "x2-dance-kiosk-web-${AWS::AccountId}"
      WebsiteConfiguration:
        IndexDocument: index.html

  WebBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref WebBucket
      PolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: cloudfront.amazonaws.com
            Action: s3:GetObject
            Resource: !Sub "${WebBucket.Arn}/*"
            Condition:
              StringEquals:
                AWS:SourceArn: !Sub "arn:aws:cloudfront::${AWS::AccountId}:distribution/${CloudFrontDistribution}"

  # ── CloudFront ───────────────────────────────────────────

  CloudFrontDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Enabled: true
        DefaultRootObject: index.html
        Origins:
          - Id: S3Origin
            DomainName: !GetAtt WebBucket.RegionalDomainName
            OriginAccessControlId: !Ref CloudFrontOAC
            S3OriginConfig:
              OriginAccessIdentity: ""
        DefaultCacheBehavior:
          TargetOriginId: S3Origin
          ViewerProtocolPolicy: redirect-to-https
          CachePolicyId: 658327ea-f89d-4fab-a63d-7e88639e58f6  # CachingOptimized
          AllowedMethods: [GET, HEAD]
          CachedMethods: [GET, HEAD]

  CloudFrontOAC:
    Type: AWS::CloudFront::OriginAccessControl
    Properties:
      OriginAccessControlConfig:
        Name: X2DanceKioskOAC
        OriginAccessControlOriginType: s3
        SigningBehavior: always
        SigningProtocol: sigv4

Outputs:
  ApiUrl:
    Description: API Gateway endpoint URL
    Value: !Sub "https://${HttpApi}.execute-api.${AWS::Region}.amazonaws.com/prod"
  WebBucketName:
    Description: S3 bucket for web assets
    Value: !Ref WebBucket
  CloudFrontDomain:
    Description: CloudFront distribution domain
    Value: !GetAtt CloudFrontDistribution.DomainName
  RobotStateTableName:
    Description: DynamoDB table for robot state
    Value: !Ref RobotStateTable
  TransactionsTableName:
    Description: DynamoDB table for transactions
    Value: !Ref TransactionsTable
```

- [ ] **Step 3: Commit**

```bash
git add cloud/infra/template.yaml
git commit -m "feat: SAM template with API Gateway, Lambda, DynamoDB, IoT Rule, S3, CloudFront"
```

---

## Task 5: Lambda — create_checkout

**Files:**
- Create: `cloud/lambdas/create_checkout.py`
- Create: `cloud/lambdas/requirements.txt`

- [ ] **Step 1: Write requirements.txt**

Create `cloud/lambdas/requirements.txt`:

```
stripe==8.12.0
boto3==1.35.0
```

- [ ] **Step 2: Write create_checkout.py**

Create `cloud/lambdas/create_checkout.py`:

```python
# cloud/lambdas/create_checkout.py
"""Lambda: Create a Stripe Checkout session for a dance payment."""
import json
import os
import stripe
import boto3

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
PRICE_CENTS = int(os.environ.get("STRIPE_PRICE_CENTS", "200"))
DOMAIN = os.environ.get("DOMAIN_NAME", "localhost")
TABLE = os.environ["ROBOT_STATE_TABLE"]

dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE)


def lambda_handler(event, context):
    try:
        body = json.loads(event.get("body", "{}"))
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON"})

    robot_id = body.get("robot_id", "")
    motion_id = body.get("motion_id", "")

    if not robot_id or not motion_id:
        return _response(400, {"error": "robot_id and motion_id required"})

    # Check robot state
    result = table.get_item(Key={"robot_id": robot_id})
    item = result.get("Item")
    if item:
        state = item.get("state", "offline")
        if state == "dancing":
            return _response(409, {"error": "Robot is busy dancing", "state": state})
        if state == "offline":
            return _response(409, {"error": "Robot is offline", "state": state})

    # Create Stripe Checkout session
    session = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "usd",
                "product_data": {"name": f"Robot Dance: {motion_id}"},
                "unit_amount": PRICE_CENTS,
            },
            "quantity": 1,
        }],
        mode="payment",
        metadata={"robot_id": robot_id, "motion_id": motion_id},
        success_url=f"https://{DOMAIN}/{robot_id}?success=true",
        cancel_url=f"https://{DOMAIN}/{robot_id}?cancelled=true",
    )

    return _response(200, {"checkout_url": session.url})


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
```

- [ ] **Step 3: Commit**

```bash
git add cloud/lambdas/create_checkout.py cloud/lambdas/requirements.txt
git commit -m "feat: create-checkout Lambda with Stripe session and robot state check"
```

---

## Task 6: Lambda — handle_webhook

**Files:**
- Create: `cloud/lambdas/handle_webhook.py`

- [ ] **Step 1: Write handle_webhook.py**

Create `cloud/lambdas/handle_webhook.py`:

```python
# cloud/lambdas/handle_webhook.py
"""Lambda: Handle Stripe webhook → verify payment → send MQTT command to robot."""
import json
import os
from datetime import datetime, timezone

import stripe
import boto3

stripe.api_key = os.environ["STRIPE_SECRET_KEY"]
WEBHOOK_SECRET = os.environ["STRIPE_WEBHOOK_SECRET"]
IOT_ENDPOINT = os.environ["IOT_ENDPOINT"]
STATE_TABLE = os.environ["ROBOT_STATE_TABLE"]
TX_TABLE = os.environ["TRANSACTIONS_TABLE"]

dynamodb = boto3.resource("dynamodb")
state_table = dynamodb.Table(STATE_TABLE)
tx_table = dynamodb.Table(TX_TABLE)
iot_client = boto3.client("iot-data", endpoint_url=f"https://{IOT_ENDPOINT}")


def lambda_handler(event, context):
    body = event.get("body", "")
    sig_header = event.get("headers", {}).get("stripe-signature", "")

    # Verify webhook signature
    try:
        evt = stripe.Webhook.construct_event(body, sig_header, WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError:
        return _response(400, {"error": "Invalid signature"})
    except Exception as e:
        return _response(400, {"error": str(e)})

    if evt["type"] != "checkout.session.completed":
        return _response(200, {"status": "ignored", "type": evt["type"]})

    session = evt["data"]["object"]
    metadata = session.get("metadata", {})
    robot_id = metadata.get("robot_id", "")
    motion_id = metadata.get("motion_id", "")
    amount = session.get("amount_total", 0)
    session_id = session["id"]

    if not robot_id or not motion_id:
        return _response(400, {"error": "Missing metadata"})

    # Check robot state — refund if busy
    result = state_table.get_item(Key={"robot_id": robot_id})
    item = result.get("Item", {})
    state = item.get("state", "unknown")

    if state == "dancing":
        # Refund
        stripe.Refund.create(payment_intent=session["payment_intent"])
        _log_transaction(session_id, robot_id, motion_id, amount, "refunded")
        return _response(200, {"status": "refunded", "reason": "robot_busy"})

    # Update robot state to dancing
    now = datetime.now(timezone.utc).isoformat()
    state_table.put_item(Item={
        "robot_id": robot_id,
        "state": "dancing",
        "current_motion": motion_id,
        "last_updated": now,
    })

    # Publish MQTT command
    command = {
        "request_id": session_id,
        "action": "play_motion",
        "payload": {
            "motion_id": motion_id,
            "interrupt": False,
            "auto_stand": True,
        },
        "timestamp": now,
    }

    topic = f"x2/{robot_id}/command/motion/play"
    iot_client.publish(
        topic=topic,
        qos=1,
        payload=json.dumps(command).encode("utf-8"),
    )

    # Log transaction
    _log_transaction(session_id, robot_id, motion_id, amount, "completed")

    return _response(200, {"status": "command_sent", "robot_id": robot_id, "motion_id": motion_id})


def _log_transaction(session_id, robot_id, motion_id, amount, status):
    tx_table.put_item(Item={
        "transaction_id": session_id,
        "robot_id": robot_id,
        "motion_id": motion_id,
        "amount_cents": amount,
        "status": status,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
```

- [ ] **Step 2: Commit**

```bash
git add cloud/lambdas/handle_webhook.py
git commit -m "feat: handle-webhook Lambda — Stripe verification, refund, MQTT publish"
```

---

## Task 7: Lambda — get_status

**Files:**
- Create: `cloud/lambdas/get_status.py`

- [ ] **Step 1: Write get_status.py**

Create `cloud/lambdas/get_status.py`:

```python
# cloud/lambdas/get_status.py
"""Lambda: Return current robot state from DynamoDB."""
import json
import os
import boto3

TABLE = os.environ["ROBOT_STATE_TABLE"]
dynamodb = boto3.resource("dynamodb")
table = dynamodb.Table(TABLE)


def lambda_handler(event, context):
    robot_id = event.get("pathParameters", {}).get("robot_id", "")

    if not robot_id:
        return _response(400, {"error": "robot_id required"})

    result = table.get_item(Key={"robot_id": robot_id})
    item = result.get("Item")

    if not item:
        return _response(200, {
            "robot_id": robot_id,
            "state": "unknown",
            "current_motion": None,
            "last_updated": None,
        })

    return _response(200, {
        "robot_id": item.get("robot_id"),
        "state": item.get("state", "unknown"),
        "current_motion": item.get("current_motion"),
        "last_updated": item.get("last_updated"),
    })


def _response(status_code: int, body: dict) -> dict:
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
        },
        "body": json.dumps(body),
    }
```

- [ ] **Step 2: Commit**

```bash
git add cloud/lambdas/get_status.py
git commit -m "feat: get-status Lambda — read robot state from DynamoDB"
```

---

## Task 8: IoT Provisioning Script

**Files:**
- Create: `cloud/scripts/provision_robot.py`

- [ ] **Step 1: Write provision_robot.py**

Create `cloud/scripts/provision_robot.py`:

```python
#!/usr/bin/env python3
# cloud/scripts/provision_robot.py
"""Provision an X2 robot as an AWS IoT Thing with certs and policy.

Usage:
    python provision_robot.py <robot_id> [--scp]

Example:
    python provision_robot.py x2-001 --scp
"""
import argparse
import json
import os
import subprocess
import sys

import boto3

iot = boto3.client("iot")


def get_account_and_region():
    sts = boto3.client("sts")
    account = sts.get_caller_identity()["Account"]
    region = boto3.session.Session().region_name
    return account, region


def create_policy(robot_id: str, account: str, region: str) -> str:
    policy_name = f"X2DanceKiosk-{robot_id}"
    policy_doc = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Action": "iot:Connect",
                "Resource": f"arn:aws:iot:{region}:{account}:client/{robot_id}",
            },
            {
                "Effect": "Allow",
                "Action": "iot:Subscribe",
                "Resource": f"arn:aws:iot:{region}:{account}:topicfilter/x2/{robot_id}/command/*",
            },
            {
                "Effect": "Allow",
                "Action": "iot:Receive",
                "Resource": f"arn:aws:iot:{region}:{account}:topic/x2/{robot_id}/command/*",
            },
            {
                "Effect": "Allow",
                "Action": "iot:Publish",
                "Resource": f"arn:aws:iot:{region}:{account}:topic/x2/{robot_id}/status/*",
            },
        ],
    }

    try:
        iot.create_policy(
            policyName=policy_name,
            policyDocument=json.dumps(policy_doc),
        )
        print(f"Created IoT policy: {policy_name}")
    except iot.exceptions.ResourceAlreadyExistsException:
        print(f"IoT policy already exists: {policy_name}")

    return policy_name


def provision(robot_id: str, scp: bool):
    account, region = get_account_and_region()
    print(f"Account: {account}, Region: {region}")

    # Create Thing
    try:
        iot.create_thing(thingName=robot_id)
        print(f"Created IoT Thing: {robot_id}")
    except iot.exceptions.ResourceAlreadyExistsException:
        print(f"IoT Thing already exists: {robot_id}")

    # Create certificate
    cert_response = iot.create_keys_and_certificate(setAsActive=True)
    cert_arn = cert_response["certificateArn"]
    cert_id = cert_response["certificateId"]
    cert_pem = cert_response["certificatePem"]
    private_key = cert_response["keyPair"]["PrivateKey"]
    print(f"Created certificate: {cert_id[:12]}...")

    # Attach cert to Thing
    iot.attach_thing_principal(thingName=robot_id, principal=cert_arn)
    print(f"Attached certificate to Thing: {robot_id}")

    # Create and attach policy
    policy_name = create_policy(robot_id, account, region)
    iot.attach_policy(policyName=policy_name, target=cert_arn)
    print(f"Attached policy: {policy_name}")

    # Save cert files locally
    out_dir = os.path.join("certs", robot_id)
    os.makedirs(out_dir, exist_ok=True)

    cert_file = os.path.join(out_dir, "cert.pem")
    key_file = os.path.join(out_dir, "private.key")
    ca_file = os.path.join(out_dir, "AmazonRootCA1.pem")

    with open(cert_file, "w") as f:
        f.write(cert_pem)
    with open(key_file, "w") as f:
        f.write(private_key)

    # Download Amazon Root CA
    import urllib.request
    urllib.request.urlretrieve(
        "https://www.amazontrust.com/repository/AmazonRootCA1.pem",
        ca_file,
    )

    print(f"\nCert bundle saved to {out_dir}/")
    print(f"  {cert_file}")
    print(f"  {key_file}")
    print(f"  {ca_file}")

    # Get IoT endpoint
    endpoint = iot.describe_endpoint(endpointType="iot:Data-ATS")["endpointAddress"]
    print(f"\nIoT Endpoint: {endpoint}")
    print(f"Set on robot: export X2_IOT_ENDPOINT={endpoint}")

    # SCP to robot
    if scp:
        print(f"\nSCPing certs to X2:/home/run/x2_api/certs/ ...")
        subprocess.run(["ssh", "X2", "mkdir -p /home/run/x2_api/certs"], check=True)
        for fname in ["cert.pem", "private.key", "AmazonRootCA1.pem"]:
            src = os.path.join(out_dir, fname)
            subprocess.run(["scp", src, f"X2:/home/run/x2_api/certs/{fname}"], check=True)
        print("Done. Certs deployed to robot.")


def main():
    parser = argparse.ArgumentParser(description="Provision X2 robot as AWS IoT Thing")
    parser.add_argument("robot_id", help="Robot ID (e.g. x2-001)")
    parser.add_argument("--scp", action="store_true", help="SCP certs to robot via SSH alias X2")
    args = parser.parse_args()
    provision(args.robot_id, args.scp)


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Make executable**

```bash
chmod +x cloud/scripts/provision_robot.py
```

- [ ] **Step 3: Commit**

```bash
git add cloud/scripts/provision_robot.py
git commit -m "feat: IoT provisioning script — create Thing, certs, policy, optional SCP"
```

---

## Task 9: Mobile Web Page

**Files:**
- Create: `cloud/web/index.html`
- Create: `cloud/web/style.css`
- Create: `cloud/web/app.js`

- [ ] **Step 1: Write index.html**

Create `cloud/web/index.html`:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X2 Dance Kiosk</title>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div id="app">
        <header>
            <h1>X2 Dance Kiosk</h1>
            <div id="status-badge" class="badge offline">Loading...</div>
        </header>

        <main>
            <!-- Idle: show dance menu -->
            <section id="dance-menu" class="hidden">
                <p class="subtitle">Pick a dance and watch the robot perform!</p>
                <div id="dance-list" class="dance-grid"></div>
            </section>

            <!-- Dancing: show feedback -->
            <section id="dancing-view" class="hidden">
                <div class="dancing-animation">🤖💃</div>
                <h2>Robot is dancing!</h2>
                <p id="dancing-motion-name"></p>
                <p class="subtle">Check back in a moment for another dance.</p>
            </section>

            <!-- Offline -->
            <section id="offline-view" class="hidden">
                <div class="offline-icon">📡</div>
                <h2>Robot is offline</h2>
                <p>Please try again later.</p>
            </section>

            <!-- Payment success -->
            <section id="success-view" class="hidden">
                <div class="success-icon">🎉</div>
                <h2>Payment received!</h2>
                <p>The robot is about to dance...</p>
            </section>

            <!-- Payment cancelled -->
            <section id="cancelled-view" class="hidden">
                <h2>Payment cancelled</h2>
                <p>No charge was made. <a href="#" id="back-to-menu">Back to dances</a></p>
            </section>

            <!-- Error -->
            <section id="error-view" class="hidden">
                <h2>Something went wrong</h2>
                <p id="error-message"></p>
                <button id="retry-btn" class="btn">Try Again</button>
            </section>
        </main>

        <footer>
            <p>Powered by AgiBot X2</p>
        </footer>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

- [ ] **Step 2: Write style.css**

Create `cloud/web/style.css`:

```css
/* cloud/web/style.css — Mobile-first dance kiosk */
* { margin: 0; padding: 0; box-sizing: border-box; }

:root {
    --bg: #0a0a0f;
    --surface: #16161d;
    --border: #2a2a35;
    --text: #e8e8ed;
    --text-subtle: #8888aa;
    --accent: #6c5ce7;
    --accent-light: #a29bfe;
    --success: #00b894;
    --danger: #e17055;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    justify-content: center;
}

#app {
    width: 100%;
    max-width: 480px;
    padding: 24px 16px;
}

header {
    text-align: center;
    margin-bottom: 32px;
}

header h1 {
    font-size: 1.5rem;
    font-weight: 700;
    margin-bottom: 12px;
}

.badge {
    display: inline-block;
    padding: 4px 12px;
    border-radius: 20px;
    font-size: 0.8rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.05em;
}
.badge.idle { background: var(--success); color: #000; }
.badge.dancing { background: var(--accent); color: #fff; }
.badge.offline { background: var(--danger); color: #fff; }

.subtitle {
    color: var(--text-subtle);
    margin-bottom: 24px;
    text-align: center;
}

.dance-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 12px;
}

.dance-card {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 20px 12px;
    text-align: center;
    cursor: pointer;
    transition: transform 0.15s, border-color 0.15s;
}
.dance-card:active {
    transform: scale(0.97);
    border-color: var(--accent);
}

.dance-card .emoji {
    font-size: 2rem;
    margin-bottom: 8px;
}

.dance-card .name {
    font-size: 0.95rem;
    font-weight: 600;
    margin-bottom: 4px;
}

.dance-card .price {
    font-size: 0.85rem;
    color: var(--accent-light);
    font-weight: 600;
}

.dancing-animation {
    font-size: 4rem;
    text-align: center;
    margin: 40px 0 20px;
    animation: bounce 1s ease infinite;
}

@keyframes bounce {
    0%, 100% { transform: translateY(0); }
    50% { transform: translateY(-12px); }
}

.offline-icon, .success-icon {
    font-size: 3rem;
    text-align: center;
    margin: 40px 0 20px;
}

main section {
    text-align: center;
}

main h2 {
    font-size: 1.3rem;
    margin-bottom: 8px;
}

.subtle {
    color: var(--text-subtle);
    font-size: 0.9rem;
    margin-top: 12px;
}

.btn {
    display: inline-block;
    padding: 12px 32px;
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    font-weight: 600;
    cursor: pointer;
    margin-top: 16px;
}

footer {
    text-align: center;
    color: var(--text-subtle);
    font-size: 0.75rem;
    margin-top: 48px;
}

.hidden { display: none !important; }

a { color: var(--accent-light); }
```

- [ ] **Step 3: Write app.js**

Create `cloud/web/app.js`:

```javascript
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
            // Redirect to Stripe Checkout
            window.location.href = data.checkout_url;
        } catch (e) {
            if (e.status === 409) {
                // Robot busy or offline — refresh state
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
        // Extract robot_id from URL path: /x2-001
        const path = window.location.pathname.replace(/^\//, "").replace(/\/$/, "");
        robotId = path || "x2-001";

        // Check for Stripe redirect params
        const params = new URLSearchParams(window.location.search);

        if (params.get("success") === "true") {
            setBadge("dancing");
            show($success);
            // Start polling — will switch to dancing view when status updates
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
```

- [ ] **Step 4: Commit**

```bash
git add cloud/web/index.html cloud/web/style.css cloud/web/app.js
git commit -m "feat: mobile web SPA — dance menu, Stripe checkout, status polling"
```

---

## Task 10: AWS CLI Setup and Deploy

**Files:** None (operational steps)

This task walks through the one-time AWS setup, SAM deployment, and Stripe configuration.

- [ ] **Step 1: Install AWS CLI**

```bash
# macOS
brew install awscli
```

- [ ] **Step 2: Configure AWS CLI**

```bash
aws configure
# Enter: AWS Access Key ID, Secret Key, Region (e.g. us-east-1), output format (json)
```

- [ ] **Step 3: Install AWS SAM CLI**

```bash
brew install aws-sam-cli
```

- [ ] **Step 4: Verify tools**

```bash
aws sts get-caller-identity
sam --version
```
Expected: Account ID and SAM version printed.

- [ ] **Step 5: Create a Stripe account and get keys**

Go to https://dashboard.stripe.com/test/apikeys and note:
- `STRIPE_SECRET_KEY` (starts with `sk_test_`)
- Create a webhook endpoint pointing to `{API_URL}/api/webhook/stripe` for `checkout.session.completed` events
- Note the `STRIPE_WEBHOOK_SECRET` (starts with `whsec_`)

(The webhook URL won't exist yet — create a placeholder, update after deploy.)

- [ ] **Step 6: Get IoT endpoint**

```bash
aws iot describe-endpoint --endpoint-type iot:Data-ATS --query 'endpointAddress' --output text
```

- [ ] **Step 7: Build and deploy SAM stack**

```bash
cd cloud/infra
sam build
sam deploy --guided \
  --stack-name X2DanceKiosk \
  --capabilities CAPABILITY_IAM \
  --parameter-overrides \
    StripeSecretKey=sk_test_YOUR_KEY \
    StripeWebhookSecret=whsec_YOUR_SECRET \
    StripePriceCents=200 \
    DomainName=dance.yourdomain.com \
    IoTEndpoint=YOUR_IOT_ENDPOINT
```

Note the outputs: `ApiUrl`, `WebBucketName`, `CloudFrontDomain`.

- [ ] **Step 8: Upload web assets to S3**

```bash
aws s3 sync ../web/ s3://BUCKET_NAME_FROM_OUTPUT/ --delete
```

- [ ] **Step 9: Update Stripe webhook URL**

Go to Stripe Dashboard → Webhooks → update the endpoint URL to:
`{ApiUrl}/api/webhook/stripe`

- [ ] **Step 10: Provision robot**

```bash
cd ../../cloud/scripts
pip install boto3
python provision_robot.py x2-001 --scp
```

- [ ] **Step 11: Start MQTT client on robot**

```bash
ssh X2 "export X2_IOT_ENDPOINT=YOUR_ENDPOINT && \
  export X2_ROBOT_ID=x2-001 && \
  cd /home/run/x2_api && bash mqtt_run.sh"
```

- [ ] **Step 12: End-to-end smoke test**

```bash
# Check robot status via cloud API
curl https://API_URL/prod/api/status/x2-001

# Open web page in mobile browser
# Visit: https://CLOUDFRONT_DOMAIN/x2-001
# Should see dance menu with robot status "idle"
```

- [ ] **Step 13: Commit any config updates**

```bash
git add -A
git commit -m "chore: deployment notes and config"
```

---

## Summary

| Task | What it builds | Key files |
|------|---------------|-----------|
| 1 | MQTT config + gitignore | `config.py`, `.gitignore` |
| 2 | MQTT client tests (TDD red) | `tests/test_mqtt_client.py` |
| 3 | MQTT client implementation | `mqtt_client.py`, `mqtt_run.sh`, systemd unit |
| 4 | SAM/CloudFormation infra | `template.yaml` |
| 5 | create-checkout Lambda | `create_checkout.py` |
| 6 | handle-webhook Lambda | `handle_webhook.py` |
| 7 | get-status Lambda | `get_status.py` |
| 8 | IoT provisioning script | `provision_robot.py` |
| 9 | Mobile web SPA | `index.html`, `style.css`, `app.js` |
| 10 | AWS CLI setup + deploy | Operational steps |
