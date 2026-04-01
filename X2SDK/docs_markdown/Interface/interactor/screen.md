# 5.2.2 Screen Control

**The screen control interface provides full display control capabilities, including emoji playback, video playback, and more. It enables developers to implement rich visual interaction features for the robot.**

## Key Features

- Playback of multiple preset emoji expressions
- Custom video playback
- Playlists (coming soon) and loop playback
- Playback priority control

## Emoji Playback Status Topic

| Topic Name | Data Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/face_ui_proxy/status` | `FaceEmojiStatus` | Emoji playback status | `RELIABLE` | 1Hz |

- `FaceEmojiStatus` ros2-msg @ face\_ui/FaceEmojiStatus.msg

  ```
  # Emoji Status Info

  MessageHeader header             # Message header
  string e_path                    # Path of the emoji file
  string[] e_path_list             # List of emoji paths in the current sequence
  uint8 e_id                       # Emoji ID
  uint8 mode                       # Playback mode (1: once, 2: loop)
  int32 priority                   # Priority
  uint8 status                     # Current status (0: idle, 1: start, 2: running, 3: completed, 4: stopped)
  float64 time_to_end_ms           # Remaining time (seconds)
  ```

  `status` special notes:

  - The following states are edge-triggered (reported only once):

    - 1 - start, 3 - completed, 4 - stopped

## Emoji Playback Service

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/PlayEmoji` | `PlayEmoji` | Play emoji |

- `PlayEmoji` ros2-srv @ face\_ui/srv/PlayEmoji.srv

  ```
  # Play Emoji
  # Service: /aimdk_5Fmsgs/srv/PlayEmoji

  # Request
  CommonRequest header  # Request header

  uint8 emotion_id  # Emoji ID
  uint8 mode  # Playback mode (1: once, 2: loop)
  int32 priority  # Playback priority

  ---

  # Response
  CommonResponse header  # Response header

  bool success  # Whether the command succeeded
  string message
  ```

  `emotion_id` Emoji Mapping Table:

  | Emoji ID | Emoji name | Description |
  | --- | --- | --- |
  | 1 | Blink | Basic blink action |
  | 10 | Calm - eye variation 1 | Eye variation for calm state |
  | 11 | Calm - eye variation 2 | Eye variation for calm state |
  | 20 | Calm - game | Game-state emoji |
  | 30-33 | Calm - cute | Cute expression series |
  | 40 | Close eyes | Close-eye action |
  | 50 | Open eyes | Open-eye action |
  | 60 | Bored | Bored expression |
  | 70 | Abnormal | Abnormal state |
  | 80 | Sleeping | Sleeping state |
  | 90 | Happy | Happy expression |
  | 100-101 | Extra happy / ecstatic | Extremely happy expression |
  | 110 | Sad | Sad expression |
  | 120 | Sympathy | Sympathetic expression |
  | 130 | Confused | Confused expression |
  | 140 | Shocked | Shocked expression |
  | 150 | Acting cute | Cute/affectionate expression |
  | 160 | Serious | Serious expression |
  | 170 | Thinking | Thinking expression |
  | 180 | Angry | Angry expression |
  | 190 | Extra angry | Extremely angry expression |
  | 200 | Adoration | Adoring expression |
  | 210 | Extra adoring | Extremely adoring expression |
  | 220 | Charging | Charging state |

  `priority` Priority Mechanism Explanation:

  - This priority mechanism applies to emoji playback (PlayEmoji) and video playback (PlayVideo).
  - If the new request’s priority is not lower than the current one, it overrides the current request.
  - If the new request’s priority is lower, it is ignored.

## Video Playback Service

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/PlayVideo` | `PlayVideo` | Play video |
| `/aimdk_5Fmsgs/srv/PlayVideoGroup` | `PlayVideoGroup` | Play a list of videos |

- `PlayVideo` ros2-srv @ face\_ui/srv/PlayVideo.srv

  ```
  # Play Video
  # Service: /aimdk_5Fmsgs/srv/PlayVideo

  # Request
  CommonRequest header             # Request header
  string video_path                # Absolute path of video file (must be on the interaction compute unit and readable by all)
  uint8 mode                       # Playback mode (1: once, 2: loop)
  int32 priority                   # Playback priority

  # Response
  CommonResponse header            # Response header
  bool success                     # Whether playback succeeded
  string message                   # Response message
  ```

  **Notes:**

  - By default, video playback does not include audio.
  - Audio and video files must use absolute paths.
  - Audio and video files must be stored on the interaction compute unit (PC3, 10.0.1.42), not the development compute unit (PC2).
  - Audio and video files (and all parent directories up to root) must be readable by all users(new subdirectory under /var/tmp/ is recommended)
- `PlayVideoGroup` ros2-srv @ face\_ui/srv/PlayVideoGroup.srv

  ```
  # Play Video
  # Service: /aimdk_5Fmsgs/srv/PlayVideoGroup

  # Request
  CommonRequest header             # Request header
  string[] video_path_list         # List of absolute path of video files (must be on the interaction compute unit and readable by all)
  uint8 mode                       # Playback mode (1: once, 2: loop)
  int32 priority                   # Playback priority

  # Response
  CommonResponse header            # Response header
  bool success                     # Whether playback succeeded
  string message                   # Response message
  ```

  **Notes:**

  - see notes of PlayVideo [>>](screen.html#playvideo-notes)

## Programming Examples

For detailed code examples and explanations, refer to:

- **C++ Examples**:

  - [Emoji Control](../../example/Cpp.html#cpp-play-emoji)
  - [Play Video](../../example/Cpp.html#cpp-play-video)
- **Python Examples**:

  - [Emoji (expression) control](../../example/Python.html#py-play-emoji)
  - [Play video](../../example/Python.html#py-play-video)

## Safety Notes

Warning

**Display Control Limitations**

- Emoji playback occupies display resources; manage resources carefully.
- Video playback requires correct and accessible file paths.
- Set priorities properly to avoid conflicts.

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

Note

**Best Practices**

- Use appropriate playback modes to avoid unnecessary looping.
- Monitor display states and handle exceptions.
- Implement content queueing for better control.
- Ensure correct file paths and formats.
