# 5.2 Interaction Module

**AgiBot X2 AimDK Interaction Module – providing rich human–robot interaction interfaces**

**Core Features**

- **Voice Interaction**: speech recognition, text-to-speech, and voice command handling
- **Expression Control**: rich facial expressions and emotion display
- **Multimedia Playback**: video, audio, and image playback
- **Haptic Feedback**: tactile sensors and feedback control

**Interface Specifications**

- **Service Interfaces**: most use the `/aimdk_5Fmsgs/srv/` and `/face_ui_proxy/` prefixes
- **Message Types**: defined in the `aimdk_msgs` package
- **Language Support**: C++ and Python
- **Message Format**: standard ROS 2 message formats

**Version Compatibility**

- **Current Version**: v0.8
- **Minimum Version**: v0.6 (partial feature support)
- **ROS 2 Distribution**: Humble
- **Supported Architectures**: x86\_64, aarch64

**Safety Notes**

Warning

**Important Safety Reminders**

- The TTS service is priority-based; avoid playing multiple voices at the same time.
- Expression playback consumes display resources; manage system resources carefully.
- For multimedia playback, ensure file paths are correct and accessible.

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

**Feature Modules**

- [5.2.1 Voice Control](voice.html)
- [5.2.2 Screen Control](screen.html)
- [5.2.3 LED Strip Control](lights.html)
