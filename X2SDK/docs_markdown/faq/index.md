# 7 FAQ

**Q: Running the example reports: “Package ‘examples’ not found”**

- Refer to [Environment installation and configuration](../quick_start/prerequisites.html#aimdk-build) and [Run an Example Program](../quick_start/run_example.html#aimdk-run) to confirm AimDK has been successfully built and sourced.

**Q: Example build failed**

- If `colcon` is not found, ensure ROS is installed correctly and sourced properly.
- Check build error logs; if libraries are missing, verify dependency installation.
- Clear build caches and retry.

**Q: After connecting via Ethernet, the examples show no response?**

- Try running `ros2 topic list` and `ros2 topic echo topic_name` (replace `topic_name` with the actual topic) to check system status.
- Preset motions require the robot to be in the Stable Standing Mode.
- For TTS/audio playback issues, check the following:

  - 1. Whether the volume is muted, and whether the TTS text or audio format meets interface requirements.
  - 2. **Verify that the X2 built-in voice interaction system is not disabled.**

**Q: There is no response when I directly control the motor**

If you are controlling the HAL layer directly, the MC module must be stopped.

- Use `aima em stop-app mc` to stop the MC module.
- Restart your program afterward.

**Q: When switching to Stand-Ready (Position-Control Standing) mode, the legs don’t respond and the arms move slowly**

- Low battery may prevent power delivery to the legs; replace with a sufficiently charged battery.

**Q: Robot service calls have no response**

- Verify that all service request fields are correctly set.

**Q: Error when using `cv_bridge` on the robot (`Assertion failed: s >= 0 in function 'setSize'`)**

- Check the OpenCV version used during compilation:
  The robot environment includes both Nvidia-supplied OpenCV and Ubuntu repository OpenCV.
  When using `cv_bridge`, you must link against the Ubuntu-sourced OpenCV.
