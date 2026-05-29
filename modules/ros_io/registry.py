from dataclasses import asdict, dataclass


@dataclass(frozen=True)
class TopicReadSpec:
    key: str
    name: str
    topic: str
    message_type: str
    qos_depth: int = 10
    stale_after_sec: float = 1.0
    description: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class TopicWriteSpec:
    key: str
    name: str
    topic: str
    message_type: str
    builder: str
    qos_depth: int = 10
    description: str = ""

    def to_dict(self):
        payload = asdict(self)
        payload.pop("builder", None)
        return payload


READ_TOPICS = {
    "piper_single_joint_state": TopicReadSpec(
        key="piper_single_joint_state",
        name="Piper single joint state",
        topic="/joint_states_single",
        message_type="sensor_msgs/msg/JointState",
        stale_after_sec=0.5,
        description="Joint state feedback from start_single_piper.launch.py remapping.",
    ),
    "piper_left_joint_state": TopicReadSpec(
        key="piper_left_joint_state",
        name="Piper left joint state",
        topic="/puppet/joint_left",
        message_type="sensor_msgs/msg/JointState",
        stale_after_sec=0.5,
        description="Left arm joint feedback without launch remapping.",
    ),
    "piper_right_joint_state": TopicReadSpec(
        key="piper_right_joint_state",
        name="Piper right joint state",
        topic="/puppet/joint_right",
        message_type="sensor_msgs/msg/JointState",
        stale_after_sec=0.5,
        description="Right arm joint feedback without launch remapping.",
    ),
    "piper_left_joint_state_double": TopicReadSpec(
        key="piper_left_joint_state_double",
        name="Piper left joint state double",
        topic="/joint_states_single_l",
        message_type="sensor_msgs/msg/JointState",
        stale_after_sec=0.5,
        description="Left arm joint feedback from start_double_piper.launch.py remapping.",
    ),
    "piper_right_joint_state_double": TopicReadSpec(
        key="piper_right_joint_state_double",
        name="Piper right joint state double",
        topic="/joint_states_single_r",
        message_type="sensor_msgs/msg/JointState",
        stale_after_sec=0.5,
        description="Right arm joint feedback from start_double_piper.launch.py remapping.",
    ),
    "piper_left_end_pose": TopicReadSpec(
        key="piper_left_end_pose",
        name="Piper left end pose",
        topic="/puppet/end_pose_left",
        message_type="geometry_msgs/msg/PoseStamped",
        stale_after_sec=0.5,
        description="Left arm end-effector pose feedback.",
    ),
    "piper_right_end_pose": TopicReadSpec(
        key="piper_right_end_pose",
        name="Piper right end pose",
        topic="/puppet/end_pose_right",
        message_type="geometry_msgs/msg/PoseStamped",
        stale_after_sec=0.5,
        description="Right arm end-effector pose feedback.",
    ),
    "piper_single_arm_status": TopicReadSpec(
        key="piper_single_arm_status",
        name="Piper single arm status",
        topic="/piper_ctrl_single_node/arm_status",
        message_type="piper_msgs/msg/PiperStatusMsg",
        stale_after_sec=0.5,
        description="Single Piper node status feedback.",
    ),
    "piper_left_arm_status": TopicReadSpec(
        key="piper_left_arm_status",
        name="Piper left arm status",
        topic="/piper_left_ctrl_node/arm_status",
        message_type="piper_msgs/msg/PiperStatusMsg",
        stale_after_sec=0.5,
        description="Left Piper node status feedback.",
    ),
    "piper_right_arm_status": TopicReadSpec(
        key="piper_right_arm_status",
        name="Piper right arm status",
        topic="/piper_right_ctrl_node/arm_status",
        message_type="piper_msgs/msg/PiperStatusMsg",
        stale_after_sec=0.5,
        description="Right Piper node status feedback.",
    ),
    "lifting_motor_state": TopicReadSpec(
        key="lifting_motor_state",
        name="Lifting motor state",
        topic="/LiftMotorStatePub",
        message_type="lifting_msg_pkg/msg/LiftMotorMsg",
        stale_after_sec=0.8,
        description="Lifting axis motor state feedback.",
    ),
    "chassis_system_state": TopicReadSpec(
        key="chassis_system_state",
        name="Chassis system state",
        topic="/system_state",
        message_type="ranger_msgs/msg/SystemState",
        stale_after_sec=0.8,
        description="Ranger chassis system, control mode, error code, battery voltage, and motion mode.",
    ),
    "chassis_motion_state": TopicReadSpec(
        key="chassis_motion_state",
        name="Chassis motion state",
        topic="/motion_state",
        message_type="ranger_msgs/msg/MotionState",
        stale_after_sec=0.8,
        description="Ranger chassis motion mode feedback.",
    ),
    "chassis_battery_state": TopicReadSpec(
        key="chassis_battery_state",
        name="Chassis battery state",
        topic="/battery_state",
        message_type="sensor_msgs/msg/BatteryState",
        stale_after_sec=1.0,
        description="Ranger chassis BMS feedback.",
    ),
    "chassis_odom": TopicReadSpec(
        key="chassis_odom",
        name="Chassis odometry",
        topic="/odom",
        message_type="nav_msgs/msg/Odometry",
        stale_after_sec=0.8,
        description="Ranger chassis odometry published by ranger_base_node.",
    ),
}


