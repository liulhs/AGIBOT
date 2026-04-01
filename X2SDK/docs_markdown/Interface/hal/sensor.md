# 5.4.1 Sensor Interfaces

**The sensor interfaces provide data access and control for the robot’s various sensors, including cameras, IMUs, LiDAR, and touch sensors.**

## Core Features

### Vision Sensors

- **RGB Camera**: Captures color images
- **Depth Camera**: Provides depth information
- **Camera Intrinsics**: Retrieves calibration parameters

### Pose Sensors

- **IMU Data**: Acceleration, angular velocity, and attitude angles
- **Gyroscope**: Measures angular velocity
- **Accelerometer**: Measures acceleration

### Environmental Perception Sensors

- **LiDAR**: Provides point cloud data
- **Touch Sensors**: Tactile feedback

## Standard Sensor Messages

Most sensor interfaces use the standard message types defined in ROS `sensor_msgs`:

| Sensor Data Type | Message Definition |
| --- | --- |
| Camera intrinsics | [`CameraInfo`](https://docs.ros.org/en/humble/p/sensor_msgs/msg/CameraInfo.html "sensor_msgs::msg::CameraInfo") |
| Raw image | [`Image`](https://docs.ros.org/en/humble/p/sensor_msgs/msg/Image.html "sensor_msgs::msg::Image") |
| Compressed image | [`CompressedImage`](https://docs.ros.org/en/humble/p/sensor_msgs/msg/CompressedImage.html "sensor_msgs::msg::CompressedImage") |
| IMU data | [`Imu`](https://docs.ros.org/en/humble/p/sensor_msgs/msg/Imu.html "sensor_msgs::msg::Imu") |
| LiDAR point cloud | [`PointCloud2`](https://docs.ros.org/en/humble/p/sensor_msgs/msg/PointCloud2.html "sensor_msgs::msg::PointCloud2") |

## IMU Topics

Includes chest IMU and torso IMU, both located on the development compute unit (PC2).
You can also use the IMUs integrated in [LiDAR](sensor.html#interface-lidar) and the [RGB-D camera](sensor.html#interface-rgbd-camera).

| Topic Name | Data Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/aima/hal/imu/chest/state` | `Imu` | Chest IMU data | `TRANSIENT_LOCAL` | 500Hz |
| `/aima/hal/imu/torso/state` | `Imu` | Torso IMU data | `TRANSIENT_LOCAL` | 500Hz |
| `/aima/hal/sensor/lidar_chest_front/imu` | `Imu` | LiDAR IMU data | `TRANSIENT_LOCAL` | 200Hz |
| `/aima/hal/sensor/rgbd_head_front/imu` | `Imu` | RGB-D camera IMU data | `RELIABLE` | 200Hz |

## Head Touch Status Topic

Supported features:

- Access low-level touch events and raw samples
- Disable the built-in “head pat” skill (to be enabled)

| Topic Name | Data Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/aima/hal/sensor/touch_head` | `TouchState` | Head touch status | `TRANSIENT_LOCAL` | 100Hz |

- `TouchState` ros2-msg @ hal/msg/TouchState.msg

  ```
  # Head touch status
  # Topic: /aima/hal/sensor/touch_head

  MessageHeader header             # Message header
  uint8 event_type                 # Touch event (0-unknown, 1-idle, 2-touch, 3-slide, 4-single tap, 5-double tap, 6-triple tap)
  uint32[8] data                   # Raw sensor values for 8 channels
  uint32[8] threshold              # Touch thresholds for 8 channels
  bool[8] is_touched               # Touch state of 8 channels
  ```

## Rear RGB Camera Topics

The rear RGB camera is on the development compute unit (PC2) and can be used for visual localization assistance and semantic scene understanding.
Raw image bandwidth is about 90 MB/s — **use only on the same compute unit, do not subscribe across units.**

| Topic Name | Data Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/aima/hal/sensor/rgb_head_rear/camera_info` | `CameraInfo` | Camera intrinsics | `RELIABLE`+`TRANSIENT_LOCAL` | N/A |
| `/aima/hal/sensor/rgb_head_rear/rgb_image` | `Image` | Raw image | `TRANSIENT_LOCAL` | 10Hz |
| `/aima/hal/sensor/rgb_head_rear/rgb_image/compressed` | `CompressedImage` | Compressed image | `TRANSIENT_LOCAL` | 10Hz |

Note: The handle behind AgiBot X2’s neck would obstruct the view of Rear RGB Camera partially. If your vision algorithms affected by this, please refer to [Rear Head Monocular Camera Data Subscription](../../example/Cpp.html#cpp-echo-camera-head-rear) to mask obstructed area of images

Obstructed view of Rear RGB Camera on default head posture:

[![后视RGB相机遮挡示意图](../../_images/camera_head_rear_obstructed.jpg)](../../_images/camera_head_rear_obstructed.jpg)

Rear RGB Camera - Obstructed View Diagram

## Stereo Camera Topics

The stereo camera is on the development compute unit (PC2) and can be used for stereo vision, teleoperation, obstacle perception, object recognition, VIO SLAM, VLA and more.
Raw image bandwidth is about 90 MB/s per eye — **use only on the same compute unit, do not subscribe across units.**

| Topic Name | Data Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/aima/hal/sensor/stereo_head_front_left/camera_info` | `CameraInfo` | Left camera intrinsics | `RELIABLE`+`TRANSIENT_LOCAL` | N/A |
| `/aima/hal/sensor/stereo_head_front_left/rgb_image` | `Image` | Left raw image | `TRANSIENT_LOCAL` | 10Hz |
| `/aima/hal/sensor/stereo_head_front_left/rgb_image/compressed` | `CompressedImage` | Left compressed image | `TRANSIENT_LOCAL` | 10Hz |
| `/aima/hal/sensor/stereo_head_front_right/camera_info` | `CameraInfo` | Right camera intrinsics | `RELIABLE`+`TRANSIENT_LOCAL` | N/A |
| `/aima/hal/sensor/stereo_head_front_right/rgb_image` | `Image` | Right raw image | `TRANSIENT_LOCAL` | 10Hz |
| `/aima/hal/sensor/stereo_head_front_right/rgb_image/compressed` | `CompressedImage` | Right compressed image | `TRANSIENT_LOCAL` | 10Hz |

## RGB-D Camera Topics

The RGB-D camera is on the development compute unit (PC2) and can be used for object detection, spatial obstacle avoidance, and semantic environment understanding.
**Raw image bandwidth is about 25 MB/s per stream — use only on the same compute unit, do not subscribe across units.**

| Topic Name | Data Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/aima/hal/sensor/rgbd_head_front/rgb_camera_info` | `CameraInfo` | RGB intrinsics | `RELIABLE` | 10Hz |
| `/aima/hal/sensor/rgbd_head_front/rgb_image` | `Image` | Raw image | `RELIABLE` | 10Hz |
| `/aima/hal/sensor/rgbd_head_front/rgb_image/compressed` | `CompressedImage` | Compressed image | `RELIABLE` | 10Hz |
| `/aima/hal/sensor/rgbd_head_front/depth_camera_info` | `CameraInfo` | Depth intrinsics | `RELIABLE` | 10Hz |
| `/aima/hal/sensor/rgbd_head_front/depth_image` | `Image` | Depth image | `RELIABLE` | 10Hz |
| `/aima/hal/sensor/rgbd_head_front/depth_pointcloud` | `PointCloud2` | Depth point cloud | `RELIABLE` | 10Hz |
| `/aima/hal/sensor/rgbd_head_front/imu` | `Imu` | IMU data | `RELIABLE` | 200Hz |

## LiDAR Topics

Provides LiDAR point clouds and LiDAR-integrated IMU data for obstacle avoidance and SLAM/localization.
The LiDAR is on the development compute unit (PC2) with data bandwidth on the order of 10 MB/s — cross-unit subscriptions are **not recommended**.

| Topic Name | Data Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/aima/hal/sensor/lidar_chest_front/lidar_pointcloud` | `PointCloud2` | LiDAR point cloud | `TRANSIENT_LOCAL` | 10Hz |
| `/aima/hal/sensor/lidar_chest_front/imu` | `Imu` | LiDAR IMU data | `TRANSIENT_LOCAL` | 200Hz |

## Code Examples

For detailed code samples and explanations, see:

- **C++ Examples**: [Code samples](../../example/Cpp.html), sensor interface section
- **Python Examples**: [Code samples](../../example/Python.html), sensor interface section

## Safety Notes

Attention

- For high-bandwidth raw camera streams, do not subscribe across compute units; this may destabilize the system and create safety risks.
