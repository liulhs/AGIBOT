# x2_api/tests/test_mqtt_client.py
"""Tests for MQTT client message handling logic."""
import json
import pytest
from unittest.mock import MagicMock, patch


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

import sys
import os
import types

# Stub out native/ROS2/AWS modules not available on dev machine
def _stub_native_modules():
    for name in [
        "awscrt", "awscrt.io", "awscrt.mqtt",
        "awsiot", "awsiot.mqtt_connection_builder",
        "rclpy", "rclpy.node",
        "aimdk_msgs", "aimdk_msgs.srv", "aimdk_msgs.msg",
    ]:
        if name not in sys.modules:
            sys.modules[name] = MagicMock()

_stub_native_modules()
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from mqtt_client import MqttCommandHandler  # noqa: E402


@pytest.fixture
def mqtt_handler():
    """Create MqttCommandHandler with mocked bridge, catalog, and publish."""
    mock_bridge = MagicMock()
    mock_catalog = MagicMock()
    mock_publish = MagicMock()

    mock_catalog.get_by_id.return_value = {
        "id": "golf_swing_pro",
        "name": "Golf Swing",
        "tag": "linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6_0.0.1",
        "motion_type": 2,
        "res_path": "/fake/path/policy.onnx",
        "registered": True,
    }
    mock_catalog.list_all.return_value = [mock_catalog.get_by_id.return_value]
    mock_bridge.get_mode.return_value = {"mode": "STAND_DEFAULT", "status": "RUNNING", "status_code": 100}

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
