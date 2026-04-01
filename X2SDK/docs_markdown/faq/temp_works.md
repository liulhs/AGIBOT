# 8 Temporary Transitional Solutions Statement

- During the SDK iteration process, we provide certain **temporary methods and temporary notes** to support advanced secondary-development requirements, announce interface attributes that are not yet open but will be supported soon, and deprecate certain interfaces/parameters based on system architecture adjustments.
- In subsequent SDK releases, these transitional solutions will be replaced by a more coherent and fully integrated software–hardware ecosystem. Please stay tuned.

## 8.1 Disable the Built-in Interaction System and Use Your Own Voice System

**By default, when the robot is powered on, it automatically enters natural voice interaction mode, and the interaction module occupies the audio input/output streams.** If you need to integrate your own voice system and access the audio streams, you can temporarily disable the built-in interaction module using the steps below. **Future versions will support one-click switching to secondary-development interaction mode to further simplify custom voice system integration.**

### 8.1.1 Steps to Temporarily Disable the Built-in Interaction System

1. Power on the robot.
2. Switch the interaction mode (disable the LLM) by executing the following command:

   ```
   ros2 service call /aimdk_5Fmsgs/srv/SetAgentPropertiesRequest \
     aimdk_msgs/srv/SetAgentPropertiesRequest "
   contents:
     properties:
       - key:
           value: 2  # AGENT_PROPERTY_RUN_MODE = 0x02
         value: 'only_voice'
   "
   ```

   > This operation updates the local configuration file and disables the large model.
3. Restart the agent module for the changes to take effect:

   ```
   # Stop the interaction module
   aima em stop-app agent

   # Start the interaction module in secondary-development mode
   aima em start-app agent
   ```
4. You can now subscribe to audio data for secondary development. Refer to the [MIC Audio Stream Capture Topic](../Interface/interactor/voice.html#mic-receiver-vad) section for details.

---

### 8.1.2 Steps to Restore the Built-in Interaction System

1. Power on the robot.
2. Switch back to the normal interaction mode using the following command:

   ```
   ros2 service call /aimdk_5Fmsgs/srv/SetAgentPropertiesRequest \
     aimdk_msgs/srv/SetAgentPropertiesRequest "
   contents:
     properties:
       - key:
           value: 2  # AGENT_PROPERTY_RUN_MODE = 0x02
         value: 'normal'
   "
   ```
3. Restart the agent module:

   ```
   aima em stop-app agent

   # Start the interaction module in normal mode
   aima em start-app agent
   ```
4. The built-in AgiBot LLM interaction features can now be used normally.

## 8.2 Motion State Simplification: Some McAction state codes prior to v0.7.x are no longer supported

Caution

**Starting from v0.8, the following motion mode codes must NOT be used.** They may still exist temporarily but are no longer guaranteed or open for secondary development.

- `ZERO_TORQUE_DEFAULT`: The Chinese name “Zero-Torque Mode” remains, but its corresponding mode is now changed to `PASSIVE_DEFAULT`.
- `SOFT_EMERGENCY_STOP`: Soft emergency stop is no longer an independent motion mode. Use `PASSIVE_DEFAULT` (zero torque) or `DAMPING_DEFAULT` (damping mode).
- `JOINT_FREEZE`: Deprecated. Use `JOINT_DEFAULT` (Stand-Ready / Position-Control Standing) for fully locked joints, and `DAMPING_DEFAULT` for joint damping.
- `STAND_BODY_CONTROL`: Deprecated. Use `STAND_DEFAULT` (Stable Standing).
- `RUN_DEFAULT`: Running mode removed. Use `LOCOMOTION_DEFAULT` instead.
