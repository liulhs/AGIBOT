---
name: x2-aimsdk
description: AgiBot X2 AimDK (AI Motion Development Kit) SDK reference. Use this skill whenever the user asks about the AgiBot X2 humanoid robot SDK, including motion control, joint control, locomotion, preset motions, end-effector control, voice/screen/LED interaction, sensors, power management, startup/shutdown procedures, ROS 2 interfaces, or writing Python/C++ code for the X2 robot. Trigger on any mention of AimDK, AgiBot X2, x2 robot SDK, or robot control code involving this platform.
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
