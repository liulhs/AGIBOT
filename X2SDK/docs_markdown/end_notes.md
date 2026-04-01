# 9 Boundaries & Disclaimer for Secondary Development

Warning

1. Do not modify the system environment on the ORIN module (such as OS, drivers, or dependency libraries), as this may affect the robot’s stability and compatibility.
2. Taking Motion Control Computing Unit(PC1, 10.0.1.40) as build & run environment for secondary development is strictly prohibited to avoid safety risks
3. It is not recommended to alter system configurations or built-in algorithm parameters (including DDS configuration files, kernel settings, and algorithm-related configurations).
4. Unauthorized modifications or connections to hardware interfaces, the power system, or communication buses are strictly prohibited to prevent hardware damage or safety risks.
5. If third-party software or libraries are required during secondary development, consult the official technical support team beforehand to assess compatibility risks such as library conflicts, and ensure compliance with relevant open-source licenses and legal requirements.
6. All custom functions and extension modules should be implemented as plugins or independent processes, rather than replacing or overriding official core components.
7. If system abnormalities, functional issues, or safety warnings occur, refer to the robot operation guide or contact official technical support. Do not attempt high-risk operations on your own.

AgiBot will not provide support or warranty for software or hardware damage, or interface-call failures, resulting from violations of the above boundaries.
