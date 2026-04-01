# 5.1.2 Locomotion Control

**The locomotion control interfaces provide the core functions for controlling the robot’s walking and running velocities.**

## Control Functions

- Supports locomotion control based on lateral velocity, forward velocity, and yaw rate (angular velocity around the vertical axis).
- Supports dynamic management and priority arbitration of multiple control input sources.

## Locomotion Control Topic

| Topic Name | Data Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/aima/mc/locomotion/velocity` | `McLocomotionVelocity` | Locomotion control(**switch to Stable Stand first**) | - | - |

- `McLocomotionVelocity` ros2-msg @ mc/motion/McLocomotionVelocity.msg

  ```
  # Locomotion control
  # Topic: /aima/mc/locomotion/velocity

  MessageHeader header             # Message header
  string source                    # Input source name, custom for secondary development. Do not reuse names used by other modules; see notes below.
  float64 forward_velocity         # Forward/backward velocity (m/s), forward is positive
  float64 lateral_velocity         # Lateral velocity (m/s), left is positive
  float64 angular_velocity         # Yaw rate (rad/s), counterclockwise is positive
  ```

  **Note that here the developer is the publisher of locomotion control messages**, which may conflict with locomotion commands from other native system modules (such as the remote controller).

  The motion control system provides a multi-input management mechanism that arbitrates conflicting commands in real time based on priority.

  **Developers must register a custom input source and use it in the `source` field of locomotion commands.**

  For details, see the next section [MC Control Signal Configuration](MC_control.html).

  Locomotion start threshold constraints:

  When the robot is stationary, the first step requires the commanded target velocity to exceed a certain threshold. After the robot is already moving, smaller target velocities can be used. The target velocity is composed from `forward_velocity`, `lateral_velocity`, and `angular_velocity`. Reference threshold values for using a single control component are given in the table below.

  | Target velocity type | Start threshold | Notes |
  | --- | --- | --- |
  | `forward_velocity` | 0.09 | Forward/backward |
  | `lateral_velocity` | 0.60 | Absolute value; left/right both valid |
  | `angular_velocity` | 0.03 | Absolute value; clockwise/counterclockwise both valid |

Important

The thresholds may vary among releases, always check them and tune your code when the firmware changed

## Programming Examples

For detailed programming examples and code explanations, refer to:

- **C++ Examples**:

  - [Robot Locomotion Control](../../example/Cpp.html#cpp-locomotion)
  - [Register Secondary Development Input Source](../../example/Cpp.html#cpp-set-mc-input-source)
- **Python Examples**:

  - [Control robot locomotion](../../example/Python.html#py-locomotion)
  - [Register custom input source](../../example/Python.html#py-set-mc-input-source)

## Safety Notes

Warning

**Motion Control Constraints**

- Ensure the robot is in a safe state before switching motion modes.
- An input source must be registered before performing locomotion control.
- It is recommended to test locomotion control code in a simulation environment first.

Note

**Best Practices**

- Implement motion state monitoring and exception handling.
- Implement safety checks around locomotion control.
- Ensure velocity commands are smooth and continuous.
