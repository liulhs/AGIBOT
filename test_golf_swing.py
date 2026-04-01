#!/usr/bin/env python3
"""
Test Golf Swing (ONNX) on AGIBOT X2

DRP registers motions on-demand (not at boot). This script:
  1. Queries current mode (safety check)
  2. Switches to STAND_DEFAULT if needed
  3. Registers the motion with MC (correct tag + path to .onnx file)
  4. Plays the Golf Swing via SetMcMotion

Usage:
  scp test_golf_swing.py X2:/home/run/
  ssh X2
  source /opt/ros/humble/setup.bash
  source ~/aimdk/install/setup.bash
  export PYTHONPATH=/agibot/software/drp/local/lib/python3.10/dist-packages:$PYTHONPATH
  export LD_LIBRARY_PATH=/agibot/software/drp/lib:$LD_LIBRARY_PATH
  python3 test_golf_swing.py
"""

import sys
import time
import rclpy
from rclpy.node import Node

# Standard SDK imports
from aimdk_msgs.srv import SetMcAction, GetMcAction
from aimdk_msgs.msg import (
    RequestHeader, CommonState, McActionCommand,
)

# LinkCraft imports (from /agibot/software/drp)
from aimdk_msgs.srv import RegisterCustomMotion, SetMcMotion, GetMcMotions
from aimdk_msgs.msg import McMotion, McMotionType


# ── Motion config ────────────────────────────────────────────────
# Tag and path must match EXACTLY what MC audit.log expects:
#   tag  = {resource_key}_{version}
#   path = full path to the policy.onnx FILE (not directory)
MOTION_TAG = "linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6_0.0.1"
MOTION_TYPE = McMotionType.MIMIC  # 2 = ONNX policy
MOTION_RES_PATH = (
    "/agibot/nfs/soc0/var/robot_proxy/resources/"
    "linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6/0.0.1/unzip/policy.onnx"
)

# Other available motions (uncomment to try):
# MOTION_TAG = "linkcraft_resource_onnx_erlianti_0.0.1"      # Double Kick
# MOTION_RES_PATH = "/agibot/nfs/soc0/var/robot_proxy/resources/linkcraft_resource_onnx_erlianti/0.0.1/unzip/policy.onnx"
#
# MOTION_TAG = "linkcraft_resource_onnx_zuiquan_0.0.1"       # Drunk Kung Fu
# MOTION_RES_PATH = "/agibot/nfs/soc0/var/robot_proxy/resources/linkcraft_resource_onnx_zuiquan/0.0.1/unzip/policy.onnx"
#
# MOTION_TAG = "linkcraft_resource_onnx_taiji_0.0.1"         # Tai Chi
# MOTION_RES_PATH = "/agibot/nfs/soc0/var/robot_proxy/resources/linkcraft_resource_onnx_taiji/0.0.1/unzip/policy.onnx"
#
# MOTION_TAG = "linkcraft_resource_onnx_tianmao_0.0.1"       # Miao
# MOTION_RES_PATH = "/agibot/nfs/soc0/var/robot_proxy/resources/linkcraft_resource_onnx_tianmao/0.0.1/unzip/policy.onnx"
#
# MOTION_TAG = "linkcraft_resource_onnx_depasito_0.0.1"      # Despacito
# MOTION_RES_PATH = "/agibot/nfs/soc0/var/robot_proxy/resources/linkcraft_resource_onnx_depasito/0.0.1/unzip/policy.onnx"
#
# MOTION_TAG = "linkcraft_resource_onnx_01KEVJX7PSAZQ04TW6YGPBP5SV_0.0.1"  # Love You
# MOTION_RES_PATH = "/agibot/nfs/soc0/var/robot_proxy/resources/linkcraft_resource_onnx_01KEVJX7PSAZQ04TW6YGPBP5SV/0.0.1/unzip/policy.onnx"


