# AGIBOT X2 Motion System — Complete Reference

> Findings from reverse-engineering the X2 Ultra (SN: X220026C2Z0063) running firmware v0.9.4, OS `lx2501_3_t2d5-soc1-v0.4.57`, AIMDK `release-lx2501_3_t2d5-soc1-v0.9.4`.

---

## 1. Hardware Architecture

The X2 is a **dual-SoC humanoid robot**:

| SoC | Hardware | Role | SSH Access |
|-----|----------|------|------------|
| SoC0 | ARM (custom) | Realtime motion control, EtherCAT, cloud_proxy | Not directly accessible from dev network |
| SoC1 | NVIDIA Jetson Orin NX (aarch64) | AI/perception, DRP, SDK development | `ssh X2` (profile configured) |

**Inter-SoC networking:**
- `10.0.1.40` / `10.0.1.41` — develop0 interface (SoC0 / SoC1)
- `10.0.200.40` / `10.0.200.41` — ssh0 interface (SoC0 / SoC1)
- `10.11.1.1` — sensor0 (SoC1)
- `192.168.50.227` — WiFi (SoC1, network: "robotx 5G")
- `48.x.x.x` — 5G modem wwan0 (SoC1)

**SDK development runs on SoC1.** Never run SDK code on SoC0/PC1 (the motion control compute unit).

---

## 2. OS Layout (SoC1)

| Path | Purpose |
|------|---------|
| `/agibot/software/` | Main software partition |
| `/agibot/software/entry/` | Boot scripts, process manager config (`run_agibot.yaml`) |
| `/agibot/software/ec/` | EtherCAT communications, HDS diagnostics |
| `/agibot/software/dm/` | Decision-making / data management |
| `/agibot/software/drp/` | Dynamic Runtime Platform (motion resources, protobuf types) |
| `/agibot/software/nav/` | Navigation, planning, motion control (vectorflux/PNC) |
| `/agibot/software/em/` | Execution Manager (process lifecycle) |
| `/agibot/software/common/share/protocol/proto/` | Protobuf service definitions |
| `/agibot/software/common/share/protocol/py/` | Python protobuf generated code |
| `/agibot/software/cloud_proxy/` | Cloud/app gateway (runs on SoC0, config visible via NFS) |
| `/agibot/nfs/soc0/var/robot_proxy/resources/` | Downloaded LinkCraft motion resources (ONNX policies) |
| `/agibot/nfs/soc0/var/mc/audit.log` | MC motion execution audit trail |
| `/agibot/nfs/soc0/log/log_YYYYMMDD_HHMMSS/` | Per-boot log directories for each module |
| `/home/run/aimdk/` | AIMDK SDK (Python/C++ examples, user workspace) |
| `/opt/ros/humble/` | ROS2 Humble distribution |

---

## 3. CLI Tool: `aima`

Located at `/usr/local/bin/aima`. Key subcommands:

```bash
aima em list-apps          # List all managed processes
aima em start-app <name>   # Start a process
aima em stop-app <name>    # Stop a process
aima em run-app <name>     # Run interactively
aima robot                 # Robot info
aima log                   # Log management
aima doctor                # Diagnostics
aima topic / node / proc   # ROS2-like introspection
```

---

## 4. Motion System — Three Layers

### 4a. Mode Switching (`SetMcAction`)

Controls the robot's operating state. **Must be in STAND_DEFAULT before any motion.**

| Mode | Description |
|------|-------------|
| `PASSIVE_DEFAULT` | Zero torque, limp joints (startup/maintenance) |
| `DAMPING_DEFAULT` | Damping mode (safe movement) |
| `JOINT_DEFAULT` | Position-locked stand (precise joint control) |
| `STAND_DEFAULT` | Auto-balanced stand (**required for motions**) |
| `LOCOMOTION_DEFAULT` | Walking/running mode |
| `SIT_DOWN_DEFAULT` | Sit down |
| `CROUCH_DOWN_DEFAULT` | Crouch |
| `LIE_DOWN_DEFAULT` | Lie down |
| `STAND_UP_DEFAULT` | Stand up from lying |
| `ASCEND_STAIRS` / `DESCEND_STAIRS` | Stair modes |

**ROS2 Service:** `/aimdk_5Fmsgs/srv/SetMcAction`
**Query:** `/aimdk_5Fmsgs/srv/GetMcAction`

### 4b. Preset Motions (`SetMcPresetMotion`)

Built-in gestures. Available in the **public AIMDK SDK**.