WRITE_ACTIONS = {
    "piper_single_pose": TopicWriteSpec(
        key="piper_single_pose",
        name="Piper single pose command",
        topic="/pos_cmd",
        message_type="piper_msgs/msg/PosCmd",
        builder="pos_cmd",
        description="Publish a Cartesian pose command for a single Piper node.",
    ),
    "piper_left_pose": TopicWriteSpec(
        key="piper_left_pose",
        name="Piper left pose command",
        topic="/pos_left_cmd",
        message_type="piper_msgs/msg/PosCmd",
        builder="pos_cmd",
        description="Publish a Cartesian pose command for the left Piper node.",
    ),
    "piper_right_pose": TopicWriteSpec(
        key="piper_right_pose",
        name="Piper right pose command",
        topic="/pos_right_cmd",
        message_type="piper_msgs/msg/PosCmd",
        builder="pos_cmd",
        description="Publish a Cartesian pose command for the right Piper node.",
    ),
    "piper_single_joint": TopicWriteSpec(
        key="piper_single_joint",
        name="Piper single joint command",
        topic="/joint_states_gripper",
        message_type="sensor_msgs/msg/JointState",
        builder="joint_state",
        description="Publish a joint command for start_single_piper.launch.py.",
    ),
    "piper_left_joint": TopicWriteSpec(
        key="piper_left_joint",
        name="Piper left joint command",
        topic="/joint_left_states",
        message_type="sensor_msgs/msg/JointState",
        builder="joint_state",
        description="Publish a joint command for the left Piper node.",
    ),
    "piper_right_joint": TopicWriteSpec(
        key="piper_right_joint",
        name="Piper right joint command",
        topic="/joint_right_states",
        message_type="sensor_msgs/msg/JointState",
        builder="joint_state",
        description="Publish a joint command for the right Piper node.",
    ),
    "piper_left_joint_double": TopicWriteSpec(
        key="piper_left_joint_double",
        name="Piper left joint command double",
        topic="/joint_states_gripper_l",
        message_type="sensor_msgs/msg/JointState",
        builder="joint_state",
        description="Publish a joint command for start_double_piper.launch.py left remapping.",
    ),
    "piper_right_joint_double": TopicWriteSpec(
        key="piper_right_joint_double",
        name="Piper right joint command double",
        topic="/joint_states_gripper_r",
        message_type="sensor_msgs/msg/JointState",
        builder="joint_state",
        description="Publish a joint command for start_double_piper.launch.py right remapping.",
    ),
    "piper_single_joint_smoother_hold": TopicWriteSpec(
        key="piper_single_joint_smoother_hold",
        name="Piper single joint smoother hold",
        topic="/joint_states_gripper/hold",
        message_type="std_msgs/msg/Bool",
        builder="bool",
        description="Clear the single Piper smoother target and hold its current interpolation position.",
    ),
    "piper_left_joint_smoother_hold": TopicWriteSpec(
        key="piper_left_joint_smoother_hold",
        name="Piper left joint smoother hold",
        topic="/joint_states_gripper_l/hold",
        message_type="std_msgs/msg/Bool",
        builder="bool",
        description="Clear the left Piper smoother target and hold its current interpolation position.",
    ),
    "piper_right_joint_smoother_hold": TopicWriteSpec(
        key="piper_right_joint_smoother_hold",
        name="Piper right joint smoother hold",
        topic="/joint_states_gripper_r/hold",
        message_type="std_msgs/msg/Bool",
        builder="bool",
        description="Clear the right Piper smoother target and hold its current interpolation position.",
    ),
    "piper_enable_all": TopicWriteSpec(
        key="piper_enable_all",
        name="Piper enable flag",
        topic="/enable_flag",
        message_type="std_msgs/msg/Bool",
        builder="bool",
        description="Publish the shared enable flag used by current Piper launch files.",
    ),
    "chassis_cmd_vel": TopicWriteSpec(
        key="chassis_cmd_vel",
        name="Chassis velocity command",
        topic="/cmd_vel",
        message_type="geometry_msgs/msg/Twist",
        builder="twist",
        qos_depth=1,
        description="Publish Ranger chassis velocity commands.",
    ),
}


def read_topic_specs():
    return READ_TOPICS


def write_action_specs():
    return WRITE_ACTIONS
