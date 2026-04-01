# x2_api/mqtt_client.py
"""MQTT client for AWS IoT Core — receives dance commands, controls robot.

Runs as a standalone process alongside the Flask REST API.
Delegates all robot control to the REST API on localhost:8080 to avoid
ROS2 threading issues with rclpy.spin_until_future_complete.
"""
import os
import sys
import json
import time
import logging
import threading
import queue
from datetime import datetime, timezone
from typing import Optional

import requests
from awscrt import io, mqtt
from awsiot import mqtt_connection_builder

from config import (
    MQTT_ROBOT_ID,
    MQTT_IOT_ENDPOINT,
    MQTT_CERT_PATH,
    MQTT_COMMAND_TOPIC_PREFIX,
    MQTT_STATUS_TOPIC,
    MQTT_HEARTBEAT_TOPIC,
    VALID_MODES,
    API_KEY,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("x2_mqtt")

REST_BASE = "http://127.0.0.1:8080/api/v1"
REST_HEADERS = {"X-API-Key": API_KEY, "Content-Type": "application/json"}
REST_TIMEOUT = 15


class MqttCommandHandler:
    """Handles incoming MQTT commands by calling the local REST API."""

    VALID_ACTIONS = {"play_motion", "stop_motion", "set_mode", "play_preset"}

    def __init__(self, publish_fn, robot_id: str):
        self._publish = publish_fn
        self._robot_id = robot_id
        self._state = "idle"
        self._current_motion = None

    @staticmethod
    def _now():
        return datetime.now(timezone.utc).isoformat()

    def _rest(self, method: str, path: str, body: Optional[dict] = None) -> dict:
        """Call the local REST API."""
        url = REST_BASE + path
        resp = requests.request(method, url, headers=REST_HEADERS,
                                json=body, timeout=REST_TIMEOUT)
        return resp.json()

    def _get_mode(self) -> str:
        try:
            data = self._rest("GET", "/robot/state")
            return data.get("mode", "UNKNOWN")
        except Exception:
            return "UNKNOWN"

    def _publish_status(self, extra: Optional[dict] = None):
        """Publish current state to the status topic."""
        topic = MQTT_STATUS_TOPIC.format(robot_id=self._robot_id)
        msg = {
            "robot_id": self._robot_id,
            "state": self._state,
            "current_motion": self._current_motion,
            "mode": self._get_mode(),
            "timestamp": self._now(),
        }
        if extra:
            msg.update(extra)
        self._publish(topic, json.dumps(msg))

    def _publish_error(self, request_id: str, error: str):
        """Publish an error response to the status topic."""
        logger.error("Command error [%s]: %s", request_id, error)
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

        try:
            if action == "play_motion":
                self._handle_play_motion(request_id, payload)
            elif action == "stop_motion":
                self._handle_stop_motion(request_id)
            elif action == "set_mode":
                self._handle_set_mode(request_id, payload)
            elif action == "play_preset":
                self._handle_play_preset(request_id, payload)
        except Exception:
            logger.exception("Error handling %s", action)
            self._publish_error(request_id, f"Internal error handling {action}")

    def _handle_play_motion(self, request_id: str, payload: dict):
        motion_id = payload.get("motion_id", "")
        auto_stand = payload.get("auto_stand", False)

        if self._state == "dancing":
            self._publish_status()
            return

        # Auto-stand if needed
        mode = self._get_mode()
        if mode != "STAND_DEFAULT":
            if auto_stand:
                logger.info("Auto-standing robot (current mode: %s)", mode)
                self._rest("POST", "/robot/mode", {"mode": "STAND_DEFAULT"})
                time.sleep(3)
            else:
                self._publish_error(request_id,
                                    f"Robot not standing (mode={mode}). Set auto_stand=true.")
                return

        # Play motion via REST API
        logger.info("Playing motion: %s", motion_id)
        result = self._rest("POST", "/motions/play", {
            "motion_id": motion_id,
            "auto_stand": False,
        })
        logger.info("Play result: %s", result)

        if "error" not in result:
            self._state = "dancing"
            self._current_motion = motion_id
        else:
            self._publish_error(request_id, result.get("error", "play failed"))
            return
        self._publish_status()

    def _handle_stop_motion(self, request_id: str):
        self._rest("POST", "/motions/stop", {})
        self._state = "idle"
        self._current_motion = None
        self._publish_status()

    def _handle_set_mode(self, request_id: str, payload: dict):
        mode = payload.get("mode", "")
        if mode not in VALID_MODES:
            self._publish_error(request_id, f"Invalid mode: {mode}")
            return
        self._rest("POST", "/robot/mode", {"mode": mode})
        self._publish_status()

    def _handle_play_preset(self, request_id: str, payload: dict):
        motion_id = payload.get("motion_id")
        area = payload.get("area", 11)
        if not motion_id:
            self._publish_error(request_id, "Missing 'motion_id' for preset")
            return
        self._rest("POST", "/presets/play", {"motion_id": motion_id, "area": area})
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
        logger.error("X2_IOT_ENDPOINT is required.")
        sys.exit(1)

    cert_file = os.path.join(cert_path, "cert.pem")
    key_file = os.path.join(cert_path, "private.key")
    ca_file = os.path.join(cert_path, "AmazonRootCA1.pem")

    for f in [cert_file, key_file, ca_file]:
        if not os.path.exists(f):
            logger.error("Missing cert file: %s", f)
            sys.exit(1)

    # ── Wait for REST API to be available ───────────────────
    logger.info("Waiting for REST API at %s ...", REST_BASE)
    for i in range(30):
        try:
            requests.get(REST_BASE + "/health", timeout=2)
            logger.info("REST API is up.")
            break
        except Exception:
            time.sleep(1)
    else:
        logger.error("REST API not available after 30s — continuing anyway")

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
        logger.debug("Published to %s", topic)

    # ── Handler ──────────────────────────────────────────────
    handler = MqttCommandHandler(publish, robot_id)

    # ── Command queue — single worker thread for all ROS2/REST calls ──
    cmd_queue = queue.Queue()

    def worker_loop():
        """Process commands, heartbeats, and motion-complete detection."""
        status_topic = MQTT_STATUS_TOPIC.format(robot_id=robot_id)
        last_heartbeat = 0.0
        last_poll = 0.0
        while True:
            try:
                cmd = cmd_queue.get(timeout=1.0)
                if cmd is None:
                    break
                if cmd.get("_type") == "heartbeat":
                    try:
                        # Detect motion completion: if we think we're dancing
                        # but the robot is back to STAND_DEFAULT, motion finished.
                        if handler._state == "dancing":
                            try:
                                data = handler._rest("GET", "/robot/state")
                                mode = data.get("mode", "UNKNOWN")
                                status = data.get("status", "")
                                if mode == "STAND_DEFAULT" and status == "RUNNING":
                                    logger.info("Motion completed — resetting to idle")
                                    handler._state = "idle"
                                    handler._current_motion = None
                            except Exception:
                                pass

                        msg = json.dumps({
                            "robot_id": robot_id,
                            "state": handler._state,
                            "current_motion": handler._current_motion,
                            "mode": handler._get_mode(),
                            "timestamp": datetime.now(timezone.utc).isoformat(),
                        })
                        publish(status_topic, msg)
                    except Exception:
                        logger.exception("Heartbeat publish failed")
                else:
                    handler.handle_command(cmd)
            except queue.Empty:
                now = time.monotonic()
                # Poll every 2s while dancing, every 10s otherwise
                interval = 2 if handler._state == "dancing" else 10
                if now - last_heartbeat >= interval:
                    last_heartbeat = now
                    cmd_queue.put({"_type": "heartbeat"})

    worker_thread = threading.Thread(target=worker_loop, daemon=True)
    worker_thread.start()

    # ── Subscribe to commands ────────────────────────────────
    command_topic = MQTT_COMMAND_TOPIC_PREFIX.format(robot_id=robot_id) + "/#"

    def on_message(topic, payload, **kwargs):
        try:
            cmd = json.loads(payload)
            logger.info("Received on %s: %s", topic, json.dumps(cmd)[:200])
            cmd_queue.put(cmd)
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

    logger.info("MQTT client running. Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        logger.info("Disconnecting...")
        mqtt_connection.disconnect().result()
        logger.info("Done.")


if __name__ == "__main__":
    main()
