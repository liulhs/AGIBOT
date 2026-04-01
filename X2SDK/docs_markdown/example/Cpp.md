# 6.2 C++ Interface Usage Example

**This section will guide you through implementing the functions listed in the index**

**Build & Run Instructions**

- Enter the top-level directory of the extracted SDK and execute the following commands

  ```
  source /opt/ros/humble/setup.bash
  colcon build
  source install/setup.bash
  ros2 run examples 'function name, e.g., get_mc_action'
  ```

> **📝 Code Notes**
>
> The full implementation includes complete mechanisms for error handling, signal handling, timeout handling, and more, ensuring the robustness of the program. **Please check/modify in the examples directory**

Caution

As standard ROS DO NOT handle cross-host service (request-response) well, **please refer to SDK examples to use open interfaces in a robust way (with protection mechanisms e.g. exception safety and retransmission)**

## 6.2.1 Get Robot Mode

Retrieve the robot’s current operating mode by calling the `GetMcAction` service, including the description, and status information.

[Motion Mode Definitions](../Interface/control_mod/modeswitch.html#tbl-mc-action)

```
  1#include "aimdk_msgs/srv/get_mc_action.hpp"
  2#include "aimdk_msgs/msg/common_request.hpp"
  3#include "aimdk_msgs/msg/response_header.hpp"
  4#include "rclcpp/rclcpp.hpp"
  5#include <chrono>
  6#include <memory>
  7#include <signal.h>
  8
  9// Global variable used for signal handling
 10std::shared_ptr<rclcpp::Node> g_node = nullptr;
 11
 12// Signal handler function
 13void signal_handler(int signal) {
 14  if (g_node) {
 15    RCLCPP_INFO(g_node->get_logger(), "Received signal %d, shutting down...",
 16                signal);
 17    g_node.reset();
 18  }
 19  rclcpp::shutdown();
 20  exit(signal);
 21}
 22
 23class GetMcActionClient : public rclcpp::Node {
 24public:
 25  GetMcActionClient() : Node("get_mc_action_client") {
 26
 27    client_ = this->create_client<aimdk_msgs::srv::GetMcAction>(
 28        "/aimdk_5Fmsgs/srv/GetMcAction"); // correct the service path
 29    RCLCPP_INFO(this->get_logger(), "✅ GetMcAction client node created.");
 30
 31    while (!client_->wait_for_service(std::chrono::seconds(2))) {
 32      RCLCPP_INFO(this->get_logger(), "⏳ Service unavailable, waiting...");
 33    }
 34    RCLCPP_INFO(this->get_logger(),
 35                "🟢 Service available, ready to send request.");
 36  }
 37
 38  void send_request() {
 39    try {
 40      auto request = std::make_shared<aimdk_msgs::srv::GetMcAction::Request>();
 41      request->request = aimdk_msgs::msg::CommonRequest();
 42
 43      RCLCPP_INFO(this->get_logger(), "📨 Sending request to get robot mode");
 44
 45      // Set a service call timeout
 46      const std::chrono::milliseconds timeout(250);
 47      for (int i = 0; i < 8; i++) {
 48        request->request.header.stamp = this->now();
 49        auto future = client_->async_send_request(request);
 50        auto retcode = rclcpp::spin_until_future_complete(shared_from_this(),
 51                                                          future, timeout);
 52        if (retcode != rclcpp::FutureReturnCode::SUCCESS) {
 53          // retry as remote peer is NOT handled well by ROS
 54          RCLCPP_INFO(this->get_logger(), "trying ... [%d]", i);
 55          continue;
 56        }
 57        // future.done
 58        auto response = future.get();
 59        RCLCPP_INFO(this->get_logger(), "✅ Robot mode get successfully.");
 60        RCLCPP_INFO(this->get_logger(), "Mode name: %s",
 61                    response->info.action_desc.c_str());
 62        RCLCPP_INFO(this->get_logger(), "Mode status: %d",
 63                    response->info.status.value);
 64        return;
 65      }
 66      RCLCPP_ERROR(this->get_logger(), "❌ Service call failed or timed out.");
 67    } catch (const std::exception &e) {
 68      RCLCPP_ERROR(this->get_logger(), "Exception occurred: %s", e.what());
 69    }
 70  }
 71
 72private:
 73  rclcpp::Client<aimdk_msgs::srv::GetMcAction>::SharedPtr client_;
 74};
 75
 76int main(int argc, char *argv[]) {
 77  try {
 78    rclcpp::init(argc, argv);
 79
 80    // Set up signal handlers
 81    signal(SIGINT, signal_handler);
 82    signal(SIGTERM, signal_handler);
 83
 84    // Create node
 85    g_node = std::make_shared<GetMcActionClient>();
 86    auto client = std::dynamic_pointer_cast<GetMcActionClient>(g_node);
 87    if (client) {
 88      client->send_request();
 89    }
 90
 91    // Clean up resources
 92    g_node.reset();
 93    rclcpp::shutdown();
 94
 95    return 0;
 96  } catch (const std::exception &e) {
 97    RCLCPP_ERROR(rclcpp::get_logger("main"),
 98                 "Program exited with exception: %s", e.what());
 99    return 1;
100  }
101}
```

**Usage Instructions**

```
ros2 run examples get_mc_action
```

**Output Example**

```
...
[INFO] [1764066631.021247791] [get_mc_action_client]: Current robot mode:
[INFO] [1764066631.021832667] [get_mc_action_client]: Mode name: PASSIVE_DEFAULT
[INFO] [1764066631.022396136] [get_mc_action_client]: Mode status: 100
```

**Interface Reference**

- Service: `/aimdk_5Fmsgs/srv/GetMcAction`
- Message: `aimdk_msgs/srv/GetMcAction`

## 6.2.2 Set Robot Mode

**This example uses the SetMcAction service.** After running the node, enter the corresponding field value of the mode in the terminal, and the robot will immediately switch to the appropriate [motion mode](../Interface/control_mod/modeswitch.html#tbl-mc-action).
**Before switching to the Stable Standing mode (`STAND_DEFAULT`), ensure the robot is standing and its feet are already on the ground.**
**The motion mode switching must follow its state transition digram, other transitions would be rejected**
**Locomotion Mode(`LOCOMOTION_DEFAULT`) and Stable Standing Mode(`STAND_DEFAULT`) are unified and will auto switch internally, so switching manually to the nearer one is enough**

```
  1#include "aimdk_msgs/srv/set_mc_action.hpp"
  2#include "aimdk_msgs/msg/common_response.hpp"
  3#include "aimdk_msgs/msg/common_state.hpp"
  4#include "aimdk_msgs/msg/mc_action.hpp"
  5#include "aimdk_msgs/msg/mc_action_command.hpp"
  6#include "aimdk_msgs/msg/request_header.hpp"
  7#include "rclcpp/rclcpp.hpp"
  8#include <chrono>
  9#include <iomanip>
 10#include <memory>
 11#include <signal.h>
 12#include <unordered_map>
 13#include <vector>
 14
 15// Global variable used for signal handling
 16std::shared_ptr<rclcpp::Node> g_node = nullptr;
 17
 18// Signal handler function
 19void signal_handler(int signal) {
 20  if (g_node) {
 21    RCLCPP_INFO(g_node->get_logger(), "Received signal %d, shutting down...",
 22                signal);
 23    g_node.reset();
 24  }
 25  rclcpp::shutdown();
 26  exit(signal);
 27}
 28
 29class SetMcActionClient : public rclcpp::Node {
 30public:
 31  SetMcActionClient() : Node("set_mc_action_client") {
 32
 33    client_ = this->create_client<aimdk_msgs::srv::SetMcAction>(
 34        "/aimdk_5Fmsgs/srv/SetMcAction");
 35    RCLCPP_INFO(this->get_logger(), "✅ SetMcAction client node created.");
 36
 37    // Wait for the service to become available
 38    while (!client_->wait_for_service(std::chrono::seconds(2))) {
 39      RCLCPP_INFO(this->get_logger(), "⏳ Service unavailable, waiting...");
 40    }
 41    RCLCPP_INFO(this->get_logger(),
 42                "🟢 Service available, ready to send request.");
 43  }
 44
 45  bool send_request(std::string &action_name) {
 46    try {
 47      auto request = std::make_shared<aimdk_msgs::srv::SetMcAction::Request>();
 48      request->header = aimdk_msgs::msg::RequestHeader();
 49
 50      // Set robot mode
 51      aimdk_msgs::msg::McActionCommand command;
 52      command.action_desc = action_name;
 53      request->command = command;
 54
 55      RCLCPP_INFO(this->get_logger(), "📨 Sending request to set robot mode: %s",
 56                  action_name.c_str());
 57
 58      // Set Service Call Timeout
 59      const std::chrono::milliseconds timeout(250);
 60      for (int i = 0; i < 8; i++) {
 61        request->header.stamp = this->now();
 62        auto future = client_->async_send_request(request);
 63        auto retcode = rclcpp::spin_until_future_complete(shared_from_this(),
 64                                                          future, timeout);
 65        if (retcode != rclcpp::FutureReturnCode::SUCCESS) {
 66          // retry as remote peer is NOT handled well by ROS
 67          RCLCPP_INFO(this->get_logger(), "trying ... [%d]", i);
 68          continue;
 69        }
 70        // future.done
 71        auto response = future.get();
 72        if (response->response.status.value ==
 73            aimdk_msgs::msg::CommonState::SUCCESS) {
 74          RCLCPP_INFO(this->get_logger(), "✅ Robot mode set successfully.");
 75          return true;
 76        } else {
 77          RCLCPP_ERROR(this->get_logger(), "❌ Failed to set robot mode: %s",
 78                       response->response.message.c_str());
 79          return false;
 80        }
 81      }
 82      RCLCPP_ERROR(this->get_logger(), "❌ Service call failed or timed out.");
 83      return false;
 84    } catch (const std::exception &e) {
 85      RCLCPP_ERROR(this->get_logger(), "Exception occurred: %s", e.what());
 86      return false;
 87    }
 88  }
 89
 90private:
 91  rclcpp::Client<aimdk_msgs::srv::SetMcAction>::SharedPtr client_;
 92};
 93
 94static std::unordered_map<std::string, std::vector<std::string>> g_action_info =
 95    {
 96        {"PASSIVE_DEFAULT", {"PD", "joints with zero torque"}},
 97        {"DAMPING_DEFAULT", {"DD", "joints in damping mode"}},
 98        {"JOINT_DEFAULT", {"JD", "Position Control Stand (joints locked)"}},
 99        {"STAND_DEFAULT", {"SD", "Stable Stand (auto-balance)"}},
100        {"LOCOMOTION_DEFAULT", {"LD", "locomotion mode (walk or run)"}},
101};
102
103int main(int argc, char *argv[]) {
104  try {
105    rclcpp::init(argc, argv);
106
107    // Set up signal handlers
108    signal(SIGINT, signal_handler);
109    signal(SIGTERM, signal_handler);
110
111    // Create node
112    g_node = std::make_shared<SetMcActionClient>();
113    auto client = std::dynamic_pointer_cast<SetMcActionClient>(g_node);
114
115    if (client) {
116      std::unordered_map<std::string, std::string> choices;
117      std::string motion;
118
119      // Prefer command-line argument; otherwise prompt user
120      if (argc > 1) {
121        motion = argv[1];
122        RCLCPP_INFO(g_node->get_logger(),
123                    "Using abbr of motion mode from cmdline: %s", argv[1]);
124      } else {
125        std::cout << std::left << std::setw(4) << "abbr"
126                  << " - " << std::setw(20) << "robot mode"
127                  << " : "
128                  << "description" << std::endl;
129        for (auto &it : g_action_info) {
130          std::cout << std::left << std::setw(4) << it.second[0] << " - "
131                    << std::setw(20) << it.first << " : " << it.second[1]
132                    << std::endl;
133        }
134        std::cout << "Enter abbr of motion mode:";
135        std::cin >> motion;
136      }
137      for (auto &it : g_action_info) {
138        choices[it.second[0]] = it.first;
139      }
140
141      auto m = choices.find(motion);
142      if (m != choices.end()) {
143        auto &action_name = m->second;
144        client->send_request(action_name);
145      } else {
146        RCLCPP_ERROR(g_node->get_logger(), "Invalid abbr of robot mode: %s",
147                     motion.c_str());
148      }
149    }
150
151    // Clean up resources
152    g_node.reset();
153    rclcpp::shutdown();
154
155    return 0;
156  } catch (const std::exception &e) {
157    RCLCPP_ERROR(rclcpp::get_logger("main"),
158                 "Program exited with exception: %s", e.what());
159    return 1;
160  }
161}
```

**Usage Instructions**

```
# Use command-line arguments to set the mode (recommended)
ros2 run py_examples set_mc_action JD  # Zero-Torque >> Position-Control Standing
ros2 run py_examples set_mc_action SD  # Ensure your robot's feet on the ground, Position-Control Standing >> Stable Standing
# Stable Standing >> Locomotion Mode. auto done internally, don't switch manually

# Or run without arguments and the program will prompt for input
ros2 run py_examples set_mc_action
```

**Output Example**

```
...
[INFO] [1764066567.502968540] [set_mc_action_client]: ✅ Robot mode set successfully.
```

**Notes**

- Ensure the robot’s feet are on the ground before switching to the `STAND_DEFAULT` mode
- Mode switching may take several seconds to complete

**Interface Reference**

- Service: `/aimdk_5Fmsgs/srv/SetMcAction`
- Message: `aimdk_msgs/srv/SetMcAction`

## 6.2.3 Set Robot Motion

**This example uses `preset_motion_client`**; after switching to Stable Stand Mode and starting the node, enter the corresponding field values to perform preset actions with the left (or right) hand such as handshake, raise hand, wave, or air kiss.

Available parameters can be found in the [Preset Motion Table](../Interface/control_mod/preset_motion.html#tbl-preset-motion)

```
  1#include "aimdk_msgs/msg/common_response.hpp"
  2#include "aimdk_msgs/msg/common_state.hpp"
  3#include "aimdk_msgs/msg/common_task_response.hpp"
  4#include "aimdk_msgs/msg/mc_control_area.hpp"
  5#include "aimdk_msgs/msg/mc_preset_motion.hpp"
  6#include "aimdk_msgs/msg/request_header.hpp"
  7#include "aimdk_msgs/srv/set_mc_preset_motion.hpp"
  8#include "rclcpp/rclcpp.hpp"
  9#include <chrono>
 10#include <memory>
 11#include <signal.h>
 12
 13std::shared_ptr<rclcpp::Node> g_node = nullptr;
 14
 15void signal_handler(int signal) {
 16  if (g_node) {
 17    RCLCPP_INFO(g_node->get_logger(), "Received signal %d, shutting down...",
 18                signal);
 19    g_node.reset();
 20  }
 21  rclcpp::shutdown();
 22  exit(signal);
 23}
 24
 25class PresetMotionClient : public rclcpp::Node {
 26public:
 27  PresetMotionClient() : Node("preset_motion_client") {
 28    const std::chrono::seconds timeout(8);
 29
 30    client_ = this->create_client<aimdk_msgs::srv::SetMcPresetMotion>(
 31        "/aimdk_5Fmsgs/srv/SetMcPresetMotion");
 32
 33    RCLCPP_INFO(this->get_logger(), "✅ SetMcPresetMotion client node created.");
 34
 35    // Wait for the service to become available
 36    while (!client_->wait_for_service(std::chrono::seconds(2))) {
 37      RCLCPP_INFO(this->get_logger(), "⏳ Service unavailable, waiting...");
 38    }
 39    RCLCPP_INFO(this->get_logger(),
 40                "🟢 Service available, ready to send request.");
 41  }
 42
 43  bool send_request(int area_id, int motion_id) {
 44    try {
 45      auto request =
 46          std::make_shared<aimdk_msgs::srv::SetMcPresetMotion::Request>();
 47      request->header = aimdk_msgs::msg::RequestHeader();
 48
 49      aimdk_msgs::msg::McPresetMotion motion;
 50      aimdk_msgs::msg::McControlArea area;
 51
 52      motion.value = motion_id; // Preset motion ID
 53      area.value = area_id;     // Control area ID
 54      request->motion = motion;
 55      request->area = area;
 56      request->interrupt = false; // Not interrupt current motion
 57
 58      RCLCPP_INFO(this->get_logger(),
 59                  "📨 Sending request to set preset motion: motion=%d, area=%d",
 60                  motion_id, area_id);
 61
 62      const std::chrono::milliseconds timeout(250);
 63      for (int i = 0; i < 8; i++) {
 64        request->header.stamp = this->now();
 65        auto future = client_->async_send_request(request);
 66        auto retcode = rclcpp::spin_until_future_complete(shared_from_this(),
 67                                                          future, timeout);
 68        if (retcode != rclcpp::FutureReturnCode::SUCCESS) {
 69          // retry as remote peer is NOT handled well by ROS
 70          RCLCPP_INFO(this->get_logger(), "trying ... [%d]", i);
 71          continue;
 72        }
 73        // future.done
 74        auto response = future.get();
 75        if (response->response.header.code == 0) {
 76          RCLCPP_INFO(this->get_logger(),
 77                      "✅ Preset motion set successfully: %lu",
 78                      response->response.task_id);
 79          return true;
 80        } else if (response->response.state.value ==
 81                   aimdk_msgs::msg::CommonState::RUNNING) {
 82          RCLCPP_INFO(this->get_logger(), "⏳ Preset motion executing: %lu",
 83                      response->response.task_id);
 84          return true;
 85        } else {
 86          RCLCPP_WARN(this->get_logger(), "❌ Failed to set preset motion: %lu",
 87                      response->response.task_id);
 88          return false;
 89        }
 90      }
 91      RCLCPP_ERROR(this->get_logger(), "❌ Service call failed or timed out.");
 92      return false;
 93    } catch (const std::exception &e) {
 94      RCLCPP_ERROR(this->get_logger(), "Exception occurred: %s", e.what());
 95      return false;
 96    }
 97  }
 98
 99private:
100  rclcpp::Client<aimdk_msgs::srv::SetMcPresetMotion>::SharedPtr client_;
101};
102
103int main(int argc, char *argv[]) {
104  try {
105    rclcpp::init(argc, argv);
106    signal(SIGINT, signal_handler);
107    signal(SIGTERM, signal_handler);
108
109    g_node = std::make_shared<PresetMotionClient>();
110    // Cast g_node (std::shared_ptr<rclcpp::Node>) to a derived
111    // PresetMotionClient pointer (std::shared_ptr<PresetMotionClient>)
112    auto client = std::dynamic_pointer_cast<PresetMotionClient>(g_node);
113
114    int area = 1;
115    int motion = 1003;
116    std::cout << "Enter arm area ID (1-left, 2-right): ";
117    std::cin >> area;
118    std::cout
119        << "Enter preset motion ID (1001-raise, 1002-wave, 1003-handshake, "
120           "1004-airkiss): ";
121    std::cin >> motion;
122    if (client) {
123      client->send_request(area, motion);
124    }
125
126    // Clean up resources
127    g_node.reset();
128    rclcpp::shutdown();
129
130    return 0;
131  } catch (const std::exception &e) {
132    RCLCPP_ERROR(rclcpp::get_logger("main"),
133                 "Program exited with exception: %s", e.what());
134    return 1;
135  }
136}
```

## 6.2.4 Gripper Control

**This example uses hand\_control. By publishing messages to the topic `/aima/hal/joint/hand/command`, you can control the movement of the gripper.**

Attention

***Warning ⚠️ : Before running this example, you must stop the native motion control module using `aima em stop-app mc` on the robot’s Motion Control Computing Unit (PC1) to obtain control authority. Ensure robot safety at all times.***

```
 1#include "aimdk_msgs/msg/hand_command.hpp"
 2#include "aimdk_msgs/msg/hand_command_array.hpp"
 3#include "aimdk_msgs/msg/hand_type.hpp"
 4#include "aimdk_msgs/msg/message_header.hpp"
 5#include "rclcpp/rclcpp.hpp"
 6#include <chrono>
 7#include <vector>
 8
 9class HandControl : public rclcpp::Node {
10public:
11  HandControl()
12      : Node("hand_control"), position_pairs_({
13                                  {1.0, 1.0},
14                                  {0.0, 0.0},
15                                  {0.5, 0.5},
16                                  {0.2, 0.8},
17                                  {0.7, 0.3},
18                              }),
19        current_index_(0) {
20    publisher_ = this->create_publisher<aimdk_msgs::msg::HandCommandArray>(
21        "/aima/hal/joint/hand/command", 10);
22
23    timer_ = this->create_wall_timer(
24        std::chrono::milliseconds(20), // 50Hz
25        std::bind(&HandControl::publish_hand_commands, this));
26
27    last_switch_time_ = now();
28    RCLCPP_INFO(this->get_logger(), "The hand control node has been started!");
29  }
30
31  void publish_hand_commands() {
32    // 1. Determine if it's time to switch parameters.
33    auto now_time = this->now();
34    if ((now_time - last_switch_time_).seconds() >= 2.0) {
35      current_index_ = (current_index_ + 1) % position_pairs_.size();
36      last_switch_time_ = now_time;
37      RCLCPP_INFO(this->get_logger(),
38                  "Switched to the next parameter group, index=%zu (left=%.2f, "
39                  "right=%.2f)",
40                  current_index_, position_pairs_[current_index_].first,
41                  position_pairs_[current_index_].second);
42    }
43
44    auto msg = std::make_unique<aimdk_msgs::msg::HandCommandArray>();
45    msg->header = aimdk_msgs::msg::MessageHeader();
46
47    float left_position = position_pairs_[current_index_].first;
48    float right_position = position_pairs_[current_index_].second;
49
50    aimdk_msgs::msg::HandCommand left_hands;
51    left_hands.name = "left_hand";
52    left_hands.position = left_position;
53    left_hands.velocity = 1.0;
54    left_hands.acceleration = 1.0;
55    left_hands.deceleration = 1.0;
56    left_hands.effort = 1.0;
57
58    aimdk_msgs::msg::HandCommand right_hands;
59    right_hands.name = "right_hand";
60    right_hands.position = right_position;
61    right_hands.velocity = 1.0;
62    right_hands.acceleration = 1.0;
63    right_hands.deceleration = 1.0;
64    right_hands.effort = 1.0;
65
66    msg->left_hands.push_back(left_hands);
67    msg->right_hands.push_back(right_hands);
68    msg->left_hand_type.value = 2;
69    msg->right_hand_type.value = 2;
70
71    publisher_->publish(std::move(msg));
72  }
73
74private:
75  rclcpp::Publisher<aimdk_msgs::msg::HandCommandArray>::SharedPtr publisher_;
76  rclcpp::TimerBase::SharedPtr timer_;
77
78  std::vector<std::pair<float, float>> position_pairs_;
79  size_t current_index_;
80
81  rclcpp::Time last_switch_time_;
82};
83
84int main(int argc, char *argv[]) {
85  rclcpp::init(argc, argv);
86  auto hand_control_node = std::make_shared<HandControl>();
87  rclcpp::spin(hand_control_node);
88  rclcpp::shutdown();
89  return 0;
90}
```

## 6.2.5 Dexterous Hand Control

**This example uses omnihand\_control. By publishing messages to the topic `/aima/hal/joint/hand/command`, you can control the movement of the omnihand.**

Attention

***Warning ⚠️ : Before running this example, you must stop the native motion control module using `aima em stop-app mc` on the robot’s Motion Control Computing Unit (PC1) to obtain control authority. Ensure robot safety at all times.***

```
  1#include <aimdk_msgs/msg/hand_command_array.hpp>
  2#include <chrono>
  3#include <cmath>
  4#include <memory>
  5#include <rclcpp/rclcpp.hpp>
  6
  7using namespace std::chrono_literals;
  8
  9class HandCommandPublisher : public rclcpp::Node {
 10public:
 11  HandCommandPublisher() : Node("hand_command_publisher") {
 12    publisher_ = this->create_publisher<aimdk_msgs::msg::HandCommandArray>(
 13        "/aima/hal/joint/hand/command", 10);
 14
 15    // Create a timer to publish once per second
 16    timer_ = this->create_wall_timer(
 17        1s, std::bind(&HandCommandPublisher::publish_command, this));
 18
 19    // Create a timer to publish once per second
 20    int target_finger = 0;
 21    int step_ = 1;
 22    bool increasing_ = true;
 23  }
 24
 25private:
 26  void publish_command() {
 27    auto message = aimdk_msgs::msg::HandCommandArray();
 28
 29    // Set hander
 30    message.header.stamp = this->now();
 31    message.header.frame_id = "hand_command";
 32
 33    // Set the hand type
 34    message.left_hand_type.value = 1;  // NIMBLE_HANDS
 35    message.right_hand_type.value = 1; // NIMBLE_HANDS
 36
 37    // Create left hand command array
 38    message.left_hands.resize(10);
 39
 40    // Set left thumb
 41    message.left_hands[0].name = "left_thumb";
 42    message.left_hands[0].position = 0.0;
 43    message.left_hands[0].velocity = 0.1;
 44    message.left_hands[0].acceleration = 0.0;
 45    message.left_hands[0].deceleration = 0.0;
 46    message.left_hands[0].effort = 0.0;
 47    // Set other left fingers
 48    for (int i = 1; i < 10; i++) {
 49      message.left_hands[i].name = "left_index";
 50      message.left_hands[i].position = 0.0;
 51      message.left_hands[i].velocity = 0.1;
 52      message.left_hands[i].acceleration = 0.0;
 53      message.left_hands[i].deceleration = 0.0;
 54      message.left_hands[i].effort = 0.0;
 55    }
 56
 57    // Create right hand command array
 58    message.right_hands.resize(10);
 59
 60    // Set right thumb
 61    message.right_hands[0].name = "right_thumb";
 62    message.right_hands[0].position = 0.0;
 63    message.right_hands[0].velocity = 0.1;
 64    message.right_hands[0].acceleration = 0.0;
 65    message.right_hands[0].deceleration = 0.0;
 66    message.right_hands[0].effort = 0.0;
 67
 68    // Set other right fingers (pinky)
 69    for (int i = 1; i < 10; i++) {
 70      message.right_hands[i].name = "right_pinky";
 71      message.right_hands[i].position = 0.0;
 72      message.right_hands[i].velocity = 0.1;
 73      message.right_hands[i].acceleration = 0.0;
 74      message.right_hands[i].deceleration = 0.0;
 75      message.right_hands[i].effort = 0.0;
 76    }
 77
 78    if (target_finger <= 10) {
 79      message.right_hands[target_finger].position = 0.8;
 80    } else {
 81      int target_finger_ = target_finger - 10;
 82      double target_position = 0.8;
 83      if (target_finger_ < 3) {
 84        // The three thumb motors on the left hand need their signs inverted to
 85        // mirror the right hand's motion
 86        target_position = -target_position;
 87      }
 88      message.left_hands[target_finger_].position = target_position;
 89    }
 90
 91    // Publish the message
 92    publisher_->publish(message);
 93
 94    RCLCPP_INFO(this->get_logger(),
 95                "Published hand command with target_finger: %d", target_finger);
 96
 97    update_target_finger();
 98  }
 99
100  void update_target_finger() {
101    if (increasing_) {
102      target_finger += step_;
103      if (target_finger >= 19) {
104        target_finger = 19;
105        increasing_ = false;
106      }
107    } else {
108      target_finger -= step_;
109      if (target_finger <= 0) {
110        target_finger = 0;
111        increasing_ = true;
112      }
113    }
114  }
115
116  rclcpp::Publisher<aimdk_msgs::msg::HandCommandArray>::SharedPtr publisher_;
117  rclcpp::TimerBase::SharedPtr timer_;
118
119  int target_finger = 0;
120  int step_ = 1;
121  bool increasing_ = true;
122};
123
124int main(int argc, char **argv) {
125  rclcpp::init(argc, argv);
126  auto node = std::make_shared<HandCommandPublisher>();
127  rclcpp::spin(node);
128  rclcpp::shutdown();
129  return 0;
130}
```

## 6.2.6 Register Secondary Development Input Source

**For versions after v0.7, an input source must be registered before controlling the MC. In this example, the `/aimdk_5Fmsgs/srv/SetMcInputSource` service is used to register the secondary development input source, so that the MC can recognize it. Only after registration can robot velocity control be performed.**

```
  1#include "aimdk_msgs/srv/set_mc_input_source.hpp"
  2#include "aimdk_msgs/msg/common_request.hpp"
  3#include "aimdk_msgs/msg/common_response.hpp"
  4#include "aimdk_msgs/msg/common_state.hpp"
  5#include "aimdk_msgs/msg/common_task_response.hpp"
  6#include "aimdk_msgs/msg/mc_input_action.hpp"
  7#include "rclcpp/rclcpp.hpp"
  8#include <chrono>
  9#include <memory>
 10#include <signal.h>
 11
 12std::shared_ptr<rclcpp::Node> g_node = nullptr;
 13
 14void signal_handler(int signal) {
 15  if (g_node) {
 16    RCLCPP_INFO(g_node->get_logger(), "Received signal %d, shutting down...",
 17                signal);
 18    g_node.reset();
 19  }
 20  rclcpp::shutdown();
 21  exit(signal);
 22}
 23
 24class McInputClient : public rclcpp::Node {
 25public:
 26  McInputClient() : Node("set_mc_input_source_client") {
 27    client_ = this->create_client<aimdk_msgs::srv::SetMcInputSource>(
 28        "/aimdk_5Fmsgs/srv/SetMcInputSource");
 29
 30    RCLCPP_INFO(this->get_logger(), "✅ SetMcInputSource client node created.");
 31
 32    // Wait for the service to become available
 33    while (!client_->wait_for_service(std::chrono::seconds(2))) {
 34      RCLCPP_INFO(this->get_logger(), "⏳ Service unavailable, waiting...");
 35    }
 36    RCLCPP_INFO(this->get_logger(),
 37                "🟢 Service available, ready to send request.");
 38  }
 39
 40  bool send_request() {
 41    try {
 42      auto request =
 43          std::make_shared<aimdk_msgs::srv::SetMcInputSource::Request>();
 44
 45      // Set request data
 46      request->action.value = 1001;         // Add new input source
 47      request->input_source.name = "node";  // Set message source
 48      request->input_source.priority = 40;  // Set priority
 49      request->input_source.timeout = 1000; // Set timeout (ms)
 50
 51      RCLCPP_INFO(this->get_logger(), "📨 Sending input source request: (ID=%d)",
 52                  request->action.value);
 53
 54      auto timeout = std::chrono::milliseconds(250);
 55      for (int i = 0; i < 8; i++) {
 56        // Set header timestamp
 57        request->request.header.stamp = this->now(); // use Node::now()
 58        auto future = client_->async_send_request(request);
 59        auto retcode = rclcpp::spin_until_future_complete(
 60            this->shared_from_this(), future, timeout);
 61        if (retcode != rclcpp::FutureReturnCode::SUCCESS) {
 62          // retry as remote peer is NOT handled well by ROS
 63          RCLCPP_INFO(this->get_logger(), "trying ... [%d]", i);
 64          continue;
 65        }
 66        // future.done
 67        auto response = future.get();
 68        auto code = response->response.header.code;
 69        if (code == 0) {
 70          RCLCPP_INFO(this->get_logger(),
 71                      "✅ Input source set successfully. task_id=%lu",
 72                      response->response.task_id);
 73          return true;
 74        } else {
 75          RCLCPP_ERROR(
 76              this->get_logger(),
 77              "❌ Input source set failed. ret_code=%ld, task_id=%lu "
 78              "(duplicated ADD? or MODIFY/ENABLE/DISABLE for unknown source?)",
 79              code, response->response.task_id);
 80          return false;
 81        }
 82      }
 83      RCLCPP_ERROR(this->get_logger(), "❌ Service call failed or timed out.");
 84      return false;
 85    } catch (const std::exception &e) {
 86      RCLCPP_ERROR(this->get_logger(), "Exception occurred: %s", e.what());
 87      return false;
 88    }
 89  }
 90
 91private:
 92  rclcpp::Client<aimdk_msgs::srv::SetMcInputSource>::SharedPtr client_;
 93};
 94
 95int main(int argc, char *argv[]) {
 96  try {
 97    rclcpp::init(argc, argv);
 98    signal(SIGINT, signal_handler);
 99    signal(SIGTERM, signal_handler);
100
101    g_node = std::make_shared<McInputClient>();
102    auto client = std::dynamic_pointer_cast<McInputClient>(g_node);
103
104    if (client) {
105      client->send_request();
106    }
107
108    g_node.reset();
109    rclcpp::shutdown();
110
111    return 0;
112  } catch (const std::exception &e) {
113    RCLCPP_ERROR(rclcpp::get_logger("main"),
114                 "Program terminated with exception: %s", e.what());
115    return 1;
116  }
117}
```

## 6.2.7 Get Current Input Source

**This example uses the GetCurrentInputSource service**, which is used to obtain information about the currently registered input source, including the input source name, priority, and timeout settings.

```
  1#include "aimdk_msgs/srv/get_current_input_source.hpp"
  2#include "aimdk_msgs/msg/common_request.hpp"
  3#include "aimdk_msgs/msg/response_header.hpp"
  4#include "rclcpp/rclcpp.hpp"
  5#include <chrono>
  6#include <memory>
  7#include <signal.h>
  8
  9// Global node object
 10std::shared_ptr<rclcpp::Node> g_node = nullptr;
 11
 12// Signal handler
 13void signal_handler(int signal) {
 14  if (g_node) {
 15    RCLCPP_INFO(g_node->get_logger(), "Received signal %d, shutting down...",
 16                signal);
 17    g_node.reset();
 18  }
 19  rclcpp::shutdown();
 20  exit(signal);
 21}
 22
 23// Client Class
 24class GetCurrentInputSourceClient : public rclcpp::Node {
 25public:
 26  GetCurrentInputSourceClient() : Node("get_current_input_source_client") {
 27
 28    client_ = this->create_client<aimdk_msgs::srv::GetCurrentInputSource>(
 29        "/aimdk_5Fmsgs/srv/GetCurrentInputSource");
 30
 31    RCLCPP_INFO(this->get_logger(),
 32                "✅ GetCurrentInputSource client node created.");
 33
 34    // Wait for the service to become available
 35    while (!client_->wait_for_service(std::chrono::seconds(2))) {
 36      RCLCPP_INFO(this->get_logger(), "⏳ Service unavailable, waiting...");
 37    }
 38    RCLCPP_INFO(this->get_logger(),
 39                "🟢 Service available, ready to send request.");
 40  }
 41
 42  void send_request() {
 43    try {
 44      auto request =
 45          std::make_shared<aimdk_msgs::srv::GetCurrentInputSource::Request>();
 46      request->request = aimdk_msgs::msg::CommonRequest();
 47
 48      RCLCPP_INFO(this->get_logger(),
 49                  "📨 Sending request to get current input source");
 50
 51      auto timeout = std::chrono::milliseconds(250);
 52
 53      for (int i = 0; i < 8; i++) {
 54        request->request.header.stamp = this->now();
 55        auto future = client_->async_send_request(request);
 56        auto retcode = rclcpp::spin_until_future_complete(
 57            this->shared_from_this(), future, timeout);
 58        if (retcode != rclcpp::FutureReturnCode::SUCCESS) {
 59          // retry as remote peer is NOT handled well by ROS
 60          RCLCPP_INFO(this->get_logger(), "trying ... [%d]", i);
 61          continue;
 62        }
 63        // future.done
 64        auto response = future.get();
 65        if (response->response.header.code == 0) {
 66          RCLCPP_INFO(this->get_logger(),
 67                      "✅ Current input source get successfully:");
 68          RCLCPP_INFO(this->get_logger(), "Name: %s",
 69                      response->input_source.name.c_str());
 70          RCLCPP_INFO(this->get_logger(), "Priority: %d",
 71                      response->input_source.priority);
 72          RCLCPP_INFO(this->get_logger(), "Timeout: %d",
 73                      response->input_source.timeout);
 74        } else {
 75          RCLCPP_WARN(this->get_logger(),
 76                      "❌ Current input source get failed, return code: %ld",
 77                      response->response.header.code);
 78        }
 79        return;
 80      }
 81      RCLCPP_ERROR(this->get_logger(), "❌ Service call failed or timed out.");
 82    } catch (const std::exception &e) {
 83      RCLCPP_ERROR(this->get_logger(), "Exception occurred: %s", e.what());
 84    }
 85  }
 86
 87private:
 88  rclcpp::Client<aimdk_msgs::srv::GetCurrentInputSource>::SharedPtr client_;
 89};
 90
 91int main(int argc, char *argv[]) {
 92  try {
 93    rclcpp::init(argc, argv);
 94
 95    signal(SIGINT, signal_handler);
 96    signal(SIGTERM, signal_handler);
 97
 98    g_node = std::make_shared<GetCurrentInputSourceClient>();
 99    auto client =
100        std::dynamic_pointer_cast<GetCurrentInputSourceClient>(g_node);
101
102    if (client) {
103      client->send_request();
104    }
105
106    g_node.reset();
107    rclcpp::shutdown();
108    return 0;
109  } catch (const std::exception &e) {
110    RCLCPP_ERROR(rclcpp::get_logger("main"),
111                 "Program exited with exception: %s", e.what());
112    return 1;
113  }
114}
```

**Usage Instructions**

```
# Get current input source information
ros2 run examples get_current_input_source
```

**Output Example**

```
[INFO] [get_current_input_source_client]: Current input source: node
[INFO] [get_current_input_source_client]: Priority: 40
[INFO] [get_current_input_source_client]: Timeout: 1000
```

**Notes**

- Ensure the GetCurrentInputSource service is running properly
- Valid information can only be obtained after an input source has been registered
- A status code of 0 indicates a successful query

## 6.2.8 Robot Locomotion Control

**This example uses mc\_locomotion\_velocity. The following example controls the robot’s walking by publishing to the `/aima/mc/locomotion/velocity` topic. For versions after v0.7, an input source must be registered before enabling velocity control (this example already includes input source registration). Refer to the code for detailed registration steps.**

Start the node after switching to Stable Standing Mode:

```
  1#include "aimdk_msgs/msg/mc_locomotion_velocity.hpp"
  2#include "aimdk_msgs/msg/common_request.hpp"
  3#include "aimdk_msgs/msg/common_response.hpp"
  4#include "aimdk_msgs/msg/common_state.hpp"
  5#include "aimdk_msgs/msg/common_task_response.hpp"
  6#include "aimdk_msgs/msg/mc_input_action.hpp"
  7#include "aimdk_msgs/msg/message_header.hpp"
  8#include "aimdk_msgs/srv/set_mc_input_source.hpp"
  9
 10#include "rclcpp/rclcpp.hpp"
 11#include <chrono>
 12#include <memory>
 13#include <signal.h>
 14#include <thread>
 15
 16class DirectVelocityControl : public rclcpp::Node {
 17public:
 18  DirectVelocityControl() : Node("direct_velocity_control") {
 19    // Create publisher
 20    publisher_ = this->create_publisher<aimdk_msgs::msg::McLocomotionVelocity>(
 21        "/aima/mc/locomotion/velocity", 10);
 22    // Create service client
 23    client_ = this->create_client<aimdk_msgs::srv::SetMcInputSource>(
 24        "/aimdk_5Fmsgs/srv/SetMcInputSource");
 25
 26    // Maximum speed limits
 27    max_forward_speed_ = 1.0; // m/s
 28    max_lateral_speed_ = 1.0; // m/s
 29    max_angular_speed_ = 1.0; // rad/s
 30    // Minimum speed limits (0 is also OK)
 31    min_forward_speed_ = 0.2; // m/s
 32    min_lateral_speed_ = 0.2; // m/s
 33    min_angular_speed_ = 0.1; // rad/s
 34
 35    RCLCPP_INFO(this->get_logger(), "Direct velocity control node started.");
 36  }
 37
 38  void start_publish() {
 39    if (timer_ != nullptr) {
 40      return;
 41    }
 42    // Set timer to periodically publish velocity messages (50Hz)
 43    timer_ = this->create_wall_timer(
 44        std::chrono::milliseconds(20),
 45        std::bind(&DirectVelocityControl::publish_velocity, this));
 46  }
 47
 48  bool register_input_source() {
 49    const std::chrono::seconds timeout(8);
 50    auto start_time = std::chrono::steady_clock::now();
 51    while (!client_->wait_for_service(std::chrono::seconds(2))) {
 52      if (std::chrono::steady_clock::now() - start_time > timeout) {
 53        RCLCPP_ERROR(this->get_logger(), "Waiting for service timed out");
 54        return false;
 55      }
 56      RCLCPP_INFO(this->get_logger(), "Waiting for input source service...");
 57    }
 58
 59    auto request =
 60        std::make_shared<aimdk_msgs::srv::SetMcInputSource::Request>();
 61    request->action.value = 1001;
 62    request->input_source.name = "node";
 63    request->input_source.priority = 40;
 64    request->input_source.timeout = 1000;
 65
 66    auto timeout2 = std::chrono::milliseconds(250);
 67
 68    for (int i = 0; i < 8; i++) {
 69      request->request.header.stamp = this->now();
 70      auto future = client_->async_send_request(request);
 71      auto retcode = rclcpp::spin_until_future_complete(
 72          this->shared_from_this(), future, timeout2);
 73      if (retcode != rclcpp::FutureReturnCode::SUCCESS) {
 74        // retry as remote peer is NOT handled well by ROS
 75        RCLCPP_INFO(this->get_logger(),
 76                    "trying to register input source... [%d]", i);
 77        continue;
 78      }
 79      // future.done
 80      auto response = future.get();
 81      int state = response->response.state.value;
 82      RCLCPP_INFO(this->get_logger(),
 83                  "Set input source succeeded: state=%d, task_id=%lu", state,
 84                  response->response.task_id);
 85      return true;
 86    }
 87    RCLCPP_ERROR(this->get_logger(), "Service call failed or timed out");
 88    return false;
 89  }
 90
 91  void publish_velocity() {
 92    auto msg = std::make_unique<aimdk_msgs::msg::McLocomotionVelocity>();
 93    msg->header = aimdk_msgs::msg::MessageHeader();
 94    msg->header.stamp = this->now();
 95    msg->source = "node"; // Set message source
 96    msg->forward_velocity = forward_velocity_;
 97    msg->lateral_velocity = lateral_velocity_;
 98    msg->angular_velocity = angular_velocity_;
 99
100    publisher_->publish(std::move(msg));
101    RCLCPP_INFO(this->get_logger(),
102                "Published velocity: Forward %.2f m/s, Lateral %.2f m/s, "
103                "Angular %.2f rad/s",
104                forward_velocity_, lateral_velocity_, angular_velocity_);
105  }
106
107  void clear_velocity() {
108    forward_velocity_ = 0.0;
109    lateral_velocity_ = 0.0;
110    angular_velocity_ = 0.0;
111  }
112
113  bool set_forward(double forward) {
114    if (abs(forward) < 0.005) {
115      forward_velocity_ = 0.0;
116      return true;
117    } else if ((abs(forward) > max_forward_speed_) ||
118               (abs(forward) < min_forward_speed_)) {
119      RCLCPP_ERROR(this->get_logger(), "input value out of range, exiting");
120      return false;
121    } else {
122      forward_velocity_ = forward;
123      return true;
124    }
125  }
126
127  bool set_lateral(double lateral) {
128    if (abs(lateral) < 0.005) {
129      lateral_velocity_ = 0.0;
130      return true;
131    } else if ((abs(lateral) > max_lateral_speed_) ||
132               (abs(lateral) < min_lateral_speed_)) {
133      RCLCPP_ERROR(this->get_logger(), "input value out of range, exiting");
134      return false;
135    } else {
136      lateral_velocity_ = lateral;
137      return true;
138    }
139  }
140
141  bool set_angular(double angular) {
142    if (abs(angular) < 0.005) {
143      angular_velocity_ = 0.0;
144      return true;
145    } else if ((abs(angular) > max_angular_speed_) ||
146               (abs(angular) < min_angular_speed_)) {
147      RCLCPP_ERROR(this->get_logger(), "input value out of range, exiting");
148      return false;
149    } else {
150      angular_velocity_ = angular;
151      return true;
152    }
153  }
154
155private:
156  rclcpp::Publisher<aimdk_msgs::msg::McLocomotionVelocity>::SharedPtr
157      publisher_;
158  rclcpp::Client<aimdk_msgs::srv::SetMcInputSource>::SharedPtr client_;
159  rclcpp::TimerBase::SharedPtr timer_;
160
161  double forward_velocity_;
162  double lateral_velocity_;
163  double angular_velocity_;
164
165  double max_forward_speed_;
166  double max_lateral_speed_;
167  double max_angular_speed_;
168
169  double min_forward_speed_;
170  double min_lateral_speed_;
171  double min_angular_speed_;
172};
173
174// Signal Processing
175std::shared_ptr<DirectVelocityControl> global_node = nullptr;
176void signal_handler(int sig) {
177  if (global_node) {
178    global_node->clear_velocity();
179    RCLCPP_INFO(global_node->get_logger(),
180                "Received signal %d: clearing velocity and shutting down", sig);
181  }
182  rclcpp::shutdown();
183  exit(sig);
184}
185
186int main(int argc, char *argv[]) {
187  rclcpp::init(argc, argv);
188  signal(SIGINT, signal_handler);
189  signal(SIGTERM, signal_handler);
190
191  global_node = std::make_shared<DirectVelocityControl>();
192  auto node = global_node;
193
194  if (!node->register_input_source()) {
195    RCLCPP_ERROR(node->get_logger(),
196                 "Input source registration failed, exiting");
197    global_node.reset();
198    rclcpp::shutdown();
199    return 1;
200  }
201
202  // get and check control values
203  // notice that mc has thresholds to start movement
204  double forward, lateral, angular;
205  std::cout << "Enter forward speed 0 or ±(0.2 ~ 1.0) m/s: ";
206  std::cin >> forward;
207  if (!node->set_forward(forward)) {
208    return 2;
209  }
210  std::cout << "Enter lateral speed 0 or ±(0.2 ~ 1.0) m/s: ";
211  std::cin >> lateral;
212  if (!node->set_lateral(lateral)) {
213    return 2;
214  }
215  std::cout << "Enter angular speed 0 or ±(0.1 ~ 1.0) rad/s: ";
216  std::cin >> angular;
217  if (!node->set_angular(angular)) {
218    return 2;
219  }
220
221  RCLCPP_INFO(node->get_logger(), "Setting velocity; moving for 5 seconds");
222
223  node->start_publish();
224
225  auto start_time = node->now();
226  while ((node->now() - start_time).seconds() < 5.0) {
227    rclcpp::spin_some(node);
228    std::this_thread::sleep_for(std::chrono::milliseconds(1));
229  }
230
231  node->clear_velocity();
232  RCLCPP_INFO(node->get_logger(), "5 seconds elapsed; robot stopped");
233
234  rclcpp::spin(node);
235  rclcpp::shutdown();
236  return 0;
237}
```

## 6.2.9 Joint Motor Control

**This example demonstrates how to use ROS2 and the Ruckig library to control the robot’s joint movements.**

Attention

***Warning ⚠️ : Before running this example, you must stop the native motion control module using `aima em stop-app mc` on the robot’s Motion Control Computing Unit (PC1) to obtain control authority. Ensure robot safety at all times.***

! This example directly controls the underlying motors (HAL layer). Before running the program, please verify that the joint safety limits in the code match the actual robot model, and ensure safety!

### Robot Joint Control Example

This example demonstrates how to control the robot’s joints using ROS2 and the Ruckig library. It includes the following features:

1. Joint model definition
2. Trajectory interpolation using Ruckig
3. Multi-joint coordinated control
4. Real-time position, velocity, and acceleration control

#### Dependencies

- ROS2
- Ruckig library
- aimdk\_msgs package

#### Build Instructions

1. Place the code in the `src` directory of your ROS2 workspace
2. Add the following to your CMakeLists.txt:

```
find_package(rclcpp REQUIRED)
find_package(aimdk_msgs REQUIRED)
find_package(ruckig REQUIRED)

add_executable(joint_control_example joint_control_example.cpp)
ament_target_dependencies(joint_control_example
  rclcpp
  aimdk_msgs
  ruckig
)
```

3. Add dependencies in package.xml:

```
<depend>rclcpp</depend>
<depend>aimdk_msgs</depend>
<depend>ruckig</depend>
```

#### Example Function Overview

1. Four controller nodes are created to control:

   - Legs × 2 (12 joints)
   - Waist × 1 (3 joints)
   - Arms × 2 (14 joints)
   - Head × 1 (2 joints)
2. Demonstrated features:

   - Make a designated joint oscillate between ±0.5 radians every 10 seconds
   - Generate smooth motion trajectories using the Ruckig library
   - Publish joint control commands in real time

#### Customization

2. Add new control logic:

   - Modify the `SetTargetPosition` function
   - Add new control callback functions
3. Adjust control frequency:

   - Modify the period of `control_timer_` (currently 2 ms)

```
  1#include <aimdk_msgs/msg/joint_command_array.hpp>
  2#include <aimdk_msgs/msg/joint_state_array.hpp>
  3#include <atomic>
  4#include <cstdlib>
  5#include <memory>
  6#include <rclcpp/rclcpp.hpp>
  7#include <ruckig/ruckig.hpp>
  8#include <signal.h>
  9#include <string>
 10#include <unordered_map>
 11#include <vector>
 12
 13/**
 14 * @brief Global variables and signal handling
 15 */
 16// Global variables to control program state
 17std::atomic<bool> g_running(true);
 18std::atomic<bool> g_emergency_stop(false);
 19
 20// Signal handler function
 21void signal_handler(int) {
 22  g_running = false;
 23  RCLCPP_INFO(rclcpp::get_logger("main"),
 24              "Received termination signal, shutting down...");
 25}
 26
 27/**
 28 * @brief Robot model definition
 29 */
 30enum class JointArea {
 31  HEAD,  // Head joints
 32  ARM,   // Arm joints
 33  WAIST, // Waist joints
 34  LEG,   // Leg joints
 35};
 36
 37/**
 38 * @brief Joint information structure
 39 */
 40struct JointInfo {
 41  std::string name;   // Joint name
 42  double lower_limit; // Joint angle lower limit
 43  double upper_limit; // Joint angle upper limit
 44  double kp;          // Position control gain
 45  double kd;          // Velocity control gain
 46};
 47
 48/**
 49 * @brief Robot model configuration
 50 * Contains parameters for all joints, enabling or disabling specific joints as
 51 * needed
 52 */
 53std::map<JointArea, std::vector<JointInfo>> robot_model = {
 54    {JointArea::LEG,
 55     {
 56         // Left leg joint configuration
 57         {"left_hip_pitch_joint", -2.704, 2.556, 40.0, 4.0},
 58         {"left_hip_roll_joint", -0.235, 2.906, 40.0, 4.0},
 59         {"left_hip_yaw_joint", -1.684, 3.430, 30.0, 3.0},
 60         {"left_knee_joint", 0.0000, 2.4073, 80.0, 8.0},
 61         {"left_ankle_pitch_joint", -0.803, 0.453, 40.0, 4.0},
 62         {"left_ankle_roll_joint", -0.2625, 0.2625, 20.0, 2.0},
 63         // Right leg joint configuration
 64         {"right_hip_pitch_joint", -2.704, 2.556, 40.0, 4.0},
 65         {"right_hip_roll_joint", -2.906, 0.235, 40.0, 4.0},
 66         {"right_hip_yaw_joint", -3.430, 1.684, 30.0, 3.0},
 67         {"right_knee_joint", 0.0000, 2.4073, 80.0, 8.0},
 68         {"right_ankle_pitch_joint", -0.803, 0.453, 40.0, 4.0},
 69         {"right_ankle_roll_joint", -0.2625, 0.2625, 20.0, 2.0},
 70     }},
 71
 72    {JointArea::WAIST,
 73     {
 74         // Waist joint configuration
 75         {"waist_yaw_joint", -3.43, 2.382, 20.0, 4.0},
 76         {"waist_pitch_joint", -0.314, 0.314, 20.0, 4.0},
 77         {"waist_roll_joint", -0.488, 0.488, 20.0, 4.0},
 78     }},
 79    {JointArea::ARM,
 80     {
 81         // Left arm joint configuration
 82         {"left_shoulder_pitch_joint", -3.08, 2.04, 20.0, 2.0},
 83         {"left_shoulder_roll_joint", -0.061, 2.993, 20.0, 2.0},
 84         {"left_shoulder_yaw_joint", -2.556, 2.556, 20.0, 2.0},
 85         {"left_elbow_joint", -2.3556, 0.0, 20.0, 2.0},
 86         {"left_wrist_yaw_joint", -2.556, 2.556, 20.0, 2.0},
 87         {"left_wrist_pitch_joint", -0.558, 0.558, 20.0, 2.0},
 88         {"left_wrist_roll_joint", -1.571, 0.724, 20.0, 2.0},
 89         // Right arm joint configuration
 90         {"right_shoulder_pitch_joint", -3.08, 2.04, 20.0, 2.0},
 91         {"right_shoulder_roll_joint", -2.993, 0.061, 20.0, 2.0},
 92         {"right_shoulder_yaw_joint", -2.556, 2.556, 20.0, 2.0},
 93         {"right_elbow_joint", -2.3556, 0.0000, 20.0, 2.0},
 94         {"right_wrist_yaw_joint", -2.556, 2.556, 20.0, 2.0},
 95         {"right_wrist_pitch_joint", -0.558, 0.558, 20.0, 2.0},
 96         {"right_wrist_roll_joint", -0.724, 1.571, 20.0, 2.0},
 97     }},
 98    {JointArea::HEAD,
 99     {
100         // Head joint configuration
101         {"head_yaw_joint", -0.366, 0.366, 20.0, 2.0},
102         {"head_pitch_joint", -0.3838, 0.3838, 20.0, 2.0},
103     }},
104};
105
106/**
107 * @brief Joint controller node class
108 * @tparam DOFs Degrees of freedom
109 * @tparam Area Joint area
110 */
111template <int DOFs, JointArea Area>
112class JointControllerNode : public rclcpp::Node {
113public:
114  /**
115   * @brief Constructor
116   * @param node_name Node name
117   * @param sub_topic Subscription topic name
118   * @param pub_topic Publication topic name
119   * @param qos QoS configuration
120   */
121  JointControllerNode(std::string node_name, std::string sub_topic,
122                      std::string pub_topic,
123                      rclcpp::QoS qos = rclcpp::SensorDataQoS())
124      : Node(node_name), ruckig(0.002) {
125    joint_info_ = robot_model[Area];
126    if (joint_info_.size() != DOFs) {
127      RCLCPP_ERROR(this->get_logger(), "Joint count mismatch.");
128      exit(1);
129    }
130
131    // Set motion constraints for Ruckig trajectory planner
132    for (int i = 0; i < DOFs; ++i) {
133      input.max_velocity[i] = 1.0;     // Max velocity limit
134      input.max_acceleration[i] = 1.0; // Max acceleration limit
135      input.max_jerk[i] = 25.0; // Max jerk (change of acceleration) limit
136    }
137
138    // Create joint state subscriber
139    sub_ = this->create_subscription<aimdk_msgs::msg::JointStateArray>(
140        sub_topic, qos,
141        std::bind(&JointControllerNode::JointStateCallback, this,
142                  std::placeholders::_1));
143
144    // Create joint command publisher
145    pub_ = this->create_publisher<aimdk_msgs::msg::JointCommandArray>(pub_topic,
146                                                                      qos);
147  }
148
149private:
150  // Ruckig trajectory planner variables
151  ruckig::Ruckig<DOFs> ruckig;          // Trajectory planner instance
152  ruckig::InputParameter<DOFs> input;   // Input parameters
153  ruckig::OutputParameter<DOFs> output; // Output parameters
154  bool ruckig_initialized_ = false;   // Trajectory planner initialization flag
155  std::vector<JointInfo> joint_info_; // Joint information list
156
157  // ROS communication variables
158  rclcpp::Subscription<aimdk_msgs::msg::JointStateArray>::SharedPtr
159      sub_; // State subscriber
160  rclcpp::Publisher<aimdk_msgs::msg::JointCommandArray>::SharedPtr
161      pub_; // Command publisher
162
163  /**
164   * @brief Joint state callback function
165   * @param msg Joint state message
166   */
167  void
168  JointStateCallback(const aimdk_msgs::msg::JointStateArray::SharedPtr msg) {
169    // Initialize trajectory planner on first state reception
170    if (!ruckig_initialized_) {
171      for (int i = 0; i < DOFs; ++i) {
172        input.current_position[i] = msg->joints[i].position;
173        input.current_velocity[i] = msg->joints[i].velocity;
174        input.current_acceleration[i] = 0.0;
175      }
176      ruckig_initialized_ = true;
177      RCLCPP_INFO(this->get_logger(),
178                  "Ruckig trajectory planner initialization complete");
179    }
180  }
181
182public:
183  /**
184   * @brief Set target joint position
185   * @param joint_name Joint name
186   * @param target_position Target position
187   * @return Whether the target position was successfully set
188   */
189  bool SetTargetPosition(std::string joint_name, double target_position) {
190    if (!ruckig_initialized_) {
191      RCLCPP_WARN(this->get_logger(),
192                  "Ruckig trajectory planner not initialized");
193      return false;
194    }
195
196    // Find target joint and set its position
197    int target_joint = -1;
198    for (int i = 0; i < DOFs; ++i) {
199      if (joint_info_[i].name == joint_name) {
200        // Check if target position is within limits
201        if (target_position < joint_info_[i].lower_limit ||
202            target_position > joint_info_[i].upper_limit) {
203          RCLCPP_ERROR(
204              this->get_logger(),
205              "Target position %.3f exceeds limit for joint %s [%.3f, %.3f]",
206              target_position, joint_name.c_str(), joint_info_[i].lower_limit,
207              joint_info_[i].upper_limit);
208          return false;
209        }
210        input.target_position[i] = target_position;
211        input.target_velocity[i] = 0.0;
212        input.target_acceleration[i] = 0.0;
213        target_joint = i;
214      } else {
215        input.target_position[i] = input.current_position[i];
216        input.target_velocity[i] = 0.0;
217        input.target_acceleration[i] = 0.0;
218      }
219    }
220
221    if (target_joint == -1) {
222      RCLCPP_ERROR(this->get_logger(), "Joint %s not found",
223                   joint_name.c_str());
224      return false;
225    }
226
227    // Perform trajectory planning and send command using Ruckig
228    const double tolerance = 1e-6;
229    while (g_running && rclcpp::ok() && !g_emergency_stop) {
230      auto result = ruckig.update(input, output);
231      if (result != ruckig::Result::Working &&
232          result != ruckig::Result::Finished) {
233        RCLCPP_WARN(this->get_logger(), "Trajectory planning failed");
234        break;
235      }
236
237      // Update current state
238      for (int i = 0; i < DOFs; ++i) {
239        input.current_position[i] = output.new_position[i];
240        input.current_velocity[i] = output.new_velocity[i];
241        input.current_acceleration[i] = output.new_acceleration[i];
242      }
243
244      // Check if target position is reached
245      if (std::abs(output.new_position[target_joint] - target_position) <
246          tolerance) {
247        RCLCPP_INFO(this->get_logger(), "Joint %s reached target position",
248                    joint_name.c_str());
249        break;
250      }
251
252      // Create and send joint command
253      aimdk_msgs::msg::JointCommandArray cmd;
254      cmd.joints.resize(DOFs);
255      for (int i = 0; i < DOFs; ++i) {
256        auto &joint = joint_info_[i];
257        cmd.joints[i].name = joint.name;
258        cmd.joints[i].position = output.new_position[i];
259        cmd.joints[i].velocity = output.new_velocity[i];
260        cmd.joints[i].stiffness = joint.kp;
261        cmd.joints[i].damping = joint.kd;
262      }
263      pub_->publish(cmd);
264
265      // Short delay to avoid excessive CPU usage
266      std::this_thread::sleep_for(std::chrono::milliseconds(2));
267    }
268
269    return true;
270  }
271
272  /**
273   * @brief Safely stop all joints
274   */
275  void safe_stop() {
276    if (!ruckig_initialized_) {
277      RCLCPP_WARN(this->get_logger(), "Ruckig trajectory planner not "
278                                      "initialized, cannot perform safe stop");
279      return;
280    }
281
282    RCLCPP_INFO(this->get_logger(), "Performing safe stop...");
283
284    // Set all joint target positions to current positions
285    for (int i = 0; i < DOFs; ++i) {
286      input.target_position[i] = input.current_position[i];
287      input.target_velocity[i] = 0.0;
288      input.target_acceleration[i] = 0.0;
289    }
290
291    // Send final command to ensure joints stop
292    aimdk_msgs::msg::JointCommandArray cmd;
293    cmd.joints.resize(DOFs);
294    for (int i = 0; i < DOFs; ++i) {
295      auto &joint = joint_info_[i];
296      cmd.joints[i].name = joint.name;
297      cmd.joints[i].position = input.current_position[i];
298      cmd.joints[i].velocity = 0.0;
299      cmd.joints[i].stiffness = joint.kp;
300      cmd.joints[i].damping = joint.kd;
301    }
302    pub_->publish(cmd);
303
304    RCLCPP_INFO(this->get_logger(), "Safe stop complete");
305  }
306
307  /**
308   * @brief Emergency stop for all joints
309   */
310  void emergency_stop() {
311    g_emergency_stop = true;
312    safe_stop();
313    RCLCPP_ERROR(this->get_logger(), "Emergency stop triggered");
314  }
315};
316
317/**
318 * @brief Main function
319 */
320int main(int argc, char *argv[]) {
321  rclcpp::init(argc, argv);
322
323  // Set up signal handling
324  signal(SIGINT, signal_handler);
325  signal(SIGTERM, signal_handler);
326
327  try {
328    // Create leg controller node
329    auto leg_node = std::make_shared<JointControllerNode<12, JointArea::LEG>>(
330        "leg_node", "/aima/hal/joint/leg/state", "/aima/hal/joint/leg/command");
331
332    // Create timer node
333    rclcpp::Node::SharedPtr timer_node =
334        rclcpp::Node::make_shared("timer_node");
335    double position = 0.8;
336
337    // Create timer callback function
338    auto timer = timer_node->create_wall_timer(std::chrono::seconds(3), [&]() {
339      if (!g_running || g_emergency_stop)
340        return; // If the program is shutting down or emergency stopped, do not
341                // execute new actions
342      position = -position;
343      position = 1.3 + position;
344      if (!leg_node->SetTargetPosition("left_knee_joint", position)) {
345        RCLCPP_ERROR(rclcpp::get_logger("main"),
346                     "Failed to set target position");
347      }
348    });
349
350    // Create executor
351    rclcpp::executors::MultiThreadedExecutor executor;
352    executor.add_node(leg_node);
353    executor.add_node(timer_node);
354
355    // Main loop
356    while (g_running && rclcpp::ok() && !g_emergency_stop) {
357      executor.spin_once(std::chrono::milliseconds(100));
358    }
359
360    // Safely stop all joints
361    RCLCPP_INFO(rclcpp::get_logger("main"), "Safely stopping all joints...");
362    leg_node->safe_stop();
363
364    // Wait a short time to ensure command transmission is complete
365    std::this_thread::sleep_for(std::chrono::milliseconds(100));
366
367    // Clean up resources
368    RCLCPP_INFO(rclcpp::get_logger("main"), "Cleaning up resources...");
369    leg_node.reset();
370    timer_node.reset();
371
372  } catch (const std::exception &e) {
373    RCLCPP_ERROR(rclcpp::get_logger("main"), "Exception occurred: %s",
374                 e.what());
375    g_emergency_stop = true;
376  } catch (...) {
377    RCLCPP_ERROR(rclcpp::get_logger("main"), "Unknown exception occurred");
378    g_emergency_stop = true;
379  }
380
381  RCLCPP_INFO(rclcpp::get_logger("main"), "Program exited safely");
382  rclcpp::shutdown();
383  return 0;
384}
```

## 6.2.10 Keyboard Control of the Robot

**This example enables controlling the robot’s forward, backward, and turning movements using PC keyboard input.**

**Use `W` `A` `S` `D` to control the walking direction, increase/decrease linear velocity (±0.2 m/s), use `Q` / `E` to increase/decrease angular velocity (±0.1 rad/s), `ESC` exits the program and releases terminal resources, and `Space` immediately resets the velocity to zero to perform an emergency stop.**

Caution

***Note: Before running this example, use the controller to switch the robot to Stable Standing Mode. (Standing Preparation Mode (Position-Control Standing Mode) / Locomotion Mode, press `R2` + `X`; for other modes, refer to the [mode routing diagram](../quick_start/run_example.html#fig-routing-to-stand-default)). Then, in the robot’s terminal, run `aima em stop-app rc` to disable the remote controller and prevent channel occupation.***

Before enabling keyboard control, an input source must be registered (already implemented in this example).
The `curse` module needs to be installed before running:

```
  sudo apt install libncurses-dev
```

```
  1#include "aimdk_msgs/msg/common_request.hpp"
  2#include "aimdk_msgs/msg/common_response.hpp"
  3#include "aimdk_msgs/msg/common_state.hpp"
  4#include "aimdk_msgs/msg/common_task_response.hpp"
  5#include "aimdk_msgs/msg/mc_input_action.hpp"
  6#include "aimdk_msgs/msg/mc_locomotion_velocity.hpp"
  7#include "aimdk_msgs/msg/message_header.hpp"
  8#include "aimdk_msgs/srv/set_mc_input_source.hpp"
  9
 10#include <algorithm>
 11#include <chrono>
 12#include <csignal>
 13#include <curses.h>
 14#include <rclcpp/rclcpp.hpp>
 15
 16using aimdk_msgs::msg::McLocomotionVelocity;
 17using std::placeholders::_1;
 18
 19class KeyboardVelocityController : public rclcpp::Node {
 20public:
 21  KeyboardVelocityController()
 22      : Node("keyboard_velocity_controller"), forward_velocity_(0.0),
 23        lateral_velocity_(0.0), angular_velocity_(0.0), step_(0.2),
 24        angular_step_(0.1) {
 25    pub_ = this->create_publisher<McLocomotionVelocity>(
 26        "/aima/mc/locomotion/velocity", 10);
 27    client_ = this->create_client<aimdk_msgs::srv::SetMcInputSource>(
 28        "/aimdk_5Fmsgs/srv/SetMcInputSource");
 29    // Register input source
 30    if (!register_input_source()) {
 31      RCLCPP_ERROR(this->get_logger(),
 32                   "Input source registration failed, exiting");
 33      throw std::runtime_error("Input source registration failed");
 34    }
 35    // Initialize ncurses
 36    initscr();
 37    cbreak();
 38    noecho();
 39    keypad(stdscr, TRUE);
 40    nodelay(stdscr, TRUE);
 41
 42    timer_ = this->create_wall_timer(
 43        std::chrono::milliseconds(50),
 44        std::bind(&KeyboardVelocityController::checkKeyAndPublish, this));
 45
 46    RCLCPP_INFO(this->get_logger(),
 47                "Control started: W/S Forward/Backward | A/D Strafe Left/Right "
 48                "| Q/E Turn Left/Right | Space Stop | ESC Exit");
 49  }
 50
 51  ~KeyboardVelocityController() {
 52    endwin(); // Restore terminal
 53  }
 54
 55private:
 56  rclcpp::Publisher<McLocomotionVelocity>::SharedPtr pub_;
 57  rclcpp::Client<aimdk_msgs::srv::SetMcInputSource>::SharedPtr client_;
 58  rclcpp::TimerBase::SharedPtr timer_;
 59
 60  float forward_velocity_, lateral_velocity_, angular_velocity_;
 61  const float step_, angular_step_;
 62
 63  bool register_input_source() {
 64    const std::chrono::seconds srv_timeout(8);
 65    auto start_time = std::chrono::steady_clock::now();
 66    while (!client_->wait_for_service(std::chrono::seconds(2))) {
 67      if (std::chrono::steady_clock::now() - start_time > srv_timeout) {
 68        RCLCPP_ERROR(this->get_logger(), "Waiting for service timed out");
 69        return false;
 70      }
 71      RCLCPP_INFO(this->get_logger(), "Waiting for input source service...");
 72    }
 73
 74    auto request =
 75        std::make_shared<aimdk_msgs::srv::SetMcInputSource::Request>();
 76    request->action.value = 1001;
 77    request->input_source.name = "node";
 78    request->input_source.priority = 40;
 79    request->input_source.timeout = 1000;
 80
 81    auto timeout = std::chrono::milliseconds(250);
 82
 83    for (int i = 0; i < 8; i++) {
 84      request->request.header.stamp = this->now();
 85      auto future = client_->async_send_request(request);
 86      auto retcode = rclcpp::spin_until_future_complete(
 87          this->get_node_base_interface(), future, timeout);
 88      if (retcode != rclcpp::FutureReturnCode::SUCCESS) {
 89        // retry as remote peer is NOT handled well by ROS
 90        RCLCPP_INFO(this->get_logger(),
 91                    "trying to register input source... [%d]", i);
 92        continue;
 93      }
 94      // future.done
 95      auto response = future.get();
 96      int state = response->response.state.value;
 97      RCLCPP_INFO(this->get_logger(),
 98                  "Set input source succeeded: state=%d, task_id=%lu", state,
 99                  response->response.task_id);
100      return true;
101    }
102    RCLCPP_ERROR(this->get_logger(), "Service call failed or timed out");
103    return false;
104  }
105
106  void checkKeyAndPublish() {
107    int ch = getch(); // non-blocking read
108
109    switch (ch) {
110    case ' ': // Space key
111      forward_velocity_ = 0.0;
112      lateral_velocity_ = 0.0;
113      angular_velocity_ = 0.0;
114      break;
115    case 'w':
116      forward_velocity_ = std::min(forward_velocity_ + step_, 1.0f);
117      break;
118    case 's':
119      forward_velocity_ = std::max(forward_velocity_ - step_, -1.0f);
120      break;
121    case 'a':
122      lateral_velocity_ = std::min(lateral_velocity_ + step_, 1.0f);
123      break;
124    case 'd':
125      lateral_velocity_ = std::max(lateral_velocity_ - step_, -1.0f);
126      break;
127    case 'q':
128      angular_velocity_ = std::min(angular_velocity_ + angular_step_, 1.0f);
129      break;
130    case 'e':
131      angular_velocity_ = std::max(angular_velocity_ - angular_step_, -1.0f);
132      break;
133    case 27: // ESC Key
134      RCLCPP_INFO(this->get_logger(), "Exiting control");
135      rclcpp::shutdown();
136      return;
137    }
138
139    auto msg = std::make_unique<McLocomotionVelocity>();
140    msg->header = aimdk_msgs::msg::MessageHeader();
141    msg->header.stamp = this->now();
142    msg->source = "node";
143    msg->forward_velocity = forward_velocity_;
144    msg->lateral_velocity = lateral_velocity_;
145    msg->angular_velocity = angular_velocity_;
146
147    float fwd = forward_velocity_;
148    float lat = lateral_velocity_;
149    float ang = angular_velocity_;
150
151    pub_->publish(std::move(msg));
152
153    // Screen Output
154    clear();
155    mvprintw(0, 0,
156             "W/S: Forward/Backward | A/D: Left/Right Strafe | Q/E: Turn "
157             "Left/Right | Space: Stop | ESC: Exit");
158    mvprintw(2, 0,
159             "Speed Status: Forward: %.2f m/s | Lateral: %.2f m/s | Angular: "
160             "%.2f rad/s",
161             fwd, lat, ang);
162    refresh();
163  }
164};
165
166int main(int argc, char *argv[]) {
167  rclcpp::init(argc, argv);
168  try {
169    auto node = std::make_shared<KeyboardVelocityController>();
170    rclcpp::spin(node);
171  } catch (const std::exception &e) {
172    RCLCPP_FATAL(rclcpp::get_logger("main"),
173                 "Program exited with exception: %s", e.what());
174  }
175  rclcpp::shutdown();
176  return 0;
177}
```

## 6.2.11 Take Photo

**This example uses take\_photo.** Before running the node, modify the camera topic from which to capture the image. After starting the node, an `/images/` directory will be created, and the current frame will be saved into this directory.

```
 1#include <chrono>
 2#include <cv_bridge/cv_bridge.h>
 3#include <filesystem>
 4#include <opencv2/opencv.hpp>
 5#include <rclcpp/rclcpp.hpp>
 6#include <sensor_msgs/msg/image.hpp>
 7#include <string>
 8
 9class SaveOneRaw : public rclcpp::Node {
10public:
11  SaveOneRaw() : Node("save_one_image"), saved_(false) {
12    topic_ = declare_parameter<std::string>(
13        "image_topic", "/aima/hal/sensor/stereo_head_front_left/rgb_image");
14
15    std::filesystem::create_directories("images");
16
17    auto qos = rclcpp::SensorDataQoS(); // BestEffort/Volatile
18    sub_ = create_subscription<sensor_msgs::msg::Image>(
19        topic_, qos, std::bind(&SaveOneRaw::cb, this, std::placeholders::_1));
20
21    RCLCPP_INFO(get_logger(), "Subscribing (raw): %s", topic_.c_str());
22  }
23
24private:
25  void cb(const sensor_msgs::msg::Image::SharedPtr msg) {
26    if (saved_)
27      return;
28
29    try {
30      // Obtain the Mat without copying by not specifying encoding
31      cv_bridge::CvImageConstPtr cvp = cv_bridge::toCvShare(msg);
32      cv::Mat img = cvp->image;
33
34      // Convert to BGR for uniform saving
35      if (msg->encoding == "rgb8") {
36        cv::cvtColor(img, img, cv::COLOR_RGB2BGR);
37      } else if (msg->encoding == "mono8") {
38        cv::cvtColor(img, img, cv::COLOR_GRAY2BGR);
39      } // bgr8 Use this directly; add more branches as needed to support
40        // additional encodings.
41
42      auto now = std::chrono::system_clock::now();
43      auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
44                    now.time_since_epoch())
45                    .count();
46      std::string path = "images/frame_" + std::to_string(ms) + ".png";
47
48      if (cv::imwrite(path, img)) {
49        RCLCPP_INFO(get_logger(), "Saved: %s  (%dx%d)", path.c_str(), img.cols,
50                    img.rows);
51        saved_ = true;
52        rclcpp::shutdown();
53      } else {
54        RCLCPP_ERROR(get_logger(), "cv::imwrite failed: %s", path.c_str());
55      }
56    } catch (const std::exception &e) {
57      RCLCPP_ERROR(get_logger(), "raw decode failed: %s", e.what());
58      // Do not set the saved flag; wait for the next frame
59    }
60  }
61
62  std::string topic_;
63  bool saved_;
64  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_;
65};
66
67int main(int argc, char **argv) {
68  rclcpp::init(argc, argv);
69  rclcpp::spin(std::make_shared<SaveOneRaw>());
70  return 0;
71}
```

## 6.2.12 Camera Streaming Example Collection

**This example set provides multiple camera data subscription and processing functions, supporting data streams from depth cameras, stereo cameras, and monocular cameras.**
These camera subscription examples do not provide actual application-level logic; they only print basic camera data information. If you are familiar with ROS2, you may notice that `ros2 topic echo` + `ros2 topic hz` can also achieve similar functionality. You may directly check the topic list in the SDK interface manual to start developing your own module, or you may use these camera examples as scaffolding to integrate your own business logic. **All published sensor data is raw and unprocessed (e.g., without undistortion). If you need detailed sensor information (such as resolution, focal length, etc.), please refer to the `camera_info` topic.**

### Depth Camera Data Subscription

**This example uses echo\_camera\_rgbd**, subscribing to the `/aima/hal/sensor/rgbd_head_front/` topic to receive depth camera data, supporting multiple data types including depth point clouds, depth images, RGB images, compressed RGB images, and camera intrinsic parameters.

**Features:**

- Supports multiple data types (depth point cloud, depth image, RGB image, compressed image, camera intrinsics)
- Real-time FPS statistics and data display
- Supports RGB video recording
- Configurable topic type selection

**Supported Data Types:**

- `depth_pointcloud`: Depth point cloud data (sensor\_msgs/PointCloud2)
- `depth_image`: Depth image (sensor\_msgs/Image)
- `rgb_image`: RGB image (sensor\_msgs/Image)
- `rgb_image_compressed`: Compressed RGB image (sensor\_msgs/CompressedImage)
- `camera_info`: Camera intrinsic parameters (sensor\_msgs/CameraInfo)

```
  1#include <deque>
  2#include <iomanip>
  3#include <memory>
  4#include <rclcpp/rclcpp.hpp>
  5#include <sensor_msgs/msg/camera_info.hpp>
  6#include <sensor_msgs/msg/compressed_image.hpp>
  7#include <sensor_msgs/msg/image.hpp>
  8#include <sensor_msgs/msg/point_cloud2.hpp>
  9#include <sstream>
 10#include <string>
 11#include <vector>
 12
 13// OpenCV headers for image/video writing
 14#include <cv_bridge/cv_bridge.h>
 15#include <opencv2/opencv.hpp>
 16
 17/**
 18 * @brief Example of subscribing to multiple topics for the head depth camera
 19 *
 20 * You can select which topic type to subscribe to via the startup argument
 21 * --ros-args -p topic_type:=<type>:
 22 *   - depth_pointcloud: Depth point cloud (sensor_msgs/PointCloud2)
 23 *   - depth_image: Depth image (sensor_msgs/Image)
 24 *   - rgb_image: RGB image (sensor_msgs/Image)
 25 *   - rgb_image_compressed: RGB compressed image (sensor_msgs/CompressedImage)
 26 *   - rgb_camera_info: Camera intrinsic parameters (sensor_msgs/CameraInfo)
 27 *   - depth_camera_info: Camera intrinsic parameters (sensor_msgs/CameraInfo)
 28 *
 29 * Examples:
 30 *   ros2 run examples echo_camera_rgbd --ros-args -p
 31 * topic_type:=depth_pointcloud ros2 run examples echo_camera_rgbd --ros-args -p
 32 * topic_type:=rgb_image ros2 run examples echo_camera_rgbd --ros-args -p
 33 * topic_type:=rgb_camera_info
 34 *
 35 * topic_type defaults to "rgb_image"
 36 *
 37 * See individual callbacks for more detailed comments
 38 */
 39class CameraTopicEcho : public rclcpp::Node {
 40public:
 41  CameraTopicEcho() : Node("camera_topic_echo") {
 42    // Select which topic type to subscribe to
 43    topic_type_ = declare_parameter<std::string>("topic_type", "rgb_image");
 44    dump_video_path_ = declare_parameter<std::string>("dump_video_path", "");
 45
 46    // Subscribed topics and their message layouts
 47    // 1. /aima/hal/sensor/rgbd_head_front/depth_pointcloud
 48    //    - topic_type: depth_pointcloud
 49    //    - message type: sensor_msgs::msg::PointCloud2
 50    //    - frame_id: rgbd_head_front
 51    //    - child_frame_id: /
 52    //    - contents: depth point cloud
 53    // 2. /aima/hal/sensor/rgbd_head_front/depth_image
 54    //    - topic_type: depth_image
 55    //    - message type: sensor_msgs::msg::Image
 56    //    - frame_id: rgbd_head_front
 57    //    - contents: depth image
 58    // 3. /aima/hal/sensor/rgbd_head_front/rgb_image
 59    //    - topic_type: rgb_image
 60    //    - message type: sensor_msgs::msg::Image
 61    //    - frame_id: rgbd_head_front
 62    //    - contents: RGB image
 63    // 4. /aima/hal/sensor/rgbd_head_front/rgb_image/compressed
 64    //    - topic_type: rgb_image_compressed
 65    //    - message type: sensor_msgs::msg::CompressedImage
 66    //    - frame_id: rgbd_head_front
 67    //    - contents: RGB compressed image
 68    // 5. /aima/hal/sensor/rgbd_head_front/rgb_camera_info
 69    //    - topic_type: camera_info
 70    //    - message type: sensor_msgs::msg::CameraInfo
 71    //    - frame_id: rgbd_head_front
 72    //    - contents: RGB camera intrinsic parameters
 73    // 6. /aima/hal/sensor/rgbd_head_front/depth_camera_info
 74    //    - topic_type: camera_info
 75    //    - message type: sensor_msgs::msg::CameraInfo
 76    //    - frame_id: rgbd_head_front
 77    //    - contents: RGB camera intrinsic parameters
 78
 79    auto qos = rclcpp::SensorDataQoS();
 80
 81    // Enable depth pointcloud subscription
 82    if (topic_type_ == "depth_pointcloud") {
 83      topic_name_ = "/aima/hal/sensor/rgbd_head_front/depth_pointcloud";
 84      sub_pointcloud_ = create_subscription<sensor_msgs::msg::PointCloud2>(
 85          topic_name_, qos,
 86          std::bind(&CameraTopicEcho::cb_pointcloud, this,
 87                    std::placeholders::_1));
 88      RCLCPP_INFO(get_logger(), "✅ Subscribing PointCloud2: %s",
 89                  topic_name_.c_str());
 90
 91      // Enable depth image subscription
 92    } else if (topic_type_ == "depth_image") {
 93      topic_name_ = "/aima/hal/sensor/rgbd_head_front/depth_image";
 94      sub_image_ = create_subscription<sensor_msgs::msg::Image>(
 95          topic_name_, qos,
 96          std::bind(&CameraTopicEcho::cb_image, this, std::placeholders::_1));
 97      RCLCPP_INFO(get_logger(), "✅ Subscribing Depth Image: %s",
 98                  topic_name_.c_str());
 99
100      // Enable RGB image subscription
101    } else if (topic_type_ == "rgb_image") {
102      topic_name_ = "/aima/hal/sensor/rgbd_head_front/rgb_image";
103      sub_image_ = create_subscription<sensor_msgs::msg::Image>(
104          topic_name_, qos,
105          std::bind(&CameraTopicEcho::cb_image, this, std::placeholders::_1));
106      RCLCPP_INFO(get_logger(), "✅ Subscribing RGB Image: %s",
107                  topic_name_.c_str());
108      if (!dump_video_path_.empty()) {
109        RCLCPP_INFO(get_logger(), "📝 Will dump received images to video: %s",
110                    dump_video_path_.c_str());
111      }
112
113      // Enable RGB compressed image subscription
114    } else if (topic_type_ == "rgb_image_compressed") {
115      topic_name_ = "/aima/hal/sensor/rgbd_head_front/rgb_image/compressed";
116      sub_compressed_ = create_subscription<sensor_msgs::msg::CompressedImage>(
117          topic_name_, qos,
118          std::bind(&CameraTopicEcho::cb_compressed, this,
119                    std::placeholders::_1));
120      RCLCPP_INFO(get_logger(), "✅ Subscribing CompressedImage: %s",
121                  topic_name_.c_str());
122
123      // Enable rgb camera info subscription
124    } else if (topic_type_ == "rgb_camera_info") {
125      topic_name_ = "/aima/hal/sensor/rgbd_head_front/rgb_camera_info";
126      // RGB-D CameraInfo subscriptions is different with other cameras.
127      // The messages arrive in about 10Hz and SensorDataQoS is enough.
128      sub_camerainfo_ = create_subscription<sensor_msgs::msg::CameraInfo>(
129          topic_name_, qos,
130          std::bind(&CameraTopicEcho::cb_camerainfo, this,
131                    std::placeholders::_1));
132      RCLCPP_INFO(get_logger(), "✅ Subscribing RGB CameraInfo: %s",
133                  topic_name_.c_str());
134
135      // Enable depth camera info subscription
136    } else if (topic_type_ == "depth_camera_info") {
137      topic_name_ = "/aima/hal/sensor/rgbd_head_front/depth_camera_info";
138      // RGB-D CameraInfo subscriptions is different with other cameras.
139      // The messages arrive in about 10Hz and SensorDataQoS is enough.
140      sub_camerainfo_ = create_subscription<sensor_msgs::msg::CameraInfo>(
141          topic_name_, qos,
142          std::bind(&CameraTopicEcho::cb_camerainfo, this,
143                    std::placeholders::_1));
144      RCLCPP_INFO(get_logger(), "✅ Subscribing Depth CameraInfo: %s",
145                  topic_name_.c_str());
146
147      // Unknown topic_type error
148    } else {
149      RCLCPP_ERROR(get_logger(), "Unknown topic_type: %s", topic_type_.c_str());
150      throw std::runtime_error("Unknown topic_type");
151    }
152  }
153
154  ~CameraTopicEcho() override {
155    if (video_writer_.isOpened()) {
156      video_writer_.release();
157      RCLCPP_INFO(get_logger(), "Video file closed.");
158    }
159  }
160
161private:
162  // PointCloud2 callback
163  void cb_pointcloud(const sensor_msgs::msg::PointCloud2::SharedPtr msg) {
164    // Update arrivals (for FPS calculation)
165    update_arrivals();
166
167    // Print point cloud basic info
168    if (should_print()) {
169      std::ostringstream oss;
170      oss << "🌫️ PointCloud2 received\n"
171          << "  • frame_id:        " << msg->header.frame_id << "\n"
172          << "  • stamp (sec):     "
173          << rclcpp::Time(msg->header.stamp).seconds() << "\n"
174          << "  • width x height:  " << msg->width << " x " << msg->height
175          << "\n"
176          << "  • point_step:      " << msg->point_step << "\n"
177          << "  • row_step:        " << msg->row_step << "\n"
178          << "  • fields:          ";
179      for (const auto &f : msg->fields)
180        oss << f.name << "(" << (int)f.datatype << ") ";
181      oss << "\n  • is_bigendian:    " << msg->is_bigendian
182          << "\n  • is_dense:        " << msg->is_dense
183          << "\n  • data size:       " << msg->data.size()
184          << "\n  • recv FPS (1s):   " << get_fps();
185      RCLCPP_INFO(get_logger(), "%s", oss.str().c_str());
186    }
187  }
188
189  // Image callback (depth/RGB image)
190  void cb_image(const sensor_msgs::msg::Image::SharedPtr msg) {
191    update_arrivals();
192
193    if (should_print()) {
194      RCLCPP_INFO(get_logger(),
195                  "📸 %s received\n"
196                  "  • frame_id:        %s\n"
197                  "  • stamp (sec):     %.6f\n"
198                  "  • encoding:        %s\n"
199                  "  • size (WxH):      %u x %u\n"
200                  "  • step (bytes/row):%u\n"
201                  "  • is_bigendian:    %u\n"
202                  "  • recv FPS (1s):   %.1f",
203                  topic_type_.c_str(), msg->header.frame_id.c_str(),
204                  rclcpp::Time(msg->header.stamp).seconds(),
205                  msg->encoding.c_str(), msg->width, msg->height, msg->step,
206                  msg->is_bigendian, get_fps());
207    }
208
209    // Video dump is supported only for RGB images
210    if (topic_type_ == "rgb_image" && !dump_video_path_.empty()) {
211      dump_image_to_video(msg);
212    }
213  }
214
215  // CompressedImage callback
216  void cb_compressed(const sensor_msgs::msg::CompressedImage::SharedPtr msg) {
217    update_arrivals();
218
219    if (should_print()) {
220      RCLCPP_INFO(get_logger(),
221                  "🗜️  CompressedImage received\n"
222                  "  • frame_id:        %s\n"
223                  "  • stamp (sec):     %.6f\n"
224                  "  • format:          %s\n"
225                  "  • data size:       %zu\n"
226                  "  • recv FPS (1s):   %.1f",
227                  msg->header.frame_id.c_str(),
228                  rclcpp::Time(msg->header.stamp).seconds(),
229                  msg->format.c_str(), msg->data.size(), get_fps());
230    }
231  }
232
233  // CameraInfo callback (camera intrinsic parameters)
234  void cb_camerainfo(const sensor_msgs::msg::CameraInfo::SharedPtr msg) {
235    // CameraInfo is typically published once; print it once
236    std::ostringstream oss;
237    oss << "📷 " << topic_type_ << " received\n"
238        << "  • frame_id:        " << msg->header.frame_id << "\n"
239        << "  • stamp (sec):     " << rclcpp::Time(msg->header.stamp).seconds()
240        << "\n"
241        << "  • width x height:  " << msg->width << " x " << msg->height << "\n"
242        << "  • distortion_model:" << msg->distortion_model << "\n"
243        << "  • D: [";
244    for (size_t i = 0; i < msg->d.size(); ++i) {
245      oss << msg->d[i];
246      if (i + 1 < msg->d.size())
247        oss << ", ";
248    }
249    oss << "]\n  • K: [";
250    for (int i = 0; i < 9; ++i) {
251      oss << msg->k[i];
252      if (i + 1 < 9)
253        oss << ", ";
254    }
255    oss << "]\n  • R: [";
256    for (int i = 0; i < 9; ++i) {
257      oss << msg->r[i];
258      if (i + 1 < 9)
259        oss << ", ";
260    }
261    oss << "]\n  • P: [";
262    for (int i = 0; i < 12; ++i) {
263      oss << msg->p[i];
264      if (i + 1 < 12)
265        oss << ", ";
266    }
267    oss << "]\n"
268        << "  • binning_x: " << msg->binning_x << "\n"
269        << "  • binning_y: " << msg->binning_y << "\n"
270        << "  • roi: { x_offset: " << msg->roi.x_offset
271        << ", y_offset: " << msg->roi.y_offset
272        << ", height: " << msg->roi.height << ", width: " << msg->roi.width
273        << ", do_rectify: " << (msg->roi.do_rectify ? "true" : "false") << " }";
274    RCLCPP_INFO(get_logger(), "%s", oss.str().c_str());
275  }
276
277  // Track arrival timestamps to compute FPS
278  void update_arrivals() {
279    const rclcpp::Time now = this->get_clock()->now();
280    arrivals_.push_back(now);
281    while (!arrivals_.empty() && (now - arrivals_.front()).seconds() > 1.0) {
282      arrivals_.pop_front();
283    }
284  }
285  double get_fps() const { return static_cast<double>(arrivals_.size()); }
286
287  // Control printing frequency
288  bool should_print() {
289    const rclcpp::Time now = this->get_clock()->now();
290    if ((now - last_print_).seconds() >= 1.0) {
291      last_print_ = now;
292      return true;
293    }
294    return false;
295  }
296
297  // Dump received images to a video file (RGB images only)
298  void dump_image_to_video(const sensor_msgs::msg::Image::SharedPtr &msg) {
299    cv::Mat image;
300    try {
301      // Obtain the Mat without copying by not specifying encoding
302      cv_bridge::CvImageConstPtr cvp = cv_bridge::toCvShare(msg);
303      image = cvp->image;
304      // Convert to BGR for uniform saving
305      if (msg->encoding == "rgb8") {
306        cv::cvtColor(image, image, cv::COLOR_RGB2BGR);
307      } else {
308        RCLCPP_WARN(get_logger(), "image encoding not expected: %s",
309                    msg->encoding.c_str());
310        return;
311      }
312    } catch (const std::exception &e) {
313      RCLCPP_WARN(get_logger(), "cv_bridge exception: %s", e.what());
314      return;
315    }
316
317    // Initialize VideoWriter
318    if (!video_writer_.isOpened()) {
319      int fourcc = cv::VideoWriter::fourcc('M', 'J', 'P', 'G');
320      double fps = std::max(1.0, get_fps());
321      bool ok = video_writer_.open(dump_video_path_, fourcc, fps,
322                                   cv::Size(image.cols, image.rows), true);
323      if (!ok) {
324        RCLCPP_ERROR(get_logger(), "Failed to open video file: %s",
325                     dump_video_path_.c_str());
326        dump_video_path_.clear(); // stop trying
327        return;
328      }
329      RCLCPP_INFO(get_logger(), "VideoWriter started: %s, size=%dx%d, fps=%.1f",
330                  dump_video_path_.c_str(), image.cols, image.rows, fps);
331    }
332    video_writer_.write(image);
333  }
334
335  // Member variables
336  std::string topic_type_;
337  std::string topic_name_;
338  std::string dump_video_path_;
339
340  // Subscriptions
341  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_image_;
342  rclcpp::Subscription<sensor_msgs::msg::CompressedImage>::SharedPtr
343      sub_compressed_;
344  rclcpp::Subscription<sensor_msgs::msg::CameraInfo>::SharedPtr sub_camerainfo_;
345  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr
346      sub_pointcloud_;
347
348  // FPS statistics
349  rclcpp::Time last_print_{0, 0, RCL_ROS_TIME};
350  std::deque<rclcpp::Time> arrivals_;
351
352  // Video writer
353  cv::VideoWriter video_writer_;
354};
355
356int main(int argc, char **argv) {
357  rclcpp::init(argc, argv);
358  auto node = std::make_shared<CameraTopicEcho>();
359  rclcpp::spin(node);
360  rclcpp::shutdown();
361  return 0;
362}
```

**Usage Instructions:**

1. Subscribe to depth point cloud data:

   ```
   ros2 run examples echo_camera_rgbd --ros-args -p topic_type:=depth_pointcloud
   ```
2. Subscribe to RGB image data:

   ```
   ros2 run examples echo_camera_rgbd --ros-args -p topic_type:=rgb_image
   ```
3. Subscribe to camera intrinsic parameters:

   ```
   ros2 run examples echo_camera_rgbd --ros-args -p topic_type:=rgb_camera_info
   ros2 run examples echo_camera_rgbd --ros-args -p topic_type:=depth_camera_info
   ```
4. Record RGB video:

   ```
   # The value of dump_video_path can be changed to another path; make sure the directory exists beforehand
   ros2 run examples echo_camera_rgbd --ros-args -p topic_type:=rgb_image -p dump_video_path:=$PWD/output.avi
   ```

### Stereo Camera Data Subscription

**This example uses echo\_camera\_stereo**, subscribing to the `/aima/hal/sensor/stereo_head_front_*/` topics to receive stereo camera data, supporting RGB images, compressed images, and camera intrinsic parameters from both the left and right cameras.

**Features:**

- Supports independent subscription for left and right cameras
- Real-time FPS statistics and data display
- Supports RGB video recording
- Configurable camera selection (left/right)

**Supported Data Types:**

- `left_rgb_image`: Left camera RGB image (sensor\_msgs/Image)
- `left_rgb_image_compressed`: Left camera compressed RGB image (sensor\_msgs/CompressedImage)
- `left_camera_info`: Left camera intrinsic parameters (sensor\_msgs/CameraInfo)
- `right_rgb_image`: Right camera RGB image (sensor\_msgs/Image)
- `right_rgb_image_compressed`: Right camera compressed RGB image (sensor\_msgs/CompressedImage)
- `right_camera_info`: Right camera intrinsic parameters (sensor\_msgs/CameraInfo)

```
  1#include <deque>
  2#include <iomanip>
  3#include <memory>
  4#include <rclcpp/rclcpp.hpp>
  5#include <sensor_msgs/msg/camera_info.hpp>
  6#include <sensor_msgs/msg/compressed_image.hpp>
  7#include <sensor_msgs/msg/image.hpp>
  8#include <sstream>
  9#include <string>
 10#include <vector>
 11
 12// OpenCV headers for image/video writing
 13#include <cv_bridge/cv_bridge.h>
 14#include <opencv2/opencv.hpp>
 15
 16/**
 17 * @brief Example of subscribing to multiple topics for the stereo head camera
 18 *
 19 * You can select which topic type to subscribe to via the startup argument
 20 * --ros-args -p topic_type:=<type>:
 21 *   - left_rgb_image: left camera RGB image (sensor_msgs/Image)
 22 *   - left_rgb_image_compressed: left camera RGB compressed image
 23 * (sensor_msgs/CompressedImage)
 24 *   - left_camera_info: left camera intrinsic parameters
 25 * (sensor_msgs/CameraInfo)
 26 *   - right_rgb_image: right camera RGB image (sensor_msgs/Image)
 27 *   - right_rgb_image_compressed: right camera RGB compressed image
 28 * (sensor_msgs/CompressedImage)
 29 *   - right_camera_info: right camera intrinsic parameters
 30 * (sensor_msgs/CameraInfo)
 31 *
 32 * Examples:
 33 *   ros2 run examples echo_camera_stereo --ros-args -p
 34 * topic_type:=left_rgb_image ros2 run examples echo_camera_stereo --ros-args -p
 35 * topic_type:=right_rgb_image ros2 run examples echo_camera_stereo --ros-args
 36 * -p topic_type:=left_camera_info
 37 *
 38 * topic_type defaults to "left_rgb_image"
 39 *
 40 * See individual callbacks for more detailed comments
 41 */
 42class StereoCameraTopicEcho : public rclcpp::Node {
 43public:
 44  StereoCameraTopicEcho() : Node("stereo_camera_topic_echo") {
 45    // Select which topic type to subscribe to
 46    topic_type_ =
 47        declare_parameter<std::string>("topic_type", "left_rgb_image");
 48    dump_video_path_ = declare_parameter<std::string>("dump_video_path", "");
 49
 50    // Subscribed topics and their message layouts
 51    // 1. /aima/hal/sensor/stereo_head_front_left/rgb_image
 52    //    - topic_type: left_rgb_image
 53    //    - message type: sensor_msgs::msg::Image
 54    //    - frame_id: stereo_head_front
 55    //    - child_frame_id: /
 56    //    - contents: left camera raw image
 57    // 2. /aima/hal/sensor/stereo_head_front_left/rgb_image/compressed
 58    //    - topic_type: left_rgb_image_compressed
 59    //    - message type: sensor_msgs::msg::CompressedImage
 60    //    - frame_id: stereo_head_front
 61    //    - contents: left camera compressed image
 62    // 3. /aima/hal/sensor/stereo_head_front_left/camera_info
 63    //    - topic_type: left_camera_info
 64    //    - message type: sensor_msgs::msg::CameraInfo
 65    //    - frame_id: stereo_head_front
 66    //    - contents: left camera intrinsic parameters
 67    // 4. /aima/hal/sensor/stereo_head_front_right/rgb_image
 68    //    - topic_type: right_rgb_image
 69    //    - message type: sensor_msgs::msg::Image
 70    //    - frame_id: stereo_head_front_right
 71    //    - child_frame_id: /
 72    //    - contents: right camera raw image
 73    // 5. /aima/hal/sensor/stereo_head_front_right/rgb_image/compressed
 74    //    - topic_type: right_rgb_image_compressed
 75    //    - message type: sensor_msgs::msg::CompressedImage
 76    //    - frame_id: stereo_head_front_right
 77    //    - contents: right camera compressed image
 78    // 6. /aima/hal/sensor/stereo_head_front_right/camera_info
 79    //    - topic_type: right_camera_info
 80    //    - message type: sensor_msgs::msg::CameraInfo
 81    //    - frame_id: stereo_head_front_right
 82    //    - contents: right camera intrinsic parameters
 83
 84    // Set QoS parameters - use SensorData QoS
 85    auto qos = rclcpp::SensorDataQoS();
 86
 87    // Enable left camera RGB image subscription
 88    if (topic_type_ == "left_rgb_image") {
 89      topic_name_ = "/aima/hal/sensor/stereo_head_front_left/rgb_image";
 90      sub_image_ = create_subscription<sensor_msgs::msg::Image>(
 91          topic_name_, qos,
 92          std::bind(&StereoCameraTopicEcho::cb_image, this,
 93                    std::placeholders::_1));
 94      RCLCPP_INFO(get_logger(), "✅ Subscribing Left RGB Image: %s",
 95                  topic_name_.c_str());
 96      if (!dump_video_path_.empty()) {
 97        RCLCPP_INFO(get_logger(), "📝 Will dump received images to video: %s",
 98                    dump_video_path_.c_str());
 99      }
100
101      // Enable left camera RGB compressed image subscription
102    } else if (topic_type_ == "left_rgb_image_compressed") {
103      topic_name_ =
104          "/aima/hal/sensor/stereo_head_front_left/rgb_image/compressed";
105      sub_compressed_ = create_subscription<sensor_msgs::msg::CompressedImage>(
106          topic_name_, qos,
107          std::bind(&StereoCameraTopicEcho::cb_compressed, this,
108                    std::placeholders::_1));
109      RCLCPP_INFO(get_logger(), "✅ Subscribing Left CompressedImage: %s",
110                  topic_name_.c_str());
111
112      // Enable left camera info subscription
113    } else if (topic_type_ == "left_camera_info") {
114
115      topic_name_ = "/aima/hal/sensor/stereo_head_front_left/camera_info";
116      // CameraInfo subscriptions must use reliable + transient_local
117      // QoS in order to receive latched/history messages (even if only one
118      // message was published). Here we use keep_last(1) + reliable
119      // + transient_local.
120      sub_camerainfo_ = create_subscription<sensor_msgs::msg::CameraInfo>(
121          topic_name_,
122          rclcpp::QoS(rclcpp::KeepLast(1)).reliable().transient_local(),
123          std::bind(&StereoCameraTopicEcho::cb_camerainfo, this,
124                    std::placeholders::_1));
125      RCLCPP_INFO(get_logger(),
126                  "✅ Subscribing Left CameraInfo (with transient_local): %s",
127                  topic_name_.c_str());
128
129      // Enable right camera RGB image subscription
130    } else if (topic_type_ == "right_rgb_image") {
131      topic_name_ = "/aima/hal/sensor/stereo_head_front_right/rgb_image";
132      sub_image_ = create_subscription<sensor_msgs::msg::Image>(
133          topic_name_, qos,
134          std::bind(&StereoCameraTopicEcho::cb_image, this,
135                    std::placeholders::_1));
136      RCLCPP_INFO(get_logger(), "✅ Subscribing Right RGB Image: %s",
137                  topic_name_.c_str());
138      if (!dump_video_path_.empty()) {
139        RCLCPP_INFO(get_logger(), "📝 Will dump received images to video: %s",
140                    dump_video_path_.c_str());
141      }
142
143      // Enable right camera RGB compressed image subscription
144    } else if (topic_type_ == "right_rgb_image_compressed") {
145      topic_name_ =
146          "/aima/hal/sensor/stereo_head_front_right/rgb_image/compressed";
147      sub_compressed_ = create_subscription<sensor_msgs::msg::CompressedImage>(
148          topic_name_, qos,
149          std::bind(&StereoCameraTopicEcho::cb_compressed, this,
150                    std::placeholders::_1));
151      RCLCPP_INFO(get_logger(), "✅ Subscribing Right CompressedImage: %s",
152                  topic_name_.c_str());
153
154      // Enable right camera info subscription
155    } else if (topic_type_ == "right_camera_info") {
156      topic_name_ = "/aima/hal/sensor/stereo_head_front_right/camera_info";
157      // CameraInfo subscriptions must use reliable + transient_local
158      // QoS in order to receive latched/history messages (even if only one
159      // message was published). Here we use keep_last(1) + reliable
160      // + transient_local.
161      sub_camerainfo_ = create_subscription<sensor_msgs::msg::CameraInfo>(
162          topic_name_,
163          rclcpp::QoS(rclcpp::KeepLast(1)).reliable().transient_local(),
164          std::bind(&StereoCameraTopicEcho::cb_camerainfo, this,
165                    std::placeholders::_1));
166      RCLCPP_INFO(get_logger(),
167                  "✅ Subscribing Right CameraInfo (with transient_local): %s",
168                  topic_name_.c_str());
169
170      // Unknown topic_type error
171    } else {
172      RCLCPP_ERROR(get_logger(), "Unknown topic_type: %s", topic_type_.c_str());
173      throw std::runtime_error("Unknown topic_type");
174    }
175  }
176
177  ~StereoCameraTopicEcho() override {
178    if (video_writer_.isOpened()) {
179      video_writer_.release();
180      RCLCPP_INFO(get_logger(), "Video file closed.");
181    }
182  }
183
184private:
185  // Image callback (left/right RGB image)
186  void cb_image(const sensor_msgs::msg::Image::SharedPtr msg) {
187    update_arrivals();
188
189    if (should_print()) {
190      RCLCPP_INFO(get_logger(),
191                  "📸 %s received\n"
192                  "  • frame_id:        %s\n"
193                  "  • stamp (sec):     %.6f\n"
194                  "  • encoding:        %s\n"
195                  "  • size (WxH):      %u x %u\n"
196                  "  • step (bytes/row):%u\n"
197                  "  • is_bigendian:    %u\n"
198                  "  • recv FPS (1s):   %.1f",
199                  topic_type_.c_str(), msg->header.frame_id.c_str(),
200                  rclcpp::Time(msg->header.stamp).seconds(),
201                  msg->encoding.c_str(), msg->width, msg->height, msg->step,
202                  msg->is_bigendian, get_fps());
203    }
204
205    // Video dump is supported only for RGB images
206    if ((topic_type_ == "left_rgb_image" || topic_type_ == "right_rgb_image") &&
207        !dump_video_path_.empty()) {
208      dump_image_to_video(msg);
209    }
210  }
211
212  // CompressedImage callback (left/right RGB compressed image)
213  void cb_compressed(const sensor_msgs::msg::CompressedImage::SharedPtr msg) {
214    update_arrivals();
215
216    if (should_print()) {
217      RCLCPP_INFO(get_logger(),
218                  "🗜️  %s received\n"
219                  "  • frame_id:        %s\n"
220                  "  • stamp (sec):     %.6f\n"
221                  "  • format:          %s\n"
222                  "  • data size:       %zu\n"
223                  "  • recv FPS (1s):   %.1f",
224                  topic_type_.c_str(), msg->header.frame_id.c_str(),
225                  rclcpp::Time(msg->header.stamp).seconds(),
226                  msg->format.c_str(), msg->data.size(), get_fps());
227    }
228  }
229
230  // CameraInfo callback (left/right camera intrinsic parameters)
231  void cb_camerainfo(const sensor_msgs::msg::CameraInfo::SharedPtr msg) {
232    // CameraInfo is typically published once; print it once
233    std::ostringstream oss;
234    oss << "📷 " << topic_type_ << " received\n"
235        << "  • frame_id:        " << msg->header.frame_id << "\n"
236        << "  • stamp (sec):     " << rclcpp::Time(msg->header.stamp).seconds()
237        << "\n"
238        << "  • width x height:  " << msg->width << " x " << msg->height << "\n"
239        << "  • distortion_model:" << msg->distortion_model << "\n"
240        << "  • D: [";
241    for (size_t i = 0; i < msg->d.size(); ++i) {
242      oss << msg->d[i];
243      if (i + 1 < msg->d.size())
244        oss << ", ";
245    }
246    oss << "]\n  • K: [";
247    for (int i = 0; i < 9; ++i) {
248      oss << msg->k[i];
249      if (i + 1 < 9)
250        oss << ", ";
251    }
252    oss << "]\n  • R: [";
253    for (int i = 0; i < 9; ++i) {
254      oss << msg->r[i];
255      if (i + 1 < 9)
256        oss << ", ";
257    }
258    oss << "]\n  • P: [";
259    for (int i = 0; i < 12; ++i) {
260      oss << msg->p[i];
261      if (i + 1 < 12)
262        oss << ", ";
263    }
264    oss << "]\n"
265        << "  • binning_x: " << msg->binning_x << "\n"
266        << "  • binning_y: " << msg->binning_y << "\n"
267        << "  • roi: { x_offset: " << msg->roi.x_offset
268        << ", y_offset: " << msg->roi.y_offset
269        << ", height: " << msg->roi.height << ", width: " << msg->roi.width
270        << ", do_rectify: " << (msg->roi.do_rectify ? "true" : "false") << " }";
271    RCLCPP_INFO(get_logger(), "%s", oss.str().c_str());
272  }
273
274  // Track arrival timestamps to compute FPS
275  void update_arrivals() {
276    const rclcpp::Time now = this->get_clock()->now();
277    arrivals_.push_back(now);
278    while (!arrivals_.empty() && (now - arrivals_.front()).seconds() > 1.0) {
279      arrivals_.pop_front();
280    }
281  }
282  double get_fps() const { return static_cast<double>(arrivals_.size()); }
283
284  // Control printing frequency
285  bool should_print() {
286    const rclcpp::Time now = this->get_clock()->now();
287    if ((now - last_print_).seconds() >= 1.0) {
288      last_print_ = now;
289      return true;
290    }
291    return false;
292  }
293
294  // Dump received images to a video file (RGB images only)
295  void dump_image_to_video(const sensor_msgs::msg::Image::SharedPtr &msg) {
296    cv::Mat image;
297    try {
298      // Obtain the Mat without copying by not specifying encoding
299      cv_bridge::CvImageConstPtr cvp = cv_bridge::toCvShare(msg);
300      image = cvp->image;
301      // Convert to BGR for uniform saving
302      if (msg->encoding == "rgb8") {
303        cv::cvtColor(image, image, cv::COLOR_RGB2BGR);
304      } else {
305        RCLCPP_WARN(get_logger(), "image encoding not expected: %s",
306                    msg->encoding.c_str());
307        return;
308      }
309    } catch (const std::exception &e) {
310      RCLCPP_WARN(get_logger(), "cv_bridge exception: %s", e.what());
311      return;
312    }
313
314    // Initialize VideoWriter
315    if (!video_writer_.isOpened()) {
316      int fourcc = cv::VideoWriter::fourcc('M', 'J', 'P', 'G');
317      double fps = std::max(1.0, get_fps());
318      bool ok = video_writer_.open(dump_video_path_, fourcc, fps,
319                                   cv::Size(image.cols, image.rows), true);
320      if (!ok) {
321        RCLCPP_ERROR(get_logger(), "Failed to open video file: %s",
322                     dump_video_path_.c_str());
323        dump_video_path_.clear(); // stop trying
324        return;
325      }
326      RCLCPP_INFO(get_logger(), "VideoWriter started: %s, size=%dx%d, fps=%.1f",
327                  dump_video_path_.c_str(), image.cols, image.rows, fps);
328    }
329    video_writer_.write(image);
330  }
331
332  // Member variables
333  std::string topic_type_;
334  std::string topic_name_;
335  std::string dump_video_path_;
336
337  // Subscriptions
338  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_image_;
339  rclcpp::Subscription<sensor_msgs::msg::CompressedImage>::SharedPtr
340      sub_compressed_;
341  rclcpp::Subscription<sensor_msgs::msg::CameraInfo>::SharedPtr sub_camerainfo_;
342
343  // FPS statistics
344  rclcpp::Time last_print_{0, 0, RCL_ROS_TIME};
345  std::deque<rclcpp::Time> arrivals_;
346
347  // Video writer
348  cv::VideoWriter video_writer_;
349};
350
351int main(int argc, char **argv) {
352  rclcpp::init(argc, argv);
353  auto node = std::make_shared<StereoCameraTopicEcho>();
354  rclcpp::spin(node);
355  rclcpp::shutdown();
356  return 0;
357}
```

**Usage Instructions:**

1. Subscribe to left camera RGB image:

   ```
   ros2 run examples echo_camera_stereo --ros-args -p topic_type:=left_rgb_image
   ```
2. Subscribe to right camera RGB image:

   ```
   ros2 run examples echo_camera_stereo --ros-args -p topic_type:=right_rgb_image
   ```
3. Subscribe to left camera intrinsic parameters:

   ```
   ros2 run examples echo_camera_stereo --ros-args -p topic_type:=left_camera_info
   ```
4. Record left camera video:

   ```
   # The value of dump_video_path can be changed to another path; make sure the directory exists beforehand
   ros2 run examples echo_camera_stereo --ros-args -p topic_type:=left_rgb_image -p dump_video_path:=$PWD/left_camera.avi
   ```

### Rear Head Monocular Camera Data Subscription

**This example uses echo\_camera\_head\_rear**, subscribing to the `/aima/hal/sensor/rgb_head_rear/` topic to receive data from the robot’s rear head monocular camera, supporting RGB images (with/without mask), compressed images, and camera intrinsic parameters.

**Features:**

- Supports rear head camera data subscription
- Real-time FPS statistics and data display
- Supports RGB video recording with/without obstructed area masked
- Configurable topic type selection

**Supported Data Types:**

- `rgb_image`: RGB image (sensor\_msgs/Image)
- `rgb_image_compressed`: Compressed RGB image (sensor\_msgs/CompressedImage)
- `camera_info`: Camera intrinsic parameters (sensor\_msgs/CameraInfo)

```
  1#include <deque>
  2#include <filesystem>
  3#include <iomanip>
  4#include <memory>
  5#include <rclcpp/rclcpp.hpp>
  6#include <sensor_msgs/msg/camera_info.hpp>
  7#include <sensor_msgs/msg/compressed_image.hpp>
  8#include <sensor_msgs/msg/image.hpp>
  9#include <sstream>
 10#include <string>
 11#include <vector>
 12
 13// OpenCV headers for image/video writing
 14#include <cv_bridge/cv_bridge.h>
 15#include <opencv2/opencv.hpp>
 16
 17/**
 18 * @brief Example of subscribing to multiple topics for the rear head monocular
 19 * camera
 20 *
 21 * You can select which topic type to subscribe to via the startup argument
 22 * --ros-args -p topic_type:=<type>:
 23 *   - rgb_image: RGB image (sensor_msgs/Image)
 24 *   - rgb_image_compressed: RGB compressed image (sensor_msgs/CompressedImage)
 25 *   - camera_info: Camera intrinsic parameters (sensor_msgs/CameraInfo)
 26 *
 27 * Examples:
 28 *   ros2 run examples echo_camera_head_rear --ros-args -p topic_type:=rgb_image
 29 *   ros2 run examples echo_camera_head_rear --ros-args -p
 30 * topic_type:=rgb_image_compressed ros2 run examples echo_camera_head_rear
 31 * --ros-args -p topic_type:=camera_info
 32 *
 33 * topic_type defaults to "rgb_image"
 34 *
 35 * See individual callbacks for more detailed comments
 36 */
 37class HeadRearCameraTopicEcho : public rclcpp::Node {
 38public:
 39  HeadRearCameraTopicEcho() : Node("head_rear_camera_topic_echo") {
 40    // Select which topic type to subscribe to
 41    topic_type_ = declare_parameter<std::string>("topic_type", "rgb_image");
 42    dump_video_path_ = declare_parameter<std::string>("dump_video_path", "");
 43    with_mask_ = declare_parameter<bool>("with_mask", false);
 44
 45    // Subscribed topics and their message layouts
 46    // 1. /aima/hal/sensor/rgb_head_rear/rgb_image
 47    //    - topic_type: rgb_image
 48    //    - message type: sensor_msgs::msg::Image
 49    //    - frame_id: rgb_head_rear
 50    //    - child_frame_id: /
 51    //    - contents: raw image data
 52    // 2. /aima/hal/sensor/rgb_head_rear/rgb_image/compressed
 53    //    - topic_type: rgb_image_compressed
 54    //    - message type: sensor_msgs::msg::CompressedImage
 55    //    - frame_id: rgb_head_rear
 56    //    - contents: compressed image data
 57    // 3. /aima/hal/sensor/rgb_head_rear/camera_info
 58    //    - topic_type: camera_info
 59    //    - message type: sensor_msgs::msg::CameraInfo
 60    //    - frame_id: rgb_head_rear
 61    //    - contents: camera intrinsic parameters
 62
 63    // Set QoS parameters - use SensorData QoS
 64    auto qos = rclcpp::SensorDataQoS();
 65
 66    if (with_mask_ && !dump_video_path_.empty()) {
 67      auto mask_path =
 68          std::filesystem::read_symlink("/proc/self/exe").parent_path() /
 69          "data" / "rgb_head_rear_mask.png";
 70      mask_image_ = cv::imread(mask_path, cv::IMREAD_GRAYSCALE);
 71      if (mask_image_.empty()) {
 72        RCLCPP_ERROR(get_logger(), "Failed to load mask file from %s",
 73                     mask_path.c_str());
 74        throw std::runtime_error("Failed to load mask file");
 75      }
 76    }
 77
 78    // Enable RGB image subscription
 79    if (topic_type_ == "rgb_image") {
 80      topic_name_ = "/aima/hal/sensor/rgb_head_rear/rgb_image";
 81      sub_image_ = create_subscription<sensor_msgs::msg::Image>(
 82          topic_name_, qos,
 83          std::bind(&HeadRearCameraTopicEcho::cb_image, this,
 84                    std::placeholders::_1));
 85      RCLCPP_INFO(get_logger(), "✅ Subscribing RGB Image: %s",
 86                  topic_name_.c_str());
 87      if (!dump_video_path_.empty()) {
 88        RCLCPP_INFO(
 89            get_logger(), "📝 Will dump received images %s mask to video: %s",
 90            (with_mask_ ? "with" : "without"), dump_video_path_.c_str());
 91      }
 92    }
 93
 94    // Enable RGB compressed image subscription
 95    else if (topic_type_ == "rgb_image_compressed") {
 96      topic_name_ = "/aima/hal/sensor/rgb_head_rear/rgb_image/compressed";
 97      sub_compressed_ = create_subscription<sensor_msgs::msg::CompressedImage>(
 98          topic_name_, qos,
 99          std::bind(&HeadRearCameraTopicEcho::cb_compressed, this,
100                    std::placeholders::_1));
101      RCLCPP_INFO(get_logger(), "✅ Subscribing CompressedImage: %s",
102                  topic_name_.c_str());
103
104      // Enable camera info subscription
105    } else if (topic_type_ == "camera_info") {
106      topic_name_ = "/aima/hal/sensor/rgb_head_rear/camera_info";
107      // CameraInfo subscriptions must use reliable + transient_local
108      // QoS in order to receive latched/history messages (even if only one
109      // message was published). Here we use keep_last(1) + reliable
110      // + transient_local.
111      sub_camerainfo_ = create_subscription<sensor_msgs::msg::CameraInfo>(
112          topic_name_,
113          rclcpp::QoS(rclcpp::KeepLast(1)).reliable().transient_local(),
114          std::bind(&HeadRearCameraTopicEcho::cb_camerainfo, this,
115                    std::placeholders::_1));
116      RCLCPP_INFO(get_logger(),
117                  "✅ Subscribing CameraInfo (with transient_local): %s",
118                  topic_name_.c_str());
119
120      // Unknown topic_type error
121    } else {
122      RCLCPP_ERROR(get_logger(), "Unknown topic_type: %s", topic_type_.c_str());
123      throw std::runtime_error("Unknown topic_type");
124    }
125  }
126
127  ~HeadRearCameraTopicEcho() override {
128    if (video_writer_.isOpened()) {
129      video_writer_.release();
130      RCLCPP_INFO(get_logger(), "Video file closed.");
131    }
132  }
133
134private:
135  // Image callback (RGB image)
136  void cb_image(const sensor_msgs::msg::Image::SharedPtr msg) {
137    update_arrivals();
138
139    if (should_print()) {
140      RCLCPP_INFO(get_logger(),
141                  "📸 %s received\n"
142                  "  • frame_id:        %s\n"
143                  "  • stamp (sec):     %.6f\n"
144                  "  • encoding:        %s\n"
145                  "  • size (WxH):      %u x %u\n"
146                  "  • step (bytes/row):%u\n"
147                  "  • is_bigendian:    %u\n"
148                  "  • recv FPS (1s):   %.1f",
149                  topic_type_.c_str(), msg->header.frame_id.c_str(),
150                  rclcpp::Time(msg->header.stamp).seconds(),
151                  msg->encoding.c_str(), msg->width, msg->height, msg->step,
152                  msg->is_bigendian, get_fps());
153    }
154
155    // Video dump is supported only for RGB images
156    if (topic_type_ == "rgb_image" && !dump_video_path_.empty()) {
157      dump_image_to_video(msg);
158    }
159  }
160
161  // CompressedImage callback (RGB compressed image)
162  void cb_compressed(const sensor_msgs::msg::CompressedImage::SharedPtr msg) {
163    update_arrivals();
164
165    if (should_print()) {
166      RCLCPP_INFO(get_logger(),
167                  "🗜️  %s received\n"
168                  "  • frame_id:        %s\n"
169                  "  • stamp (sec):     %.6f\n"
170                  "  • format:          %s\n"
171                  "  • data size:       %zu\n"
172                  "  • recv FPS (1s):   %.1f",
173                  topic_type_.c_str(), msg->header.frame_id.c_str(),
174                  rclcpp::Time(msg->header.stamp).seconds(),
175                  msg->format.c_str(), msg->data.size(), get_fps());
176    }
177  }
178
179  // CameraInfo callback (camera intrinsic parameters)
180  void cb_camerainfo(const sensor_msgs::msg::CameraInfo::SharedPtr msg) {
181    // CameraInfo is typically published once; print it once
182    std::ostringstream oss;
183    oss << "📷 " << topic_type_ << " received\n"
184        << "  • frame_id:        " << msg->header.frame_id << "\n"
185        << "  • stamp (sec):     " << rclcpp::Time(msg->header.stamp).seconds()
186        << "\n"
187        << "  • width x height:  " << msg->width << " x " << msg->height << "\n"
188        << "  • distortion_model:" << msg->distortion_model << "\n"
189        << "  • D: [";
190    for (size_t i = 0; i < msg->d.size(); ++i) {
191      oss << msg->d[i];
192      if (i + 1 < msg->d.size())
193        oss << ", ";
194    }
195    oss << "]\n  • K: [";
196    for (int i = 0; i < 9; ++i) {
197      oss << msg->k[i];
198      if (i + 1 < 9)
199        oss << ", ";
200    }
201    oss << "]\n  • R: [";
202    for (int i = 0; i < 9; ++i) {
203      oss << msg->r[i];
204      if (i + 1 < 9)
205        oss << ", ";
206    }
207    oss << "]\n  • P: [";
208    for (int i = 0; i < 12; ++i) {
209      oss << msg->p[i];
210      if (i + 1 < 12)
211        oss << ", ";
212    }
213    oss << "]\n"
214        << "  • binning_x: " << msg->binning_x << "\n"
215        << "  • binning_y: " << msg->binning_y << "\n"
216        << "  • roi: { x_offset: " << msg->roi.x_offset
217        << ", y_offset: " << msg->roi.y_offset
218        << ", height: " << msg->roi.height << ", width: " << msg->roi.width
219        << ", do_rectify: " << (msg->roi.do_rectify ? "true" : "false") << " }";
220    RCLCPP_INFO(get_logger(), "%s", oss.str().c_str());
221  }
222
223  // Track arrival timestamps to compute FPS
224  void update_arrivals() {
225    const rclcpp::Time now = this->get_clock()->now();
226    arrivals_.push_back(now);
227    while (!arrivals_.empty() && (now - arrivals_.front()).seconds() > 1.0) {
228      arrivals_.pop_front();
229    }
230  }
231  double get_fps() const { return static_cast<double>(arrivals_.size()); }
232
233  // Control printing frequency
234  bool should_print() {
235    const rclcpp::Time now = this->get_clock()->now();
236    if ((now - last_print_).seconds() >= 1.0) {
237      last_print_ = now;
238      return true;
239    }
240    return false;
241  }
242
243  // Dump received images to a video file (RGB images only)
244  void dump_image_to_video(const sensor_msgs::msg::Image::SharedPtr &msg) {
245    cv::Mat image;
246    try {
247      // Obtain the Mat without copying by not specifying encoding
248      cv_bridge::CvImageConstPtr cvp = cv_bridge::toCvShare(msg);
249      image = cvp->image;
250      // Convert to BGR for uniform saving
251      if (msg->encoding == "rgb8") {
252        cv::cvtColor(image, image, cv::COLOR_RGB2BGR);
253      } else {
254        RCLCPP_WARN(get_logger(), "image encoding not expected: %s",
255                    msg->encoding.c_str());
256        return;
257      }
258      if (with_mask_) {
259        image.setTo(cv::Scalar(0, 0, 0), mask_image_ == 0);
260      }
261    } catch (const std::exception &e) {
262      RCLCPP_WARN(get_logger(), "cv_bridge exception: %s", e.what());
263      return;
264    }
265
266    // Initialize VideoWriter
267    if (!video_writer_.isOpened()) {
268      int fourcc = cv::VideoWriter::fourcc('M', 'J', 'P', 'G');
269      double fps = std::max(1.0, get_fps());
270      bool ok = video_writer_.open(dump_video_path_, fourcc, fps,
271                                   cv::Size(image.cols, image.rows), true);
272      if (!ok) {
273        RCLCPP_ERROR(get_logger(), "Failed to open video file: %s",
274                     dump_video_path_.c_str());
275        dump_video_path_.clear(); // stop trying
276        return;
277      }
278      RCLCPP_INFO(get_logger(), "VideoWriter started: %s, size=%dx%d, fps=%.1f",
279                  dump_video_path_.c_str(), image.cols, image.rows, fps);
280    }
281    video_writer_.write(image);
282  }
283
284  // Member variables
285  std::string topic_type_;
286  std::string topic_name_;
287  std::string dump_video_path_;
288  bool with_mask_;
289  cv::Mat mask_image_;
290
291  // Subscriptions
292  rclcpp::Subscription<sensor_msgs::msg::Image>::SharedPtr sub_image_;
293  rclcpp::Subscription<sensor_msgs::msg::CompressedImage>::SharedPtr
294      sub_compressed_;
295  rclcpp::Subscription<sensor_msgs::msg::CameraInfo>::SharedPtr sub_camerainfo_;
296
297  // FPS statistics
298  rclcpp::Time last_print_{0, 0, RCL_ROS_TIME};
299  std::deque<rclcpp::Time> arrivals_;
300
301  // Video writer
302  cv::VideoWriter video_writer_;
303};
304
305int main(int argc, char **argv) {
306  rclcpp::init(argc, argv);
307  auto node = std::make_shared<HeadRearCameraTopicEcho>();
308  rclcpp::spin(node);
309  rclcpp::shutdown();
310  return 0;
311}
```

**Usage Instructions:**

1. Subscribe to RGB image data:

   ```
   ros2 run examples echo_camera_head_rear --ros-args -p topic_type:=rgb_image
   ```
2. Subscribe to compressed image data:

   ```
   ros2 run examples echo_camera_head_rear --ros-args -p topic_type:=rgb_image_compressed
   ```
3. Subscribe to camera intrinsic parameters:

   ```
   ros2 run examples echo_camera_head_rear --ros-args -p topic_type:=camera_info
   ```
4. Record video:

   ```
   # The value of dump_video_path can be changed to another path; make sure the directory exists beforehand
   ros2 run examples echo_camera_head_rear --ros-args -p topic_type:=rgb_image -p dump_video_path:=$PWD/rear_camera.avi
   ```
5. Record video and mask obstructed area:

   ```
   # The value of dump_video_path can be changed to another path; make sure the directory exists beforehand
   ros2 run examples echo_camera_head_rear --ros-args -p topic_type:=rgb_image -p with_mask:=true -p dump_video_path:=$PWD/rear_camera.avi
   ```

**Application Scenarios:**

- Face recognition and tracking
- Object detection and recognition
- Visual SLAM
- Image processing and computer vision algorithm development
- Robot visual navigation

## 6.2.13 Head touch sensor data subscription

**This example uses echo\_head\_touch\_sensor**, which subscribes to the `/aima/hal/sensor/touch_head` topic to receive the robot’s touch sensor data on the head.

**Features:**

- The event data would change from “IDLE” to “TOUCH” when robot’s head touched

```
 1//
 2// Created by agiuser on 2026/1/23.
 3//
 4
 5#include <aimdk_msgs/msg/touch_state.hpp>
 6#include <rclcpp/rclcpp.hpp>
 7
 8class TouchStateSubscriber : public rclcpp::Node {
 9public:
10  TouchStateSubscriber() : Node("touch_state_subscriber") {
11    subscription_ = this->create_subscription<aimdk_msgs::msg::TouchState>(
12        "/aima/hal/sensor/touch_head", 10,
13        std::bind(&TouchStateSubscriber::touch_callback, this,
14                  std::placeholders::_1));
15
16    RCLCPP_INFO(this->get_logger(), "TouchState subscriber started, listening "
17                                    "to /aima/hal/sensor/touch_head");
18  }
19
20private:
21  void touch_callback(const aimdk_msgs::msg::TouchState::SharedPtr msg) {
22    // print message info
23    RCLCPP_INFO(this->get_logger(), "Received TouchState message:");
24    RCLCPP_INFO(this->get_logger(), "  Timestamp: %d.%09d",
25                msg->header.stamp.sec, msg->header.stamp.nanosec);
26
27    std::string event_str = get_event_type_string(msg->event_type);
28    RCLCPP_INFO(this->get_logger(), "  Event Type: %s (%d)", event_str.c_str(),
29                msg->event_type);
30  }
31
32  std::string get_event_type_string(uint8_t event_type) {
33    switch (event_type) {
34    case aimdk_msgs::msg::TouchState::UNKNOWN:
35      return "UNKNOWN";
36    case aimdk_msgs::msg::TouchState::IDLE:
37      return "IDLE";
38    case aimdk_msgs::msg::TouchState::TOUCH:
39      return "TOUCH";
40    case aimdk_msgs::msg::TouchState::SLIDE:
41      return "SLIDE";
42    case aimdk_msgs::msg::TouchState::PAT_ONCE:
43      return "PAT_ONCE";
44    case aimdk_msgs::msg::TouchState::PAT_TWICE:
45      return "PAT_TWICE";
46    case aimdk_msgs::msg::TouchState::PAT_TRIPLE:
47      return "PAT_TRIPLE";
48    default:
49      return "INVALID";
50    }
51  }
52  rclcpp::Subscription<aimdk_msgs::msg::TouchState>::SharedPtr subscription_;
53};
54
55int main(int argc, char *argv[]) {
56  rclcpp::init(argc, argv);
57  auto node = std::make_shared<TouchStateSubscriber>();
58  rclcpp::spin(node);
59  rclcpp::shutdown();
60  return 0;
61}
```

**Usage Instructions:**

```
ros2 ros2 run examples echo_head_touch_sensor
```

**Example Output:**

```
[INFO] [1769162721.359354722] [touch_state_subscriber]:   Timestamp: 1769162726.863282315
[INFO] [1769162721.359361643] [touch_state_subscriber]:   Event Type: IDLE (1)
[INFO] [1769167184.142143492] [touch_state_subscriber]:   Timestamp: 1769167189.364879133
[INFO] [1769167184.142147126] [touch_state_subscriber]:   Event Type: TOUCH (2)
```

## 6.2.14 LiDAR Data Subscription

**This example uses echo\_lidar\_data**, subscribing to the `/aima/hal/sensor/lidar_chest_front/` topic to receive LiDAR data, supporting both point cloud data and IMU data types.

**Features:**

- Supports LiDAR point cloud subscription
- Supports LiDAR IMU data subscription
- Real-time FPS statistics and data display
- Configurable topic type selection
- Detailed output of data field information

**Supported Data Types:**

- `PointCloud2`: LiDAR point cloud data (sensor\_msgs/PointCloud2)
- `Imu`: LiDAR IMU data (sensor\_msgs/Imu)

**Technical Implementation:**

- Uses SensorDataQoS configuration (`BEST_EFFORT` + `VOLATILE`)
- Supports parsing and displaying point cloud field information
- Supports IMU quaternion, angular velocity, and linear acceleration data
- Provides detailed debugging log output

**Application Scenarios:**

- LiDAR data acquisition and analysis
- Point cloud data processing and visualization
- Robot navigation and localization
- SLAM algorithm development
- Environmental perception and mapping

```
  1#include <deque>
  2#include <iomanip>
  3#include <memory>
  4#include <rclcpp/rclcpp.hpp>
  5#include <sensor_msgs/msg/imu.hpp>
  6#include <sensor_msgs/msg/point_cloud2.hpp>
  7#include <sstream>
  8#include <string>
  9#include <vector>
 10
 11/**
 12 * @brief Example for subscribing to chest LIDAR data
 13 *
 14 * Supports subscribing to the following topics:
 15 *   1. /aima/hal/sensor/lidar_chest_front/lidar_pointcloud
 16 *      - Data type: sensor_msgs::msg::PointCloud2
 17 *      - frame_id: lidar_chest_front
 18 *      - child_frame_id: /
 19 *      - Content: LIDAR point cloud data
 20 *   2. /aima/hal/sensor/lidar_chest_front/imu
 21 *      - Data type: sensor_msgs::msg::Imu
 22 *      - frame_id: lidar_imu_chest_front
 23 *      - Content: LIDAR IMU data
 24 *
 25 * You can select the topic type to subscribe to using the launch parameter
 26 * --ros-args -p topic_type:=<type>:
 27 *   - pointcloud: Subscribe to LIDAR point cloud
 28 *   - imu: Subscribe to LIDAR IMU
 29 * The default topic_type is pointcloud
 30 */
 31class LidarChestEcho : public rclcpp::Node {
 32public:
 33  LidarChestEcho() : Node("lidar_chest_echo") {
 34    topic_type_ = declare_parameter<std::string>("topic_type", "pointcloud");
 35
 36    auto qos = rclcpp::SensorDataQoS();
 37
 38    if (topic_type_ == "pointcloud") {
 39      topic_name_ = "/aima/hal/sensor/lidar_chest_front/lidar_pointcloud";
 40      sub_pointcloud_ = create_subscription<sensor_msgs::msg::PointCloud2>(
 41          topic_name_, qos,
 42          std::bind(&LidarChestEcho::cb_pointcloud, this,
 43                    std::placeholders::_1));
 44      RCLCPP_INFO(get_logger(), "✅ Subscribing LIDAR PointCloud2: %s",
 45                  topic_name_.c_str());
 46    } else if (topic_type_ == "imu") {
 47      topic_name_ = "/aima/hal/sensor/lidar_chest_front/imu";
 48      sub_imu_ = create_subscription<sensor_msgs::msg::Imu>(
 49          topic_name_, qos,
 50          std::bind(&LidarChestEcho::cb_imu, this, std::placeholders::_1));
 51      RCLCPP_INFO(get_logger(), "✅ Subscribing LIDAR IMU: %s",
 52                  topic_name_.c_str());
 53    } else {
 54      RCLCPP_ERROR(get_logger(), "Unknown topic_type: %s", topic_type_.c_str());
 55      throw std::runtime_error("Unknown topic_type");
 56    }
 57  }
 58
 59private:
 60  // PointCloud2 callback
 61  void cb_pointcloud(const sensor_msgs::msg::PointCloud2::SharedPtr msg) {
 62    update_arrivals();
 63
 64    if (should_print()) {
 65      std::ostringstream oss;
 66      oss << "🟢 LIDAR PointCloud2 received\n"
 67          << "  • frame_id:        " << msg->header.frame_id << "\n"
 68          << "  • stamp (sec):     "
 69          << rclcpp::Time(msg->header.stamp).seconds() << "\n"
 70          << "  • width x height:  " << msg->width << " x " << msg->height
 71          << "\n"
 72          << "  • point_step:      " << msg->point_step << "\n"
 73          << "  • row_step:        " << msg->row_step << "\n"
 74          << "  • fields:          ";
 75      for (const auto &f : msg->fields)
 76        oss << f.name << "(" << (int)f.datatype << ") ";
 77      oss << "\n  • is_bigendian:    " << msg->is_bigendian
 78          << "\n  • is_dense:        " << msg->is_dense
 79          << "\n  • data size:       " << msg->data.size()
 80          << "\n  • recv FPS (1s):   " << get_fps();
 81      RCLCPP_INFO(get_logger(), "%s", oss.str().c_str());
 82    }
 83  }
 84
 85  // IMU callback
 86  void cb_imu(const sensor_msgs::msg::Imu::SharedPtr msg) {
 87    update_arrivals();
 88
 89    if (should_print()) {
 90      std::ostringstream oss;
 91      oss << "🟢 LIDAR IMU received\n"
 92          << "  • frame_id:        " << msg->header.frame_id << "\n"
 93          << "  • stamp (sec):     "
 94          << rclcpp::Time(msg->header.stamp).seconds() << "\n"
 95          << "  • orientation:     [" << msg->orientation.x << ", "
 96          << msg->orientation.y << ", " << msg->orientation.z << ", "
 97          << msg->orientation.w << "]\n"
 98          << "  • angular_velocity:[" << msg->angular_velocity.x << ", "
 99          << msg->angular_velocity.y << ", " << msg->angular_velocity.z << "]\n"
100          << "  • linear_accel:    [" << msg->linear_acceleration.x << ", "
101          << msg->linear_acceleration.y << ", " << msg->linear_acceleration.z
102          << "]\n"
103          << "  • recv FPS (1s):   " << get_fps();
104      RCLCPP_INFO(get_logger(), "%s", oss.str().c_str());
105    }
106  }
107
108  // Update FPS statistics
109  void update_arrivals() {
110    const rclcpp::Time now = this->get_clock()->now();
111    arrivals_.push_back(now);
112    while (!arrivals_.empty() && (now - arrivals_.front()).seconds() > 1.0) {
113      arrivals_.pop_front();
114    }
115  }
116  double get_fps() const { return static_cast<double>(arrivals_.size()); }
117
118  // Control print frequency
119  bool should_print() {
120    const rclcpp::Time now = this->get_clock()->now();
121    if ((now - last_print_).seconds() >= 1.0) {
122      last_print_ = now;
123      return true;
124    }
125    return false;
126  }
127
128  // Member variables
129  std::string topic_type_;
130  std::string topic_name_;
131
132  rclcpp::Subscription<sensor_msgs::msg::PointCloud2>::SharedPtr
133      sub_pointcloud_;
134  rclcpp::Subscription<sensor_msgs::msg::Imu>::SharedPtr sub_imu_;
135
136  rclcpp::Time last_print_{0, 0, RCL_ROS_TIME};
137  std::deque<rclcpp::Time> arrivals_;
138};
139
140int main(int argc, char **argv) {
141  rclcpp::init(argc, argv);
142  auto node = std::make_shared<LidarChestEcho>();
143  rclcpp::spin(node);
144  rclcpp::shutdown();
145  return 0;
146}
```

**Usage Instructions:**

```
# Subscribe to LiDAR point cloud data
ros2 run examples echo_lidar_data --ros-args -p topic_type:=pointcloud

# Subscribe to LiDAR IMU data
ros2 run examples echo_lidar_data --ros-args -p topic_type:=imu
```

**Example Output:**

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

## 6.2.15 Play Video

**This example uses play\_video.** Before running the node, you must upload the video file to the robot’s **Interaction Computing Unit (PC3)** (you may create a directory there to store videos, e.g. /var/tmp/videos/). Then, modify the `video_path` in the node program to the path of the video you want to play.

Attention

**⚠️ Warning! The Interaction Computing Unit (PC3) is independent from the Development Computing Unit (PC2) where secondary development programs run. Audio and video files must be stored on the Interaction Computing Unit (IP: 10.0.1.42).**
**Audio and video files (and all parent directories up to root) must be readable by all users(new subdirectory under /var/tmp/ is recommended)**

**Function Description** By calling the `PlayVideo` service, the robot can play a video file located at a specified path on its screen. Ensure the video file has been uploaded to the Interaction Computing Unit, otherwise playback will fail.

```
  1#include "aimdk_msgs/srv/play_video.hpp"
  2#include "aimdk_msgs/msg/common_request.hpp"
  3#include "rclcpp/rclcpp.hpp"
  4#include <chrono>
  5#include <memory>
  6#include <signal.h>
  7#include <string>
  8
  9// Global variable used for signal handling
 10std::shared_ptr<rclcpp::Node> g_node = nullptr;
 11
 12// Signal handler function
 13void signal_handler(int signal) {
 14  if (g_node) {
 15    RCLCPP_INFO(g_node->get_logger(), "Received signal %d, shutting down...",
 16                signal);
 17    g_node.reset();
 18  }
 19  rclcpp::shutdown();
 20  exit(signal);
 21}
 22
 23class PlayVideoClient : public rclcpp::Node {
 24public:
 25  PlayVideoClient() : Node("play_video_client") {
 26    client_ = this->create_client<aimdk_msgs::srv::PlayVideo>(
 27        "/face_ui_proxy/play_video");
 28    RCLCPP_INFO(this->get_logger(), "✅ PlayVideo client node started.");
 29
 30    // Wait for the service to become available
 31    while (!client_->wait_for_service(std::chrono::seconds(2))) {
 32      RCLCPP_INFO(this->get_logger(), "⏳ Service unavailable, waiting...");
 33    }
 34    RCLCPP_INFO(this->get_logger(),
 35                "🟢 Service available, ready to send request.");
 36  }
 37
 38  bool send_request(const std::string &video_path, uint8_t mode,
 39                    int32_t priority) {
 40    try {
 41      auto request = std::make_shared<aimdk_msgs::srv::PlayVideo::Request>();
 42
 43      request->video_path = video_path;
 44      request->mode = mode;
 45      request->priority = priority;
 46
 47      RCLCPP_INFO(this->get_logger(),
 48                  "📨 Sending request to play video: mode=%hhu video=%s", mode,
 49                  video_path.c_str());
 50
 51      const std::chrono::milliseconds timeout(250);
 52      for (int i = 0; i < 8; i++) {
 53        request->header.header.stamp = this->now();
 54        auto future = client_->async_send_request(request);
 55        auto retcode = rclcpp::spin_until_future_complete(shared_from_this(),
 56                                                          future, timeout);
 57        if (retcode != rclcpp::FutureReturnCode::SUCCESS) {
 58          // retry as remote peer is NOT handled well by ROS
 59          RCLCPP_INFO(this->get_logger(), "trying ... [%d]", i);
 60          continue;
 61        }
 62        // future.done
 63        auto response = future.get();
 64        if (response->success) {
 65          RCLCPP_INFO(this->get_logger(),
 66                      "✅ Request to play video recorded successfully: %s",
 67                      response->message.c_str());
 68          return true;
 69        } else {
 70          RCLCPP_ERROR(this->get_logger(),
 71                       "❌ Failed to record play-video request: %s",
 72                       response->message.c_str());
 73          return false;
 74        }
 75      }
 76      RCLCPP_ERROR(this->get_logger(), "❌ Service call failed or timed out.");
 77      return false;
 78    } catch (const std::exception &e) {
 79      RCLCPP_ERROR(this->get_logger(), "Exception occurred: %s", e.what());
 80      return false;
 81    }
 82  }
 83
 84private:
 85  rclcpp::Client<aimdk_msgs::srv::PlayVideo>::SharedPtr client_;
 86};
 87
 88int main(int argc, char **argv) {
 89  try {
 90    rclcpp::init(argc, argv);
 91
 92    // Set up signal handlers
 93    signal(SIGINT, signal_handler);
 94    signal(SIGTERM, signal_handler);
 95
 96    std::string video_path =
 97        "/agibot/data/home/agi/zhiyuan.mp4"; // Default video path; modify as
 98                                             // needed
 99    int32_t priority = 5;
100    int mode = 2; // Loop playback
101    std::cout << "Enter video play mode (1: once, 2: loop): ";
102    std::cin >> mode;
103    if (mode < 1 || mode > 2) {
104      RCLCPP_ERROR(rclcpp::get_logger("main"), "Invalid play mode: %d", mode);
105      rclcpp::shutdown();
106      return 1;
107    }
108
109    g_node = std::make_shared<PlayVideoClient>();
110    auto client = std::dynamic_pointer_cast<PlayVideoClient>(g_node);
111
112    if (client) {
113      client->send_request(video_path, mode, priority);
114    }
115
116    // Clean up resources
117    g_node.reset();
118    rclcpp::shutdown();
119
120    return 0;
121  } catch (const std::exception &e) {
122    RCLCPP_ERROR(rclcpp::get_logger("main"),
123                 "Program exited with exception: %s", e.what());
124    return 1;
125  }
126}
```

## 6.2.16 Media File Playback

**This example uses play\_media**, enabling playback of specified media files (such as audio files). It supports audio formats including WAV and MP3.

**Features:**

- Supports multiple audio formats (WAV, MP3, etc.)
- Supports priority control, allowing playback priority configuration
- Supports interruption mechanism, allowing ongoing playback to be interrupted
- Supports custom file paths and playback parameters
- Provides complete error handling and playback status feedback

**Technical Implementation:**

- Uses the PlayMediaFile service to play media files
- Supports priority level settings (0–99)
- Supports interrupt control (via the is\_interrupted parameter)
- Provides detailed playback status feedback

**Application Scenarios:**

- Audio playback and media control
- Voice prompts and sound effects playback
- Multimedia application development
- Robot interaction audio feedback

Attention

**⚠️ Warning! The Interaction Computing Unit (PC3) is independent from the Development Computing Unit (PC2) where secondary development programs run. Audio and video files must be stored on the Interaction Computing Unit (IP: 10.0.1.42).**
**Audio and video files (and all parent directories up to root) must be readable by all users(new subdirectory under /var/tmp/ is recommended)**

```
 1#include <aimdk_msgs/msg/tts_priority_level.hpp>
 2#include <aimdk_msgs/srv/play_media_file.hpp>
 3#include <iostream>
 4#include <rclcpp/rclcpp.hpp>
 5#include <string>
 6
 7using PlayMediaFile = aimdk_msgs::srv::PlayMediaFile;
 8
 9int main(int argc, char **argv) {
10  rclcpp::init(argc, argv);
11  auto node = rclcpp::Node::make_shared("play_media_file_client_min");
12
13  // 1) Service name
14  const std::string service_name = "/aimdk_5Fmsgs/srv/PlayMediaFile";
15  auto client = node->create_client<PlayMediaFile>(service_name);
16
17  // 2) Input file path (prompt user if not provided as argument)
18  std::string default_file =
19      "/agibot/data/var/interaction/tts_cache/normal/demo.wav";
20  std::string file_name;
21
22  if (argc > 1) {
23    file_name = argv[1];
24  } else {
25    std::cout << "Enter the media file path to play (default: " << default_file
26              << "): ";
27    std::getline(std::cin, file_name);
28    if (file_name.empty()) {
29      file_name = default_file;
30    }
31  }
32
33  // 3) Build the request
34  auto req = std::make_shared<PlayMediaFile::Request>();
35  // CommonRequest request -> RequestHeader header -> builtin_interfaces/Time
36  // stamp
37  req->header.header.stamp = node->now();
38
39  // PlayMediaFileRequest required fields
40  req->media_file_req.file_name = file_name;
41  req->media_file_req.domain = "demo_client"; // Required: identifies the caller
42  req->media_file_req.trace_id = "demo";      // Optional: request identifier
43  req->media_file_req.is_interrupted =
44      true; // Whether to interrupt same-priority playback
45  req->media_file_req.priority_weight = 0; // Optional: 0~99
46  // Priority level: default INTERACTION_L6
47  req->media_file_req.priority_level.value = 6;
48
49  // 4) Wait for service and call
50  RCLCPP_INFO(node->get_logger(), "Waiting for service: %s",
51              service_name.c_str());
52  if (!client->wait_for_service(std::chrono::seconds(5))) {
53    RCLCPP_ERROR(node->get_logger(), "Service unavailable: %s",
54                 service_name.c_str());
55    rclcpp::shutdown();
56    return 1;
57  }
58
59  auto future = client->async_send_request(req);
60  auto rc = rclcpp::spin_until_future_complete(node, future,
61                                               std::chrono::seconds(10));
62
63  if (rc == rclcpp::FutureReturnCode::INTERRUPTED) {
64    RCLCPP_WARN(node->get_logger(), "Interrupted while waiting");
65    rclcpp::shutdown();
66    return 1;
67  }
68
69  if (rc != rclcpp::FutureReturnCode::SUCCESS) {
70    RCLCPP_ERROR(node->get_logger(), "Call timed out or did not complete");
71    rclcpp::shutdown();
72    return 1;
73  }
74
75  // 5) Handle response (success is in tts_resp)
76  try {
77    const auto resp = future.get();
78    bool success = resp->tts_resp.is_success;
79
80    if (success) {
81      RCLCPP_INFO(node->get_logger(), "✅ Media file play request succeeded: %s",
82                  file_name.c_str());
83    } else {
84      RCLCPP_ERROR(node->get_logger(), "❌ Media file play request failed: %s",
85                   file_name.c_str());
86    }
87  } catch (const std::exception &e) {
88    RCLCPP_ERROR(node->get_logger(), "Call exception: %s", e.what());
89  }
90
91  rclcpp::shutdown();
92  return 0;
93}
```

**Usage Instructions:**

```
# Play default audio file
ros2 run examples play_media

# Play a specified audio file
# Replace /path/to/your/audio_file.wav with the actual file path on the interaction board
ros2 run examples play_media /path/to/your/audio_file.wav

# Play TTS cached audio file
ros2 run examples play_media /agibot/data/var/interaction/tts_cache/normal/demo.wav
```

**Example Output:**

```
[INFO] [play_media_file_client_min]: ✅ Media file playback request succeeded
```

**Notes:**

- Ensure the audio file path is correct and the file exists
- Supported file formats: WAV, MP3, etc.
- Priority settings affect playback queue order
- Interruption mechanism can stop the currently playing audio

## 6.2.17 TTS (Text-to-Speech)

**This example uses play\_tts**, enabling the robot to speak the provided text. Users can input any text depending on the scenario.

**Features:**

- Supports command-line arguments and interactive input
- Includes full service availability checks and error handling
- Supports priority control and interruption mechanism
- Provides detailed playback status feedback

**Core Code**

```
 1#include <aimdk_msgs/msg/tts_priority_level.hpp>
 2#include <aimdk_msgs/srv/play_tts.hpp>
 3#include <iostream>
 4#include <rclcpp/rclcpp.hpp>
 5#include <string>
 6
 7using PlayTTS = aimdk_msgs::srv::PlayTts;
 8
 9int main(int argc, char **argv) {
10  rclcpp::init(argc, argv);
11  auto node = rclcpp::Node::make_shared("play_tts_client_min");
12
13  const std::string service_name = "/aimdk_5Fmsgs/srv/PlayTts";
14  auto client = node->create_client<PlayTTS>(service_name);
15
16  // Get text to speak
17  std::string tts_text;
18  if (argc > 1) {
19    tts_text = argv[1];
20  } else {
21    std::cout << "Enter text to speak: ";
22    std::getline(std::cin, tts_text);
23    if (tts_text.empty()) {
24      tts_text = "Hello, I am AgiBot X2.";
25    }
26  }
27
28  auto req = std::make_shared<PlayTTS::Request>();
29  req->header.header.stamp = node->now();
30  req->tts_req.text = tts_text;
31  req->tts_req.domain = "demo_client"; // Required: identifies the caller
32  req->tts_req.trace_id =
33      "demo"; // Optional: request identifier for the TTS request
34  req->tts_req.is_interrupted =
35      true; // Required: whether to interrupt same-priority playback
36  req->tts_req.priority_weight = 0;
37  req->tts_req.priority_level.value = 6;
38
39  if (!client->wait_for_service(
40          std::chrono::duration_cast<std::chrono::seconds>(
41              std::chrono::seconds(5)))) {
42    RCLCPP_ERROR(node->get_logger(), "Service unavailable: %s",
43                 service_name.c_str());
44    rclcpp::shutdown();
45    return 1;
46  }
47
48  auto future = client->async_send_request(req);
49  if (rclcpp::spin_until_future_complete(
50          node, future,
51          std::chrono::duration_cast<std::chrono::seconds>(
52              std::chrono::seconds(10))) != rclcpp::FutureReturnCode::SUCCESS) {
53    RCLCPP_ERROR(node->get_logger(), "Call timed out");
54    rclcpp::shutdown();
55    return 1;
56  }
57
58  const auto resp = future.get();
59  if (resp->tts_resp.is_success) {
60    RCLCPP_INFO(node->get_logger(), "✅ TTS play request succeeded");
61  } else {
62    RCLCPP_ERROR(node->get_logger(), "❌ TTS play request failed");
63  }
64
65  rclcpp::shutdown();
66  return 0;
67}
```

**Usage Instructions**

```
# Use command-line arguments to speak text (recommended)
ros2 run examples play_tts "Hello, I am the AgiBot X2 robot"

# Or run without arguments; the program will prompt for input
ros2 run examples play_tts
```

**Output Example**

```
[INFO] [play_tts_client_min]: ✅ TTS request succeeded
```

**Notes**

- Ensure the TTS service is running properly
- Supports both Chinese and English text-to-speech
- Priority settings affect playback queue order
- Interruption mechanism can stop the currently playing speech

**Interface Reference**

- Service: `/aimdk_5Fmsgs/srv/PlayTts`
- Message: `aimdk_msgs/srv/PlayTts`

## 6.2.18 Microphone Audio Reception

**This example uses mic\_receiver**, subscribing to the `/agent/process_audio_output` topic to receive the robot’s noise-reduced audio stream. It supports both internal and external microphone audio streams, and automatically saves complete speech segments as PCM files based on VAD (Voice Activity Detection) states.

**Features:**

- Supports receiving multiple audio streams simultaneously (internal mic stream\_id=1, external mic stream\_id=2)
- Automatically detects speech start, processing, and end based on VAD state
- Automatically saves complete speech segments as PCM files
- Stores files organized by timestamp and audio stream ID
- Supports audio duration calculation and statistical output

**VAD State Description:**

- `0`: No speech
- `1`: Speech start
- `2`: Speech processing
- `3`: Speech end

```
  1#include <aimdk_msgs/msg/audio_vad_state_type.hpp>
  2#include <aimdk_msgs/msg/processed_audio_output.hpp>
  3#include <chrono>
  4#include <ctime>
  5#include <filesystem>
  6#include <fstream>
  7#include <iomanip>
  8#include <rclcpp/rclcpp.hpp>
  9#include <sstream>
 10#include <string>
 11#include <unordered_map>
 12#include <vector>
 13
 14namespace fs = std::filesystem;
 15
 16class AudioSubscriber : public rclcpp::Node {
 17public:
 18  AudioSubscriber() : rclcpp::Node("audio_subscriber") {
 19    // Audio buffers, stored separately by stream_id
 20    // stream_id -> buffer
 21    audio_buffers_ = {};
 22    recording_state_ = {};
 23
 24    audio_output_dir_ = "audio_recordings";
 25    fs::create_directories(audio_output_dir_);
 26
 27    // Note: deep queue to avoid missing data in a burst at start of VAD.
 28    auto qos = rclcpp::QoS(
 29        rclcpp::QoSInitialization::from_rmw(rmw_qos_profile_sensor_data));
 30    qos.keep_last(500).best_effort();
 31
 32    subscription_ =
 33        this->create_subscription<aimdk_msgs::msg::ProcessedAudioOutput>(
 34            "/agent/process_audio_output", qos,
 35            std::bind(&AudioSubscriber::audio_callback, this,
 36                      std::placeholders::_1));
 37
 38    RCLCPP_INFO(this->get_logger(),
 39                "Starting to subscribe to denoised audio data...");
 40  }
 41
 42private:
 43  void
 44  audio_callback(const aimdk_msgs::msg::ProcessedAudioOutput::SharedPtr msg) {
 45    try {
 46      uint32_t stream_id = msg->stream_id;
 47      uint8_t vad_state = msg->audio_vad_state.value;
 48      const std::vector<uint8_t> &audio_data = msg->audio_data;
 49
 50      static const std::unordered_map<uint8_t, std::string> vad_state_names = {
 51          {0, "No Speech"},
 52          {1, "Speech Start"},
 53          {2, "Speech Processing"},
 54          {3, "Speech End"}};
 55      static const std::unordered_map<uint32_t, std::string> stream_names = {
 56          {1, "Internal Microphone"}, {2, "External Microphone"}};
 57
 58      RCLCPP_INFO(this->get_logger(),
 59                  "Audio data received: stream_id=%u, vad_state=%u(%s), "
 60                  "audio_size=%zu bytes",
 61                  stream_id, vad_state,
 62                  vad_state_names.count(vad_state)
 63                      ? vad_state_names.at(vad_state).c_str()
 64                      : "Unknown State",
 65                  audio_data.size());
 66
 67      handle_vad_state(stream_id, vad_state, audio_data);
 68    } catch (const std::exception &e) {
 69      RCLCPP_ERROR(this->get_logger(), "Error processing audio message: %s",
 70                   e.what());
 71    }
 72  }
 73
 74  void handle_vad_state(uint32_t stream_id, uint8_t vad_state,
 75                        const std::vector<uint8_t> &audio_data) {
 76    // Initialize the buffer for this stream_id (if it does not exist)
 77    if (audio_buffers_.count(stream_id) == 0) {
 78      audio_buffers_[stream_id] = std::vector<uint8_t>();
 79      recording_state_[stream_id] = false;
 80    }
 81
 82    static const std::unordered_map<uint8_t, std::string> vad_state_names = {
 83        {0, "No Speech"},
 84        {1, "Speech Start"},
 85        {2, "Speech Processing"},
 86        {3, "Speech End"}};
 87    static const std::unordered_map<uint32_t, std::string> stream_names = {
 88        {1, "Internal Microphone"}, {2, "External Microphone"}};
 89
 90    RCLCPP_INFO(this->get_logger(), "[%s] VAD Atate: %s Audio Data: %zu bytes",
 91                stream_names.count(stream_id)
 92                    ? stream_names.at(stream_id).c_str()
 93                    : ("Unknown Stream " + std::to_string(stream_id)).c_str(),
 94                vad_state_names.count(vad_state)
 95                    ? vad_state_names.at(vad_state).c_str()
 96                    : ("Unknown State" + std::to_string(vad_state)).c_str(),
 97                audio_data.size());
 98
 99    // AUDIO_VAD_STATE_BEGIN
100    if (vad_state == 1) {
101      RCLCPP_INFO(this->get_logger(), "🎤 Speech detected - Start");
102      if (recording_state_[stream_id] == false) {
103        audio_buffers_[stream_id].clear();
104        recording_state_[stream_id] = true;
105      }
106      if (!audio_data.empty()) {
107        audio_buffers_[stream_id].insert(audio_buffers_[stream_id].end(),
108                                         audio_data.begin(), audio_data.end());
109      }
110
111      // AUDIO_VAD_STATE_PROCESSING
112    } else if (vad_state == 2) {
113      RCLCPP_INFO(this->get_logger(), "🔄 Speech Processing...");
114      if (recording_state_[stream_id] && !audio_data.empty()) {
115        audio_buffers_[stream_id].insert(audio_buffers_[stream_id].end(),
116                                         audio_data.begin(), audio_data.end());
117      }
118
119      // AUDIO_VAD_STATE_END
120    } else if (vad_state == 3) {
121      RCLCPP_INFO(this->get_logger(), "✅ Speech End");
122      if (recording_state_[stream_id] && !audio_data.empty()) {
123        audio_buffers_[stream_id].insert(audio_buffers_[stream_id].end(),
124                                         audio_data.begin(), audio_data.end());
125      }
126      if (recording_state_[stream_id] && !audio_buffers_[stream_id].empty()) {
127        save_audio_segment(audio_buffers_[stream_id], stream_id);
128      }
129      recording_state_[stream_id] = false;
130
131      // AUDIO_VAD_STATE_NONE
132    } else if (vad_state == 0) {
133      if (recording_state_[stream_id]) {
134        RCLCPP_INFO(this->get_logger(), "⏹️ Recording state reset");
135        recording_state_[stream_id] = false;
136      }
137    }
138
139    // Output the current buffer status.
140    size_t buffer_size = audio_buffers_[stream_id].size();
141    bool recording = recording_state_[stream_id];
142    RCLCPP_DEBUG(this->get_logger(),
143                 "[Stream %u] Buffer size: %zu bytes, Recording state: %s",
144                 stream_id, buffer_size, recording ? "true" : "false");
145  }
146
147  void save_audio_segment(const std::vector<uint8_t> &audio_data,
148                          uint32_t stream_id) {
149    if (audio_data.empty())
150      return;
151
152    // Get the current timestamp.
153    auto now = std::chrono::system_clock::now();
154    std::time_t t = std::chrono::system_clock::to_time_t(now);
155    auto ms = std::chrono::duration_cast<std::chrono::milliseconds>(
156                  now.time_since_epoch()) %
157              1000;
158
159    std::ostringstream oss;
160    oss << std::put_time(std::localtime(&t), "%Y%m%d_%H%M%S") << "_"
161        << std::setw(3) << std::setfill('0') << ms.count();
162
163    // Create a subdirectory by stream_id.
164    fs::path stream_dir =
165        fs::path(audio_output_dir_) / ("stream_" + std::to_string(stream_id));
166    fs::create_directories(stream_dir);
167
168    static const std::unordered_map<uint32_t, std::string> stream_names = {
169        {1, "internal_mic"}, {2, "external_mic"}};
170    std::string stream_name = stream_names.count(stream_id)
171                                  ? stream_names.at(stream_id)
172                                  : ("stream_" + std::to_string(stream_id));
173    std::string filename = stream_name + "_" + oss.str() + ".pcm";
174    fs::path filepath = stream_dir / filename;
175
176    try {
177      std::ofstream ofs(filepath, std::ios::binary);
178      ofs.write(reinterpret_cast<const char *>(audio_data.data()),
179                audio_data.size());
180      ofs.close();
181      RCLCPP_INFO(this->get_logger(),
182                  "Audio segment saved: %s (size: %zu bytes)", filepath.c_str(),
183                  audio_data.size());
184
185      // Record audio file duration (assuming 16kHz, 16-bit, mono)
186      int sample_rate = 16000;
187      int bits_per_sample = 16;
188      int channels = 1;
189      int bytes_per_sample = bits_per_sample / 8;
190      size_t total_samples = audio_data.size() / (bytes_per_sample * channels);
191      double duration_seconds =
192          static_cast<double>(total_samples) / sample_rate;
193
194      RCLCPP_INFO(this->get_logger(),
195                  "Audio duration: %.2f seconds (%zu samples)",
196                  duration_seconds, total_samples);
197    } catch (const std::exception &e) {
198      RCLCPP_ERROR(this->get_logger(), "Failed to save audio file: %s",
199                   e.what());
200    }
201  }
202
203  // Member variables
204  std::unordered_map<uint32_t, std::vector<uint8_t>> audio_buffers_;
205  std::unordered_map<uint32_t, bool> recording_state_;
206  std::string audio_output_dir_;
207  rclcpp::Subscription<aimdk_msgs::msg::ProcessedAudioOutput>::SharedPtr
208      subscription_;
209};
210
211int main(int argc, char **argv) {
212  rclcpp::init(argc, argv);
213  auto node = std::make_shared<AudioSubscriber>();
214  RCLCPP_INFO(node->get_logger(),
215              "Listening for denoised audio data, press Ctrl+C to exit...");
216  rclcpp::spin(node);
217  rclcpp::shutdown();
218  return 0;
219}
```

**Usage Instructions:**

1. After running the node, an `audio_recordings` directory will be created automatically
2. Audio files are stored by stream\_id:

   - `stream_1/`: Internal microphone audio
   - `stream_2/`: External microphone audio
3. File naming format: `{stream_name}_{timestamp}.pcm`
4. Audio format: 16 kHz, 16-bit, mono PCM
5. You can play the saved PCM file using the following command:

   ```
   aplay -r 16000 -f S16_LE -c 1 external_mic_20250909_133649_738.pcm
   ```
6. You should say wake words to make VAD ready to capture voice

**Example Output:**

```
[INFO] Start subscribing to denoised audio data...
[INFO] Received audio data: stream_id=2, vad_state=1 (Speech Start), audio_size=320 bytes
[INFO] [External Mic] VAD State: Speech Start, Audio: 320 bytes
[INFO] 🎤 Speech detected
[INFO] Received audio data: stream_id=2, vad_state=2 (In Speech), audio_size=320 bytes
[INFO] [External Mic] VAD State: In Speech, Audio: 320 bytes
[INFO] 🔄 Processing speech...
[INFO] Received audio data: stream_id=2, vad_state=3 (Speech End), audio_size=320 bytes
[INFO] [External Mic] VAD State: Speech End, Audio: 320 bytes
[INFO] ✅ Speech ended
[INFO] Audio segment saved: audio_recordings/stream_2/external_mic_20250909_133649_738.pcm (Size: 960 bytes)
[INFO] Audio duration: 0.06 seconds (480 samples)
```

***Example: Playing a PCM audio file (using aplay on Linux)***

Assuming you have recorded and saved the audio file external\_mic\_20250909\_151117\_223.pcm, you can play it using the following command:

```
aplay -r 16000 -f S16_LE -c 1 audio_recordings/stream_2/external_mic_20250909_151117_223.pcm
```

Parameter explanation:

- -r 16000 # Sampling rate 16 kHz
- -f S16\_LE # 16-bit little-endian format
- -c 1 # Mono. You may also use other audio players (e.g., Audacity) to import and play raw PCM files.

Note: If you recorded audio from the internal microphone, the path should be audio\_recordings/stream\_1/internal\_mic\_xxx.pcm

## 6.2.19 Emoji Control

**This example uses play\_emoji**, which allows the robot to display a specified emoji. Users can choose an emoji from the available list; see the [Emoji List](../Interface/interactor/screen.html#tbl-emotion-id) for details.

```
  1#include "aimdk_msgs/srv/play_emoji.hpp"
  2#include "aimdk_msgs/msg/common_request.hpp"
  3#include "rclcpp/rclcpp.hpp"
  4#include <chrono>
  5#include <memory>
  6#include <signal.h>
  7#include <string>
  8
  9// Global variable used for signal handling
 10std::shared_ptr<rclcpp::Node> g_node = nullptr;
 11
 12// Signal handler function
 13void signal_handler(int signal) {
 14  if (g_node) {
 15    RCLCPP_INFO(g_node->get_logger(), "Received signal %d, shutting down...",
 16                signal);
 17    g_node.reset();
 18  }
 19  rclcpp::shutdown();
 20  exit(signal);
 21}
 22
 23class PlayEmojiClient : public rclcpp::Node {
 24public:
 25  PlayEmojiClient() : Node("play_emoji_client") {
 26    client_ = this->create_client<aimdk_msgs::srv::PlayEmoji>(
 27        "/face_ui_proxy/play_emoji");
 28    RCLCPP_INFO(this->get_logger(), "✅ PlayEmoji client node started.");
 29
 30    // Wait for the service to become available
 31    while (!client_->wait_for_service(std::chrono::seconds(2))) {
 32      RCLCPP_INFO(this->get_logger(), "⏳ Service unavailable, waiting...");
 33    }
 34    RCLCPP_INFO(this->get_logger(),
 35                "🟢 Service available, ready to send request.");
 36  }
 37
 38  bool send_request(uint8_t emoji, uint8_t mode, int32_t priority) {
 39    try {
 40      auto request = std::make_shared<aimdk_msgs::srv::PlayEmoji::Request>();
 41
 42      request->emotion_id = emoji;
 43      request->mode = mode;
 44      request->priority = priority;
 45
 46      RCLCPP_INFO(
 47          this->get_logger(),
 48          "📨 Sending request to play emoji: id=%hhu, mode=%hhu, priority=%d",
 49          emoji, mode, priority);
 50
 51      const std::chrono::milliseconds timeout(250);
 52      for (int i = 0; i < 8; i++) {
 53        request->header.header.stamp = this->now();
 54        auto future = client_->async_send_request(request);
 55        auto retcode = rclcpp::spin_until_future_complete(shared_from_this(),
 56                                                          future, timeout);
 57        if (retcode != rclcpp::FutureReturnCode::SUCCESS) {
 58          // retry as remote peer is NOT handled well by ROS
 59          RCLCPP_INFO(this->get_logger(), "trying ... [%d]", i);
 60          continue;
 61        }
 62        // future.done
 63        auto response = future.get();
 64        if (response->success) {
 65          RCLCPP_INFO(this->get_logger(),
 66                      "✅ Request to play emoji recorded successfully: %s",
 67                      response->message.c_str());
 68          return true;
 69        } else {
 70          RCLCPP_ERROR(this->get_logger(),
 71                       "❌ Failed to record play-emoji request: %s",
 72                       response->message.c_str());
 73          return false;
 74        }
 75      }
 76      RCLCPP_ERROR(this->get_logger(), "❌ Service call failed or timed out.");
 77      return false;
 78    } catch (const std::exception &e) {
 79      RCLCPP_ERROR(this->get_logger(), "Exception occurred: %s", e.what());
 80      return false;
 81    }
 82  }
 83
 84private:
 85  rclcpp::Client<aimdk_msgs::srv::PlayEmoji>::SharedPtr client_;
 86};
 87
 88int main(int argc, char **argv) {
 89  try {
 90    rclcpp::init(argc, argv);
 91
 92    // Set up signal handlers
 93    signal(SIGINT, signal_handler);
 94    signal(SIGTERM, signal_handler);
 95
 96    int32_t priority = 10;
 97
 98    int emotion = 1; // Expression type, 1 means Blink
 99    std::cout
100        << "Enter expression ID: 1-Blink, 60-Bored, 70-Abnormal, 80-Sleeping, "
101           "90-Happy, 190-Very Angry, 200-Adoration"
102        << std::endl;
103    std::cin >> emotion;
104
105    int mode = 1; // Playback mode, 1 means play once, 2 means loop
106    std::cout << "Enter play mode (1: once, 2: loop): ";
107    std::cin >> mode;
108    if (mode < 1 || mode > 2) {
109      RCLCPP_ERROR(rclcpp::get_logger("main"), "Invalid play mode: %d", mode);
110      rclcpp::shutdown();
111      return 1;
112    }
113
114    g_node = std::make_shared<PlayEmojiClient>();
115    auto client = std::dynamic_pointer_cast<PlayEmojiClient>(g_node);
116
117    if (client) {
118      client->send_request(emotion, mode, priority);
119    }
120
121    // Clean up resources
122    g_node.reset();
123    rclcpp::shutdown();
124
125    return 0;
126  } catch (const std::exception &e) {
127    RCLCPP_ERROR(rclcpp::get_logger("main"),
128                 "Program exited with exception: %s", e.what());
129    return 1;
130  }
131}
```

## 6.2.20 LED Strip Control

**Function Description**: Demonstrates how to control the robot’s LED strip, supporting multiple display modes and customizable colors.

**Core Code**:

```
  1#include <aimdk_msgs/msg/common_request.hpp>
  2#include <aimdk_msgs/srv/led_strip_command.hpp>
  3#include <chrono>
  4#include <memory>
  5#include <rclcpp/rclcpp.hpp>
  6#include <signal.h>
  7#include <string>
  8
  9std::shared_ptr<rclcpp::Node> g_node = nullptr;
 10
 11void signal_handler(int signal) {
 12  if (g_node) {
 13    RCLCPP_INFO(g_node->get_logger(), "Received signal %d, shutting down...",
 14                signal);
 15    g_node.reset();
 16  }
 17  rclcpp::shutdown();
 18  exit(signal);
 19}
 20
 21class PlayLightsClient : public rclcpp::Node {
 22public:
 23  PlayLightsClient() : Node("play_lights_client") {
 24    client_ = this->create_client<aimdk_msgs::srv::LedStripCommand>(
 25        "/aimdk_5Fmsgs/srv/LedStripCommand");
 26    RCLCPP_INFO(this->get_logger(), "✅ PlayLights client node started.");
 27
 28    // Wait for the service to become available
 29    while (!client_->wait_for_service(std::chrono::seconds(2))) {
 30      RCLCPP_INFO(this->get_logger(), "⏳ Service unavailable, waiting...");
 31    }
 32    RCLCPP_INFO(this->get_logger(),
 33                "🟢 Service available, ready to send request.");
 34  }
 35
 36  bool send_request(uint8_t led_mode, uint8_t r, uint8_t g, uint8_t b) {
 37    try {
 38      auto request =
 39          std::make_shared<aimdk_msgs::srv::LedStripCommand::Request>();
 40
 41      request->led_strip_mode = led_mode;
 42      request->r = r;
 43      request->g = g;
 44      request->b = b;
 45
 46      RCLCPP_INFO(this->get_logger(),
 47                  "📨 Sending request to control led strip: mode=%hhu, "
 48                  "RGB=(%hhu, %hhu, %hhu)",
 49                  led_mode, r, g, b);
 50
 51      // LED strip is slow to response (up to ~5s)
 52      const std::chrono::milliseconds timeout(5000);
 53      for (int i = 0; i < 4; i++) {
 54        request->request.header.stamp = this->now();
 55        auto future = client_->async_send_request(request);
 56        auto retcode = rclcpp::spin_until_future_complete(
 57            this->shared_from_this(), future, timeout);
 58
 59        if (retcode != rclcpp::FutureReturnCode::SUCCESS) {
 60          // retry as remote peer is NOT handled well by ROS
 61          RCLCPP_INFO(this->get_logger(), "trying ... [%d]", i);
 62          continue;
 63        }
 64        // future.done
 65        auto response = future.get();
 66        if (response->status_code == 0) {
 67          RCLCPP_INFO(this->get_logger(),
 68                      "✅ LED strip command sent successfully.");
 69          return true;
 70        } else {
 71          RCLCPP_ERROR(this->get_logger(),
 72                       "❌ LED strip command failed with status: %d",
 73                       response->status_code);
 74          return false;
 75        }
 76      }
 77      RCLCPP_ERROR(this->get_logger(), "❌ Service call failed or timed out.");
 78      return false;
 79    } catch (const std::exception &e) {
 80      RCLCPP_ERROR(this->get_logger(), "Exception occurred: %s", e.what());
 81      return false;
 82    }
 83  }
 84
 85private:
 86  rclcpp::Client<aimdk_msgs::srv::LedStripCommand>::SharedPtr client_;
 87};
 88
 89int main(int argc, char **argv) {
 90  try {
 91    rclcpp::init(argc, argv);
 92    signal(SIGINT, signal_handler);
 93    signal(SIGTERM, signal_handler);
 94
 95    g_node = std::make_shared<PlayLightsClient>();
 96    auto client_node = std::dynamic_pointer_cast<PlayLightsClient>(g_node);
 97
 98    int led_mode = 0;          // LED Strip Mode
 99    int r = 255, g = 0, b = 0; // RGB values
100
101    std::cout << "=== LED Strip Control Example ===" << std::endl;
102    std::cout << "Select LED strip mode:" << std::endl;
103    std::cout << "0 - Steady On" << std::endl;
104    std::cout << "1 - Breathing (4s period, sinusoidal brightness)"
105              << std::endl;
106    std::cout << "2 - Blinking (1s period, 0.5s on, 0.5s off)" << std::endl;
107    std::cout << "3 - Flow (2s period, lights turn on left to right)"
108              << std::endl;
109    std::cout << "Enter mode (0-3): ";
110    std::cin >> led_mode;
111
112    std::cout << "\nSet RGB color values (0-255):" << std::endl;
113    std::cout << "Red component (R): ";
114    std::cin >> r;
115    std::cout << "Green component (G): ";
116    std::cin >> g;
117    std::cout << "Blue component (B): ";
118    std::cin >> b;
119
120    // clamp mode to range 0-3
121    led_mode = std::max(0, std::min(3, led_mode));
122    // clamp r/g/b to range 0-255
123    r = std::max(0, std::min(255, r));
124    g = std::max(0, std::min(255, g));
125    b = std::max(0, std::min(255, b));
126
127    if (client_node) {
128      client_node->send_request(led_mode, r, g, b);
129    }
130
131    g_node.reset();
132    rclcpp::shutdown();
133
134    return 0;
135  } catch (const std::exception &e) {
136    RCLCPP_ERROR(rclcpp::get_logger("main"),
137                 "Program terminated with exception: %s", e.what());
138    return 1;
139  }
140}
```

**Usage Instructions:**

```
# Build
colcon build --packages-select examples

# Run
ros2 run examples play_lights
```

**Output Example:**

```
=== LED Strip Control Example ===
Please select LED mode:
0 - Constant ON
1 - Breathing Mode (4s cycle, sinusoidal brightness)
2 - Blinking Mode (1s cycle, 0.5s ON / 0.5s OFF)
3 - Flowing Mode (2s cycle, lights on from left to right)
Enter mode (0–3): 1

Set RGB color values (0–255):
Red component (R): 255
Green component (G): 0
Blue component (B): 0

Sending LED control command...
Mode: 1, Color: RGB(255, 0, 0)
✅ LED strip command sent successfully
```

**Technical Features:**

- Supports 4 LED display modes
- Customizable RGB colors
- Asynchronous service calls
- Input parameter validation
- User-friendly interaction interface
