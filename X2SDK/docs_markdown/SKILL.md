---
name: x2-aimsdk
description: AgiBot X2 AimDK (AI Motion Development Kit) SDK reference. Use this skill whenever the user asks about the AgiBot X2 humanoid robot SDK, including motion control, joint control, locomotion, preset motions, end-effector control, voice/screen/LED interaction, sensors, power management, startup/shutdown procedures, ROS 2 interfaces, writing Python/C++ code for the X2 robot, the X2 REST API, MQTT client, AWS IoT Core connectivity, or the Dance Kiosk cloud stack. Trigger on any mention of AimDK, AgiBot X2, x2 robot SDK, robot control code, x2_api, mqtt_client, or dance kiosk involving this platform.
---

# AimDK_X2 SDK — Claude Code Agent Skill

## Overview

This skill gives Claude Code agents full knowledge of the **AgiBot X2 AimDK** (AI Motion Development Kit), the SDK for programming the AgiBot X2 humanoid robot.

When a user asks about the X2 robot SDK — including motion control, sensor interfaces, voice/screen interaction, startup procedures, or code examples — **load the relevant markdown files from the documentation directory** before answering.

**Documentation base path:** `/Users/jasonliu/Github/AGIBOT/X2SDK/docs_markdown/`

All file references below are relative to this base path. When reading files, prepend this path.

---

## How to Use This Skill

1. **Identify the topic** from the user's request (e.g. "locomotion", "joint control", "voice", "startup").
2. **Read the matching markdown file(s)** from `/Users/jasonliu/Github/AGIBOT/X2SDK/docs_markdown/` using the index below.
3. **Answer using the file content** as authoritative reference.

You may read multiple files to answer a single question. File content is plain markdown — no stripping required.

---

## Documentation Structure

```
docs_markdown/
├── SKILL.md                          ← you are here
├── INDEX.md                          ← full flat file listing
│
├── index.md                          ← SDK introduction & table of contents
├── changelog.md                      ← version history
├── end_notes.md                      ← legal / secondary-dev boundaries
│
├── about_agibot_X2/
│   ├── index.md                      ← hardware overview
│   ├── part_name.md                  ← product overview (X2 Ultra)
│   ├── robot_specifications.md       ← weight, DOF, speed, power specs
│   ├── onboard_computer.md           ← standard & dev compute units
│   ├── user_debug_interface.md       ← debug port specs (Ultra)
│   ├── SDK_interface.md              ← secondary-dev interfaces (Ultra)
│   ├── sensor_fov.md                 ← LiDAR, RGB-D, stereo cams, IMU specs
│   ├── joint_name_and_limit.md       ← joint names + motion range (arm/leg/head/waist)
│   └── coordinate_system.md         ← robot coordinate conventions
│
├── operation_guide/
│   ├── index.md
│   ├── start_up_guide.md             ← 3 startup modes (gantry / supine / sitting)
│   ├── robot_connection.md           ← Agibot Go mobile app connection
│   ├── remote_controller.md          ← PS5 remote controller pairing
│   └── shutdown.md                   ← safe shutdown procedures
│
├── get_sdk/
│   └── index.md                      ← how to download the SDK package
│
├── quick_start/
│   ├── index.md                      ← quick-start chapter overview
│   ├── prerequisites.md              ← safety precautions & terminology
│   ├── run_example.md                ← running the bundled example programs
│   └── code_sample.md                ← step-by-step code tutorial (Python, ROS 2)
│
├── Interface/
│   ├── index.md                      ← interface chapter overview
│   │
│   ├── control_mod/
│   │   ├── index.md                  ← control module overview
│   │   ├── modeswitch.md             ← motion mode switching API
│   │   ├── locomotion.md             ← locomotion (walking/velocity) control
│   │   ├── MC_control.md             ← MC signal config & priority arbitration
│   │   ├── preset_motion.md          ← preset motion (wave, handshake, …) API
│   │   ├── endeffector.md            ← end-effector (hand/gripper) control
│   │   └── joint_control.md          ← low-level joint position/velocity/torque
│   │
│   ├── interactor/
│   │   ├── index.md                  ← interaction module overview
│   │   ├── voice.md                  ← TTS / ASR / speech playback API
│   │   ├── screen.md                 ← face-screen rendering API
│   │   └── lights.md                 ← LED strip control API
│   │
│   ├── hal/
│   │   ├── index.md                  ← HAL module overview
│   │   ├── sensor.md                 ← IMU, touch, audio sensor interfaces
│   │   └── pmu.md                    ← power management unit (battery, voltage)
│   │
│   ├── perception/
│   │   ├── index.md                  ← perception module overview (coming soon)
│   │   ├── vision.md                 ← vision interface (coming soon)
│   │   └── SLAM.md                   ← SLAM interface (coming soon)
│   │
│   └── FASM/
│       ├── index.md                  ← fault & system management overview
│       ├── fault.md                  ← fault handling (coming soon)
│       └── sudo.md                   ← permission management (coming soon)
│
├── example/
│   ├── index.md                      ← example chapter overview
│   ├── Python.md                     ← full Python interface usage examples
│   └── Cpp.md                        ← full C++ interface usage examples
│
└── faq/
    ├── index.md                      ← FAQ overview
    └── temp_works.md                 ← temporary / transitional solutions
```

