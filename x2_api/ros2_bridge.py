# x2_api/ros2_bridge.py
"""ROS2 bridge — wraps all aimdk_msgs service calls for the Flask API.

This module creates a single rclpy node that persists for the lifetime of the
Flask app. All methods use the SDK-standard retry pattern (8 attempts, 500ms
timeout per attempt) because ROS2 cross-host service calls are unreliable.
"""
import threading
import logging
from typing import Optional
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
        self._node: Optional[Node] = None
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

    def _call(self, client_name: str, request, label: str = "") -> Optional[object]:
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
        """Register a LinkCraft motion with MC. Returns {success, message}.

        After calling RegisterCustomMotion, verifies the motion is actually
        in MC's registry via GetMcMotions.  This catches silent failures where
        MC returns code=0 but doesn't load the motion.
        """
        req = RegisterCustomMotion.Request()
        motion = McMotion()
        motion.tag = tag
        mt = McMotionType()
        mt.value = motion_type
        motion.type = mt
        req.motion = motion
        req.res_path = res_path
        req.write_to_disk = False

        logger.info("Registering motion: tag=%s, type=%d, path=%s", tag, motion_type, res_path)

        resp = self._call("register_motion", req, "RegisterCustomMotion")
        if resp is None:
            return {"success": False, "message": "Service call failed (no response)"}

        code = resp.response.header.code
        status = resp.response.status.value
        logger.info("RegisterCustomMotion response: code=%d, status=%d", code, status)

        if code == 0 and status == CommonState.SUCCESS:
            logger.info("Registration returned SUCCESS, verifying in MC registry...")
        else:
            logger.warning("Registration returned code=%d, status=%d — verifying in MC registry...", code, status)

        # Verify the motion is actually in MC's registry (like test_golf_swing.py)
        registered = self.list_registered_motions()
        found = any(m["tag"] == tag for m in registered)
        logger.info("MC registry has %d motions, target '%s' %s",
                     len(registered), tag, "FOUND" if found else "NOT FOUND")
        if registered:
            for m in registered:
                marker = " <-- TARGET" if m["tag"] == tag else ""
                logger.debug("  - %s (type=%d)%s", m["tag"], m["type"], marker)

        if found:
            return {"success": True, "message": "Verified in MC registry"}
        return {"success": False, "message": f"NOT in MC registry after register (code={code}, status={status})"}

    def play_motion(self, tag: str, motion_type: int, interrupt: bool = False) -> dict:
        """Play a registered LinkCraft motion. Returns {success, message}.

        Pre-checks that the motion is in MC's registry before attempting to play.
        """
        # Pre-check: verify motion is registered before trying to play
        registered = self.list_registered_motions()
        found = any(m["tag"] == tag for m in registered)
        if not found:
            logger.error("Motion '%s' NOT in MC registry — cannot play. Registered: %s",
                         tag, [m["tag"] for m in registered])
            return {"success": False,
                    "message": f"Motion '{tag}' not in MC registry ({len(registered)} motions registered)"}

        logger.info("Playing motion: tag=%s, type=%d, interrupt=%s", tag, motion_type, interrupt)

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
            return {"success": False, "message": "Service call failed (no response)"}

        code = resp.response.header.code
        logger.info("SetMcMotion response: code=%d", code)

        if code == 0:
            return {"success": True, "message": "Motion playing"}
        return {"success": False, "message": f"SetMcMotion failed (code={code})"}

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
