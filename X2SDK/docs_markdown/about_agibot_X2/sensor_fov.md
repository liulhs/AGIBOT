# 1.6 AgiBot X2 Sensor Overview

## 1.6.1 Sensor Capabilities & FOV Diagram

| Version | Sensor Suite | Perception Capabilities |
| --- | --- | --- |
| **X2 Ultra Edition** | LiDAR RGB-D Depth Camera Front Stereo RGB Camera Front Interaction RGB Camera Rear RGB Camera | **LiDAR:** a. Captures high-precision environmental data in real time; b. Rapidly detects and measures surrounding objects; c. Outputs high-resolution point clouds as a core input for environmental perception.  **In addition to the chest-mounted LiDAR,** multiple camera types are included for richer perception, including: a. Depth camera: assists in acquiring 3D spatial information of objects; b. Stereo camera: improves 3D perception and distance estimation accuracy; c. Rear camera: covers the rear field of view to reduce perception blind spots; d. Interaction camera: supports visual recognition and response for human-robot interaction scenarios. |

---

[![../_images/sensor_fov.en.png](../_images/sensor_fov.en.png)](../_images/sensor_fov.en.png)

## 1.6.2 Sensor Specifications

### LiDAR

| Manufacturer | Model | Wavelength | Horizontal FOV | Vertical FOV |
| --- | --- | --- | --- | --- |
| RoboSense | E1R | 940 nm | 120° (-60.0° to +60.0°) ±1% | 90° (-45° to +45°) |

### RGB-D Camera

| Manufacturer | Model | Laser Wavelength | Resolution | Frame Rate | Depth FOV | Color FOV |
| --- | --- | --- | --- | --- | --- | --- |
| Orbbec | Gemini335 | 850nm | Depth: up to 1280 × 800 Color: up to 1920 × 1080 | Up to 60fps | 90° × 65° ± 3° @ 2m (1280 × 800) | 94° × 68° ± 3° @ 2m |

### Front Stereo RGB Camera

| Manufacturer | Model | Resolution | Frame Rate | Horizontal FOV | Vertical FOV |
| --- | --- | --- | --- | --- | --- |
| SenYun | SDS23NNS1 | Up to 2064H × 1552V | Up to 40fps | 156° | 120° |

### Front Interaction RGB Camera

| Manufacturer | Model | Resolution | Frame Rate | Horizontal FOV | Vertical FOV |
| --- | --- | --- | --- | --- | --- |
| SenYun | SM5M12NJ | Up to 2608 × 1960 | Up to 30 fps | 110° | 80° |

### Rear RGB Camera

| Manufacturer | Model | Resolution | Frame Rate | Horizontal FOV | Vertical FOV |
| --- | --- | --- | --- | --- | --- |
| SenYun | SM3S23NS | Up to 2064H × 1552V | Up to 30fps | 156° | 120° |

### Touch Sensor

| Manufacturer | Model | Sampling Rate | Single click | Double click | Triple click | Short press | Long press | Slide |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Awinic (Shanghai) | AW93208GQNR | Up to 250 kHz | ✓ | ✓ | ✓ | ✓ | ✓ | ✓ |

### Standalone Inertial Sensor (IMU)

| Installation Location | Manufacturer | Model | Type | Rate |
| --- | --- | --- | --- | --- |
| One each at the chest and hip | FORSENSE | FSS-IMU16460-DM | 6DoF MEMS IMU | Configurable up to 1kHz |