class GolfSwingTest(Node):
    def __init__(self):
        super().__init__("golf_swing_test")

        # Create service clients
        self.action_client = self.create_client(
            SetMcAction, "/aimdk_5Fmsgs/srv/SetMcAction"
        )
        self.get_action_client = self.create_client(
            GetMcAction, "/aimdk_5Fmsgs/srv/GetMcAction"
        )
        self.register_client = self.create_client(
            RegisterCustomMotion, "/aimdk_5Fmsgs/srv/RegisterCustomMotion"
        )
        self.get_motions_client = self.create_client(
            GetMcMotions, "/aimdk_5Fmsgs/srv/GetMcMotions"
        )
        self.play_client = self.create_client(
            SetMcMotion, "/aimdk_5Fmsgs/srv/SetMcMotion"
        )

        # Wait for essential services
        for name, client in [
            ("SetMcAction", self.action_client),
            ("GetMcAction", self.get_action_client),
            ("RegisterCustomMotion", self.register_client),
            ("GetMcMotions", self.get_motions_client),
            ("SetMcMotion", self.play_client),
        ]:
            self.get_logger().info(f"Waiting for {name} service...")
            if not client.wait_for_service(timeout_sec=5.0):
                self.get_logger().error(f"{name} service not available!")
                sys.exit(1)

        self.get_logger().info("All services available.")

    def _call_service(self, client, request, label="service", retries=8):
        """Call a ROS2 service with retry logic (handles unreliable remote calls)."""
        for i in range(retries):
            if hasattr(request, "header") and hasattr(request.header, "stamp"):
                request.header.stamp = self.get_clock().now().to_msg()

            future = client.call_async(request)
            rclpy.spin_until_future_complete(self, future, timeout_sec=0.5)

            if future.done():
                result = future.result()
                if result is not None:
                    return result

            self.get_logger().info(f"  retry {label} [{i+1}/{retries}]")

        self.get_logger().error(f"{label} failed after {retries} retries.")
        return None

    # ── Step 1: Check current mode ───────────────────────────────────
    def get_current_mode(self) -> str:
        self.get_logger().info("=" * 50)
        self.get_logger().info("Step 1: Checking current robot mode...")

        req = GetMcAction.Request()
        req.request.header = RequestHeader()

        resp = self._call_service(self.get_action_client, req, "GetMcAction")
        if resp is None:
            return "UNKNOWN"

        mode = resp.info.action_desc
        status = resp.info.status.value
        status_str = "RUNNING" if status == 100 else "SWITCHING" if status == 200 else f"({status})"
        self.get_logger().info(f"Current mode: {mode} [{status_str}]")
        return mode

    # ── Step 2: Switch to STAND_DEFAULT ──────────────────────────────
    def stand_up(self):
        self.get_logger().info("=" * 50)
        self.get_logger().info("Step 2: Switching to STAND_DEFAULT mode...")

        req = SetMcAction.Request()
        req.header = RequestHeader()
        cmd = McActionCommand()
        cmd.action_desc = "STAND_DEFAULT"
        req.command = cmd

        resp = self._call_service(self.action_client, req, "SetMcAction")
        if resp is None:
            return False

        if resp.response.status.value == CommonState.SUCCESS:
            self.get_logger().info("Robot is now in STAND_DEFAULT mode.")
            return True
        else:
            self.get_logger().error(
                f"Failed to set STAND_DEFAULT (status={resp.response.status.value})"
            )
            return False

    # ── Step 3: Register the motion ─────────────────────────────────
    def register_motion(self) -> bool:
        self.get_logger().info("=" * 50)
        self.get_logger().info(
            f"Step 3: Registering motion with MC...\n"
            f"  tag:  {MOTION_TAG}\n"
            f"  type: MIMIC ({MOTION_TYPE})\n"
            f"  path: {MOTION_RES_PATH}"
        )

        req = RegisterCustomMotion.Request()
        motion = McMotion()
        motion.tag = MOTION_TAG
        motion_type = McMotionType()
        motion_type.value = MOTION_TYPE
        motion.type = motion_type
        req.motion = motion
        req.res_path = MOTION_RES_PATH
        req.write_to_disk = False

        resp = self._call_service(self.register_client, req, "RegisterCustomMotion")
        if resp is None:
            return False

        code = resp.response.header.code
        status = resp.response.status.value
        if code == 0 and status == CommonState.SUCCESS:
            self.get_logger().info("Motion registered successfully.")
            return True
        else:
            # code != 0 likely means "already registered" — that's fine
            self.get_logger().info(
                f"Registration returned code={code}, status={status} "
                f"(likely already registered, continuing)."
            )
            return True

    # ── Step 3b: Verify registration ─────────────────────────────────
    def verify_registration(self) -> bool:
        self.get_logger().info("Verifying registration...")

        req = GetMcMotions.Request()
        req.header = RequestHeader()

        resp = self._call_service(self.get_motions_client, req, "GetMcMotions")
        if resp is None:
            self.get_logger().warn("Could not query motion list, continuing anyway.")
            return True

        if len(resp.motion) == 0:
            self.get_logger().warn("Motion list still empty after registration.")
            return True  # Might still work — continue to play

        self.get_logger().info(f"Registered motions ({len(resp.motion)}):")
        found = False
        for m in resp.motion:
            marker = "  <-- WILL PLAY THIS" if m.tag == MOTION_TAG else ""
            self.get_logger().info(f"  - {m.tag} (type={m.type.value}){marker}")
            if m.tag == MOTION_TAG:
                found = True

        if found:
            self.get_logger().info("Target motion confirmed in registry.")
        return True  # Don't block — try to play regardless

    # ── Step 4: Play the motion ──────────────────────────────────────
    def play_motion(self):
        self.get_logger().info("=" * 50)
        self.get_logger().info(f"Step 4: Playing motion '{MOTION_TAG}'...")

        req = SetMcMotion.Request()
        req.header = RequestHeader()

        motion = McMotion()
        motion.tag = MOTION_TAG
        motion_type = McMotionType()
        motion_type.value = MOTION_TYPE
        motion.type = motion_type

        req.motion = motion
        req.interrupt = False
        req.play_timestamp = 0  # Play immediately

        resp = self._call_service(self.play_client, req, "SetMcMotion")
        if resp is None:
            return False

        if resp.response.header.code == 0:
            self.get_logger().info("Motion playing!")
            return True
        else:
            self.get_logger().error(
                f"Failed to play motion (code={resp.response.header.code})"
            )
            return False