| ID | Motion | Area |
|----|--------|------|
| 1001 | Raise Hand | 1 (left) or 2 (right) |
| 1002 | Wave Hand | 1 or 2 |
| 1003 | Handshake | 1 or 2 |
| 1004 | Flying Kiss | 1 or 2 |
| 1008 | Clap | 11 (both) |
| 1013 | Salute | 2 (right) |
| 3001 | Bow | 11 |
| 3002 | Thumbs Up | 11 |
| 3003 | Peace Sign | 11 |
| 3004 | Heart Above Head | 3 |
| 3008 | Hug | 11 |
| 3011 | Cheer | 11 |
| 3013-14 | Bass Dance 1 & 2 | 11 |
| 4001 | Nod Head | 4 (head) |
| 4002 | Shake Head | 4 |

**Area values:** 1=LEFT_HAND, 2=RIGHT_HAND, 3=both hands, 4=HEAD, 8=WAIST, 11=full body

**ROS2 Service:** `/aimdk_5Fmsgs/srv/SetMcPresetMotion`
**Query:** `/aimdk_5Fmsgs/srv/GetMcPresetMotionState`

### 4c. LinkCraft Motions (ONNX neural-net policies)

Full-body motions stored as ONNX files. **NOT in the public AIMDK SDK** — requires the `drp` package.

**Available on robot:**

| Tag (for SetMcMotion) | Display Name | Resource Key |
|------------------------|-------------|--------------|
| `linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6_0.0.1` | Golf Swing Pro | `linkcraft_resource_onnx_01KMS0NMK8F7MMFSET1MDV0BG6` |
| `linkcraft_resource_onnx_erlianti_0.0.1` | Double Kick | `linkcraft_resource_onnx_erlianti` |
| `linkcraft_resource_onnx_zuiquan_0.0.1` | Drunk Kung Fu | `linkcraft_resource_onnx_zuiquan` |
| `linkcraft_resource_onnx_taiji_0.0.1` | Tai Chi | `linkcraft_resource_onnx_taiji` |
| `linkcraft_resource_onnx_tianmao_0.0.1` | Miao | `linkcraft_resource_onnx_tianmao` |
| `linkcraft_resource_onnx_depasito_0.0.1` | Despacito Dance | `linkcraft_resource_onnx_depasito` |
| `linkcraft_resource_onnx_01KEVJX7PSAZQ04TW6YGPBP5SV_0.0.1` | Love You | `linkcraft_resource_onnx_01KEVJX7PSAZQ04TW6YGPBP5SV` |
| `linkcraft_resource_01KMRTZQ9HWX5WBEAYEK251GQ2_0.0.1` | Golf Swing (CSV) | `linkcraft_resource_01KMRTZQ9HWX5WBEAYEK251GQ2` |

**Tag naming convention:** `{resource_key}_{version}` (e.g., `linkcraft_resource_onnx_zuiquan_0.0.1`)

**Resource path convention:** `/agibot/nfs/soc0/var/robot_proxy/resources/{resource_key}/{version}/unzip/policy.onnx`

**Resource catalog:** `/agibot/nfs/soc0/var/robot_proxy/resources/resource_config.yaml`

---

## 5. LinkCraft Motion — How to Trigger

### Step 1: Environment Setup

```bash
source /opt/ros/humble/setup.bash
source ~/aimdk/install/setup.bash
export PYTHONPATH=/agibot/software/drp/local/lib/python3.10/dist-packages:$PYTHONPATH
export LD_LIBRARY_PATH=/agibot/software/drp/lib:$LD_LIBRARY_PATH
```

**Why the drp paths?** The user AIMDK at `~/aimdk/install/aimdk_msgs/` does NOT include `RegisterCustomMotion`, `SetMcMotion`, or `GetMcMotions`. These interfaces exist only in `/agibot/software/drp/share/aimdk_msgs/`. Adding drp to `AMENT_PREFIX_PATH` makes `ros2 interface show` work; adding the Python/lib paths makes Python imports work.

### Step 2: Register the Motion

Motions are **NOT auto-registered at boot**. DRP registers them **on-demand** before each play. You must call `RegisterCustomMotion` yourself.

```python
from aimdk_msgs.srv import RegisterCustomMotion
from aimdk_msgs.msg import McMotion, McMotionType

req = RegisterCustomMotion.Request()
motion = McMotion()
motion.tag = "linkcraft_resource_onnx_zuiquan_0.0.1"  # EXACT tag format
motion_type = McMotionType()
motion_type.value = McMotionType.MIMIC  # 2 for ONNX
motion.type = motion_type
req.motion = motion
req.res_path = "/agibot/nfs/soc0/var/robot_proxy/resources/linkcraft_resource_onnx_zuiquan/0.0.1/unzip/policy.onnx"
req.write_to_disk = False
```

