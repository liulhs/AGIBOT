# 5 Interface Description

**AgiBot X2 AimDK Interface Documentation – ROS2-based humanoid robot development interfaces**

The AgiBot X2 AimDK provides a complete set of ROS2 interfaces for controlling the AgiBot X2 humanoid robot. The interfaces follow ROS2 standards and support both C++ and Python, offering developers a flexible and efficient environment for robot application development.

**Package structure** The aimdk\_msgs protocol package is organized by module layers. The srv and msg structures vary across modules, but all correctly link to generate stub code corresponding to the aimdk\_msgs interfaces.

```
aimdk_msgs/interface/robot
├── hal/                    # Hardware Abstraction Layer
│   ├── msg/                # General messages
│   ├── srv/                # Control-related services
│   └── audio/              # Audio related
├── mc/                     # Motion control module
│   ├── action/             # Motion mode related
│   ├── data/               # State data
│   └── motion/             # Motion control
└── ...                     # Additional interfaces
```

**Module overview**

🤖 **Control Module** – Provides low-level robot control interfaces including motion control, joint control, and end-effector control

- MC control signal configuration and input source management
- Joint control and mode switching
- Preset action execution
- End-effector control (gripper/dexterous hand)

🎯 **Perception Module (Coming soon)** – Provides multimodal perception capabilities including vision and SLAM

- Visual perception
- SLAM localization and mapping
- Multi-sensor fusion

💬 **Interaction Module** – Provides human-robot interaction interfaces supporting speech, expressions, and more

- Speech recognition and synthesis
- Expression control
- Multimedia playback

🔧 **Fault and System Management (To be released)** – Provides system monitoring, fault diagnostics, and permission management

- Fault detection and diagnostics
- System permission management
- System status monitoring

**Module interfaces**

- [5.1 Control Module](control_mod/index.html)
  - [5.1.1 Motion Mode Switching](control_mod/modeswitch.html)
  - [5.1.2 Locomotion Control](control_mod/locomotion.html)
  - [5.1.3 MC Control Signal Configuration](control_mod/MC_control.html)
  - [5.1.4 Preset Motion Control](control_mod/preset_motion.html)
  - [5.1.5 End Effector Control](control_mod/endeffector.html)
  - [5.1.6 Joint Control](control_mod/joint_control.html)
- [5.2 Interaction Module](interactor/index.html)
  - [5.2.1 Voice Control](interactor/voice.html)
  - [5.2.2 Screen Control](interactor/screen.html)
  - [5.2.3 LED Strip Control](interactor/lights.html)
- [5.3 Fault & System Management Module (Coming Soon)](FASM/index.html)
  - [5.3.1 Fault Handling (Coming Soon)](FASM/fault.html)
  - [5.3.2 Permission Management (Coming Soon)](FASM/sudo.html)
- [5.4 Hardware Abstraction Module](hal/index.html)
  - [5.4.1 Sensor Interfaces](hal/sensor.html)
  - [5.4.2 Power Management Unit (PMU)](hal/pmu.html)
- [5.5 Perception Module (Coming Soon)](perception/index.html)
  - [5.5.1 Vision (Coming Soon)](perception/vision.html)
  - [5.5.2 SLAM (Coming Soon)](perception/SLAM.html)
