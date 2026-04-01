# 5.1.6 Joint Control

**The joint control interfaces provide precise control over each robot joint, supporting multiple control modes and joint groups.**

## Key Features

### Control Modes

- **Position Control**: Drive a joint to a specified target angle.
- **Velocity Control**: Drive a joint at a specified angular velocity.
- **Torque Control**: Command a joint to output a specified torque.

### Supported Joints

- **Left Arm Joints**: 7-DoF (3 shoulder joints, 1 elbow joint, 3 wrist joints).
- **Right Arm Joints**: 7-DoF (3 shoulder joints, 1 elbow joint, 3 wrist joints).
- **Left Leg Joints**: 6-DoF (3 hip joints, 1 knee joint, 2 ankle joints).
- **Right Leg Joints**: 6-DoF (3 hip joints, 1 knee joint, 2 ankle joints).
- **Waist Joints**: Yaw, pitch, and roll.
- **Head Joints**: PitchN.Y.A., and yaw

## Joint Control Topics

Joints are controlled by body part (arms, legs, waist, head), and closed-loop control can be implemented using status feedback.

| Topic Name | Data Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/aima/hal/joint/*/command` | `JointCommandArray` | Joint control commands | - | Hz |
| `/aima/hal/joint/*/state` | `JointStateArray` | Joint state feedback | `TRANSIENT_LOCAL` | Hz |

Here, `*` can be `head` (requires supported head hardware), `arm`, `waist`, or `leg`.

- `JointCommandArray` ros2-msg @ hal/msg/JointCommandArray.msg

  ```
  # Joint control command array
  MessageHeader header             # Message header
  JointCommand[] joints            # Joint command array
  ```

  - `JointCommand` ros2-msg @ hal/msg/JointCommand.msg

    ```
    # Joint control command
    string name                      # Joint name (optional)
    float64 position                 # Position (rad)
    float64 velocity                 # Velocity (rad/s)
    float64 effort                   # Torque (N·m)
    float64 stiffness                # Stiffness (N·m/rad)
    float64 damping                  # Damping (N·m·s/rad)
    ```

  The length and ordering of `JointCommand[]` are defined in the table below.

  | Joint group | Length | Contents | Notes |
  | --- | --- | --- | --- |
  | head | 2 | `head_yaw`, `head_pitch` | only yaw now, and pitch is unavailable |
  | waist | 3 | `wrist_yaw`, `wrist_pitch`, `wrist_roll` |  |
  | arm | 7\*2 | `shoulder_pitch`, `shoulder_roll`, `shoulder_yaw`, `elbow`, `wrist_yaw`, `wrist_pitch`, `wrist_roll` | All left-side joints first, then all right-side joints |
  | leg | 6\*2 | `hip_pitch`, `hip_roll`, `hip_yaw`, `knee`, `ankle_pitch`, `ankle_roll` | All left-side joints first, then all right-side joints |
- `JointStateArray` ros2-msg @ hal/msg/JointStateArray.msg

  ```
  # Joint state array
  MessageHeader header             # Message header
  DomainErrorState state           # Joint error state
  JointState[] joints              # Joint state array
  ```

  - `DomainErrorState` ros2-msg @ hal/msg/DomainErrorState.msg

    ```
    # Joint error state
    uint8 value        # 1: Damping, 2: PowerOff, 3: Disabled, 4: Communication Failed, Others: NA
    ```
  - `JointState` ros2-msg @ hal/msg/JointState.msg

    ```
    # Joint state information
    string name                      # Joint name (currently unused)
    float64 position                 # Position (rad)
    float64 velocity                 # Velocity (rad/s)
    float64 effort                   # Torque (N·m)
    uint8 coil_temp                  # Coil temperature (°C)
    uint8 motor_temp                 # Motor temperature (°C)
    uint8 motor_vol                  # Motor voltage (V)
    ```

  The length and ordering of `JointState[]` follow the `JointCommand[]` joint ordering described in [Joint Order](joint_control.html#tbl-joint-order).

## Joint State Query Service

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/GetAllJointState` | `GetAllJointState` | Actively query joint states |

- `GetAllJointState` ros2-srv @ hal/srv/GetAllJointState.srv

  ```
  # Get all joint states
  # Service: /aimdk_5Fmsgs/srv/GetAllJointState

  # Request
  CommonRequest request            # Common request

  # Response
  CommonResponse reponse           # Common response
  JointState[] head_joints         # Head joint states
  JointState[] arm_joints          # Arm joint states
  JointState[] waist_joints        # Waist joint states
  JointState[] leg_joints          # Leg joint states
  ```

  The length and ordering of [`JointState[]`](joint_control.html#rosmsg-jointstate) follow the `JointCommand[]` [joint ordering description](joint_control.html#tbl-joint-order) above.

## Programming Examples

For detailed examples and code explanations, refer to:

- **C++ Example**: [Robot Joint Control Example](../../example/Cpp.html#cpp-joint-control)
- **Python Example**: [Robot joint control example](../../example/Python.html#py-joint-control)

## Safety Notes

Warning

**Joint Limits**

- All joints have motion range limits; exceeding them may cause mechanical damage.
- It is recommended to check that joint angles are within their safe ranges before sending commands.
- Be especially cautious about safety limits when using torque control.

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

Note

**Best Practices**

- Use smooth trajectory planning to avoid sudden joint motions.
- Implement joint state monitoring and anomaly detection.
- Ensure the robot is in a safe state before issuing control commands.
