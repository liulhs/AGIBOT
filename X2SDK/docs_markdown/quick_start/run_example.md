# 4.5 Run an Example Program

## 4.5.1 Get the Robot’s Current State

```
# Enter the SDK directory
# Replace the path below with your actual extraction path
cd /path/to/aimdk

# Set environment variables
source /opt/ros/humble/setup.bash
source install/local_setup.bash

# Run the example to get the robot’s current mode
# Refer to each example’s documentation for more detailed instructions

# Python example
ros2 run py_examples get_mc_action

# C++ example
ros2 run examples get_mc_action
```

**Sample Output**

If you see the following output, you have successfully connected to the robot and retrieved its current Locomotion Mode.

```
[INFO] [1764066631.016733611] [get_mc_action_client]: ✅ GetMCAction client node created
[INFO] [1764066631.017900579] [get_mc_action_client]: 🟢 Service available, ready to send request.
[INFO] [1764066631.018566508] [get_mc_action_client]: Sending request to get robot mode
[INFO] [1764066631.021247791] [get_mc_action_client]: Current robot mode:
[INFO] [1764066631.021832667] [get_mc_action_client]: Mode name: PASSIVE_DEFAULT
[INFO] [1764066631.022396136] [get_mc_action_client]: Mode status: 100
```

## 4.5.2 Make the Robot Wave

Switch the robot to Stable Standing Mode (Force-Control Stand). Please refer to the state transition diagram.

```
        block-beta
  columns 8
  JD("Position-Controlled Standing\nJOINT DEFAULT"):2 space SD("<span class='highlight-target'>Stable Standing\nSTAND_DEFAULT</span>"):2 space LD("Locomotion Mode\nLOCOMOTION_DEFAULT"):2
  space:8
  PA("Zero-Torque Mode\nPASSIVE_DEFAULT"):2 space:4 LS("Off-Road Mode\nLOCOMOTION_STEP"):2
  space:8
  DA("Damping Mode\nDAMPING_DEFAULT"):2 space:6

  DA --> PA
  PA --> JD
  JD --> SD
  LD --> SD
  LS --> LD
```

Important

Before switching to Stable Stand (`STAND_DEFAULT`), ensure that the robot is standing and both of it’s feet are firmly in contact with the ground.

```
# 1. Switch to Standing Preparation Mode (Position-Control Stand)
## Python example
ros2 run py_examples set_mc_action JD

## or C++ example
ros2 run examples set_mc_action JD

# 2. Then switch to Stable Standing Mode (Force-Control Stand)
## Python example
ros2 run py_examples set_mc_action SD

## or C++ example
ros2 run examples set_mc_action SD
```

Once the robot has switched to Stable Standing Mode, you can trigger the wave motion:

```
## Python example
ros2 run py_examples preset_motion_client
## C++ example
ros2 run examples preset_motion_client
```

**Enter the following when prompted:**

- **Arm Area:** `2` (right arm)
- **Preset Action ID:** `1002` (wave)

**Expected Result:** The robot will perform a wave gesture!
