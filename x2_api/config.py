# x2_api/config.py
"""All constants and paths for the X2 Motion API."""

# Server
API_HOST = "0.0.0.0"
API_PORT = 8080
API_KEY_HEADER = "X-API-Key"
API_KEY = "x2-dev-key-change-me"  # Override via X2_API_KEY env var

# ROS2 service names
SVC_SET_MC_ACTION = "/aimdk_5Fmsgs/srv/SetMcAction"
SVC_GET_MC_ACTION = "/aimdk_5Fmsgs/srv/GetMcAction"
SVC_REGISTER_MOTION = "/aimdk_5Fmsgs/srv/RegisterCustomMotion"
SVC_SET_MC_MOTION = "/aimdk_5Fmsgs/srv/SetMcMotion"
SVC_GET_MC_MOTIONS = "/aimdk_5Fmsgs/srv/GetMcMotions"
SVC_SET_PRESET_MOTION = "/aimdk_5Fmsgs/srv/SetMcPresetMotion"
SVC_GET_PRESET_STATE = "/aimdk_5Fmsgs/srv/GetMcPresetMotionState"

# ROS2 retry settings
ROS2_RETRIES = 8
ROS2_TIMEOUT_SEC = 0.5
ROS2_SERVICE_WAIT_SEC = 5.0

# Motion resource paths
RESOURCE_CONFIG_PATH = "/agibot/nfs/soc0/var/robot_proxy/resources/resource_config.yaml"
RESOURCE_BASE_PATH = "/agibot/nfs/soc0/var/robot_proxy/resources"

# Motion type constants
MOTION_TYPE_NONE = 0
MOTION_TYPE_ANIMATION = 1  # CSV trajectory
MOTION_TYPE_MIMIC = 2      # ONNX neural-net policy
MOTION_TYPE_FOUNDATION = 3

# Valid robot modes
VALID_MODES = [
    "PASSIVE_DEFAULT",
    "DAMPING_DEFAULT",
    "JOINT_DEFAULT",
    "STAND_DEFAULT",
    "LOCOMOTION_DEFAULT",
    "SIT_DOWN_DEFAULT",
    "CROUCH_DOWN_DEFAULT",
    "LIE_DOWN_DEFAULT",
    "STAND_UP_DEFAULT",
    "ASCEND_STAIRS",
    "DESCEND_STAIRS",
]
