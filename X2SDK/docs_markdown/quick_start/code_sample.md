# 4.6 Code Implementation

**In this section, you will develop a simple robot control program that makes robot X2 perform a sequence of hand motions and speech playback.**

## 4.6.1 Project Overview

In this project, we will develop a Python program that uses ROS 2 interfaces to control robot X2 to perform the following action sequence:

1. Execute the first action (wave)
2. Speech playback
3. Execute the second action (handshake)

**Prerequisite**: As in the previous section, the robot must be in the Stable Standing Mode.

This project will help you understand how to use the SDK to control the robot’s hand motion sequence and interaction features, laying the groundwork for more complex tasks.

## 4.6.2 Add the Example to the Existing SDK Workspace

We will add a new example program to the existing SDK workspace, which allows you to:

- Reuse the existing build system
- Keep code organization consistent
- Simplify the build and run workflow

### Understand the Existing Structure

The SDK workspace has the following structure:

```
aimdk/
├── src/
│   ├── examples/          # C++ examples
│   │   ├── src/
│   │   │   ├── hal/       # Hardware Abstraction Layer examples
│   │   │   ├── mc/        # Motion control examples
│   │   │   └── interaction/ # Interaction feature examples
│   │   └── CMakeLists.txt
│   └── py_examples/       # Python examples
│       ├── py_examples/
│       └── setup.py
```

Caution

Notes about non-volatile user data:

- The disks in the robot would be reformated during firmware upgrade/downgrade, please backup you data
- User data under `$HOME`(/agibot/data/home/agi) would suervive in general
- Exception 1: DO NOT save data into `$HOME/aimdk*`, which are preserved and maintained by the system
- BE CAREFUL of features like factory reset, which would force erase all user data (include `$HOME`)

### Add a New Python Example

We will add a new example program under the `py_examples` directory:

```
# Go to the SDK directory
# Replace the path below with your actual extracted path
cd /path/to/aimdk

# Create a new example file under py_examples
touch src/py_examples/py_examples/action_sequence_demo.py
```

## 4.6.3 Write the Control Code

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

### Create the Robot Control Class

In `src/py_examples/py_examples/action_sequence_demo.py`, add the following code:

```
#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import time

from aimdk_msgs.srv import SetMcPresetMotion, PlayTts
from aimdk_msgs.msg import (
    RequestHeader, McPresetMotion, McControlArea, CommonState,
    TtsPriorityLevel
)

class ActionSequenceDemo(Node):
    def __init__(self):
        super().__init__('action_sequence_demo')

        # Create service clients
        self.set_preset_motion_client = self.create_client(
            SetMcPresetMotion, '/aimdk_5Fmsgs/srv/SetMcPresetMotion')
        self.play_tts_client = self.create_client(
            PlayTts, '/aimdk_5Fmsgs/srv/PlayTts')

        self.get_logger().info('Action Sequence Demo created')

        # Wait for services to become available
        while not self.set_preset_motion_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for preset motion service...')
        while not self.play_tts_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for TTS service...')

    def perform_preset_motion(self, area_id, motion_id):
        """Execute a preset motion"""
        request = SetMcPresetMotion.Request()
        request.header = RequestHeader()
        request.header.stamp = self.get_clock().now().to_msg()

        motion = McPresetMotion()
        motion.value = motion_id
        area = McControlArea()
        area.value = area_id

        request.motion = motion
        request.area = area
        request.interrupt = False

        self.get_logger().info(f'Executing preset motion: area={area_id}, motion={motion_id}')
        future = self.set_preset_motion_client.call_async(request)
        rclpy.spin_until_future_complete(self, future)

        if future.result() is not None:
            response = future.result()
            if response.response.header.code == 0:
                self.get_logger().info('Preset motion executed successfully')
                return True
            else:
                self.get_logger().error('Preset motion execution failed')
                return False
        else:
            self.get_logger().error('Failed to call preset motion service')
            return False

    def speak(self, text):
        """Trigger TTS speech output"""
        if not self.play_tts_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('TTS service unavailable')
            return False

        request = PlayTts.Request()
        request.header.header.stamp = self.get_clock().now().to_msg()

        # Configure TTS request
        request.tts_req.text = text
        request.tts_req.domain = 'action_sequence_demo'  # Caller identifier
        request.tts_req.trace_id = 'sequence'            # Request ID
        request.tts_req.is_interrupted = True            # Allow interrupting same-priority speech
        request.tts_req.priority_weight = 0
        request.tts_req.priority_level = TtsPriorityLevel()
        request.tts_req.priority_level.value = 6         # Priority level

        self.get_logger().info(f'TTS speak: {text}')
        future = self.play_tts_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=10.0)

        if future.result() is not None:
            response = future.result()
            if response.tts_resp.is_success:
                self.get_logger().info('Speech playback succeeded')
                return True
            else:
                self.get_logger().error('Speech playback failed')
                return False
        else:
            self.get_logger().error('Failed to call TTS service')
            return False

    def wave_hand(self):
        """Control robot to wave hand"""
        # Use preset motion: right-hand wave (area=2, motion=1002)
        return self.perform_preset_motion(2, 1002)

    def shake_hand(self):
        """Control robot to perform handshake"""
        # Use preset motion: right-hand handshake (area=2, motion=1003)
        return self.perform_preset_motion(2, 1003)

    def perform_action_sequence(self):
        """Execute the complete action sequence"""
        self.get_logger().info('Starting action sequence...')
        self.get_logger().info('Prerequisite: robot must be standing')

        # 1. First action: Wave hand
        if not self.wave_hand():
            self.get_logger().error('Wave hand failed')
            return False
        time.sleep(5)

        # 2. TTS speech
        if not self.speak('Hello! I am AgiBot X2. Now demonstrating a hand action sequence!'):
            self.get_logger().error('TTS failed')
            return False
        time.sleep(3)

        # 3. Second action: Handshake
        if not self.shake_hand():
            self.get_logger().error('Handshake failed')
            return False
        time.sleep(3)

        self.get_logger().info('Action sequence completed')
        return True
```