def main():
    rclpy.init()
    node = None

    try:
        node = GolfSwingTest()

        # Step 1: Check current mode
        current_mode = node.get_current_mode()

        # Step 2: Switch to STAND_DEFAULT if not already
        if current_mode == "STAND_DEFAULT":
            node.get_logger().info("Already in STAND_DEFAULT, skipping mode switch.")
        else:
            if not node.stand_up():
                node.get_logger().error("Aborting: could not enter STAND_DEFAULT.")
                return
            node.get_logger().info("Waiting 5s for robot to stabilize...")
            time.sleep(5.0)

        # Step 3: Register motion (DRP does this on-demand, not at boot)
        if not node.register_motion():
            node.get_logger().error("Aborting: could not register motion.")
            return

        time.sleep(1.0)

        # Step 3b: Verify (informational, won't block)
        node.verify_registration()

        # Step 4: Play!
        confirm = input(
            f"\nReady to play: {MOTION_TAG}\n"
            f"Press ENTER to swing! (or Ctrl+C to abort)\n"
        )
        node.play_motion()

        # Keep alive to observe
        node.get_logger().info("Waiting for motion to complete... (Ctrl+C to exit)")
        while rclpy.ok():
            rclpy.spin_once(node, timeout_sec=1.0)

    except KeyboardInterrupt:
        print("\nInterrupted by user.")
    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if node:
            node.destroy_node()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
