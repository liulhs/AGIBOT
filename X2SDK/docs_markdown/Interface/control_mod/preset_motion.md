# 5.1.4 Preset Motion Control

**Preset motion control allows the robot to execute predefined actions such as waving, handshaking, raising an arm, etc. With a simple service call, the robot can quickly perform specific actions, making this interface ideal for common interaction scenarios.**

## Preset Motion Control Service

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/SetMcPresetMotion` | `SetMcPresetMotion` | Execute a preset motion(**switch to Stable Stand first**) |

- `SetMcPresetMotion` ros2-srv @ mc/motion/srv/SetMcPresetMotion.srv

  ```
  # Execute preset motion
  # Service: /aimdk_5Fmsgs/srv/SetMcPresetMotion

  # Request
  RequestHeader header             # Request header
  McControlArea area               # Control area
  McPresetMotion motion            # Preset motion
  bool interrupt                   # Whether to interrupt the previous action
  string ani_path                  # Custom animation path (to be supported in future)

  ---

  # Response
  CommonTaskResponse response      # Task response
  ```

  Where

  - `McControlArea` ros2-msg @ mc/motion/McControlArea.msg

    ```
    # Control area definition
    int32 value                      # Area value
    ```
  - `McPresetMotion` ros2-msg @ mc/motion/McPresetMotion.msg

    ```
    # Preset motion definition
    int32 value                      # Motion value
    ```

  Note: Starting from v0.8.0, the original area partitioning concept has been simplified. The `area` field is now used together with `motion` to map to specific actions. **The currently supported combinations are listed below:**

  | Action Name | `motion` | `area` | Notes |
  | --- | --- | --- | --- |
  | Right-hand wave | 1002 | 2 | switch to Stable Stand first |
  | Left-hand wave | 1002 | 1 | same as above |
  | Right-hand handshake | 1003 | 2 | same as above |
  | Left-hand handshake | 1003 | 1 | same as above |
  | Right-hand raise | 1001 | 2 | same as above |
  | Left-hand raise | 1001 | 1 | same as above |
  | Right-hand blow a kiss | 1004 | 2 | same as above |
  | Left-hand blow a kiss | 1004 | 1 | same as above |
  | Clap | 3017 | 11 | same as above |
  | Right-hand salute | 1013 | 2 | same as above |
  | Left-hand salute | 1013 | 1 | same as above |
  | Heart gesture (both hands) | 1007 | 3 | same as above |
  | Right-hand heart gesture | 1007 | 2 | same as above |
  | Left-hand heart gesture | 1007 | 1 | same as above |
  | Hug | 3008 | 11 | same as above |
  | Cheer | 3011 | 11 | same as above |
  | Raise both hands | 1010 | 3 | same as above |
  | Raise right hand | 1010 | 2 | same as above |
  | Raise left hand | 1010 | 1 | same as above |
  | Wave goodbye | 3031 | 11 | same as above |
  | Dynamic light wave | 3007 | 11 | same as above |
  | Right-hand high-five | 1008 | 2 | same as above |
  | Left-hand high-five | 1008 | 1 | same as above |
  | Cross arms | 3009 | 11 | same as above |
  | Right-hand wave at chest | 1011 | 2 | same as above |
  | Left-hand wave at chest | 1011 | 1 | same as above |
  | Bow | 3001 | 11 | same as above |
  | Scratch head | 3024 | 11 | same as above |
  | Grab buttocks | 3025 | 11 | same as above |

  - `CommonTaskResponse` ros2-msg @ common/CommonTaskResponse.msg

    ```
    # Embedded response message

    ResponseHeader header  # Response header
    uint64 task_id        # Task ID
    CommonState state     # State
    ```

    - `ResponseHeader` ros2-msg @ common/ResponseHeader.msg

      ```
      builtin_interfaces/Time stamp
      int64 code  # (0: success, others: failure)
      ```

    Use `response.header.code` to determine whether the request succeeded.

## Programming Examples

For detailed programming examples and code explanations, see:

- **C++ Example**: [Set Robot Motion](../../example/Cpp.html#cpp-preset-motion)
- **Python Example**: [Set robot action](../../example/Python.html#py-preset-motion)

## Safety Notes

Warning

**Motion Execution Limitations**

- Some motions may require the robot to be in a specific posture; ensure the robot is in a safe state before execution.

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

Note

**Best Practices**

- Set `interrupt=true` to interrupt any action currently in execution.
- Choose suitable motions and areas based on interaction scenarios.
