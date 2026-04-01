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
from typing import Optional

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

    def _publish_status(self, extra: Optional[dict] = None):
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
        self._bridge.play_preset(int(motion_id), int(area), interrupt)
        self._publish_status()


def _build_lwt_message(robot_id: str) -> str:
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
        clean_session=True,
        keep_alive_secs=30,
        will=mqtt.Will(
            lwt_topic,
            mqtt.QoS.AT_LEAST_ONCE,
            lwt_payload.encode("utf-8"),
            False,
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