**Critical:** The `res_path` must point to the **actual `.onnx` file**, NOT the directory. Using a directory or wrong tag will crash the MC module ("运动模块心跳异常") and force a reboot.

Re-registering an already-registered motion returns a warning ("Motion already registered") but does NOT crash — this is safe.

### Step 3: Play the Motion

```python
from aimdk_msgs.srv import SetMcMotion

req = SetMcMotion.Request()
req.header = RequestHeader()
motion = McMotion()
motion.tag = "linkcraft_resource_onnx_zuiquan_0.0.1"
motion_type = McMotionType()
motion_type.value = McMotionType.MIMIC
motion.type = motion_type
req.motion = motion
req.interrupt = False
req.play_timestamp = 0  # Play immediately
```

### ROS2 Service Retry Pattern

ROS2 cross-host service calls are unreliable. Always use retry logic:

```python
for i in range(8):
    request.header.stamp = self.get_clock().now().to_msg()
    future = self.client.call_async(request)
    rclpy.spin_until_future_complete(self, future, timeout_sec=0.5)
    if future.done() and future.result() is not None:
        break
```

---

## 6. ROS2 Services — Full List (Motion-Related)

| Service | Package | Purpose |
|---------|---------|---------|
| `/aimdk_5Fmsgs/srv/SetMcAction` | aimdk (user SDK) | Switch robot mode |
| `/aimdk_5Fmsgs/srv/GetMcAction` | aimdk (user SDK) | Query current mode |
| `/aimdk_5Fmsgs/srv/SetMcPresetMotion` | aimdk (user SDK) | Play preset gesture |
| `/aimdk_5Fmsgs/srv/GetMcPresetMotionState` | aimdk (user SDK) | Query preset motion state |
| `/aimdk_5Fmsgs/srv/RegisterCustomMotion` | drp only | Register a LinkCraft motion with MC |
| `/aimdk_5Fmsgs/srv/SetMcMotion` | drp only | Play a registered LinkCraft motion |
| `/aimdk_5Fmsgs/srv/GetMcMotions` | drp only | List registered LinkCraft motions |
| `/aimdk_5Fmsgs/srv/SetMcMotionSeq` | drp only | Play motion sequence (not yet implemented) |
| `/aimdk_5Fmsgs/srv/SetMcInputSource` | aimdk (user SDK) | Register locomotion input source |
| `/aimdk_5Fmsgs/srv/SetMcLocomotionSpeedMode` | aimdk (user SDK) | Set walking speed |
| `/aimdk_5Fmsgs/srv/SetMcSecureMotion` | drp only | Safety motion control |
| `/aimdk_5Fmsgs/srv/SetAgileMotionState` | drp only | Agile motion state |

---

## 7. Service Interface Definitions

### SetMcMotion.srv
```
RequestHeader header          # header.stamp (builtin_interfaces/Time)
McMotion motion               # { tag: string, type: McMotionType }
bool interrupt                # Interrupt current motion
uint64 play_timestamp         # 0 = immediate, else UNIX ms
---
CommonResponse response       # { header: { stamp, code }, status: CommonState }
```

### RegisterCustomMotion.srv
```
McMotion motion               # { tag: string, type: McMotionType }
string res_path               # Full path to policy.onnx file
bool write_to_disk            # Persist registration (not yet functional)
---
CommonResponse response       # { header: { stamp, code }, status: CommonState }
```

### McMotion.msg
```
string tag                    # Motion name (resource_key + version)
McMotionType type             # { value: int32 }
```

### McMotionType.msg
```
int32 NONE = 0
int32 ANIMATION = 1           # CSV trajectory (upper body)
int32 MIMIC = 2               # ONNX neural-net policy (full body)
int32 FOUNDATION = 3          # Base/foundation motion
```

---

## 8. Protobuf MotionCommandService (Cloud/App Path)

Defined at `/agibot/software/common/share/protocol/proto/aimdk/protocol/motion_player/motion_command.proto`.

```protobuf
service MotionCommandService {
  rpc SendMotionCommand(MotionCommandRequest) returns (CommonResponse);
  rpc GetMotionStatus(CommonRequest) returns (MotionCommandResponse);
  rpc GetMotionList(CommonRequest) returns (MotionListResponse);
}
```

**Hosted by:** `cloud_proxy` on SoC0, port 51057, via HTTP + MQTT.

