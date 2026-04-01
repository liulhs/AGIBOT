# 5.4 Hardware Abstraction Module

**AgiBot X2 AimDK Hardware Abstraction Module – Provides Low-Level Hardware Interfaces and Sensor Data Access**

The hardware abstraction module is a foundational component of the AgiBot X2 AimDK, providing abstracted interfaces to the robot’s various hardware devices. It follows the ROS2 standard and supports both C++ and Python, offering developers a unified hardware access interface.

**Core Features**

- **Sensor Interfaces**: cameras, IMU, LiDAR, touch sensors, etc.
- **Power Management**: battery status monitoring and power control
- **Hardware Monitoring**: device status monitoring and fault diagnostics
- **Data Acquisition**: real-time sensor data collection

**Interface Specifications**

- **Message Types**: uses `aimdk_msgs` and `sensor_msgs` packages
- **QoS Policy**: sensor data uses `BEST_EFFORT` + `VOLATILE` by default
- **Language Support**: C++ and Python
- **Message Format**: standard ROS2 message format

**Version Compatibility**

- **Current Version**: v0.8
- **Minimum Supported Version**: v0.6 (partial features)
- **ROS2 Version**: Humble
- **Supported Architectures**: x86\_64, aarch64

**Safety Notes**

Warning

**Hardware Interface Limitations**

- Sensor data can be large; pay attention to memory management
- Hardware control must be used carefully to avoid equipment damage

**Functional Modules**

- [5.4.1 Sensor Interfaces](sensor.html)
- [5.4.2 Power Management Unit (PMU)](pmu.html)
