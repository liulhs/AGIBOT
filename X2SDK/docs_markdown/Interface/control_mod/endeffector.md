# 5.1.5 End Effector Control

The end-effector control module currently supports:

- Dexterous Hand: OmniHand Dynamic Edition 2025
- Gripper: OmniPicker

## Hand Control Features

- **Dexterous Hand Mode**: Supports multi-finger coordinated control, suitable for complex manipulation.
- **Gripper Mode**: Supports open/close control, suitable for simple grasping.
- **Status Monitoring**: Real-time monitoring of hand status and fault codes.
- **Type Query**: Supports dynamic querying of the current hand type.

## Hand Control Topics

| Topic Name | Message Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/aima/hal/joint/hand/command` | `HandCommandArray` | Hand control command | - | Hz |

- `HandCommandArray` ros2-msg @ hal/msg/HandCommandArray.msg

  ```
  # Hand command array
  MessageHeader header             # Message header
  HandType left_hand_type          # Left hand type (1: Dexterous Hand, 2: Gripper)
  HandCommand[] left_hands         # Left hand commands
  HandType right_hand_type         # Right hand type (1: Dexterous Hand, 2: Gripper)
  HandCommand[] right_hands        # Right hand commands
  ```

  Notes on `HandCommand[]` length and ordering:

  | Hand Type | Array Length | Order | Additional Info |
  | --- | --- | --- | --- |
  | Gripper OmniPicker | 1 | N/A | N/A |
  | Dexterous Hand OmniHand | 10 | `ThumbRoll`, `ThumbAbAd`, `ThumbMCP`, `IndexAbAd`, `IndexPIP`, `MiddlePIP`, `RingAbAd`, `RingPIP`, `PinkyAbAd`, `PinkyPIP` | Currently only supports configuring all joints at once; arranged in active joint index order |

  - `HandCommand` ros2-msg @ hal/msg/HandCommand.msg

    ```
    # Hand control command
    string name                      # Joint name
    float64 position                 # Position
    float64 velocity                 # Velocity
    float64 acceleration             # Acceleration
    float64 deceleration             # Deceleration
    float64 effort                   # Effort / torque
    ```

    **Note: The meaning and value range of these fields varies significantly depending on the hand type:**

    - Gripper OmniPicker:

      | Field Name | Value Range | Description |
      | --- | --- | --- |
      | position | 0.0-1.0 (float) | Linearly maps gripper open/close travel; 1.0 = fully open |
      | velocity | 0.0-1.0 (float) | Linearly maps gripper speed; 1.0 = maximum speed |
      | acceleration | 0.0-1.0 (float) | Linearly maps gripper acceleration; 1.0 = maximum acceleration |
      | deceleration | 0.0-1.0 (float) | Linearly maps gripper deceleration; 1.0 = maximum deceleration |
      | effort | 0.0-1.0 (float) | Linearly maps gripper holding torque; 1.0 = maximum torque |
    - Dexterous Hand OmniHand:

      | Field Name | Value Range | Description |
      | --- | --- | --- |
      | position | Active joint range, in radians (rad) | See the OmniHand developer manual |
      | velocity | N/A | Not used |
      | acceleration | N/A | Not used |
      | deceleration | N/A | Not used |
      | effort | N/A | Not used |

Attention

Before attempting to control the hand autonomously, **ensure the robot is in a safe state and disable the native MC module on PC1 using `aima em stop-app mc`**.

If your application requires native locomotion management while using hand control, please contact technical support for system-level adaptation.

## Hand Status Topics

| Topic Name | Message Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/aima/hal/joint/hand/state` | `HandStateArray` | Hand status information | `TRANSIENT_LOCAL` | Same frequency as commands |

- `HandStateArray` ros2-msg @ hal/msg/HandStateArray.msg

  ```
  # Hand status array
  MessageHeader header             # Message header
  HandType left_hand_type          # Left hand type (1: Dexterous Hand, 2: Gripper)
  HandState[] left_hands           # Left hand states
  HandType right_hand_type         # Right hand type (1: Dexterous Hand, 2: Gripper)
  HandState[] right_hands          # Right hand states
  ```

  Notes on `HandState[]` length and ordering:

  | Hand Type | Array Length | Order | Additional Info |
  | --- | --- | --- | --- |
  | Gripper OmniPicker | 1 | N/A | N/A |
  | Dexterous Hand OmniHand Dynamic Edition 2025 | 10 | Ordered by active joint index, consistent with the earlier [`HandCommand[]`](endeffector.html#tbl-hand-order). | N/A |

  - `HandState` ros2-msg @ hal/msg/HandState.msg

    ```
    # Hand status information
    string name                      # Joint name
    float64 position                 # Current position
    float64 velocity                 # Current velocity
    float64 effort                   # Current torque
    int32 state                      # State
    int32 faultcode                  # Fault code
    ```

    **Note: The meaning and value range of these fields varies significantly depending on the hand type:**

    - Gripper OmniPicker:

      | Field Name | Value Range | Description |
      | --- | --- | --- |
      | position | 0.0-1.0 (float) | Current travel; same value range as above |
      | velocity | 0.0-1.0 (float) | Current speed; same value range as above |
      | effort | 0.0-1.0 (float) | Current torque; same value range as above |
      | state | 0 - reached target position / 1 - gripper moving / 2 - gripper stalled / 3 - object dropped | State |
      | faultcode | 0 - no fault / 1 - over-temperature warning / 2 - overspeed warning / 3 - initialization fault warning / 4 - limit-detection warning | Fault code |
    - Dexterous Hand OmniHand:

      | Field Name | Value Range | Description |
      | --- | --- | --- |
      | position | radians (rad) | Current position |
      | velocity | N/A | Not yet used |
      | effort | N/A | Current (A), to be implemented |
      | state | N/A | Not yet used |
      | faultcode | N/A | Fault code, pending adaptation |

## Hand Type Query Service

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/GetHandType` | `GetHandType` | Actively query the hand type |

- `GetHandType` ros2-srv @ hal/srv/GetHandType.srv

  ```
  # Get hand type
  # Service: /aimdk_5Fmsgs/srv/GetHandType

  # Request
  CommonRequest request            # Common request

  # Response
  CommonResponse reponse           # Common response
  HandType left_hands_type         # Left hand type (1: Dexterous Hand, 2: Gripper)
  HandType right_hands_type        # Right hand type (1: Dexterous Hand, 2: Gripper)
  ```

  `HandType` definition same as above: 0x0-None, 0x1-Dexterous Hand, 0x2-Gripper, 0xFF-Error.

## Programming Examples

For detailed programming examples and explanations, refer to:

- **C++ Example**: [Gripper Control](../../example/Cpp.html#cpp-hand-control)
- **Python Example**: [Robot joint control example](../../example/Python.html#py-joint-control)

## Safety Notes

Warning

- Autonomous control of the hand requires disabling native motor control. Ensure control of other joints and maintain proper safety precautions.
- Do not modify hand component configurations manually. For special system-level adaptation, please contact technical support.

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**
