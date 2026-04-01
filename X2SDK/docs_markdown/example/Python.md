# 6.1 Python interface usage example

**This chapter will guide you through implementing several features shown in the index**

**Build & Run Instructions**

- Change into the `aimdk` directory and run the following commands

  ```
  source /opt/ros/humble/setup.bash
  colcon build
  source install/setup.bash
  ros2 run py_examples '<corresponding feature name e.g.: get_mc_action>'
  ```

> **📝 Code explanation**
>
> The complete code implementation includes full error handling, signal handling, timeout handling, and other mechanisms to ensure program robustness. **Please view or modify the code in the py\_examples directory**

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

## 6.1.1 Get robot mode

Retrieve the robot’s current operating mode by calling the `GetMcAction` service, including the description, and status information.

[Motion Mode Definitions](../Interface/control_mod/modeswitch.html#tbl-mc-action)

```
 1#!/usr/bin/env python3
 2
 3import rclpy
 4import rclpy.logging
 5from rclpy.node import Node
 6
 7from aimdk_msgs.srv import GetMcAction
 8from aimdk_msgs.msg import CommonRequest
 9
10
11class GetMcActionClient(Node):
12    def __init__(self):
13        super().__init__('get_mc_action_client')
14        self.client = self.create_client(
15            GetMcAction, '/aimdk_5Fmsgs/srv/GetMcAction')
16        self.get_logger().info('✅ GetMcAction client node created.')
17
18        # Wait for the service to become available
19        while not self.client.wait_for_service(timeout_sec=2.0):
20            self.get_logger().info('⏳ Service unavailable, waiting...')
21
22        self.get_logger().info('🟢 Service available, ready to send request.')
23
24    def send_request(self):
25        request = GetMcAction.Request()
26        request.request = CommonRequest()
27
28        self.get_logger().info('📨 Sending request to get robot mode')
29        for i in range(8):
30            request.request.header.stamp = self.get_clock().now().to_msg()
31            future = self.client.call_async(request)
32            rclpy.spin_until_future_complete(self, future, timeout_sec=0.25)
33
34            if future.done():
35                break
36
37            # retry as remote peer is NOT handled well by ROS
38            self.get_logger().info(f'trying ... [{i}]')
39
40        response = future.result()
41        if response is None:
42            self.get_logger().error('❌ Service call failed or timed out.')
43            return
44
45        self.get_logger().info('✅ Robot mode get successfully.')
46        self.get_logger().info(f'Mode name: {response.info.action_desc}')
47        self.get_logger().info(f'Mode status: {response.info.status.value}')
48
49
50def main(args=None):
51    rclpy.init(args=args)
52    node = None
53    try:
54        node = GetMcActionClient()
55        node.send_request()
56    except KeyboardInterrupt:
57        pass
58    except Exception as e:
59        rclpy.logging.get_logger('main').error(
60            f'Program exited with exception: {e}')
61
62    if node:
63        node.destroy_node()
64    if rclpy.ok():
65        rclpy.shutdown()
66
67
68if __name__ == '__main__':
69    main()
```

## 6.1.2 Set robot mode

**This example uses the SetMcAction service.** After running the node, enter the corresponding field value of the mode in the terminal, and the robot will immediately switch to the appropriate [motion mode](../Interface/control_mod/modeswitch.html#tbl-mc-action).
**Before switching to the Stable Standing mode (`STAND_DEFAULT`), ensure the robot is standing and its feet are already on the ground.**
**The motion mode switching must follow its state transition digram, other transitions would be rejected**
**Locomotion Mode(`LOCOMOTION_DEFAULT`) and Stable Standing Mode(`STAND_DEFAULT`) are unified and will auto switch internally, so switching manually to the nearer one is enough**

```
  1#!/usr/bin/env python3
  2
  3import sys
  4import rclpy
  5import rclpy.logging
  6from rclpy.node import Node
  7
  8from aimdk_msgs.srv import SetMcAction
  9from aimdk_msgs.msg import RequestHeader, CommonState, McAction, McActionCommand
 10
 11
 12class SetMcActionClient(Node):
 13    def __init__(self):
 14        super().__init__('set_mc_action_client')
 15        self.client = self.create_client(
 16            SetMcAction, '/aimdk_5Fmsgs/srv/SetMcAction'
 17        )
 18        self.get_logger().info('✅ SetMcAction client node created.')
 19
 20        # Wait for the service to become available
 21        while not self.client.wait_for_service(timeout_sec=2.0):
 22            self.get_logger().info('⏳ Service unavailable, waiting...')
 23
 24        self.get_logger().info('🟢 Service available, ready to send request.')
 25
 26    def send_request(self, action_name: str):
 27        req = SetMcAction.Request()
 28        req.header = RequestHeader()
 29
 30        cmd = McActionCommand()
 31        cmd.action_desc = action_name
 32        req.command = cmd
 33
 34        self.get_logger().info(
 35            f'📨 Sending request to set robot mode: {action_name}')
 36        for i in range(8):
 37            req.header.stamp = self.get_clock().now().to_msg()
 38            future = self.client.call_async(req)
 39            rclpy.spin_until_future_complete(self, future, timeout_sec=0.25)
 40
 41            if future.done():
 42                break
 43
 44            # retry as remote peer is NOT handled well by ROS
 45            self.get_logger().info(f'trying ... [{i}]')
 46
 47        response = future.result()
 48        if response is None:
 49            self.get_logger().error('❌ Service call failed or timed out.')
 50            return
 51
 52        if response.response.status.value == CommonState.SUCCESS:
 53            self.get_logger().info('✅ Robot mode set successfully.')
 54        else:
 55            self.get_logger().error(
 56                f'❌ Failed to set robot mode: {response.response.message}'
 57            )
 58
 59
 60def main(args=None):
 61    action_info = {
 62        'PASSIVE_DEFAULT': ('PD', 'joints with zero torque'),
 63        'DAMPING_DEFAULT': ('DD', 'joints in damping mode'),
 64        'JOINT_DEFAULT': ('JD', 'Position Control Stand (joints locked)'),
 65        'STAND_DEFAULT': ('SD', 'Stable Stand (auto-balance)'),
 66        'LOCOMOTION_DEFAULT': ('LD', 'locomotion mode (walk or run)'),
 67    }
 68
 69    choices = {}
 70    for k, v in action_info.items():
 71        choices[v[0]] = k
 72
 73    rclpy.init(args=args)
 74    node = None
 75    try:
 76        # Prefer command-line argument, otherwise prompt for input
 77        if len(sys.argv) > 1:
 78            motion = sys.argv[1]
 79        else:
 80            print('{:<4} - {:<20} : {}'.format('abbr',
 81                  'robot mode', 'description'))
 82            for k, v in action_info.items():
 83                print(f'{v[0]:<4} - {k:<20} : {v[1]}')
 84            motion = input('Enter abbr of robot mode:')
 85
 86        action_name = choices.get(motion)
 87        if not action_name:
 88            raise ValueError(f'Invalid abbr of robot mode: {motion}')
 89
 90        node = SetMcActionClient()
 91        node.send_request(action_name)
 92    except KeyboardInterrupt:
 93        pass
 94    except Exception as e:
 95        rclpy.logging.get_logger('main').error(
 96            f'Program exited with exception: {e}')
 97
 98    if node:
 99        node.destroy_node()
100    if rclpy.ok():
101        rclpy.shutdown()
102
103
104if __name__ == '__main__':
105    main()
```

**Usage**

```
# Use command-line arguments to set the mode (recommended)
ros2 run py_examples set_mc_action JD  # Zero-Torque >> Position-Control Standing
ros2 run py_examples set_mc_action SD  # Ensure your robot's feet on the ground, Position-Control Standing >> Stable Standing
# Stable Standing >> Locomotion Mode. auto done internally, don't switch manually

# Or run without arguments and the program will prompt for input
ros2 run py_examples set_mc_action
```

**Example output**

```
...
[INFO] [1764066567.502968540] [set_mc_action_client]: ✅ Robot mode set successfully.
```

**Notes**

- Ensure the robot is standing and its feet are on the ground before switching to `STAND_DEFAULT` mode
- Mode switching may take several seconds to complete

**Interface reference**

- Service: `/aimdk_5Fmsgs/srv/SetMcAction`
- Message: `aimdk_msgs/srv/SetMcAction`

## 6.1.3 Set robot action

**This example uses `preset_motion_client`**; after switching to Stable Stand Mode and starting the node, enter the corresponding field values to perform preset actions with the left (or right) hand such as handshake, raise hand, wave, or air kiss.

Available parameters are listed in the [preset motions table](../Interface/control_mod/preset_motion.html#tbl-preset-motion)

```
 1#!/usr/bin/env python3
 2
 3import rclpy
 4import rclpy.logging
 5from rclpy.node import Node
 6
 7from aimdk_msgs.srv import SetMcPresetMotion
 8from aimdk_msgs.msg import McPresetMotion, McControlArea, RequestHeader, CommonState
 9
10
11class SetMcPresetMotionClient(Node):
12    def __init__(self):
13        super().__init__('preset_motion_client')
14        self.client = self.create_client(
15            SetMcPresetMotion, '/aimdk_5Fmsgs/srv/SetMcPresetMotion')
16        self.get_logger().info('✅ SetMcPresetMotion client node created.')
17
18        # Wait for the service to become available
19        while not self.client.wait_for_service(timeout_sec=2.0):
20            self.get_logger().info('⏳ Service unavailable, waiting...')
21
22        self.get_logger().info('🟢 Service available, ready to send request.')
23
24    def send_request(self, area_id: int, motion_id: int) -> bool:
25        request = SetMcPresetMotion.Request()
26        request.header = RequestHeader()
27
28        motion = McPresetMotion()
29        area = McControlArea()
30
31        motion.value = motion_id
32        area.value = area_id
33
34        request.motion = motion
35        request.area = area
36        request.interrupt = False
37
38        self.get_logger().info(
39            f'📨 Sending request to set preset motion: motion={motion_id}, area={area_id}')
40
41        for i in range(8):
42            request.header.stamp = self.get_clock().now().to_msg()
43            future = self.client.call_async(request)
44            rclpy.spin_until_future_complete(self, future, timeout_sec=0.25)
45
46            if future.done():
47                break
48
49            # retry as remote peer is NOT handled well by ROS
50            self.get_logger().info(f'trying ... [{i}]')
51
52        response = future.result()
53        if response is None:
54            self.get_logger().error('❌ Service call failed or timed out.')
55            return False
56
57        if response.response.header.code == 0:
58            self.get_logger().info(
59                f'✅ Preset motion set successfully: {response.response.task_id}')
60            return True
61        elif response.response.state.value == CommonState.RUNNING:
62            self.get_logger().info(
63                f'⏳ Preset motion executing: {response.response.task_id}')
64            return True
65        else:
66            self.get_logger().error(
67                f'❌ Failed to set preset motion: {response.response.task_id}'
68            )
69            return False
70
71
72def main(args=None):
73    rclpy.init(args=args)
74    node = None
75    try:
76        area = int(input("Enter arm area ID (1-left, 2-right): "))
77        motion = int(input(
78            "Enter preset motion ID (1001-raise，1002-wave，1003-handshake，1004-airkiss): "))
79
80        node = SetMcPresetMotionClient()
81        node.send_request(area, motion)
82    except KeyboardInterrupt:
83        pass
84    except Exception as e:
85        rclpy.logging.get_logger('main').error(
86            f'Program exited with exception: {e}')
87
88    if node:
89        node.destroy_node()
90    if rclpy.ok():
91        rclpy.shutdown()
92
93
94if __name__ == '__main__':
95    main()
```

## 6.1.4 Gripper control

**This example uses `hand_control`. Publish messages to the `/aima/hal/joint/hand/command` topic to control the gripper.**

Attention

***Note ⚠️: Before running this example, stop the native MC module on the robot control unit (PC1) by running `aima em stop-app mc` to obtain control of the robot. Ensure the robot is safe before operating.***

```
 1import rclpy
 2from rclpy.node import Node
 3from aimdk_msgs.msg import HandCommandArray, HandCommand, HandType, MessageHeader
 4import time
 5
 6
 7class HandControl(Node):
 8    def __init__(self):
 9        super().__init__('hand_control')
10
11        # Preset parameter list: [(left hand, right hand), ...]
12        self.position_pairs = [
13            (1.0, 1.0),   # fully open
14            (0.0, 0.0),   # fully closed
15            (0.5, 0.5),   # half open
16            (0.2, 0.8),   # left slightly closed, right more open
17            (0.7, 0.3)    # left more open, right slightly closed
18        ]
19        self.current_index = 0
20        self.last_switch_time = self.get_clock().now().nanoseconds / 1e9  # seconds
21
22        # Create publisher
23        self.publisher_ = self.create_publisher(
24            HandCommandArray,
25            '/aima/hal/joint/hand/command',
26            10
27        )
28
29        # 50 Hz timer
30        self.timer_ = self.create_timer(
31            0.02,  # 20 ms = 50 Hz
32            self.publish_hand_commands
33        )
34
35        self.get_logger().info("Hand control node started!")
36
37    def publish_hand_commands(self):
38        # Check time to decide whether to switch to the next preset
39        now_sec = self.get_clock().now().nanoseconds / 1e9
40        if now_sec - self.last_switch_time >= 2.0:
41            self.current_index = (self.current_index +
42                                  1) % len(self.position_pairs)
43            self.last_switch_time = now_sec
44            self.get_logger().info(
45                f"Switched to preset: {self.current_index}, left={self.position_pairs[self.current_index][0]:.2f}, right={self.position_pairs[self.current_index][1]:.2f}"
46            )
47
48        # Use current preset
49        left_position, right_position = self.position_pairs[self.current_index]
50
51        msg = HandCommandArray()
52        msg.header = MessageHeader()
53
54        # Configure left hand
55        left_hand = HandCommand()
56        left_hand.name = "left_hand"
57        left_hand.position = float(left_position)
58        left_hand.velocity = 1.0
59        left_hand.acceleration = 1.0
60        left_hand.deceleration = 1.0
61        left_hand.effort = 1.0
62
63        # Configure right hand
64        right_hand = HandCommand()
65        right_hand.name = "right_hand"
66        right_hand.position = float(right_position)
67        right_hand.velocity = 1.0
68        right_hand.acceleration = 1.0
69        right_hand.deceleration = 1.0
70        right_hand.effort = 1.0
71
72        msg.left_hand_type = HandType(value=2)  # gripper mode
73        msg.right_hand_type = HandType(value=2)
74        msg.left_hands = [left_hand]
75        msg.right_hands = [right_hand]
76
77        # Publish message
78        self.publisher_.publish(msg)
79        # We only log when switching presets to avoid too much log output
80
81
82def main(args=None):
83    rclpy.init(args=args)
84    hand_control_node = HandControl()
85
86    try:
87        rclpy.spin(hand_control_node)
88    except KeyboardInterrupt:
89        pass
90    finally:
91        hand_control_node.destroy_node()
92        rclpy.shutdown()
93
94
95if __name__ == '__main__':
96    main()
```

## 6.1.5 Dexterous Hand Control

**This example uses `omnihand_control`. Publish messages to the `/aima/hal/joint/hand/command` topic to control the omnihand.**

Attention

***Note ⚠️: Before running this example, stop the native MC module on the robot control unit (PC1) by running `aima em stop-app mc` to obtain control of the robot. Ensure the robot is safe before operating.***

```
  1import rclpy
  2from rclpy.node import Node
  3from aimdk_msgs.msg import HandCommandArray, HandCommand, HandType, MessageHeader
  4import time
  5
  6
  7class HandControl(Node):
  8    def __init__(self):
  9        super().__init__('hand_control')
 10
 11        # Create publisher
 12        self.publisher_ = self.create_publisher(
 13            HandCommandArray,
 14            '/aima/hal/joint/hand/command',
 15            10
 16        )
 17
 18        self.timer_ = self.create_timer(
 19            0.8,
 20            self.publish_hand_commands
 21        )
 22
 23        # Initialize variables
 24        self.target_finger = 0
 25        self.step = 1
 26        self.increasing = True
 27        self.get_logger().info("Hand control node started!")
 28
 29    def build_hand_cmd(self, name: str) -> HandCommand:
 30        cmd = HandCommand()
 31        cmd.name = name
 32        cmd.position = 0.0
 33        cmd.velocity = 0.1
 34        cmd.acceleration = 0.0
 35        cmd.deceleration = 0.0
 36        cmd.effort = 0.0
 37        return cmd
 38
 39    def publish_hand_commands(self):
 40        msg = HandCommandArray()
 41        msg.header.stamp = self.get_clock().now().to_msg()
 42        msg.header.frame_id = 'hand_command'
 43        msg.left_hand_type.value = 1      # NIMBLE_HANDS
 44        msg.right_hand_type.value = 1     # NIMBLE_HANDS
 45
 46        # left hand
 47        msg.left_hands = [self.build_hand_cmd('') for _ in range(10)]
 48        msg.left_hands[0].name = 'left_thumb'
 49        for i in range(1, 10):
 50            msg.left_hands[i].name = 'left_index'
 51
 52        # right hand
 53        msg.right_hands = [self.build_hand_cmd('') for _ in range(10)]
 54        msg.right_hands[0].name = 'right_thumb'
 55        for i in range(1, 10):
 56            msg.right_hands[i].name = 'right_pinky'
 57
 58        if self.target_finger < 10:
 59            msg.right_hands[self.target_finger].position = 0.8
 60        else:
 61            target_finger_ = self.target_finger - 10
 62            target_position = 0.8
 63            if target_finger_ < 3:
 64                # The three thumb motors on the left hand need their signs inverted to mirror the right hand's motion
 65                target_position = -target_position
 66            msg.left_hands[target_finger_].position = target_position
 67
 68        self.publisher_.publish(msg)
 69        self.get_logger().info(
 70            f'Published hand command with target_finger: {self.target_finger}')
 71        self.update_target_finger()
 72
 73    def update_target_finger(self):
 74        if self.increasing:
 75            self.target_finger += self.step
 76            if self.target_finger >= 19:
 77                self.target_finger = 19
 78                self.increasing = False
 79        else:
 80            self.target_finger -= self.step
 81            if self.target_finger <= 0:
 82                self.target_finger = 0
 83                self.increasing = True
 84
 85
 86def main(args=None):
 87    rclpy.init(args=args)
 88    hand_control_node = HandControl()
 89
 90    try:
 91        rclpy.spin(hand_control_node)
 92    except KeyboardInterrupt:
 93        pass
 94    finally:
 95        hand_control_node.destroy_node()
 96        rclpy.shutdown()
 97
 98
 99if __name__ == '__main__':
100    main()
```

## 6.1.6 Register custom input source

**For versions after v0.7, you must register an input source before controlling the MC. This example registers a custom input source via the `/aimdk_5Fmsgs/srv/SetMcInputSource` service so MC becomes aware of it; only registered input sources can perform robot velocity control.**

```
  1#!/usr/bin/env python3
  2
  3import rclpy
  4import rclpy.logging
  5from rclpy.node import Node
  6
  7from aimdk_msgs.srv import SetMcInputSource
  8from aimdk_msgs.msg import RequestHeader, McInputAction
  9
 10
 11class McInputClient(Node):
 12    def __init__(self):
 13        super().__init__('set_mc_input_source_client')
 14        self.client = self.create_client(
 15            SetMcInputSource, '/aimdk_5Fmsgs/srv/SetMcInputSource'
 16        )
 17
 18        self.get_logger().info('✅ SetMcInputSource client node created.')
 19
 20        # Wait for the service to become available
 21        while not self.client.wait_for_service(timeout_sec=2.0):
 22            self.get_logger().info('⏳ Service unavailable, waiting...')
 23
 24        self.get_logger().info('🟢 Service available, ready to send request.')
 25
 26    def send_request(self):
 27        req = SetMcInputSource.Request()
 28
 29        # header
 30        req.request.header = RequestHeader()
 31
 32        # action (e.g. 1001 = register)
 33        req.action = McInputAction()
 34        req.action.value = 1001
 35
 36        # input source info
 37        req.input_source.name = 'node'
 38        req.input_source.priority = 40
 39        req.input_source.timeout = 1000  # ms
 40
 41        # Send request and wait for response
 42        self.get_logger().info(
 43            f'📨 Sending input source request: action_id={req.action.value}, '
 44            f'name={req.input_source.name}, priority={req.input_source.priority}'
 45        )
 46        for i in range(8):
 47            req.request.header.stamp = self.get_clock().now().to_msg()
 48            future = self.client.call_async(req)
 49            rclpy.spin_until_future_complete(
 50                self, future, timeout_sec=0.25)
 51
 52            if future.done():
 53                break
 54
 55            # retry as remote peer is NOT handled well by ROS
 56            self.get_logger().info(f'trying ... [{i}]')
 57
 58        if not future.done():
 59            self.get_logger().error('❌ Service call failed or timed out.')
 60            return False
 61
 62        response = future.result()
 63        ret_code = response.response.header.code
 64        task_id = response.response.task_id
 65
 66        if ret_code == 0:
 67            self.get_logger().info(
 68                f'✅ Input source set successfully. task_id={task_id}'
 69            )
 70            return True
 71        else:
 72            self.get_logger().error(
 73                f'❌ Input source set failed. ret_code={ret_code}, task_id={task_id} (duplicated ADD? or MODIFY/ENABLE/DISABLE for unknown source?)'
 74            )
 75            return False
 76
 77
 78def main(args=None):
 79    rclpy.init(args=args)
 80
 81    node = None
 82    try:
 83        node = McInputClient()
 84        ok = node.send_request()
 85        if not ok:
 86            node.get_logger().error('Input source request failed.')
 87    except KeyboardInterrupt:
 88        pass
 89    except Exception as e:
 90        rclpy.logging.get_logger('main').error(
 91            f'Program exited with exception: {e}')
 92
 93    if node:
 94        node.destroy_node()
 95    if rclpy.ok():
 96        rclpy.shutdown()
 97
 98
 99if __name__ == '__main__':
100    main()
```

## 6.1.7 Get current input source

**This example uses the `GetCurrentInputSource` service** to retrieve information about the currently registered input source, including name, priority, and timeout.

```
 1#!/usr/bin/env python3
 2
 3import rclpy
 4from rclpy.node import Node
 5from aimdk_msgs.srv import GetCurrentInputSource
 6from aimdk_msgs.msg import CommonRequest
 7
 8
 9class GetCurrentInputSourceClient(Node):
10    def __init__(self):
11        super().__init__('get_current_input_source_client')
12        self.client = self.create_client(
13            GetCurrentInputSource,
14            '/aimdk_5Fmsgs/srv/GetCurrentInputSource'
15        )
16
17        self.get_logger().info('✅ GetCurrentInputSource client node created.')
18
19        # Wait for the service to become available
20        while not self.client.wait_for_service(timeout_sec=2.0):
21            self.get_logger().info('⏳ Service unavailable, waiting...')
22
23        self.get_logger().info('🟢 Service available, ready to send request.')
24
25    def send_request(self):
26        # Create request
27        req = GetCurrentInputSource.Request()
28        req.request = CommonRequest()
29
30        # Send request and wait for response
31        self.get_logger().info('📨 Sending request to get current input source')
32        for i in range(8):
33            req.request.header.stamp = self.get_clock().now().to_msg()
34            future = self.client.call_async(req)
35            rclpy.spin_until_future_complete(self, future, timeout_sec=0.25)
36
37            if future.done():
38                break
39
40            # retry as remote peer is NOT handled well by ROS
41            self.get_logger().info(f'trying ... [{i}]')
42
43        if not future.done():
44            self.get_logger().error('❌ Service call failed or timed out.')
45            return False
46
47        response = future.result()
48        ret_code = response.response.header.code
49        if ret_code == 0:
50            self.get_logger().info(
51                f'✅ Current input source get successfully:')
52            self.get_logger().info(
53                f'Name: {response.input_source.name}')
54            self.get_logger().info(
55                f'Priority: {response.input_source.priority}')
56            self.get_logger().info(
57                f'Timeout: {response.input_source.timeout}')
58            return True
59        else:
60            self.get_logger().error(
61                f'❌ Current input source get failed, return code: {ret_code}')
62            return False
63
64
65def main(args=None):
66    rclpy.init(args=args)
67
68    node = None
69    try:
70        node = GetCurrentInputSourceClient()
71        success = node.send_request()
72    except KeyboardInterrupt:
73        pass
74    except Exception as e:
75        rclpy.logging.get_logger('main').error(
76            f'Program exited with exception: {e}')
77
78    if node:
79        node.destroy_node()
80    if rclpy.ok():
81        rclpy.shutdown()
82
83
84if __name__ == '__main__':
85    main()
```

**Usage**

```
# Get current input source info
ros2 run py_examples get_current_input_source
```

**Example output**

```
[INFO] [get_current_input_source_client]: Current input source: node
[INFO] [get_current_input_source_client]: Priority: 40
[INFO] [get_current_input_source_client]: Timeout: 1000
```

**Notes**

- Ensure the GetCurrentInputSource service is running properly
- Valid information can only be retrieved after registering an input source
- A status code of 0 indicates the query succeeded

## 6.1.8 Control robot locomotion

**This example uses `mc_locomotion_velocity`. The example below controls robot walking by publishing to the `/aima/mc/locomotion/velocity` topic. For versions after v0.7, you must register an input source before enabling velocity control (this example already registers an input source); see the code for registration steps.**

Start the node after switching to Stable Standing Mode:

```
  1#!/usr/bin/env python3
  2
  3import rclpy
  4from rclpy.node import Node
  5import time
  6import signal
  7import sys
  8
  9from aimdk_msgs.msg import McLocomotionVelocity, MessageHeader
 10from aimdk_msgs.srv import SetMcInputSource
 11
 12
 13class DirectVelocityControl(Node):
 14    def __init__(self):
 15        super().__init__('direct_velocity_control')
 16
 17        self.publisher = self.create_publisher(
 18            McLocomotionVelocity, '/aima/mc/locomotion/velocity', 10)
 19        self.client = self.create_client(
 20            SetMcInputSource, '/aimdk_5Fmsgs/srv/SetMcInputSource')
 21
 22        self.forward_velocity = 0.0
 23        self.lateral_velocity = 0.0
 24        self.angular_velocity = 0.0
 25
 26        self.max_forward_speed = 1.0
 27        self.min_forward_speed = 0.2
 28
 29        self.max_lateral_speed = 1.0
 30        self.min_lateral_speed = 0.2
 31
 32        self.max_angular_speed = 1.0
 33        self.min_angular_speed = 0.1
 34
 35        self.timer = None
 36
 37        self.get_logger().info("Direct velocity control node started!")
 38
 39    def start_publish(self):
 40        if not self.timer:
 41            self.timer = self.create_timer(0.02, self.publish_velocity)
 42
 43    def register_input_source(self):
 44        self.get_logger().info("Registering input source...")
 45
 46        timeout_sec = 8.0
 47        start = self.get_clock().now().nanoseconds / 1e9
 48
 49        while not self.client.wait_for_service(timeout_sec=2.0):
 50            now = self.get_clock().now().nanoseconds / 1e9
 51            if now - start > timeout_sec:
 52                self.get_logger().error("Waiting for service timed out")
 53                return False
 54            self.get_logger().info("Waiting for input source service...")
 55
 56        req = SetMcInputSource.Request()
 57        req.action.value = 1001
 58        req.input_source.name = "node"
 59        req.input_source.priority = 40
 60        req.input_source.timeout = 1000
 61
 62        for i in range(8):
 63            req.request.header.stamp = self.get_clock().now().to_msg()
 64            future = self.client.call_async(req)
 65            rclpy.spin_until_future_complete(self, future, timeout_sec=0.25)
 66
 67            if future.done():
 68                break
 69
 70            # retry as remote peer is NOT handled well by ROS
 71            self.get_logger().info(f"trying to register input source... [{i}]")
 72
 73        if future.done():
 74            try:
 75                response = future.result()
 76                state = response.response.state.value
 77                self.get_logger().info(
 78                    f"Input source set successfully: state={state}, task_id={response.response.task_id}")
 79                return True
 80            except Exception as e:
 81                self.get_logger().error(f"Service call exception: {str(e)}")
 82                return False
 83        else:
 84            self.get_logger().error("Service call failed or timed out")
 85            return False
 86
 87    def publish_velocity(self):
 88        msg = McLocomotionVelocity()
 89        msg.header = MessageHeader()
 90        msg.header.stamp = self.get_clock().now().to_msg()
 91        msg.source = "node"
 92        msg.forward_velocity = self.forward_velocity
 93        msg.lateral_velocity = self.lateral_velocity
 94        msg.angular_velocity = self.angular_velocity
 95
 96        self.publisher.publish(msg)
 97
 98        self.get_logger().info(
 99            f"Publishing velocity: forward {self.forward_velocity:.2f} m/s, "
100            f"lateral {self.lateral_velocity:.2f} m/s, "
101            f"angular {self.angular_velocity:.2f} rad/s"
102        )
103
104    def set_forward(self, forward):
105        # check value range, mc has thresholds to start movement
106        if abs(forward) < 0.005:
107            self.forward_velocity = 0.0
108            return True
109        elif abs(forward) > self.max_forward_speed or abs(forward) < self.min_forward_speed:
110            raise ValueError("out of range")
111        else:
112            self.forward_velocity = forward
113            return True
114
115    def set_lateral(self, lateral):
116        # check value range, mc has thresholds to start movement
117        if abs(lateral) < 0.005:
118            self.lateral_velocity = 0.0
119            return True
120        elif abs(lateral) > self.max_lateral_speed or abs(lateral) < self.min_lateral_speed:
121            raise ValueError("out of range")
122        else:
123            self.lateral_velocity = lateral
124            return True
125
126    def set_angular(self, angular):
127        # check value range, mc has thresholds to start movement
128        if abs(angular) < 0.005:
129            self.angular_velocity = 0.0
130            return True
131        elif abs(angular) > self.max_angular_speed or abs(angular) < self.min_angular_speed:
132            raise ValueError("out of range")
133        else:
134            self.angular_velocity = angular
135            return True
136
137    def clear_velocity(self):
138        self.forward_velocity = 0.0
139        self.lateral_velocity = 0.0
140        self.angular_velocity = 0.0
141
142
143# Global node instance for signal handling
144global_node = None
145
146
147def signal_handler(sig, frame):
148    global global_node
149    if global_node is not None:
150        global_node.clear_velocity()
151        global_node.get_logger().info(
152            f"Received signal {sig}, clearing velocity and shutting down")
153    rclpy.shutdown()
154    sys.exit(0)
155
156
157def main():
158    global global_node
159    rclpy.init()
160
161    node = DirectVelocityControl()
162    global_node = node
163
164    signal.signal(signal.SIGINT, signal_handler)
165    signal.signal(signal.SIGTERM, signal_handler)
166
167    if not node.register_input_source():
168        node.get_logger().error("Input source registration failed, exiting")
169        rclpy.shutdown()
170        return
171
172    # get and check control values
173    # notice that mc has thresholds to start movement
174    try:
175        # get input forward
176        forward = float(
177            input("Please enter forward velocity 0 or ±(0.2 ~ 1.0) m/s: "))
178        node.set_forward(forward)
179        # get input lateral
180        lateral = float(
181            input("Please enter lateral velocity 0 or ±(0.2 ~ 1.0) m/s: "))
182        node.set_lateral(lateral)
183        # get input angular
184        angular = float(
185            input("Please enter angular velocity 0 or ±(0.1 ~ 1.0) rad/s: "))
186        node.set_angular(angular)
187    except Exception as e:
188        node.get_logger().error(f"Invalid input: {e}")
189        rclpy.shutdown()
190        return
191
192    node.get_logger().info("Setting velocity, moving for 5 seconds")
193    node.start_publish()
194
195    start = node.get_clock().now()
196    while (node.get_clock().now() - start).nanoseconds / 1e9 < 5.0:
197        rclpy.spin_once(node, timeout_sec=0.1)
198        time.sleep(0.001)
199
200    node.clear_velocity()
201    node.get_logger().info("5-second motion finished, robot stopped")
202
203    rclpy.spin(node)
204    rclpy.shutdown()
205
206
207if __name__ == '__main__':
208    main()
```

## 6.1.9 Joint motor control

**This example demonstrates how to use ROS2 and the Ruckig library to control robot joint motion.**

Attention

***Note ⚠️: Before running this example, stop the native MC module on the robot control unit (PC1) by running `aima em stop-app mc` to obtain control of the robot. Ensure the robot is safe before operating.***

! This example directly controls low-level motors (the HAL layer). Before running, verify that the joint safety limits in the code match your robot and ensure safety!

### Robot joint control example

This example shows how to use ROS2 and the Ruckig library to control robot joints. The example implements the following features:

1. Robot joint model definition
2. Trajectory interpolation using Ruckig
3. Multi-joint coordinated control
4. Real-time control of position, velocity, and acceleration

#### Example feature description

1. Creates four controller nodes, which control:

   - Legs x2 (12 joints)
   - Waist x1 (3 joints)
   - Arms x2 (14 joints)
   - Head x1 (2 joints)
2. Demo features:

   - Oscillate a specified joint between ±0.5 radians every 10 seconds
   - Use the Ruckig library to generate smooth motion trajectories
   - Publish joint control commands in real time

#### Custom usage

2. Add new control logic:

   - Add new control callback functions
   - Compose joint motions freely
3. Adjust control frequency:

   - Modify the `control_timer_` period (currently 2 ms)

```
  1#!/usr/bin/env python3
  2"""
  3Robot joint control example
  4This script implements a ROS2-based robot joint control system, using the Ruckig trajectory
  5planner to achieve smooth joint motion control.
  6
  7Main features:
  81. Supports controlling multiple joint areas (head, arm, waist, leg)
  92. Uses Ruckig for trajectory planning to ensure smooth motion
 103. Supports real-time control of joint position, velocity, and acceleration
 114. Provides joint limit and PID (stiffness/damping) parameter configuration
 12"""
 13
 14import rclpy
 15from rclpy.node import Node
 16from rclpy.qos import QoSProfile, ReliabilityPolicy, HistoryPolicy, DurabilityPolicy
 17from aimdk_msgs.msg import JointCommandArray, JointStateArray, JointCommand
 18from std_msgs.msg import Header
 19import ruckig
 20from enum import Enum
 21from dataclasses import dataclass
 22from typing import List, Dict
 23from threading import Lock
 24
 25# QoS config: define ROS2 Quality of Service parameters
 26# Subscriber QoS: best-effort reliability, keep last 10 messages
 27subscriber_qos = QoSProfile(
 28    reliability=ReliabilityPolicy.BEST_EFFORT,
 29    history=HistoryPolicy.KEEP_LAST,
 30    depth=10,
 31    durability=DurabilityPolicy.VOLATILE
 32)
 33
 34# Publisher QoS: reliable transport, keep last 10 messages
 35publisher_qos = QoSProfile(
 36    reliability=ReliabilityPolicy.RELIABLE,
 37    history=HistoryPolicy.KEEP_LAST,
 38    depth=10,
 39    durability=DurabilityPolicy.VOLATILE
 40)
 41
 42
 43class JointArea(Enum):
 44    HEAD = 'HEAD'    # Head joints
 45    ARM = 'ARM'      # Arm joints
 46    WAIST = 'WAIST'  # Waist joints
 47    LEG = 'LEG'      # Leg joints
 48
 49
 50@dataclass
 51class JointInfo:
 52    # Joint information data class
 53    name: str           # Joint name
 54    lower_limit: float  # Joint lower angle limit
 55    upper_limit: float  # Joint upper angle limit
 56    kp: float           # Position control proportional gain
 57    kd: float           # Velocity control derivative gain
 58
 59
 60# Robot model configuration: define all joint parameters
 61robot_model: Dict[JointArea, List[JointInfo]] = {
 62    # Leg joint configuration
 63    JointArea.LEG: [
 64        # Left leg joints
 65        JointInfo("left_hip_pitch_joint", -2.704, 2.556, 40.0, 4.0),
 66        JointInfo("left_hip_roll_joint", -0.235, 2.906, 40.0, 4.0),
 67        JointInfo("left_hip_yaw_joint", -1.684, 3.430, 30.0, 3.0),
 68        JointInfo("left_knee_joint", 0.0000, 2.4073, 80.0, 8.0),
 69        JointInfo("left_ankle_pitch_joint", -0.803, 0.453, 40.0, 4.0),
 70        JointInfo("left_ankle_roll_joint", -0.2625, 0.2625, 20.0, 2.0),
 71        # Right leg joints
 72        JointInfo("right_hip_pitch_joint", -2.704, 2.556, 40.0, 4.0),
 73        JointInfo("right_hip_roll_joint", -2.906, 0.235, 40.0, 4.0),
 74        JointInfo("right_hip_yaw_joint", -3.430, 1.684, 30.0, 3.0),
 75        JointInfo("right_knee_joint", 0.0000, 2.4073, 80.0, 8.0),
 76        JointInfo("right_ankle_pitch_joint", -0.803, 0.453, 40.0, 4.0),
 77        JointInfo("right_ankle_roll_joint", -0.2625, 0.2625, 20.0, 2.0),
 78    ],
 79    # Waist joint configuration
 80    JointArea.WAIST: [
 81        JointInfo("waist_yaw_joint", -3.43, 2.382, 20.0, 4.0),
 82        JointInfo("waist_pitch_joint", -0.314, 0.314, 20.0, 4.0),
 83        JointInfo("waist_roll_joint", -0.488, 0.488, 20.0, 4.0),
 84    ],
 85    # Arm joint configuration
 86    JointArea.ARM: [
 87        # Left arm
 88        JointInfo("left_shoulder_pitch_joint", -3.08, 2.04, 20.0, 2.0),
 89        JointInfo("left_shoulder_roll_joint", -0.061, 2.993, 20.0, 2.0),
 90        JointInfo("left_shoulder_yaw_joint", -2.556, 2.556, 20.0, 2.0),
 91        JointInfo("left_elbow_joint", -2.3556, 0.0, 20.0, 2.0),
 92        JointInfo("left_wrist_yaw_joint", -2.556, 2.556, 20.0, 2.0),
 93        JointInfo("left_wrist_pitch_joint", -0.558, 0.558, 20.0, 2.0),
 94        JointInfo("left_wrist_roll_joint", -1.571, 0.724, 20.0, 2.0),
 95        # Right arm
 96        JointInfo("right_shoulder_pitch_joint", -3.08, 2.04, 20.0, 2.0),
 97        JointInfo("right_shoulder_roll_joint", -2.993, 0.061, 20.0, 2.0),
 98        JointInfo("right_shoulder_yaw_joint", -2.556, 2.556, 20.0, 2.0),
 99        JointInfo("right_elbow_joint", -2.3556, 0.0000, 20.0, 2.0),
100        JointInfo("right_wrist_yaw_joint", -2.556, 2.556, 20.0, 2.0),
101        JointInfo("right_wrist_pitch_joint", -0.558, 0.558, 20.0, 2.0),
102        JointInfo("right_wrist_roll_joint", -0.724, 1.571, 20.0, 2.0),
103    ],
104    # Head joint configuration
105    JointArea.HEAD: [
106        JointInfo("head_yaw_joint", -0.366, 0.366, 20.0, 2.0),
107        JointInfo("head_pitch_joint", -0.3838, 0.3838, 20.0, 2.0),
108    ],
109}
110
111
112class JointControllerNode(Node):
113    """
114    Joint controller node
115    Responsible for receiving joint states, using Ruckig for trajectory planning,
116    and publishing joint commands.
117    """
118
119    def __init__(self, node_name: str, sub_topic: str, pub_topic: str, area: JointArea, dofs: int):
120        """
121        Initialize joint controller
122        Args:
123            node_name: node name
124            sub_topic: topic name to subscribe (joint states)
125            pub_topic: topic name to publish (joint commands)
126            area: joint area (head/arm/waist/leg)
127            dofs: number of DOFs
128        """
129        super().__init__(node_name)
130        self.lock = Lock()
131        self.joint_info = robot_model[area]
132        self.dofs = dofs
133        self.ruckig = ruckig.Ruckig(dofs, 0.002)  # 2 ms control period
134        self.input = ruckig.InputParameter(dofs)
135        self.output = ruckig.OutputParameter(dofs)
136        self.ruckig_initialized = False
137
138        # Initialize trajectory parameters
139        self.input.current_position = [0.0] * dofs
140        self.input.current_velocity = [0.0] * dofs
141        self.input.current_acceleration = [0.0] * dofs
142
143        # Motion limits
144        self.input.max_velocity = [1.0] * dofs
145        self.input.max_acceleration = [1.0] * dofs
146        self.input.max_jerk = [25.0] * dofs
147
148        # ROS2 subscriber and publisher
149        self.sub = self.create_subscription(
150            JointStateArray,
151            sub_topic,
152            self.joint_state_callback,
153            subscriber_qos
154        )
155        self.pub = self.create_publisher(
156            JointCommandArray,
157            pub_topic,
158            publisher_qos
159        )
160
161    def joint_state_callback(self, msg: JointStateArray):
162        """
163        Joint state callback
164        Receives and processes joint state messages
165        """
166        self.ruckig_initialized = True
167
168    def control_callback(self, joint_idx):
169        """
170        Control callback
171        Uses Ruckig for trajectory planning and publishes control commands
172        Args:
173            joint_idx: target joint index
174        """
175        # Run Ruckig until the target is reached
176        while self.ruckig.update(self.input, self.output) in [ruckig.Result.Working, ruckig.Result.Finished]:
177            # Update current state
178            self.input.current_position = self.output.new_position
179            self.input.current_velocity = self.output.new_velocity
180            self.input.current_acceleration = self.output.new_acceleration
181
182            # Check if target is reached
183            tolerance = 1e-6
184            current_p = self.output.new_position[joint_idx]
185            if abs(current_p - self.input.target_position[joint_idx]) < tolerance:
186                break
187
188            # Create and publish command
189            cmd = JointCommandArray()
190            for i, joint in enumerate(self.joint_info):
191                j = JointCommand()
192                j.name = joint.name
193                j.position = self.output.new_position[i]
194                j.velocity = self.output.new_velocity[i]
195                j.effort = 0.0
196                j.stiffness = joint.kp
197                j.damping = joint.kd
198                cmd.joints.append(j)
199
200            self.pub.publish(cmd)
201
202    def set_target_position(self, joint_name, position):
203        """
204        Set target joint position
205        Args:
206            joint_name: joint name
207            position: target position
208        """
209        p_s = [0.0] * self.dofs
210        joint_idx = 0
211        for i, joint in enumerate(self.joint_info):
212            if joint.name == joint_name:
213                p_s[i] = position
214                joint_idx = i
215        self.input.target_position = p_s
216        self.input.target_velocity = [0.0] * self.dofs
217        self.input.target_acceleration = [0.0] * self.dofs
218        self.control_callback(joint_idx)
219
220
221def main(args=None):
222    """
223    Main function
224    Initialize ROS2 node and start joint controller
225    """
226    rclpy.init(args=args)
227
228    # Create leg controller node
229    leg_node = JointControllerNode(
230        "leg_node",
231        "/aima/hal/joint/leg/state",
232        "/aima/hal/joint/leg/command",
233        JointArea.LEG,
234        12
235    )
236
237    # waist_node = JointControllerNode(
238    #     "waist_node",
239    #     "/aima/hal/joint/waist/state",
240    #     "/aima/hal/joint/waist/command",
241    #     JointArea.WAIST,
242    #     3
243    # )
244
245    # arm_node = JointControllerNode(
246    #     "arm_node",
247    #     "/aima/hal/joint/arm/state",
248    #     "/aima/hal/joint/arm/command",
249    #     JointArea.ARM,
250    #     14
251    # )
252
253    # head_node = JointControllerNode(
254    #     "head_node",
255    #     "/aima/hal/joint/head/state",
256    #     "/aima/hal/joint/head/command",
257    #     JointArea.HEAD,
258    #     2
259    # )
260
261    position = 0.8
262
263    # Only control the left leg joint. If you want to control a specific joint, assign it directly.
264    def timer_callback():
265        """
266        Timer callback
267        Periodically change target position to achieve oscillating motion
268        """
269        nonlocal position
270        position = -position
271        position = 1.3 + position
272        leg_node.set_target_position("left_knee_joint", position)
273
274    #     arm_node.set_target_position("left_shoulder_pitch_joint", position)
275    #     waist_node.set_target_position("waist_yaw_joint", position)
276    #     head_node.set_target_position("head_pitch_joint", position)
277
278    leg_node.create_timer(3.0, timer_callback)
279
280    # Multi-threaded executor
281    executor = rclpy.executors.MultiThreadedExecutor()
282    executor.add_node(leg_node)
283
284    # executor.add_node(waist_node)
285    # executor.add_node(arm_node)
286    # executor.add_node(head_node)
287
288    try:
289        executor.spin()
290    except KeyboardInterrupt:
291        pass
292    finally:
293        leg_node.destroy_node()
294        # waist_node.destroy_node()
295        # arm_node.destroy_node()
296        # head_node.destroy_node()
297        if rclpy.ok():
298            rclpy.shutdown()
299
300
301if __name__ == '__main__':
302    main()
```

## 6.1.10 Keyboard control

**This example implements robot forward/backward and turning control using keyboard input from a PC.**

**Use `W` `A` `S` `D` to control robot direction; increase/decrease speed by ±0.2 m/s. Use `Q`/`E` to increase/decrease angular speed by ±0.1 rad/s. Press `ESC` to exit and release terminal resources. Press `Space` to immediately zero speed (emergency stop).**

Caution

***Note: Before running this example, use the controller to put the robot into the Stable Standing Mode mode. (For position-control stand / locomotion modes press `R2` + `X`; see the [mode transition diagram](../quick_start/run_example.html#fig-routing-to-stand-default) for other modes.) Then run `aima em stop-app rc` on the robot’s terminal to stop the remote controller and prevent channel occupation.***

You must register an input source before using keyboard control (this example registers one).

```
  1#!/usr/bin/env python3
  2
  3import rclpy
  4import rclpy.logging
  5from rclpy.node import Node
  6from aimdk_msgs.msg import McLocomotionVelocity, MessageHeader
  7from aimdk_msgs.srv import SetMcInputSource
  8import curses
  9import time
 10from functools import partial
 11
 12
 13class KeyboardVelocityController(Node):
 14    def __init__(self, stdscr):
 15        super().__init__('keyboard_velocity_controller')
 16        self.stdscr = stdscr
 17        self.forward_velocity = 0.0
 18        self.lateral_velocity = 0.0
 19        self.angular_velocity = 0.0
 20        self.step = 0.2
 21        self.angular_step = 0.1
 22
 23        self.publisher = self.create_publisher(
 24            McLocomotionVelocity, '/aima/mc/locomotion/velocity', 10)
 25        self.client = self.create_client(
 26            SetMcInputSource, '/aimdk_5Fmsgs/srv/SetMcInputSource')
 27
 28        if not self.register_input_source():
 29            self.get_logger().error("Input source registration failed, exiting")
 30            raise RuntimeError("Failed to register input source")
 31
 32        # Configure curses
 33        curses.cbreak()
 34        curses.noecho()
 35        self.stdscr.keypad(True)
 36        self.stdscr.nodelay(True)
 37
 38        self.get_logger().info(
 39            "Control started: W/S forward/backward, A/D strafe, Q/E turn, Space stop, Esc exit")
 40
 41        # Timer: check keyboard every 50 ms
 42        self.timer = self.create_timer(0.05, self.check_key_and_publish)
 43
 44    def register_input_source(self):
 45        self.get_logger().info("Registering input source...")
 46
 47        timeout_sec = 8.0
 48        start = self.get_clock().now().nanoseconds / 1e9
 49
 50        while not self.client.wait_for_service(timeout_sec=2.0):
 51            now = self.get_clock().now().nanoseconds / 1e9
 52            if now - start > timeout_sec:
 53                self.get_logger().error("Waiting for service timed out")
 54                return False
 55            self.get_logger().info("Waiting for input source service...")
 56
 57        req = SetMcInputSource.Request()
 58        req.action.value = 1001
 59        req.input_source.name = "node"
 60        req.input_source.priority = 40
 61        req.input_source.timeout = 1000
 62
 63        for i in range(8):
 64            req.request.header.stamp = self.get_clock().now().to_msg()
 65            future = self.client.call_async(req)
 66            rclpy.spin_until_future_complete(self, future, timeout_sec=0.25)
 67
 68            if future.done():
 69                break
 70
 71            # retry as remote peer is NOT handled well by ROS
 72            self.get_logger().info(f"trying to register input source... [{i}]")
 73
 74        if future.done():
 75            try:
 76                resp = future.result()
 77                state = resp.response.state.value
 78                self.get_logger().info(
 79                    f"Input source set successfully: state={state}, task_id={resp.response.task_id}")
 80                return True
 81            except Exception as e:
 82                self.get_logger().error(f"Service exception: {str(e)}")
 83                return False
 84        else:
 85            self.get_logger().error("Service call failed or timed out")
 86            return False
 87
 88    def check_key_and_publish(self):
 89        try:
 90            ch = self.stdscr.getch()
 91        except Exception:
 92            ch = -1
 93
 94        if ch != -1:
 95            if ch == ord(' '):
 96                self.forward_velocity = 0.0
 97                self.lateral_velocity = 0.0
 98                self.angular_velocity = 0.0
 99            elif ch == ord('w'):
100                self.forward_velocity = min(
101                    self.forward_velocity + self.step, 1.0)
102            elif ch == ord('s'):
103                self.forward_velocity = max(
104                    self.forward_velocity - self.step, -1.0)
105            elif ch == ord('a'):
106                self.lateral_velocity = min(
107                    self.lateral_velocity + self.step, 1.0)
108            elif ch == ord('d'):
109                self.lateral_velocity = max(
110                    self.lateral_velocity - self.step, -1.0)
111            elif ch == ord('q'):
112                self.angular_velocity = min(
113                    self.angular_velocity + self.angular_step, 1.0)
114            elif ch == ord('e'):
115                self.angular_velocity = max(
116                    self.angular_velocity - self.angular_step, -1.0)
117            elif ch == 27:  # ESC
118                self.get_logger().info("Exiting control")
119                rclpy.shutdown()
120                return
121
122        msg = McLocomotionVelocity()
123        msg.header = MessageHeader()
124        msg.header.stamp = self.get_clock().now().to_msg()
125        msg.source = "node"
126        msg.forward_velocity = self.forward_velocity
127        msg.lateral_velocity = self.lateral_velocity
128        msg.angular_velocity = self.angular_velocity
129
130        self.publisher.publish(msg)
131
132        # Update UI
133        self.stdscr.clear()
134        self.stdscr.addstr(
135            0, 0, "W/S: Forward/Backward | A/D: Strafe | Q/E: Turn | Space: Stop | ESC: Exit")
136        self.stdscr.addstr(2, 0,
137                           f"Speed Status: Forward: {self.forward_velocity:.2f} m/s | "
138                           f"Lateral: {self.lateral_velocity:.2f} m/s | "
139                           f"Angular: {self.angular_velocity:.2f} rad/s")
140        self.stdscr.refresh()
141
142
143def curses_main(stdscr):
144    rclpy.init()
145    try:
146        node = KeyboardVelocityController(stdscr)
147        rclpy.spin(node)
148    except Exception as e:
149        rclpy.logging.get_logger("main").fatal(
150            f"Program exited with exception: {e}")
151    finally:
152        curses.endwin()
153        rclpy.shutdown()
154
155
156def main():
157    curses.wrapper(curses_main)
158
159
160if __name__ == '__main__':
161    main()
```

## 6.1.11 Take photo

**This example uses `take_photo`. Before running the node, set the camera topic to capture. When started, the node creates an `/images/` directory and saves the current frame into that directory.**

```
 1#!/usr/bin/env python3
 2import time
 3from pathlib import Path
 4
 5import rclpy
 6from rclpy.node import Node
 7from rclpy.qos import qos_profile_sensor_data
 8from sensor_msgs.msg import Image
 9from cv_bridge import CvBridge
10import cv2
11
12
13class SaveOneRawPy(Node):
14    def __init__(self):
15        super().__init__('save_one_image')
16
17        # parameter: image topic
18        self.declare_parameter(
19            'image_topic', '/aima/hal/sensor/stereo_head_front_left/rgb_image'
20        )
21        self.topic = self.get_parameter(
22            'image_topic').get_parameter_value().string_value
23
24        # save directory
25        self.save_dir = Path('images').resolve()
26        self.save_dir.mkdir(parents=True, exist_ok=True)
27
28        # state
29        self._saved = False
30        self._bridge = CvBridge()
31
32        # subscriber (sensor QoS)
33        self.sub = self.create_subscription(
34            Image,
35            self.topic,
36            self.image_cb,
37            qos_profile_sensor_data
38        )
39        self.get_logger().info(f'Subscribing to raw image: {self.topic}')
40        self.get_logger().info(f'Images will be saved to: {self.save_dir}')
41
42    def image_cb(self, msg: Image):
43        # already saved one, ignore later frames
44        if self._saved:
45            return
46
47        try:
48            enc = msg.encoding.lower()
49            self.get_logger().info(f'Received image with encoding: {enc}')
50
51            # convert from ROS Image to cv2
52            img = self._bridge.imgmsg_to_cv2(
53                msg, desired_encoding='passthrough')
54
55            # normalize to BGR for saving
56            if enc == 'rgb8':
57                img = cv2.cvtColor(img, cv2.COLOR_RGB2BGR)
58            elif enc == 'mono8':
59                img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)
60            # if it's bgr8 or other 8-bit bgr that cv2 can save, we just use it
61
62            ts_ms = int(time.time() * 1000)
63            out_path = self.save_dir / f'frame_{ts_ms}.png'
64
65            ok = cv2.imwrite(str(out_path), img)
66            if ok:
67                self.get_logger().info(
68                    f'Saved image: {out_path}  ({img.shape[1]}x{img.shape[0]})'
69                )
70                self._saved = True
71                # shut down once we got exactly one frame
72                # destroy node first, then shutdown rclpy
73                self.destroy_node()
74                if rclpy.ok():
75                    rclpy.shutdown()
76            else:
77                self.get_logger().error(f'cv2.imwrite failed: {out_path}')
78        except Exception as e:
79            self.get_logger().error(f'Failed to decode / save image: {e}')
80
81
82def main():
83    rclpy.init()
84    node = SaveOneRawPy()
85    rclpy.spin(node)
86    # in case the node was already destroyed in the callback
87    if rclpy.ok():
88        try:
89            node.destroy_node()
90        except Exception:
91            pass
92        rclpy.shutdown()
93
94
95if __name__ == '__main__':
96    main()
```

## 6.1.12 Camera stream examples

**This example collection provides multiple camera subscription and processing demos, supporting depth, stereo, and mono camera streams.**
These camera subscription examples are not application-level; they only print basic camera data. If you are familiar with ROS2, you can achieve similar results with `ros2 topic echo` + `ros2 topic hz`. You can consult the SDK topic list to jump directly into module development or use these camera examples as scaffolding for your own logic. **The published sensor data are raw (no preprocessing like undistortion). For detailed sensor information (e.g., resolution, focal length), check the corresponding camera\_info topic.**

### Depth camera data subscription

**This example uses `echo_camera_rgbd` to subscribe to `/aima/hal/sensor/rgbd_head_front/` and receive the robot’s depth camera data. It supports depth pointclouds, depth images, RGB images, compressed RGB images, and camera intrinsics.**

**Features:**

- Supports multiple data type subscriptions (depth pointcloud, depth image, RGB image, compressed image, camera intrinsics)
- Real-time FPS statistics and data display
- Supports RGB image video recording(TBD, see [C++ examples](Cpp.html#cpp-echo-camera-rgbd))
- Configurable topic type selection

**Supported data types:**

- `depth_pointcloud`: Depth point cloud data (sensor\_msgs/PointCloud2)
- `depth_image`: Depth image (sensor\_msgs/Image)
- `rgb_image`: RGB image (sensor\_msgs/Image)
- `rgb_image_compressed`: Compressed RGB image (sensor\_msgs/CompressedImage)
- `camera_info`: Camera intrinsic parameters (sensor\_msgs/CameraInfo)

```
  1#!/usr/bin/env python3
  2"""
  3Head depth camera multi-topic subscription example
  4
  5Supports selecting the topic type to subscribe via startup parameter --ros-args -p topic_type:=<type>:
  6  - depth_pointcloud: Depth point cloud (sensor_msgs/PointCloud2)
  7  - depth_image: Depth image (sensor_msgs/Image)
  8  - depth_camera_info: Camera intrinsic parameters (sensor_msgs/CameraInfo)
  9  - rgb_image: RGB image (sensor_msgs/Image)
 10  - rgb_image_compressed: RGB compressed image (sensor_msgs/CompressedImage)
 11  - rgb_camera_info: Camera intrinsic parameters (sensor_msgs/CameraInfo)
 12
 13Example:
 14  ros2 run py_examples echo_camera_rgbd --ros-args -p topic_type:=depth_pointcloud
 15  ros2 run py_examples echo_camera_rgbd --ros-args -p topic_type:=rgb_image
 16  ros2 run py_examples echo_camera_rgbd --ros-args -p topic_type:=rgb_camera_info
 17
 18Default topic_type is rgb_image
 19"""
 20
 21import rclpy
 22from rclpy.node import Node
 23from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
 24from sensor_msgs.msg import Image, CompressedImage, CameraInfo, PointCloud2
 25from collections import deque
 26import time
 27
 28
 29class CameraTopicEcho(Node):
 30    def __init__(self):
 31        super().__init__('camera_topic_echo')
 32
 33        # Select the topic type to subscribe
 34        self.declare_parameter('topic_type', 'rgb_image')
 35        self.declare_parameter('dump_video_path', '')
 36
 37        self.topic_type = self.get_parameter('topic_type').value
 38        self.dump_video_path = self.get_parameter('dump_video_path').value
 39
 40        # SensorDataQoS: BEST_EFFORT + VOLATILE
 41        qos = QoSProfile(
 42            reliability=QoSReliabilityPolicy.BEST_EFFORT,
 43            history=QoSHistoryPolicy.KEEP_LAST,
 44            depth=5
 45        )
 46
 47        # Create different subscribers based on topic_type
 48        if self.topic_type == "depth_pointcloud":
 49            self.topic_name = "/aima/hal/sensor/rgbd_head_front/depth_pointcloud"
 50            self.sub_pointcloud = self.create_subscription(
 51                PointCloud2, self.topic_name, self.cb_pointcloud, qos)
 52            self.get_logger().info(
 53                f"✅ Subscribing PointCloud2: {self.topic_name}")
 54
 55        elif self.topic_type == "depth_image":
 56            self.topic_name = "/aima/hal/sensor/rgbd_head_front/depth_image"
 57            self.sub_image = self.create_subscription(
 58                Image, self.topic_name, self.cb_image, qos)
 59            self.get_logger().info(
 60                f"✅ Subscribing Depth Image: {self.topic_name}")
 61
 62        elif self.topic_type == "rgb_image":
 63            self.topic_name = "/aima/hal/sensor/rgbd_head_front/rgb_image"
 64            self.sub_image = self.create_subscription(
 65                Image, self.topic_name, self.cb_image, qos)
 66            self.get_logger().info(
 67                f"✅ Subscribing RGB Image: {self.topic_name}")
 68            if self.dump_video_path:
 69                self.get_logger().info(
 70                    f"📝 Will dump received images to video: {self.dump_video_path}")
 71
 72        elif self.topic_type == "rgb_image_compressed":
 73            self.topic_name = "/aima/hal/sensor/rgbd_head_front/rgb_image/compressed"
 74            self.sub_compressed = self.create_subscription(
 75                CompressedImage, self.topic_name, self.cb_compressed, qos)
 76            self.get_logger().info(
 77                f"✅ Subscribing CompressedImage: {self.topic_name}")
 78
 79        elif self.topic_type == "rgb_camera_info":
 80            self.topic_name = "/aima/hal/sensor/rgbd_head_front/rgb_camera_info"
 81            # RGB-D CameraInfo is different with other cameras. The best_effort + volatile QoS is enough for 10Hz rgb_camera_info
 82            self.sub_camerainfo = self.create_subscription(
 83                CameraInfo, self.topic_name, self.cb_camerainfo, qos)
 84            self.get_logger().info(
 85                f"✅ Subscribing RGB CameraInfo: {self.topic_name}")
 86
 87        elif self.topic_type == "depth_camera_info":
 88            self.topic_name = "/aima/hal/sensor/rgbd_head_front/depth_camera_info"
 89            # RGB-D CameraInfo is different with other cameras. The best_effort + volatile QoS is enough for 10Hz depth_camera_info
 90            self.sub_camerainfo = self.create_subscription(
 91                CameraInfo, self.topic_name, self.cb_camerainfo, qos)
 92            self.get_logger().info(
 93                f"✅ Subscribing Depth CameraInfo: {self.topic_name}")
 94
 95        else:
 96            self.get_logger().error(f"Unknown topic_type: {self.topic_type}")
 97            raise ValueError("Unknown topic_type")
 98
 99        # Internal state
100        self.last_print = self.get_clock().now()
101        self.print_allowed = False
102        self.arrivals = deque()
103
104    def update_arrivals(self):
105        """Calculate received FPS"""
106        now = self.get_clock().now()
107        self.arrivals.append(now)
108        while self.arrivals and (now - self.arrivals[0]).nanoseconds * 1e-9 > 1.0:
109            self.arrivals.popleft()
110
111    def get_fps(self):
112        """Get FPS"""
113        return len(self.arrivals)
114
115    def should_print(self, master=True):
116        """Control print frequency"""
117        if not master:
118            return self.print_allowed
119        now = self.get_clock().now()
120        if (now - self.last_print).nanoseconds * 1e-9 >= 1.0:
121            self.last_print = now
122            self.print_allowed = True
123        else:
124            self.print_allowed = False
125        return self.print_allowed
126
127    def cb_pointcloud(self, msg: PointCloud2):
128        """PointCloud2 callback"""
129        self.update_arrivals()
130
131        if self.should_print():
132            stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
133
134            # Format fields information
135            fields_str = " ".join(
136                [f"{f.name}({f.datatype})" for f in msg.fields])
137
138            self.get_logger().info(
139                f"🌫️ PointCloud2 received\n"
140                f"  • frame_id:        {msg.header.frame_id}\n"
141                f"  • stamp (sec):     {stamp_sec:.6f}\n"
142                f"  • width x height:  {msg.width} x {msg.height}\n"
143                f"  • point_step:      {msg.point_step}\n"
144                f"  • row_step:        {msg.row_step}\n"
145                f"  • fields:          {fields_str}\n"
146                f"  • is_bigendian:    {msg.is_bigendian}\n"
147                f"  • is_dense:        {msg.is_dense}\n"
148                f"  • data size:       {len(msg.data)}\n"
149                f"  • recv FPS (1s):   {self.get_fps():.1f}"
150            )
151
152    def cb_image(self, msg: Image):
153        """Image callback (Depth/RGB image)"""
154        self.update_arrivals()
155
156        if self.should_print():
157            stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
158            self.get_logger().info(
159                f"📸 {self.topic_type} received\n"
160                f"  • frame_id:        {msg.header.frame_id}\n"
161                f"  • stamp (sec):     {stamp_sec:.6f}\n"
162                f"  • encoding:        {msg.encoding}\n"
163                f"  • size (WxH):      {msg.width} x {msg.height}\n"
164                f"  • step (bytes/row):{msg.step}\n"
165                f"  • is_bigendian:    {msg.is_bigendian}\n"
166                f"  • recv FPS (1s):   {self.get_fps():.1f}"
167            )
168
169        # Only RGB image supports video dump
170        if self.topic_type == "rgb_image" and self.dump_video_path:
171            self.dump_image_to_video(msg)
172
173    def cb_compressed(self, msg: CompressedImage):
174        """CompressedImage callback"""
175        self.update_arrivals()
176
177        if self.should_print():
178            stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
179            self.get_logger().info(
180                f"🗜️  CompressedImage received\n"
181                f"  • frame_id:        {msg.header.frame_id}\n"
182                f"  • stamp (sec):     {stamp_sec:.6f}\n"
183                f"  • format:          {msg.format}\n"
184                f"  • data size:       {len(msg.data)}\n"
185                f"  • recv FPS (1s):   {self.get_fps():.1f}"
186            )
187
188    def cb_camerainfo(self, msg: CameraInfo):
189        """CameraInfo callback (camera intrinsic parameters)"""
190        # Camera info will only receive one frame, print it directly
191        stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
192
193        # Format D array
194        d_str = ", ".join([f"{d:.6f}" for d in msg.d])
195
196        # Format K matrix
197        k_str = ", ".join([f"{k:.6f}" for k in msg.k])
198
199        # Format P matrix
200        p_str = ", ".join([f"{p:.6f}" for p in msg.p])
201
202        self.get_logger().info(
203            f"📷 {self.topic_type} received\n"
204            f"  • frame_id:        {msg.header.frame_id}\n"
205            f"  • stamp (sec):     {stamp_sec:.6f}\n"
206            f"  • width x height:  {msg.width} x {msg.height}\n"
207            f"  • distortion_model:{msg.distortion_model}\n"
208            f"  • D: [{d_str}]\n"
209            f"  • K: [{k_str}]\n"
210            f"  • P: [{p_str}]\n"
211            f"  • binning_x: {msg.binning_x}\n"
212            f"  • binning_y: {msg.binning_y}\n"
213            f"  • roi: {{ x_offset: {msg.roi.x_offset}, y_offset: {msg.roi.y_offset}, height: {msg.roi.height}, width: {msg.roi.width}, do_rectify: {msg.roi.do_rectify} }}"
214        )
215
216    def dump_image_to_video(self, msg: Image):
217        """Video dump is only supported for RGB images"""
218        # You can add video recording functionality here
219        # Simplified in the Python version, only logs instead
220        if self.should_print(master=False):
221            self.get_logger().info(f"📝 Video dump not implemented in Python version")
222
223
224def main(args=None):
225    rclpy.init(args=args)
226    try:
227        node = CameraTopicEcho()
228        rclpy.spin(node)
229    except KeyboardInterrupt:
230        pass
231    except Exception as e:
232        print(f"Error: {e}")
233    finally:
234        if 'node' in locals():
235            node.destroy_node()
236        rclpy.shutdown()
237
238
239if __name__ == '__main__':
240    main()
```

**Usage:**

1. Subscribe to depth pointcloud:

   ```
   ros2 run py_examples echo_camera_rgbd --ros-args -p topic_type:=depth_pointcloud
   ```
2. Subscribe to RGB image data:

   ```
   ros2 run py_examples echo_camera_rgbd --ros-args -p topic_type:=rgb_image
   ```
3. Subscribe to camera intrinsics:

   ```
   ros2 run py_examples echo_camera_rgbd --ros-args -p topic_type:=rgb_camera_info
   ros2 run py_examples echo_camera_rgbd --ros-args -p topic_type:=depth_camera_info
   ```
4. Record RGB video:

   ```
   # You can change dump_video_path to another path; ensure the directory exists before saving
   ros2 run py_examples echo_camera_rgbd --ros-args -p topic_type:=rgb_image -p dump_video_path:=$PWD/output.avi
   ```

### Stereo camera data subscription

**This example uses `echo_camera_stereo` to subscribe to `/aima/hal/sensor/stereo_head_front_*/` and receive stereo camera data from the robot, supporting left/right RGB images, compressed images, and camera intrinsics.**

**Features:**

- Supports independent left/right camera subscriptions
- Real-time FPS statistics and data display
- Supports RGB image video recording(TBD, see [C++ examples](Cpp.html#cpp-echo-camera-stereo))
- Configurable camera selection (left/right)

**Supported data types:**

- `left_rgb_image`: Left camera RGB image (sensor\_msgs/Image)
- `left_rgb_image_compressed`: Left camera compressed RGB image (sensor\_msgs/CompressedImage)
- `left_camera_info`: Left camera intrinsics (sensor\_msgs/CameraInfo)
- `right_rgb_image`: Right camera RGB image (sensor\_msgs/Image)
- `right_rgb_image_compressed`: Right camera compressed RGB image (sensor\_msgs/CompressedImage)
- `right_camera_info`: Right camera intrinsics (sensor\_msgs/CameraInfo)

```
  1#!/usr/bin/env python3
  2"""
  3Head stereo camera multi-topic subscription example
  4
  5Supports selecting the topic type to subscribe via startup parameter --ros-args -p topic_type:=<type>:
  6  - left_rgb_image: Left camera RGB image (sensor_msgs/Image)
  7  - left_rgb_image_compressed: Left camera RGB compressed image (sensor_msgs/CompressedImage)
  8  - left_camera_info: Left camera intrinsic parameters (sensor_msgs/CameraInfo)
  9  - right_rgb_image: Right camera RGB image (sensor_msgs/Image)
 10  - right_rgb_image_compressed: Right camera RGB compressed image (sensor_msgs/CompressedImage)
 11  - right_camera_info: Right camera intrinsic parameters (sensor_msgs/CameraInfo)
 12
 13Example:
 14  ros2 run py_examples echo_camera_stereo --ros-args -p topic_type:=left_rgb_image
 15  ros2 run py_examples echo_camera_stereo --ros-args -p topic_type:=right_rgb_image
 16  ros2 run py_examples echo_camera_stereo --ros-args -p topic_type:=left_camera_info
 17
 18Default topic_type is left_rgb_image
 19"""
 20
 21import rclpy
 22from rclpy.node import Node
 23from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy, QoSHistoryPolicy
 24from sensor_msgs.msg import Image, CompressedImage, CameraInfo
 25from collections import deque
 26import time
 27
 28
 29class StereoCameraTopicEcho(Node):
 30    def __init__(self):
 31        super().__init__('stereo_camera_topic_echo')
 32
 33        # Select the topic type to subscribe
 34        self.declare_parameter('topic_type', 'left_rgb_image')
 35        self.declare_parameter('dump_video_path', '')
 36
 37        self.topic_type = self.get_parameter('topic_type').value
 38        self.dump_video_path = self.get_parameter('dump_video_path').value
 39
 40        # Set QoS parameters - use sensor data QoS
 41        qos = QoSProfile(
 42            reliability=QoSReliabilityPolicy.BEST_EFFORT,
 43            history=QoSHistoryPolicy.KEEP_LAST,
 44            depth=5,
 45            durability=QoSDurabilityPolicy.VOLATILE
 46        )
 47
 48        # Create different subscribers based on topic_type
 49        if self.topic_type == "left_rgb_image":
 50            self.topic_name = "/aima/hal/sensor/stereo_head_front_left/rgb_image"
 51            self.sub_image = self.create_subscription(
 52                Image, self.topic_name, self.cb_image, qos)
 53            self.get_logger().info(
 54                f"✅ Subscribing Left RGB Image: {self.topic_name}")
 55            if self.dump_video_path:
 56                self.get_logger().info(
 57                    f"📝 Will dump received images to video: {self.dump_video_path}")
 58
 59        elif self.topic_type == "left_rgb_image_compressed":
 60            self.topic_name = "/aima/hal/sensor/stereo_head_front_left/rgb_image/compressed"
 61            self.sub_compressed = self.create_subscription(
 62                CompressedImage, self.topic_name, self.cb_compressed, qos)
 63            self.get_logger().info(
 64                f"✅ Subscribing Left CompressedImage: {self.topic_name}")
 65
 66        elif self.topic_type == "left_camera_info":
 67            self.topic_name = "/aima/hal/sensor/stereo_head_front_left/camera_info"
 68            # CameraInfo subscription must use reliable + transient_local QoS to receive historical messages (even if only one frame is published)
 69            camera_qos = QoSProfile(
 70                reliability=QoSReliabilityPolicy.RELIABLE,
 71                history=QoSHistoryPolicy.KEEP_LAST,
 72                depth=1,
 73                durability=QoSDurabilityPolicy.TRANSIENT_LOCAL
 74            )
 75            self.sub_camerainfo = self.create_subscription(
 76                CameraInfo, self.topic_name, self.cb_camerainfo, camera_qos)
 77            self.get_logger().info(
 78                f"✅ Subscribing Left CameraInfo (with transient_local): {self.topic_name}")
 79
 80        elif self.topic_type == "right_rgb_image":
 81            self.topic_name = "/aima/hal/sensor/stereo_head_front_right/rgb_image"
 82            self.sub_image = self.create_subscription(
 83                Image, self.topic_name, self.cb_image, qos)
 84            self.get_logger().info(
 85                f"✅ Subscribing Right RGB Image: {self.topic_name}")
 86            if self.dump_video_path:
 87                self.get_logger().info(
 88                    f"📝 Will dump received images to video: {self.dump_video_path}")
 89
 90        elif self.topic_type == "right_rgb_image_compressed":
 91            self.topic_name = "/aima/hal/sensor/stereo_head_front_right/rgb_image/compressed"
 92            self.sub_compressed = self.create_subscription(
 93                CompressedImage, self.topic_name, self.cb_compressed, qos)
 94            self.get_logger().info(
 95                f"✅ Subscribing Right CompressedImage: {self.topic_name}")
 96
 97        elif self.topic_type == "right_camera_info":
 98            self.topic_name = "/aima/hal/sensor/stereo_head_front_right/camera_info"
 99            # CameraInfo subscription must use reliable + transient_local QoS to receive historical messages (even if only one frame is published)
100            camera_qos = QoSProfile(
101                reliability=QoSReliabilityPolicy.RELIABLE,
102                history=QoSHistoryPolicy.KEEP_LAST,
103                depth=1,
104                durability=QoSDurabilityPolicy.TRANSIENT_LOCAL
105            )
106            self.sub_camerainfo = self.create_subscription(
107                CameraInfo, self.topic_name, self.cb_camerainfo, camera_qos)
108            self.get_logger().info(
109                f"✅ Subscribing Right CameraInfo (with transient_local): {self.topic_name}")
110
111        else:
112            self.get_logger().error(f"Unknown topic_type: {self.topic_type}")
113            raise ValueError("Unknown topic_type")
114
115        # Internal state
116        self.last_print = self.get_clock().now()
117        self.print_allowed = False
118        self.arrivals = deque()
119
120    def update_arrivals(self):
121        """Calculate received FPS"""
122        now = self.get_clock().now()
123        self.arrivals.append(now)
124        while self.arrivals and (now - self.arrivals[0]).nanoseconds * 1e-9 > 1.0:
125            self.arrivals.popleft()
126
127    def get_fps(self):
128        """Get FPS"""
129        return len(self.arrivals)
130
131    def should_print(self, master=True):
132        """Control print frequency"""
133        if not master:
134            return self.print_allowed
135        now = self.get_clock().now()
136        if (now - self.last_print).nanoseconds * 1e-9 >= 1.0:
137            self.last_print = now
138            self.print_allowed = True
139        else:
140            self.print_allowed = False
141        return self.print_allowed
142
143    def cb_image(self, msg: Image):
144        """Image callback (Left/Right camera RGB image)"""
145        self.update_arrivals()
146
147        if self.should_print():
148            stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
149            self.get_logger().info(
150                f"📸 {self.topic_type} received\n"
151                f"  • frame_id:        {msg.header.frame_id}\n"
152                f"  • stamp (sec):     {stamp_sec:.6f}\n"
153                f"  • encoding:        {msg.encoding}\n"
154                f"  • size (WxH):      {msg.width} x {msg.height}\n"
155                f"  • step (bytes/row):{msg.step}\n"
156                f"  • is_bigendian:    {msg.is_bigendian}\n"
157                f"  • recv FPS (1s):   {self.get_fps():.1f}"
158            )
159
160        # Only RGB images support video dump
161        if (self.topic_type in ["left_rgb_image", "right_rgb_image"]) and self.dump_video_path:
162            self.dump_image_to_video(msg)
163
164    def cb_compressed(self, msg: CompressedImage):
165        """CompressedImage callback (Left/Right camera RGB compressed image)"""
166        self.update_arrivals()
167
168        if self.should_print():
169            stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
170            self.get_logger().info(
171                f"🗜️  {self.topic_type} received\n"
172                f"  • frame_id:        {msg.header.frame_id}\n"
173                f"  • stamp (sec):     {stamp_sec:.6f}\n"
174                f"  • format:          {msg.format}\n"
175                f"  • data size:       {len(msg.data)}\n"
176                f"  • recv FPS (1s):   {self.get_fps():.1f}"
177            )
178
179    def cb_camerainfo(self, msg: CameraInfo):
180        """CameraInfo callback (Left/Right camera intrinsic parameters)"""
181        # Camera info will only receive one frame, print it directly
182        stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
183
184        # Format D array
185        d_str = ", ".join([f"{d:.6f}" for d in msg.d])
186
187        # Format K matrix
188        k_str = ", ".join([f"{k:.6f}" for k in msg.k])
189
190        # Format P matrix
191        p_str = ", ".join([f"{p:.6f}" for p in msg.p])
192
193        self.get_logger().info(
194            f"📷 {self.topic_type} received\n"
195            f"  • frame_id:        {msg.header.frame_id}\n"
196            f"  • stamp (sec):     {stamp_sec:.6f}\n"
197            f"  • width x height:  {msg.width} x {msg.height}\n"
198            f"  • distortion_model:{msg.distortion_model}\n"
199            f"  • D: [{d_str}]\n"
200            f"  • K: [{k_str}]\n"
201            f"  • P: [{p_str}]\n"
202            f"  • binning_x: {msg.binning_x}\n"
203            f"  • binning_y: {msg.binning_y}\n"
204            f"  • roi: {{ x_offset: {msg.roi.x_offset}, y_offset: {msg.roi.y_offset}, height: {msg.roi.height}, width: {msg.roi.width}, do_rectify: {msg.roi.do_rectify} }}"
205        )
206
207    def dump_image_to_video(self, msg: Image):
208        """Video dump is only supported for RGB images"""
209        # You can add video recording functionality here
210        # Simplified in the Python version, only logs instead
211        if self.should_print(master=False):
212            self.get_logger().info(f"📝 Video dump not implemented in Python version")
213
214
215def main(args=None):
216    rclpy.init(args=args)
217    try:
218        node = StereoCameraTopicEcho()
219        rclpy.spin(node)
220    except KeyboardInterrupt:
221        pass
222    except Exception as e:
223        print(f"Error: {e}")
224    finally:
225        if 'node' in locals():
226            node.destroy_node()
227        rclpy.shutdown()
228
229
230if __name__ == '__main__':
231    main()
```

**Usage:**

1. Subscribe to left camera RGB image:

   ```
   ros2 run py_examples echo_camera_stereo --ros-args -p topic_type:=left_rgb_image
   ```
2. Subscribe to right camera RGB image:

   ```
   ros2 run py_examples echo_camera_stereo --ros-args -p topic_type:=right_rgb_image
   ```
3. Subscribe to left camera intrinsics:

   ```
   ros2 run py_examples echo_camera_stereo --ros-args -p topic_type:=left_camera_info
   ```
4. Record left camera video:

   ```
   # You can change dump_video_path to another path; ensure the directory exists before saving
   ros2 run py_examples echo_camera_stereo --ros-args -p topic_type:=left_rgb_image -p dump_video_path:=$PWD/left_camera.avi
   ```

### Head rear monocular camera data subscription

**This example uses `echo_camera_head_rear` to subscribe to `/aima/hal/sensor/rgb_head_rear/` and receive the robot’s head rear monocular camera data, supporting RGB images, compressed images, and camera intrinsics.**

**Features:**

- Supports head rear camera data subscription
- Real-time FPS statistics and data display
- Supports RGB image video recording with/without obstructed area masked (TBD, see [C++ examples](Cpp.html#cpp-echo-camera-head-rear))
- Configurable topic type selection

**Supported data types:**

- `rgb_image`: RGB image (sensor\_msgs/Image)
- `rgb_image_compressed`: Compressed RGB image (sensor\_msgs/CompressedImage)
- `camera_info`: Camera intrinsic parameters (sensor\_msgs/CameraInfo)

```
  1#!/usr/bin/env python3
  2"""
  3Head rear monocular camera multi-topic subscription example
  4
  5Supports selecting the topic type to subscribe via startup parameter --ros-args -p topic_type:=<type>:
  6  - rgb_image: RGB image (sensor_msgs/Image)
  7  - rgb_image_compressed: RGB compressed image (sensor_msgs/CompressedImage)
  8  - camera_info: Camera intrinsic parameters (sensor_msgs/CameraInfo)
  9
 10Example:
 11  ros2 run py_examples echo_camera_head_rear --ros-args -p topic_type:=rgb_image
 12  ros2 run py_examples echo_camera_head_rear --ros-args -p topic_type:=rgb_image_compressed
 13  ros2 run py_examples echo_camera_head_rear --ros-args -p topic_type:=camera_info
 14
 15Default topic_type is rgb_image
 16"""
 17
 18import rclpy
 19from rclpy.node import Node
 20from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSDurabilityPolicy, QoSHistoryPolicy
 21from sensor_msgs.msg import Image, CompressedImage, CameraInfo
 22from collections import deque
 23import time
 24import os
 25import cv2
 26
 27
 28class HeadRearCameraTopicEcho(Node):
 29    def __init__(self):
 30        super().__init__('head_rear_camera_topic_echo')
 31
 32        # Select the topic type to subscribe
 33        self.declare_parameter('topic_type', 'rgb_image')
 34        self.declare_parameter('dump_video_path', '')
 35        self.declare_parameter('with_mask', False)
 36
 37        self.topic_type = self.get_parameter('topic_type').value
 38        self.dump_video_path = self.get_parameter('dump_video_path').value
 39        self.with_mask = self.get_parameter('with_mask').value
 40        self.mask_image = None
 41
 42        # Set QoS parameters - use sensor data QoS
 43        qos = QoSProfile(
 44            reliability=QoSReliabilityPolicy.BEST_EFFORT,
 45            history=QoSHistoryPolicy.KEEP_LAST,
 46            depth=5,
 47            durability=QoSDurabilityPolicy.VOLATILE
 48        )
 49
 50        if self.with_mask and self.dump_video_path:
 51            mask_path = os.path.join(os.path.dirname(
 52                __file__), 'data', 'rgb_head_rear_mask.png')
 53            self.mask_image = cv2.imread(mask_path, cv2.IMREAD_GRAYSCALE)
 54            if self.mask_image is None:
 55                self.get_logger().error(
 56                    f"Failed to load mask file: {mask_path}")
 57                raise ValueError("Failed to load mask file")
 58
 59        # Create different subscribers based on topic_type
 60        if self.topic_type == "rgb_image":
 61            self.topic_name = "/aima/hal/sensor/rgb_head_rear/rgb_image"
 62            self.sub_image = self.create_subscription(
 63                Image, self.topic_name, self.cb_image, qos)
 64            self.get_logger().info(
 65                f"✅ Subscribing RGB Image: {self.topic_name}")
 66            if self.dump_video_path:
 67                mask_state = "with mask" if self.with_mask else "without mask"
 68                self.get_logger().info(
 69                    f"📝 Will dump received images {mask_state} to video: {self.dump_video_path}")
 70
 71        elif self.topic_type == "rgb_image_compressed":
 72            self.topic_name = "/aima/hal/sensor/rgb_head_rear/rgb_image/compressed"
 73            self.sub_compressed = self.create_subscription(
 74                CompressedImage, self.topic_name, self.cb_compressed, qos)
 75            self.get_logger().info(
 76                f"✅ Subscribing CompressedImage: {self.topic_name}")
 77
 78        elif self.topic_type == "camera_info":
 79            self.topic_name = "/aima/hal/sensor/rgb_head_rear/camera_info"
 80            # CameraInfo subscription must use reliable + transient_local QoS to receive historical messages (even if only one frame is published)
 81            camera_qos = QoSProfile(
 82                reliability=QoSReliabilityPolicy.RELIABLE,
 83                history=QoSHistoryPolicy.KEEP_LAST,
 84                depth=1,
 85                durability=QoSDurabilityPolicy.TRANSIENT_LOCAL
 86            )
 87            self.sub_camerainfo = self.create_subscription(
 88                CameraInfo, self.topic_name, self.cb_camerainfo, camera_qos)
 89            self.get_logger().info(
 90                f"✅ Subscribing CameraInfo (with transient_local): {self.topic_name}")
 91
 92        else:
 93            self.get_logger().error(f"Unknown topic_type: {self.topic_type}")
 94            raise ValueError("Unknown topic_type")
 95
 96        # Internal state
 97        self.last_print = self.get_clock().now()
 98        self.print_allowed = False
 99        self.arrivals = deque()
100
101    def update_arrivals(self):
102        """Calculate received FPS"""
103        now = self.get_clock().now()
104        self.arrivals.append(now)
105        while self.arrivals and (now - self.arrivals[0]).nanoseconds * 1e-9 > 1.0:
106            self.arrivals.popleft()
107
108    def get_fps(self):
109        """Get FPS"""
110        return len(self.arrivals)
111
112    def should_print(self, master=True):
113        """Control print frequency"""
114        if not master:
115            return self.print_allowed
116        now = self.get_clock().now()
117        if (now - self.last_print).nanoseconds * 1e-9 >= 1.0:
118            self.last_print = now
119            self.print_allowed = True
120        else:
121            self.print_allowed = False
122        return self.print_allowed
123
124    def cb_image(self, msg: Image):
125        """Image callback (RGB image)"""
126        self.update_arrivals()
127
128        if self.should_print():
129            stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
130            self.get_logger().info(
131                f"📸 {self.topic_type} received\n"
132                f"  • frame_id:        {msg.header.frame_id}\n"
133                f"  • stamp (sec):     {stamp_sec:.6f}\n"
134                f"  • encoding:        {msg.encoding}\n"
135                f"  • size (WxH):      {msg.width} x {msg.height}\n"
136                f"  • step (bytes/row):{msg.step}\n"
137                f"  • is_bigendian:    {msg.is_bigendian}\n"
138                f"  • recv FPS (1s):   {self.get_fps():.1f}"
139            )
140
141        # Only RGB image supports video dump
142        if self.topic_type == "rgb_image" and self.dump_video_path:
143            self.dump_image_to_video(msg)
144
145    def cb_compressed(self, msg: CompressedImage):
146        """CompressedImage callback (RGB compressed image)"""
147        self.update_arrivals()
148
149        if self.should_print():
150            stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
151            self.get_logger().info(
152                f"🗜️  {self.topic_type} received\n"
153                f"  • frame_id:        {msg.header.frame_id}\n"
154                f"  • stamp (sec):     {stamp_sec:.6f}\n"
155                f"  • format:          {msg.format}\n"
156                f"  • data size:       {len(msg.data)}\n"
157                f"  • recv FPS (1s):   {self.get_fps():.1f}"
158            )
159
160    def cb_camerainfo(self, msg: CameraInfo):
161        """CameraInfo callback (camera intrinsic parameters)"""
162        # Camera info will only receive one frame, print it directly
163        stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
164
165        # Format D array
166        d_str = ", ".join([f"{d:.6f}" for d in msg.d])
167
168        # Format K matrix
169        k_str = ", ".join([f"{k:.6f}" for k in msg.k])
170
171        # Format P matrix
172        p_str = ", ".join([f"{p:.6f}" for p in msg.p])
173
174        self.get_logger().info(
175            f"📷 {self.topic_type} received\n"
176            f"  • frame_id:        {msg.header.frame_id}\n"
177            f"  • stamp (sec):     {stamp_sec:.6f}\n"
178            f"  • width x height:  {msg.width} x {msg.height}\n"
179            f"  • distortion_model:{msg.distortion_model}\n"
180            f"  • D: [{d_str}]\n"
181            f"  • K: [{k_str}]\n"
182            f"  • P: [{p_str}]\n"
183            f"  • binning_x: {msg.binning_x}\n"
184            f"  • binning_y: {msg.binning_y}\n"
185            f"  • roi: {{ x_offset: {msg.roi.x_offset}, y_offset: {msg.roi.y_offset}, height: {msg.roi.height}, width: {msg.roi.width}, do_rectify: {msg.roi.do_rectify} }}"
186        )
187
188    def dump_image_to_video(self, msg: Image):
189        """Video dump is only supported for RGB images"""
190        # You can add video recording functionality here
191        # Simplified in the Python version, only logs instead
192        # Note: Refer to cpp implementation, get cv images by cv_bridge first,
193        # then you can use 'image[self.mask_image == 0] = 0' to mask them and
194        # finally use VideoWriter to save them as video
195        if self.should_print(master=False):
196            self.get_logger().info(f"📝 Video dump not implemented in Python version")
197
198
199def main(args=None):
200    rclpy.init(args=args)
201    try:
202        node = HeadRearCameraTopicEcho()
203        rclpy.spin(node)
204    except KeyboardInterrupt:
205        pass
206    except Exception as e:
207        print(f"Error: {e}")
208    finally:
209        if 'node' in locals():
210            node.destroy_node()
211        rclpy.shutdown()
212
213
214if __name__ == '__main__':
215    main()
```

**Usage:**

1. Subscribe to RGB image data:

   ```
   ros2 run py_examples echo_camera_head_rear --ros-args -p topic_type:=rgb_image
   ```
2. Subscribe to compressed image data:

   ```
   ros2 run py_examples echo_camera_head_rear --ros-args -p topic_type:=rgb_image_compressed
   ```
3. Subscribe to camera intrinsics:

   ```
   ros2 run py_examples echo_camera_head_rear --ros-args -p topic_type:=camera_info
   ```
4. Record video:

   ```
   # You can change dump_video_path to another path; ensure the directory exists before saving
   ros2 run py_examples echo_camera_head_rear --ros-args -p topic_type:=rgb_image -p dump_video_path:=$PWD/rear_camera.avi
   ```

**Use cases:**

- Face recognition and tracking
- Object detection and recognition
- Visual SLAM
- Image processing and computer vision algorithm development
- Robot visual navigation

## 6.1.13 Head touch sensor data subscription

**This example uses echo\_head\_touch\_sensor**, which subscribes to the `/aima/hal/sensor/touch_head` topic to receive the robot’s touch sensor data on the head.

**Features:**

- The event data would change from “IDLE” to “TOUCH” when robot’s head touched

```
 1#!/usr/bin/env python3
 2"""
 3Head touch state subscription example
 4"""
 5
 6import rclpy
 7from rclpy.node import Node
 8from aimdk_msgs.msg import TouchState
 9
10
11class TouchStateSubscriber(Node):
12    def __init__(self):
13        super().__init__('touch_state_subscriber')
14
15        # touch event types
16        self.event_type_map = {
17            TouchState.UNKNOWN: "UNKNOWN",
18            TouchState.IDLE: "IDLE",
19            TouchState.TOUCH: "TOUCH",
20            TouchState.SLIDE: "SLIDE",
21            TouchState.PAT_ONCE: "PAT_ONCE",
22            TouchState.PAT_TWICE: "PAT_TWICE",
23            TouchState.PAT_TRIPLE: "PAT_TRIPLE"
24        }
25
26        # create subscriber
27        self.subscription = self.create_subscription(
28            TouchState,
29            '/aima/hal/sensor/touch_head',
30            self.touch_callback,
31            10
32        )
33
34        self.get_logger().info(
35            'TouchState subscriber started, listening to /aima/hal/sensor/touch_head')
36
37    def touch_callback(self, msg):
38        event_str = self.event_type_map.get(
39            msg.event_type, f"INVALID({msg.event_type})")
40
41        self.get_logger().info(f'Timestamp: {msg.header.stamp.sec}.{msg.header.stamp.nanosec:09d}, '
42                               f'Event: {event_str} ({msg.event_type})')
43
44
45def main(args=None):
46    rclpy.init(args=args)
47    node = TouchStateSubscriber()
48    rclpy.spin(node)
49    node.destroy_node()
50    rclpy.shutdown()
51
52
53if __name__ == '__main__':
54    main()
```

**Usage:**

```
ros2 run py_examples echo_head_touch_sensor
```

**Example output:**

```
[INFO] [1769420383.315173538] [touch_state_subscriber]: Timestamp: 1769420394.129927670, Event: IDLE (1)
[INFO] [1769420383.324978563] [touch_state_subscriber]: Timestamp: 1769420394.139941215, Event: IDLE (1)
[INFO] [1769420383.335265681] [touch_state_subscriber]: Timestamp: 1769420394.149990634, Event: TOUCH (2)
[INFO] [1769420383.344826732] [touch_state_subscriber]: Timestamp: 1769420394.159926892, Event: TOUCH (2)
```

## 6.1.14 LiDAR data subscription

**This example uses echo\_lidar\_data**, which subscribes to the `/aima/hal/sensor/lidar_chest_front/` topic to receive the robot’s LiDAR data, supporting both point cloud and IMU data types.

**Features:**

- Supports LiDAR point cloud data subscription
- Supports LiDAR IMU data subscription
- Real-time FPS statistics and data display
- Configurable topic type selection
- Detailed data field information output

**Supported data types:**

- `PointCloud2`: LiDAR point cloud data (sensor\_msgs/PointCloud2)
- `Imu`: LiDAR IMU data (sensor\_msgs/Imu)

**Technical implementation:**

- Uses SensorDataQoS configuration (`BEST_EFFORT` + `VOLATILE`)
- Supports point cloud field parsing and visualization
- Supports IMU quaternion, angular velocity, and linear acceleration data
- Provides detailed debugging log output

**Use cases:**

- LiDAR data acquisition and analysis
- Point cloud data processing and visualization
- Robot navigation and localization
- SLAM algorithm development
- Environmental perception and mapping

```
  1#!/usr/bin/env python3
  2"""
  3Chest LiDAR data subscription example
  4
  5Supports subscribing to the following topics:
  6  1. /aima/hal/sensor/lidar_chest_front/lidar_pointcloud
  7     - Data type: sensor_msgs/PointCloud2
  8     - frame_id: lidar_chest_front
  9     - child_frame_id: /
 10     - Content: LiDAR point cloud data
 11  2. /aima/hal/sensor/lidar_chest_front/imu
 12     - Data type: sensor_msgs/Imu
 13     - frame_id: lidar_imu_chest_front
 14     - Content: LiDAR IMU data
 15
 16You can select the topic type to subscribe via startup parameter --ros-args -p topic_type:=<type>:
 17  - pointcloud: subscribe to LiDAR point cloud
 18  - imu: subscribe to LiDAR IMU
 19Default topic_type is pointcloud
 20
 21Examples:
 22  ros2 run py_examples echo_lidar_data --ros-args -p topic_type:=pointcloud
 23  ros2 run py_examples echo_lidar_data --ros-args -p topic_type:=imu
 24"""
 25
 26import rclpy
 27from rclpy.node import Node
 28from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
 29from sensor_msgs.msg import PointCloud2, Imu
 30from collections import deque
 31import time
 32
 33
 34class LidarChestEcho(Node):
 35    def __init__(self):
 36        super().__init__('lidar_chest_echo')
 37
 38        # Select the topic type to subscribe
 39        self.declare_parameter('topic_type', 'pointcloud')
 40        self.topic_type = self.get_parameter('topic_type').value
 41
 42        # SensorDataQoS: BEST_EFFORT + VOLATILE
 43        qos = QoSProfile(
 44            reliability=QoSReliabilityPolicy.BEST_EFFORT,
 45            history=QoSHistoryPolicy.KEEP_LAST,
 46            depth=5
 47        )
 48
 49        # Create different subscribers based on topic_type
 50        if self.topic_type == "pointcloud":
 51            self.topic_name = "/aima/hal/sensor/lidar_chest_front/lidar_pointcloud"
 52            self.sub_pointcloud = self.create_subscription(
 53                PointCloud2, self.topic_name, self.cb_pointcloud, qos)
 54            self.get_logger().info(
 55                f"✅ Subscribing LIDAR PointCloud2: {self.topic_name}")
 56
 57        elif self.topic_type == "imu":
 58            self.topic_name = "/aima/hal/sensor/lidar_chest_front/imu"
 59            self.sub_imu = self.create_subscription(
 60                Imu, self.topic_name, self.cb_imu, qos)
 61            self.get_logger().info(
 62                f"✅ Subscribing LIDAR IMU: {self.topic_name}")
 63
 64        else:
 65            self.get_logger().error(f"Unknown topic_type: {self.topic_type}")
 66            raise ValueError("Unknown topic_type")
 67
 68        # Internal state
 69        self.last_print = self.get_clock().now()
 70        self.arrivals = deque()
 71
 72    def update_arrivals(self):
 73        """Calculate received FPS"""
 74        now = self.get_clock().now()
 75        self.arrivals.append(now)
 76        while self.arrivals and (now - self.arrivals[0]).nanoseconds * 1e-9 > 1.0:
 77            self.arrivals.popleft()
 78
 79    def get_fps(self):
 80        """Get FPS"""
 81        return len(self.arrivals)
 82
 83    def should_print(self):
 84        """Control print frequency"""
 85        now = self.get_clock().now()
 86        if (now - self.last_print).nanoseconds * 1e-9 >= 1.0:
 87            self.last_print = now
 88            return True
 89        return False
 90
 91    def cb_pointcloud(self, msg: PointCloud2):
 92        """PointCloud2 callback (LiDAR point cloud)"""
 93        self.update_arrivals()
 94
 95        if self.should_print():
 96            stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
 97
 98            # Format fields info
 99            fields_str = " ".join(
100                [f"{f.name}({f.datatype})" for f in msg.fields])
101
102            self.get_logger().info(
103                f"🟢 LIDAR PointCloud2 received\n"
104                f"  • frame_id:        {msg.header.frame_id}\n"
105                f"  • stamp (sec):     {stamp_sec:.6f}\n"
106                f"  • width x height:  {msg.width} x {msg.height}\n"
107                f"  • point_step:      {msg.point_step}\n"
108                f"  • row_step:        {msg.row_step}\n"
109                f"  • fields:          {fields_str}\n"
110                f"  • is_bigendian:    {msg.is_bigendian}\n"
111                f"  • is_dense:        {msg.is_dense}\n"
112                f"  • data size:       {len(msg.data)}\n"
113                f"  • recv FPS (1s):   {self.get_fps():1.1f}"
114            )
115
116    def cb_imu(self, msg: Imu):
117        """IMU callback (LiDAR IMU)"""
118        self.update_arrivals()
119
120        if self.should_print():
121            stamp_sec = msg.header.stamp.sec + msg.header.stamp.nanosec * 1e-9
122
123            self.get_logger().info(
124                f"🟢 LIDAR IMU received\n"
125                f"  • frame_id:        {msg.header.frame_id}\n"
126                f"  • stamp (sec):     {stamp_sec:.6f}\n"
127                f"  • orientation:     [{msg.orientation.x:.6f}, {msg.orientation.y:.6f}, {msg.orientation.z:.6f}, {msg.orientation.w:.6f}]\n"
128                f"  • angular_velocity:[{msg.angular_velocity.x:.6f}, {msg.angular_velocity.y:.6f}, {msg.angular_velocity.z:.6f}]\n"
129                f"  • linear_accel:    [{msg.linear_acceleration.x:.6f}, {msg.linear_acceleration.y:.6f}, {msg.linear_acceleration.z:.6f}]\n"
130                f"  • recv FPS (1s):   {self.get_fps():.1f}"
131            )
132
133
134def main(args=None):
135    rclpy.init(args=args)
136    try:
137        node = LidarChestEcho()
138        rclpy.spin(node)
139    except KeyboardInterrupt:
140        pass
141    except Exception as e:
142        print(f"Error: {e}")
143    finally:
144        if 'node' in locals():
145            node.destroy_node()
146        rclpy.shutdown()
147
148
149if __name__ == '__main__':
150    main()
```

**Usage:**

```
# Subscribe to LiDAR point cloud data
ros2 run py_examples echo_lidar_data --ros-args -p topic_type:=pointcloud

# Subscribe to LiDAR IMU data
ros2 run py_examples echo_lidar_data --ros-args -p topic_type:=imu
```

**Example output:**

```
[INFO] [lidar_chest_echo]: ✅ Subscribing LIDAR PointCloud2: /aima/hal/sensor/lidar_chest_front/lidar_pointcloud
[INFO] [lidar_chest_echo]: 🟢 LIDAR PointCloud2 received
  • frame_id:        lidar_chest_front
  • stamp (sec):     1234567890.123456
  • width x height:  1 x 36000
  • point_step:      16
  • row_step:        16
  • fields:          x(7) y(7) z(7) intensity(7)
  • is_bigendian:    False
  • is_dense:        True
  • data size:       576000
  • recv FPS (1s):   10.0
```

## 6.1.15 Play video

**This example uses play\_video**. Before running the node, you must upload the video to the robot’s **Interaction Computing Unit (PC3)** (you may create a directory on it to store videos, e.g. /var/tmp/videos/), and then change the `video_path` in the node program to the path of the video you want to play.

Attention

**⚠️ Attention! The Interaction Computing Unit (PC3) is independent from the Development Computing Unit (PC2) where secondary development programs run. Audio and video files must be stored on the Interaction Computing Unit (IP: 10.0.1.42).**
**Audio and video files (and all parent directories up to root) must be readable by all users(new subdirectory under /var/tmp/ is recommended)**

**Function description** By calling the `PlayVideo` service, the robot can play a video file from a specified path on its screen. Please ensure the video file has been uploaded to the Interaction Computing Unit, otherwise playback will fail.

```
 1#!/usr/bin/env python3
 2
 3import rclpy
 4import rclpy.logging
 5from rclpy.node import Node
 6
 7from aimdk_msgs.srv import PlayVideo
 8
 9
10class PlayVideoClient(Node):
11    def __init__(self):
12        super().__init__('play_video_client')
13        self.client = self.create_client(
14            PlayVideo, '/face_ui_proxy/play_video')
15        self.get_logger().info('✅ PlayVideo client node created.')
16
17        # Wait for the service to become available
18        while not self.client.wait_for_service(timeout_sec=2.0):
19            self.get_logger().info('⏳ Service unavailable, waiting...')
20
21        self.get_logger().info('🟢 Service available, ready to send request.')
22
23    def send_request(self, video_path, mode, priority):
24        req = PlayVideo.Request()
25
26        req.video_path = video_path
27        req.mode = mode
28        req.priority = priority
29
30        # async call
31        self.get_logger().info(
32            f'📨 Sending request to play video: mode={mode} video={video_path}')
33        for i in range(8):
34            req.header.header.stamp = self.get_clock().now().to_msg()
35            future = self.client.call_async(req)
36            rclpy.spin_until_future_complete(self, future, timeout_sec=0.25)
37
38            if future.done():
39                break
40
41            # retry as remote peer is NOT handled well by ROS
42            self.get_logger().info(f'trying ... [{i}]')
43
44        resp = future.result()
45        if resp is None:
46            self.get_logger().error('❌ Service call not completed or timed out.')
47            return False
48
49        if resp.success:
50            self.get_logger().info(
51                f'✅ Request to play video recorded successfully: {resp.message}')
52            return True
53        else:
54            self.get_logger().error(
55                f'❌ Failed to record play-video request: {resp.message}')
56            return False
57
58
59def main(args=None):
60    rclpy.init(args=args)
61    node = None
62
63    try:
64        # video path and priority can be customized
65        video_path = "/agibot/data/home/agi/zhiyuan.mp4"
66        priority = 5
67        # input play mode
68        mode = int(input("Enter video play mode (1: play once, 2: loop): "))
69        if mode not in (1, 2):
70            raise ValueError(f'invalid mode {mode}')
71
72        node = PlayVideoClient()
73        node.send_request(video_path, mode, priority)
74    except KeyboardInterrupt:
75        pass
76    except Exception as e:
77        rclpy.logging.get_logger('main').error(
78            f'Program exited with exception: {e}')
79
80    if node:
81        node.destroy_node()
82    if rclpy.ok():
83        rclpy.shutdown()
84
85
86if __name__ == '__main__':
87    main()
```

## 6.1.16 Media file playback

**This example uses play\_media**, which enables playback of specified media files (such as audio files) through the node, supporting audio formats including WAV and MP3.

**Features:**

- Supports playback of multiple audio formats (WAV, MP3, etc.)
- Supports priority control with configurable playback priority
- Supports interruption mechanism to stop current playback
- Supports custom file paths and playback parameters
- Provides complete error handling and status feedback

**Technical implementation:**

- Uses the PlayMediaFile service for media file playback
- Supports priority level configuration (0–99)
- Supports interruption control (is\_interrupted parameter)
- Provides detailed playback status feedback
- Compatible with different response field formats

**Use cases:**

- Audio file playback and media control
- Voice prompts and sound effect playback
- Multimedia application development
- Robot interaction audio feedback

Attention

**⚠️ Attention! The Interaction Computing Unit (PC3) is independent from the Development Computing Unit (PC2) where secondary development programs run. Audio and video files must be stored on the Interaction Computing Unit (IP: 10.0.1.42).**
**Audio and video files (and all parent directories up to root) must be readable by all users(new subdirectory under /var/tmp/ is recommended)**

```
 1#!/usr/bin/env python3
 2
 3import sys
 4import rclpy
 5import rclpy.logging
 6from rclpy.node import Node
 7
 8from aimdk_msgs.srv import PlayMediaFile
 9from aimdk_msgs.msg import TtsPriorityLevel
10
11
12class PlayMediaClient(Node):
13    def __init__(self):
14        super().__init__('play_media_client')
15        self.client = self.create_client(
16            PlayMediaFile, '/aimdk_5Fmsgs/srv/PlayMediaFile')
17        self.get_logger().info('✅ PlayMedia client node created.')
18
19        # Wait for the service to become available
20        while not self.client.wait_for_service(timeout_sec=2.0):
21            self.get_logger().info('⏳ Service unavailable, waiting...')
22
23        self.get_logger().info('🟢 Service available, ready to send request.')
24
25    def send_request(self, media_path):
26        req = PlayMediaFile.Request()
27
28        req.media_file_req.file_name = media_path
29        req.media_file_req.domain = 'demo_client'       # required: caller domain
30        req.media_file_req.trace_id = 'demo'            # optional
31        req.media_file_req.is_interrupted = True        # interrupt same-priority
32        req.media_file_req.priority_weight = 0          # optional: 0~99
33        req.media_file_req.priority_level.value = TtsPriorityLevel.INTERACTION_L6
34
35        self.get_logger().info(
36            f'📨 Sending request to play media: {media_path}')
37        for i in range(8):
38            req.header.header.stamp = self.get_clock().now().to_msg()
39            future = self.client.call_async(req)
40            rclpy.spin_until_future_complete(self, future, timeout_sec=0.25)
41
42            if future.done():
43                break
44
45            # retry as remote peer is NOT handled well by ROS
46            self.get_logger().info(f'trying ... [{i}]')
47
48        resp = future.result()
49        if resp is None:
50            self.get_logger().error('❌ Service call not completed or timed out.')
51            return False
52
53        if resp.tts_resp.is_success:
54            self.get_logger().info('✅ Request to play media file recorded successfully.')
55            return True
56        else:
57            self.get_logger().error('❌ Failed to record play-media request.')
58            return False
59
60
61def main(args=None):
62    rclpy.init(args=args)
63    node = None
64
65    default_media = '/agibot/data/var/interaction/tts_cache/normal/demo.wav'
66    try:
67        if len(sys.argv) > 1:
68            media_path = sys.argv[1]
69        else:
70            media_path = input(
71                f'Enter media file path to play (default: {default_media}): ').strip()
72            if not media_path:
73                media_path = default_media
74
75        node = PlayMediaClient()
76        node.send_request(media_path)
77    except KeyboardInterrupt:
78        pass
79    except Exception as e:
80        rclpy.logging.get_logger('main').error(
81            f'Program exited with exception: {e}')
82
83    if node:
84        node.destroy_node()
85    if rclpy.ok():
86        rclpy.shutdown()
87
88
89if __name__ == '__main__':
90    main()
```

**Usage:**

```
# Play default audio file
ros2 run py_examples play_media

# Play a specified audio file
# Note: replace /path/to/your/audio_file.wav with the actual file path on the interaction unit
ros2 run py_examples play_media /path/to/your/audio_file.wav

# Play a TTS cached file
ros2 run py_examples play_media /agibot/data/var/interaction/tts_cache/normal/demo.wav
```

**Example output:**

```
[INFO] [play_media_file_client_min]: Waiting for service: /aimdk_5Fmsgs/srv/PlayMediaFile
[INFO] [play_media_file_client_min]: ✅ Media file playback request succeeded
```

**Notes:**

- Ensure the audio file path is correct and the file exists
- Supported file formats: WAV, MP3, etc.
- Priority settings affect playback queue order
- Interruption feature can stop the currently playing audio
- The program includes complete exception handling mechanisms

## 6.1.17 TTS (Text-to-Speech)

**This example uses play\_tts**, which enables the robot to speak the provided text through the node. Users can input different text according to various scenarios.

**Features:**

- Supports command-line parameters and interactive input
- Includes complete service availability checks and error handling
- Supports priority control and interruption mechanism
- Provides detailed playback status feedback

**Core code**

```
 1#!/usr/bin/env python3
 2
 3import sys
 4import rclpy
 5import rclpy.logging
 6from rclpy.node import Node
 7
 8from aimdk_msgs.srv import PlayTts
 9from aimdk_msgs.msg import TtsPriorityLevel
10
11
12class PlayTTSClient(Node):
13    def __init__(self):
14        super().__init__('play_tts_client')
15
16        # fill in the actual service name
17        self.client = self.create_client(PlayTts, '/aimdk_5Fmsgs/srv/PlayTts')
18        self.get_logger().info('✅ PlayTts client node created.')
19
20        # Wait for the service to become available
21        while not self.client.wait_for_service(timeout_sec=2.0):
22            self.get_logger().info('⏳ Service unavailable, waiting...')
23
24        self.get_logger().info('🟢 Service available, ready to send request.')
25
26    def send_request(self, text):
27        req = PlayTts.Request()
28
29        req.tts_req.text = text
30        req.tts_req.domain = 'demo_client'   # required: caller domain
31        req.tts_req.trace_id = 'demo'        # optional: request id
32        req.tts_req.is_interrupted = True    # required: interrupt same-priority
33        req.tts_req.priority_weight = 0
34        req.tts_req.priority_level.value = 6
35
36        self.get_logger().info(f'📨 Sending request to play tts: text={text}')
37        for i in range(8):
38            req.header.header.stamp = self.get_clock().now().to_msg()
39            future = self.client.call_async(req)
40            rclpy.spin_until_future_complete(self, future, timeout_sec=0.25)
41
42            if future.done():
43                break
44
45            # retry as remote peer is NOT handled well by ROS
46            self.get_logger().info(f'trying ... [{i}]')
47
48        resp = future.result()
49        if resp is None:
50            self.get_logger().error('❌ Service call not completed or timed out.')
51            return False
52
53        if resp.tts_resp.is_success:
54            self.get_logger().info('✅ TTS sent successfully.')
55            return True
56        else:
57            self.get_logger().error('❌ Failed to send TTS.')
58            return False
59
60
61def main(args=None):
62    rclpy.init(args=args)
63    node = None
64
65    try:
66        # get text to speak
67        if len(sys.argv) > 1:
68            text = sys.argv[1]
69        else:
70            text = input('Enter text to speak: ')
71            if not text:
72                text = 'Hello, I am AgiBot X2.'
73
74        node = PlayTTSClient()
75        node.send_request(text)
76    except KeyboardInterrupt:
77        pass
78    except Exception as e:
79        rclpy.logging.get_logger('main').error(
80            f'Program exited with exception: {e}')
81
82    if node:
83        node.destroy_node()
84    if rclpy.ok():
85        rclpy.shutdown()
86
87
88if __name__ == '__main__':
89    main()
```

**Usage**

```
# Play text using command-line parameters (recommended)
ros2 run py_examples play_tts "Hello, I am the AgiBot X2 robot"

# Or run without parameters and the program will prompt for input
ros2 run py_examples play_tts
```

**Example output**

```
[INFO] [play_tts_client_min]: ✅ Speech playback request succeeded
```

**Notes**

- Ensure the TTS service is running properly
- Supports Chinese and English text playback
- Priority settings affect playback queue order
- Interruption feature can stop the currently playing speech

**Interface reference**

- Service: `/aimdk_5Fmsgs/srv/PlayTts`
- Message: `aimdk_msgs/srv/PlayTts`

## 6.1.18 Microphone data reception

**This example uses mic\_receiver**, which subscribes to the `/agent/process_audio_output` topic to receive noise-reduced audio data from the robot, supporting both internal and external microphone audio streams, and automatically saving complete speech segments as PCM files based on VAD (Voice Activity Detection) status.

**Features:**

- Supports simultaneous reception of multiple audio streams (internal microphone stream\_id=1, external microphone stream\_id=2)
- Automatically detects speech start, in-progress, and end based on VAD state
- Automatically saves complete speech segments as PCM files
- Stores recordings categorized by timestamp and audio stream
- Supports duration calculation and statistical information output
- Intelligent buffer management to prevent memory leaks
- Complete error handling and exception management
- Detailed debugging log output

**VAD state description:**

- `0`: No speech
- `1`: Speech start
- `2`: Speech in progress
- `3`: Speech end

**Technical implementation:**

- Supports saving PCM audio files (16 kHz, 16-bit, mono)
- Provides detailed log output and status monitoring
- Supports real-time audio stream processing and file saving

**Use cases:**

- Speech recognition and speech processing
- Audio data acquisition and analysis
- Real-time speech monitoring
- Audio quality evaluation
- Multi-microphone array data processing

```
  1#!/usr/bin/env python3
  2"""
  3Microphone data receiving example
  4
  5This example subscribes to the `/agent/process_audio_output` topic to receive the robot's
  6noise-suppressed audio data. It supports both the built-in microphone and the external
  7microphone audio streams, and automatically saves complete speech segments as PCM files
  8based on the VAD (Voice Activity Detection) state.
  9
 10Features:
 11- Supports receiving multiple audio streams at the same time (built-in mic stream_id=1, external mic stream_id=2)
 12- Automatically detects speech start / in-progress / end based on VAD state
 13- Automatically saves complete speech segments as PCM files
 14- Stores files categorized by timestamp and audio stream
 15- Supports audio duration calculation and logging
 16
 17VAD state description:
 18- 0: No speech
 19- 1: Speech start
 20- 2: Speech in progress
 21- 3: Speech end
 22"""
 23
 24import rclpy
 25from rclpy.node import Node
 26from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
 27from aimdk_msgs.msg import ProcessedAudioOutput, AudioVadStateType
 28import os
 29import time
 30from datetime import datetime
 31from collections import defaultdict
 32from typing import Dict, List
 33
 34
 35class AudioSubscriber(Node):
 36    def __init__(self):
 37        super().__init__('audio_subscriber')
 38
 39        # Audio buffers, stored separately by stream_id
 40        # stream_id -> buffer
 41        self.audio_buffers: Dict[int, List[bytes]] = defaultdict(list)
 42        self.recording_state: Dict[int, bool] = defaultdict(bool)
 43
 44        # Create audio output directory
 45        self.audio_output_dir = "audio_recordings"
 46        os.makedirs(self.audio_output_dir, exist_ok=True)
 47
 48        # VAD state name mapping
 49        self.vad_state_names = {
 50            0: "No speech",
 51            1: "Speech start",
 52            2: "Speech in progress",
 53            3: "Speech end"
 54        }
 55
 56        # Audio stream name mapping
 57        self.stream_names = {
 58            1: "Built-in microphone",
 59            2: "External microphone"
 60        }
 61
 62        # QoS settings
 63        # Note: deep queue to avoid missing data in a burst at start of VAD.
 64        qos = QoSProfile(
 65            history=QoSHistoryPolicy.KEEP_LAST,
 66            depth=500,
 67            reliability=QoSReliabilityPolicy.BEST_EFFORT
 68        )
 69
 70        # Create subscriber
 71        self.subscription = self.create_subscription(
 72            ProcessedAudioOutput,
 73            '/agent/process_audio_output',
 74            self.audio_callback,
 75            qos
 76        )
 77
 78        self.get_logger().info("Start subscribing to noise-suppressed audio data...")
 79
 80    def audio_callback(self, msg: ProcessedAudioOutput):
 81        """Audio data callback"""
 82        try:
 83            stream_id = msg.stream_id
 84            vad_state = msg.audio_vad_state.value
 85            audio_data = bytes(msg.audio_data)
 86
 87            self.get_logger().info(
 88                f"Received audio data: stream_id={stream_id}, "
 89                f"vad_state={vad_state}({self.vad_state_names.get(vad_state, 'Unknown state')}), "
 90                f"audio_size={len(audio_data)} bytes"
 91            )
 92
 93            self.handle_vad_state(stream_id, vad_state, audio_data)
 94
 95        except Exception as e:
 96            self.get_logger().error(
 97                f"Error while processing audio message: {str(e)}")
 98
 99    def handle_vad_state(self, stream_id: int, vad_state: int, audio_data: bytes):
100        """Handle VAD state changes"""
101        stream_name = self.stream_names.get(
102            stream_id, f"Unknown stream {stream_id}")
103        vad_name = self.vad_state_names.get(
104            vad_state, f"Unknown state {vad_state}")
105
106        self.get_logger().info(
107            f"[{stream_name}] VAD state: {vad_name} audio: {len(audio_data)} bytes"
108        )
109
110        # Speech start
111        if vad_state == 1:
112            self.get_logger().info("🎤 Speech start detected")
113            if not self.recording_state[stream_id]:
114                self.audio_buffers[stream_id].clear()
115                self.recording_state[stream_id] = True
116            if audio_data:
117                self.audio_buffers[stream_id].append(audio_data)
118
119        # Speech in progress
120        elif vad_state == 2:
121            self.get_logger().info("🔄 Speech in progress...")
122            if self.recording_state[stream_id] and audio_data:
123                self.audio_buffers[stream_id].append(audio_data)
124
125        # Speech end
126        elif vad_state == 3:
127            self.get_logger().info("✅ Speech end")
128            if self.recording_state[stream_id] and audio_data:
129                self.audio_buffers[stream_id].append(audio_data)
130
131            if self.recording_state[stream_id] and self.audio_buffers[stream_id]:
132                self.save_audio_segment(stream_id)
133            self.recording_state[stream_id] = False
134
135        # No speech
136        elif vad_state == 0:
137            if self.recording_state[stream_id]:
138                self.get_logger().info("⏹️ Reset recording state")
139                self.recording_state[stream_id] = False
140
141        # Print current buffer status
142        buffer_size = sum(len(chunk)
143                          for chunk in self.audio_buffers[stream_id])
144        recording = self.recording_state[stream_id]
145        self.get_logger().debug(
146            f"[Stream {stream_id}] Buffer size: {buffer_size} bytes, recording: {recording}"
147        )
148
149    def save_audio_segment(self, stream_id: int):
150        """Save audio segment"""
151        if not self.audio_buffers[stream_id]:
152            return
153
154        # Merge all audio data
155        audio_data = b''.join(self.audio_buffers[stream_id])
156
157        # Get current timestamp
158        now = datetime.now()
159        timestamp = now.strftime("%Y%m%d_%H%M%S_%f")[:-3]  # to milliseconds
160
161        # Create subdirectory by stream_id
162        stream_dir = os.path.join(self.audio_output_dir, f"stream_{stream_id}")
163        os.makedirs(stream_dir, exist_ok=True)
164
165        # Generate filename
166        stream_name = "internal_mic" if stream_id == 1 else "external_mic" if stream_id == 2 else f"stream_{stream_id}"
167        filename = f"{stream_name}_{timestamp}.pcm"
168        filepath = os.path.join(stream_dir, filename)
169
170        try:
171            # Save PCM file
172            with open(filepath, 'wb') as f:
173                f.write(audio_data)
174
175            self.get_logger().info(
176                f"Audio segment saved: {filepath} (size: {len(audio_data)} bytes)")
177
178            # Calculate audio duration (assuming 16 kHz, 16-bit, mono)
179            sample_rate = 16000
180            bits_per_sample = 16
181            channels = 1
182            bytes_per_sample = bits_per_sample // 8
183            total_samples = len(audio_data) // (bytes_per_sample * channels)
184            duration_seconds = total_samples / sample_rate
185
186            self.get_logger().info(
187                f"Audio duration: {duration_seconds:.2f} s ({total_samples} samples)")
188
189        except Exception as e:
190            self.get_logger().error(f"Failed to save audio file: {str(e)}")
191
192
193def main(args=None):
194    rclpy.init(args=args)
195    node = AudioSubscriber()
196
197    try:
198        node.get_logger().info("Listening to noise-suppressed audio data, press Ctrl+C to exit...")
199        rclpy.spin(node)
200    except KeyboardInterrupt:
201        node.get_logger().info("Interrupt signal received, exiting...")
202    finally:
203        node.destroy_node()
204        rclpy.shutdown()
205
206
207if __name__ == '__main__':
208    main()
```

**Usage:**

1. **Run the program:**

   ```
   # Build the Python package
   colcon build --packages-select py_examples

   # Run the microphone receiver and activate VAD with wake words
   ros2 run py_examples mic_receiver
   ```
2. **Directory structure:**

   - The `audio_recordings` directory will be created automatically after running the node
   - Audio files are stored by stream\_id:

     - `stream_1/`: Internal microphone audio
     - `stream_2/`: External microphone audio
3. **File naming format**: `{stream_name}_{timestamp}.pcm`

   - `internal_mic_20250909_133649_738.pcm` (internal microphone)
   - `external_mic_20250909_133650_123.pcm` (external microphone)
4. **Audio format**: 16 kHz, 16-bit, mono PCM
5. **Play saved PCM files:**

   ```
   # Play internal microphone recording
   aplay -r 16000 -f S16_LE -c 1 audio_recordings/stream_1/internal_mic_20250909_133649_738.pcm

   # Play external microphone recording
   aplay -r 16000 -f S16_LE -c 1 audio_recordings/stream_2/external_mic_20250909_133650_123.pcm
   ```
6. **Convert to WAV format (optional):**

   ```
   # Convert to WAV format using ffmpeg
   ffmpeg -f s16le -ar 16000 -ac 1 -i external_mic_20250909_133649_738.pcm output.wav
   ```
7. **Program control:**

   - Press `Ctrl`+`C` to safely exit the program
   - The program automatically handles audio stream start and end
   - Supports processing multiple audio streams simultaneously

**Example output:**

**Normal startup and operation:**

```
[INFO] Started subscribing to noise-reduced audio data...
[INFO] Received audio data: stream_id=1, vad_state=0(no speech), audio_size=0 bytes
[INFO] [Internal mic] VAD state: no speech Audio data: 0 bytes
[INFO] Received audio data: stream_id=2, vad_state=0(no speech), audio_size=0 bytes
[INFO] [External mic] VAD state: no speech Audio data: 0 bytes
```

**Speech start detected:**

```
[INFO] Received audio data: stream_id=2, vad_state=1(speech start), audio_size=320 bytes
[INFO] [External mic] VAD state: speech start Audio data: 320 bytes
[INFO] 🎤 Speech start detected
```

**Speech processing:**

```
[INFO] Received audio data: stream_id=2, vad_state=2(speech in progress), audio_size=320 bytes
[INFO] [External mic] VAD state: speech in progress Audio data: 320 bytes
[INFO] 🔄 Speech in progress...
[INFO] Received audio data: stream_id=2, vad_state=2(speech in progress), audio_size=320 bytes
[INFO] [External mic] VAD state: speech in progress Audio data: 320 bytes
[INFO] 🔄 Speech in progress...
```

**Speech end and save:**

```
[INFO] Received audio data: stream_id=2, vad_state=3(speech end), audio_size=320 bytes
[INFO] [External mic] VAD state: speech end Audio data: 320 bytes
[INFO] ✅ Speech ended
[INFO] Audio segment saved: audio_recordings/stream_2/external_mic_20250909_133649_738.pcm (size: 960 bytes)
[INFO] Audio duration: 0.06 seconds (480 samples)
```

**Simultaneous multi-stream processing:**

```
[INFO] Received audio data: stream_id=1, vad_state=1(speech start), audio_size=320 bytes
[INFO] [Internal mic] VAD state: speech start Audio data: 320 bytes
[INFO] 🎤 Speech start detected
[INFO] Received audio data: stream_id=2, vad_state=1(speech start), audio_size=320 bytes
[INFO] [External mic] VAD state: speech start Audio data: 320 bytes
[INFO] 🎤 Speech start detected
```

**Program exit:**

```
^C[INFO] Interrupt signal received, exiting...
[INFO] Program exited safely
```

**Notes:**

- The program supports processing multiple audio streams (internal and external microphones)
- Each audio stream has an independent buffer and recording state
- Audio files are automatically saved by timestamp and audio stream
- The program includes complete error handling mechanisms to ensure stable operation

## 6.1.19 Emoji (expression) control

**This example uses play\_emoji**, which enables the robot to display a specified expression. Users can select expressions from the available list. For the full expression list, refer to the [expression list](../Interface/interactor/screen.html#tbl-emotion-id)

```
 1#!/usr/bin/env python3
 2
 3import rclpy
 4import rclpy.logging
 5from rclpy.node import Node
 6
 7from aimdk_msgs.srv import PlayEmoji
 8
 9
10class PlayEmojiClient(Node):
11    def __init__(self):
12        super().__init__('play_emoji_client')
13        self.client = self.create_client(
14            PlayEmoji, '/face_ui_proxy/play_emoji')
15        self.get_logger().info('✅ PlayEmoji client node created.')
16
17        # Wait for the service to become available
18        while not self.client.wait_for_service(timeout_sec=2.0):
19            self.get_logger().info('⏳ Service unavailable, waiting...')
20
21        self.get_logger().info('🟢 Service available, ready to send request.')
22
23    def send_request(self, emoji: int, mode: int, priority: int):
24        req = PlayEmoji.Request()
25
26        req.emotion_id = int(emoji)
27        req.mode = int(mode)
28        req.priority = int(priority)
29
30        self.get_logger().info(
31            f'📨 Sending request to play emoji: id={emoji}, mode={mode}, priority={priority}')
32        for i in range(8):
33            req.header.header.stamp = self.get_clock().now().to_msg()
34            future = self.client.call_async(req)
35            rclpy.spin_until_future_complete(self, future, timeout_sec=0.25)
36
37            if future.done():
38                break
39
40            # retry as remote peer is NOT handled well by ROS
41            self.get_logger().info(f'trying ... [{i}]')
42
43        resp = future.result()
44        if resp is None:
45            self.get_logger().error('❌ Service call not completed or timed out.')
46            return False
47
48        if resp.success:
49            self.get_logger().info(
50                f'✅ Emoji played successfully: {resp.message}')
51            return True
52        else:
53            self.get_logger().error(f'❌ Failed to play emoji: {resp.message}')
54            return False
55
56
57def main(args=None):
58    rclpy.init(args=args)
59    node = None
60
61    # Interactive input, same as the original C++ version
62    try:
63        emotion = int(
64            input("Enter emoji ID: 1-blink, 60-bored, 70-abnormal, 80-sleeping, 90-happy ... 190-double angry, 200-adore: "))
65        mode = int(input("Enter play mode (1: play once, 2: loop): "))
66        if mode not in (1, 2):
67            raise ValueError("invalid mode")
68        priority = 10  # default priority
69
70        node = PlayEmojiClient()
71        node.send_request(emotion, mode, priority)
72    except KeyboardInterrupt:
73        pass
74    except Exception as e:
75        rclpy.logging.get_logger('main').error(
76            f'Program exited with exception: {e}')
77
78    if node:
79        node.destroy_node()
80    if rclpy.ok():
81        rclpy.shutdown()
82
83
84if __name__ == '__main__':
85    main()
```

## 6.1.20 LED light strip control

**Function description**: Demonstrates how to control the robot’s LED light strip, supporting multiple display modes and custom colors.

**Core code:**

```
  1#!/usr/bin/env python3
  2
  3import sys
  4import rclpy
  5import rclpy.logging
  6from rclpy.node import Node
  7
  8from aimdk_msgs.msg import CommonRequest
  9from aimdk_msgs.srv import LedStripCommand
 10
 11
 12class PlayLightsClient(Node):
 13    def __init__(self):
 14        super().__init__('play_lights_client')
 15
 16        # create service client
 17        self.client = self.create_client(
 18            LedStripCommand, '/aimdk_5Fmsgs/srv/LedStripCommand')
 19
 20        self.get_logger().info('✅ PlayLights client node created.')
 21
 22        # Wait for the service to become available
 23        while not self.client.wait_for_service(timeout_sec=2.0):
 24            self.get_logger().info('⏳ Service unavailable, waiting...')
 25
 26        self.get_logger().info('🟢 Service available, ready to send request.')
 27
 28    def send_request(self, led_mode, r, g, b):
 29        """Send LED control request"""
 30        # create request
 31        request = LedStripCommand.Request()
 32        request.led_strip_mode = led_mode
 33        request.r = r
 34        request.g = g
 35        request.b = b
 36
 37        # send request
 38        # Note: LED strip is slow to response (up to ~5s)
 39        self.get_logger().info(
 40            f'📨 Sending request to control led strip: mode={led_mode}, RGB=({r}, {g}, {b})')
 41        for i in range(4):
 42            request.request.header.stamp = self.get_clock().now().to_msg()
 43            future = self.client.call_async(request)
 44            rclpy.spin_until_future_complete(self, future, timeout_sec=5)
 45
 46            if future.done():
 47                break
 48
 49            # retry as remote peer is NOT handled well by ROS
 50            self.get_logger().info(f'trying ... [{i}]')
 51
 52        response = future.result()
 53        if response is None:
 54            self.get_logger().error('❌ Service call not completed or timed out.')
 55            return False
 56
 57        if response.status_code == 0:
 58            self.get_logger().info('✅ LED strip command sent successfully.')
 59            return True
 60        else:
 61            self.get_logger().error(
 62                f'❌ LED strip command failed with status: {response.status_code}')
 63            return False
 64
 65
 66def main(args=None):
 67    rclpy.init(args=args)
 68    node = None
 69
 70    try:
 71        # get command line args
 72        if len(sys.argv) > 4:
 73            # use CLI args
 74            led_mode = int(sys.argv[1])
 75            if led_mode not in (0, 1, 2, 3):
 76                raise ValueError("invalid mode")
 77            r = int(sys.argv[2])
 78            if r < 0 or r > 255:
 79                raise ValueError("invalid R value")
 80            g = int(sys.argv[3])
 81            if g < 0 or g > 255:
 82                raise ValueError("invalid G value")
 83            b = int(sys.argv[4])
 84            if b < 0 or b > 255:
 85                raise ValueError("invalid B value")
 86        else:
 87            # interactive input
 88            print("=== LED strip control example ===")
 89            print("Select LED strip mode:")
 90            print("0 - Steady on")
 91            print("1 - Breathing (4s cycle, sine brightness)")
 92            print("2 - Blinking (1s cycle, 0.5s on, 0.5s off)")
 93            print("3 - Flowing (2s cycle, light up from left to right)")
 94
 95            led_mode = int(input("Enter mode (0-3): "))
 96            if led_mode not in (0, 1, 2, 3):
 97                raise ValueError("invalid mode")
 98
 99            print("\nSet RGB color values (0-255):")
100            r = int(input("Red (R): "))
101            if r < 0 or r > 255:
102                raise ValueError("invalid R value")
103            g = int(input("Green (G): "))
104            if g < 0 or g > 255:
105                raise ValueError("invalid G value")
106            b = int(input("Blue (B): "))
107            if b < 0 or b > 255:
108                raise ValueError("invalid B value")
109
110        node = PlayLightsClient()
111        node.send_request(led_mode, r, g, b)
112    except KeyboardInterrupt:
113        pass
114    except Exception as e:
115        rclpy.logging.get_logger('main').error(
116            f'Program exited with exception: {e}')
117
118    if node:
119        node.destroy_node()
120    if rclpy.ok():
121        rclpy.shutdown()
122
123
124if __name__ == '__main__':
125    main()
```

**Usage instructions:**

```
# Build
colcon build --packages-select py_examples

# Run interactively
ros2 run py_examples play_lights

# Run with command-line parameters
ros2 run py_examples play_lights 1 255 0 0  # Mode 1, red
```

**Example output:**

```
=== LED Light Strip Control Example ===
Please select LED mode:
0 - Constant mode
1 - Breathing mode (4s cycle, sinusoidal brightness)
2 - Blinking mode (1s cycle, 0.5s on, 0.5s off)
3 - Flowing mode (2s cycle, lights activate from left to right)
Enter mode (0-3): 1

Please set RGB values (0-255):
Red component (R): 255
Green component (G): 0
Blue component (B): 0

Sending LED control command...
Mode: 1, Color: RGB(255, 0, 0)
✅ LED strip command sent successfully
```

**Technical features:**

- Supports four LED display modes
- Custom RGB color configuration
- Synchronous service invocation
- Command-line parameter support
- Input parameter validation
- User-friendly interactive interface
