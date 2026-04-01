# 5.2.1 Voice Control

**The voice control interface provides a complete set of voice interaction capabilities, including speech synthesis, speech recognition, audio noise reduction, audio playback, and volume control.**

## Key Features

### Text-to-Speech (TTS)

- **Text-to-speech**: Convert text into natural-sounding speech.
- **Multi-language support**: Supports Chinese, English, and other languages.
- **Emotional speech**: Supports different emotional styles for synthesis.
- **Priority management**: Supports multi-level priority control.

### Automatic Speech Recognition (ASR) (coming soon)

- **Real-time recognition**: Supports real-time speech recognition.
- **Multi-language recognition**: Supports Chinese, English, and other languages.
- **Audio stream processing**: Supports real-time processing of audio streams.

### Audio Processing

- **Real-time noise reduction**: Supports real-time audio denoising.
- **Voice activity detection**: Supports VAD (Voice Activity Detection).
- **Streaming**: Supports streaming of denoised audio.

### Audio Playback

- **Audio stream playback**: Supports playback of audio data streams.
- **Priority control**: Supports playback priority management.
- **Format support**: Supports multiple audio formats.

### Volume Control

- **Volume adjustment**: Supports system volume adjustment.
- **Mute control**: Supports mute / unmute.
- **Volume query**: Supports querying the current volume.

## Volume Control Services

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/GetVolume` | [`GetVolume`](voice.html#def-rossrv-getvolume) | Query volume |
| `/aimdk_5Fmsgs/srv/SetVolume` | [`SetVolume`](voice.html#def-rossrv-setvolume) | Set volume |
| `/aimdk_5Fmsgs/srv/GetMute` | [`GetMute`](voice.html#def-rossrv-getmute) | Query mute status |
| `/aimdk_5Fmsgs/srv/SetMute` | [`SetMute`](voice.html#def-rossrv-setmute) | Set mute |

- `GetVolume` ros2-srv @ /hal/audio/srv/GetVolume.srv

  ```
  # Get Volume
  # Service: /aimdk_5Fmsgs/srv/GetVolume

  # Request
  CommonRequest request            # Request header

  ---

  # Response
  CommonResponse reponse           # Response header
  uint32 audio_volume              # Current volume (0–100)
  ```

- `SetVolume` ros2-srv @ /hal/audio/srv/SetVolume.srv

  ```
  # Set Volume
  # Service: /aimdk_5Fmsgs/srv/SetVolume

  # Request
  CommonRequest request            # Request header
  uint32 audio_volume              # Target volume (0–100)

  ---

  # Response
  CommonResponse reponse           # Response header
  uint32 audio_volume              # Current volume (0–100)
  ```

- `GetMute` ros2-srv @ /hal/audio/srv/GetMute.srv

  ```
  # Get Mute Status
  # Service: /aimdk_5Fmsgs/srv/GetMute

  # Request
  CommonRequest request            # Request header

  ---

  # Response
  CommonResponse reponse           # Response header
  bool is_mute                     # Current mute state
  ```

- `SetMute` ros2-srv @ /hal/audio/srv/SetMute.srv

  ```
  # Set Mute
  # Service: /aimdk_5Fmsgs/srv/SetMute

  # Request
  CommonRequest request            # Request header
  bool is_mute                     # Target mute state

  ---

  # Response
  CommonResponse reponse           # Response header
  bool is_mute                     # Current mute state
  ```

## Speech Synthesis Services

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/PlayTts` | `PlayTts` | Text-to-speech playback |

- `PlayTts` ros2-srv @ interaction/srv/PlayTts.srv

  ```
  # TTS Playback
  # Service: /aimdk_5Fmsgs/srv/PlayTts

  # Request
  CommonRequest header
  PlayTtsRequest tts_req  # Embedded request msg

  ---

  # Response
  CommonResponse header
  PlayTtsResponse tts_resp  # Embedded response msg
  ```

  Where

  - `PlayTtsRequest` ros2-msg @ interaction/msg/PlayTtsRequest.msg

    ```
    # Embedded request msg

    string text                      # Text content
    TtsPriorityLevel priority_level  # Priority level (see TtsPriorityLevel below)
    uint32 priority_weight           # Priority weight (0–99)
    string domain                    # Caller domain
    string trace_id                  # Request trace ID
    bool is_interrupted              # Whether to interrupt broadcasts of the same priority (otherwise queued)
    ```

    - `TtsPriorityLevel` ros2-msg @ interaction/msg/TtsPriorityLevel.msg

      ```
      # TTS priority level
      uint8 value                      # Priority value
      ```

      Available `TtsPriorityLevel` values:

      | Level | Value | Description | Usage scenarios |
      | --- | --- | --- | --- |
      | Emergency safety layer (SAFETY\_L10) | 10 | Highest priority | Safety alerts, emergency notifications |
      | Warning layer (WARNING\_L8) | 8 | High priority | Hazard alerts and warning messages |
      | System notice layer (SYSTEM\_L7) | 7 | Medium-high priority | System-level Notice |
      | Interaction response layer (INTERACTION\_L6) | 6 | Medium priority | User interaction and conversational responses |
      | Mission execution layer (MISSION\_L4) | 4 | Medium-low priority | Task execution and status broadcasts |
      | Service layer (SERVICE\_L2) | 2 | Low priority | Proactive services and reminders |
      | Background service layer (BACKGROUND\_L1) | 1 | Lowest priority | Background services and logging |

      Audio playback priority mechanism:

      - This priority system applies to both TTS playback (PlayTts) and audio file playback (PlayMediaFile).
      - Higher priority playback interrupts lower priority playback.
      - For the same priority level, behavior is determined by `priority_weight` and `is_interrupted`.
      - The playback queue would be reset when interrupted
      - The emergency safety level has the highest priority and cannot be interrupted by any other level.
  - `PlayTtsResponse` ros2-msg @ interaction/msg/PlayTtsResponse.msg

    ```
    # Embedded response msg
    string text                      # Response text
    TtsPriorityLevel priority_level  # Priority level
    uint32 priority_weight           # Priority weight
    string domain                    # Caller domain
    string trace_id                  # Request trace ID
    bool is_success                  # Whether the request succeeded
    string error_message             # Error message
    uint32 estimated_duration        # Estimated duration (ms)
    ```