### Add the Main Entry Point

In the same file, add the main entry point:

```
def main(args=None):
    rclpy.init(args=args)
    demo = ActionSequenceDemo()

    # Execute the action sequence
    demo.perform_action_sequence()

    # Shut down the ROS node
    demo.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
```

### Register in the Build System

To run the new example with the `ros2 run` command, you need to add an entry point in `setup.py`:

```
# In src/py_examples/setup.py, add this to entry_points:
"action_sequence_demo = py_examples.action_sequence_demo:main",
```

The complete `entry_points` section should include:

```
entry_points={
    "console_scripts": [
        # ... existing entries ...
        "action_sequence_demo = py_examples.action_sequence_demo:main",
    ],
},
```

## 4.6.4 Build and Run

### Build the Project

```
# Go to the SDK directory
# Replace the path below with your actual extracted path
cd /path/to/aimdk

# Set environment variables
source /opt/ros/humble/setup.bash

# Build the project
colcon build --packages-select py_examples
```

### Run the Project

```
# Set environment variables
source install/local_setup.bash

# Run the new example program
ros2 run py_examples action_sequence_demo
```

## 4.6.5 Code Walkthrough

### Robot Control Class

The `ActionSequenceDemo` class is the core of robot control and provides the following capabilities:

- **Initialize ROS node and service clients**: The constructor creates the ROS node and the required service clients.
- **Execute preset motions**: The `perform_preset_motion` method is used to execute predefined motions.
- **Speech playback**: The `speak` method triggers TTS-based speech playback.
- **Control robot actions**: Methods such as `wave_hand` and `shake_hand` are provided to control the robot’s hand motions.
- **Execute the action sequence**: The `perform_action_sequence` method runs the sequence wave → speak → handshake in order.

## 4.6.6 Extensions and Optimization

### Add More Actions and Interactions

You can extend the existing code to add more robot actions and interaction features, for example:

- Blow a kiss (preset motion ID: 1004)
- Salute (preset motion ID: 1013)
- Heart gesture (preset motion ID: 1007)
- Raise hand (preset motion ID: 1001)
- Additional speech content
- Expression control
- And so on

### Add Parameter Configuration

You can use the ROS 2 parameter system to make action parameters configurable:

```
# Declare parameters in the constructor
self.declare_parameter('wave_count', 3)
self.declare_parameter('wait_duration', 3.0)

# Use parameters in your methods
wait_duration = self.get_parameter('wait_duration').value
time.sleep(wait_duration)
```

### Add Error Handling

You can refer to the example [Get robot mode](../example/Python.html#py-get-mc-action) to add more error-handling logic and make the program more robust:

```
    def send_request(self):
        request = GetMcAction.Request()
        request.request = CommonRequest()

        self.get_logger().info('📨 Sending request to get robot mode')
        for i in range(8):
            request.request.header.stamp = self.get_clock().now().to_msg()
            future = self.client.call_async(request)
            rclpy.spin_until_future_complete(self, future, timeout_sec=0.25)

            if future.done():
                break

            # retry as remote peer is NOT handled well by ROS
            self.get_logger().info(f'trying ... [{i}]')

        response = future.result()
        if response is None:
            self.get_logger().error('❌ Service call failed or timed out.')
            return

        self.get_logger().info('✅ Robot mode get successfully.')
        self.get_logger().info(f'Mode name: {response.info.action_desc}')
        self.get_logger().info(f'Mode status: {response.info.status.value}')
```

### Add More Interaction Features

You can integrate additional interaction features:

```
# Add an expression service client
from aimdk_msgs.srv import PlayEmoji

# Add expressions in the action sequence
def show_expression(self, emoji_id):
    # Implement expression control here
    pass

# Add multiple speech messages
def speak_multiple_messages(self, messages):
    for message in messages:
        self.speak(message)
        time.sleep(1)
```

## 4.6.7 Troubleshooting

First, check the  [FAQ](../faq/index.html#faq) section. If the issue is still not resolved, consider contacting AgiBot X2 technical support.

## 4.6.8 Next Steps

After completing this section, you can:

1. **Explore more examples**: Review other example programs under `src/py_examples/py_examples/` or `src/examples/src/`.
2. **Integrate perception features**: Learn how to access and process sensor data.
3. **Develop more complex tasks**: Combine multiple functional modules to build more complex robot applications.

## 4.6.9 Summary

By now, you have learned how to:

- ✅ Add a new example program to an existing SDK workspace
- ✅ Execute a preset motion sequence
- ✅ Implement TTS speech playback
- ✅ Build and run a custom example program
- ✅ Control a sequence of hand motions for the robot: wave → speak → handshake

Congratulations! You have now mastered the basic development skills for the AgiBot X2 AimDK, including motion control, speech interaction, and action-sequence orchestration, and you are ready to start building your own robot applications!