---

## Key Topics Quick-Reference

| User asks about… | Read these files |
|---|---|
| Robot hardware, specs, sensors | `about_agibot_X2/robot_specifications.md`, `about_agibot_X2/sensor_fov.md` |
| Joint names, limits, DOF | `about_agibot_X2/joint_name_and_limit.md` |
| Starting up / shutting down the robot | `operation_guide/start_up_guide.md`, `operation_guide/shutdown.md` |
| Connecting via app or controller | `operation_guide/robot_connection.md`, `operation_guide/remote_controller.md` |
| Getting the SDK / installation | `get_sdk/index.md`, `quick_start/prerequisites.md` |
| Running examples | `quick_start/run_example.md` |
| Writing control code (tutorial) | `quick_start/code_sample.md` |
| Motion mode switching | `Interface/control_mod/modeswitch.md` |
| Walking / velocity commands | `Interface/control_mod/locomotion.md` |
| Input source priority / arbitration | `Interface/control_mod/MC_control.md` |
| Preset motions (wave, handshake…) | `Interface/control_mod/preset_motion.md` |
| Hand / gripper / end-effector | `Interface/control_mod/endeffector.md` |
| Raw joint control | `Interface/control_mod/joint_control.md` |
| Speech / TTS / ASR | `Interface/interactor/voice.md` |
| Face screen display | `Interface/interactor/screen.md` |
| LED lights | `Interface/interactor/lights.md` |
| IMU / touch / audio sensors | `Interface/hal/sensor.md` |
| Battery / power status | `Interface/hal/pmu.md` |
| Full Python code examples | `example/Python.md` |
| Full C++ code examples | `example/Cpp.md` |
| Errors / troubleshooting | `faq/index.md`, `faq/temp_works.md` |
| Changelog / version history | `changelog.md` |

---

## SDK Technology Stack

- **Communication**: ROS 2 (Humble)
- **Languages**: Python 3, C++ (C++17)
- **Build system**: colcon / CMake
- **Robot**: AgiBot X2 humanoid (29 DOF, ~65 kg)
- **Key interfaces**: ROS 2 topics, services, and actions via `aimdk_msgs`

## Important Notes for Code Generation

- Always check `quick_start/prerequisites.md` for safety precautions before generating robot-control code.
- The robot must be in **Stable Standing Mode** before most motion commands are issued.
- Use the SDK input-source registration pattern (see `Interface/control_mod/MC_control.md`) rather than raw topic publishing, to ensure priority-safe control.
- Standard ROS 2 cross-host services have reliability issues; follow SDK example patterns (retransmission, exception safety) shown in `example/Python.md` and `example/Cpp.md`.
- Data under `$HOME/aimdk*` is managed by the system — do not write user data there.

---

## X2 Robot Services (Deployed)

