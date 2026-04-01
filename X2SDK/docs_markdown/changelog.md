# Changelog

| Version | Date | Update Summary |
| --- | --- | --- |
| v0.9.0 (Beta 2.0) | 2026.02.03 | Migration of some interfaces needed Example tuning and documentation updates [[Details>>]](changelog.html#changelog-v0-9-0) |
| v0.8.2 (Beta 1.2) | 2025.12.10 | **Motion Control Unit (PC1) is prohibited for secondary development** Migration of ‘SetMcAction/GetMcAction’ interfaces needed Example tuning and documentation updates URDF available online The pitch axis of head is locked [[Details>>]](changelog.html#changelog-v0-8-2) |
| v0.8.1 (Beta 1.1) | 2025.11.11 | Example tuning and documentation updates Light strip control enabled, online SDK documentation added Interaction camera and playlist features removed [[Details>>]](changelog.html#changelog-v0-8-1) |
| v0.8.0 (Beta 1.0) | 2025.11.06 | Changes in some data definitions and topics Joint motor control, power monitoring, and head touch sensor enabled Posture control removed [[Details>>]](changelog.html#changelog-v0-8-0) |
| v0.7.x (Alpha) | - | Will soon be discontinued |

---

## Changelog v0.9.0

### Newly Released Features

- User data in [specified path would survive](get_sdk/index.html) firmware upgrade/downgrade (**others still get erased**)
- Added sensor info of X2

### Adjustments to Existing Features

- Changes on handling some interfaces

  - Added field `source` in SetMcAction
  - Added field `DomainErrorState state` in JointStateArray
  - Added new layer `SYSTEM_L7` for TtsPriorityLevel
  - `/aimdk_5Fmsgs/srv/PlayVideoGroup` available
  - Wake words required for VAD (`/agent/process_audio_output`)
- Example updates

  - The omnihand\_control examples available
  - Added examples for head touch sensor
  - Updated joint info in motocontrol examples

### Deprecated / Removed Features

## Changelog v0.8.2

### Newly Released Features

- URDF available online

### Adjustments to Existing Features

- Taking Motion Control Computing Unit(PC1, 10.0.1.40) as build & run environment for secondary development is strictly prohibited to avoid safety risks
- Changes on handling some interfaces

  - The numeric ID (`McAction`) is abandoned in `SetMcAction`/`GetMcAction`, instead string field `action_desc` applied to pass motion mode
- Example updates

  - Improved handling of shutdown and interrupts
- Documentation enhancements

  - Added notes on validating trigger-speed thresholds for locomotion after switching the firmware
  - Added notes on following examples (applying protection mechanisms e.g. exception safety and retansmission) to keep away from ROS bugs (esp. on cross-host request/response service)
  - Added notes on file location and access permission for audio/video files used in interaction interfaces

### Deprecated / Removed Features

- The pitch axis of head is locked

## Changelog v0.8.1

### Newly Released Features

- Online SDK Documentation: <https://x2-aimdk.agibot.com>
- Interaction – LED Strip Control Service: RGB color control and dynamic/mode control for the chest LED light strip

  - `/aimdk_5Fmsgs/srv/LedStripCommand`

### Adjustments to Existing Features

- Example updates

  - Improved communication workflow in motion-control examples
  - Camera-related examples enhanced for better compatibility with the robot’s internal system environment
- Documentation enhancements

  - Added explanations for interface frequency, QoS, and bandwidth considerations
  - Added explanation of directional trigger-speed thresholds for locomotion control and reference values
  - Clarified that MC control must be disabled before hand-control operations
  - Additional refinements including path descriptions and terminology unification

### Deprecated / Removed Features

- All interaction-camera interfaces removed: high resource usage made them unsuitable for secondary development; functionalities can be replaced by other cameras. Affected topics/services:

  - `/aima/hal/sensor/rgb_head_front_center/camera_info`
  - `/aima/hal/sensor/rgb_head_front_center/rgb_image`
  - `/aima/hal/sensor/rgb_head_front_center/rgb_image/compressed`
- Head IMU: hardware changes; now replaced by the depth camera IMU. Affected topics/services:

  - `/aima/hal/imu/head/state`
- Playlist functionality temporarily removed for stability improvements. Affected topics/services:

  - `/aimdk_5Fmsgs/srv/PlayEmojiGroup`
  - `/aimdk_5Fmsgs/srv/PlayVideoGroup`

---

## Changelog v0.8.0

### Newly Released Features

- Added low-level joint motor control interfaces (supports control and state queries for arms, waist, and legs)
- Added power-status monitoring interface (battery BMS, 48V/12V output status, fault detection: undervoltage, overcurrent, overheating, short circuit, etc.)
- Added head-touch sensor subscription interface
- Added system volume adjustment interface
- Opened IMU data streams (head / chest / pelvis)

### Adjustments to Existing Features

- Preset motion expansion and ID mapping updates
- RGB-D Camera

  - Released intrinsic camera-info topics for depth and RGB images
- Emoji playback upgraded:

  - ROS service-based playback mode officially supported
  - Added emoji status subscription (FaceEmojiStatus.msg)

### Deprecated / Removed Features

- Robot posture control (McBodyPose.msg)
- Available-action query service (GetMcAvailableActions.srv)

### Other Updates

- Topic updates

  - Depth-camera depth-image intrinsics – `/aima/hal/sensor/rgbd_head_front/depth_camera_info`
  - Depth-camera RGB-image intrinsics – `/aima/hal/sensor/rgbd_head_front/rgb_camera_info`
  - Emoji playback – `/aimdk_5Fmsgs/srv/PlayEmoji`
  - Video playback – `/aimdk_5Fmsgs/srv/PlayVideo`
- Message definition updates

  - MC multi-input-source management

    1. Updated SetMcInputSource.srv (introduced intermediate McInputSource.msg wrapper)
    2. Updated GetCurrentInputSource.srv (same modification)
  - Text-to-Speech

    1. Updated PlayTts.srv (`tty_xx` → `tts_xx`)
    2. Updated TtsResponse (renamed `is_success` field)
  - Audio playback

    1. Updated PlayMediaFile.srv (renamed request/response headers; `tty_resp` → `tts_resp`)
  - Emoji playback

    1. Updated PlayEmoji.srv (`priority`: uint8 → int32)
  - Video playback

    1. Updated PlayVideo.srv (`priority`: uint8 → int32)