**HTTP endpoints:**
```
POST http://<soc0-ip>:51057/rpc/aimdk.protocol.MotionCommandService/SendMotionCommand
POST http://<soc0-ip>:51057/rpc/aimdk.protocol.MotionCommandService/GetMotionStatus
POST http://<soc0-ip>:51057/rpc/aimdk.protocol.MotionCommandService/GetMotionList
```

**NOT usable from SoC1** — connections establish but time out. This API is designed for the AGIBOT mobile app via MQTT/cloud, not for on-robot SDK code. The backend routing goes through cloud_proxy's nginx-like proxy layer which expects app-level authentication/sessions.

**Python protobuf packages:**
- `/agibot/software/common/share/protocol/py/aimdk/protocol/motion_player/motion_command_pb2.py`
- `/agibot/software/common/share/protocol/py/aimdk/protocol/motion_player/motion_command_aimrt_rpc_pb2.py`

---

## 9. Danger Zones

1. **Wrong tag or path in RegisterCustomMotion** → Crashes MC module → "运动模块心跳异常" → Robot powers down → Requires reboot
2. **Running SDK code on SoC0/PC1** → Can interfere with realtime motion control
3. **SetMcAction while robot is not physically stable** → Robot may fall
4. **Publishing to joint command topics without proper control loop** → Dangerous at 500Hz
5. **Locomotion without registered input source** → Commands ignored silently

---

## 10. Example Files on Robot

| File | Purpose |
|------|---------|
| `/home/run/aimdk/src/py_examples/py_examples/preset_motion_client.py` | Preset gesture example |
| `/home/run/aimdk/src/py_examples/py_examples/set_mc_action.py` | Mode switching example |
| `/home/run/aimdk/src/py_examples/py_examples/set_mc_input_source.py` | Input source registration |
| `/home/run/aimdk/src/py_examples/py_examples/mc_locomotion_velocity.py` | Walking velocity control |
| `/home/run/aimdk/src/py_examples/py_examples/motocontrol.py` | Direct joint control (Ruckig) |
| `/home/run/test_golf_swing.py` | LinkCraft motion test script (we wrote this) |

---

## 11. Software Dependencies on SoC1

- **Python 3.10.12**
- **ROS2 Humble** at `/opt/ros/humble/`
- **Flask 3.1.2** + flask-cors 6.0.2 (already installed)
- **requests 2.25.1** (installed)
- **awsiotsdk** (AWS IoT Device SDK, installed via pip3)
- FastAPI/uvicorn NOT installed (can be `pip3 install --user`)
- AimRT middleware (custom, C++ based, Python bindings via protobuf)
- Available ports: 8000, 5000 free. **Port 8080 in use** by x2-motion-api.service.
- Disk: 384GB free

---

## 12. Deployed Services on SoC1

Two custom systemd services run at `/home/run/x2_api/`:

| Service | Port/Protocol | Purpose | Status |
|---------|---------------|---------|--------|
| `x2-motion-api.service` | HTTP :8080 | Flask REST API for motion control | enabled, active |
| `x2-mqtt-client.service` | MQTT (TLS) | AWS IoT Core client for cloud commands | enabled, active |

The REST API uses `ros2_bridge.py`, `motion_catalog.py`, and `config.py` directly. The MQTT client delegates all robot control to the REST API on `localhost:8080` (no direct ROS2 calls) — this avoids `rclpy.spin_until_future_complete` threading deadlocks. The MQTT client depends on the REST API and waits up to 30s for it at startup.

**MQTT client key features:** REST API delegation, command queue (single worker thread), motion completion detection (polls state every 2s while dancing), adaptive heartbeat (10s idle / 2s dancing), LWT offline detection, auto-stand.

### WiFi / Network

- **SSID:** `robotx 5G` (5GHz, WPA2/WPA3)
- **WiFi IP:** `192.168.50.227` (DHCP, metric 600)
- **5G Cellular:** `wwan0` (primary default route)
- **Autoconnect:** `no` — WiFi managed by Agibot housekeeper (`aima nm`), does NOT auto-reconnect on reboot
- The 5G cellular connection provides internet fallback even without WiFi

### AWS IoT Core Connection

- **Thing Name:** `x2-001`
- **IoT Endpoint:** `a1thbiemoccm90-ats.iot.us-east-2.amazonaws.com`
- **Certs:** `/home/run/x2_api/certs/` (cert.pem, private.key, AmazonRootCA1.pem)
- **Policy:** `X2DanceKiosk-x2-001` (connect, subscribe command/*, receive command/*, publish status + status/*)
- **Provisioned via:** `cloud/scripts/provision_robot.py x2-001 --scp`