The robot runs two custom services alongside the AIMDK stack. Source code is at `/Users/jasonliu/Github/AGIBOT/x2_api/`, deployed to `/home/run/x2_api/` on the robot.

### REST API (`x2-motion-api.service`)

Flask REST API on port 8080 exposing motion control over HTTP.

| Component | File | Purpose |
|-----------|------|---------|
| `server.py` | Flask app, routes | HTTP endpoints for motion control |
| `ros2_bridge.py` | ROS2 wrapper | Service calls with retry logic |
| `motion_catalog.py` | Motion registry | YAML-based motion ID → ROS2 tag mapping |
| `auth.py` | Authentication | API key validation |
| `config.py` | Configuration | Shared settings (REST + MQTT) |

**Endpoints:** `/api/v1/health`, `/api/v1/robot/state`, `/api/v1/motions`, `/api/v1/motions/play`, `/api/v1/motions/stop`, `/api/v1/robot/mode`, `/api/v1/presets/play`

### MQTT Client (`x2-mqtt-client.service`)

AWS IoT Core MQTT client for cloud-to-robot command dispatch. Delegates all robot control to the local REST API on `localhost:8080` — no direct ROS2 calls, avoiding `rclpy.spin_until_future_complete` threading deadlocks.

| Component | File | Purpose |
|-----------|------|---------|
| `mqtt_client.py` | MQTT handler | Command dispatch via REST API, state publishing, LWT |
| `mqtt_run.sh` | Launcher | Sets env vars, starts mqtt_client.py (no ROS2 env needed) |
| `certs/` | TLS certs | X.509 mutual TLS (cert.pem, private.key, AmazonRootCA1.pem) |

**Topics:** `x2/{robot_id}/command/#` (subscribe), `x2/{robot_id}/status` (publish)

**Actions:** `play_motion`, `stop_motion`, `set_mode`, `play_preset`

**Key behaviors:**
- **REST API delegation:** All robot control goes through `localhost:8080` — no direct ROS2 calls
- **Command queue:** Single worker thread processes commands and heartbeats sequentially, preventing race conditions
- **Motion completion detection:** Polls robot state every 2s while dancing; auto-resets to `idle` when motion finishes
- **Adaptive heartbeat:** Publishes status every 10s (idle) or 2s (dancing) to keep DynamoDB fresh
- **LWT:** Auto-publishes `state: "offline"` on disconnect
- **Auto-stand:** Safe multi-step transition to STAND_DEFAULT before playing motions (PASSIVE → DAMPING → JOINT → STAND, with settling time at each step)
- **Startup wait:** Waits up to 30s for REST API to be available before connecting to MQTT

### AWS Dance Kiosk Cloud Stack

CloudFormation stack `X2DanceKiosk` in `us-east-2`. Source at `/Users/jasonliu/Github/AGIBOT/cloud/`.

| Component | Path | Purpose |
|-----------|------|---------|
| `cloud/infra/template.yaml` | SAM template | Full stack definition |
| `cloud/lambdas/create_checkout.py` | Lambda | Stripe Checkout Session creation |
| `cloud/lambdas/handle_webhook.py` | Lambda | Stripe webhook → MQTT command |
| `cloud/lambdas/get_status.py` | Lambda | DynamoDB → robot state |
| `cloud/web/` | S3/CloudFront | Kiosk SPA (HTML/CSS/JS) |
| `cloud/scripts/provision_robot.py` | Script | IoT Thing + cert provisioning |

**Flow:** Browser → Stripe Checkout → webhook Lambda → MQTT publish → Robot plays dance
**If robot busy:** Auto-refunds via Stripe
**CloudFront:** Custom error responses (403/404 → `index.html`) for SPA routing

**URLs:**
- Kiosk: `https://d3h2rdy9lq3b29.cloudfront.net`
- API: `https://x37qk3dqwc.execute-api.us-east-2.amazonaws.com/prod`
- IoT: `a1thbiemoccm90-ats.iot.us-east-2.amazonaws.com`

For full documentation, see `/Users/jasonliu/Github/AGIBOT/x2_api/README.md`.
