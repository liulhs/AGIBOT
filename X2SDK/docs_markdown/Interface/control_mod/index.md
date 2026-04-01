# 5.1 Control Module

**AgiBot X2 AimDK Control Module – Providing a Complete Low-Level Robot Control Interface**

The control module is a core component of the AgiBot X2 AimDK, providing comprehensive low-level control interfaces for the robot. It follows the ROS2 standard and supports both C++ and Python, enabling developers to achieve flexible and efficient robot control.

**Core Features**

- **Motion Control**: Multi-source input management, velocity control, and mode switching.
- **Joint Control**: Joint-level control with support for multiple control modes.
- **End-Effector Control**: Gripper and dexterous hand control.
- **Preset Motions**: A rich library of built-in motion presets.

**Interface Specifications**

- **Service Interfaces**: Use the `/aimdk_5Fmsgs/srv/` prefix.
- **Topic Interfaces**: Most use the `/aima/` prefix.
- **Message Types**: Provided in the `aimdk_msgs` package.
- **Supported Languages**: C++ and Python.
- **Message Format**: Standard ROS2 message formats.

**Version Compatibility**

- **Current Version**: v0.8
- **Minimum Supported Version**: v0.6 (partial feature support)
- **ROS2 Version**: Humble
- **Supported Architectures**: x86\_64, aarch64

**Safety Notes**

Warning

**Important Safety Reminders**

- When developing velocity-based control programs, remember to register your input source.
- Some joint control examples require temporarily disabling the MC module.
- It is recommended to test your code in a simulation environment first.
- Ensure the robot is operating in a safe environment.
- Taking Motion Control Computing Unit(PC1, 10.0.1.40) as build & run environment for secondary development is strictly prohibited to avoid safety risks

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

**Functional Modules**

- [5.1.1 Motion Mode Switching](modeswitch.html)
  - [Core Functions](modeswitch.html#id2)
  - [Motion Mode Query Service](modeswitch.html#id3)
  - [Motion Mode Set Service](modeswitch.html#id4)
  - [Programming Examples](modeswitch.html#id5)
  - [Safety Notes](modeswitch.html#id6)
- [5.1.2 Locomotion Control](locomotion.html)
  - [Control Functions](locomotion.html#id2)
  - [Locomotion Control Topic](locomotion.html#id3)
  - [Programming Examples](locomotion.html#id4)
  - [Safety Notes](locomotion.html#id5)
- [5.1.3 MC Control Signal Configuration](MC_control.html)
  - [Key Features](MC_control.html#id1)
  - [Input Source Configuration](MC_control.html#id3)
  - [Arbitration Workflow](MC_control.html#id5)
  - [Input Source Management Services](MC_control.html#id7)
  - [Programming Examples](MC_control.html#id8)
  - [Notes](MC_control.html#id9)
- [5.1.4 Preset Motion Control](preset_motion.html)
  - [Preset Motion Control Service](preset_motion.html#id2)
  - [Programming Examples](preset_motion.html#id3)
  - [Safety Notes](preset_motion.html#id4)
- [5.1.5 End Effector Control](endeffector.html)
  - [Hand Control Features](endeffector.html#id2)
  - [Hand Control Topics](endeffector.html#id3)
  - [Hand Status Topics](endeffector.html#id4)
  - [Hand Type Query Service](endeffector.html#id5)
  - [Programming Examples](endeffector.html#id6)
  - [Safety Notes](endeffector.html#id7)
- [5.1.6 Joint Control](joint_control.html)
  - [Key Features](joint_control.html#id2)
  - [Joint Control Topics](joint_control.html#id5)
  - [Joint State Query Service](joint_control.html#id6)
  - [Programming Examples](joint_control.html#id7)
  - [Safety Notes](joint_control.html#id8)