## Audio File Playback Service

| Service Name | Data Type | Description |
| --- | --- | --- |
| `/aimdk_5Fmsgs/srv/PlayMediaFile` | `PlayMediaFile` | Play audio file |

- `PlayMediaFile` ros2-srv @ interaction/srv/PlayMediaFile.srv

  ```
  # Play audio file
  # Service: /aimdk_5Fmsgs/srv/PlayMediaFile

  # Request
  CommonRequest header
  PlayMediaFileRequest media_file_req

  ---

  # Response
  CommonResponse header
  PlayTtsResponse tts_resp  # Reuses PlayTtsResponse
  ```

  - `PlayMediaFileRequest` ros2-msg @ interaction/msg/PlayMediaFileRequest.msg

    ```
    # Embedded request msg

    string file_name  # Absolute path to the audio file (must be on the interaction compute unit and readable by all)
    uint32 sample_rate  # Currently unused, default 16k1ch
    TtsPriorityLevel priority_level  # Recommended default: INTERACTION_L6
    uint32 priority_weight  # Weight (0–99)
    string domain  # Caller domain
    string trace_id  # Request trace ID
    bool is_interrupted # Whether to interrupt broadcasts of the same priority (otherwise queued)
    ```

    For `priority_level` values, see the [audio priority table](voice.html#tbl-tts-prioritylevel).
  - `PlayTtsResponse` as described [above](voice.html#def-rosmsg-playttsresponse).

  Notes:

  - Audio files must be PCM-encoded raw files (.pcm) or WAV files wrapping this PCM data (.wav).
  - Audio must be 16 kHz sample rate, 16-bit, mono.
  - Audio and video files must use absolute paths.
  - Audio and video files must be stored on the interaction compute unit (PC3, 10.0.1.42), not the development compute unit (PC2).
  - Audio and video files (and all parent directories up to root) must be readable by all users(new subdirectory under /var/tmp/ is recommended)

## MIC Audio Stream Capture Topic

Supports receiving VAD (Voice Activity Detection) events on denoised audio and the corresponding audio stream.

| Topic Name | Data Type | Description | QoS | Frequency |
| --- | --- | --- | --- | --- |
| `/agent/process_audio_output` | `ProcessedAudioOutput` | VAD audio capture | - | Event-triggered, cached data for voice recognition would be sent in a burst at start of VAD event, then would update at ~25Hz |

- `ProcessedAudioOutput` ros2-msg @ interaction/msg/ProcessedAudioOutput.msg

  ```
  MessageHeader header  # Message header

  uint32 stream_id  # Audio stream ID (1: onboard mic, 2: external mic)
  AudioVadStateType audio_vad_state  # VAD state (0: no speech, 1: speech start, 2: in speech, 3: speech end)
  uint8[] audio_data  # Audio data (PCM, 16 kHz / 16 bit / 1 ch)
  ```

**Audio stream format:**

- Sample rate: 16 kHz
- Bit depth: 16 bit
- Channels: mono
- Encoding: PCM

Attention

The wake word required to activate VAD (since v0.9):

- In default mode (built-in interaction ON), always say the wake word before target voice, as VAD only keep activated for a short while.
- In [`only_voice` mode](../../faq/temp_works.html#agent-only-voice) (build-in interaction disabled), VAD keep activated for long once waked by the wake word. No more wake words needed later, all voice detected later on would be captured as VAD streams

## Programming Examples

For detailed programming examples and code descriptions, see:

- **C++ Examples**:

  - [TTS (Text-to-Speech)](../../example/Cpp.html#cpp-play-tts)
  - [Media File Playback](../../example/Cpp.html#cpp-play-media)
  - [Microphone Audio Reception](../../example/Cpp.html#cpp-mic-receiver)
- **Python Examples**:

  - [TTS (Text-to-Speech)](../../example/Cpp.html#cpp-play-tts)
  - [Media File Playback](../../example/Cpp.html#cpp-play-media)
  - [Microphone Audio Reception](../../example/Cpp.html#cpp-mic-receiver)

## Safety Notes

Warning

**Voice playback limitations**

- The TTS service uses a priority system; avoid starting multiple speech playbacks at the same time.
- Higher-priority speech will interrupt lower-priority speech; configure priorities carefully.
- Check the current playback state before starting new speech.

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

Note

**Best Practices**

- Choose appropriate priority levels to avoid interfering with important announcements.
- Implement monitoring and exception handling for speech playback.
- Implement a playback queue for speech management.
- Pay attention to the required audio format and sample rate.
- The receive queue (QoS depth) of VAD should be large enough
- Never forget wake words when using VAD
