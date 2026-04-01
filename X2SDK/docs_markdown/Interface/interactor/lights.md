# 5.2.3 LED Strip Control

**The chest LED strip control interface provides enhanced visual interaction capabilities.**

## Key Features

- Independent RGB component control
- Multiple display modes supported

## LED Strip Control Service

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/LedStripCommand` | `LedStripCommand` | LED Strip Control |

Attention

The LED strip service responds slowly; expect ~5 seconds for a full call. For multitasking, run this service in a separate thread or use asynchronous calls.

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

- `LedStripCommand` ros2-srv @ hal/srv/LedStripCommand.srv

  ```
  # LED Strip Control
  # Service: /aimdk_5Fmsgs/srv/LedStripCommand

  # Request
  CommonRequest request  # Request header

  uint8 led_strip_mode  # LED mode (0: steady, 1: breathing, 2: blinking, 3: flowing)
  uint8 r  # Red component (0–255)
  uint8 g  # Green component (0–255)
  uint8 b  # Blue component (0–255)

  ---

  # Response
  ResponseHeader header  # Response header
  uint16 status_code  # Status code (0: success, others: failure)
  ```

  `led_strip_mode` description:

  | Value | Mode | Description |
  | --- | --- | --- |
  | 0 | Steady |  |
  | 1 | Breathing | 4-second cycle, sinusoidal brightness transition |
  | 2 | Blinking | 1-second cycle, toggles every 0.5s |
  | 3 | Flowing | 2-second cycle, lights move left → right, then turn off simultaneously |

## Programming Examples

For detailed programming samples and explanations, refer to:

- **C++ Example**: [LED Strip Control](../../example/Cpp.html#cpp-play-lights)
- **Python Example**: [LED light strip control](../../example/Python.html#py-play-lights)
