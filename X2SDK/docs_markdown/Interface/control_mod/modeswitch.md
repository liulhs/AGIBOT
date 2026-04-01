# 5.1.1 Motion Mode Switching

**The mode-switch and locomotion interfaces provide core capabilities for switching motion modes and controlling walking/running.**

## Core Functions

Supports switching into the following basic motion modes:

| Mode | Value | Description | Use cases |
| --- | --- | --- | --- |
| Zero-Torque Mode | `PASSIVE_DEFAULT` | Robot joints zero torque, free state | System startup, maintenance, soft e-stop |
| Damping Mode | `DAMPING_DEFAULT` | The joint exhibits a damping effect | Safe movement |
| Position-controlled Stand | `JOINT_DEFAULT` | Position-controlled stand | Precise joint position control |
| Stable Stand | `STAND_DEFAULT` | Active force to ensure standing | Dynamic balance control, walking/action ready state |
| Locomotion Mode | `LOCOMOTION_DEFAULT` | Normal walking/running | Daily movement |

**Note: Starting from v0.8.0, the stable-stand mode and Locomotion Mode are unified and will switch internally based on the current motion commands.**

## Motion Mode Query Service

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/GetMcAction` | `GetMcAction` | Query current motion mode |

- `GetMcAction` ros2-srv @ mc/action/srv/GetMcAction.srv

  ```
  # Get current motion mode
  # Service: /aimdk_5Fmsgs/srv/GetMcAction

  # Request
  CommonRequest request            # Common request

  ---

  # Response
  ResponseHeader response          # Response header
  McActionInfo info                # Information about the current motion mode
  ```

  - `McActionInfo` ros2-msg @ mc/action/McActionInfo.msg

    ```
    # Motion mode information
    McAction current_action  # Current motion mode(abandoned since v0.8.2)
    string action_desc       # Description
    McActionStatus status    # Status of the motion mode
    ```

    - `McActionStatus` ros2-msg @ mc/action/McActionStatus.msg

      ```
      int32 value  # Action status (100: running, 200: switching)
      ```

## Motion Mode Set Service

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/SetMcAction` | `SetMcAction` | Set motion mode |

- `SetMcAction` ros2-srv @ mc/motion/srv/SetMcAction.srv

  ```
  # Set motion mode
  # Service: /aimdk_5Fmsgs/srv/SetMcAction

  # Request
  RequestHeader header             # Request header
  string source                    # Input source
  McActionCommand command          # Motion command

  ---

  # Response
  CommonResponse response          # Generic response; response.status.value = 1 indicates success
  ```

  - `McActionCommand` ros2-msg @ mc/motion/McActionCommand.msg

    ```
    # McActionCommand
    McAction action      # abandoned since v0.8.2
    string action_desc   # Mode description
    ```

## Programming Examples

For detailed programming examples and code explanations, see:

- **C++ Examples**: [Get Robot Mode](../../example/Cpp.html#cpp-get-mc-action) [Set Robot Mode](../../example/Cpp.html#cpp-set-mc-action)
- **Python Examples**: [Get robot mode](../../example/Python.html#py-get-mc-action) [Set robot mode](../../example/Python.html#py-set-mc-action)

## Safety Notes

Warning

- **Do not use motion modes or mode descriptions that are not explicitly documented in this section.**
- Ensure the robot is in a safe state before switching motion modes.
- It is recommended to test motion-control code in a simulation environment first.
- Do not deploy SDK applications on the motion-control compute unit (PC1) to avoid interfering with high real-time motion tasks.

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

Note

**Best Practices**

- Implement motion state monitoring and exception handling.
- Implement additional safety checks around motion control where possible.
