# 5.3 Fault & System Management Module (Coming Soon)

**AgiBot X2 SDK Fault & System Management Module – Providing fault diagnostics and system management capabilities**

The Fault & System Management module is a key component of the AgiBot X2 SDK, providing fault diagnostics and system-level management capabilities. Through these interfaces, developers can promptly detect and handle robot faults, manage permissions, monitor system status, and ensure safe and stable operation.

**Key Features**

- **Fault Detection**: Hardware and software fault monitoring and diagnostics
- **Permission Management**: User role configuration, authentication, and access control
- **System Status Monitoring**: Runtime state and performance metrics tracking
- **Log Management**: System log recording, querying, and export
- **Alert Management**: Alert configuration, triggering, and handling

**Interface Specifications**

- **Service Interfaces**: Using the `/aimdk_5Fmsgs/srv/` prefix
- **Message Types**: Provided by the `aimdk_msgs` package
- **QoS Policy**: Fault messages use `RELIABLE` + `TRANSIENT_LOCAL` by default
- **Language Support**: C++ and Python
- **Message Format**: Standard ROS2 message definitions

**Version Compatibility**

- **Current Version**: v0.8 (partial functionality available)
- **Minimum Version**: v0.6 (basic functionality)
- **ROS2 Version**: Humble
- **Supported Architectures**: x86\_64, aarch64

**Safety Notes**

Warning

**Important Safety Reminders**

- Some features of the Fault & System Management module are still under development
- Permission management affects system security — operate with caution
- Fault detection consumes system resources — be mindful of performance impact

**Module Overview**

- [5.3.1 Fault Handling (Coming Soon)](fault.html)
- [5.3.2 Permission Management (Coming Soon)](sudo.html)
