# 4 Quick Start

In this chapter, we demonstrate how to use **AimDK** for secondary development on the AgiBot X2 by walking through **building and running SDK sample programs** and **developing combined robot control programs**.

- [4.1 Read the user guide to familiarize yourself with relevant terminology and safety precautions.](prerequisites.html)
- [4.2 Complete the basic system configuration](prerequisites.html#id2)
- [4.3 Network connection](prerequisites.html#id3)
- [4.4 Environment installation and configuration](prerequisites.html#aimdk-build)
- [4.5 Run an Example Program](run_example.html)
  - [4.5.1 Get the Robot’s Current State](run_example.html#id1)
  - [4.5.2 Make the Robot Wave](run_example.html#id2)
- [4.6 Code Implementation](code_sample.html)
  - [4.6.1 Project Overview](code_sample.html#id2)
  - [4.6.2 Add the Example to the Existing SDK Workspace](code_sample.html#sdk)
  - [4.6.3 Write the Control Code](code_sample.html#id4)
  - [4.6.4 Build and Run](code_sample.html#id8)
  - [4.6.5 Code Walkthrough](code_sample.html#id11)
  - [4.6.6 Extensions and Optimization](code_sample.html#id13)
  - [4.6.7 Troubleshooting](code_sample.html#id18)
  - [4.6.8 Next Steps](code_sample.html#id19)
  - [4.6.9 Summary](code_sample.html#id20)

Caution

Notes about non-volatile user data:

- The disks in the robot would be reformated during firmware upgrade/downgrade, please backup you data
- User data under `$HOME`(/agibot/data/home/agi) would suervive in general
- Exception 1: DO NOT save data into `$HOME/aimdk*`, which are preserved and maintained by the system
- BE CAREFUL of features like factory reset, which would force erase all user data (include `$HOME`)
