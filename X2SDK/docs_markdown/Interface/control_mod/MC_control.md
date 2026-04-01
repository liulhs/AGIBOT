# 5.1.3 MC Control Signal Configuration

**MC control signal configuration provides unified management of multiple input sources, ensuring the robot always responds to the highest-priority control signal.**

Control signal configuration is one of the core features of the AgiBot X2 AimDK, enabling unified management and priority arbitration among multiple control sources. This mechanism ensures that when multiple control inputs are active, the robot safely and reliably responds to the command with the highest priority.

## Key Features

### Multi-Source Integration

- **RC Control**: PS5 remote controller (priority 80)
- **VR Control**: Teleoperation control (priority 70)
- **App Control**: Control via the mobile app (priority 60)
- **Voice Control**: Voice-command control (priority 50)
- …
- **SDK Customization**: Developer-defined control sources (priority 20–100, configurable)

### Priority Management

- **Dynamic Adjustment**: Priority can be modified at runtime.
- **Automatic Arbitration**: Automatically selects the highest-priority active input source.
- **Conflict Resolution**: If multiple sources share the same priority, the earliest active source is selected.

## Input Source Configuration

### Priority Reference

- **100–80**: System-level control (emergency stop, safety modes)
- **79–60**: High-level control (remote controller, mobile app)
- **59–40**: Mid-level control (voice, gestures)
- **39–20**: Low-level control (SDK custom development sources)
- **19–0**: Backup control (debugging, testing)

## Arbitration Workflow

### Arbitration Mechanism

**Input Source Arbitration and Management Rules:**

- Commands from disabled or unknown input sources are discarded.
- Among valid sources, the system selects the one with the highest priority and accepts only its commands.
- If a new active source with a higher priority appears, it immediately replaces the current one.
- If the selected input source becomes inactive (timeout, etc.), it is treated as lowest priority and re-selection occurs.

**Note: After a system restart, all input-source priority states reset.**

Modules developed via SDK should register a **unique input source name** and assign an appropriate priority (recommended 20–100).

The built-in control input sources are listed below:

| `source` | Description | Priority | Timeout (ms) |
| --- | --- | --- | --- |
| rc | Remote controller | 80 | 1000 |
| app\_proxy | Agibot Go mobile app | 60 | 1000 |
| vr | Teleoperation module | 70 | 1000 |
| interaction | AgiBot Interaction module | 50 | 1000 |
| pnc | AgiBot Planner module | 40 | 1000 |

## Input Source Management Services

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/GetCurrentInputSource` | `GetCurrentInputSource` | Query the current control input source |
| `/aimdk_5Fmsgs/srv/SetMcInputSource` | `SetMcInputSource` | Configure input source |

- `GetCurrentInputSource` ros2-srv @ mc/motion/srv/GetCurrentInputSource.srv

  ```
  # Get current control input source
  # Service: /aimdk_5Fmsgs/srv/GetCurrentInputSource

  # Request
  CommonRequest request        # Standard request header

  ---

  # Response
  CommonTaskResponse response  # response.header.code = 0 indicates success
  McInputSource input_source   # Current input source
  ```

  - `McInputSource` ros2-msg @ mc/motion/McInputSource.msg

    ```
    string name               # Name of the currently selected input source (e.g., rc/vr/app_proxy/...)
    int32 priority             # Configured priority (0–100)
    int32 timeout              # Configured timeout (ms)
    ```
- `SetMcInputSource` ros2-srv @ mc/motion/srv/SetMcInputSource.srv

  ```
  # Service: /aimdk_5Fmsgs/srv/SetMcInputSource

  # Request
  CommonRequest request        # Standard request header
  McInputAction action         # Operation type (ADD/MODIFY/DELETE/DISABLE/ENABLE)
  McInputSource input_source   # Input source

  ---

  # Response
  CommonTaskResponse response  # response.header.code = 0 indicates success
  ```

  - `McInputAction` ros2-msg @ mc/motion/McInputAction.msg

    ```
    int32 value  # Operation type (1001: ADD, 1002: MODIFY, 1003: DELETE, 2001: ENABLE, 2002: DISABLE)
    ```

  | Operation Type (Value) | Description | Required field(s) in `input_source` |
  | --- | --- | --- |
  | ADD (1001) | Add new input source | `name`, `priority`, `timeout` |
  | MODIFY (1002) | Modify existing input source | `name`, `priority`, `timeout` |
  | DELETE (1003) | Delete input source | `name` |
  | ENABLE (2001) | Enable input source | `name` |
  | DISABLE (2002) | Disable input source | `name` |

## Programming Examples

For detailed programming examples and code explanations, refer to:

- **C++ Examples**:

  - [Register Secondary Development Input Source](../../example/Cpp.html#cpp-set-mc-input-source)
  - [Get Current Input Source](../../example/Cpp.html#cpp-get-mc-input-source)
- **Python Examples**:

  - [Register custom input source](../../example/Python.html#py-set-mc-input-source)
  - [Get current input source](../../example/Python.html#py-get-mc-input-source)

## Notes

Important

**Version Compatibility**: MC control signal configuration is available only in X2\_AimDK v0.7 and later; it is not supported in v0.6 or earlier.

Attention

SDK modules should register a **unique input-source name** based on the [system modules list](MC_control.html#mc-input-source-list) and assign an appropriate priority (recommended 20–100).

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

Note

Before the motion-control system receives any valid input (e.g., after power-on with no movement and all commanded velocities being zero), querying the current input source may return empty.
