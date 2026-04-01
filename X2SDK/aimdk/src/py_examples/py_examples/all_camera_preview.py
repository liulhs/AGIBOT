#!/usr/bin/env python3
"""
All major camera streams preview dashboard for AgiBot X2.

This example subscribes to:
  - /aima/hal/sensor/rgbd_head_front/rgb_image
  - /aima/hal/sensor/rgbd_head_front/depth_image
  - /aima/hal/sensor/stereo_head_front_left/rgb_image
  - /aima/hal/sensor/stereo_head_front_right/rgb_image
  - /aima/hal/sensor/rgb_head_rear/rgb_image

It renders a single tiled OpenCV dashboard window and overlays stream labels
and simple FPS/status text. Press q or ESC in the preview window to exit.
"""

from collections import deque

import cv2
from cv_bridge import CvBridge, CvBridgeError
import numpy as np
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSDurabilityPolicy, QoSHistoryPolicy
from rclpy.qos import QoSProfile, QoSReliabilityPolicy
from sensor_msgs.msg import Image


class AllCameraPreview(Node):
    def __init__(self):
        super().__init__("all_camera_preview")

        self.bridge = CvBridge()
        self.window_name = "all_camera_preview"
        self.declare_parameter("tile_width", 320)
        self.declare_parameter("tile_height", 180)
        self.declare_parameter("display_scale", 1.0)
        self.tile_width = int(self.get_parameter("tile_width").value)
        self.tile_height = int(self.get_parameter("tile_height").value)
        self.display_scale = float(self.get_parameter("display_scale").value)
        self.dashboard_rows = 2
        self.dashboard_cols = 3
        self.shutdown_requested = False
        self.stream_order = [
            "rgbd_front_rgb",
            "rgbd_front_depth",
            "stereo_left",
            "stereo_right",
            "rear_head",
            "status",
        ]
        self.stream_specs = {
            "rgbd_front_rgb": {
                "topic": "/aima/hal/sensor/rgbd_head_front/rgb_image",
                "label": "rgbd_front_rgb",
                "encoding": "passthrough",
                "is_depth": False,
            },
            "rgbd_front_depth": {
                "topic": "/aima/hal/sensor/rgbd_head_front/depth_image",
                "label": "rgbd_front_depth",
                "encoding": "passthrough",
                "is_depth": True,
            },
            "stereo_left": {
                "topic": "/aima/hal/sensor/stereo_head_front_left/rgb_image",
                "label": "stereo_left",
                "encoding": "passthrough",
                "is_depth": False,
            },
            "stereo_right": {
                "topic": "/aima/hal/sensor/stereo_head_front_right/rgb_image",
                "label": "stereo_right",
                "encoding": "passthrough",
                "is_depth": False,
            },
            "rear_head": {
                "topic": "/aima/hal/sensor/rgb_head_rear/rgb_image",
                "label": "rear_head",
                "encoding": "passthrough",
                "is_depth": False,
            },
        }
        self.stream_state = {
            name: {
                "frame": None,
                "stamp_sec": None,
                "arrivals": deque(),
                "fps": 0.0,
                "encoding": "unknown",
                "size": None,
            }
            for name in self.stream_specs
        }

        qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=5,
            durability=QoSDurabilityPolicy.VOLATILE,
        )

        self.image_subscriptions = []
        for stream_name, spec in self.stream_specs.items():
            subscription = self.create_subscription(
                Image,
                spec["topic"],
                self._make_image_callback(stream_name),
                qos,
            )
            self.image_subscriptions.append(subscription)
            self.get_logger().info(
                f"✅ Subscribing {spec['label']}: {spec['topic']}"
            )

        cv2.namedWindow(self.window_name, cv2.WINDOW_AUTOSIZE)
        self.create_timer(0.05, self.render_dashboard)

    def _make_image_callback(self, stream_name):
        def callback(msg):
            self.handle_image(stream_name, msg)

        return callback

    def handle_image(self, stream_name, msg: Image):
        spec = self.stream_specs[stream_name]
        state = self.stream_state[stream_name]

        try:
            image = self.bridge.imgmsg_to_cv2(msg, desired_encoding=spec["encoding"])
        except CvBridgeError as exc:
            self.get_logger().error(
                f"Failed to convert {stream_name}: {exc}"
            )
            return

        state["frame"] = image
        state["stamp_sec"] = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
        state["encoding"] = msg.encoding
        state["size"] = (msg.width, msg.height)
        self._update_arrivals(state)

    def _update_arrivals(self, state):
        now = self.get_clock().now()
        state["arrivals"].append(now)
        while state["arrivals"] and (
            now - state["arrivals"][0]
        ).nanoseconds * 1e-9 > 1.0:
            state["arrivals"].popleft()
        state["fps"] = float(len(state["arrivals"]))

    def render_dashboard(self):
        if self.shutdown_requested:
            return

        tiles = []
        for stream_name in self.stream_order[:-1]:
            tiles.append(self.render_stream_tile(stream_name))
        tiles.append(self.render_status_tile())

        rows = []
        for idx in range(0, len(tiles), self.dashboard_cols):
            row_tiles = tiles[idx : idx + self.dashboard_cols]
            rows.append(np.hstack(row_tiles))
        dashboard = np.vstack(rows)

        if self.display_scale != 1.0:
            scaled_width = max(1, int(dashboard.shape[1] * self.display_scale))
            scaled_height = max(1, int(dashboard.shape[0] * self.display_scale))
            dashboard = cv2.resize(
                dashboard,
                (scaled_width, scaled_height),
                interpolation=cv2.INTER_AREA,
            )

        cv2.imshow(self.window_name, dashboard)
        key = cv2.waitKey(1) & 0xFF
        if key in (27, ord("q")):
            self.shutdown_requested = True
            rclpy.shutdown()

    def render_stream_tile(self, stream_name):
        spec = self.stream_specs[stream_name]
        state = self.stream_state[stream_name]
        frame = state["frame"]

        if frame is None:
            tile = self.make_placeholder_tile(
                spec["label"], "waiting for frames"
            )
        else:
            if spec["is_depth"]:
                tile = self.prepare_depth_tile(frame)
            else:
                tile = self.prepare_rgb_tile(frame)

            tile = cv2.resize(
                tile,
                (self.tile_width, self.tile_height),
                interpolation=cv2.INTER_AREA,
            )

        status = self.build_stream_status(stream_name)
        return self.draw_overlay(tile, spec["label"], status)

    def render_status_tile(self):
        tile = np.zeros((self.tile_height, self.tile_width, 3), dtype=np.uint8)
        cv2.rectangle(tile, (0, 0), (self.tile_width - 1, self.tile_height - 1), (90, 90, 90), 1)
        cv2.putText(
            tile,
            "all_camera_preview",
            (16, 34),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )

        lines = []
        for stream_name in self.stream_order[:-1]:
            state = self.stream_state[stream_name]
            status = "ready" if state["frame"] is not None else "waiting"
            lines.append(f"{stream_name}: {status} {state['fps']:.1f} fps")

        lines.append("Keys: q / ESC to exit")

        y = 72
        for line in lines:
            cv2.putText(
                tile,
                line,
                (16, y),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.55,
                (210, 210, 210),
                1,
                cv2.LINE_AA,
            )
            y += 30

        return tile

    def prepare_rgb_tile(self, frame):
        if frame.ndim == 2:
            return cv2.cvtColor(frame, cv2.COLOR_GRAY2BGR)

        if frame.shape[2] == 3:
            return cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        if frame.shape[2] == 4:
            return cv2.cvtColor(frame, cv2.COLOR_RGBA2BGR)

        return cv2.cvtColor(frame[:, :, :3], cv2.COLOR_RGB2BGR)

    def prepare_depth_tile(self, frame):
        depth = np.nan_to_num(frame, nan=0.0, posinf=0.0, neginf=0.0)
        depth = depth.astype(np.float32)
        valid_mask = depth > 0.0

        if np.any(valid_mask):
            valid_depth = depth[valid_mask]
            min_depth = float(np.min(valid_depth))
            max_depth = float(np.max(valid_depth))
            if max_depth > min_depth:
                normalized = np.zeros_like(depth, dtype=np.uint8)
                scaled = (depth - min_depth) / (max_depth - min_depth)
                normalized[valid_mask] = np.clip(
                    scaled[valid_mask] * 255.0, 0, 255
                ).astype(np.uint8)
            else:
                normalized = np.zeros_like(depth, dtype=np.uint8)
                normalized[valid_mask] = 255
        else:
            normalized = np.zeros_like(depth, dtype=np.uint8)

        colored = cv2.applyColorMap(normalized, cv2.COLORMAP_JET)
        colored[~valid_mask] = (0, 0, 0)
        return colored

    def make_placeholder_tile(self, label, message):
        tile = np.zeros((self.tile_height, self.tile_width, 3), dtype=np.uint8)
        cv2.rectangle(tile, (0, 0), (self.tile_width - 1, self.tile_height - 1), (90, 90, 90), 1)
        cv2.putText(
            tile,
            label,
            (16, 36),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            tile,
            message,
            (16, self.tile_height // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (180, 180, 180),
            2,
            cv2.LINE_AA,
        )
        return tile

    def build_stream_status(self, stream_name):
        state = self.stream_state[stream_name]
        size = state["size"]
        size_text = f"{size[0]}x{size[1]}" if size else "unknown"
        stamp_text = f"{state['stamp_sec']:.3f}" if state["stamp_sec"] is not None else "n/a"
        return (
            f"{state['encoding']} | {size_text} | "
            f"{state['fps']:.1f} fps | t={stamp_text}"
        )

    def draw_overlay(self, tile, label, status):
        overlay = tile.copy()
        cv2.rectangle(overlay, (0, 0), (self.tile_width, 54), (0, 0, 0), -1)
        cv2.rectangle(
            overlay,
            (0, self.tile_height - 30),
            (self.tile_width, self.tile_height),
            (0, 0, 0),
            -1,
        )
        cv2.addWeighted(overlay, 0.45, tile, 0.55, 0, tile)

        cv2.putText(
            tile,
            label,
            (12, 24),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.65,
            (255, 255, 255),
            2,
            cv2.LINE_AA,
        )
        cv2.putText(
            tile,
            status,
            (12, self.tile_height - 10),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.42,
            (230, 230, 230),
            1,
            cv2.LINE_AA,
        )
        return tile

    def destroy(self):
        if not self.shutdown_requested:
            self.shutdown_requested = True
        cv2.destroyAllWindows()
        self.destroy_node()


def main(args=None):
    rclpy.init(args=args)
    node = None
    try:
        node = AllCameraPreview()
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    except Exception as exc:
        print(f"Error: {exc}")
    finally:
        if node is not None:
            node.destroy()
        if rclpy.ok():
            rclpy.shutdown()


if __name__ == "__main__":
    main()
