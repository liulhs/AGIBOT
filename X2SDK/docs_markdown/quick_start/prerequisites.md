# 4.1 Read the user guide to familiarize yourself with relevant terminology and safety precautions.

- [AgiBot X2 Ultra User Guide](https://www.agibot.com/filepage/271.html)
- [OmniPicker User Manual](https://www.agibot.com/filepage/265.html)
- [OmniHand 2025 User Manual](https://www.agibot.com/filepage/276.html)

---

# 4.2 Complete the basic system configuration

- **Operating System**: Ubuntu 22.04 LTS
- **ROS 2 Version**: Humble
- **Python Version**: Python 3.8 or later
- **C++ Standard**: C++17

And SDK example dependencies:

- **OpenCV**: Image processing
- **Ruckig**: Trajectory generation
- **ncurses**: Terminal control
- **libcurl**: Network communication
- **cv\_bridge**: ROS–OpenCV image conversion

Depending on how you use the SDK, the scenarios are as follows:

- SDK-on-device mode: the development computing unit already includes all prerequisites, so no installation is required. (Recommended for quick start.)
- PC-side SDK + cross-device networking mode: ensure the host PC meets the above requirements.

*Host PC installation reference*

- For Ubuntu 22.04 LTS installation, refer to the [official Ubuntu installation guide](https://ubuntu.com/tutorials/install-ubuntu-desktop) and download from the [official release page](https://releases.ubuntu.com/22.04).
- For ROS 2 installation, refer to the [official ROS 2 documentation](https://docs.ros.org/en/humble/index.html).
- Python 3 and C++ requirements are already satisfied by default on Ubuntu 22.04 with ROS Humble.

---

# 4.3 Network connection

The AgiBot X2 Ultra supports multiple network access methods to connect to the onboard system:

**(1) Direct wired connection via the rear Ethernet port** — Connect a network cable between the robot’s [SDK development Ethernet port](../about_agibot_X2/SDK_interface.html#img-x2-sdk-interface) and the host PC.

- Configure the host PC network interface to a static IP **(10.0.1.2, subnet mask 255.255.255.0)**.
- The development computing unit will then be accessible at **10.0.1.41**, enabling cross-device ROS networking and **SSH login** (credentials require technical support).

**(2) Wi-Fi connection through the robot’s built-in hotspot**

- Enable the **AP Hotspot** in the **robot APP**, and check the Wi-Fi SSID and password.
- After connecting to the hotspot, you can access the development computing unit via the jump host at **192.168.88.88** (SSH credentials require technical support).

---

Attention

Taking Motion Control Computing Unit(PC1, 10.0.1.40) as build & run environment for secondary development is strictly prohibited to avoid safety risks

Attention

For PC-side SDK + cross-device networking, use a wired direct connection. **Wi-Fi should only be used for SSH debugging**.

Important

It is not recommended to place the robot and development PC on a public or complex network with other devices. Developers must properly manage **network security risks** to prevent communication interference or data leakage.

# 4.4 Environment installation and configuration

Place the SDK into the target environment and extract it.

```
# Set environment variables (this step can be skipped when running directly on the development computing unit)
source /opt/ros/humble/setup.bash

# Build the SDK
# Assume the extracted top-level directory for the X2 AimDK project is named 'aimdk'
cd ./aimdk/
colcon build
```

Caution

Notes about non-volatile user data:

- The disks in the robot would be reformated during firmware upgrade/downgrade, please backup you data
- User data under `$HOME`(/agibot/data/home/agi) would suervive in general
- Exception 1: DO NOT save data into `$HOME/aimdk*`, which are preserved and maintained by the system
- BE CAREFUL of features like factory reset, which would force erase all user data (include `$HOME`)
