const state = {
  task: "idle",
  owner: "空闲",
  alerts: [
    {
      level: "warn",
      title: "CAN 状态待确认",
      detail: "CAN 还没有通过自检，请先执行整机自检。",
    },
    {
      level: "warn",
      title: "自检未执行",
      detail: "开始归位、数采或推理前建议先完成一次自检。",
    },
  ],
  logs: [],
  selfCheckRanAt: null,
  collectionTimer: null,
  inferenceTimer: null,
  homingTimer: null,
  playbackTimer: null,
  collectionSeconds: 0,
  inferenceTicks: 0,
  activeLogFilter: "全部",
  selfCheckResults: [],
  canActivation: {
    busy: false,
  },
  auth: {
    authenticated: false,
    user: "",
    active: null,
    users: ["zhuzl", "caizj", "xiangpc", "liuyc", "liuxy", "wusr"],
    busy: false,
    conflict: null,
    message: "请先登录后再控制机器人。",
    messageLevel: "idle",
  },
  piperRuntime: {
    status: "stopped",
  },
  liftingRuntime: {
    status: "stopped",
  },
  chassisRuntime: {
    status: "stopped",
  },
  localizationRuntime: {
    status: "stopped",
  },
  cameraRuntime: {
    status: "stopped",
  },
  cameraFrames: {
    previewEnabled: false,
    feeds: [],
    error: "",
    updatedAt: null,
    activeRequests: {},
    frameObjectUrls: {},
    frameSequences: {},
    frameTimers: {},
  },
  lidarRuntime: {
    status: "stopped",
  },
  lidarCloud: {
    previewEnabled: false,
    clouds: [],
    error: "",
    sequence: null,
    activeRequest: false,
    frameTimer: null,
    initialized: false,
    initPromise: null,
    hasFrame: false,
    pointCount: 0,
    sourcePointCount: 0,
    ageMs: null,
    stale: true,
    frameId: "",
    receivedAt: null,
    frameRate: null,
    frameTimes: [],
    three: null,
    scene: null,
    camera: null,
    renderer: null,
    geometry: null,
    material: null,
    points: null,
    pointRadius: 0.014,
    controls: null,
    animationFrame: null,
    resizeObserver: null,
  },
  playback: {
    running: false,
    status: "idle",
    busy: false,
    elapsedSec: 0,
    durationSec: 432,
    path: "/data/robot_station/replay.parquet",
    chartGroup: "all",
    robotEnabled: false,
    loading: false,
    loadError: "",
    loadedPath: "",
    dataset: null,
    currentFrameIndex: 0,
    lastTickMs: null,
    lastError: "",
    maxJointSpeedDegS: 20,
  },
  robotModel: {
    models: [],
    selectedKey: "",
    status: "idle",
    detail: "等待模型资源接入",
    loadedKey: "",
    metadata: null,
    loadPromise: null,
    progress: {
      active: false,
      value: 0,
      label: "等待加载",
      detail: "选择模型后点击加载",
      level: "idle",
      meshLoaded: 0,
      meshTotal: 0,
    },
    initialized: false,
    initPromise: null,
    hasModel: false,
    error: "",
    three: null,
    scene: null,
    camera: null,
    renderer: null,
    modelRoot: null,
    displayRoot: null,
    joints: {},
    colliders: [],
    meshCache: new Map(),
    lidarOverlay: {
      enabled: false,
      points: null,
      geometry: null,
      material: null,
      frameObject: null,
      lastFrameId: "",
      sequence: null,
      activeRequest: false,
      frameTimer: null,
      error: "",
    },
    poseSyncEnabled: false,
    controls: null,
    animationFrame: null,
    resizeObserver: null,
  },
  mapping: {
    status: "idle",
    busy: false,
    session: null,
    frameCount: 10,
    cloudTopic: "/rslidar_points",
    odomTopic: "/odom",
    baseFrame: "base_link",
    captureTimer: null,
    lastError: "",
    saveName: "",
    mapPreview: {
      activeRequest: false,
      hasFrame: false,
      initialized: false,
      pointCount: 0,
      sourcePointCount: 0,
      sizeBytes: 0,
      mtimeMs: null,
      loadedRevision: "",
      error: "",
      geometry: null,
      material: null,
      points: null,
    },
  },
  localization: {
    maps: [],
    mapsLoading: false,
    selectedMapName: "",
    selectedMap: null,
    status: "idle",
    lastError: "",
    mapPreview: {
      activeRequest: false,
      hasFrame: false,
      initialized: false,
      pointCount: 0,
      sourcePointCount: 0,
      sizeBytes: 0,
      mtimeMs: null,
      loadedName: "",
      error: "",
      bounds: null,
      geometry: null,
      material: null,
      points: null,
    },
  },
  armControl: {
    active: false,
    busy: false,
    publishTimer: null,
    maxJointSpeedDegS: 10,
  },
  piperEnableBusy: false,
  backgroundPollResumeTimer: null,
  inference: {
    status: "disconnected",
    connected: false,
    prompt: "",
    remoteUrl: "",
    chunkId: null,
    chunkSteps: 0,
    executedSteps: 0,
    chunkTiming: null,
    executionTiming: null,
    loopTiming: null,
    lastError: null,
    looping: false,
    busy: false,
    chassisHardLimits: { maxLinearMps: 0.2, maxLateralMps: 0.15, maxAngularRadS: 0.5 },
    mask: {
      left: { enabled: true, joints: [true, true, true, true, true, true], gripper: true },
      right: { enabled: true, joints: [true, true, true, true, true, true], gripper: true },
      lift: true,
      speed: true,
    },
  },
  liftPreview: {
    height: 0.42,
    speed: 0.08,
    stepUpMm: 50,
    stepDownMm: 50,
    mode: "等待初始化",
  },
  chassisControl: {
    driveTimer: null,
    stopTimers: [],
    activeDrive: null,
    keyboardListening: false,
    keyboardKeys: [],
    keyboardActiveKey: null,
    busy: false,
    resettingOdom: false,
    commandSequence: Date.now(),
    command: {
      linearX: 0,
      linearY: 0,
      angularZ: 0,
    },
  },
  liftingState: {
    ok: false,
    code: "ROS-R-WAITING",
    detail: "等待升降轴反馈。",
    heightM: null,
    targetHeightM: null,
    backSpeedMps: null,
    voltage: null,
    current: null,
    runState: false,
    reachTarget: false,
    fpsError: null,
    initState: false,
    upLimit: false,
    downLimit: false,
    ageMs: null,
    stale: true,
    receivedAt: null,
    limits: {
      minHeightM: 0.05,
      maxHeightM: 0.88,
    },
  },
  chassisState: {
    ok: false,
    code: "ROS-R-WAITING",
    detail: "等待底盘反馈。",
    system: null,
    motion: null,
    battery: null,
    odom: null,
    ageMs: null,
    stale: true,
    receivedAt: null,
    lastOkAt: null,
    polling: false,
  },
  piperActions: {
    left: {
      positions: [null, null, null, null, null, null, null],
      status: "idle",
      detail: "未设置 Action。",
      lastPublishedAt: null,
    },
    right: {
      positions: [null, null, null, null, null, null, null],
      status: "idle",
      detail: "未设置 Action。",
      lastPublishedAt: null,
    },
  },
  piperJoints: {
    left: {
      ok: false,
      code: "ROS-R-WAITING",
      detail: "等待左臂关节反馈。",
      names: [],
      positions: [],
      ageMs: null,
      stale: true,
      receivedAt: null,
      lastOkAt: null,
    },
    right: {
      ok: false,
      code: "ROS-R-WAITING",
      detail: "等待右臂关节反馈。",
      names: [],
      positions: [],
      ageMs: null,
      stale: true,
      receivedAt: null,
      lastOkAt: null,
    },
  },
  piperJointPolling: false,
};

const healthItems = [
  ["机械臂", "ok", "反馈 100 Hz", 92, "未使能"],
  ["底盘", "ok", "里程计在线", 86, "速度 0.00 m/s"],
  ["相机", "ok", "2 路在线", 90, "30 / 28 fps"],
  ["LiDAR", "ok", "点云在线", 82, "8 Hz"],
  ["存储", "warn", "剩余 128 GB", 64, "建议清理旧数据"],
  ["算力", "ok", "GPU 可用", 74, "温度 58 C"],
];

const selfCheckItems = [
  {
    name: "ROS2 daemon",
    status: "未检测",
    source: "ROS",
    code: "ROS2-D-000",
    advice: "确认 ROS2 环境已 source，必要时由自检启动 ros2 daemon。",
    detail: "用于确认 ROS2 CLI graph daemon 是否可用。",
    metric: { label: "daemon", value: "--", percent: 0, level: "idle" },
  },
  {
    name: "核心节点",
    status: "未检测",
    source: "ROS",
    code: "ROS-N-000",
    advice: "确认任务节点和设备节点已启动。",
    detail: "检查控制台依赖的核心节点是否在线。",
    metric: { label: "节点", value: "--", percent: 0, level: "idle" },
  },
  {
    name: "CAN 接口",
    status: "未检测",
    source: "系统",
    code: "CAN-I-000",
    advice: "can_left/can_right/can_chassis 未就绪时先激活 CAN。",
    detail: "检查机械臂和底盘 CAN 接口是否存在、是否 UP、bitrate 是否正确。",
    metric: { label: "CAN", value: "--", percent: 0, level: "idle" },
  },
  {
    name: "机械臂反馈",
    status: "未检测",
    source: "机械臂",
    code: "ARM-F-000",
    advice: "检查 Piper 电源、CAN 与反馈话题。",
    detail: "检查关节状态、末端位姿和夹爪反馈。",
    metric: { label: "反馈", value: "--", percent: 0, level: "idle" },
  },
  {
    name: "底盘反馈",
    status: "未检测",
    source: "底盘",
    code: "BASE-F-000",
    advice: "确认底盘驱动和里程计话题。",
    detail: "检查底盘速度反馈、里程计和驱动状态。",
    metric: { label: "里程计", value: "--", percent: 0, level: "idle" },
  },
  {
    name: "相机帧率",
    status: "未检测",
    source: "相机",
    code: "CAM-F-000",
    advice: "确认相机连接和曝光配置。",
    detail: "检查多路相机是否在线以及帧率是否达到任务要求。",
    metric: { label: "帧率", value: "--", percent: 0, level: "idle" },
  },
  {
    name: "LiDAR 点云",
    status: "未检测",
    source: "LiDAR",
    code: "LDR-P-000",
    advice: "确认雷达供电和点云话题。",
    detail: "检查 scan/points 话题是否持续更新。",
    metric: { label: "频率", value: "--", percent: 0, level: "idle" },
  },
  {
    name: "磁盘空间",
    status: "未检测",
    source: "系统",
    code: "DSK-S-000",
    advice: "建议保留至少 50 GB。",
    detail: "检查默认数据目录所在磁盘余量。",
    metric: { label: "占用", value: "--", percent: 0, level: "idle" },
  },
  {
    name: "GPU 可用性",
    status: "未检测",
    source: "系统",
    code: "GPU-A-000",
    advice: "确认驱动、CUDA 或推理运行时。",
    detail: "检查 GPU 是否可用于模型加载和推理。",
    metric: { label: "负载", value: "--", percent: 0, level: "idle" },
  },
];

const homingSteps = [
  "确认安全区域",
  "使能机械臂",
  "夹爪到默认状态",
  "机械臂回 home",
  "底盘停止",
  "传感器在线确认",
];

const logSources = ["全部", "系统", "ROS", "机械臂", "底盘", "升降轴", "相机", "LiDAR", "数采", "推理"];

const historyItems = [
  ["数采 episode_042", "成功", "09:42 - 09:49 / /data/robot_station/episodes/042"],
  ["归位流程", "完成", "09:36 - 09:37 / home"],
  ["整机自检", "警告", "09:35 / CAN 待确认，磁盘注意"],
  ["推理任务", "停止", "昨日 18:12 / operator stop"],
  ["数采 episode_041", "失败", "昨日 17:28 / 相机丢帧"],
];

const playbackFileDefaults = {
  durationSec: 432,
  rows: 21600,
};

const playbackSeriesDetails = {
  state: { label: "State", color: "#2563eb" },
  action: { label: "Action", color: "#d97706" },
};

const playbackSignalGroups = [
  {
    key: "left",
    label: "左臂",
    signals: [
      { key: "left.joint1", label: "L J1", unit: "rad", precision: 4 },
      { key: "left.joint2", label: "L J2", unit: "rad", precision: 4 },
      { key: "left.joint3", label: "L J3", unit: "rad", precision: 4 },
      { key: "left.joint4", label: "L J4", unit: "rad", precision: 4 },
      { key: "left.joint5", label: "L J5", unit: "rad", precision: 4 },
      { key: "left.joint6", label: "L J6", unit: "rad", precision: 4 },
      { key: "left.gripper", label: "L Grip", unit: "m", base: 0.035, amp: 0.018, freq: 0.024, phase: 0.4, precision: 3 },
    ],
  },
  {
    key: "right",
    label: "右臂",
    signals: [
      { key: "right.joint1", label: "R J1", unit: "rad", precision: 4 },
      { key: "right.joint2", label: "R J2", unit: "rad", precision: 4 },
      { key: "right.joint3", label: "R J3", unit: "rad", precision: 4 },
      { key: "right.joint4", label: "R J4", unit: "rad", precision: 4 },
      { key: "right.joint5", label: "R J5", unit: "rad", precision: 4 },
      { key: "right.joint6", label: "R J6", unit: "rad", precision: 4 },
      { key: "right.gripper", label: "R Grip", unit: "m", base: 0.032, amp: 0.016, freq: 0.024, phase: 1.6, precision: 3 },
    ],
  },
  {
    key: "platform",
    label: "平台",
    signals: [
      { key: "lift.height", label: "Lift", unit: "m", base: 0.42, amp: 0.08, freq: 0.006, phase: 0.2, precision: 3 },
      { key: "speed.vx", label: "vx", unit: "m/s", base: 0.02, amp: 0.12, freq: 0.028, phase: 0.4, precision: 2 },
      { key: "speed.vy", label: "vy", unit: "m/s", base: 0.0, amp: 0.08, freq: 0.026, phase: 1.8, precision: 2 },
      { key: "speed.wz", label: "wz", unit: "rad/s", base: 0.0, amp: 0.22, freq: 0.02, phase: 2.4, precision: 2 },
    ],
  },
];

const playbackArmValueKeys = ["joint1", "joint2", "joint3", "joint4", "joint5", "joint6", "gripper"];
const playbackStateFieldOrder = [
  ...playbackArmValueKeys.map((key) => `left.${key}`),
  ...playbackArmValueKeys.map((key) => `right.${key}`),
];
const playbackActionFieldOrder = [
  ...playbackStateFieldOrder,
  "lift.height",
  "speed.vx",
  "speed.vy",
  "speed.wz",
];
const playbackSignalLookup = playbackSignalGroups.reduce((lookup, group) => {
  group.signals.forEach((signal) => {
    lookup[signal.key] = signal;
  });
  return lookup;
}, {});
const playbackChartSamples = 180;
const playbackMinYAxisTickStep = 0.1;
const playbackTickMs = 100;

const baseArmJointLimits = [
  { name: "J1", min: -150, max: 150 },
  { name: "J2", min: 0, max: 179.9 },
  { name: "J3", min: -170, max: 0 },
  { name: "J4", min: -99.9, max: 99.9 },
  { name: "J5", min: -69.9, max: 69.9 },
  { name: "J6", min: -120, max: 120 },
];

function armJointLimitsFor(side) {
  return baseArmJointLimits.map((limit, index) => {
    if (index !== 0) return limit;
    if (side === "left") return { ...limit, max: 25 };
    if (side === "right") return { ...limit, min: -25 };
    return limit;
  });
}

const piperJointTopicKeys = {
  left: "piper_left_joint_state_double",
  right: "piper_right_joint_state_double",
};

const piperJointPollIntervalMs = 100;
const piperJointReadWaitSec = 0.04;

const piperEnableActionKey = "piper_enable_all";

const piperJointTopicNames = {
  left: "/joint_states_single_l",
  right: "/joint_states_single_r",
};

const piperWriteActionTopics = {
  left: "/joint_states_gripper_l",
  right: "/joint_states_gripper_r",
};

const piperArmLabels = {
  left: "左臂",
  right: "右臂",
};

const PIPER_GRIPPER_EFFORT = 1.0;
const PIPER_JOINT_SPEED_MIN = 0.5;
const PIPER_JOINT_SPEED_MAX = 30;
const PIPER_JOINT_SPEED_STEP = 0.5;
const ARM_ACTION_PUBLISH_DEBOUNCE_MS = 60;

const deviceBaseControlItems = [
  { key: "linear", label: "前向速度", value: 0, min: 0, max: 1, step: 0.01, unit: "", commandMax: 0.2, commandUnit: "m/s", commandDigits: 3 },
  { key: "lateral", label: "横向速度", value: 0, min: 0, max: 1, step: 0.01, unit: "", commandMax: 0.15, commandUnit: "m/s", commandDigits: 3 },
  { key: "angular", label: "旋转速度", value: 0, min: 0, max: 1, step: 0.01, unit: "", commandMax: 0.5, commandUnit: "rad/s", commandDigits: 3 },
];
const chassisKeyboardDriveMap = {
  w: { action: "forward", label: "W 前进" },
  s: { action: "backward", label: "S 后退" },
  a: { action: "strafe-left", label: "A 左移" },
  d: { action: "strafe-right", label: "D 右移" },
  q: { action: "left", label: "Q 左旋" },
  e: { action: "right", label: "E 右旋" },
};
const CHASSIS_DRIVE_REPEAT_MS = 100;
const CHASSIS_STOP_REPEAT_COUNT = 3;
const CHASSIS_STOP_REPEAT_MS = 25;
const feedbackLatencyThresholdsMs = {
  okMax: 100,
  warnMax: 300,
};

const liftPreviewLimits = {
  min: 0.05,
  max: 0.88,
  speedMin: 0.02,
  speedMax: 0.16,
};

const piperRuntimeLabels = {
  stopped: { title: "Piper 未启动，点击启动", level: "idle", pressed: false },
  starting: { title: "Piper 启动中", level: "warn", pressed: false, busy: true },
  running: { title: "Piper 运行中，点击清理关闭", level: "ok", pressed: true },
  stopping: { title: "Piper 清理关闭中", level: "warn", pressed: true, busy: true },
  external: { title: "检测到旧 Piper ROS，点击清理", level: "warn", pressed: true },
  failed: { title: "Piper 启动失败，点击重试", level: "danger", pressed: false },
  error: { title: "Piper 异常，点击重试", level: "danger", pressed: false },
  unknown: { title: "Piper 状态未知，点击刷新", level: "idle", pressed: false },
};

const liftingRuntimeLabels = {
  stopped: { title: "升降轴未启动，点击启动", level: "idle", pressed: false },
  starting: { title: "升降轴启动中", level: "warn", pressed: false, busy: true },
  running: { title: "升降轴运行中，点击清理关闭", level: "ok", pressed: true },
  stopping: { title: "升降轴清理关闭中", level: "warn", pressed: true, busy: true },
  external: { title: "检测到旧升降轴 ROS，点击清理", level: "warn", pressed: true },
  failed: { title: "升降轴启动失败，点击重试", level: "danger", pressed: false },
  error: { title: "升降轴异常，点击重试", level: "danger", pressed: false },
  unknown: { title: "升降轴状态未知，点击刷新", level: "idle", pressed: false },
};

const chassisRuntimeLabels = {
  stopped: { title: "Chassis 未启动，点击启动", level: "idle", pressed: false },
  starting: { title: "Chassis 启动中", level: "warn", pressed: false, busy: true },
  running: { title: "Chassis 运行中，点击清理关闭", level: "ok", pressed: true },
  stopping: { title: "Chassis 清理关闭中", level: "warn", pressed: true, busy: true },
  external: { title: "检测到旧 Chassis ROS，点击清理", level: "warn", pressed: true },
  failed: { title: "Chassis 启动失败，点击重试", level: "danger", pressed: false },
  error: { title: "Chassis 异常，点击重试", level: "danger", pressed: false },
  unknown: { title: "Chassis 状态未知，点击刷新", level: "idle", pressed: false },
};

const localizationRuntimeLabels = {
  stopped: { title: "Loc 未启动，选择地图后点击启动", level: "idle", pressed: false },
  running: { title: "Loc 已开启，点击停止", level: "ok", pressed: true },
  error: { title: "Loc 异常，点击重试", level: "danger", pressed: false },
};

const cameraRuntimeLabels = {
  stopped: { title: "Camera 未启动，点击启动", level: "idle", pressed: false },
  starting: { title: "Camera 启动中", level: "warn", pressed: false, busy: true },
  running: { title: "Camera 运行中，点击清理关闭", level: "ok", pressed: true },
  stopping: { title: "Camera 清理关闭中", level: "warn", pressed: true, busy: true },
  external: { title: "检测到旧 Camera ROS，点击清理", level: "warn", pressed: true },
  failed: { title: "Camera 启动失败，点击重试", level: "danger", pressed: false },
  error: { title: "Camera 异常，点击重试", level: "danger", pressed: false },
  unknown: { title: "Camera 状态未知，点击刷新", level: "idle", pressed: false },
};

const cameraFeedLayout = [
  { camera: "camera_f", kind: "color", label: "Front RGB" },
  { camera: "camera_l", kind: "color", label: "Left RGB" },
  { camera: "camera_r", kind: "color", label: "Right RGB" },
  { camera: "camera_f", kind: "depth", label: "Front Depth" },
  { camera: "camera_l", kind: "depth", label: "Left Depth" },
  { camera: "camera_r", kind: "depth", label: "Right Depth" },
  { camera: "camera_f", kind: "ir", label: "Front IR" },
  { camera: "camera_l", kind: "ir", label: "Left IR" },
  { camera: "camera_r", kind: "ir", label: "Right IR" },
];
const cameraFrameIntervalMs = 180;
const cameraFrameStaggerMs = 70;
const lidarViewerCloudKey = "rslidar_points";
const robotLidarCloudKey = "rslidar_points";
const lidarFrameIntervalMs = 120;
const lidarFrameWaitSec = 0.15;
const lidarMaxPoints = 60000;
const lidarPointRadiusMin = 0.006;
const lidarPointRadiusMax = 0.035;
const lidarPointRadiusStep = 0.001;
const lidarPointRadiusDefault = 0.014;
const threeModuleUrl = "./vendor/three.module.min.js";
const colladaLoaderUrl = "./vendor/ColladaLoader.js";
const stlLoaderUrl = "./vendor/STLLoader.js";
const urdfLoaderUrl = "./vendor/URDFLoader.js";
const localizationDefaultModelKey = "ranger_mini_v3";
let threeModulePromise = null;
let threeLoaderPromise = null;

const lidarRuntimeLabels = {
  stopped: { title: "LiDAR 未启动，点击启动", level: "idle", pressed: false },
  starting: { title: "LiDAR 启动中", level: "warn", pressed: false, busy: true },
  running: { title: "LiDAR 运行中，点击清理关闭", level: "ok", pressed: true },
  stopping: { title: "LiDAR 清理关闭中", level: "warn", pressed: true, busy: true },
  external: { title: "检测到旧 LiDAR ROS，点击清理", level: "warn", pressed: true },
  failed: { title: "LiDAR 启动失败，点击重试", level: "danger", pressed: false },
  error: { title: "LiDAR 异常，点击重试", level: "danger", pressed: false },
  unknown: { title: "LiDAR 状态未知，点击刷新", level: "idle", pressed: false },
};

const liftingTopicKey = "lifting_motor_state";
const chassisTopicKeys = {
  system: "chassis_system_state",
  motion: "chassis_motion_state",
  battery: "chassis_battery_state",
  odom: "chassis_odom",
};
const mappingStatusMeta = {
  idle: { label: "未开始", level: "idle" },
  ready: { label: "可采集", level: "ok" },
  capturing: { label: "采集中", level: "warn" },
  failed: { label: "失败", level: "danger" },
  saved: { label: "已保存", level: "ok" },
};

const mappingProgressMeta = {
  capturing: { label: "采集点云", level: "warn" },
  filtering: { label: "合并点云", level: "warn" },
  registering: { label: "配准中", level: "warn" },
  registering_ndt: { label: "NDT 配准", level: "warn" },
  registering_gicp: { label: "GICP 配准", level: "warn" },
  writing_map: { label: "写入地图", level: "warn" },
  done: { label: "完成", level: "ok" },
  failed: { label: "失败", level: "danger" },
};

const chassisMotionModeLabels = {
  0: "阿克曼",
  1: "蟹行",
  2: "旋转",
  3: "侧滑",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));
const nativeFetch = window.fetch.bind(window);

window.fetch = async (input, init = {}) => {
  const options = { ...init, credentials: init.credentials || "include" };
  const response = await nativeFetch(input, options);
  if (response.status === 401 && !isAuthApiRequest(input)) {
    const result = await response.clone().json().catch(() => null);
    if (result && typeof result.code === "string" && result.code.startsWith("AUTH-")) {
      applyAuthStatus(result, { fromFetch: true });
    }
  }
  return response;
};

function isAuthApiRequest(input) {
  const url = typeof input === "string" ? input : String(input && input.url ? input.url : "");
  return url.includes("/api/auth/");
}

function formatTime(date = new Date()) {
  return date.toLocaleTimeString("zh-CN", { hour12: false });
}

function addLog(source, message) {
  state.logs.unshift({
    time: formatTime(),
    source,
    message,
  });
  state.logs = state.logs.slice(0, 80);
  renderLogs();
}

function setTask(task, owner, label) {
  state.task = task;
  state.owner = owner;
  setText("#ownerLabel", owner);
  $("#taskStatus").textContent = `当前任务：${label}`;
  $("#drawerTask").textContent = label === "空闲" ? "当前空闲" : `当前任务：${label}`;
  renderActionLocks();
}

function setText(selector, text) {
  const node = $(selector);
  if (node) node.textContent = text;
}

function setStateBadge(selector, text, level) {
  const node = $(selector);
  if (!node) return;
  node.textContent = text;
  node.className = `state-badge ${level}`;
}

function authActiveUserLabel(active = state.auth.active) {
  if (!active || !active.user) return "无";
  return active.client ? `${active.user} @ ${active.client}` : active.user;
}

function setAuthMessage(message, level = "idle") {
  state.auth.message = message;
  state.auth.messageLevel = level;
}

function lockFrontendForAuth(reason) {
  window.clearInterval(state.homingTimer);
  window.clearInterval(state.collectionTimer);
  window.clearInterval(state.inferenceTimer);
  window.clearTimeout(state.armControl.publishTimer);
  state.armControl.active = false;
  state.inference.looping = false;
  const loopToggle = $("#inferenceLoopToggle");
  if (loopToggle) loopToggle.checked = false;
  if (state.task !== "idle") setTask("idle", "空闲", "空闲");
  renderArmComparisons();
  renderInferenceStatus();
  addLog("登录", reason);
}

function populateAuthUsers(users) {
  if (Array.isArray(users) && users.length) {
    state.auth.users = users;
  }
  const select = $("#authUsernameInput");
  if (!select) return;
  const current = select.value || state.auth.user || state.auth.users[0] || "";
  select.innerHTML = state.auth.users.map((user) => `<option value="${escapeHtml(user)}">${escapeHtml(user)}</option>`).join("");
  if (state.auth.users.includes(current)) {
    select.value = current;
  }
}

function renderAuth() {
  populateAuthUsers();
  document.body.classList.toggle("auth-locked", !state.auth.authenticated);
  const overlay = $("#authOverlay");
  if (overlay) overlay.hidden = state.auth.authenticated;

  const status = $("#authStatus");
  if (status) {
    status.textContent = state.auth.authenticated ? `操作者：${state.auth.user}` : `等待登录：${authActiveUserLabel()}`;
    status.className = state.auth.authenticated ? "status-pill ok" : "status-pill warn";
  }

  const logoutButton = $("#authLogoutButton");
  if (logoutButton) logoutButton.disabled = !state.auth.authenticated || state.auth.busy;

  const loginButton = $("#authLoginButton");
  if (loginButton) loginButton.disabled = state.auth.busy;

  const message = $("#authMessage");
  if (message) {
    message.textContent = state.auth.message;
    message.className = `auth-message ${state.auth.messageLevel === "error" ? "is-error" : ""}`;
  }

  const conflictPanel = $("#authConflictPanel");
  if (conflictPanel) conflictPanel.hidden = !state.auth.conflict;
  const conflictDetail = $("#authConflictDetail");
  if (conflictDetail && state.auth.conflict) {
    conflictDetail.textContent = `${authActiveUserLabel(state.auth.conflict)} 正在控制。可以暂停登录，或强制接管并让当前输出进入安全保持。`;
  }

  renderActionLocks();
}

function applyAuthStatus(result, options = {}) {
  if (!result || typeof result !== "object") return;
  populateAuthUsers(result.users);
  state.auth.active = result.active || null;
  state.auth.authenticated = Boolean(result.authenticated);
  state.auth.user = result.authenticated ? (result.user || "") : "";
  if (result.authenticated) {
    state.auth.conflict = null;
    setAuthMessage(`已登录：${state.auth.user}`, "idle");
  } else if (result.code === "AUTH-CONFLICT") {
    state.auth.conflict = result.active || null;
    setAuthMessage("已有操作者在线，请选择暂停登录或强制登录。", "error");
  } else if (result.code === "AUTH-REVOKED") {
    state.auth.conflict = null;
    setAuthMessage("当前登录已被其他用户接管，请重新登录。", "error");
    if (!options.silent) lockFrontendForAuth("当前登录已被强制接管，本地控制已暂停");
  } else {
    state.auth.conflict = null;
    setAuthMessage(result.detail || "请先登录后再控制机器人。", result.code === "AUTH-INVALID" ? "error" : "idle");
  }
  renderAuth();
}

async function refreshAuthStatus(options = {}) {
  try {
    const response = await fetch("/api/auth/status", { cache: "no-store" });
    const result = await response.json().catch(() => ({}));
    applyAuthStatus(result, { silent: options.silent });
    return result;
  } catch (error) {
    if (!options.silent) {
      setAuthMessage(`登录状态检查失败：${error.message}`, "error");
      renderAuth();
    }
    return null;
  }
}

async function submitAuthLogin(force = false) {
  const username = String($("#authUsernameInput")?.value || "").trim();
  const password = String($("#authPasswordInput")?.value || "");
  if (!username || !password) {
    setAuthMessage("请输入用户名和密码。", "error");
    renderAuth();
    return;
  }
  state.auth.busy = true;
  state.auth.conflict = force ? state.auth.conflict : null;
  setAuthMessage(force ? "正在强制接管..." : "正在登录...", "idle");
  renderAuth();
  try {
    const response = await fetch("/api/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ username, password, force }),
      cache: "no-store",
    });
    const result = await response.json().catch(() => ({}));
    applyAuthStatus(result);
    if (result.ok) {
      addLog("登录", result.code === "AUTH-FORCED" ? `${username} 已强制接管控制权` : `${username} 已登录`);
    }
  } catch (error) {
    setAuthMessage(`登录失败：${error.message}`, "error");
    renderAuth();
  } finally {
    state.auth.busy = false;
    renderAuth();
  }
}

async function logoutAuth() {
  if (!state.auth.authenticated) {
    renderAuth();
    return;
  }
  state.auth.busy = true;
  renderAuth();
  try {
    const response = await fetch("/api/auth/logout", { method: "POST", cache: "no-store" });
    const result = await response.json().catch(() => ({}));
    applyAuthStatus(result);
    addLog("登录", "已退出登录，机器人输出已请求安全保持");
  } catch (error) {
    addLog("登录", `退出登录失败：${error.message}`);
  } finally {
    state.auth.busy = false;
    renderAuth();
  }
}

function clamp(value, min, max) {
  return Math.max(min, Math.min(max, value));
}

function normalizedSpeedValue(item) {
  if (!item) return 0;
  const min = Number.isFinite(Number(item.min)) ? Number(item.min) : 0;
  const max = Number.isFinite(Number(item.max)) ? Number(item.max) : 1;
  const value = Number(item.value);
  return Number.isFinite(value) ? clamp(value, min, max) : min;
}

function commandSpeedValue(item, value = normalizedSpeedValue(item)) {
  if (!item) return 0;
  const commandMax = Number(item.commandMax);
  return Number.isFinite(commandMax) ? value * commandMax : value;
}

function formatCommandSpeed(item, value = normalizedSpeedValue(item)) {
  if (!item) return "--";
  const digits = Number.isInteger(item.commandDigits) ? item.commandDigits : 2;
  const unit = item.commandUnit || item.unit || "";
  return `${formatNumber(commandSpeedValue(item, value), digits)} ${unit}`.trim();
}

function chassisControlUrl(path) {
  const configuredOrigin = String(window.ROBOT_STATION_CONTROL_ORIGIN || "").trim();
  if (configuredOrigin) {
    return `${configuredOrigin.replace(/\/+$/, "")}${path}`;
  }

  const configuredPort = String(window.ROBOT_STATION_CONTROL_PORT || "9998").trim();
  if (window.location.protocol === "http:" && window.location.hostname && configuredPort && configuredPort !== window.location.port) {
    return `${window.location.protocol}//${window.location.hostname}:${configuredPort}${path}`;
  }
  return path;
}

async function fetchChassisControl(path, payload) {
  const primaryUrl = chassisControlUrl(path);
  const init = {
    method: "POST",
    headers: { "Content-Type": "text/plain;charset=UTF-8" },
    body: JSON.stringify(payload),
    cache: "no-store",
    priority: "high",
  };
  try {
    return await fetch(primaryUrl, init);
  } catch (error) {
    if (primaryUrl === path) {
      throw error;
    }
    return fetch(path, init);
  }
}

function liftingControlUrl(path) {
  const configuredOrigin = String(window.ROBOT_STATION_LIFTING_CONTROL_ORIGIN || "").trim();
  if (configuredOrigin) {
    return `${configuredOrigin.replace(/\/+$/, "")}${path}`;
  }

  const configuredPort = String(window.ROBOT_STATION_LIFTING_CONTROL_PORT || "9997").trim();
  if (window.location.protocol === "http:" && window.location.hostname && configuredPort && configuredPort !== window.location.port) {
    return `${window.location.protocol}//${window.location.hostname}:${configuredPort}${path}`;
  }
  return path;
}

async function fetchLiftingControl(path, payload) {
  const primaryUrl = liftingControlUrl(path);
  const init = {
    method: "POST",
    // text/plain keeps this a CORS "simple request" so the browser skips the
    // preflight round-trip; the backend parses the JSON body regardless.
    headers: { "Content-Type": "text/plain;charset=UTF-8" },
    body: JSON.stringify(payload),
    cache: "no-store",
    priority: "high",
  };
  try {
    return await fetch(primaryUrl, init);
  } catch (error) {
    if (primaryUrl === path) {
      throw error;
    }
    return fetch(path, init);
  }
}

function piperControlUrl(path) {
  const configuredOrigin = String(window.ROBOT_STATION_PIPER_CONTROL_ORIGIN || "").trim();
  if (configuredOrigin) {
    return `${configuredOrigin.replace(/\/+$/, "")}${path}`;
  }

  const configuredPort = String(window.ROBOT_STATION_PIPER_CONTROL_PORT || "9996").trim();
  if (window.location.protocol === "http:" && window.location.hostname && configuredPort && configuredPort !== window.location.port) {
    return `${window.location.protocol}//${window.location.hostname}:${configuredPort}${path}`;
  }
  return path;
}

async function fetchPiperControl(path, payload) {
  const primaryUrl = piperControlUrl(path);
  const init = {
    method: "POST",
    // text/plain keeps this a CORS "simple request" so the browser skips the
    // preflight round-trip; the backend parses the JSON body regardless.
    headers: { "Content-Type": "text/plain;charset=UTF-8" },
    body: JSON.stringify(payload),
    cache: "no-store",
    priority: "high",
  };
  try {
    return await fetch(primaryUrl, init);
  } catch (error) {
    if (primaryUrl === path) {
      throw error;
    }
    return fetch(path, init);
  }
}

function speedRiskColor(value) {
  const percent = clamp(Number(value), 0, 1) * 100;
  if (percent <= 50) {
    const mix = percent / 50;
    return `rgb(${Math.round(22 + 223 * mix)}, ${Math.round(163 - 5 * mix)}, ${Math.round(74 - 63 * mix)})`;
  }
  const mix = (percent - 50) / 50;
  return `rgb(${Math.round(245 - 25 * mix)}, ${Math.round(158 - 120 * mix)}, ${Math.round(11 + 27 * mix)})`;
}

function normalizeJointSpeedDegS(value, fallback = state.armControl.maxJointSpeedDegS) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return fallback;
  const stepped = Math.round(parsed / PIPER_JOINT_SPEED_STEP) * PIPER_JOINT_SPEED_STEP;
  return clamp(stepped, PIPER_JOINT_SPEED_MIN, PIPER_JOINT_SPEED_MAX);
}

function formatNumber(value, digits = 3) {
  return Number.isFinite(value) ? value.toFixed(digits) : "--";
}

function formatBytes(value) {
  const bytes = Number(value);
  if (!Number.isFinite(bytes) || bytes <= 0) return "--";
  const units = ["B", "KB", "MB", "GB"];
  let size = bytes;
  let unitIndex = 0;
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024;
    unitIndex += 1;
  }
  return `${size >= 10 || unitIndex === 0 ? size.toFixed(0) : size.toFixed(1)} ${units[unitIndex]}`;
}

function radToDeg(rad) {
  return rad * 180 / Math.PI;
}

function statusSwitchClass(level) {
  if (level === "ok") return "is-on";
  if (level === "warn") return "is-warn";
  if (level === "danger") return "is-danger";
  return "is-idle";
}

function renderStatusSwitch(selector, label, level, options = {}) {
  const node = $(selector);
  if (!node) return;
  const pressed = options.pressed !== undefined ? options.pressed : level === "ok";
  const classes = ["status-switch", statusSwitchClass(level)];
  if (options.readonly) classes.push("is-readonly");
  if (options.busy) classes.push("is-busy");
  node.className = classes.join(" ");
  node.innerHTML = `<span>${label}</span><i aria-hidden="true"></i>`;
  node.title = options.title || label;
  node.setAttribute("aria-label", options.title || label);
  node.setAttribute("aria-pressed", pressed ? "true" : "false");
  if (options.readonly) {
    node.setAttribute("aria-disabled", "true");
    node.setAttribute("tabindex", "-1");
  } else {
    node.removeAttribute("aria-disabled");
    node.removeAttribute("tabindex");
  }
}

function piperReady() {
  return state.piperRuntime.status === "running";
}

function liftingReady() {
  return state.liftingRuntime.status === "running" || state.liftingRuntime.status === "external";
}

function chassisReady() {
  return state.chassisRuntime.status === "running" || state.chassisRuntime.status === "external";
}

function liftingInitialized() {
  return liftingReady() && state.liftingState.ok && !state.liftingState.stale && state.liftingState.initState;
}

function getPiperRuntimeLabel() {
  return piperRuntimeLabels[state.piperRuntime.status] || piperRuntimeLabels.error;
}

function getLiftingRuntimeLabel() {
  return liftingRuntimeLabels[state.liftingRuntime.status] || liftingRuntimeLabels.error;
}

function getChassisRuntimeLabel() {
  return chassisRuntimeLabels[state.chassisRuntime.status] || chassisRuntimeLabels.error;
}

function getLocalizationRuntimeLabel() {
  if (!state.localization.selectedMapName && state.localizationRuntime.status !== "running") {
    return { ...localizationRuntimeLabels.stopped, title: "请先在定位页面选择地图" };
  }
  return localizationRuntimeLabels[state.localizationRuntime.status] || localizationRuntimeLabels.error;
}

function getCameraRuntimeLabel() {
  return cameraRuntimeLabels[state.cameraRuntime.status] || cameraRuntimeLabels.error;
}

function getLidarRuntimeLabel() {
  return lidarRuntimeLabels[state.lidarRuntime.status] || lidarRuntimeLabels.error;
}

function setPiperRuntime(status) {
  state.piperRuntime.status = piperRuntimeLabels[status] ? status : "unknown";
  if (state.piperRuntime.status !== "running" && state.armControl.active) {
    window.clearTimeout(state.armControl.publishTimer);
    state.armControl.active = false;
    state.armControl.busy = false;
  }
  renderPiperRuntime();
  renderPiperJointFeedback();
  renderInferenceStatus();
  renderActionLocks();
}

function setLiftingRuntime(status) {
  state.liftingRuntime.status = liftingRuntimeLabels[status] ? status : "unknown";
  renderLiftingRuntime();
  renderLiftPreview();
}

function setChassisRuntime(status) {
  state.chassisRuntime.status = chassisRuntimeLabels[status] ? status : "unknown";
  if (!chassisReady() && state.chassisControl.keyboardListening) {
    stopChassisKeyboardControl("Chassis 服务未运行，键盘监听停止", { deactivate: true });
  }
  renderChassisRuntime();
  renderDeviceBaseMetrics();
}

function setLocalizationRuntime(status) {
  state.localizationRuntime.status = localizationRuntimeLabels[status] ? status : "error";
  renderLocalizationRuntime();
  renderLocalizationStatus();
}

function setCameraRuntime(status) {
  state.cameraRuntime.status = cameraRuntimeLabels[status] ? status : "unknown";
  renderCameraRuntime();
}

function setLidarRuntime(status) {
  state.lidarRuntime.status = lidarRuntimeLabels[status] ? status : "unknown";
  renderLidarRuntime();
}

function showView(view) {
  if (!["platform-control", "robot-view"].includes(view) && state.chassisControl.keyboardListening) {
    stopChassisKeyboardControl("离开底盘控制视图，键盘监听停止", { deactivate: true });
  }
  document.body.dataset.activeView = view;
  $$(".nav-item").forEach((item) => item.classList.toggle("is-active", item.dataset.view === view));
  $$(".view").forEach((panel) => panel.classList.toggle("is-active", panel.dataset.viewPanel === view));
  if (view === "sensors") {
    window.setTimeout(resizeLidarViewer, 0);
  }
  if (view === "data-playback") {
    renderPlayback();
  }
  if (view === "robot-view") {
    fetchRobotModels({ silent: true });
    initializeRobotViewer();
    window.setTimeout(resizeRobotViewer, 0);
  }
  if (view === "localization") {
    fetchLocalizationMaps({ silent: true });
    ensureLocalizationRobotModel();
    window.setTimeout(() => {
      syncRobotViewerMount();
      syncRobotViewerLayersForView();
      resizeRobotViewer();
      renderLocalizationStatus();
    }, 0);
  } else {
    window.setTimeout(() => {
      syncRobotViewerMount();
      syncRobotViewerLayersForView();
      resizeRobotViewer();
      updateRobotModelTransforms();
    }, 0);
  }
}

function renderHealth() {
  const grid = $("#healthGrid");
  if (!grid) return;
  grid.innerHTML = healthItems
    .map(
      ([name, level, primary, percent, detail]) => `
        <article class="health-card ${level}">
          <strong>${name}</strong>
          <span>${primary}</span>
          <div class="health-meter"><i style="width:${percent}%"></i></div>
          <span>${detail}</span>
        </article>
      `,
    )
    .join("");
}

function statusClass(text) {
  if (text === "正常") return "ok";
  if (text === "警告") return "warn";
  if (text === "错误") return "danger";
  return "idle";
}

function cloneCheckItems(items) {
  return items.map((item) => ({
    ...item,
    metric: { ...item.metric },
  }));
}

function renderSelfCheckOverview(items) {
  const counts = items.reduce(
    (acc, item) => {
      acc[statusClass(item.status)] += 1;
      return acc;
    },
    { ok: 0, warn: 0, danger: 0, idle: 0 },
  );
  const total = items.length;
  const stateText = counts.danger
    ? "存在阻塞"
    : counts.warn
      ? "有警告"
      : counts.idle === total
        ? "未检测"
        : "可继续";
  const stateLevel = counts.danger ? "danger" : counts.warn ? "warn" : counts.idle === total ? "idle" : "ok";
  const checkedAt = state.selfCheckRanAt ? formatTime(state.selfCheckRanAt) : "--";

  $("#selfCheckOverview").innerHTML = [
    ["总体状态", stateText, stateLevel, `最近检查 ${checkedAt}`],
    ["正常", counts.ok, "ok", `${total} 项中的通过项`],
    ["警告", counts.warn, counts.warn ? "warn" : "idle", "需要操作员确认"],
    ["错误", counts.danger, counts.danger ? "danger" : "idle", "会阻塞任务启动"],
  ]
    .map(
      ([label, value, level, detail]) => `
        <article class="self-summary-card ${level}">
          <span>${label}</span>
          <strong>${value}</strong>
          <small>${detail}</small>
        </article>
      `,
    )
    .join("");
}

function renderSelfCheckMetrics(items) {
  const metricNames = ["CAN 接口", "相机帧率", "磁盘空间", "GPU 可用性"];
  $("#selfCheckMetrics").innerHTML = metricNames
    .map((name) => items.find((item) => item.name === name))
    .filter(Boolean)
    .map((item) => {
      const level = item.metric.level || statusClass(item.status);
      return `
        <article class="mini-metric ${level}">
          <div>
            <span>${item.metric.label}</span>
            <strong>${item.metric.value}</strong>
          </div>
          <div class="mini-bar" aria-hidden="true">
            <i style="width:${item.metric.percent}%"></i>
          </div>
          <small>${item.name}</small>
        </article>
      `;
    })
    .join("");
}

function renderSelfCheck(items = selfCheckItems) {
  state.selfCheckResults = cloneCheckItems(items);
  renderSelfCheckOverview(items);
  renderSelfCheckMetrics(items);
  $("#selfCheckTable").innerHTML = items
    .map((item, index) => {
      const level = statusClass(item.status);
      const checkedAt = item.checkedAt || "--";
      return `
        <div
          class="check-row"
          data-check-index="${index}"
          data-tooltip-title="${item.name}"
          data-tooltip-code="${item.code}"
          data-tooltip-time="${checkedAt}"
          data-tooltip-detail="${item.detail}"
          data-tooltip-advice="${item.advice}"
        >
          <strong>${item.name}</strong>
          <span class="status-text ${level}">${item.status}</span>
          <span>${item.advice}</span>
          <div class="check-actions" aria-label="${item.name}操作">
            <button data-check-action="log" data-check-index="${index}">日志</button>
            <button data-check-action="retry" data-check-index="${index}">复查</button>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderAdvice() {
  const html = state.alerts
    .map(
      (alert) => `
        <div class="advice-item ${alert.level}">
          <strong>${alert.title}</strong>
          <span>${alert.detail}</span>
        </div>
      `,
    )
    .join("");
  const adviceList = $("#adviceList");
  if (adviceList) adviceList.innerHTML = html;
  $("#drawerAlerts").innerHTML = html;
  $("#alertStatus").textContent = `告警 ${state.alerts.length}`;
}

function renderHomingSteps(activeIndex = -1, failedIndex = -1) {
  const stepsNode = $("#homingSteps");
  if (!stepsNode) return;
  stepsNode.innerHTML = homingSteps
    .map((step, index) => {
      let cls = "";
      if (failedIndex === index) cls = "is-error";
      else if (index < activeIndex) cls = "is-done";
      else if (index === activeIndex) cls = "is-current";
      return `<li class="${cls}">${step}</li>`;
    })
    .join("");
}

function renderHomeFlow(steps, activeIndex, progress) {
  const stepsNode = $("#homeFlowSteps");
  const progressBar = $("#taskProgressBar");
  if (!stepsNode || !progressBar) return;
  stepsNode.innerHTML = steps
    .map((step, index) => {
      const cls = index < activeIndex ? "is-done" : index === activeIndex ? "is-current" : "";
      return `<li class="${cls}">${step}</li>`;
    })
    .join("");
  progressBar.style.width = `${progress}%`;
}

function renderCollectionMetrics() {
  const frames = Math.max(0, state.collectionSeconds * 29 - 3);
  const size = (state.collectionSeconds * 0.18).toFixed(1);
  const dropped = state.collectionSeconds > 15 ? 4 : 0;
  $("#collectionMetrics").innerHTML = [
    ["录制时长", `${state.collectionSeconds}s`],
    ["帧率", "29.4 fps"],
    ["丢帧", `${dropped}`],
    ["数据大小", `${size} GB`],
    ["Episode", "043"],
    ["样本帧", `${frames}`],
  ]
    .map(([label, value]) => `<div class="metric-card"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");

  $("#qualityStrip").innerHTML = [
    ["相机帧率", dropped ? "警告" : "正常", dropped ? "front_rgb 有短时丢帧。" : "帧率稳定。"],
    ["磁盘空间", "警告", "剩余空间低于建议值。"],
    ["时间戳", "正常", "传感器时间戳连续。"],
  ]
    .map(([name, status, detail]) => `<div class="quality-item"><strong>${name}</strong><span class="status-text ${statusClass(status)}">${status}</span><span>${detail}</span></div>`)
    .join("");
}

const INFERENCE_STATUS_LABELS = {
  disconnected: "未连接",
  connected: "已连接",
  requesting: "请求中",
  chunk_ready: "chunk 就绪",
  executing: "执行中",
  stopped: "已停止",
  error: "错误",
};
const INFERENCE_STATUS_LEVELS = {
  disconnected: "idle",
  connected: "ok",
  requesting: "warn",
  chunk_ready: "ok",
  executing: "warn",
  stopped: "idle",
  error: "danger",
};

function renderInferenceMetrics() {
  const info = state.inference;
  const node = $("#inferenceMetrics");
  if (!node) return;
  const loopTiming = info.loopTiming || {};
  const statusText = INFERENCE_STATUS_LABELS[info.status] || info.status || "--";
  const loopText = info.looping ? (loopTiming.seq ? `开启 #${loopTiming.seq}` : "开启") : "关闭";
  node.innerHTML = [
    ["连接", info.connected ? "已连接" : "未连接"],
    ["状态", statusText],
    ["chunk", info.chunkId ? `${info.chunkId} (${info.chunkSteps} 步)` : "无"],
    ["已执行", `${info.executedSteps} 步`],
    ["连续闭环", loopText],
    ["控制权", state.owner],
    ["动作通道", describeMask()],
  ]
    .map(([label, value]) => `<div class="metric-card"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
}

function applyInferenceStatus(result) {
  if (!result || typeof result !== "object") return;
  const info = state.inference;
  if (typeof result.status === "string") info.status = result.status;
  if ("connected" in result) info.connected = Boolean(result.connected);
  if ("remoteUrl" in result) info.remoteUrl = result.remoteUrl || "";
  if ("prompt" in result) info.prompt = result.prompt || "";
  if ("chunkId" in result) info.chunkId = result.chunkId || null;
  if ("chunkSteps" in result) info.chunkSteps = Number(result.chunkSteps) || 0;
  if ("executedSteps" in result) info.executedSteps = Number(result.executedSteps) || 0;
  if ("chunkTiming" in result) info.chunkTiming = result.chunkTiming || null;
  if ("executionTiming" in result) info.executionTiming = result.executionTiming || null;
  if ("lastError" in result) info.lastError = result.lastError || null;
  renderInferenceStatus();
}

function renderInferenceStatus() {
  const info = state.inference;
  const locked = !state.auth.authenticated;
  const level = INFERENCE_STATUS_LEVELS[info.status] || "idle";
  setStateBadge("#inferenceBadge", INFERENCE_STATUS_LABELS[info.status] || info.status, level);
  const summary = $("#inferenceSummary");
  if (summary) {
    if (info.lastError && info.status === "error") {
      summary.textContent = `错误：${info.lastError}`;
    } else if (!info.connected) {
      summary.textContent = "未连接远端推理服务";
    } else {
      summary.textContent = `${INFERENCE_STATUS_LABELS[info.status] || info.status}${info.remoteUrl ? ` · ${info.remoteUrl}` : ""}`;
    }
  }
  const connectButton = $("#inferenceConnectButton");
  if (connectButton) connectButton.disabled = locked || info.busy;
  const disconnectButton = $("#inferenceDisconnectButton");
  if (disconnectButton) disconnectButton.disabled = locked || info.busy || !info.connected;
  const requestButton = $("#requestChunkButton");
  if (requestButton) requestButton.disabled = locked || info.busy || !info.connected || info.looping;
  const executeButton = $("#executeChunkButton");
  if (executeButton) executeButton.disabled = locked || info.busy || !info.chunkId || info.looping;
  const enableButton = $("#inferenceEnablePiperButton");
  if (enableButton) {
    enableButton.disabled = locked || info.busy || state.piperEnableBusy || !piperReady();
    enableButton.textContent = state.piperEnableBusy ? "使能中" : "使能 Piper";
  }
  renderInferenceMetrics();
}

function renderPreflight() {
  const selfCheckFresh = Boolean(state.selfCheckRanAt);
  const idle = state.task === "idle";
  const runtimeReady = piperReady();
  $("#preflightList").innerHTML = [
    ["任务控制权", idle ? "正常" : "警告", idle ? "当前空闲。" : "已有任务占用机器人。"],
    ["Piper 控制", runtimeReady ? "正常" : "警告", runtimeReady ? "双臂控制节点运行中。" : "Piper 控制节点未启动。"],
    ["最近自检", selfCheckFresh ? "正常" : "警告", selfCheckFresh ? "自检结果可用。" : "建议先执行整机自检。"],
    ["人工停止", "正常", "顶部停止按钮可用。"],
  ]
    .map(([name, status, detail]) => `<div class="preflight-item"><strong>${name}</strong><span class="status-text ${statusClass(status)}">${status}</span><span>${detail}</span></div>`)
    .join("");
}

function jointPercent(value, limit) {
  return ((value - limit.min) / (limit.max - limit.min)) * 100;
}

function actionReady(side) {
  const action = state.piperActions[side];
  return Boolean(action && action.positions.every((value) => Number.isFinite(Number(value))));
}

function allActionsReady() {
  return actionReady("left") && actionReady("right");
}

function feedbackAgeMs(feedback) {
  const parsed = Number(feedback && feedback.ageMs);
  return Number.isFinite(parsed) ? Math.max(0, Math.round(parsed)) : null;
}

function feedbackLatencyLevelFromAge(ageMs) {
  const parsed = Number(ageMs);
  if (!Number.isFinite(parsed)) return "idle";
  if (parsed <= feedbackLatencyThresholdsMs.okMax) return "ok";
  if (parsed <= feedbackLatencyThresholdsMs.warnMax) return "warn";
  return "danger";
}

function feedbackLatencyText(ageMs) {
  const parsed = Number(ageMs);
  if (!Number.isFinite(parsed)) return "--";
  if (parsed < 1000) return `${Math.max(0, Math.round(parsed))} ms`;
  return `${(parsed / 1000).toFixed(1)} s`;
}

function feedbackLatencyMeta(feedback, options = {}) {
  const ready = options.ready !== false;
  const stoppedText = options.stoppedText || "未启动";
  const waitingText = options.waitingText || "等待反馈";
  if (!ready) {
    return { level: "idle", text: stoppedText, detail: "无反馈", inlineText: stoppedText, ageMs: null };
  }
  if (!feedback || !feedback.ok) {
    if (feedback && feedback.code === "ROS-R-WAITING") {
      return { level: "idle", text: waitingText, detail: "无数据", inlineText: waitingText, ageMs: null };
    }
    if (feedback && feedback.code === "ROS-R-NODATA") {
      return { level: "warn", text: "无反馈", detail: "无数据", inlineText: "无反馈", ageMs: null };
    }
    return { level: "danger", text: "异常", detail: "不可用", inlineText: "反馈异常", ageMs: null };
  }
  const ageMs = feedbackAgeMs(feedback);
  if (ageMs === null) {
    const level = feedback.stale ? "warn" : "ok";
    return { level, text: "已接收", detail: "无延迟数据", inlineText: "已接收", ageMs: null };
  }
  const level = feedbackLatencyLevelFromAge(ageMs);
  const detail = feedbackLatencyText(ageMs);
  return { level, text: "延迟", detail, inlineText: `延迟 ${detail}`, ageMs };
}

function feedbackLevel(feedback) {
  if (!feedback) return "idle";
  if (feedback && feedback.ok) return feedbackLatencyMeta(feedback).level;
  if (feedback.code === "ROS-R-WAITING") return "idle";
  if (feedback.code === "ROS-R-NODATA") return "warn";
  return "danger";
}

function armStatusText(side) {
  const feedback = state.piperJoints[side];
  if (!feedback) return { level: "idle", text: "等待反馈", detail: "无数据" };
  if (feedback.ok) {
    return feedbackLatencyMeta(feedback);
  }
  if (!piperReady()) {
    return { level: "idle", text: "未启动", detail: "等待 Piper" };
  }
  const level = feedbackLevel(feedback);
  const waiting = feedback.code === "ROS-R-WAITING" || feedback.code === "ROS-R-NODATA";
  return {
    level,
    text: waiting ? "等待反馈" : "异常",
    detail: waiting ? "无数据" : "不可用",
  };
}

function renderArmCompareBadge() {
  const sides = ["left", "right"];
  const statuses = sides.map((side) => armStatusText(side));
  const onlineCount = statuses.filter((status) => status.level === "ok").length;
  const warnCount = statuses.filter((status) => status.level === "warn").length;
  const dangerCount = statuses.filter((status) => status.level === "danger").length;
  if (onlineCount === sides.length) {
    setStateBadge("#armCompareBadge", "双臂在线", "ok");
    return;
  }
  if (dangerCount > 0) {
    setStateBadge("#armCompareBadge", dangerCount === sides.length ? "反馈超时" : "部分超时", "danger");
    return;
  }
  if (onlineCount > 0 || warnCount > 0) {
    setStateBadge("#armCompareBadge", "部分在线", "warn");
    return;
  }
  setStateBadge("#armCompareBadge", piperReady() ? "等待反馈" : "未启动", piperReady() ? "warn" : "idle");
}

function stateValueFor(feedback, index) {
  if (!feedback || !feedback.ok || !Array.isArray(feedback.positions)) return NaN;
  return Number(feedback.positions[index]);
}

function normalizedJointStateName(name) {
  return String(name || "").trim().replace(/^\/+/, "");
}

function jointStateNameMatches(actualName, expectedName) {
  const actual = normalizedJointStateName(actualName);
  const expected = normalizedJointStateName(expectedName);
  return actual === expected || actual.endsWith(`/${expected}`);
}

function jointStateIndexForName(feedback, expectedName) {
  const names = Array.isArray(feedback?.names) ? feedback.names : [];
  if (!names.length || !Array.isArray(feedback?.positions) || names.length !== feedback.positions.length) return -1;
  return names.findIndex((name) => jointStateNameMatches(name, expectedName));
}

function hasZeroBasedPiperJointNames(feedback) {
  const names = Array.isArray(feedback?.names) ? feedback.names : [];
  return names.some((name) => jointStateNameMatches(name, "joint0"));
}

// Piper feedback uses joint0..joint6, while the URDF uses joint1..joint8.
function robotArmStateValueFor(feedback, side, robotJointName, fallbackIndex) {
  if (!feedback || !feedback.ok || !Array.isArray(feedback.positions)) return NaN;
  const names = Array.isArray(feedback.names) ? feedback.names : [];
  if (names.length === feedback.positions.length) {
    const bareName = String(robotJointName || "").split("/").pop();
    const exactCandidates = [robotJointName, `${side}/${bareName}`].filter(Boolean);
    for (const candidate of exactCandidates) {
      const namedIndex = jointStateIndexForName(feedback, candidate);
      if (namedIndex >= 0) return Number(feedback.positions[namedIndex]);
    }

    const piperIndex = hasZeroBasedPiperJointNames(feedback) ? fallbackIndex : fallbackIndex + 1;
    const piperCandidates = [`joint${piperIndex}`, `joint_${piperIndex}`];
    for (const candidate of piperCandidates) {
      const namedIndex = jointStateIndexForName(feedback, candidate);
      if (namedIndex >= 0) return Number(feedback.positions[namedIndex]);
    }
  }
  return Number(feedback.positions[fallbackIndex]);
}

function gripperStateValueFor(feedback) {
  if (!feedback || !feedback.ok || !Array.isArray(feedback.positions)) return NaN;
  const names = Array.isArray(feedback.names) ? feedback.names : [];
  if (names.length === feedback.positions.length) {
    const candidates = hasZeroBasedPiperJointNames(feedback)
      ? ["joint6", "joint_6", "gripper", "gripper_joint"]
      : ["joint7", "joint_7", "gripper", "gripper_joint"];
    for (const candidate of candidates) {
      const namedIndex = jointStateIndexForName(feedback, candidate);
      if (namedIndex >= 0) return Number(feedback.positions[namedIndex]);
    }
  }
  return Number(feedback.positions[6]);
}

function actionValueFor(side, index) {
  const action = state.piperActions[side];
  if (action && Number.isFinite(Number(action.positions[index]))) {
    return Number(action.positions[index]);
  }
  return stateValueFor(state.piperJoints[side], index);
}

function seedActionFromState(side) {
  const action = state.piperActions[side];
  const feedback = state.piperJoints[side];
  if (!action || actionReady(side) || !feedback || !Array.isArray(feedback.positions) || feedback.positions.length < 7) return;
  action.positions = feedback.positions.slice(0, 7).map((value) => Number(value));
  action.status = "ready";
  action.detail = "Action 跟随当前 State 初始化，可拖动滑条调整。";
}

function canCopyStateToAction(side) {
  const feedback = state.piperJoints[side];
  if (!feedback || !feedback.ok || !Array.isArray(feedback.positions) || feedback.positions.length < 7) return false;
  return feedback.positions.slice(0, 7).every((value) => Number.isFinite(Number(value)));
}

function allArmStatesCopyable() {
  return ["left", "right"].every((side) => canCopyStateToAction(side));
}

function copyAllStatesToActions() {
  if (!allArmStatesCopyable()) {
    ["left", "right"].forEach((side) => {
      const action = state.piperActions[side];
      if (!action || canCopyStateToAction(side)) return;
      action.status = "idle";
      action.detail = `${piperArmLabels[side]} State 暂不可复制。`;
    });
    addLog("机械臂", "复制 State 失败：左右臂反馈未全部就绪");
    renderArmComparisons();
    return;
  }

  ["left", "right"].forEach((side) => {
    const action = state.piperActions[side];
    const feedback = state.piperJoints[side];
    action.positions = feedback.positions.slice(0, 7).map((value) => Number(value));
    action.status = "ready";
    action.detail = "已复制当前 State 到 Action。";
  });
  addLog("机械臂", "已复制左右臂 State 到 Action");
  renderArmComparisons();
}

function zeroAllArmActions() {
  ["left", "right"].forEach((side) => {
    const action = state.piperActions[side];
    if (!action) return;
    action.positions = [0, 0, 0, 0, 0, 0, 0];
    action.status = "ready";
    action.detail = "归位目标已设为 0。";
  });
  addLog("机械臂", "归位目标已设为左右臂全关节与夹爪 0");
  renderArmComparisons();
  if (state.armControl.active) {
    scheduleDirectArmPublish();
  }
}

function renderJointBounds(limit) {
  const minRad = (limit.min * Math.PI) / 180;
  const maxRad = (limit.max * Math.PI) / 180;
  return `${limit.min} deg / ${formatNumber(minRad, 4)} rad ~ ${limit.max} deg / ${formatNumber(maxRad, 4)} rad`;
}

function renderJointCompareRow(side, limit, index) {
  seedActionFromState(side);
  const feedback = state.piperJoints[side];
  const stateRad = stateValueFor(feedback, index);
  const hasState = Number.isFinite(stateRad);
  const stateDeg = hasState ? radToDeg(stateRad) : NaN;
  const statePercent = hasState ? clamp(jointPercent(stateDeg, limit), 0, 100) : 0;
  const actionRad = actionValueFor(side, index);
  const hasAction = Number.isFinite(actionRad);
  const actionDeg = hasAction ? radToDeg(actionRad) : limit.min;

  return `
    <div class="joint-compare-card">
      <div class="joint-compare-head">
        <strong>${limit.name}</strong>
        <span>${renderJointBounds(limit)}</span>
      </div>
      <div class="compare-value state-value">
        <span class="compare-label">State</span>
        <span class="joint-state-indicator" aria-hidden="true"><i style="width: ${statePercent}%"></i></span>
        <strong>${hasState ? formatNumber(stateDeg, 2) : "--"} deg</strong>
        <small>${hasState ? formatNumber(stateRad, 4) : "--"} rad</small>
      </div>
      <div class="compare-value action-value">
        <span class="compare-label">Action</span>
        <input
          type="range"
          min="${limit.min}"
          max="${limit.max}"
          step="0.1"
          value="${formatNumber(actionDeg, 2)}"
          style="--action-position: ${hasAction ? clamp(jointPercent(actionDeg, limit), 0, 100) : 0}%"
          data-action-side="${side}"
          data-action-kind="joint"
          data-action-index="${index}"
          aria-label="${piperArmLabels[side]} ${limit.name} action deg"
        />
        <strong>${hasAction ? formatNumber(actionDeg, 2) : "--"} deg</strong>
        <small>${hasAction ? formatNumber(actionRad, 4) : "--"} rad</small>
      </div>
    </div>
  `;
}

function renderGripperCompareRow(side) {
  seedActionFromState(side);
  const feedback = state.piperJoints[side];
  const stateMeters = stateValueFor(feedback, 6);
  const hasState = Number.isFinite(stateMeters);
  const statePercent = hasState ? clamp(stateMeters * 1000, 0, 100) : 0;
  const actionMeters = actionValueFor(side, 6);
  const hasAction = Number.isFinite(actionMeters);
  const sliderValue = hasAction ? actionMeters : 0;

  return `
    <div class="joint-compare-card">
      <div class="joint-compare-head">
        <strong>夹爪</strong>
        <span>0 m ~ 0.1 m</span>
      </div>
      <div class="compare-value state-value gripper-feedback-row">
        <span class="compare-label">State</span>
        <span class="joint-state-indicator" aria-hidden="true"><i style="width: ${statePercent}%"></i></span>
        <strong>${hasState ? formatNumber(stateMeters, 4) : "--"} m</strong>
        <small>position[6]</small>
      </div>
      <div class="compare-value action-value gripper-feedback-row">
        <span class="compare-label">Action</span>
        <input
          type="range"
          min="0"
          max="0.1"
          step="0.001"
          value="${formatNumber(sliderValue, 4)}"
          style="--action-position: ${hasAction ? clamp(actionMeters * 1000, 0, 100) : 0}%"
          data-action-side="${side}"
          data-action-kind="gripper"
          data-action-index="6"
          aria-label="${piperArmLabels[side]} gripper action m"
        />
        <strong>${hasAction ? formatNumber(actionMeters, 4) : "--"} m</strong>
        <small>position[6]</small>
      </div>
    </div>
  `;
}

function renderArmComparison(side) {
  const label = piperArmLabels[side] || side;
  const action = state.piperActions[side];
  const status = armStatusText(side);
  const jointRows = armJointLimitsFor(side).map((limit, index) => renderJointCompareRow(side, limit, index)).join("");

  return `
    <section class="arm-inline-card" data-arm-panel="${side}">
      <div class="arm-inline-head">
        <div>
          <h3>${label}</h3>
          <p>
            <span class="status-text ${status.level}">${status.text}</span>
            <span>${status.detail}</span>
            <span>State ${piperJointTopicNames[side]}</span>
            <span>Action ${piperWriteActionTopics[side]}</span>
          </p>
        </div>
      </div>
      <div class="joint-compare-grid">
        ${jointRows}
        ${renderGripperCompareRow(side)}
      </div>
      <div class="action-feedback-note ${action && action.status === "error" ? "is-danger" : ""}">
        ${action && action.detail ? action.detail : "接管控制后拖动 Action 滑条。"}
      </div>
    </section>
  `;
}

function armActionInputIsActive() {
  const active = document.activeElement;
  return Boolean(active && active.matches && active.matches("#armCompareList [data-action-kind]"));
}

function renderArmActionFeedbackNotes() {
  ["left", "right"].forEach((side) => {
    const action = state.piperActions[side];
    const note = $(`[data-arm-panel="${side}"] .action-feedback-note`);
    if (!note) return;
    note.textContent = action && action.detail ? action.detail : "接管控制后拖动 Action 滑条。";
    note.classList.toggle("is-danger", Boolean(action && action.status === "error"));
  });
}

function renderArmComparisons(options = {}) {
  const node = $("#armCompareList");
  if (!node) return;
  renderArmCompareBadge();
  if (!options.force && armActionInputIsActive()) {
    renderArmActionFeedbackNotes();
    renderArmControlButtons();
    return;
  }
  node.innerHTML = `
    <div class="dual-arm-grid">
      ${renderArmComparison("left")}
      ${renderArmComparison("right")}
    </div>
  `;
  renderArmControlButtons();
}

function renderArmControlButtons() {
  const copyButton = $("#copyAllArmStateButton");
  if (copyButton) copyButton.disabled = !allArmStatesCopyable();
  const controlButton = $("#armControlToggleButton");
  if (controlButton) {
    controlButton.textContent = state.armControl.active ? "退出接管" : "接管控制";
    controlButton.disabled = state.armControl.busy || (!state.armControl.active && !piperReady());
    controlButton.classList.toggle("is-active", state.armControl.active);
  }
  const homeButton = $("#armHomeButton");
  if (homeButton) homeButton.disabled = state.armControl.busy;
  renderJointSpeedInput();
}

function renderJointSpeedInput() {
  const input = $("#jointSpeedInput");
  if (!input || document.activeElement === input) return;
  input.value = formatNumber(state.armControl.maxJointSpeedDegS, 1);
}

function updateJointSpeedFromInput(input, options = {}) {
  const speed = normalizeJointSpeedDegS(input.value);
  state.armControl.maxJointSpeedDegS = speed;
  input.value = formatNumber(speed, 1);
  if (options.publish !== false && state.armControl.active) {
    scheduleDirectArmPublish();
  }
  return speed;
}

function renderPlaybackJointSpeedInput() {
  const input = $("#playbackJointSpeedInput");
  if (!input || document.activeElement === input) return;
  input.value = formatNumber(state.playback.maxJointSpeedDegS, 1);
}

function updatePlaybackJointSpeedFromInput(input) {
  const speed = normalizeJointSpeedDegS(input.value, state.playback.maxJointSpeedDegS);
  state.playback.maxJointSpeedDegS = speed;
  input.value = formatNumber(speed, 1);
  return speed;
}

function updateArmActionPreview(input) {
  const row = input.closest(".action-value");
  if (!row) return;

  const kind = input.dataset.actionKind;
  const value = Number(input.value);
  const strong = row.querySelector("strong");
  const small = row.querySelector("small");
  if (!Number.isFinite(value)) return;

  if (kind === "joint") {
    const min = Number(input.min);
    const max = Number(input.max);
    const rad = (value * Math.PI) / 180;
    input.style.setProperty("--action-position", `${clamp(jointPercent(value, { min, max }), 0, 100)}%`);
    if (strong) strong.textContent = `${formatNumber(value, 2)} deg`;
    if (small) small.textContent = `${formatNumber(rad, 4)} rad`;
    return;
  }

  input.style.setProperty("--action-position", `${clamp(value * 1000, 0, 100)}%`);
  if (strong) strong.textContent = `${formatNumber(value, 4)} m`;
}

function updateArmActionFromInput(input, options = {}) {
  const side = input.dataset.actionSide === "right" ? "right" : "left";
  const action = state.piperActions[side];
  if (!action) return;
  seedActionFromState(side);

  const index = Number(input.dataset.actionIndex);
  if (!Number.isInteger(index) || index < 0 || index > 6) return;

  const value = Number(input.value);
  if (!Number.isFinite(value)) {
    action.positions[index] = null;
    action.status = "idle";
    action.detail = "Action 值未填写完整。";
    if (options.render !== false) renderArmComparisons();
    else renderArmActionFeedbackNotes();
    return;
  }

  action.positions[index] = input.dataset.actionKind === "joint" ? (value * Math.PI) / 180 : value;
  action.status = actionReady(side) ? "ready" : "idle";
  action.detail = actionReady(side) ? "Action 已就绪。" : "Action 值未填写完整。";
  if (options.render !== false) renderArmComparisons();
  else {
    updateArmActionPreview(input);
    renderArmActionFeedbackNotes();
  }
  if (state.armControl.active) {
    scheduleDirectArmPublish();
  }
}

async function publishArmActionsNow(options = {}) {
  const source = options.source || "接管控制";
  const logSuccess = options.logSuccess !== false;
  if (!allActionsReady()) {
    if (logSuccess) addLog("机械臂", `${source}未启动：左右臂 Action 参数未就绪`);
    renderArmComparisons();
    return null;
  }

  const speedInput = $("#jointSpeedInput");
  const maxJointSpeedDegS = speedInput ? updateJointSpeedFromInput(speedInput, { publish: false }) : state.armControl.maxJointSpeedDegS;
  const payload = {
    left: { positions: state.piperActions.left.positions.map((value) => Number(value)) },
    right: { positions: state.piperActions.right.positions.map((value) => Number(value)) },
    max_joint_speed_deg_s: maxJointSpeedDegS,
    gripper_effort: PIPER_GRIPPER_EFFORT,
  };

  ["left", "right"].forEach((side) => {
    const action = state.piperActions[side];
    action.status = "publishing";
    action.detail = `${piperArmLabels[side]} Action 下发中。`;
  });
  renderArmComparisons();

  try {
    const response = await fetchPiperControl("/api/control/piper/joint-targets", payload);
    const result = await response.json();
    if (!response.ok || !result.ok) {
      throw new Error(result.detail || `HTTP ${response.status}`);
    }
    const publishedAt = result.publishedAt || formatTime();
    ["left", "right"].forEach((side) => {
      const action = state.piperActions[side];
      action.status = "published";
      action.lastPublishedAt = publishedAt;
      action.detail = `${piperArmLabels[side]} Action 已下发 ${publishedAt}，${formatNumber(maxJointSpeedDegS, 1)} deg/s。`;
    });
    const topics = Array.isArray(result.topics) && result.topics.length ? result.topics.join(" / ") : "joint-targets";
    if (logSuccess) addLog("机械臂", `${source}完成：${topics}`);
    return result;
  } catch (error) {
    ["left", "right"].forEach((side) => {
      const action = state.piperActions[side];
      action.status = "error";
      action.detail = `${piperArmLabels[side]} Action 下发失败：${error.message}`;
    });
    addLog("机械臂", `${source}失败：${error.message}`);
    return null;
  } finally {
    renderArmComparisons();
  }
}

function scheduleDirectArmPublish() {
  window.clearTimeout(state.armControl.publishTimer);
  state.armControl.publishTimer = window.setTimeout(() => {
    if (!state.armControl.active) return;
    publishArmActionsNow({ source: "接管控制自动下发", logSuccess: false });
  }, ARM_ACTION_PUBLISH_DEBOUNCE_MS);
}

function sleepMs(ms) {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

function runBackgroundPoll(callback) {
  if (state.inference.looping) return;
  callback();
}

function resumeBackgroundPollsNow() {
  if (state.inference.looping) return;
  window.clearTimeout(state.backgroundPollResumeTimer);
  state.backgroundPollResumeTimer = window.setTimeout(() => {
    if (state.inference.looping) return;
    refreshInferenceStatus();
    fetchPiperRuntimeStatus({ silent: true });
    fetchLiftingRuntimeStatus({ silent: true });
    fetchChassisRuntimeStatus({ silent: true });
    fetchCameraRuntimeStatus({ silent: true });
    if (state.cameraFrames.previewEnabled) fetchCameraFrames({ silent: true });
    fetchLidarRuntimeStatus({ silent: true });
    if (state.lidarCloud.previewEnabled) fetchLidarCloudStatus({ silent: true });
    fetchLiftingMotorState();
    fetchChassisState({ silent: true });
    fetchPiperJointStates();
  }, 50);
}

async function publishPiperEnable(enabled, options = {}) {
  const repeat = Math.max(1, Number(options.repeat) || 1);
  const intervalMs = Math.max(0, Number(options.intervalMs) || 0);
  let result = null;
  for (let index = 0; index < repeat; index += 1) {
    const response = await fetch(`/api/ros/actions/${piperEnableActionKey}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled }),
    });
    result = await response.json();
    if (!response.ok || !result.ok) {
      throw new Error(result.detail || `HTTP ${response.status}`);
    }
    if (index < repeat - 1 && intervalMs) {
      await sleepMs(intervalMs);
    }
  }
  return result;
}

function requestPiperJointHold(reason = "停止") {
  fetchPiperControl("/api/control/piper/joint-targets", { hold: true })
    .then(async (response) => {
      const result = await response.json();
      if (!response.ok || !result.ok) {
        throw new Error(result.detail || `HTTP ${response.status}`);
      }
      addLog("机械臂", `${reason}：已请求关节 smoother 保持当前位置`);
    })
    .catch((error) => addLog("机械臂", `${reason}：关节 smoother hold 请求失败：${error.message}`));
}

async function toggleArmDirectControl() {
  if (state.armControl.busy) return;
  if (!state.armControl.active && !piperReady()) {
    addLog("机械臂", "接管控制未启动：Piper 控制节点未运行");
    renderArmComparisons();
    return;
  }

  state.armControl.busy = true;
  renderArmControlButtons();
  try {
    if (state.armControl.active) {
      window.clearTimeout(state.armControl.publishTimer);
      state.armControl.active = false;
      addLog("机械臂", "已退出接管控制，机械臂保持使能");
    } else {
      if (!allArmStatesCopyable()) {
        ["left", "right"].forEach((side) => {
          const action = state.piperActions[side];
          if (!action || canCopyStateToAction(side)) return;
          action.status = "idle";
          action.detail = `${piperArmLabels[side]} State 暂不可复制。`;
        });
        throw new Error("左右臂 State 反馈未全部就绪");
      }
      ["left", "right"].forEach((side) => {
        const action = state.piperActions[side];
        const feedback = state.piperJoints[side];
        action.positions = feedback.positions.slice(0, 7).map((value) => Number(value));
        action.status = "ready";
        action.detail = "接管前已自动复制 State 到 Action。";
      });
      if (!allActionsReady()) {
        throw new Error("左右臂 Action 参数未就绪");
      }
      await publishPiperEnable(true, { repeat: 3, intervalMs: 80 });
      $("#enableStatus").textContent = "已使能";
      $("#enableStatus").className = "status-pill ok";
      state.armControl.active = true;
      addLog("机械臂", "已接管控制：已复制 State，拖动 Action 滑条将自动下发");
    }
  } catch (error) {
    addLog("机械臂", `接管控制切换失败：${error.message}`);
  } finally {
    state.armControl.busy = false;
    renderArmComparisons();
  }
}

function nestedValue(source, path) {
  return path.reduce((current, key) => (current && current[key] !== undefined ? current[key] : undefined), source);
}

function nestedNumber(source, path) {
  const value = Number(nestedValue(source, path));
  return Number.isFinite(value) ? value : null;
}

function chassisMotionModeText(mode) {
  const key = Number(mode);
  return chassisMotionModeLabels[key] || "--";
}

function chassisFeedbackLevel() {
  if (state.chassisState.ok) return feedbackLatencyMeta(state.chassisState, { ready: chassisReady() }).level;
  if (state.chassisState.code === "ROS-R-WAITING") return "idle";
  if (state.chassisState.code === "ROS-R-NODATA") return "warn";
  return chassisReady() ? "danger" : "idle";
}

function chassisFeedbackMeta() {
  return feedbackLatencyMeta(state.chassisState, {
    ready: chassisReady(),
    stoppedText: "未启动",
    waitingText: "等待",
  });
}

function renderDeviceBaseMetrics() {
  const node = $("#deviceBaseMetrics");
  if (!node) return;
  const valueFor = (key) => deviceBaseControlItems.find((entry) => entry.key === key);
  const linear = valueFor("linear");
  const lateral = valueFor("lateral");
  const angular = valueFor("angular");
  const command = state.chassisControl.command || { linearX: 0, linearY: 0, angularZ: 0 };
  const system = state.chassisState.system || {};
  const battery = state.chassisState.battery || {};
  const odom = state.chassisState.odom || {};
  const feedbackLinear = nestedNumber(odom, ["twist", "twist", "linear", "x"]);
  const feedbackLateral = nestedNumber(odom, ["twist", "twist", "linear", "y"]);
  const feedbackAngular = nestedNumber(odom, ["twist", "twist", "angular", "z"]);
  const systemVoltage = Number(system.battery_voltage);
  const bmsVoltage = Number(battery.voltage);
  const voltage = Number.isFinite(bmsVoltage) ? bmsVoltage : systemVoltage;
  const motionMode = system.motion_mode !== undefined ? system.motion_mode : state.chassisState.motion?.motion_mode;
  const feedbackMeta = chassisFeedbackMeta();
  const feedbackLevel = feedbackMeta.level;
  const odomText = state.chassisState.odom
    ? feedbackMeta.inlineText
    : "未接入";
  const serviceExternal = state.chassisRuntime.status === "external";
  const serviceText = serviceExternal ? "外部运行" : chassisReady() ? "运行中" : "未启动";
  const serviceLevel = serviceExternal ? "warn" : chassisReady() ? "ok" : "idle";
  setStatusText("#baseControlText", serviceText, serviceLevel);
  setStatusText("#baseOdomText", odomText, state.chassisState.odom ? feedbackLevel : "idle");
  $$("[data-device-drive], [data-mapping-drive]").forEach((button) => {
    const action = button.dataset.deviceDrive || button.dataset.mappingDrive;
    button.disabled = !chassisReady() && action !== "stop";
  });
  renderChassisKeyboardControl();
  node.innerHTML = [
    ["指令", `${command.linearX.toFixed(2)} / ${command.linearY.toFixed(2)} m/s`],
    ["旋转", `${command.angularZ.toFixed(2)} ${angular.commandUnit}`],
    ["反馈", feedbackLinear === null ? "--" : `${feedbackLinear.toFixed(2)} / ${(feedbackLateral || 0).toFixed(2)} m/s`],
    ["模式", chassisMotionModeText(motionMode)],
    ["角速", feedbackAngular === null ? "--" : `${feedbackAngular.toFixed(2)} rad/s`],
    ["电压", Number.isFinite(voltage) ? `${voltage.toFixed(1)} V` : "--"],
  ]
    .map(([name, value]) => `<div class="metric-card"><span>${name}</span><strong>${value}</strong></div>`)
    .join("");
  renderBaseOdomReadout(odom);
  renderRobotViewStatus();
}

function renderBaseOdomReadout(odom = state.chassisState.odom || {}) {
  const readout = $("#baseOdomReadout");
  if (!readout) return;
  const hasOdom = Boolean(state.chassisState.odom);
  const posX = nestedNumber(odom, ["pose", "pose", "position", "x"]);
  const posY = nestedNumber(odom, ["pose", "pose", "position", "y"]);
  const yaw = yawFromOdom(odom);
  const distance = posX === null || posY === null ? null : Math.hypot(posX, posY);
  readout.classList.toggle("is-live", hasOdom);
  const setText = (selector, value) => {
    const el = $(selector);
    if (el) el.textContent = value;
  };
  setText("#baseOdomPosX", posX === null ? "--" : posX.toFixed(2));
  setText("#baseOdomPosY", posY === null ? "--" : posY.toFixed(2));
  setText("#baseOdomYaw", yaw === null ? "--" : radToDeg(yaw).toFixed(1));
  setText("#baseOdomDist", distance === null ? "--" : distance.toFixed(2));
  renderBaseOdomResetButton();
}

function renderBaseOdomResetButton() {
  const button = $("#baseOdomResetButton");
  if (!button) return;
  const busy = state.chassisControl.resettingOdom;
  const ready = chassisReady();
  button.disabled = busy || !ready;
  button.classList.toggle("is-busy", busy);
  button.textContent = busy ? "归零中" : "归零";
  button.title = ready ? "将 ROS /odom 重置为 0" : "Chassis 服务未运行，无法重置 /odom";
}

function liftPercent(height = state.liftPreview.height) {
  const limits = state.liftingState.limits || {};
  const minHeight = Number.isFinite(Number(limits.minHeightM)) ? Number(limits.minHeightM) : liftPreviewLimits.min;
  const maxHeight = Number.isFinite(Number(limits.maxHeightM)) ? Number(limits.maxHeightM) : liftPreviewLimits.max;
  const range = Math.max(0.001, maxHeight - minHeight);
  return clamp(((height - minHeight) / range) * 100, 0, 100);
}

function setStatusText(selector, text, level) {
  const node = $(selector);
  if (!node) return;
  node.textContent = text;
  node.className = `status-text ${level}`;
}

function liftingFeedbackLevel() {
  if (state.liftingState.ok) return feedbackLatencyMeta(state.liftingState, { ready: liftingReady() }).level;
  if (state.liftingState.code === "ROS-R-WAITING") return "idle";
  if (state.liftingState.code === "ROS-R-NODATA") return "warn";
  return liftingReady() ? "danger" : "idle";
}

function liftingFeedbackMeta() {
  return feedbackLatencyMeta(state.liftingState, {
    ready: liftingReady(),
    stoppedText: "未启动",
    waitingText: "等待",
  });
}

function robotAgeText(ageMs) {
  const parsed = Number(ageMs);
  if (!Number.isFinite(parsed)) return "--";
  if (parsed < 1000) return `${Math.max(0, Math.round(parsed))} ms`;
  return `${(parsed / 1000).toFixed(1)} s`;
}

function yawFromOdom(odom) {
  const x = nestedNumber(odom, ["pose", "pose", "orientation", "x"]);
  const y = nestedNumber(odom, ["pose", "pose", "orientation", "y"]);
  const z = nestedNumber(odom, ["pose", "pose", "orientation", "z"]);
  const w = nestedNumber(odom, ["pose", "pose", "orientation", "w"]);
  if ([x, y, z, w].some((value) => value === null)) return null;
  return Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z));
}

function mappingFinalTransform(session = state.mapping.session) {
  const transform = session?.lastResult?.registration?.finalTransform;
  if (!Array.isArray(transform) || transform.length !== 16) return null;
  const values = transform.map((value) => Number(value));
  return values.every(Number.isFinite) ? values : null;
}

function mappingPoseFromTransform(transform = mappingFinalTransform()) {
  if (!transform) return null;
  return {
    x: transform[3],
    y: transform[7],
    z: transform[11],
    yaw: Math.atan2(transform[4], transform[0]),
  };
}

function mappingMapRevision(session = state.mapping.session) {
  if (!session?.tmpMapPath) return "";
  const keyframes = Array.isArray(session.keyframes) ? session.keyframes : [];
  if (!keyframes.length && !session.lastResult?.mapPath) return "";
  const registration = session.lastResult?.registration || {};
  return [
    session.id || "",
    Number(session.captureCount) || keyframes.length,
    registration.mapPoints || "",
    session.lastResult?.mapPath || session.tmpMapPath || "",
    session.updatedAt || "",
  ].join(":");
}

function mappingMapVisible() {
  return Boolean(state.mapping.mapPreview.hasFrame);
}

function localizationViewActive() {
  return document.body.dataset.activeView === "localization";
}

function localizationMapVisible() {
  return localizationViewActive() && Boolean(state.localization.mapPreview.hasFrame);
}

function robotJointDeg(side, index, fallback = 0) {
  const value = stateValueFor(state.piperJoints[side], index);
  return Number.isFinite(value) ? radToDeg(value) : fallback;
}

function renderRobotViewFigure() {
  const stage = $("#robotViewStage");
  if (!stage) return;
  if (!state.robotModel.poseSyncEnabled) {
    ["--lift-position", "--base-yaw", "--left-shoulder", "--right-shoulder", "--left-elbow", "--right-elbow"].forEach((property) => {
      stage.style.removeProperty(property);
    });
    return;
  }
  const actualHeight = Number(state.liftingState.heightM);
  const heightForFigure = Number.isFinite(actualHeight) ? actualHeight : state.liftPreview.height;
  const liftPosition = 34 + liftPercent(heightForFigure) * 0.36;
  const yaw = yawFromOdom(state.chassisState.odom || {});
  stage.style.setProperty("--lift-position", `${liftPosition.toFixed(1)}%`);
  if (yaw !== null) stage.style.setProperty("--base-yaw", `${yaw}rad`);
  stage.style.setProperty("--left-shoulder", `${clamp(-18 + robotJointDeg("left", 0), -58, 42)}deg`);
  stage.style.setProperty("--right-shoulder", `${clamp(18 + robotJointDeg("right", 0), -42, 58)}deg`);
  stage.style.setProperty("--left-elbow", `${clamp(-10 - robotJointDeg("left", 1) * 0.35, -50, 30)}deg`);
  stage.style.setProperty("--right-elbow", `${clamp(10 + robotJointDeg("right", 1) * 0.35, -30, 50)}deg`);
}

function robotModelStatusMeta() {
  const robot = state.robotModel;
  if (robot.status === "fetching") return { text: "查询模型", level: "warn" };
  if (robot.status === "loading") return { text: "加载中", level: "warn" };
  if (robot.status === "ready") return { text: "模型已加载", level: "ok" };
  if (robot.status === "error") return { text: "加载失败", level: "danger" };
  if (robot.models.length) return { text: "可加载", level: "idle" };
  return { text: "模型待接入", level: "idle" };
}

function robotAssetName(filename) {
  return String(filename || "")
    .split(/[\\/]/)
    .filter(Boolean)
    .pop() || "mesh";
}

function renderRobotLoadProgress() {
  const progress = state.robotModel.progress;
  const node = $("#robotLoadProgress");
  if (!node || !progress) return;
  const value = clamp(Number(progress.value) || 0, 0, 100);
  node.setAttribute("aria-valuenow", String(Math.round(value)));
  node.classList.toggle("is-active", Boolean(progress.active));
  node.classList.toggle("is-error", progress.level === "danger");

  const text = $("#robotLoadProgressText");
  if (text) text.textContent = progress.label || "等待加载";
  const percent = $("#robotLoadProgressValue");
  if (percent) percent.textContent = `${Math.round(value)}%`;
  const bar = $("#robotLoadProgressBar");
  if (bar) bar.style.width = `${value}%`;
  const detail = $("#robotLoadProgressDetail");
  if (detail) detail.textContent = progress.detail || "选择模型后点击加载";
}

function setRobotLoadProgress(patch = {}) {
  state.robotModel.progress = {
    ...state.robotModel.progress,
    ...patch,
  };
  renderRobotLoadProgress();
}

function robotFeedbackSyncMeta() {
  const liveLevels = [armStatusText("left").level, armStatusText("right").level, chassisFeedbackLevel(), liftingFeedbackLevel()];
  const okCount = liveLevels.filter((level) => level === "ok").length;
  const warnCount = liveLevels.filter((level) => level === "warn").length;
  const dangerCount = liveLevels.filter((level) => level === "danger").length;
  const level = dangerCount ? "danger" : okCount === liveLevels.length ? "ok" : okCount || warnCount ? "warn" : "idle";
  return {
    level,
    text: level === "ok" ? "反馈同步" : level === "warn" ? "部分反馈" : level === "danger" ? "反馈超时" : "等待反馈",
  };
}

function robotPoseSyncButtonMeta() {
  const robot = state.robotModel;
  const busy = robot.status === "fetching" || robot.status === "loading";
  const active = Boolean(robot.poseSyncEnabled && robot.hasModel);
  const feedback = robotFeedbackSyncMeta();
  if (!robot.hasModel) {
    return {
      active: false,
      disabled: true,
      text: busy ? "加载中" : "姿态同步",
      title: "请先加载整机模型",
    };
  }
  return {
    active,
    disabled: busy,
    text: active ? (feedback.level === "ok" ? "同步中" : feedback.level === "warn" ? "部分同步" : "等待 State") : "姿态同步",
    title: active ? "关闭后整机模型保持当前姿态" : "开启后整机模型跟随 State 姿态",
  };
}

function renderRobotPoseSyncButton() {
  const button = $("#robotPoseSyncButton");
  if (!button) return;
  const meta = robotPoseSyncButtonMeta();
  button.disabled = meta.disabled;
  button.textContent = meta.text;
  button.title = meta.title;
  button.classList.toggle("is-active", meta.active);
  button.setAttribute("aria-pressed", meta.active ? "true" : "false");
}

function robotLidarFrameName() {
  const frames = state.robotModel.metadata?.frames || {};
  return frames.lidar || "rslidar";
}

function normalizedFrameName(value) {
  return String(value || "").replace(/^\/+/, "");
}

function robotLidarFrameMatches(frameName = state.robotModel.lidarOverlay.lastFrameId || "") {
  const frameId = normalizedFrameName(frameName);
  if (!frameId) return true;
  const target = normalizedFrameName(robotLidarFrameName());
  return frameId === target || (frameId === "rslidar" && target === "lidar_link") || (frameId === "lidar_link" && target === "rslidar");
}

function robotLidarButtonMeta() {
  const robot = state.robotModel;
  const overlay = robot.lidarOverlay;
  const busy = robot.status === "fetching" || robot.status === "loading";
  if (!robot.hasModel) {
    return {
      text: busy ? "加载中" : "LiDAR",
      title: busy ? "整机模型加载中" : "点击后先加载整机模型，再显示 LiDAR 点云",
      disabled: busy || !robot.selectedKey,
      active: false,
      level: busy ? "warn" : "idle",
    };
  }
  if (busy) {
    return { text: "LiDAR", title: "整机模型加载中", disabled: true, active: overlay.enabled, level: "warn" };
  }
  if (mappingMapVisible()) {
    return {
      text: "LiDAR 已暂停",
      title: "累计地图显示中，实时 LiDAR 叠加层已暂停",
      disabled: true,
      active: false,
      level: "idle",
    };
  }
  if (overlay.enabled && overlay.error) {
    return {
      text: "LiDAR 无数据",
      title: overlay.error,
      disabled: false,
      active: true,
      level: "warn",
    };
  }
  if (overlay.enabled && overlay.lastFrameId && !robotLidarFrameMatches()) {
    return {
      text: "Frame 不匹配",
      title: `点云 frame=${overlay.lastFrameId || "--"}，模型 frame=${robotLidarFrameName()}`,
      disabled: false,
      active: true,
      level: "warn",
    };
  }
  if (overlay.enabled) {
    return {
      text: overlay.lastFrameId ? "LiDAR 显示中" : "等待 LiDAR",
      title: `点云挂载到 ${robotLidarFrameName()}`,
      disabled: false,
      active: true,
      level: overlay.lastFrameId ? "ok" : "warn",
    };
  }
  return { text: "LiDAR", title: "在整机视图显示点云", disabled: false, active: false, level: "idle" };
}

function renderRobotLidarButton() {
  const button = $("#robotLidarToggleButton");
  if (!button) return;
  const meta = robotLidarButtonMeta();
  button.disabled = meta.disabled;
  button.textContent = meta.text;
  button.title = meta.title;
  button.classList.toggle("is-active", meta.active);
  button.classList.toggle("is-warn", meta.level === "warn");
  button.classList.toggle("is-danger", meta.level === "danger");
  button.setAttribute("aria-pressed", meta.active ? "true" : "false");
}

function findRobotFrameObject(frameName) {
  const robot = state.robotModel;
  if (!robot.modelRoot || !frameName) return null;
  const link = robot.modelRoot.links?.[frameName];
  if (link) return link;
  const exact = robot.modelRoot.getObjectByName(frameName);
  if (exact) return exact;
  let found = null;
  robot.modelRoot.traverse((object) => {
    if (!found && (object.name === frameName || object.userData?.name === frameName || object.userData?.urdfName === frameName)) {
      found = object;
    }
  });
  return found;
}

function ensureRobotLidarOverlay() {
  const robot = state.robotModel;
  const overlay = robot.lidarOverlay;
  if (mappingMapVisible()) {
    overlay.error = "累计地图显示中";
    if (overlay.points) overlay.points.visible = false;
    renderRobotLidarButton();
    return false;
  }
  if (!robot.hasModel || !robot.three || !robot.modelRoot) {
    overlay.error = "请先加载整机模型";
    renderRobotLidarButton();
    return false;
  }

  const frameName = robotLidarFrameName();
  const frameObject = findRobotFrameObject(frameName) || findRobotFrameObject("rslidar") || findRobotFrameObject("lidar_link");
  if (!frameObject) {
    overlay.error = `URDF 中未找到 LiDAR frame: ${frameName}`;
    renderRobotLidarButton();
    return false;
  }

  if (!overlay.points) {
    const THREE = robot.three;
    overlay.geometry = new THREE.BufferGeometry();
    overlay.material = new THREE.PointsMaterial({
      size: lidarPointRadiusToMaterialSize(state.lidarCloud.pointRadius),
      map: createLidarPointTexture(THREE),
      vertexColors: true,
      sizeAttenuation: true,
      transparent: true,
      alphaTest: 0.12,
      opacity: 0.92,
      depthWrite: false,
    });
    overlay.points = new THREE.Points(overlay.geometry, overlay.material);
    overlay.points.name = "robot_lidar_point_cloud";
    overlay.points.frustumCulled = false;
  }

  if (overlay.points.parent !== frameObject) {
    frameObject.add(overlay.points);
  }
  overlay.frameObject = frameObject;
  overlay.error = "";
  overlay.points.visible = overlay.enabled;
  renderRobotLidarButton();
  return true;
}

async function setRobotLidarOverlayEnabled(enabled) {
  const overlay = state.robotModel.lidarOverlay;
  if (enabled && mappingMapVisible()) {
    overlay.enabled = false;
    overlay.error = "累计地图显示中";
    if (overlay.points) overlay.points.visible = false;
    renderRobotLidarButton();
    addLog("模型", "累计地图显示中，实时 LiDAR 点云叠加已暂停");
    return false;
  }
  overlay.enabled = Boolean(enabled);
  overlay.error = "";
  renderRobotLidarButton();
  if (overlay.enabled) {
    if (!state.robotModel.hasModel) {
      addLog("模型", "正在加载整机模型以显示 LiDAR 点云");
      const model = await loadRobotModel();
      if (!model) {
        overlay.enabled = false;
        overlay.error = "整机模型加载失败";
        renderRobotLidarButton();
        return false;
      }
    }
    if (!ensureRobotLidarOverlay()) {
      overlay.enabled = false;
      renderRobotLidarButton();
      return false;
    }
    requestRobotLidarFrame();
    addLog("模型", `整机 LiDAR 点云已显示：${robotLidarFrameName()}`);
  } else {
    if (overlay.points) overlay.points.visible = false;
    window.clearTimeout(overlay.frameTimer);
    addLog("模型", "整机 LiDAR 点云已隐藏");
  }
  renderRobotViewStatus();
  return overlay.enabled;
}

function toggleRobotLidarOverlay() {
  setRobotLidarOverlayEnabled(!state.robotModel.lidarOverlay.enabled);
}

function pauseRobotLidarOverlayForMappingMap() {
  const overlay = state.robotModel.lidarOverlay;
  window.clearTimeout(overlay.frameTimer);
  overlay.enabled = false;
  overlay.error = "累计地图显示中";
  if (overlay.points) overlay.points.visible = false;
  renderRobotLidarButton();
}

function robotMeshProgressValue() {
  const progress = state.robotModel.progress;
  const total = Math.max(0, Number(progress.meshTotal) || 0);
  const loaded = clamp(Number(progress.meshLoaded) || 0, 0, total || 0);
  if (!total) return 90;
  return 42 + (loaded / total) * 50;
}

function createRobotMeshProgress(totalMeshes) {
  setRobotLoadProgress({
    active: true,
    value: totalMeshes ? 42 : 90,
    label: totalMeshes ? `加载 mesh 0/${totalMeshes}` : "URDF 无 mesh 资源",
    detail: totalMeshes ? "准备读取几何资源" : "准备生成关节结构",
    level: "warn",
    meshLoaded: 0,
    meshTotal: totalMeshes,
  });
  return {
    note(filename, event) {
      const loaded = Number(event?.loaded);
      const total = Number(event?.total);
      const percent = Number.isFinite(loaded) && Number.isFinite(total) && total > 0 ? ` ${Math.round((loaded / total) * 100)}%` : "";
      setRobotLoadProgress({
        value: Math.max(state.robotModel.progress.value, robotMeshProgressValue()),
        label: `加载 mesh ${state.robotModel.progress.meshLoaded + 1}/${state.robotModel.progress.meshTotal}`,
        detail: `${robotAssetName(filename)}${percent}`,
      });
    },
    done(filename) {
      const total = Math.max(0, Number(state.robotModel.progress.meshTotal) || 0);
      const nextLoaded = Math.min(total, state.robotModel.progress.meshLoaded + 1);
      setRobotLoadProgress({
        value: total ? 42 + (nextLoaded / total) * 50 : 90,
        label: `加载 mesh ${nextLoaded}/${total}`,
        detail: `${robotAssetName(filename)} 已解析`,
        meshLoaded: nextLoaded,
      });
    },
  };
}

function setRobotModelStatus(status, detail = "") {
  state.robotModel.status = status;
  state.robotModel.detail = detail || state.robotModel.detail;
  state.robotModel.error = status === "error" ? state.robotModel.detail : "";
  renderRobotModelControls();
  renderRobotViewStatus();
  renderRobotLoadProgress();
}

function renderRobotModelControls() {
  const robot = state.robotModel;
  const select = $("#robotModelSelect");
  if (select) {
    const options = robot.models.length
      ? robot.models
          .map((model) => `<option value="${escapeHtml(model.key)}">${escapeHtml(model.name || model.key)}</option>`)
          .join("")
      : `<option value="">暂无模型</option>`;
    if (select.dataset.options !== options) {
      select.innerHTML = options;
      select.dataset.options = options;
    }
    select.value = robot.selectedKey || "";
    select.disabled = robot.status === "fetching" || robot.status === "loading" || robot.models.length === 0;
  }

  const button = $("#robotModelLoadButton");
  if (button) {
    button.disabled = !robot.selectedKey || robot.status === "fetching" || robot.status === "loading";
    button.textContent = robot.status === "loading" ? "加载中" : "加载";
  }
  renderRobotPoseSyncButton();
  renderRobotLidarButton();
}

async function fetchRobotModels(options = {}) {
  if (state.robotModel.status === "fetching") return null;
  if (!state.robotModel.hasModel) setRobotModelStatus("fetching", "正在读取模型清单");
  try {
    const response = await fetch("/api/robot-models", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !payload.ok || !Array.isArray(payload.models)) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    state.robotModel.models = payload.models;
    if (!state.robotModel.selectedKey && payload.models.length) {
      state.robotModel.selectedKey = payload.models[0].key;
    }
    const selected = payload.models.find((model) => model.key === state.robotModel.selectedKey) || payload.models[0];
    if (selected) state.robotModel.selectedKey = selected.key;
    const loadedName = state.robotModel.metadata?.name || state.robotModel.loadedKey;
    const detail = state.robotModel.hasModel
      ? `${loadedName || selected?.name || selected?.key} 已加载到整机视图`
      : selected
        ? `已发现 ${selected.name || selected.key}，点击加载显示 URDF`
        : "未发现可用模型";
    setRobotModelStatus(state.robotModel.hasModel ? "ready" : "available", detail);
    return payload;
  } catch (error) {
    setRobotModelStatus("error", `模型清单读取失败：${error.message}`);
    if (!options.silent) addLog("模型", `模型清单读取失败：${error.message}`);
    return null;
  }
}

function robotViewerStage() {
  if (localizationViewActive()) {
    return $("#localizationViewStage") || $("#robotViewStage");
  }
  return $("#robotViewStage") || $("#localizationViewStage");
}

function syncRobotViewerMount() {
  const robot = state.robotModel;
  const container = robotViewerStage();
  if (!container || !robot.renderer) return false;
  if (robot.renderer.domElement.parentElement !== container) {
    container.appendChild(robot.renderer.domElement);
  }
  return true;
}

function syncRobotViewerLayersForView() {
  const mappingPreview = state.mapping.mapPreview;
  if (mappingPreview.points) {
    mappingPreview.points.visible = !localizationViewActive() && Boolean(mappingPreview.hasFrame);
  }
  const localizationPreview = state.localization.mapPreview;
  if (localizationPreview.points) {
    localizationPreview.points.visible = localizationMapVisible();
  }
}

function updateRobotCamera() {
  const robot = state.robotModel;
  if (!robot.camera || !robot.controls) return;
  const controls = robot.controls;
  const horizontal = controls.distance * Math.cos(controls.pitch);
  robot.camera.position.set(
    controls.target.x + horizontal * Math.cos(controls.yaw),
    controls.target.y + horizontal * Math.sin(controls.yaw),
    controls.target.z + controls.distance * Math.sin(controls.pitch),
  );
  robot.camera.lookAt(controls.target);
}

function resizeRobotViewer() {
  const robot = state.robotModel;
  const container = robotViewerStage();
  syncRobotViewerMount();
  if (!container || !robot.renderer || !robot.camera) return;
  const rect = container.getBoundingClientRect();
  const width = Math.floor(rect.width);
  const height = Math.floor(rect.height);
  if (width <= 0 || height <= 0) return;
  robot.camera.aspect = width / height;
  robot.camera.updateProjectionMatrix();
  robot.renderer.setSize(width, height, false);
}

function viewerDragMode(event) {
  return event.shiftKey || event.button === 1 || event.button === 2 ? "pan" : "rotate";
}

function panViewerTarget(camera, controls, surface, dx, dy) {
  if (!camera || !controls?.target || !surface) return;
  const rect = surface.getBoundingClientRect();
  const height = Math.max(rect.height, 1);
  const fovRad = ((Number(camera.fov) || 58) * Math.PI) / 180;
  const panScale = (2 * controls.distance * Math.tan(fovRad / 2)) / height;
  camera.updateMatrixWorld();
  const right = camera.position.clone().setFromMatrixColumn(camera.matrixWorld, 0).normalize();
  const up = camera.position.clone().setFromMatrixColumn(camera.matrixWorld, 1).normalize();
  controls.target.addScaledVector(right, -dx * panScale);
  controls.target.addScaledVector(up, dy * panScale);
}

function bindRobotViewerControls(surface) {
  const controls = state.robotModel.controls;
  if (!surface || !controls) return;

  surface.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    controls.dragging = true;
    controls.dragMode = viewerDragMode(event);
    controls.lastX = event.clientX;
    controls.lastY = event.clientY;
    surface.setPointerCapture(event.pointerId);
  });

  surface.addEventListener("pointermove", (event) => {
    if (!controls.dragging) return;
    const dx = event.clientX - controls.lastX;
    const dy = event.clientY - controls.lastY;
    controls.lastX = event.clientX;
    controls.lastY = event.clientY;
    if (controls.dragMode === "pan") {
      panViewerTarget(state.robotModel.camera, controls, surface, dx, dy);
    } else {
      controls.yaw -= dx * 0.006;
      controls.pitch = clamp(controls.pitch + dy * 0.006, -1.1, 1.25);
    }
    updateRobotCamera();
  });

  const release = (event) => {
    controls.dragging = false;
    controls.dragMode = "rotate";
    if (surface.hasPointerCapture(event.pointerId)) {
      surface.releasePointerCapture(event.pointerId);
    }
  };
  surface.addEventListener("pointerup", release);
  surface.addEventListener("pointercancel", release);
  surface.addEventListener("contextmenu", (event) => event.preventDefault());
  surface.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      controls.distance = clamp(controls.distance * (event.deltaY > 0 ? 1.1 : 0.9), 1.2, 80);
      updateRobotCamera();
    },
    { passive: false },
  );
}

async function initializeRobotViewer() {
  const robot = state.robotModel;
  if (robot.initialized) {
    syncRobotViewerMount();
    syncRobotViewerLayersForView();
    resizeRobotViewer();
    return true;
  }
  if (robot.initPromise) return robot.initPromise;

  robot.initPromise = loadThreeLoaders()
    .then(({ THREE }) => {
      const container = robotViewerStage();
      if (!container) return false;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x09111f);

      const camera = new THREE.PerspectiveCamera(58, 1, 0.01, 5000);
      camera.up.set(0, 0, 1);

      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setClearColor(0x09111f, 1);
      if (THREE.SRGBColorSpace) renderer.outputColorSpace = THREE.SRGBColorSpace;

      const oldCanvas = container.querySelector("canvas");
      if (oldCanvas) oldCanvas.remove();
      container.appendChild(renderer.domElement);

      const displayRoot = new THREE.Group();
      scene.add(displayRoot);

      const grid = new THREE.GridHelper(12, 24, 0x64748b, 0x1e293b);
      grid.rotation.x = Math.PI / 2;
      scene.add(grid);
      scene.add(new THREE.AxesHelper(1.2));

      const ambient = new THREE.AmbientLight(0xffffff, 1.4);
      scene.add(ambient);
      const keyLight = new THREE.DirectionalLight(0xffffff, 2.0);
      keyLight.position.set(3.5, -4, 6);
      scene.add(keyLight);
      const fillLight = new THREE.DirectionalLight(0xc7d2fe, 0.8);
      fillLight.position.set(-4, 3, 3);
      scene.add(fillLight);

      robot.three = THREE;
      robot.scene = scene;
      robot.camera = camera;
      robot.renderer = renderer;
      robot.displayRoot = displayRoot;
      robot.controls = {
        yaw: -2.35,
        pitch: 0.52,
        distance: 7.2,
        target: new THREE.Vector3(0, 0, 0),
        dragging: false,
        dragMode: "rotate",
        lastX: 0,
        lastY: 0,
      };

      bindRobotViewerControls(renderer.domElement);
      robot.resizeObserver = new ResizeObserver(resizeRobotViewer);
      ["#robotViewStage", "#localizationViewStage"].forEach((selector) => {
        const stage = $(selector);
        if (stage) robot.resizeObserver.observe(stage);
      });
      window.addEventListener("resize", resizeRobotViewer);

      const animate = () => {
        robot.animationFrame = window.requestAnimationFrame(animate);
        renderer.render(scene, camera);
      };

      updateRobotCamera();
      resizeRobotViewer();
      animate();
      robot.initialized = true;
      return true;
    })
    .catch((error) => {
      setRobotModelStatus("error", `3D 引擎加载失败：${error.message}`);
      return false;
    });

  return robot.initPromise;
}

function parseRobotUrdfXml(urdfText) {
  const documentXml = new DOMParser().parseFromString(urdfText, "application/xml");
  const parseError = documentXml.querySelector("parsererror");
  if (parseError) throw new Error("URDF XML 解析失败");
  if (!documentXml.querySelector("robot")) throw new Error("URDF 缺少 robot 根节点");
  return documentXml;
}

function countRobotMeshReferences(documentXml) {
  return Array.from(documentXml.querySelectorAll("link > visual > geometry > mesh, link > collision > geometry > mesh")).length;
}

function robotAssetUrl(path) {
  try {
    return new URL(path, window.location.href).toString();
  } catch (error) {
    return path;
  }
}

function robotAssetExtension(path) {
  const cleanPath = String(path || "").split(/[?#]/, 1)[0];
  return cleanPath.includes(".") ? cleanPath.split(".").pop().toLowerCase() : "";
}

function loadWithThreeLoader(loader, url, onProgress) {
  return new Promise((resolve, reject) => {
    loader.load(url, resolve, onProgress, reject);
  });
}

function cloneRobotMeshObject(object) {
  return object.clone(true);
}

function cachedRobotMeshLoad(loaders, url, extension, onProgress) {
  const cacheKey = `${extension}:${url}`;
  const cache = state.robotModel.meshCache;
  let entry = cache.get(cacheKey);
  if (!entry) {
    entry = { promise: null };
    entry.promise = (async () => {
      if (extension === "dae") {
        const collada = await loadWithThreeLoader(loaders.colladaLoader, url, onProgress);
        return collada.scene;
      }
      if (extension === "stl") {
        const geometry = await loadWithThreeLoader(loaders.stlLoader, url, onProgress);
        return new loaders.THREE.Mesh(geometry, new loaders.THREE.MeshPhongMaterial());
      }
      throw new Error(`不支持的 mesh 格式：${robotAssetName(url)}`);
    })()
      .catch((error) => {
        if (cache.get(cacheKey) === entry) cache.delete(cacheKey);
        throw error;
      });
    cache.set(cacheKey, entry);
  }
  return entry.promise.then(cloneRobotMeshObject);
}

function robotObjectHasAncestor(object, predicate) {
  let current = object;
  while (current) {
    if (predicate(current)) return true;
    current = current.parent;
  }
  return false;
}

function prepareRobotViewerObject(THREE, object) {
  const colliders = [];
  object.traverse((child) => {
    if (child.isURDFCollider) {
      child.visible = false;
      child.userData.robotModelRole = "collision";
      colliders.push(child);
    }
    if (!child.isMesh) return;
    if (robotObjectHasAncestor(child, (node) => node.isURDFCollider)) {
      child.userData.robotModelRole = "collision";
    }
    child.castShadow = false;
    child.receiveShadow = true;
    const materials = Array.isArray(child.material) ? child.material : [child.material];
    materials.filter(Boolean).forEach((material) => {
      if ("side" in material) material.side = THREE.DoubleSide;
      if ("needsUpdate" in material) material.needsUpdate = true;
    });
  });
  object.userData.collisionLoaded = colliders.length > 0;
  return colliders;
}

async function buildRobotModelWithRobotViewerLoader(THREE, URDFLoader, ColladaLoader, STLLoader, model, urdfText) {
  const documentXml = parseRobotUrdfXml(urdfText);
  const meshTotal = countRobotMeshReferences(documentXml);
  const meshProgress = createRobotMeshProgress(meshTotal);
  const manager = new THREE.LoadingManager();
  const loader = new URDFLoader(manager);
  const colladaLoader = new ColladaLoader(manager);
  const stlLoader = new STLLoader(manager);
  const urdfBaseUrl = new URL("./", new URL(model.urdfUrl, window.location.href)).toString();
  const meshLoads = [];

  loader.parseVisual = true;
  loader.parseCollision = true;
  loader.packages = (packageName) => `/api/robot-model-assets/${encodeURIComponent(model.family)}/${encodeURIComponent(model.key)}`;
  loader.loadMeshCb = (path, _manager, done) => {
    const url = robotAssetUrl(path);
    const name = path || url;
    const extension = robotAssetExtension(url);
    meshProgress.note(name);
    const meshLoad = (async () => {
      return cachedRobotMeshLoad({ THREE, colladaLoader, stlLoader }, url, extension, (event) => meshProgress.note(name, event));
    })()
      .then((object) => {
        done(object, null);
        meshProgress.done(name);
        return object;
      })
      .catch((error) => {
        done(null, error);
        meshProgress.done(name);
        throw new Error(`${robotAssetName(path)} 加载失败：${error.message || error}`);
      });
    meshLoads.push(meshLoad);
  };

  const root = loader.parse(urdfText, urdfBaseUrl);
  root.name = model.key || root.robotName || "robot_model";
  await Promise.all(meshLoads);
  const colliders = prepareRobotViewerObject(THREE, root);
  setRobotLoadProgress({
    active: true,
    value: 94,
    label: "生成关节结构",
    detail: "Robot Viewer URDFLoader 已完成 link / joint / collision 层级",
    level: "warn",
  });
  return { root, joints: root.joints || {}, colliders };
}

function frameRobotModelInViewer(modelRoot) {
  const robot = state.robotModel;
  const THREE = robot.three;
  if (!THREE || !modelRoot || !robot.controls) return;

  modelRoot.position.set(0, 0, 0);
  modelRoot.scale.setScalar(1);
  modelRoot.updateMatrixWorld(true);

  const box = new THREE.Box3().setFromObject(modelRoot);
  if (box.isEmpty()) return;
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(center);
  const maxDim = Math.max(size.x, size.y, size.z);
  const scale = maxDim > 0 ? clamp(4.4 / maxDim, 0.0002, 60) : 1;
  modelRoot.scale.setScalar(scale);

  modelRoot.position.set(
    -center.x * scale,
    -center.y * scale,
    -box.min.z * scale,
  );

  const framedSize = maxDim * scale;
  robot.controls.target.set(0, 0, (center.z - box.min.z) * scale);
  robot.controls.distance = clamp(framedSize * 1.45, 2.4, 12);
  updateRobotCamera();
}

function setRobotJointValue(name, value, options = {}) {
  const robot = state.robotModel;
  const joint = robot.joints[name];
  const parsed = Number(value);
  if (!joint || !Number.isFinite(parsed)) return;
  if (typeof joint.setJointValue === "function") {
    const previousIgnoreLimits = joint.ignoreLimits;
    if (options.clamp === false) joint.ignoreLimits = true;
    joint.setJointValue(parsed);
    joint.ignoreLimits = previousIgnoreLimits;
  }
}

function robotJointLimitValue(joint, key, fallback) {
  const value = Number(joint?.limit?.[key]);
  return Number.isFinite(value) ? value : fallback;
}

function updateRobotModelTransforms() {
  const robot = state.robotModel;
  if (!robot.hasModel || !robot.modelRoot || !robot.three) return;
  const jointMap = robot.metadata && robot.metadata.jointMap ? robot.metadata.jointMap : {};
  const actualHeight = Number(state.liftingState.heightM);
  const heightForModel = Number.isFinite(actualHeight) ? actualHeight : state.liftPreview.height;
  const liftJointName = jointMap.lift || "lifting_joint";
  const liftJoint = robot.joints[liftJointName];
  if (liftJoint) {
    const lower = robotJointLimitValue(liftJoint, "lower", -0.6);
    const upper = robotJointLimitValue(liftJoint, "upper", 0);
    setRobotJointValue(liftJointName, lower + (upper - lower) * (liftPercent(heightForModel) / 100));
  }

  ["left", "right"].forEach((side) => {
    const feedback = state.piperJoints[side];
    const armNames = jointMap[`${side}Arm`] || [];
    armNames.forEach((name, index) => {
      const value = robotArmStateValueFor(feedback, side, name, index);
      if (Number.isFinite(value)) setRobotJointValue(name, value, { clamp: false });
    });

    const gripperNames = jointMap[`${side}Gripper`] || [];
    const gripperValue = gripperStateValueFor(feedback);
    if (gripperNames.length >= 2 && Number.isFinite(gripperValue)) {
      const opening = clamp(Math.abs(gripperValue), 0, 0.05);
      setRobotJointValue(gripperNames[0], opening);
      setRobotJointValue(gripperNames[1], -opening);
    }
  });

  if (localizationViewActive() && state.localization.selectedMapName) {
    robot.modelRoot.scale.setScalar(1);
    robot.modelRoot.position.set(0, 0, 0);
    robot.modelRoot.rotation.z = 0;
    return;
  }

  const mappingPose = mappingPoseFromTransform();
  if (mappingPose) {
    robot.modelRoot.scale.setScalar(1);
    robot.modelRoot.position.set(mappingPose.x, mappingPose.y, Number.isFinite(mappingPose.z) ? mappingPose.z : 0);
    robot.modelRoot.rotation.z = mappingPose.yaw;
  } else {
    const yaw = yawFromOdom(state.chassisState.odom || {});
    robot.modelRoot.rotation.z = yaw === null ? 0 : yaw;
  }
}

function setRobotPoseSyncEnabled(enabled, options = {}) {
  const robot = state.robotModel;
  if (enabled && !robot.hasModel) {
    if (!options.silent) addLog("模型", "姿态同步需要先加载整机模型");
    renderRobotPoseSyncButton();
    return false;
  }

  const nextEnabled = Boolean(enabled);
  if (robot.poseSyncEnabled === nextEnabled) {
    renderRobotPoseSyncButton();
    return robot.poseSyncEnabled;
  }

  robot.poseSyncEnabled = nextEnabled;
  if (robot.poseSyncEnabled) {
    updateRobotModelTransforms();
    if (!options.silent) addLog("模型", "姿态同步已开启：整机视图跟随 State");
  } else if (!options.silent) {
    addLog("模型", "姿态同步已关闭：整机视图保持当前姿态");
  }
  renderRobotViewStatus();
  return robot.poseSyncEnabled;
}

function toggleRobotPoseSync() {
  setRobotPoseSyncEnabled(!state.robotModel.poseSyncEnabled);
}

async function loadRobotModel(key = state.robotModel.selectedKey) {
  if (!key) return null;
  if (state.robotModel.loadPromise) return state.robotModel.loadPromise;

  const promise = (async () => {
    setRobotLoadProgress({
      active: true,
      value: 4,
      label: "读取模型信息",
      detail: "正在请求模型元数据",
      level: "warn",
      meshLoaded: 0,
      meshTotal: 0,
    });
    setRobotModelStatus("loading", "正在读取模型信息");
    const response = await fetch(`/api/robot-models/${encodeURIComponent(key)}`, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !payload.ok || !payload.model) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }

    const model = payload.model;
    setRobotLoadProgress({
      active: true,
      value: 16,
      label: "初始化 3D 视图",
      detail: model.name || key,
      level: "warn",
    });
    const initialized = await initializeRobotViewer();
    if (!initialized) throw new Error("整机 3D 视图初始化失败");
    const { THREE, URDFLoader, ColladaLoader, STLLoader } = await loadThreeLoaders();

    setRobotLoadProgress({
      active: true,
      value: 28,
      label: "下载 URDF",
      detail: robotAssetName(model.urdfUrl),
      level: "warn",
    });
    const urdfResponse = await fetch(model.urdfUrl, { cache: "no-store" });
    if (!urdfResponse.ok) throw new Error(`URDF 请求失败：HTTP ${urdfResponse.status}`);
    const urdfText = await urdfResponse.text();
    setRobotLoadProgress({
      active: true,
      value: 36,
      label: "解析 URDF",
      detail: "Robot Viewer URDFLoader 正在读取模型",
      level: "warn",
    });
    const { root, joints, colliders } = await buildRobotModelWithRobotViewerLoader(THREE, URDFLoader, ColladaLoader, STLLoader, model, urdfText);

    if (state.robotModel.lidarOverlay.points?.parent) {
      state.robotModel.lidarOverlay.points.parent.remove(state.robotModel.lidarOverlay.points);
      state.robotModel.lidarOverlay.frameObject = null;
    }
    if (state.robotModel.modelRoot) {
      state.robotModel.displayRoot.remove(state.robotModel.modelRoot);
    }
    state.robotModel.displayRoot.add(root);
    state.robotModel.modelRoot = root;
    state.robotModel.joints = joints;
    state.robotModel.colliders = colliders;
    state.robotModel.metadata = model;
    state.robotModel.loadedKey = key;
    state.robotModel.hasModel = true;
    frameRobotModelInViewer(root);
    if (state.robotModel.poseSyncEnabled || mappingFinalTransform() || localizationViewActive()) updateRobotModelTransforms();
    if (state.robotModel.lidarOverlay.enabled) ensureRobotLidarOverlay();
    setRobotLoadProgress({
      active: false,
      value: 100,
      label: "加载完成",
      detail: `${model.name || key} 已显示在整机视图`,
      level: "ok",
    });
    setRobotModelStatus("ready", `${model.name || key} 已加载到整机视图`);
    addLog("模型", `整机模型已加载：${model.name || key}`);
    return model;
  })();

  state.robotModel.loadPromise = promise;
  try {
    return await promise;
  } catch (error) {
    state.robotModel.hasModel = false;
    state.robotModel.poseSyncEnabled = false;
    setRobotLoadProgress({
      active: false,
      label: "加载失败",
      detail: error.message,
      level: "danger",
    });
    setRobotModelStatus("error", `模型加载失败：${error.message}`);
    addLog("模型", `模型加载失败：${error.message}`);
    return null;
  } finally {
    if (state.robotModel.loadPromise === promise) state.robotModel.loadPromise = null;
  }
}

function renderRobotResourceList() {
  const node = $("#robotResourceList");
  if (!node) return;
  const robot = state.robotModel;
  const meta = robotModelStatusMeta();
  const urdfText = robot.hasModel ? "已加载" : robot.status === "loading" ? "加载中" : robot.models.length ? "可加载" : "待发现";
  const urdfLevel = robot.hasModel ? "ok" : robot.status === "loading" ? "warn" : robot.models.length ? "idle" : "idle";
  const meshText = robot.hasModel ? "已解析" : robot.status === "loading" ? "解析中" : "待加载";
  const meshLevel = robot.hasModel ? "ok" : robot.status === "loading" ? "warn" : robot.status === "error" ? "danger" : "idle";
  node.innerHTML = [
    ["模型清单", meta.text, meta.level],
    ["URDF 加载", urdfText, urdfLevel],
    ["Mesh 解析", meshText, meshLevel],
  ]
    .map(
      ([name, text, level]) => `
        <div><span>${escapeHtml(name)}</span><strong class="status-text ${escapeHtml(level)}">${escapeHtml(text)}</strong></div>
      `,
    )
    .join("");
}

function renderRobotViewStatus() {
  const summaryNode = $("#robotSummaryMetrics");

  const leftArm = armStatusText("left");
  const rightArm = armStatusText("right");
  const chassisMeta = chassisFeedbackMeta();
  const liftMeta = liftingFeedbackMeta();
  const chassisLevel = chassisMeta.level;
  const liftLevel = liftMeta.level;
  const chassisText = chassisMeta.inlineText;
  const liftText = liftMeta.inlineText;
  const actualHeight = Number(state.liftingState.heightM);
  const odom = state.chassisState.odom || {};
  const linearX = nestedNumber(odom, ["twist", "twist", "linear", "x"]);
  const linearY = nestedNumber(odom, ["twist", "twist", "linear", "y"]);
  const ages = [
    state.chassisState.ageMs,
    state.liftingState.ageMs,
    state.piperJoints.left.ageMs,
    state.piperJoints.right.ageMs,
  ]
    .filter((value) => value !== null && value !== undefined)
    .map(Number)
    .filter(Number.isFinite);
  const maxAge = ages.length ? Math.max(...ages) : null;
  const robot = state.robotModel;
  const feedbackSync = robotFeedbackSyncMeta();
  const modelMeta = robotModelStatusMeta();
  const selectedModel = robot.models.find((model) => model.key === robot.selectedKey);
  const modelName = robot.metadata?.name || selectedModel?.name || selectedModel?.key || "--";

  setStateBadge("#robotModelBadge", modelMeta.text, modelMeta.level);
  setStateBadge("#robotSyncBadge", robot.poseSyncEnabled ? feedbackSync.text : "未同步", robot.poseSyncEnabled ? feedbackSync.level : "idle");

  const stage = $("#robotViewStage");
  if (stage) {
    stage.classList.toggle("is-loading", robot.status === "fetching" || robot.status === "loading");
    stage.classList.toggle("is-model-loaded", robot.hasModel);
    stage.classList.toggle("is-pose-syncing", robot.poseSyncEnabled && robot.hasModel);
  }

  const updates = [
    ["#robotFrameText", state.chassisState.odom ? "odom / base_link" : "base_link"],
    ["#robotModelSourceText", robot.hasModel ? modelName : robot.models.length ? "可选择模型" : "等待资源"],
    ["#robotSyncAgeText", robotAgeText(maxAge)],
    ["#robotOverlayTitle", robot.hasModel ? "模型已加载" : modelMeta.text],
    ["#robotOverlayDetail", robot.detail || "等待模型资源接入"],
    ["#robotModelDetail", robot.detail || "等待模型资源接入"],
  ];
  updates.forEach(([selector, text]) => {
    const node = $(selector);
    if (node) node.textContent = text;
  });

  if (summaryNode) {
    summaryNode.innerHTML = [
      ["底盘", state.chassisState.odom ? chassisText : "--"],
      ["速度", linearX === null ? "--" : `${linearX.toFixed(2)} / ${(linearY || 0).toFixed(2)} m/s`],
      ["升降", Number.isFinite(actualHeight) ? `${actualHeight.toFixed(3)} m` : "--"],
      ["左臂", leftArm.text],
      ["右臂", rightArm.text],
      ["延迟", robotAgeText(maxAge)],
    ]
      .map(([name, value]) => `<div class="metric-card"><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");
  }

  const componentRows = [
    ["底盘", chassisText, chassisLevel, state.chassisState.odom ? "里程计 /odom" : state.chassisState.detail],
    ["升降轴", liftText, liftLevel, state.liftingState.ok ? "LiftMotorStatePub" : state.liftingState.detail],
    ["左臂", leftArm.text, leftArm.level, leftArm.detail],
    ["右臂", rightArm.text, rightArm.level, rightArm.detail],
    ["模型资源", modelMeta.text, modelMeta.level, robot.detail],
  ];
  const componentNode = $("#robotComponentList");
  if (componentNode) {
    componentNode.innerHTML = componentRows
      .map(
        ([name, text, level, detail]) => `
          <div class="robot-component-row">
            <span>${escapeHtml(name)}</span>
            <strong class="status-text ${escapeHtml(level)}">${escapeHtml(text)}</strong>
            <small>${escapeHtml(detail || "--")}</small>
          </div>
        `,
      )
      .join("");
  }

  renderRobotModelControls();
  renderRobotResourceList();
  renderRobotLoadProgress();
  if (robot.poseSyncEnabled) updateRobotModelTransforms();
  renderRobotViewFigure();
}

function renderMappingStatus() {
  const mapping = state.mapping;
  const session = mapping.session;
  const statusKey = session?.status || mapping.status || "idle";
  const meta = mappingStatusMeta[statusKey] || mappingStatusMeta.idle;
  const busy = Boolean(mapping.busy || session?.busy);
  const progress = session?.progress || null;
  const progressMeta = mappingProgressMeta[progress?.phase] || null;
  const busyLabel = progress?.label || progressMeta?.label || "采集中";
  const keyframes = Array.isArray(session?.keyframes) ? session.keyframes : [];
  const lastResult = session?.lastResult || null;
  const mapPreview = mapping.mapPreview;

  setStateBadge("#mappingBadge", busy ? busyLabel : meta.label, busy ? (progressMeta?.level || "warn") : meta.level);
  setText("#mappingSummary", session?.detail || mapping.lastError || "等待创建建图会话");
  setText("#mappingSessionText", session ? `${session.id} / ${session.sessionDir || ""}` : "未创建 session");

  const frameInput = $("#mappingFrameCountInput");
  if (frameInput && document.activeElement !== frameInput) frameInput.value = String(mapping.frameCount || 10);
  const cloudInput = $("#mappingCloudTopicInput");
  if (cloudInput && document.activeElement !== cloudInput) cloudInput.value = mapping.cloudTopic || "/rslidar_points";
  const odomInput = $("#mappingOdomTopicInput");
  if (odomInput && document.activeElement !== odomInput) odomInput.value = mapping.odomTopic || "/odom";
  const baseInput = $("#mappingBaseFrameInput");
  if (baseInput && document.activeElement !== baseInput) baseInput.value = mapping.baseFrame || "base_link";

  const startButton = $("#mappingStartButton");
  if (startButton) {
    startButton.disabled = busy;
    startButton.textContent = session ? "重建" : "新建";
  }
  const captureButton = $("#mappingCaptureButton");
  if (captureButton) {
    captureButton.disabled = busy || !session;
    captureButton.textContent = busy ? busyLabel : keyframes.length ? "继续采集" : "采集点云";
  }
  const saveButton = $("#mappingSaveButton");
  if (saveButton) saveButton.disabled = busy || !session || keyframes.length === 0;
  const deleteLastButton = $("#mappingDeleteLastButton");
  if (deleteLastButton) {
    deleteLastButton.disabled = busy || !session || keyframes.length === 0 || !session.canDeleteLast;
  }
  const resetButton = $("#mappingResetButton");
  if (resetButton) resetButton.disabled = !session && !busy;

  const metrics = $("#mappingMetrics");
  if (metrics) {
    const registration = lastResult?.registration || {};
    const mapState = mapPreview.activeRequest
      ? "加载中"
      : mapPreview.error
        ? "异常"
        : mapPreview.hasFrame
          ? "已显示"
          : session?.tmpMapPath
            ? "待加载"
            : "--";
    metrics.innerHTML = [
      ["Keyframes", String(keyframes.length)],
      ["点云", mapping.cloudTopic || "--"],
      ["里程计", mapping.odomTopic || "--"],
      ["阶段", busy ? busyLabel : registration.stage || statusKey],
      ["Fitness", Number.isFinite(Number(registration.fitness)) ? Number(registration.fitness).toFixed(5) : "--"],
      ["地图", mapState],
      ["地图点", mapPreview.hasFrame ? Math.max(0, Math.round(mapPreview.pointCount || 0)).toLocaleString("zh-CN") : "--"],
      ["地图大小", mapPreview.hasFrame ? formatBytes(mapPreview.sizeBytes) : "--"],
    ]
      .map(([name, value]) => `<div class="metric-card"><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");
  }

  const list = $("#mappingKeyframeList");
  if (list) {
    list.innerHTML = keyframes.length
      ? keyframes
          .map((keyframe) => {
            const index = Number(keyframe.index);
            const frames = Number(keyframe.frames);
            return `
              <div class="mapping-keyframe-row">
                <span>#${Number.isFinite(index) ? index : "--"}</span>
                <strong>${Number.isFinite(frames) ? `${frames} 帧` : "已采集"}</strong>
                <small>${escapeHtml(keyframe.path || "")}</small>
              </div>
            `;
          })
          .join("")
      : `<div class="mapping-keyframe-empty">${escapeHtml(session?.lastError || "暂无 keyframe")}</div>`;
  }

  renderChassisKeyboardControl();
}

function localizationSelectedMap() {
  return state.localization.maps.find((entry) => entry.name === state.localization.selectedMapName) || state.localization.selectedMap || null;
}

function localizationTimestampText(value) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed) || parsed <= 0) return "--";
  return new Date(parsed).toLocaleString("zh-CN", { hour12: false });
}

function localizationMapStateText() {
  const localization = state.localization;
  const preview = localization.mapPreview;
  if (localization.mapsLoading) return "读取地图列表";
  if (preview.activeRequest) return "加载点云";
  if (localization.lastError || preview.error) return "异常";
  if (preview.hasFrame) return "已显示";
  if (localization.selectedMapName) return "待加载";
  if (localization.maps.length) return "待选择";
  return "无可用地图";
}

function localizationMapLevel() {
  const localization = state.localization;
  if (localization.mapsLoading || localization.mapPreview.activeRequest) return "warn";
  if (localization.lastError || localization.mapPreview.error) return "danger";
  if (localization.mapPreview.hasFrame) return "ok";
  return "idle";
}

function renderLocalizationMapSelect() {
  const select = $("#localizationMapSelect");
  if (!select) return;
  const localization = state.localization;
  const options = localization.maps.length
    ? [`<option value="">选择地图</option>`]
        .concat(localization.maps.map((entry) => `<option value="${escapeHtml(entry.name)}">${escapeHtml(entry.name)}</option>`))
        .join("")
    : `<option value="">${localization.mapsLoading ? "读取中" : "暂无可用地图"}</option>`;
  if (select.dataset.options !== options) {
    select.innerHTML = options;
    select.dataset.options = options;
  }
  select.value = localization.selectedMapName || "";
  select.disabled = localization.mapsLoading || localization.maps.length === 0;
}

function renderLocalizationStatus() {
  const localization = state.localization;
  const preview = localization.mapPreview;
  const selected = localizationSelectedMap();
  const statusText = localizationMapStateText();
  const statusLevel = localizationMapLevel();
  const locRunning = state.localizationRuntime.status === "running";
  const currentMap = localization.selectedMapName || "--";
  const pointCount = preview.hasFrame ? Math.max(0, Math.round(preview.pointCount || 0)).toLocaleString("zh-CN") : "--";
  const sourcePointCount = preview.hasFrame ? Math.max(0, Math.round(preview.sourcePointCount || preview.pointCount || 0)).toLocaleString("zh-CN") : "--";
  const sizeBytes = preview.hasFrame ? preview.sizeBytes : selected?.sizeBytes;
  const mtimeMs = preview.hasFrame ? preview.mtimeMs : selected?.mtimeMs;

  renderLocalizationRuntime();
  renderLocalizationMapSelect();
  setStateBadge("#localizationPageBadge", locRunning ? "Loc 运行中" : statusText, locRunning ? "ok" : statusLevel);
  setStateBadge("#localizationStatusBadge", locRunning ? "运行中" : "待接入", locRunning ? "ok" : "idle");
  setText(
    "#localizationMapSummary",
    localization.lastError || preview.error || (selected ? `${selected.name} / ${selected.mapPath || "map.pcd"}` : "选择 modules/map/data 下的已保存地图"),
  );
  setText(
    "#localizationViewerSummary",
    preview.hasFrame
      ? `${currentMap} / Ranger Mini v3 / 初始位姿 0, 0, 0`
      : "Ranger Mini v3 / 初始位姿 0, 0, 0",
  );
  setText("#localizationStatusSummary", locRunning ? "Loc 前端入口已开启，真实定位服务待接入" : "真实定位服务待接入");

  const overlayTitle = $("#localizationOverlayTitle");
  if (overlayTitle) overlayTitle.textContent = preview.activeRequest ? "地图加载中" : preview.hasFrame ? currentMap : statusText;
  const overlayDetail = $("#localizationOverlayDetail");
  if (overlayDetail) {
    overlayDetail.textContent = preview.error
      ? preview.error
      : preview.hasFrame
        ? `${pointCount} 点 / 可旋转、平移、缩放`
        : "选择保存地图后自动加载 map.pcd";
  }

  const mapMetrics = $("#localizationMapMetrics");
  if (mapMetrics) {
    mapMetrics.innerHTML = [
      ["可用地图", String(localization.maps.length)],
      ["当前地图", currentMap],
      ["地图状态", statusText],
      ["地图点", pointCount],
      ["源点数", sourcePointCount],
      ["文件大小", Number.isFinite(Number(sizeBytes)) ? formatBytes(sizeBytes) : "--"],
      ["更新时间", localizationTimestampText(mtimeMs)],
      ["初始位姿", "0 / 0 / 0"],
    ]
      .map(([name, value]) => `<div class="metric-card"><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");
  }

  const statusMetrics = $("#localizationStatusMetrics");
  if (statusMetrics) {
    statusMetrics.innerHTML = [
      ["Loc", locRunning ? "运行中" : "未启动"],
      ["地图", currentMap],
      ["NDT", "待接入"],
      ["GICP", "待接入"],
      ["Pose X/Y/Yaw", "0.00 / 0.00 / 0.0"],
      ["匹配分数", "--"],
      ["置信度", "--"],
      ["最近更新", locRunning ? formatTime() : "--"],
    ]
      .map(([name, value]) => `<div class="metric-card"><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");
  }
}

function renderLiftingRuntime() {
  const label = getLiftingRuntimeLabel();
  renderStatusSwitch("#liftingRuntimeStatus", "Lifting", label.level, {
    pressed: label.pressed,
    busy: label.busy,
    title: label.title,
  });
}

function renderChassisRuntime() {
  const label = getChassisRuntimeLabel();
  renderStatusSwitch("#chassisRuntimeStatus", "Chassis", label.level, {
    pressed: label.pressed,
    busy: label.busy,
    title: label.title,
  });
}

function renderLocalizationRuntime() {
  const label = getLocalizationRuntimeLabel();
  renderStatusSwitch("#localizationRuntimeStatus", "Loc", label.level, {
    pressed: label.pressed,
    busy: label.busy,
    title: label.title,
  });
}

function renderCameraRuntime() {
  const label = getCameraRuntimeLabel();
  renderStatusSwitch("#cameraRuntimeStatus", "Camera", label.level, {
    pressed: label.pressed,
    busy: label.busy,
    title: label.title,
  });
}

function renderLidarRuntime() {
  const label = getLidarRuntimeLabel();
  renderStatusSwitch("#lidarRuntimeStatus", "LiDAR", label.level, {
    pressed: label.pressed,
    busy: label.busy,
    title: label.title,
  });
}

function renderLiftPreview() {
  const limits = state.liftingState.limits || {};
  const minHeight = Number.isFinite(Number(limits.minHeightM)) ? Number(limits.minHeightM) : liftPreviewLimits.min;
  const maxHeight = Number.isFinite(Number(limits.maxHeightM)) ? Number(limits.maxHeightM) : liftPreviewLimits.max;
  const height = clamp(Number(state.liftPreview.height), minHeight, maxHeight);
  const speed = clamp(Number(state.liftPreview.speed), liftPreviewLimits.speedMin, liftPreviewLimits.speedMax);
  const stepUpMm = clamp(Number(state.liftPreview.stepUpMm), 1, Math.max(1, Math.round((maxHeight - minHeight) * 1000)));
  const stepDownMm = clamp(Number(state.liftPreview.stepDownMm), 1, Math.max(1, Math.round((maxHeight - minHeight) * 1000)));
  state.liftPreview.height = height;
  state.liftPreview.speed = speed;
  state.liftPreview.stepUpMm = stepUpMm;
  state.liftPreview.stepDownMm = stepDownMm;
  const percent = liftPercent(height);

  const heightText = `${height.toFixed(2)} m`;
  const speedText = `${speed.toFixed(2)} m/s`;
  const actualHeight = Number(state.liftingState.heightM);
  const actualText = Number.isFinite(actualHeight) ? `${actualHeight.toFixed(3)} m` : "--";
  const stateTargetHeight = Number(state.liftingState.targetHeightM);
  const stateTargetText = Number.isFinite(stateTargetHeight) ? `${stateTargetHeight.toFixed(3)} m` : "--";
  const backSpeed = Number(state.liftingState.backSpeedMps);
  const backSpeedText = Number.isFinite(backSpeed) ? `${backSpeed.toFixed(3)} m/s` : "--";
  const voltage = Number(state.liftingState.voltage);
  const current = Number(state.liftingState.current);
  const powerText = Number.isFinite(voltage) && Number.isFinite(current)
    ? `${voltage.toFixed(0)} V / ${current.toFixed(2)} A`
    : "--";
  const feedbackMeta = liftingFeedbackMeta();
  const actualMetaText = feedbackMeta.inlineText;
  const reachText = state.liftingState.ok ? (state.liftingState.reachTarget ? "已到位" : "运动中") : "--";
  const serviceExternal = state.liftingRuntime.status === "external";
  const serviceText = serviceExternal ? "外部运行" : liftingReady() ? "运行中" : "未启动";
  const serviceLevel = serviceExternal ? "warn" : liftingReady() ? "ok" : "idle";
  const feedbackLevel = feedbackMeta.level;
  const feedbackText = feedbackMeta.inlineText;
  const limitActive = Boolean(state.liftingState.upLimit || state.liftingState.downLimit);
  const limitText = !state.liftingState.ok ? "未知" : state.liftingState.upLimit ? "上限位" : state.liftingState.downLimit ? "下限位" : "正常";
  const limitLevel = !state.liftingState.ok ? "idle" : limitActive ? "warn" : "ok";

  const updates = [
    ["#liftHeightValue", heightText],
    ["#liftHeightPreview", heightText],
    ["#liftSpeedPreview", speedText],
    ["#liftModeValue", state.liftPreview.mode],
    ["#liftActualHeightValue", actualText],
    ["#liftActualValue", actualMetaText],
    ["#liftStateTargetValue", stateTargetText],
    ["#liftBackSpeedValue", backSpeedText],
    ["#liftPowerValue", powerText],
    ["#liftReachValue", reachText],
    ["#liftMaxLabel", `${maxHeight.toFixed(2)} m`],
    ["#liftMinLabel", `${minHeight.toFixed(2)} m`],
  ];
  updates.forEach(([selector, text]) => {
    const node = $(selector);
    if (node) node.textContent = text;
  });
  const actualMeta = $("#liftActualValue");
  if (actualMeta) actualMeta.className = `latency-text ${feedbackLevel}`;

  const heightInput = $("#liftHeightInput");
  if (heightInput) {
    heightInput.min = minHeight.toFixed(3);
    heightInput.max = maxHeight.toFixed(3);
    if (document.activeElement !== heightInput) heightInput.value = height.toFixed(2);
  }
  const heightNumberInput = $("#liftHeightNumberInput");
  if (heightNumberInput) {
    heightNumberInput.min = minHeight.toFixed(3);
    heightNumberInput.max = maxHeight.toFixed(3);
    if (document.activeElement !== heightNumberInput) heightNumberInput.value = height.toFixed(2);
  }
  const speedInput = $("#liftSpeedInput");
  if (speedInput && document.activeElement !== speedInput) speedInput.value = speed.toFixed(2);
  const stepUpInput = $("#liftStepUpInput");
  if (stepUpInput && document.activeElement !== stepUpInput) stepUpInput.value = String(Math.round(stepUpMm));
  const stepDownInput = $("#liftStepDownInput");
  if (stepDownInput && document.activeElement !== stepDownInput) stepDownInput.value = String(Math.round(stepDownMm));

  $$("[data-lift-preset]").forEach((button) => {
    const preset = Number(button.dataset.liftPreset);
    const active = Number.isFinite(preset) && Math.abs(preset - height) < 0.005;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-pressed", active ? "true" : "false");
  });

  const fill = $("#liftGaugeFill");
  if (fill) fill.style.height = `clamp(0px, ${percent}%, calc(100% - 24px))`;
  const carriage = $("#liftGaugeCarriage");
  if (carriage) carriage.style.bottom = `clamp(16px, ${percent}%, calc(100% - 16px))`;

  setStatusText("#liftServiceText", serviceText, serviceLevel);
  setStatusText("#liftInitText", state.liftingState.initState ? "完成" : "未完成", state.liftingState.initState ? "ok" : "warn");
  setStatusText("#liftFeedbackText", feedbackText, feedbackLevel);
  setStatusText("#liftLimitText", limitText, limitLevel);

  const serviceDisabled = !liftingReady();
  const actionDisabled = !liftingInitialized();
  ["#liftInitButton", "#liftStopButton"].forEach((selector) => {
    $$(selector).forEach((button) => {
      button.disabled = serviceDisabled;
    });
  });
  ["#liftApplyHeightButton", "#liftHeightInput", "#liftHeightNumberInput", "[data-lift-preset]", "[data-lift-move]", "[data-lift-step]"].forEach((selector) => {
    $$(selector).forEach((button) => {
      button.disabled = actionDisabled;
    });
  });
  renderRobotViewStatus();
}

function renderBaseControlPanel(selector) {
  const baseNode = $(selector);
  if (baseNode) {
    baseNode.innerHTML = deviceBaseControlItems
      .map((item) => {
        const value = normalizedSpeedValue(item);
        const percent = clamp(value, 0, 1) * 100;
        const color = speedRiskColor(value);
        return `
          <label class="slider-row base-slider-row base-speed-row" style="--speed-risk: ${percent}%; --speed-color: ${color};">
            <span>${item.label}</span>
            <small>${formatCommandSpeed(item, item.min)}</small>
            <input
              type="range"
              min="${item.min}"
              max="${item.max}"
              step="${item.step}"
              value="${value.toFixed(2)}"
              data-base-control="${item.key}"
              aria-label="${item.label}"
              aria-valuetext="${formatCommandSpeed(item, value)}"
            />
            <small>${formatCommandSpeed(item, item.max)}</small>
            <strong>${formatCommandSpeed(item, value)}</strong>
          </label>
        `;
      })
      .join("");
  }
}

function renderDeviceControls() {
  renderPiperJointFeedback();
  renderBaseControlPanel("#deviceBaseControlPanel");
  renderBaseControlPanel("#mappingBaseControlPanel");
  renderLiftPreview();
}

function renderPiperRuntime() {
  const label = getPiperRuntimeLabel();
  renderStatusSwitch("#piperRuntimeStatus", "Piper", label.level, {
    pressed: label.pressed,
    busy: label.busy,
    title: label.title,
  });
}

function renderLogs() {
  const logs = state.activeLogFilter === "全部" ? state.logs : state.logs.filter((log) => log.source === state.activeLogFilter);
  const html = logs
    .map(
      (log) => `
        <div class="log-item">
          <time>${log.time}</time>
          <span class="log-source">${log.source}</span>
          <span>${log.message}</span>
        </div>
      `,
    )
    .join("");
  $("#drawerEvents").innerHTML = html || `<div class="log-item"><time>--:--</time><span class="log-source">系统</span><span>暂无事件</span></div>`;
  $("#logList").innerHTML = html || `<div class="log-item"><time>--:--</time><span class="log-source">系统</span><span>暂无事件</span></div>`;
  $("#logCount").textContent = `${logs.length} 条`;
}

function renderHistory() {
  $("#historyList").innerHTML = historyItems
    .map(
      ([title, result, detail]) => `
        <div class="history-item">
          <div><strong>${title}</strong><span>${detail}</span></div>
          <span class="status-text ${statusClass(result === "成功" || result === "完成" ? "正常" : result === "警告" ? "警告" : "错误")}">${result}</span>
        </div>
      `,
    )
    .join("");
}

function renderLogFilters() {
  $("#logFilters").innerHTML = logSources
    .map((source) => `<button class="${source === state.activeLogFilter ? "is-active" : ""}" data-log-filter="${source}">${source}</button>`)
    .join("");
}

function renderActionLocks() {
  const busy = state.task !== "idle";
  const locked = !state.auth.authenticated;
  const runtimeReady = piperReady();
  $$("[data-action]").forEach((button) => {
    const action = button.dataset.action;
    const requiresPiper = action === "homing" || action === "collection" || action === "inference";
    button.disabled = locked || busy || (requiresPiper && !runtimeReady);
  });
  const startHomingButton = $("#startHomingButton");
  if (startHomingButton) startHomingButton.disabled = locked || busy || !runtimeReady;
  const startCollectionButton = $("#startCollectionButton");
  if (startCollectionButton) startCollectionButton.disabled = locked || busy || !runtimeReady;
  renderPreflight();
}

function syncClock() {
  $("#clockStatus").textContent = formatTime();
}

function formatPlaybackTime(seconds) {
  const safe = Math.max(0, Math.round(Number(seconds) || 0));
  const minutes = Math.floor(safe / 60);
  const remainder = safe % 60;
  return `${String(minutes).padStart(2, "0")}:${String(remainder).padStart(2, "0")}`;
}

function playbackFileName() {
  const path = String(state.playback.path || "").trim();
  return path.split(/[\\/]/).filter(Boolean).pop() || "未选择文件";
}

function playbackSourceTypeFromPath(path) {
  const match = String(path || "").toLowerCase().match(/\.([a-z0-9]+)(?:[?#].*)?$/);
  if (!match) return "unknown";
  if (match[1] === "h5") return "hdf5";
  if (match[1] === "hdf5") return "hdf5";
  if (match[1] === "parquet") return "parquet";
  if (match[1] === "mcap") return "mcap";
  return match[1];
}

function currentPlaybackFile() {
  const dataset = state.playback.dataset;
  if (dataset) {
    return {
      loaded: true,
      durationSec: dataset.durationSec,
      rows: dataset.rows,
      name: dataset.name || playbackFileName(),
      sourceType: dataset.sourceType || playbackSourceTypeFromPath(state.playback.path),
      stateDim: dataset.stateDim,
      actionDim: dataset.actionDim,
      fps: dataset.fps,
    };
  }
  return {
    durationSec: state.playback.durationSec || playbackFileDefaults.durationSec,
    rows: playbackFileDefaults.rows,
    name: playbackFileName(),
    sourceType: playbackSourceTypeFromPath(state.playback.path),
    stateDim: 0,
    actionDim: 0,
    fps: 0,
    loaded: false,
  };
}

function playbackGroupsForCurrentView() {
  if (state.playback.chartGroup === "all") return playbackSignalGroups;
  return playbackSignalGroups.filter((group) => group.key === state.playback.chartGroup);
}

function finitePlaybackNumber(value) {
  if (value === null || value === undefined || typeof value === "boolean") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function playbackValueFromKeys(source, keys) {
  if (!source || typeof source !== "object") return null;
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(source, key)) {
      const value = finitePlaybackNumber(source[key]);
      if (value !== null) return value;
    }
  }
  return null;
}

function playbackArmArrayFromObject(arm) {
  if (Array.isArray(arm)) {
    const values = arm.slice(0, 7).map(finitePlaybackNumber);
    return values.length === 7 && values.every((value) => value !== null) ? values : null;
  }
  if (!arm || typeof arm !== "object") return null;
  const values = playbackArmValueKeys.map((key) => finitePlaybackNumber(arm[key]));
  return values.every((value) => value !== null) ? values : null;
}

function normalizePlaybackState(raw) {
  const source = raw?.state ?? raw?.["observation.state"] ?? raw?.observation?.state;
  if (Array.isArray(source)) {
    const values = source.slice(0, 14).map(finitePlaybackNumber);
    return values.length === 14 && values.every((value) => value !== null) ? values : null;
  }
  if (!source || typeof source !== "object") return null;
  const left = playbackArmArrayFromObject(source.left);
  const right = playbackArmArrayFromObject(source.right);
  return left && right ? [...left, ...right] : null;
}

function normalizePlaybackAction(raw) {
  const source = raw?.action ?? raw?.target ?? raw?.command;
  if (Array.isArray(source)) {
    const values = source.slice(0, 18).map(finitePlaybackNumber);
    return values.length >= 14 && values.slice(0, 14).every((value) => value !== null) ? values : null;
  }
  if (!source || typeof source !== "object") return null;

  const left = playbackArmArrayFromObject(source.left);
  const right = playbackArmArrayFromObject(source.right);
  if (!left || !right) return null;

  const lift = source.lift || {};
  const speed = source.speed || source.chassis || source.base || {};
  const platform = [
    playbackValueFromKeys(lift, ["height", "heightM", "z"]) ?? playbackValueFromKeys(source, ["lift_height", "liftHeight", "height"]),
    playbackValueFromKeys(speed, ["vx", "linearX", "linearx", "linear_x"]) ?? playbackValueFromKeys(source, ["vx", "linearX", "linearx", "linear_x"]),
    playbackValueFromKeys(speed, ["vy", "linearY", "lineary", "linear_y"]) ?? playbackValueFromKeys(source, ["vy", "linearY", "lineary", "linear_y"]),
    playbackValueFromKeys(speed, ["wz", "angularZ", "angularz", "angular_z", "yawRate"]) ??
      playbackValueFromKeys(source, ["wz", "angularZ", "angularz", "angular_z", "yawRate"]),
  ];
  if (platform.some((value) => value !== null)) {
    return [...left, ...right, ...platform];
  }
  return [...left, ...right];
}

function playbackSecondsFromFrame(raw, index, baseTimestamp, fps) {
  const direct = playbackValueFromKeys(raw, ["seconds", "timeSec", "elapsedSec", "time"]);
  if (direct !== null) return Math.max(0, direct);
  const timestamp = playbackValueFromKeys(raw, ["timestamp", "timestampSec", "stamp"]);
  if (timestamp !== null) {
    if (baseTimestamp !== null) return Math.max(0, timestamp - baseTimestamp);
    return Math.max(0, timestamp);
  }
  throw new Error(`回放数据第 ${index} 帧缺少时间戳`);
}

function normalizePlaybackFrame(raw, index, baseTimestamp, fps) {
  const stateValues = normalizePlaybackState(raw);
  const actionValues = normalizePlaybackAction(raw);
  if (!stateValues && !actionValues) return null;
  const frameIndex = playbackValueFromKeys(raw, ["frame_index", "frameIndex", "index"]);
  const timestamp = playbackValueFromKeys(raw, ["timestamp", "timestampSec", "stamp"]);
  return {
    seconds: playbackSecondsFromFrame(raw, index, baseTimestamp, fps),
    frameIndex: frameIndex ?? index,
    timestamp,
    state: stateValues,
    action: actionValues,
  };
}

function playbackDisplayValue(fieldKey, value) {
  if (value === null || value === undefined || !Number.isFinite(Number(value))) return null;
  return Number(value);
}

function downsamplePlaybackSeries(series, maxPoints = playbackChartSamples) {
  if (!Array.isArray(series) || series.length <= maxPoints) return series || [];
  return Array.from({ length: maxPoints }, (_, index) => {
    const sourceIndex = Math.round((index * (series.length - 1)) / (maxPoints - 1));
    return series[sourceIndex];
  });
}

function buildPlaybackSeries(frames) {
  const series = { state: {}, action: {} };
  playbackStateFieldOrder.forEach((key) => {
    series.state[key] = [];
  });
  playbackActionFieldOrder.forEach((key) => {
    series.action[key] = [];
  });

  frames.forEach((frame) => {
    playbackStateFieldOrder.forEach((key, index) => {
      const value = playbackDisplayValue(key, frame.state?.[index]);
      if (value !== null) series.state[key].push({ seconds: frame.seconds, value });
    });
    playbackActionFieldOrder.forEach((key, index) => {
      const value = playbackDisplayValue(key, frame.action?.[index]);
      if (value !== null) series.action[key].push({ seconds: frame.seconds, value });
    });
  });
  return series;
}

function normalizePlaybackDataset(payload, path) {
  const source = payload?.dataset || payload?.data || payload?.playback || payload;
  if (!source || typeof source !== "object") {
    throw new Error("回放数据为空");
  }
  const rawFrames = source.frames || source.samples || source.records || source.rows || [];
  if (!Array.isArray(rawFrames) || rawFrames.length === 0) {
    throw new Error("回放数据缺少 state/action 帧");
  }
  const fps = finitePlaybackNumber(source.fps) || 30;
  const baseTimestamp =
    rawFrames
      .map((frame) => playbackValueFromKeys(frame, ["timestamp", "timestampSec", "stamp"]))
      .find((value) => value !== null) ?? null;

  const frames = rawFrames
    .map((frame, index) => normalizePlaybackFrame(frame, index, baseTimestamp, fps))
    .filter(Boolean)
    .sort((a, b) => a.seconds - b.seconds);
  if (!frames.length) {
    throw new Error("没有可播放的 state/action 数据");
  }

  const durationFromFrames = frames.length > 1 ? frames[frames.length - 1].seconds : frames.length / Math.max(1, fps);
  const durationSec = Math.max(0.001, finitePlaybackNumber(source.durationSec) ?? finitePlaybackNumber(source.duration_s) ?? durationFromFrames);
  const rows = finitePlaybackNumber(source.rows) ?? finitePlaybackNumber(source.frameCount) ?? frames.length;
  const stateDim = Math.max(0, ...frames.map((frame) => frame.state?.length || 0));
  const actionDim = Math.max(0, ...frames.map((frame) => frame.action?.length || 0));

  return {
    path,
    name: source.name || playbackFileName(),
    sourceType: source.sourceType || source.format || playbackSourceTypeFromPath(path),
    fps,
    rows,
    durationSec,
    stateDim,
    actionDim,
    frames,
    series: buildPlaybackSeries(frames),
  };
}

async function loadPlaybackDataset() {
  const path = String(state.playback.path || "").trim();
  if (!path) throw new Error("未选择数据文件");
  state.playback.loading = true;
  state.playback.loadError = "";
  renderPlayback();
  try {
    const response = await fetch("/api/playback/load", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        path,
        focus: ["state", "action"],
        includeImages: false,
        includeRobotControl: false,
        stateSchema: playbackStateFieldOrder,
        actionSchema: playbackActionFieldOrder,
      }),
    });
    let payload = null;
    try {
      payload = await response.json();
    } catch (error) {
      payload = {};
    }
    if (!response.ok || payload?.ok === false) {
      throw new Error(payload?.detail || payload?.error || `HTTP ${response.status}`);
    }
    const dataset = normalizePlaybackDataset(payload, path);
    state.playback.dataset = dataset;
    state.playback.loadedPath = path;
    state.playback.durationSec = dataset.durationSec;
    state.playback.elapsedSec = 0;
    state.playback.currentFrameIndex = 0;
    addLog("数采", `数据回放已加载：${dataset.name} / ${dataset.sourceType} / state ${dataset.stateDim} / action ${dataset.actionDim}`);
    return dataset;
  } catch (error) {
    state.playback.dataset = null;
    state.playback.loadedPath = "";
    state.playback.loadError = error.message;
    addLog("数采", `数据回放加载失败：${error.message}`);
    return null;
  } finally {
    state.playback.loading = false;
    renderPlayback();
  }
}

async function ensurePlaybackDataset() {
  const path = String(state.playback.path || "").trim();
  if (state.playback.dataset && state.playback.loadedPath === path) return state.playback.dataset;
  return loadPlaybackDataset();
}

function formatPlaybackAxisValue(signal, value) {
  if (!Number.isFinite(Number(value))) return "--";
  const rounded = Math.abs(value) < 1e-9 ? 0 : Number(value);
  return `${rounded.toFixed(1)} ${signal.unit}`;
}

function playbackSignalSeries(signal, file, series) {
  const values = state.playback.dataset?.series?.[series]?.[signal.key] || [];
  return downsamplePlaybackSeries(values);
}

function playbackSignalKinds(signal) {
  if (!state.playback.dataset) return [];
  return ["action", "state"].filter((kind) => (state.playback.dataset.series?.[kind]?.[signal.key] || []).length > 0);
}

function playbackAvailableKinds() {
  if (!state.playback.dataset) return ["state", "action"];
  return ["state", "action"].filter((kind) =>
    Object.values(state.playback.dataset.series?.[kind] || {}).some((series) => series.length > 0),
  );
}

function playbackNiceYAxisTickStep(span) {
  const rawStep = Math.max(Number(span) || 0, playbackMinYAxisTickStep * 2) / 4;
  const magnitude = 10 ** Math.floor(Math.log10(rawStep));
  const normalized = rawStep / magnitude;
  let multiplier = 10;
  if (normalized <= 1) multiplier = 1;
  else if (normalized <= 2) multiplier = 2;
  else if (normalized <= 5) multiplier = 5;
  return Math.max(playbackMinYAxisTickStep, multiplier * magnitude);
}

function playbackSeriesRange(seriesList) {
  const values = seriesList.flatMap((series) => series.map((point) => point.value).filter((value) => Number.isFinite(value)));
  if (!values.length) return { min: -1, max: 1, ticks: [-1, 0, 1] };
  let min = Math.min(...values);
  let max = Math.max(...values);
  if (Math.abs(max - min) < 1e-9) {
    min -= playbackMinYAxisTickStep / 2;
    max += playbackMinYAxisTickStep / 2;
  }

  const paddedMin = min - (max - min) * 0.12;
  const paddedMax = max + (max - min) * 0.12;
  const tickStep = playbackNiceYAxisTickStep(paddedMax - paddedMin);
  let axisMin = Math.floor(paddedMin / tickStep) * tickStep;
  let axisMax = Math.ceil(paddedMax / tickStep) * tickStep;

  if (min >= 0 && axisMin < 0) axisMin = 0;
  if (max <= 0 && axisMax > 0) axisMax = 0;
  if (axisMin > 0 && axisMin < tickStep) axisMin = 0;
  if (axisMax < 0 && axisMax > -tickStep) axisMax = 0;

  if (axisMax - axisMin < tickStep) {
    if (axisMin === 0) axisMax = tickStep;
    else if (axisMax === 0) axisMin = -tickStep;
    else {
      const center = (axisMin + axisMax) / 2;
      axisMin = Math.floor((center - tickStep / 2) / tickStep) * tickStep;
      axisMax = Math.ceil((center + tickStep / 2) / tickStep) * tickStep;
    }
  }

  const tickCount = Math.round((axisMax - axisMin) / tickStep);
  const ticks = Array.from({ length: tickCount + 1 }, (_, index) => Number((axisMin + index * tickStep).toFixed(10)));
  return {
    min: Number(axisMin.toFixed(10)),
    max: Number(axisMax.toFixed(10)),
    ticks,
  };
}

function playbackSvgPath(series, range, file) {
  const width = 320;
  const height = 150;
  const padLeft = 54;
  const padRight = 14;
  const padTop = 14;
  const padBottom = 32;
  const duration = Math.max(1, file.durationSec);
  const innerWidth = width - padLeft - padRight;
  const innerHeight = height - padTop - padBottom;
  return series
    .map((point, index) => {
      const x = padLeft + (point.seconds / duration) * innerWidth;
      const span = Math.max(1e-9, range.max - range.min);
      const y = padTop + (1 - (point.value - range.min) / span) * innerHeight;
      return `${index === 0 ? "M" : "L"} ${x.toFixed(1)} ${y.toFixed(1)}`;
    })
    .join(" ");
}

function playbackSvgY(value, range) {
  const padTop = 14;
  const padBottom = 32;
  const innerHeight = 150 - padTop - padBottom;
  const span = Math.max(1e-9, range.max - range.min);
  return padTop + (1 - (value - range.min) / span) * innerHeight;
}

function renderPlaybackLegend() {
  const legend = $("#playbackChartLegend");
  if (!legend) return;
  legend.innerHTML = playbackAvailableKinds()
    .map((kind) => playbackSeriesDetails[kind])
    .filter(Boolean)
    .map((detail) => `<span class="is-on"><i style="background:${detail.color}"></i>${detail.label}</span>`)
    .join("");
}

function playbackEmptyCard(title, detail) {
  return `
    <article class="playback-signal-card">
      <div class="signal-head">
        <strong>${escapeHtml(title)}</strong>
        <span>${escapeHtml(detail)}</span>
      </div>
    </article>
  `;
}

function renderPlaybackCharts() {
  const grid = $("#playbackChartGrid");
  if (!grid) return;

  const file = currentPlaybackFile();
  const groups = playbackGroupsForCurrentView();
  const signalCount = groups.reduce((total, group) => {
    if (!file.loaded) return total + group.signals.length;
    return total + group.signals.filter((signal) => playbackSignalKinds(signal).length > 0).length;
  }, 0);

  setText(
    "#playbackChartSummary",
    file.loaded
      ? `${signalCount} 个维度 / state ${file.stateDim} / action ${file.actionDim} / 横轴 time(s)`
      : "等待加载 state/action 数据",
  );
  const tabs = $("#playbackChartTabs");
  if (tabs) {
    tabs.querySelectorAll("[data-playback-chart-group]").forEach((button) => {
      button.classList.toggle("is-active", button.dataset.playbackChartGroup === state.playback.chartGroup);
    });
  }
  renderPlaybackLegend();

  if (state.playback.loading) {
    grid.innerHTML = playbackEmptyCard("正在读取 state/action", `${playbackFileName()} / ${file.sourceType}`);
    return;
  }
  if (!file.loaded) {
    const detail = state.playback.loadError || "支持 .parquet / .hdf5 / .mcap；暂不读取图像，暂不下发机器人控制。";
    grid.innerHTML = playbackEmptyCard("等待 state/action 数据", detail);
    return;
  }

  grid.innerHTML = groups
    .map((group) => {
      const charts = group.signals
        .filter((signal) => playbackSignalKinds(signal).length > 0)
        .map((signal) => {
          const seriesByKind = playbackSignalKinds(signal).map((kind) => ({
            kind,
            series: playbackSignalSeries(signal, file, kind),
          }));
          const range = playbackSeriesRange(seriesByKind.map((item) => item.series));
          const currentX = 54 + (clamp(state.playback.elapsedSec, 0, file.durationSec) / Math.max(1, file.durationSec)) * 252;
          const yTicks = range.ticks.map((tick) => {
            const y = playbackSvgY(tick, range);
            return `
                <line class="playback-grid-line" x1="54" y1="${y.toFixed(1)}" x2="306" y2="${y.toFixed(1)}"></line>
                <text class="playback-tick" x="48" y="${(y + 3).toFixed(1)}" text-anchor="end">${escapeHtml(formatPlaybackAxisValue(signal, tick))}</text>`;
          }).join("");
          const paths = seriesByKind
            .map((item) => {
              const detail = playbackSeriesDetails[item.kind];
              return `<path class="playback-line playback-line-${item.kind}" d="${playbackSvgPath(item.series, range, file)}" style="--line-color:${detail.color}"></path>`;
            })
            .join("");

          return `
            <article class="playback-signal-card">
              <div class="signal-head">
                <strong>${escapeHtml(signal.label)}</strong>
                <span>${escapeHtml(signal.key)} / ${escapeHtml(signal.unit)}</span>
              </div>
              <svg class="playback-sparkline" viewBox="0 0 320 150" role="img" aria-label="${escapeHtml(signal.key)} state action time chart">
                <line class="playback-axis" x1="54" y1="118" x2="306" y2="118"></line>
                <line class="playback-axis" x1="54" y1="14" x2="54" y2="118"></line>
                ${yTicks}
                <text class="playback-tick" x="54" y="138">0s</text>
                <text class="playback-tick" x="306" y="138" text-anchor="end">${Math.round(file.durationSec)}s</text>
                <text class="playback-axis-label" x="188" y="146" text-anchor="middle">time(s)</text>
                ${paths}
                <line class="playback-cursor" x1="${currentX.toFixed(1)}" y1="14" x2="${currentX.toFixed(1)}" y2="118"></line>
              </svg>
            </article>
          `;
        })
        .join("");
      if (!charts) {
        return `
          <section class="playback-signal-group">
            <h3>${escapeHtml(group.label)}</h3>
            <div class="playback-signal-list">${playbackEmptyCard("当前分组无数据", "该文件没有这个分组的 state/action 字段。")}</div>
          </section>
        `;
      }
      return `
        <section class="playback-signal-group">
          <h3>${escapeHtml(group.label)}</h3>
          <div class="playback-signal-list">${charts}</div>
        </section>
      `;
    })
    .join("");
}

async function requestPlaybackAction(action, payload = {}) {
  const response = await fetch(`/api/playback/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
  let result = {};
  try {
    result = await response.json();
  } catch (error) {
    result = {};
  }
  if (!response.ok || result.ok === false) {
    throw new Error(result.detail || result.error || `HTTP ${response.status}`);
  }
  return result;
}

function applyPlaybackStatus(payload) {
  if (!payload || payload.ok === false) return;
  state.playback.status = payload.status || state.playback.status || "idle";
  state.playback.running = Boolean(payload.running);
  state.playback.robotEnabled = Boolean(payload.robotEnabled);
  if (Number.isFinite(Number(payload.elapsedSec))) {
    state.playback.elapsedSec = Math.max(0, Number(payload.elapsedSec));
  }
  if (Number.isFinite(Number(payload.durationSec)) && Number(payload.durationSec) > 0) {
    state.playback.durationSec = Number(payload.durationSec);
  }
  if (payload.currentFrameIndex !== null && payload.currentFrameIndex !== undefined) {
    state.playback.currentFrameIndex = Number(payload.currentFrameIndex) || 0;
  }
  state.playback.lastError = payload.lastError || "";
}

function setPlaybackStatusPolling(active) {
  window.clearInterval(state.playbackTimer);
  state.playbackTimer = null;
  if (!active) return;
  state.playbackTimer = window.setInterval(() => {
    refreshPlaybackStatus({ silent: true });
  }, playbackTickMs * 3);
}

async function refreshPlaybackStatus(options = {}) {
  try {
    const response = await fetch("/api/playback/status", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || payload.ok === false) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    applyPlaybackStatus(payload);
    if (!state.playback.running) {
      setPlaybackStatusPolling(false);
    }
    renderPlayback();
    return payload;
  } catch (error) {
    if (!options.silent) addLog("数采", `数据回放状态同步失败：${error.message}`);
    return null;
  }
}

function renderPlaybackExecution() {
  const enableButton = $("#playbackEnableRobotButton");
  const replayButton = $("#playbackReplayButton");
  const stopButton = $("#playbackStopButton");
  const speedInput = $("#playbackJointSpeedInput");

  if (enableButton) enableButton.textContent = state.playback.robotEnabled ? "取消回放使能" : "机器人使能";
  if (enableButton) enableButton.disabled = state.playback.busy;
  if (replayButton) replayButton.disabled = !state.playback.robotEnabled || state.playback.running || state.playback.loading || state.playback.busy || !String(state.playback.path || "").trim();
  if (stopButton) stopButton.disabled = !state.playback.running || state.playback.busy;
  if (speedInput) speedInput.disabled = state.playback.running || state.playback.busy;

  const status = state.playback.loading
    ? "数据加载中"
    : state.playback.busy
    ? "指令处理中"
    : state.playback.running
    ? "数据回放中"
    : state.playback.lastError
    ? state.playback.lastError
    : state.playback.robotEnabled
      ? "机器人已使能"
      : "机器人未使能";
  setText("#playbackExecutionStatus", status);
  setStateBadge(
    "#playbackSourceBadge",
    state.playback.loading ? "加载中" : state.playback.running ? "回放中" : state.playback.robotEnabled ? "已使能" : "未使能",
    state.playback.loading || state.playback.running ? "warn" : state.playback.robotEnabled ? "ok" : "idle",
  );
}

function setPlaybackRunning(running) {
  state.playback.running = running;
  setPlaybackStatusPolling(running);
  state.playback.lastTickMs = null;
  renderPlayback();
}

function playbackCurrentFrame(seconds) {
  const frames = state.playback.dataset?.frames || [];
  if (!frames.length) return null;
  let low = 0;
  let high = frames.length - 1;
  while (low < high) {
    const mid = Math.ceil((low + high) / 2);
    if (frames[mid].seconds <= seconds) low = mid;
    else high = mid - 1;
  }
  state.playback.currentFrameIndex = low;
  return frames[low];
}

function renderPlayback() {
  const file = currentPlaybackFile();
  state.playback.durationSec = file.durationSec;
  state.playback.elapsedSec = clamp(state.playback.elapsedSec, 0, file.durationSec);
  const frame = playbackCurrentFrame(state.playback.elapsedSec);

  const progress = $("#playbackProgressBar");
  if (progress) {
    progress.style.width = `${(state.playback.elapsedSec / Math.max(1, file.durationSec)) * 100}%`;
  }

  setText("#playbackSummary", file.name);
  setText("#playbackTimeLabel", `${formatPlaybackTime(state.playback.elapsedSec)} / ${formatPlaybackTime(file.durationSec)}`);
  setStateBadge("#playbackBadge", state.playback.running ? "回放中" : state.playback.robotEnabled ? "已使能" : "待使能", state.playback.running ? "warn" : state.playback.robotEnabled ? "ok" : "idle");

  const fileInfo = $("#playbackFileInfo");
  if (fileInfo) {
    fileInfo.innerHTML = [
      ["数据文件", file.name],
      ["格式", file.sourceType || "unknown"],
      ["时长", formatPlaybackTime(file.durationSec)],
      ["时间", `${formatPlaybackTime(state.playback.elapsedSec)} / ${formatPlaybackTime(file.durationSec)}`],
      ["数据点", `${file.rows}`],
      ["State", file.loaded ? `${file.stateDim} 维` : "--"],
      ["Action", file.loaded ? `${file.actionDim} 维` : "--"],
      ["当前帧", frame ? `${frame.frameIndex}` : "--"],
      ["关节速度", `${formatNumber(state.playback.maxJointSpeedDegS, 1)} deg/s`],
      ["状态", state.playback.loadError ? state.playback.loadError : file.loaded ? "已加载 state/action" : "等待加载"],
    ]
      .map(([label, value]) => `<div class="metric-card"><span>${label}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");
  }

  renderPlaybackExecution();
  renderPlaybackJointSpeedInput();
  renderPlaybackCharts();
}

async function togglePlaybackRobotEnable() {
  if (state.playback.busy) return;
  const enabled = !state.playback.robotEnabled;
  state.playback.busy = true;
  state.playback.lastError = "";
  renderPlayback();
  try {
    if (!enabled && state.playback.running) {
      await requestPlaybackAction("stop");
      setPlaybackRunning(false);
    }
    const result = await requestPlaybackAction("enable", { enabled, repeat: 3, intervalMs: 80 });
    state.playback.robotEnabled = Boolean(result.robotEnabled);
    state.playback.status = enabled ? "idle" : "stopped";
    if (enabled && $("#enableStatus")) {
      $("#enableStatus").textContent = enabled ? "已使能" : "未使能";
      $("#enableStatus").className = enabled ? "status-pill ok" : "status-pill idle";
    }
    addLog("数采", enabled ? "数据回放 Piper 使能已打开" : "数据回放已取消，Piper 保持使能");
    await refreshPlaybackStatus({ silent: true });
  } catch (error) {
    state.playback.lastError = error.message;
    addLog("数采", `数据回放使能切换失败：${error.message}`);
  } finally {
    state.playback.busy = false;
    renderPlayback();
  }
}

async function startPlaybackRun() {
  if (!state.playback.robotEnabled) {
    addLog("数采", "数据回放未启动：机器人未使能");
    renderPlayback();
    return;
  }
  if (!String(state.playback.path || "").trim()) {
    addLog("数采", "数据回放未启动：未选择数据文件");
    return;
  }
  if (state.playback.busy) return;
  const playbackSpeedInput = $("#playbackJointSpeedInput");
  const maxJointSpeedDegS = playbackSpeedInput ? updatePlaybackJointSpeedFromInput(playbackSpeedInput) : state.playback.maxJointSpeedDegS;
  state.playback.busy = true;
  state.playback.lastError = "";
  renderPlayback();
  const dataset = await ensurePlaybackDataset();
  if (!dataset) {
    state.playback.busy = false;
    renderPlayback();
    return;
  }
  const file = currentPlaybackFile();
  try {
    const result = await requestPlaybackAction("start", {
      path: state.playback.path,
      maxJointSpeedDegS,
    });
    state.playback.elapsedSec = 0;
    state.playback.durationSec = Number(result.durationSec) || file.durationSec;
    state.playback.status = "running";
    addLog("数采", `数据回放开始：${file.name} / ${formatNumber(maxJointSpeedDegS, 1)} deg/s`);
    setPlaybackRunning(true);
    await refreshPlaybackStatus({ silent: true });
  } catch (error) {
    state.playback.lastError = error.message;
    addLog("数采", `数据回放启动失败：${error.message}`);
  } finally {
    state.playback.busy = false;
    renderPlayback();
  }
}

async function stopPlaybackRun() {
  if (state.playback.busy) return;
  const file = currentPlaybackFile();
  state.playback.busy = true;
  renderPlayback();
  try {
    await requestPlaybackAction("stop");
    setPlaybackRunning(false);
    await refreshPlaybackStatus({ silent: true });
    addLog("数采", `数据回放停止：${file.name}`);
  } catch (error) {
    state.playback.lastError = error.message;
    addLog("数采", `数据回放停止失败：${error.message}`);
  } finally {
    state.playback.busy = false;
    renderPlayback();
  }
}

function escapeHtml(value) {
  return String(value)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

function positionTooltip(anchor) {
  const tooltip = $("#richTooltip");
  const rect = anchor.getBoundingClientRect();
  const width = 320;
  const left = rect.right + width + 24 < window.innerWidth ? rect.right + 12 : Math.max(12, rect.left - width - 12);
  const top = Math.min(window.innerHeight - 170, Math.max(12, rect.top));
  tooltip.style.left = `${left}px`;
  tooltip.style.top = `${top}px`;
}

function showRichTooltip(anchor, payload) {
  const tooltip = $("#richTooltip");
  tooltip.innerHTML = `
    <strong>${escapeHtml(payload.title)}</strong>
    <dl>
      <div><dt>代码</dt><dd>${escapeHtml(payload.code)}</dd></div>
      <div><dt>时间</dt><dd>${escapeHtml(payload.time)}</dd></div>
    </dl>
    <p>${escapeHtml(payload.detail)}</p>
    <small>${escapeHtml(payload.advice)}</small>
  `;
  positionTooltip(anchor);
  tooltip.classList.add("is-visible");
  tooltip.setAttribute("aria-hidden", "false");
}

function hideRichTooltip() {
  const tooltip = $("#richTooltip");
  tooltip.classList.remove("is-visible");
  tooltip.setAttribute("aria-hidden", "true");
}

function showCheckTooltip(row) {
  showRichTooltip(row, {
    title: row.dataset.tooltipTitle,
    code: row.dataset.tooltipCode,
    time: row.dataset.tooltipTime,
    detail: row.dataset.tooltipDetail,
    advice: row.dataset.tooltipAdvice,
  });
}

function showAlertTooltip(anchor) {
  const detail = state.alerts.map((alert) => `${alert.title}`).join(" / ") || "当前无告警";
  const advice = state.alerts[0] ? state.alerts[0].detail : "系统暂无需要处理的告警。";
  showRichTooltip(anchor, {
    title: `当前告警 ${state.alerts.length}`,
    code: state.alerts.length ? "ALERT-W-ACTIVE" : "ALERT-OK",
    time: formatTime(),
    detail,
    advice,
  });
}

function confirmAction(title, body) {
  const dialog = $("#confirmDialog");
  $("#confirmTitle").textContent = title;
  $("#confirmBody").textContent = body;
  dialog.showModal();
  return new Promise((resolve) => {
    dialog.addEventListener(
      "close",
      () => {
        resolve(dialog.returnValue === "confirm");
      },
      { once: true },
    );
  });
}

function normalizeCheckResult(payload, fallback) {
  const result = Object.assign({}, fallback, payload || {});
  result.metric = Object.assign({}, fallback.metric, (payload && payload.metric) || {});
  result.name = result.name || fallback.name;
  result.status = result.status || "错误";
  result.source = result.source || fallback.source;
  result.code = result.code || fallback.code;
  result.advice = result.advice || fallback.advice;
  result.detail = result.detail || fallback.detail;
  result.checkedAt = result.checkedAt || formatTime();
  return result;
}

function backendUnavailableResult(error, fallback, label) {
  return normalizeCheckResult(
    {
      status: "错误",
      code: fallback.code.replace("000", "API"),
      advice: "请确认 bash run.sh 启动的是 Robot Station 后端服务，而不是旧的静态文件服务器。",
      detail: `无法请求本地后端 ${label} 自检接口：${error.message}`,
      checkedAt: formatTime(),
      metric: { ...fallback.metric, value: "后端不可达", percent: 8, level: "danger" },
    },
    fallback,
  );
}

async function fetchSelfCheckApi(path, fallback, label) {
  try {
    const response = await fetch(path, { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    return normalizeCheckResult(await response.json(), fallback);
  } catch (error) {
    return backendUnavailableResult(error, fallback, label);
  }
}

function fetchRosDaemonCheck() {
  return fetchSelfCheckApi("/api/self-check/ros-daemon", selfCheckItems[0], "ROS2 daemon");
}

function fetchCanInterfaceCheck(options = {}) {
  const params = new URLSearchParams();
  if (options.autoActivate !== undefined) {
    params.set("auto_activate", options.autoActivate ? "1" : "0");
  }
  const query = params.toString();
  const path = `/api/self-check/can-interface${query ? `?${query}` : ""}`;
  return fetchSelfCheckApi(path, selfCheckItems[2], "CAN 接口");
}

function fetchDiskSpaceCheck() {
  return fetchSelfCheckApi("/api/self-check/disk-space", selfCheckItems[7], "磁盘空间");
}

function fetchGpuStatusCheck() {
  return fetchSelfCheckApi("/api/self-check/gpu-status", selfCheckItems[8], "GPU 可用性");
}

function buildUnimplementedCheckResult(item, index, checkedAt) {
  return {
    ...item,
    status: "错误",
    advice: "该自检项尚未实现，请先实现对应 modules/self_check 检查逻辑。",
    code: item.code.replace("000", "TODO"),
    detail: `${item.name} 还没有接入真实自检逻辑，当前结果用于标记待开发能力。`,
    checkedAt,
    metric: {
      ...item.metric,
      value: "未实现",
      percent: 0,
      level: "danger",
    },
    implemented: false,
    order: index,
  };
}

function countCheckStatuses(results) {
  return results.reduce(
    (acc, item) => {
      acc[statusClass(item.status)] += 1;
      return acc;
    },
    { ok: 0, warn: 0, danger: 0, idle: 0 },
  );
}

function updateRosTopbar(rosResult) {
  const level = statusClass(rosResult.status);
  renderStatusSwitch("#rosStatus", "ROS", level, {
    readonly: true,
    title: level === "ok" ? "ROS 在线" : level === "warn" ? "ROS 警告" : "ROS 错误",
  });
}

function currentCanCheckResult() {
  return state.selfCheckResults.find((item) => item.name === "CAN 接口") || selfCheckItems[2];
}

function updateCanTopbar(canResult) {
  const ready = canResult.status === "正常";
  const busy = state.canActivation.busy;
  const level = busy ? "warn" : statusClass(canResult.status);
  renderStatusSwitch("#canStatus", "CAN", level, {
    readonly: ready || busy,
    busy,
    pressed: ready,
    title: busy ? "CAN 激活中" : ready ? "CAN 已激活" : "点击激活 CAN",
  });
}

function updateSingleSelfCheckResult(result) {
  const items = state.selfCheckResults.length ? cloneCheckItems(state.selfCheckResults) : cloneCheckItems(selfCheckItems);
  const index = items.findIndex((item) => item.name === result.name);
  if (index === -1) return;
  items[index] = normalizeCheckResult(result, items[index]);
  renderSelfCheck(items);
}

async function refreshCanInterfaceStatus(options = {}) {
  const canResult = await fetchCanInterfaceCheck({ autoActivate: false });
  updateSingleSelfCheckResult(canResult);
  updateCanTopbar(canResult);
  if (!options.silent) {
    addLog("系统", `CAN 状态查看：${canResult.status} / ${canResult.code}`);
  }
  return canResult;
}

async function activateCanInterface(item = currentCanCheckResult(), options = {}) {
  if (state.canActivation.busy || item.status === "正常") return;
  const can = item.can || {};
  const targets = can.requestedTargets || ["can_left", "can_right", "can_chassis"];
  const bitrate = can.expectedBitrate || 1000000;
  const expectedBitrates = can.expectedBitrates || {};
  const targetSummary = targets
    .map((target) => `${target}/${expectedBitrates[target] || bitrate}`)
    .join(" / ");
  if (options.confirm !== false) {
    const ok = await confirmAction(
      "激活 CAN",
      `将使用 sudo -n 修复 ${targetSummary}。该动作会修改系统 CAN 网络接口状态。`,
    );
    if (!ok) return;
  }

  addLog("系统", `尝试激活 CAN：${targetSummary}`);
  state.canActivation.busy = true;
  updateCanTopbar(item);
  try {
    const response = await fetch("/api/actions/can/activate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({}),
    });
    const payload = await response.json();
    addLog("系统", `CAN 激活结果：${payload.code} / ${payload.ok ? "成功" : "失败"}`);
    if (!payload.ok) {
      state.alerts.unshift({
        level: "danger",
        title: "CAN 激活失败",
        detail: payload.advice || payload.detail || "请检查 sudo 权限和 CAN 设备状态。",
      });
      renderAdvice();
    }
  } catch (error) {
    addLog("系统", `CAN 激活 API 请求失败：${error.message}`);
  } finally {
    await runSelfCheck();
    state.canActivation.busy = false;
    updateCanTopbar(currentCanCheckResult());
  }
}

async function runSelfCheck() {
  setStateBadge("#selfCheckBadge", "检查中", "warn");
  $("#selfCheckSummary").textContent = "正在检查设备状态";
  addLog("系统", "开始整机自检");

  state.selfCheckRanAt = new Date();
  const checkedAt = formatTime(state.selfCheckRanAt);
  const [rosResult, canResult, diskResult, gpuResult] = await Promise.all([
    fetchRosDaemonCheck(),
    fetchCanInterfaceCheck(),
    fetchDiskSpaceCheck(),
    fetchGpuStatusCheck(),
  ]);
  const unimplementedResults = [
    buildUnimplementedCheckResult(selfCheckItems[1], 1, checkedAt),
    ...selfCheckItems.slice(3, 7).map((item, offset) => buildUnimplementedCheckResult(item, offset + 3, checkedAt)),
  ];
  const results = [
    rosResult,
    unimplementedResults[0],
    canResult,
    ...unimplementedResults.slice(1),
    diskResult,
    gpuResult,
  ];
  const counts = countCheckStatuses(results);
  const badgeLevel = counts.danger ? "danger" : counts.warn ? "warn" : "ok";
  const badgeText = counts.danger ? "有错误" : counts.warn ? "有警告" : "正常";

  renderSelfCheck(results);
  $("#selfCheckAge").textContent = "刚刚";
  $("#selfCheckSummary").textContent = `自检完成：${counts.ok} 正常，${counts.warn} 警告，${counts.danger} 错误`;
  setStateBadge("#selfCheckBadge", badgeText, badgeLevel);
  updateRosTopbar(rosResult);
  updateCanTopbar(canResult);
  state.alerts = [];
  if (rosResult.status !== "正常") {
    state.alerts.push({
      level: statusClass(rosResult.status),
      title: `${rosResult.name} ${rosResult.status}`,
      detail: rosResult.advice,
    });
  }
  [canResult, diskResult, gpuResult].forEach((result) => {
    if (result.status !== "正常") {
      state.alerts.push({
        level: statusClass(result.status),
        title: `${result.name} ${result.status}`,
        detail: result.advice,
      });
    }
  });
  state.alerts.push({
    level: "danger",
    title: "存在未实现自检项",
    detail: `${unimplementedResults.length} 个自检项暂未接入真实检查逻辑，当前统一标记为错误。`,
  });
  renderAdvice();
  addLog("ROS", `ROS2 daemon 自检：${rosResult.status} / ${rosResult.code}`);
  addLog("系统", `CAN 接口自检：${canResult.status} / ${canResult.code}`);
  addLog("系统", `磁盘空间自检：${diskResult.status} / ${diskResult.code}`);
  addLog("系统", `GPU 可用性自检：${gpuResult.status} / ${gpuResult.code}`);
  addLog("系统", `整机自检完成：${counts.ok} 正常，${counts.warn} 警告，${counts.danger} 错误`);
}

function rerunProblemChecks() {
  const problems = state.selfCheckResults.filter((item) => item.status === "警告" || item.status === "错误");
  if (!problems.length) {
    addLog("系统", "复查异常项：当前没有异常项");
    return;
  }
  problems.forEach((item) => addLog(item.source, `复查异常项：${item.name}，结果仍需确认`));
  $("#selfCheckSummary").textContent = `已复查 ${problems.length} 个异常项，建议按提示处理后再次执行一键检查`;
}

async function startHoming() {
  if (state.task !== "idle") return;
  if (!piperReady()) {
    addLog("机械臂", "归位未启动：Piper 控制节点未运行");
    showView("device-control");
    return;
  }
  const ok = await confirmAction("开始机器人归位", "归位会使能机械臂并移动到 home。请确认机械臂和底盘周围安全。");
  if (!ok) return;

  setTask("homing", "归位流程", "归位中");
  setStateBadge("#homingBadge", "运行中", "warn");
  setStateBadge("#stateBadge", "运行中", "warn");
  setText("#taskSubtitle", "正在执行归位准备");
  setText("#homingSummary", "归位流程正在执行");
  renderHomeFlow(homingSteps, 0, 8);
  addLog("机械臂", "归位流程启动");

  let index = 0;
  window.clearInterval(state.homingTimer);
  state.homingTimer = window.setInterval(() => {
    renderHomingSteps(index);
    renderHomeFlow(homingSteps, index, Math.round(((index + 1) / homingSteps.length) * 100));
    addLog(index < 4 ? "机械臂" : "系统", `归位步骤完成：${homingSteps[index]}`);
    index += 1;
    if (index >= homingSteps.length) {
      window.clearInterval(state.homingTimer);
      renderHomingSteps(homingSteps.length);
      renderHomeFlow(["确认安全", "使能与回零", "传感器确认", "归位完成"], 3, 100);
      setTask("idle", "空闲", "空闲");
      setStateBadge("#homingBadge", "完成", "ok");
      setStateBadge("#stateBadge", "完成", "ok");
      setText("#taskSubtitle", "最近任务：归位完成");
      setText("#homingSummary", "归位完成，机器人处于准备状态");
      $("#enableStatus").textContent = "已使能";
      $("#enableStatus").className = "status-pill ok";
      addLog("系统", "归位流程完成");
    }
  }, 700);
}

async function startCollection() {
  if (state.task !== "idle") return;
  if (!piperReady()) {
    addLog("数采", "采集未启动：Piper 控制节点未运行");
    showView("device-control");
    return;
  }
  const ok = await confirmAction("开始自动数采", "开始后会占用机器人控制权，并持续记录相机、LiDAR、底盘和机械臂状态。");
  if (!ok) return;
  state.collectionSeconds = 0;
  setTask("collection", "数采任务", "数采中");
  setStateBadge("#collectionBadge", "采集中", "warn");
  setStateBadge("#stateBadge", "运行中", "warn");
  $("#collectionSummary").textContent = "episode_043 正在采集";
  setText("#taskSubtitle", "正在采集 episode_043");
  renderHomeFlow(["创建 episode", "记录传感器", "监控质量", "等待结束"], 1, 35);
  renderCollectionMetrics();
  addLog("数采", "开始采集 episode_043");
  window.clearInterval(state.collectionTimer);
  state.collectionTimer = window.setInterval(() => {
    state.collectionSeconds += 1;
    renderCollectionMetrics();
    renderHomeFlow(["创建 episode", "记录传感器", "监控质量", "等待结束"], 2, Math.min(92, 35 + state.collectionSeconds * 4));
  }, 1000);
}

function pauseCollection() {
  if (state.task !== "collection") return;
  window.clearInterval(state.collectionTimer);
  setTask("collection-paused", "数采任务暂停", "数采暂停");
  setStateBadge("#collectionBadge", "暂停", "idle");
  $("#collectionSummary").textContent = "采集已暂停";
  addLog("数采", "采集暂停");
}

function finishCollection(result = "完成") {
  if (state.task !== "collection" && state.task !== "collection-paused") return;
  window.clearInterval(state.collectionTimer);
  setTask("idle", "空闲", "空闲");
  setStateBadge("#collectionBadge", result, result === "失败" ? "danger" : "ok");
  $("#collectionSummary").textContent = `episode_043 ${result}`;
  renderHomeFlow(["创建 episode", "记录传感器", "质量摘要", "采集完成"], 3, 100);
  addLog("数采", `episode_043 ${result}`);
}

function readMappingSettings() {
  const frameCount = clamp(Math.round(Number($("#mappingFrameCountInput")?.value) || state.mapping.frameCount || 10), 1, 200);
  const cloudTopic = String($("#mappingCloudTopicInput")?.value || state.mapping.cloudTopic || "/rslidar_points").trim() || "/rslidar_points";
  const odomTopic = String($("#mappingOdomTopicInput")?.value || state.mapping.odomTopic || "/odom").trim() || "/odom";
  const baseFrame = String($("#mappingBaseFrameInput")?.value || state.mapping.baseFrame || "base_link").trim() || "base_link";
  return { frameCount, cloudTopic, odomTopic, baseFrame };
}

function applyMappingStatus(result = {}) {
  const session = result.session || null;
  state.mapping.session = session;
  state.mapping.busy = Boolean(result.busy || session?.busy);
  state.mapping.status = session?.status || "idle";
  state.mapping.lastError = session?.lastError || (!result.ok ? result.detail || result.code || "" : "");
  const settings = session?.settings;
  if (settings) {
    state.mapping.frameCount = Number(settings.frameCount) || state.mapping.frameCount;
    state.mapping.cloudTopic = settings.cloudTopic || state.mapping.cloudTopic;
    state.mapping.odomTopic = settings.odomTopic || state.mapping.odomTopic;
    state.mapping.baseFrame = settings.baseFrame || state.mapping.baseFrame;
  }
  syncMappingMapPreview();
  updateRobotModelTransforms();
  renderMappingStatus();
  renderRobotViewStatus();
  if (state.mapping.busy) {
    scheduleMappingStatusPoll(700);
  } else {
    window.clearTimeout(state.mapping.captureTimer);
    state.mapping.captureTimer = null;
  }
}

async function mappingPost(action, payload = {}) {
  const response = await fetch(`/api/mapping/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
  const result = await response.json().catch(() => ({}));
  applyMappingStatus(result);
  return { response, result };
}

async function refreshMappingStatus(options = {}) {
  try {
    const response = await fetch("/api/mapping/status", { cache: "no-store" });
    const result = await response.json();
    applyMappingStatus(result);
    return result;
  } catch (error) {
    if (!options.silent) addLog("建图", `状态刷新失败：${error.message}`);
    return null;
  }
}

function scheduleMappingStatusPoll(delayMs = 1000) {
  window.clearTimeout(state.mapping.captureTimer);
  state.mapping.captureTimer = window.setTimeout(() => refreshMappingStatus({ silent: true }), delayMs);
}

async function startMappingSession() {
  if (state.mapping.busy) return;
  const hasSession = Boolean(state.mapping.session);
  const ok = await confirmAction(
    hasSession ? "重建点云地图" : "新建点云地图",
    hasSession
      ? "重建会清空当前建图会话和所有 tmp 临时文件，然后创建新的空白会话。已保存的 .pcd 地图不会删除。"
      : "新建会清空过去的 tmp 临时建图文件，然后创建新的空白会话。已保存的 .pcd 地图不会删除。",
  );
  if (!ok) return;
  const settings = readMappingSettings();
  state.mapping.status = "ready";
  state.mapping.busy = true;
  clearMappingMapPreview();
  renderMappingStatus();
  try {
    const { result } = await mappingPost("start", settings);
    const removed = Number(result.tempCleanup?.removed || 0);
    addLog("建图", result.ok ? `建图会话已创建，已清理 ${removed} 项 tmp` : `建图启动失败：${result.detail || result.code}`);
  } catch (error) {
    addLog("建图", `建图启动失败：${error.message}`);
  } finally {
    await refreshMappingStatus({ silent: true });
  }
}

async function captureMappingKeyframe() {
  if (!state.mapping.session) {
    await startMappingSession();
    if (!state.mapping.session) return;
  }
  const settings = readMappingSettings();
  state.mapping.busy = true;
  state.mapping.status = "capturing";
  renderMappingStatus();
  try {
    const { result } = await mappingPost("capture", settings);
    addLog("建图", result.ok ? `开始采集 ${settings.frameCount} 帧点云` : `采集启动失败：${result.detail || result.code}`);
  } catch (error) {
    addLog("建图", `采集启动失败：${error.message}`);
  } finally {
    scheduleMappingStatusPoll(700);
  }
}

async function saveMappingMap() {
  if (!state.mapping.session) return;
  const name = `${state.mapping.session.id || "mapping"}.pcd`;
  try {
    const { result } = await mappingPost("save", { name });
    addLog("建图", result.ok ? `地图已保存：${result.path || name}` : `保存失败：${result.detail || result.code}`);
  } catch (error) {
    addLog("建图", `保存失败：${error.message}`);
  }
}

async function deleteLastMappingKeyframe() {
  const session = state.mapping.session;
  const keyframes = Array.isArray(session?.keyframes) ? session.keyframes : [];
  if (!session || !keyframes.length || state.mapping.busy || !session.canDeleteLast) return;

  const lastKeyframe = keyframes[keyframes.length - 1] || {};
  const index = Number(lastKeyframe.index);
  const label = Number.isFinite(index) ? `#${index}` : "上一帧";
  const ok = await confirmAction(
    "删除上一帧点云",
    `将从当前临时地图移除 keyframe ${label}，并回退建图状态。删除后不可恢复，但可以继续删除更早的 keyframe。`,
  );
  if (!ok) return;

  try {
    const { result } = await mappingPost("delete-last", {});
    const deletedIndex = result.deletedKeyframe?.index;
    const deletedLabel = deletedIndex !== undefined && deletedIndex !== null ? `#${deletedIndex}` : label;
    addLog("建图", result.ok ? `已删除上一帧 keyframe ${deletedLabel}` : `删除失败：${result.detail || result.code}`);
  } catch (error) {
    addLog("建图", `删除失败：${error.message}`);
  } finally {
    await refreshMappingStatus({ silent: true });
  }
}

async function resetMappingSession() {
  const ok = await confirmAction(
    "重置点云建图",
    "重置会停止当前建图会话，并清空所有 tmp 临时建图文件。已保存的 .pcd 地图不会删除。",
  );
  if (!ok) return;
  window.clearTimeout(state.mapping.captureTimer);
  state.mapping.captureTimer = null;
  try {
    const { result } = await mappingPost("reset", { clearTmp: true });
    const removed = Number(result.tempCleanup?.removed || 0);
    addLog("建图", result.ok ? `建图会话已重置，已清理 ${removed} 项 tmp` : `重置失败：${result.detail || result.code}`);
  } catch (error) {
    addLog("建图", `重置失败：${error.message}`);
  } finally {
    state.mapping.session = null;
    state.mapping.status = "idle";
    state.mapping.busy = false;
    clearMappingMapPreview();
    renderMappingStatus();
  }
}

async function ensureLocalizationRobotModel() {
  if (!state.robotModel.models.length) {
    await fetchRobotModels({ silent: true });
  }
  const defaultModel = state.robotModel.models.find((model) => model.key === localizationDefaultModelKey) || state.robotModel.models[0] || null;
  if (defaultModel) state.robotModel.selectedKey = defaultModel.key;
  const initialized = await initializeRobotViewer();
  if (!initialized) {
    renderLocalizationStatus();
    return null;
  }
  syncRobotViewerMount();
  syncRobotViewerLayersForView();
  if (defaultModel && (!state.robotModel.hasModel || state.robotModel.loadedKey !== defaultModel.key)) {
    const model = await loadRobotModel(defaultModel.key);
    syncRobotViewerMount();
    syncRobotViewerLayersForView();
    updateRobotModelTransforms();
    renderLocalizationStatus();
    return model;
  }
  updateRobotModelTransforms();
  renderLocalizationStatus();
  return state.robotModel.metadata || defaultModel;
}

async function fetchLocalizationMaps(options = {}) {
  const localization = state.localization;
  if (localization.mapsLoading) return null;
  localization.mapsLoading = true;
  localization.lastError = "";
  renderLocalizationStatus();
  try {
    const response = await fetch("/api/localization/maps", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !payload.ok || !Array.isArray(payload.maps)) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }

    localization.maps = payload.maps;
    const selectedStillExists = localization.maps.some((entry) => entry.name === localization.selectedMapName);
    let nextSelected = selectedStillExists ? localization.selectedMapName : "";
    if (!nextSelected && localization.maps.length === 1) {
      nextSelected = localization.maps[0].name;
    }
    localization.mapsLoading = false;
    localization.lastError = "";
    if (nextSelected !== localization.selectedMapName) {
      await selectLocalizationMap(nextSelected, { silent: options.silent });
    } else {
      localization.selectedMap = localizationSelectedMap();
      renderLocalizationStatus();
    }
    return payload;
  } catch (error) {
    localization.mapsLoading = false;
    localization.maps = [];
    localization.lastError = error.message;
    clearLocalizationMapPreview();
    if (!options.silent) addLog("定位", `地图列表读取失败：${error.message}`);
    renderLocalizationStatus();
    return null;
  }
}

async function selectLocalizationMap(name, options = {}) {
  const localization = state.localization;
  const nextName = String(name || "").trim();
  const previousName = localization.selectedMapName;
  localization.selectedMapName = nextName;
  localization.selectedMap = localizationSelectedMap();
  localization.lastError = "";
  if (previousName !== nextName) {
    clearLocalizationMapPreview();
    if (state.localizationRuntime.status === "running") {
      setLocalizationRuntime("stopped");
      addLog("定位", "地图已切换，Loc 已停止");
    }
  }
  renderLocalizationStatus();
  if (!nextName) return null;
  if (!options.silent && previousName !== nextName) addLog("定位", `已选择地图：${nextName}`);
  return requestLocalizationMapFrame(nextName);
}

function toggleLocalizationRuntime() {
  if (state.localizationRuntime.status === "running") {
    setLocalizationRuntime("stopped");
    addLog("定位", "Loc 已停止");
    return;
  }
  if (!state.localization.selectedMapName) {
    addLog("定位", "请先在定位页面选择地图");
    showView("localization");
    renderLocalizationStatus();
    return;
  }
  setLocalizationRuntime("running");
  addLog("定位", `Loc 已开启：${state.localization.selectedMapName}（真实定位服务待接入）`);
}

async function inferencePost(action, payload = {}) {
  const response = await fetch(`/api/inference/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
  const result = await response.json().catch(() => ({}));
  applyInferenceStatus(result);
  return { response, result };
}

async function refreshInferenceStatus() {
  try {
    const response = await fetch("/api/inference/status", { cache: "no-store" });
    const result = await response.json();
    applyInferenceStatus(result);
    return { ok: true, status: response.status };
  } catch (error) {
    // Keep the last known state if the status poll fails.
    return {
      ok: false,
      error: error.message,
    };
  }
}

function readInferenceExecuteParams() {
  const steps = clamp(Math.round(Number($("#inferenceStepsInput").value) || 1), 1, 200);
  const frequencyHz = clamp(Number($("#inferenceFrequencyInput").value) || 10, 1, 30);
  const maxJointSpeedDegS = clamp(Number($("#inferenceJointSpeedInput").value) || 20, 0.5, 30);
  return { steps, frequencyHz, maxJointSpeedDegS };
}

async function loadInferenceChassisLimits() {
  try {
    const response = await fetch("/api/control/chassis/limits", { cache: "no-store" });
    const result = await response.json();
    const limits = result && result.limits ? result.limits : null;
    if (!limits) return;
    state.inference.chassisHardLimits = {
      maxLinearMps: Number(limits.maxLinearMps) || 0.2,
      maxLateralMps: Number(limits.maxLateralMps) || 0.15,
      maxAngularRadS: Number(limits.maxAngularRadS) || 0.5,
    };
    const vxInput = $("#inferenceMaxVxInput");
    const vyInput = $("#inferenceMaxVyInput");
    const wzInput = $("#inferenceMaxWzInput");
    const hard = state.inference.chassisHardLimits;
    if (vxInput) {
      vxInput.max = hard.maxLinearMps;
      if (!vxInput.value) vxInput.value = hard.maxLinearMps;
    }
    if (vyInput) {
      vyInput.max = hard.maxLateralMps;
      if (!vyInput.value) vyInput.value = hard.maxLateralMps;
    }
    if (wzInput) {
      wzInput.max = hard.maxAngularRadS;
      if (!wzInput.value) wzInput.value = hard.maxAngularRadS;
    }
  } catch (error) {
    // Keep defaults if the limits endpoint is unavailable.
  }
}

function readInferenceChassisLimits() {
  const hard = state.inference.chassisHardLimits;
  const pick = (selector, ceiling) => {
    const raw = Number($(selector) && $(selector).value);
    if (!Number.isFinite(raw) || raw <= 0) return ceiling;
    return Math.min(raw, ceiling);
  };
  return {
    maxLinearMps: pick("#inferenceMaxVxInput", hard.maxLinearMps),
    maxLateralMps: pick("#inferenceMaxVyInput", hard.maxLateralMps),
    maxAngularRadS: pick("#inferenceMaxWzInput", hard.maxAngularRadS),
  };
}

function isMaskAllEnabled() {
  const m = state.inference.mask;
  return (
    m.left.enabled && m.left.joints.every(Boolean) && m.left.gripper &&
    m.right.enabled && m.right.joints.every(Boolean) && m.right.gripper &&
    m.lift && m.speed
  );
}

function setMaskAll(value) {
  const m = state.inference.mask;
  ["left", "right"].forEach((side) => {
    m[side].enabled = value;
    m[side].joints = m[side].joints.map(() => value);
    m[side].gripper = value;
  });
  m.lift = value;
  m.speed = value;
}

function describeMask() {
  const m = state.inference.mask;
  const off = [];
  ["left", "right"].forEach((side) => {
    const name = side === "left" ? "左臂" : "右臂";
    if (!m[side].enabled) {
      off.push(name);
      return;
    }
    m[side].joints.forEach((on, i) => {
      if (!on) off.push(`${name}J${i + 1}`);
    });
    if (!m[side].gripper) off.push(`${name}夹爪`);
  });
  if (!m.lift) off.push("升降台");
  if (!m.speed) off.push("速度");
  return off.length ? `已关闭 ${off.join("、")}` : "全部开启";
}

function renderInferenceMask() {
  const node = $("#inferenceMaskPanel");
  if (!node) return;
  const mask = state.inference.mask;
  const chip = (label, on, attrs, extra = "") =>
    `<button type="button" class="mask-chip ${on ? "is-on" : "is-off"} ${extra}" ${attrs}>${label}</button>`;
  const armRow = (side, name) => {
    const m = mask[side];
    const locked = m.enabled ? "" : "is-locked";
    const joints = m.joints
      .map((on, i) => chip(`J${i + 1}`, on, `data-mask="joint" data-side="${side}" data-joint="${i}"`, locked))
      .join("");
    const gripper = chip("夹爪", m.gripper, `data-mask="gripper" data-side="${side}"`, locked);
    return `
      <div class="mask-row">
        <div class="mask-row-head">
          <span class="mask-name">${name}</span>
          ${chip(m.enabled ? "开" : "关", m.enabled, `data-mask="side" data-side="${side}"`)}
        </div>
        <div class="mask-chips">${joints}${gripper}</div>
      </div>`;
  };
  const allOn = isMaskAllEnabled();
  node.innerHTML = `
    <div class="mask-header">
      <span class="mask-title">动作通道（关闭=保持不动）</span>
      <button type="button" class="mask-chip mask-global" data-mask="global">${allOn ? "全部关闭" : "全部开启"}</button>
    </div>
    ${armRow("left", "左臂")}
    ${armRow("right", "右臂")}
    <div class="mask-row simple">
      <span class="mask-name">升降台</span>
      ${chip(mask.lift ? "开" : "关", mask.lift, `data-mask="lift"`)}
    </div>
    <div class="mask-row simple">
      <span class="mask-name">速度</span>
      ${chip(mask.speed ? "开" : "关", mask.speed, `data-mask="speed"`)}
    </div>`;
}

function handleMaskClick(event) {
  const button = event.target.closest("[data-mask]");
  if (!button) return;
  const kind = button.dataset.mask;
  const mask = state.inference.mask;
  if (kind === "global") {
    setMaskAll(!isMaskAllEnabled());
  } else if (kind === "side") {
    mask[button.dataset.side].enabled = !mask[button.dataset.side].enabled;
  } else if (kind === "joint") {
    const side = button.dataset.side;
    if (!mask[side].enabled) return;
    const index = Number(button.dataset.joint);
    mask[side].joints[index] = !mask[side].joints[index];
  } else if (kind === "gripper") {
    const side = button.dataset.side;
    if (!mask[side].enabled) return;
    mask[side].gripper = !mask[side].gripper;
  } else if (kind === "lift") {
    mask.lift = !mask.lift;
  } else if (kind === "speed") {
    mask.speed = !mask.speed;
  } else {
    return;
  }
  renderInferenceMask();
  addLog("推理", `动作通道：${describeMask()}`);
}

async function enablePiperForInference() {
  if (!piperReady()) {
    addLog("推理", "Piper 使能失败：控制节点未运行");
    showView("device-control");
    return;
  }
  state.piperEnableBusy = true;
  renderInferenceStatus();
  try {
    await publishPiperEnable(true, { repeat: 3, intervalMs: 80 });
    $("#enableStatus").textContent = "已使能";
    $("#enableStatus").className = "status-pill ok";
    addLog("推理", "Piper 已使能，可执行 chunk");
  } catch (error) {
    addLog("推理", `Piper 使能失败：${error.message}`);
  } finally {
    state.piperEnableBusy = false;
    renderInferenceStatus();
  }
}

async function connectInference() {
  const url = String($("#remoteUrlInput").value || "").trim();
  if (!url) {
    addLog("推理", "连接失败：远端地址为空");
    return;
  }
  if (!piperReady()) {
    addLog("推理", "提示：Piper 控制节点未运行，执行前请先启动");
  }
  state.inference.busy = true;
  renderInferenceStatus();
  try {
    const { result } = await inferencePost("connect", { url });
    addLog("推理", result.ok ? `已连接远端：${url}` : `连接失败：${result.detail || result.code}`);
  } catch (error) {
    addLog("推理", `连接失败：${error.message}`);
  } finally {
    state.inference.busy = false;
    await refreshInferenceStatus();
  }
}

async function disconnectInference() {
  state.inference.looping = false;
  state.inference.busy = true;
  renderInferenceStatus();
  try {
    const { result } = await inferencePost("disconnect");
    addLog("推理", result.ok ? "已断开远端推理连接" : `断开失败：${result.detail || result.code}`);
  } catch (error) {
    addLog("推理", `断开失败：${error.message}`);
  } finally {
    state.inference.busy = false;
    if (state.task === "inference") setTask("idle", "空闲", "空闲");
    await refreshInferenceStatus();
    resumeBackgroundPollsNow();
  }
}

async function requestInferenceChunk(options = {}) {
  const refreshStatus = options.refreshStatus !== false;
  const writeLog = options.log !== false;
  if (!state.inference.connected) {
    addLog("推理", "请先连接远端推理服务");
    return;
  }
  const prompt = String($("#promptInput").value || "").trim();
  let result = null;
  state.inference.busy = true;
  renderInferenceStatus();
  try {
    const posted = await inferencePost("request-chunk", { prompt, chassisLimits: readInferenceChassisLimits() });
    result = posted.result;
    if (result.ok && writeLog) {
      const clipNote = result.clipped ? `，${result.clipped} 个值越限已裁剪` : "";
      addLog("推理", `收到 chunk ${result.chunkId}（${result.chunkSteps} 步）${clipNote}`);
    } else if (!result.ok) {
      addLog("推理", `请求 chunk 失败：${result.detail || result.code}`);
    }
  } catch (error) {
    addLog("推理", `请求 chunk 失败：${error.message}`);
  } finally {
    state.inference.busy = false;
    if (refreshStatus) {
      await refreshInferenceStatus();
    } else {
      renderInferenceStatus();
    }
  }
  return result;
}

async function executeInferenceChunk(options = {}) {
  const refreshStatus = options.refreshStatus !== false;
  const writeLog = options.log !== false;
  if (!state.inference.chunkId) {
    addLog("推理", "暂无可执行的 chunk");
    return null;
  }
  const params = readInferenceExecuteParams();
  params.mask = state.inference.mask;
  let result = null;
  state.inference.busy = true;
  renderInferenceStatus();
  try {
    const posted = await inferencePost("execute-chunk", params);
    result = posted.result;
    const last = $("#lastActionOutput");
    const executedSteps = result.executedSteps || 0;
    if (last) last.textContent = `最近执行：${executedSteps}/${params.steps} 步 @ ${params.frequencyHz} Hz，${params.maxJointSpeedDegS} deg/s`;
    if (writeLog || !result.ok) {
      addLog("推理", result.ok ? `执行 ${executedSteps} 步完成` : `执行结束：${result.detail || result.code}`);
    }
  } catch (error) {
    addLog("推理", `执行失败：${error.message}`);
  } finally {
    state.inference.busy = false;
    if (refreshStatus) {
      await refreshInferenceStatus();
    } else {
      renderInferenceStatus();
    }
  }
  return result;
}

async function runInferenceLoop() {
  setTask("inference", "推理任务", "推理中");
  let loopSeq = 0;
  while (state.inference.looping) {
    loopSeq += 1;
    const chunk = await requestInferenceChunk({ refreshStatus: false, log: false });
    if (!state.inference.looping) break;
    state.inference.loopTiming = { seq: loopSeq };
    if (!chunk || !chunk.ok) {
      renderInferenceStatus();
      state.inference.looping = false;
      const toggle = $("#inferenceLoopToggle");
      if (toggle) toggle.checked = false;
      break;
    }
    const executed = await executeInferenceChunk({ refreshStatus: false, log: false });
    renderInferenceStatus();
    if (!state.inference.looping) break;
    if (!executed || !executed.ok) {
      state.inference.looping = false;
      const toggle = $("#inferenceLoopToggle");
      if (toggle) toggle.checked = false;
      break;
    }
    addLog("推理", `闭环 #${loopSeq} 完成：${chunk.chunkId || "chunk"}，执行 ${executed.executedSteps || 0} 步`);
  }
  if (state.task === "inference") setTask("idle", "空闲", "空闲");
  renderInferenceStatus();
  resumeBackgroundPollsNow();
}

function toggleInferenceLoop(event) {
  const enabled = Boolean(event.currentTarget.checked);
  if (enabled && !state.inference.connected) {
    event.currentTarget.checked = false;
    addLog("推理", "请先连接远端推理服务再开启连续闭环");
    return;
  }
  state.inference.looping = enabled;
  renderInferenceStatus();
  if (enabled) {
    addLog("推理", "连续闭环已开启");
    runInferenceLoop();
  } else {
    addLog("推理", "连续闭环已关闭");
    resumeBackgroundPollsNow();
  }
}

async function stopInference() {
  state.inference.looping = false;
  const toggle = $("#inferenceLoopToggle");
  if (toggle) toggle.checked = false;
  try {
    const { result } = await inferencePost("stop");
    addLog("推理", result.ok ? "推理已停止，机器人进入安全保持" : `停止失败：${result.detail || result.code}`);
  } catch (error) {
    addLog("推理", `停止失败：${error.message}`);
  } finally {
    if (state.task === "inference") setTask("idle", "空闲", "空闲");
    await refreshInferenceStatus();
    resumeBackgroundPollsNow();
  }
}

async function stopCurrentTask() {
  if (state.task === "idle") {
    addLog("系统", "停止任务：当前空闲");
    return;
  }
  const ok = await confirmAction("停止当前任务", "停止会释放当前任务控制权，并让运动输出进入停止状态。");
  if (!ok) return;
  forceStopTask("操作员停止当前任务");
}

function forceStopTask(reason) {
  window.clearInterval(state.homingTimer);
  window.clearInterval(state.collectionTimer);
  window.clearInterval(state.inferenceTimer);
  window.clearTimeout(state.armControl.publishTimer);
  state.armControl.active = false;
  if (state.inference.looping || state.inference.connected) {
    state.inference.looping = false;
    const loopToggle = $("#inferenceLoopToggle");
    if (loopToggle) loopToggle.checked = false;
    stopInference();
  }
  setTask("idle", "空闲", "空闲");
  setStateBadge("#stateBadge", "停止", "idle");
  setText("#taskSubtitle", "当前任务已停止");
  requestPiperJointHold("停止输出");
  addLog("系统", reason);
  renderArmComparisons();
}

function triggerEmergencyStop() {
  $("#estopStatus").textContent = "急停触发";
  $("#estopStatus").className = "status-pill danger";
  state.alerts.unshift({
    level: "danger",
    title: "急停已触发",
    detail: "机器人动作输出应立即停止。恢复前请检查现场安全。",
  });
  renderAdvice();
  forceStopTask("急停触发，当前任务已强制停止");
  addLog("系统", "急停按钮触发");
}

async function startPiperRuntime() {
  if (state.piperRuntime.status === "running" || state.piperRuntime.status === "starting") return;
  await requestPiperRuntimeAction("start");
}

async function stopPiperRuntime() {
  if (state.piperRuntime.status === "stopped" || state.piperRuntime.status === "stopping") return;
  requestPiperJointHold("关闭 Piper");
  await requestPiperRuntimeAction("stop");
}

function togglePiperRuntime() {
  if (state.piperRuntime.status === "starting" || state.piperRuntime.status === "stopping") return;
  if (state.piperRuntime.status === "running" || state.piperRuntime.status === "external") {
    stopPiperRuntime();
    return;
  }
  startPiperRuntime();
}

function applyPiperServicePayload(payload) {
  const service = payload && payload.service;
  if (!service || !service.status) return false;
  setPiperRuntime(service.status);
  return true;
}

async function fetchPiperRuntimeStatus(options = {}) {
  try {
    const response = await fetch("/api/runtime/services/piper", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !applyPiperServicePayload(payload)) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    return payload;
  } catch (error) {
    if (!options.silent) {
      setPiperRuntime("error");
      addLog("机械臂", `Piper 状态查询失败：${error.message}`);
    }
    return null;
  }
}

function applyLiftingServicePayload(payload) {
  const service = payload && payload.service;
  if (!service || !service.status) return false;
  setLiftingRuntime(service.status);
  return true;
}

async function fetchLiftingRuntimeStatus(options = {}) {
  try {
    const response = await fetch("/api/runtime/services/lifting", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !applyLiftingServicePayload(payload)) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    return payload;
  } catch (error) {
    if (!options.silent) {
      setLiftingRuntime("error");
      addLog("升降轴", `升降轴状态查询失败：${error.message}`);
    }
    return null;
  }
}

function applyChassisServicePayload(payload) {
  const service = payload && payload.service;
  if (!service || !service.status) return false;
  setChassisRuntime(service.status);
  return true;
}

async function fetchChassisRuntimeStatus(options = {}) {
  try {
    const response = await fetch("/api/runtime/services/chassis", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !applyChassisServicePayload(payload)) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    return payload;
  } catch (error) {
    if (!options.silent) {
      setChassisRuntime("error");
      addLog("底盘", `Chassis 状态查询失败：${error.message}`);
    }
    return null;
  }
}

function applyCameraServicePayload(payload) {
  const service = payload && payload.service;
  if (!service || !service.status) return false;
  setCameraRuntime(service.status);
  return true;
}

async function fetchCameraRuntimeStatus(options = {}) {
  try {
    const response = await fetch("/api/runtime/services/camera", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !applyCameraServicePayload(payload)) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    return payload;
  } catch (error) {
    if (!options.silent) {
      setCameraRuntime("error");
      addLog("相机", `Camera 状态查询失败：${error.message}`);
    }
    return null;
  }
}

function applyLidarServicePayload(payload) {
  const service = payload && payload.service;
  if (!service || !service.status) return false;
  setLidarRuntime(service.status);
  return true;
}

async function fetchLidarRuntimeStatus(options = {}) {
  try {
    const response = await fetch("/api/runtime/services/lidar", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !applyLidarServicePayload(payload)) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    return payload;
  } catch (error) {
    if (!options.silent) {
      setLidarRuntime("error");
      addLog("LiDAR", `LiDAR 状态查询失败：${error.message}`);
    }
    return null;
  }
}

async function fetchLiftingLimits() {
  try {
    const response = await fetch("/api/control/lifting/limits", { cache: "no-store" });
    const payload = await response.json();
    if (response.ok && payload && payload.limits) {
      state.liftingState.limits = payload.limits;
      renderLiftPreview();
    }
    return payload;
  } catch (error) {
    addLog("升降轴", `升降轴限位读取失败：${error.message}`);
    return null;
  }
}

async function requestLiftingRuntimeAction(action) {
  const nextStatus = action === "stop" ? "stopping" : "starting";
  setLiftingRuntime(nextStatus);
  addLog("升降轴", action === "stop" ? "请求清理升降轴 ROS" : "请求启动升降轴服务");
  try {
    const response = await fetch(`/api/runtime/services/lifting/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const payload = await response.json();
    applyLiftingServicePayload(payload);
    if (!response.ok || !payload.ok) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    addLog("升降轴", `升降轴服务动作完成：${payload.code}`);
    return payload;
  } catch (error) {
    setLiftingRuntime("error");
    addLog("升降轴", `升降轴服务动作失败：${error.message}`);
    return null;
  } finally {
    window.setTimeout(() => fetchLiftingRuntimeStatus({ silent: true }), 800);
  }
}

function toggleLiftingRuntime() {
  if (state.liftingRuntime.status === "starting" || state.liftingRuntime.status === "stopping") return;
  if (state.liftingRuntime.status === "running" || state.liftingRuntime.status === "external") {
    requestLiftingControl("stop", {}, { source: "关闭升降轴" }).finally(() => requestLiftingRuntimeAction("stop"));
    return;
  }
  requestLiftingRuntimeAction("start");
}

async function requestChassisRuntimeAction(action) {
  const nextStatus = action === "stop" ? "stopping" : "starting";
  setChassisRuntime(nextStatus);
  addLog("底盘", action === "stop" ? "请求清理 Chassis ROS" : "请求启动 Chassis 服务");
  try {
    const response = await fetch(`/api/runtime/services/chassis/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const payload = await response.json();
    applyChassisServicePayload(payload);
    if (!response.ok || !payload.ok) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    addLog("底盘", `Chassis 服务动作完成：${payload.code}`);
    return payload;
  } catch (error) {
    setChassisRuntime("error");
    addLog("底盘", `Chassis 服务动作失败：${error.message}`);
    return null;
  } finally {
    window.setTimeout(() => fetchChassisRuntimeStatus({ silent: true }), 800);
  }
}

function toggleChassisRuntime() {
  if (state.chassisRuntime.status === "starting" || state.chassisRuntime.status === "stopping") return;
  if (state.chassisRuntime.status === "running" || state.chassisRuntime.status === "external") {
    stopChassisDrive("关闭 Chassis");
    requestChassisRuntimeAction("stop");
    return;
  }
  requestChassisRuntimeAction("start");
}

async function requestCameraRuntimeAction(action) {
  const nextStatus = action === "stop" ? "stopping" : "starting";
  setCameraRuntime(nextStatus);
  addLog("相机", action === "stop" ? "请求清理 Camera ROS" : "请求启动 Camera 服务");
  try {
    const response = await fetch(`/api/runtime/services/camera/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const payload = await response.json();
    applyCameraServicePayload(payload);
    if (!response.ok || !payload.ok) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    addLog("相机", `Camera 服务动作完成：${payload.code}`);
    return payload;
  } catch (error) {
    setCameraRuntime("error");
    addLog("相机", `Camera 服务动作失败：${error.message}`);
    return null;
  } finally {
    window.setTimeout(() => fetchCameraRuntimeStatus({ silent: true }), 800);
  }
}

function toggleCameraRuntime() {
  if (state.cameraRuntime.status === "starting" || state.cameraRuntime.status === "stopping") return;
  if (state.cameraRuntime.status === "running" || state.cameraRuntime.status === "external") {
    requestCameraRuntimeAction("stop");
    return;
  }
  requestCameraRuntimeAction("start");
}

async function requestLidarRuntimeAction(action) {
  const nextStatus = action === "stop" ? "stopping" : "starting";
  setLidarRuntime(nextStatus);
  addLog("LiDAR", action === "stop" ? "请求清理 LiDAR ROS" : "请求启动 LiDAR 服务");
  try {
    const response = await fetch(`/api/runtime/services/lidar/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const payload = await response.json();
    applyLidarServicePayload(payload);
    if (!response.ok || !payload.ok) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    addLog("LiDAR", `LiDAR 服务动作完成：${payload.code}`);
    return payload;
  } catch (error) {
    setLidarRuntime("error");
    addLog("LiDAR", `LiDAR 服务动作失败：${error.message}`);
    return null;
  } finally {
    window.setTimeout(() => fetchLidarRuntimeStatus({ silent: true }), 800);
  }
}

function toggleLidarRuntime() {
  if (state.lidarRuntime.status === "starting" || state.lidarRuntime.status === "stopping") return;
  if (state.lidarRuntime.status === "running" || state.lidarRuntime.status === "external") {
    requestLidarRuntimeAction("stop");
    return;
  }
  requestLidarRuntimeAction("start");
}

function applyLiftingStatePayload(payload) {
  if (!payload || !payload.ok) {
    state.liftingState.ok = false;
    state.liftingState.code = payload && payload.code ? payload.code : "ROS-R-ERROR";
    state.liftingState.detail = payload && payload.detail ? payload.detail : "升降轴反馈读取失败。";
    state.liftingState.heightM = null;
    state.liftingState.targetHeightM = null;
    state.liftingState.backSpeedMps = null;
    state.liftingState.voltage = null;
    state.liftingState.current = null;
    state.liftingState.runState = false;
    state.liftingState.reachTarget = false;
    state.liftingState.fpsError = null;
    state.liftingState.initState = false;
    state.liftingState.upLimit = false;
    state.liftingState.downLimit = false;
    state.liftingState.ageMs = payload && payload.ageMs !== undefined ? payload.ageMs : null;
    state.liftingState.stale = true;
    renderLiftPreview();
    return;
  }

  const data = payload.data || {};
  const backHeight = Number(data.back_height);
  const targetHeight = Number(data.target_height);
  const backSpeed = Number(data.back_speed);
  const voltage = Number(data.back_vol);
  const current = Number(data.back_current);
  const fpsError = Number(data.fps_error);
  state.liftingState.ok = Number.isFinite(backHeight);
  state.liftingState.code = state.liftingState.ok ? payload.code || "ROS-R-OK" : "ROS-R-NODATA";
  state.liftingState.detail = payload.detail || "";
  state.liftingState.heightM = Number.isFinite(backHeight) ? backHeight / 1000 : null;
  state.liftingState.targetHeightM = Number.isFinite(targetHeight) ? targetHeight / 1000 : null;
  state.liftingState.backSpeedMps = Number.isFinite(backSpeed) ? backSpeed / 1000 : null;
  state.liftingState.voltage = Number.isFinite(voltage) ? voltage : null;
  state.liftingState.current = Number.isFinite(current) ? current : null;
  state.liftingState.runState = Boolean(data.run_state);
  state.liftingState.reachTarget = Boolean(data.reach_target_pos);
  state.liftingState.fpsError = Number.isFinite(fpsError) ? fpsError : null;
  state.liftingState.initState = Boolean(data.init_state);
  state.liftingState.upLimit = Boolean(data.up_limit);
  state.liftingState.downLimit = Boolean(data.down_limit);
  state.liftingState.ageMs = Number.isFinite(Number(payload.ageMs)) ? Number(payload.ageMs) : null;
  state.liftingState.stale = Boolean(payload.stale);
  state.liftingState.receivedAt = payload.receivedAt || null;
  state.liftingState.topic = payload.topic || "";
  renderLiftPreview();
}

async function fetchLiftingMotorState() {
  try {
    const response = await fetch(`/api/ros/topics/${liftingTopicKey}?wait=0.1`, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok && !payload.code) {
      payload.ok = false;
      payload.code = `HTTP-${response.status}`;
      payload.detail = `HTTP ${response.status}`;
    }
    applyLiftingStatePayload(payload);
    return payload;
  } catch (error) {
    applyLiftingStatePayload({
      ok: false,
      code: "ROS-R-FETCH",
      detail: error.message,
    });
    return null;
  }
}

function elapsedSince(timestamp, fallback = null) {
  const value = Number(timestamp);
  if (!Number.isFinite(value)) return fallback;
  return Math.max(0, Math.round(Date.now() - value));
}

function chassisHasCachedState() {
  return Boolean(state.chassisState.system || state.chassisState.motion || state.chassisState.battery || state.chassisState.odom);
}

function applyChassisStatePayloads(results) {
  const byKind = {};
  results.forEach((item) => {
    byKind[item.kind] = item.payload;
  });
  const okPayloads = Object.values(byKind).filter((payload) => payload && payload.ok);
  const failedPayloads = Object.values(byKind).filter((payload) => payload && !payload.ok);
  const hadCachedState = chassisHasCachedState();

  Object.entries(chassisTopicKeys).forEach(([kind]) => {
    const payload = byKind[kind];
    if (payload && payload.ok) {
      state.chassisState[kind] = payload.data || null;
    }
  });

  if (okPayloads.length > 0) {
    const ages = okPayloads.map((payload) => Number(payload.ageMs)).filter(Number.isFinite);
    const ageMs = ages.length ? Math.max(...ages) : elapsedSince(state.chassisState.lastOkAt, state.chassisState.ageMs);
    const hasStalePayload = okPayloads.some((payload) => payload.stale);
    const hasFailedPayload = failedPayloads.length > 0;
    state.chassisState.ok = true;
    state.chassisState.code = hasStalePayload || hasFailedPayload ? "ROS-R-STALE" : "ROS-R-OK";
    state.chassisState.detail = hasFailedPayload ? "底盘反馈部分读取失败，保留上一帧。" : "底盘反馈在线。";
    state.chassisState.stale = hasStalePayload || hasFailedPayload;
    state.chassisState.ageMs = ageMs;
    state.chassisState.receivedAt = okPayloads.find((payload) => payload.receivedAt)?.receivedAt || state.chassisState.receivedAt;
    state.chassisState.lastOkAt = Number.isFinite(ageMs) ? Date.now() - ageMs : Date.now();
  } else if (hadCachedState) {
    const failedPayload = failedPayloads.find((payload) => payload.detail);
    state.chassisState.ok = true;
    state.chassisState.code = "ROS-R-STALE";
    state.chassisState.detail = failedPayload && failedPayload.detail ? `${failedPayload.detail}，保留上一帧。` : "底盘反馈本轮读取失败，保留上一帧。";
    state.chassisState.stale = true;
    state.chassisState.ageMs = elapsedSince(state.chassisState.lastOkAt, state.chassisState.ageMs);
  } else {
    const failedPayload = failedPayloads.find((payload) => payload.detail || payload.code);
    state.chassisState.ok = false;
    state.chassisState.code = (failedPayload && failedPayload.code) || "ROS-R-NODATA";
    state.chassisState.detail = (failedPayload && failedPayload.detail) || "等待底盘反馈。";
    state.chassisState.stale = true;
    state.chassisState.ageMs = null;
    state.chassisState.receivedAt = null;
  }
  renderDeviceBaseMetrics();
}

async function fetchChassisTopic(kind, key) {
  try {
    const response = await fetch(`/api/ros/topics/${key}?wait=0.05`, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok && !payload.code) {
      payload.ok = false;
      payload.code = `HTTP-${response.status}`;
      payload.detail = `HTTP ${response.status}`;
    }
    return { kind, payload };
  } catch (error) {
    return {
      kind,
      payload: {
        ok: false,
        code: "ROS-R-FETCH",
        detail: error.message,
      },
    };
  }
}

async function fetchChassisState(options = {}) {
  if (state.chassisState.polling) {
    return null;
  }
  state.chassisState.polling = true;
  try {
    const results = await Promise.all(
      Object.entries(chassisTopicKeys).map(([kind, key]) => fetchChassisTopic(kind, key)),
    );
    applyChassisStatePayloads(results);
    if (!options.silent && !state.chassisState.ok) {
      addLog("底盘", state.chassisState.detail);
    }
    return results;
  } finally {
    state.chassisState.polling = false;
  }
}

async function resetChassisOdometry() {
  if (state.chassisControl.resettingOdom) return null;
  if (!chassisReady()) {
    addLog("底盘", "Chassis 服务未启动，里程计无法归零");
    renderBaseOdomResetButton();
    return null;
  }

  state.chassisControl.resettingOdom = true;
  clearChassisStopTimers();
  stopChassisDrive("里程计归零");
  renderBaseOdomResetButton();

  try {
    const response = await fetchChassisControl("/api/control/chassis/reset_odom", {
      commandSource: "里程计归零",
    });
    const result = await response.json();
    if (!response.ok || !result.ok) {
      throw new Error(result.detail || `HTTP ${response.status}`);
    }
    addLog("底盘", `里程计归零：${result.code}`);
    await fetchChassisState({ silent: true });
    window.setTimeout(() => fetchChassisState({ silent: true }), 150);
    return result;
  } catch (error) {
    addLog("底盘", `里程计归零失败：${error.message}`);
    return null;
  } finally {
    state.chassisControl.resettingOdom = false;
    renderBaseOdomResetButton();
  }
}

function chassisBaseValue(key, fallback) {
  const item = deviceBaseControlItems.find((entry) => entry.key === key);
  if (!item) return fallback;
  return commandSpeedValue(item);
}

function chassisCommandForDrive(action) {
  const linearSpeed = chassisBaseValue("linear", 0.10);
  const lateralSpeed = chassisBaseValue("lateral", 0.08);
  const angularSpeed = chassisBaseValue("angular", 0.25);
  if (action === "forward") return { linearX: linearSpeed, linearY: 0, angularZ: 0 };
  if (action === "backward") return { linearX: -linearSpeed, linearY: 0, angularZ: 0 };
  if (action === "strafe-left") return { linearX: 0, linearY: lateralSpeed, angularZ: 0 };
  if (action === "strafe-right") return { linearX: 0, linearY: -lateralSpeed, angularZ: 0 };
  if (action === "left") return { linearX: 0, linearY: 0, angularZ: angularSpeed };
  if (action === "right") return { linearX: 0, linearY: 0, angularZ: -angularSpeed };
  return { linearX: 0, linearY: 0, angularZ: 0 };
}

function renderChassisKeyboardControl() {
  const listening = state.chassisControl.keyboardListening;
  const activeKey = state.chassisControl.keyboardActiveKey;
  ["#chassisKeyboardButton", "#mappingChassisKeyboardButton"].forEach((selector) => {
    const button = $(selector);
    if (!button) return;
    const ready = chassisReady();
    button.className = `keyboard-listen-button state-badge ${listening ? "ok" : "idle"}`;
    if (selector === "#mappingChassisKeyboardButton") {
      button.classList.add("mapping-keyboard-button");
    }
    button.textContent = listening ? "监听中" : "键盘监听";
    button.disabled = !ready;
    button.title = ready
      ? listening
        ? "正在监听 W/S/A/D 和 Q/E，点击关闭"
        : "点击后监听 W/S/A/D 和 Q/E"
      : "Chassis 服务未启动，无法监听键盘";
    button.setAttribute("aria-pressed", listening ? "true" : "false");
    button.setAttribute("aria-label", listening ? `键盘监听已开启${activeKey ? `，当前 ${activeKey.toUpperCase()}` : ""}` : "开启键盘监听");
  });
  $$("[data-device-drive], [data-mapping-drive]").forEach((driveButton) => {
    const action = driveButton.dataset.deviceDrive || driveButton.dataset.mappingDrive;
    driveButton.classList.toggle("is-active", state.chassisControl.activeDrive === action);
  });
}

function clearChassisKeyboardKeys() {
  state.chassisControl.keyboardKeys = [];
  state.chassisControl.keyboardActiveKey = null;
}

function stopChassisKeyboardControl(source = "键盘监听关闭", options = {}) {
  const hadActiveDrive = Boolean(state.chassisControl.activeDrive);
  clearChassisKeyboardKeys();
  if (options.deactivate) state.chassisControl.keyboardListening = false;
  if (hadActiveDrive) {
    stopChassisDrive(source);
  } else {
    renderChassisKeyboardControl();
  }
  if (options.log !== false) addLog("底盘", source);
}

function setChassisKeyboardListening(listening) {
  if (listening) {
    if (!chassisReady()) {
      addLog("底盘", "Chassis 服务未启动，键盘监听未开启");
      renderChassisKeyboardControl();
      return;
    }
    state.chassisControl.keyboardListening = true;
    clearChassisKeyboardKeys();
    renderChassisKeyboardControl();
    const buttonSelector = document.body.dataset.activeView === "robot-view" ? "#mappingChassisKeyboardButton" : "#chassisKeyboardButton";
    $(buttonSelector)?.focus();
    addLog("底盘", "键盘监听已开启");
    return;
  }
  stopChassisKeyboardControl("键盘监听关闭", { deactivate: true });
}

function toggleChassisKeyboardListening() {
  setChassisKeyboardListening(!state.chassisControl.keyboardListening);
}

function keyboardEventTargetIsEditable(target) {
  if (!(target instanceof Element)) return false;
  if (target.closest("#chassisKeyboardButton, #mappingChassisKeyboardButton")) return false;
  const input = target.closest("input");
  if (input) {
    const type = String(input.getAttribute("type") || "text").toLowerCase();
    return !["range", "button", "checkbox", "radio", "submit", "reset"].includes(type);
  }
  return Boolean(target.closest("textarea, select, [contenteditable='true']"));
}

function canHandleChassisKeyboardEvent(event) {
  return (
    state.chassisControl.keyboardListening &&
    ["platform-control", "robot-view"].includes(document.body.dataset.activeView) &&
    !event.altKey &&
    !event.ctrlKey &&
    !event.metaKey &&
    !keyboardEventTargetIsEditable(event.target)
  );
}

function handleChassisKeyboardKeyDown(event) {
  if (!state.chassisControl.keyboardListening) return;
  if (event.key === "Escape") {
    event.preventDefault();
    stopChassisKeyboardControl("键盘监听关闭", { deactivate: true });
    return;
  }
  if (!canHandleChassisKeyboardEvent(event)) return;
  const key = String(event.key || "").toLowerCase();
  const mapping = chassisKeyboardDriveMap[key];
  if (!mapping) return;
  event.preventDefault();
  if (!chassisReady()) {
    stopChassisKeyboardControl("Chassis 服务未运行，键盘监听停止", { deactivate: true });
    return;
  }
  const pressedKeys = state.chassisControl.keyboardKeys;
  if (pressedKeys.includes(key)) return;
  pressedKeys.push(key);
  state.chassisControl.keyboardActiveKey = key;
  startChassisDrive(mapping.action, mapping.label);
  renderChassisKeyboardControl();
}

function handleChassisKeyboardKeyUp(event) {
  if (!canHandleChassisKeyboardEvent(event)) return;
  const key = String(event.key || "").toLowerCase();
  if (!chassisKeyboardDriveMap[key]) return;
  event.preventDefault();
  state.chassisControl.keyboardKeys = state.chassisControl.keyboardKeys.filter((pressedKey) => pressedKey !== key);
  if (state.chassisControl.keyboardActiveKey !== key) {
    renderChassisKeyboardControl();
    return;
  }
  const nextKey = [...state.chassisControl.keyboardKeys].reverse().find((pressedKey) => chassisKeyboardDriveMap[pressedKey]);
  if (nextKey) {
    const mapping = chassisKeyboardDriveMap[nextKey];
    state.chassisControl.keyboardActiveKey = nextKey;
    startChassisDrive(mapping.action, mapping.label);
  } else {
    state.chassisControl.keyboardActiveKey = null;
    stopChassisDrive("键盘松开停止");
  }
  renderChassisKeyboardControl();
}

function nextChassisCommandSequence() {
  state.chassisControl.commandSequence += 1;
  return state.chassisControl.commandSequence;
}

function chassisStopCommand() {
  return { linearX: 0, linearY: 0, angularZ: 0 };
}

function clearChassisStopTimers() {
  state.chassisControl.stopTimers.forEach((timer) => window.clearTimeout(timer));
  state.chassisControl.stopTimers = [];
}

async function requestChassisVelocity(command, options = {}) {
  if (!chassisReady()) {
    if (!options.quiet) addLog("底盘", "Chassis 服务未启动，速度指令未发送");
    renderDeviceBaseMetrics();
    return null;
  }
  const commandSequence = nextChassisCommandSequence();
  const payload = {
    ...command,
    commandSequence,
    commandSource: options.source || "速度指令",
  };
  try {
    const response = await fetchChassisControl("/api/control/chassis/cmd_vel", payload);
    const result = await response.json();
    if (!response.ok || !result.ok) {
      throw new Error(result.detail || `HTTP ${response.status}`);
    }
    if (result.stale) {
      return result;
    }
    state.chassisControl.command = {
      linearX: Number(payload.linearX) || 0,
      linearY: Number(payload.linearY) || 0,
      angularZ: Number(payload.angularZ) || 0,
    };
    renderDeviceBaseMetrics();
    if (!options.quiet) addLog("底盘", `${options.source || "速度指令"}：${result.code}`);
    return result;
  } catch (error) {
    addLog("底盘", `${options.source || "速度指令"}失败：${error.message}`);
    return null;
  }
}

function requestChassisStop(source = "底盘停止") {
  clearChassisStopTimers();
  requestChassisVelocity(chassisStopCommand(), { source });
  for (let index = 1; index < CHASSIS_STOP_REPEAT_COUNT; index += 1) {
    const timer = window.setTimeout(() => {
      requestChassisVelocity(chassisStopCommand(), {
        source,
        quiet: true,
      });
    }, index * CHASSIS_STOP_REPEAT_MS);
    state.chassisControl.stopTimers.push(timer);
  }
}

function startChassisDrive(action, label) {
  if (action === "stop") {
    stopChassisDrive("底盘停止");
    return;
  }
  clearChassisStopTimers();
  if (!chassisReady()) {
    requestChassisVelocity(chassisCommandForDrive(action), { source: `点动${label}`, quiet: true });
    return;
  }
  if (state.chassisControl.driveTimer) {
    window.clearInterval(state.chassisControl.driveTimer);
  }
  state.chassisControl.activeDrive = action;
  addLog("底盘", `点动开始：${label}`);
  renderChassisKeyboardControl();
  requestChassisVelocity(chassisCommandForDrive(action), { source: `点动${label}`, quiet: true });
  state.chassisControl.driveTimer = window.setInterval(() => {
    if (!state.chassisControl.activeDrive) return;
    requestChassisVelocity(chassisCommandForDrive(state.chassisControl.activeDrive), { source: `点动${label}`, quiet: true });
  }, CHASSIS_DRIVE_REPEAT_MS);
}

function stopChassisDrive(source = "松开停止") {
  if (state.chassisControl.driveTimer) {
    window.clearInterval(state.chassisControl.driveTimer);
    state.chassisControl.driveTimer = null;
  }
  const hadActiveDrive = Boolean(state.chassisControl.activeDrive);
  state.chassisControl.activeDrive = null;
  if (hadActiveDrive || source === "底盘停止" || source === "关闭 Chassis") {
    requestChassisStop(source);
  }
  renderChassisKeyboardControl();
}

async function requestLiftingControl(action, payload = {}, options = {}) {
  if (!liftingReady() && action !== "stop") {
    addLog("升降轴", "升降轴服务未启动，指令未发送");
    renderLiftPreview();
    return null;
  }
  if (action === "height" && !liftingInitialized()) {
    addLog("升降轴", "升降轴未完成初始化，目标高度未发送");
    renderLiftPreview();
    return null;
  }
  try {
    const response = await fetchLiftingControl(`/api/control/lifting/${action}`, payload);
    const result = await response.json();
    if (!response.ok || !result.ok) {
      throw new Error(result.detail || `HTTP ${response.status}`);
    }
    state.liftPreview.mode = options.mode || "已下发";
    addLog("升降轴", `${options.source || action}：${result.code}`);
    window.setTimeout(fetchLiftingMotorState, 250);
    renderLiftPreview();
    return result;
  } catch (error) {
    state.liftPreview.mode = "指令失败";
    addLog("升降轴", `${options.source || action}失败：${error.message}`);
    renderLiftPreview();
    return null;
  }
}

function commandLiftHeight(source = "执行目标高度") {
  return requestLiftingControl(
    "height",
    { heightM: state.liftPreview.height },
    { source, mode: "执行目标" },
  );
}

function commandLiftRelative(direction) {
  if (!liftingInitialized()) {
    addLog("升降轴", "升降轴未完成初始化，相对移动未发送");
    renderLiftPreview();
    return null;
  }
  const actualHeight = Number(state.liftingState.heightM);
  if (!Number.isFinite(actualHeight)) {
    addLog("升降轴", "升降轴实际高度不可用，相对移动未发送");
    renderLiftPreview();
    return null;
  }
  const limits = state.liftingState.limits || {};
  const minHeight = Number.isFinite(Number(limits.minHeightM)) ? Number(limits.minHeightM) : liftPreviewLimits.min;
  const maxHeight = Number.isFinite(Number(limits.maxHeightM)) ? Number(limits.maxHeightM) : liftPreviewLimits.max;
  const stepMm = direction === "up" ? Number(state.liftPreview.stepUpMm) : Number(state.liftPreview.stepDownMm);
  const signedDeltaM = (direction === "up" ? 1 : -1) * (stepMm / 1000.0);
  state.liftPreview.height = clamp(actualHeight + signedDeltaM, minHeight, maxHeight);
  state.liftPreview.mode = direction === "up" ? `上升 ${Math.round(stepMm)} mm` : `下降 ${Math.round(stepMm)} mm`;
  renderLiftPreview();
  return commandLiftHeight(state.liftPreview.mode);
}

function markPiperJointFeedbackDelayed(feedback, detail) {
  const hasCachedPositions = Array.isArray(feedback.positions) && feedback.positions.length > 0;
  if (!hasCachedPositions) return false;
  feedback.ok = true;
  feedback.code = "ROS-R-STALE";
  feedback.detail = detail;
  feedback.stale = true;
  feedback.ageMs = elapsedSince(feedback.lastOkAt, feedback.ageMs);
  return true;
}

function applyPiperJointPayload(side, payload) {
  const feedback = state.piperJoints[side];
  if (!feedback) return;

  if (!payload || !payload.ok) {
    const detail = payload && payload.detail
      ? `${payload.detail}，保留上一帧。`
      : `${piperArmLabels[side]}关节反馈本轮读取失败，保留上一帧。`;
    if (markPiperJointFeedbackDelayed(feedback, detail)) return;
    feedback.ok = false;
    feedback.code = payload && payload.code ? payload.code : "ROS-R-ERROR";
    feedback.detail = payload && payload.detail ? payload.detail : `${piperArmLabels[side]}关节反馈读取失败。`;
    feedback.names = [];
    feedback.positions = [];
    feedback.ageMs = payload && payload.ageMs !== undefined ? payload.ageMs : null;
    feedback.stale = true;
    feedback.receivedAt = payload && payload.receivedAt ? payload.receivedAt : null;
    return;
  }

  const data = payload.data || {};
  const names = Array.isArray(data.name) ? data.name.map((name) => String(name)) : [];
  const positions = Array.isArray(data.position) ? data.position : [];
  if (!positions.length) {
    const detail = `${piperArmLabels[side]} JointState 中没有 position 数据，保留上一帧。`;
    if (markPiperJointFeedbackDelayed(feedback, detail)) return;
    feedback.ok = false;
    feedback.code = "ROS-R-NODATA";
    feedback.detail = `${piperArmLabels[side]} JointState 中没有 position 数据。`;
    feedback.names = [];
    feedback.positions = [];
    feedback.ageMs = null;
    feedback.stale = true;
    feedback.receivedAt = payload.receivedAt || null;
    return;
  }
  const ageMs = Number.isFinite(Number(payload.ageMs)) ? Number(payload.ageMs) : null;
  feedback.ok = true;
  feedback.code = payload.code || "ROS-R-OK";
  feedback.detail = payload.detail || "";
  feedback.names = names;
  feedback.positions = positions;
  feedback.velocity = Array.isArray(data.velocity) ? data.velocity : [];
  feedback.effort = Array.isArray(data.effort) ? data.effort : [];
  feedback.ageMs = ageMs;
  feedback.stale = Boolean(payload.stale);
  feedback.receivedAt = payload.receivedAt || null;
  feedback.lastOkAt = Number.isFinite(ageMs) ? Date.now() - ageMs : Date.now();
  feedback.topic = payload.topic || "";
}

function renderPiperJointFeedback() {
  renderArmComparisons();
  renderRobotViewStatus();
}

async function fetchPiperJointStates() {
  if (state.piperJointPolling) {
    return null;
  }
  state.piperJointPolling = true;
  try {
    const entries = Object.entries(piperJointTopicKeys);
    const results = await Promise.all(
      entries.map(async ([side, key]) => {
        try {
          const response = await fetch(`/api/ros/topics/${key}?wait=${piperJointReadWaitSec}`, { cache: "no-store" });
          const payload = await response.json();
          if (!response.ok && !payload.code) {
            payload.ok = false;
            payload.code = `HTTP-${response.status}`;
            payload.detail = `HTTP ${response.status}`;
          }
          return [side, payload];
        } catch (error) {
          return [
            side,
            {
              ok: false,
              code: "ROS-R-FETCH",
              detail: error.message,
            },
          ];
        }
      }),
    );

    results.forEach(([side, payload]) => applyPiperJointPayload(side, payload));
    renderPiperJointFeedback();
    return results;
  } finally {
    state.piperJointPolling = false;
  }
}

async function requestPiperRuntimeAction(action) {
  const nextStatus = action === "stop" ? "stopping" : "starting";
  setPiperRuntime(nextStatus);
  addLog("机械臂", action === "stop" ? "请求清理 Piper ROS" : "请求启动 Piper 服务");
  try {
    const response = await fetch(`/api/runtime/services/piper/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const payload = await response.json();
    applyPiperServicePayload(payload);
    if (!response.ok || !payload.ok) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    addLog("机械臂", `Piper 服务动作完成：${payload.code}`);
    return payload;
  } catch (error) {
    setPiperRuntime("error");
    addLog("机械臂", `Piper 服务动作失败：${error.message}`);
    return null;
  } finally {
    window.setTimeout(() => fetchPiperRuntimeStatus({ silent: true }), 800);
  }
}

function cameraFeedKey(feed) {
  return `${feed.camera}_${feed.kind}`;
}

function mergeCameraFeeds(feeds = []) {
  const feedMap = new Map(feeds.map((feed) => [cameraFeedKey(feed), feed]));
  return cameraFeedLayout.map((feed) => {
    const remote = feedMap.get(cameraFeedKey(feed)) || {};
    return {
      ...feed,
      ...remote,
      label: remote.label || feed.label,
      hasFrame: Boolean(remote.hasFrame),
      stale: remote.stale !== undefined ? Boolean(remote.stale) : true,
    };
  });
}

function renderCameraPreviewToggle() {
  const button = $("#cameraPreviewToggleButton");
  if (!button) return;
  const enabled = Boolean(state.cameraFrames.previewEnabled);
  button.textContent = enabled ? "回显开启" : "回显关闭";
  button.title = enabled ? "关闭相机图像回显" : "开启相机图像回显";
  button.classList.toggle("is-active", enabled);
  button.setAttribute("aria-pressed", enabled ? "true" : "false");
}

function clearCameraFrameDisplay() {
  Object.values(state.cameraFrames.frameTimers).forEach((timer) => window.clearTimeout(timer));
  Object.values(state.cameraFrames.frameObjectUrls).forEach((url) => {
    if (url) URL.revokeObjectURL(url);
  });
  state.cameraFrames.activeRequests = {};
  state.cameraFrames.frameObjectUrls = {};
  state.cameraFrames.frameSequences = {};
  state.cameraFrames.frameTimers = {};
  state.cameraFrames.feeds = mergeCameraFeeds();
  state.cameraFrames.error = "";
  $$("#cameraFrameGrid .camera-frame-card").forEach((card) => {
    card.classList.remove("has-frame", "is-error", "is-ok", "is-warn", "is-danger");
    card.classList.add("is-idle");
    const image = card.querySelector("img[data-camera-frame]");
    if (image) image.removeAttribute("src");
    const placeholder = card.querySelector(".camera-frame-placeholder");
    if (placeholder) placeholder.textContent = "回显关闭";
  });
}

function setCameraPreviewEnabled(enabled, options = {}) {
  const nextEnabled = Boolean(enabled);
  if (state.cameraFrames.previewEnabled === nextEnabled && !options.force) return;
  state.cameraFrames.previewEnabled = nextEnabled;
  renderCameraPreviewToggle();
  if (!nextEnabled) {
    clearCameraFrameDisplay();
    renderCameraFrames();
    if (!options.silent) addLog("相机", "相机图像回显已关闭");
    return;
  }
  renderCameraFrames();
  fetchCameraFrames({ silent: true });
  if (!options.silent) addLog("相机", "相机图像回显已开启");
}

function toggleCameraPreview() {
  setCameraPreviewEnabled(!state.cameraFrames.previewEnabled);
}

function cameraFrameAgeText(feed) {
  const ageMs = Number(feed.ageMs);
  if (!Number.isFinite(ageMs)) return "无帧";
  if (ageMs < 1000) return `${Math.max(0, Math.round(ageMs))} ms`;
  return `${(ageMs / 1000).toFixed(1)} s`;
}

function cameraFrameStatus(feed) {
  if (!state.cameraFrames.previewEnabled) return { text: "关闭", level: "idle" };
  if (!feed.hasFrame) return { text: "无帧", level: "idle" };
  if (feed.stale) return { text: "过期", level: "warn" };
  return { text: "实时", level: "ok" };
}

function cameraFrameUrl(feed) {
  const key = cameraFeedKey(feed);
  const params = new URLSearchParams({
    wait: "0.5",
    t: String(Date.now()),
  });
  const sequence = Number(state.cameraFrames.frameSequences[key]);
  if (Number.isFinite(sequence)) {
    params.set("after", String(sequence));
  }
  return `/api/sensors/cameras/${encodeURIComponent(feed.camera)}/${encodeURIComponent(feed.kind)}/frame?${params.toString()}`;
}

function decodeCameraImage(url) {
  const image = new Image();
  image.decoding = "async";
  image.src = url;
  if (image.decode) {
    return image.decode().catch(
      () =>
        new Promise((resolve, reject) => {
          image.onload = resolve;
          image.onerror = reject;
        }),
    );
  }
  return new Promise((resolve, reject) => {
    image.onload = resolve;
    image.onerror = reject;
  });
}

function scheduleCameraFrame(feed, delayMs = cameraFrameIntervalMs) {
  if (!state.cameraFrames.previewEnabled) return;
  const key = cameraFeedKey(feed);
  window.clearTimeout(state.cameraFrames.frameTimers[key]);
  state.cameraFrames.frameTimers[key] = window.setTimeout(() => {
    requestCameraFrame(feed);
  }, delayMs);
}

async function requestCameraFrame(feed) {
  if (!state.cameraFrames.previewEnabled) return;
  const key = cameraFeedKey(feed);
  if (state.cameraFrames.activeRequests[key]) return;

  const card = $(`#cameraFrameGrid [data-feed-key="${key}"]`);
  const image = card ? card.querySelector("img[data-camera-frame]") : null;
  if (!card || !image) return;

  const startedAt = performance.now();
  state.cameraFrames.activeRequests[key] = true;
  try {
    const response = await fetch(cameraFrameUrl(feed), { cache: "no-store" });
    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }
    const blob = await response.blob();
    if (!blob.type.startsWith("image/")) {
      throw new Error(blob.type || "not image");
    }
    const objectUrl = URL.createObjectURL(blob);
    try {
      await decodeCameraImage(objectUrl);
    } catch (error) {
      URL.revokeObjectURL(objectUrl);
      throw error;
    }

    if (!state.cameraFrames.previewEnabled) {
      URL.revokeObjectURL(objectUrl);
      return;
    }
    if (!card.isConnected) {
      URL.revokeObjectURL(objectUrl);
      return;
    }
    const oldUrl = state.cameraFrames.frameObjectUrls[key];
    image.src = objectUrl;
    state.cameraFrames.frameObjectUrls[key] = objectUrl;
    if (oldUrl) {
      window.setTimeout(() => URL.revokeObjectURL(oldUrl), 1000);
    }

    const sequence = Number(response.headers.get("X-Robot-Station-Frame-Sequence"));
    if (Number.isFinite(sequence)) {
      state.cameraFrames.frameSequences[key] = sequence;
    }
    card.classList.remove("is-error");
    card.classList.add("has-frame");
  } catch (error) {
    if (!card.classList.contains("has-frame")) {
      card.classList.add("is-error");
      const placeholder = card.querySelector(".camera-frame-placeholder");
      if (placeholder) placeholder.textContent = "等待画面";
    }
  } finally {
    delete state.cameraFrames.activeRequests[key];
    if (state.cameraFrames.previewEnabled && card && card.isConnected) {
      const elapsed = performance.now() - startedAt;
      scheduleCameraFrame(feed, Math.max(40, cameraFrameIntervalMs - elapsed));
    }
  }
}

function ensureCameraFrameLoop(feed) {
  if (!state.cameraFrames.previewEnabled) return;
  const key = cameraFeedKey(feed);
  if (state.cameraFrames.frameTimers[key] || state.cameraFrames.activeRequests[key]) return;
  const index = cameraFeedLayout.findIndex((entry) => cameraFeedKey(entry) === key);
  scheduleCameraFrame(feed, Math.max(0, index) * cameraFrameStaggerMs);
}

function ensureCameraFrameCard(grid, feed) {
  const key = cameraFeedKey(feed);
  let card = grid.querySelector(`[data-feed-key="${key}"]`);
  if (card) {
    ensureCameraFrameLoop(feed);
    return card;
  }

  grid.insertAdjacentHTML(
    "beforeend",
    `
      <article class="preview-card camera-frame-card is-idle" data-feed-key="${escapeHtml(key)}">
        <figure class="camera-frame-visual">
          <img alt="${escapeHtml(feed.label)}" data-camera-frame="${escapeHtml(key)}">
          <span class="camera-frame-placeholder">${state.cameraFrames.previewEnabled ? "等待画面" : "回显关闭"}</span>
        </figure>
        <div class="camera-frame-meta">
          <strong>${escapeHtml(feed.label)}</strong>
          <span class="camera-frame-status is-idle">无帧</span>
        </div>
        <p title="${escapeHtml(feed.topic || "")}">${escapeHtml(feed.topic || "")}</p>
      </article>
    `,
  );

  card = grid.querySelector(`[data-feed-key="${key}"]`);
  ensureCameraFrameLoop(feed);
  return card;
}

function updateCameraFrameCard(card, feed) {
  const status = cameraFrameStatus(feed);
  ["ok", "warn", "danger", "idle"].forEach((level) => {
    card.classList.toggle(`is-${level}`, status.level === level);
  });
  card.classList.toggle("has-frame", Boolean(feed.hasFrame));
  if (feed.hasFrame) {
    card.classList.remove("is-error");
  }

  const title = card.querySelector(".camera-frame-meta strong");
  if (title) title.textContent = feed.label;

  const badge = card.querySelector(".camera-frame-status");
  if (badge) {
    badge.className = `camera-frame-status is-${status.level}`;
    badge.textContent = status.text;
  }

  const detail = card.querySelector("p");
  if (detail) {
    const format = feed.format ? String(feed.format) : "compressed";
    const text = !state.cameraFrames.previewEnabled ? "回显关闭" : feed.hasFrame ? `${cameraFrameAgeText(feed)} / ${format}` : feed.topic || "";
    detail.textContent = text;
    detail.title = feed.topic || "";
  }

  const image = card.querySelector("img[data-camera-frame]");
  if (image && image.alt !== feed.label) {
    image.alt = feed.label;
  }
  const placeholder = card.querySelector(".camera-frame-placeholder");
  if (placeholder) {
    placeholder.textContent = state.cameraFrames.previewEnabled ? "等待画面" : "回显关闭";
  }
}

function renderCameraFrames() {
  const feeds = state.cameraFrames.feeds.length ? state.cameraFrames.feeds : mergeCameraFeeds();
  renderCameraPreviewToggle();
  const summary = $("#cameraFeedSummary");
  if (summary) {
    const liveCount = feeds.filter((feed) => feed.hasFrame && !feed.stale).length;
    const frameCount = feeds.filter((feed) => feed.hasFrame).length;
    summary.textContent = !state.cameraFrames.previewEnabled
      ? "回显关闭"
      : state.cameraFrames.error
      ? `异常：${state.cameraFrames.error}`
      : `${liveCount} 路实时 / ${frameCount} 路有帧 / 共 ${feeds.length} 路`;
  }

  const grid = $("#cameraFrameGrid");
  if (!grid) return;
  const expectedKeys = new Set(feeds.map(cameraFeedKey));
  feeds.forEach((feed) => {
    const card = ensureCameraFrameCard(grid, feed);
    updateCameraFrameCard(card, feed);
  });
  grid.querySelectorAll(".camera-frame-card").forEach((card) => {
    if (!expectedKeys.has(card.dataset.feedKey)) {
      window.clearTimeout(state.cameraFrames.frameTimers[card.dataset.feedKey]);
      delete state.cameraFrames.frameTimers[card.dataset.feedKey];
      delete state.cameraFrames.activeRequests[card.dataset.feedKey];
      const objectUrl = state.cameraFrames.frameObjectUrls[card.dataset.feedKey];
      if (objectUrl) URL.revokeObjectURL(objectUrl);
      delete state.cameraFrames.frameObjectUrls[card.dataset.feedKey];
      delete state.cameraFrames.frameSequences[card.dataset.feedKey];
      card.remove();
    }
  });
}

async function fetchCameraFrames(options = {}) {
  if (!state.cameraFrames.previewEnabled) {
    renderCameraFrames();
    return null;
  }
  try {
    const response = await fetch("/api/sensors/cameras", { cache: "no-store" });
    const payload = await response.json();
    if (!payload || !Array.isArray(payload.feeds)) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    state.cameraFrames.feeds = mergeCameraFeeds(payload.feeds);
    state.cameraFrames.error = payload.ok ? "" : payload.detail || `HTTP ${response.status}`;
    state.cameraFrames.updatedAt = formatTime();
    renderCameraFrames();
    if (!payload.ok && !options.silent) {
      addLog("相机", `相机图像状态异常：${state.cameraFrames.error}`);
    }
    return payload;
  } catch (error) {
    state.cameraFrames.error = error.message;
    renderCameraFrames();
    if (!options.silent) {
      addLog("相机", `相机图像状态查询失败：${error.message}`);
    }
    return null;
  }
}

function renderLidarPreviewToggle() {
  const button = $("#lidarPreviewToggleButton");
  if (!button) return;
  const enabled = Boolean(state.lidarCloud.previewEnabled);
  button.textContent = enabled ? "回显开启" : "回显关闭";
  button.title = enabled ? "关闭 LiDAR 点云回显" : "开启 LiDAR 点云回显";
  button.classList.toggle("is-active", enabled);
  button.setAttribute("aria-pressed", enabled ? "true" : "false");
}

function clearLidarFrameDisplay() {
  const lidar = state.lidarCloud;
  window.clearTimeout(lidar.frameTimer);
  lidar.frameTimer = null;
  lidar.activeRequest = false;
  lidar.sequence = null;
  lidar.clouds = [];
  lidar.error = "";
  lidar.hasFrame = false;
  lidar.pointCount = 0;
  lidar.sourcePointCount = 0;
  lidar.ageMs = null;
  lidar.stale = true;
  lidar.frameId = "";
  lidar.receivedAt = null;
  lidar.frameRate = null;
  lidar.frameTimes = [];
  if (lidar.points) lidar.points.visible = false;
}

function setLidarPreviewEnabled(enabled, options = {}) {
  const nextEnabled = Boolean(enabled);
  if (state.lidarCloud.previewEnabled === nextEnabled && !options.force) return;
  state.lidarCloud.previewEnabled = nextEnabled;
  renderLidarPreviewToggle();
  if (!nextEnabled) {
    clearLidarFrameDisplay();
    renderLidarCloudStatus();
    if (!options.silent) addLog("LiDAR", "LiDAR 点云回显已关闭");
    return;
  }
  if (state.lidarCloud.points) state.lidarCloud.points.visible = true;
  renderLidarCloudStatus();
  fetchLidarCloudStatus({ silent: true });
  requestLidarFrame();
  if (!options.silent) addLog("LiDAR", "LiDAR 点云回显已开启");
}

function toggleLidarPreview() {
  setLidarPreviewEnabled(!state.lidarCloud.previewEnabled);
}

function lidarAgeText(ageMs) {
  const parsed = Number(ageMs);
  if (!Number.isFinite(parsed)) return "--";
  if (parsed < 1000) return `${Math.max(0, Math.round(parsed))} ms`;
  return `${(parsed / 1000).toFixed(1)} s`;
}

function loadThreeModule() {
  if (!threeModulePromise) {
    threeModulePromise = import(threeModuleUrl);
  }
  return threeModulePromise;
}

function loadThreeLoaders() {
  if (!threeLoaderPromise) {
    threeLoaderPromise = Promise.all([loadThreeModule(), import(colladaLoaderUrl), import(stlLoaderUrl), import(urdfLoaderUrl)]).then(
      ([THREE, colladaModule, stlModule, urdfModule]) => ({
        THREE,
        ColladaLoader: colladaModule.ColladaLoader,
        STLLoader: stlModule.STLLoader,
        URDFLoader: urdfModule.default || urdfModule.URDFLoader || urdfModule,
      }),
    );
  }
  return threeLoaderPromise;
}

function updateLidarCamera() {
  const lidar = state.lidarCloud;
  if (!lidar.camera || !lidar.controls) return;
  const controls = lidar.controls;
  const horizontal = controls.distance * Math.cos(controls.pitch);
  lidar.camera.position.set(
    controls.target.x + horizontal * Math.cos(controls.yaw),
    controls.target.y + horizontal * Math.sin(controls.yaw),
    controls.target.z + controls.distance * Math.sin(controls.pitch),
  );
  lidar.camera.lookAt(controls.target);
}

function resizeLidarViewer() {
  const lidar = state.lidarCloud;
  const container = $("#lidarScene");
  if (!container || !lidar.renderer || !lidar.camera) return;
  const rect = container.getBoundingClientRect();
  const width = Math.floor(rect.width);
  const height = Math.floor(rect.height);
  if (width <= 0 || height <= 0) return;
  lidar.camera.aspect = width / height;
  lidar.camera.updateProjectionMatrix();
  lidar.renderer.setSize(width, height, false);
}

function bindLidarViewerControls(surface) {
  const controls = state.lidarCloud.controls;
  if (!surface || !controls) return;

  surface.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    controls.dragging = true;
    controls.dragMode = viewerDragMode(event);
    controls.lastX = event.clientX;
    controls.lastY = event.clientY;
    surface.setPointerCapture(event.pointerId);
  });

  surface.addEventListener("pointermove", (event) => {
    if (!controls.dragging) return;
    const dx = event.clientX - controls.lastX;
    const dy = event.clientY - controls.lastY;
    controls.lastX = event.clientX;
    controls.lastY = event.clientY;
    if (controls.dragMode === "pan") {
      panViewerTarget(state.lidarCloud.camera, controls, surface, dx, dy);
    } else {
      controls.yaw -= dx * 0.006;
      controls.pitch = clamp(controls.pitch + dy * 0.006, -1.2, 1.35);
    }
    updateLidarCamera();
  });

  const release = (event) => {
    controls.dragging = false;
    controls.dragMode = "rotate";
    if (surface.hasPointerCapture(event.pointerId)) {
      surface.releasePointerCapture(event.pointerId);
    }
  };
  surface.addEventListener("pointerup", release);
  surface.addEventListener("pointercancel", release);
  surface.addEventListener("contextmenu", (event) => event.preventDefault());
  surface.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      controls.distance = clamp(controls.distance * (event.deltaY > 0 ? 1.1 : 0.9), 1.5, 160);
      updateLidarCamera();
    },
    { passive: false },
  );
}

async function initializeLidarViewer() {
  if (state.lidarCloud.initialized) return true;
  if (state.lidarCloud.initPromise) return state.lidarCloud.initPromise;

  state.lidarCloud.initPromise = loadThreeModule()
    .then((THREE) => {
      const container = $("#lidarScene");
      if (!container) return false;

      const scene = new THREE.Scene();
      scene.background = new THREE.Color(0x09111f);

      const camera = new THREE.PerspectiveCamera(58, 1, 0.05, 500);
      camera.up.set(0, 0, 1);

      const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
      renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2));
      renderer.setClearColor(0x09111f, 1);

      container.innerHTML = "";
      container.appendChild(renderer.domElement);

      const grid = new THREE.GridHelper(40, 40, 0x64748b, 0x1e293b);
      grid.rotation.x = Math.PI / 2;
      scene.add(grid);
      scene.add(new THREE.AxesHelper(2.4));

      const geometry = new THREE.BufferGeometry();
      const material = new THREE.PointsMaterial({
        size: lidarPointRadiusToMaterialSize(state.lidarCloud.pointRadius),
        map: createLidarPointTexture(THREE),
        vertexColors: true,
        sizeAttenuation: true,
        transparent: true,
        alphaTest: 0.12,
        opacity: 0.96,
      });
      const points = new THREE.Points(geometry, material);
      scene.add(points);

      state.lidarCloud.three = THREE;
      state.lidarCloud.scene = scene;
      state.lidarCloud.camera = camera;
      state.lidarCloud.renderer = renderer;
      state.lidarCloud.geometry = geometry;
      state.lidarCloud.material = material;
      state.lidarCloud.points = points;
      state.lidarCloud.controls = {
        yaw: -2.35,
        pitch: 0.52,
        distance: 18,
        target: new THREE.Vector3(0, 0, 0),
        dragging: false,
        dragMode: "rotate",
        lastX: 0,
        lastY: 0,
      };

      bindLidarViewerControls(renderer.domElement);
      state.lidarCloud.resizeObserver = new ResizeObserver(resizeLidarViewer);
      state.lidarCloud.resizeObserver.observe(container);
      window.addEventListener("resize", resizeLidarViewer);

      const animate = () => {
        state.lidarCloud.animationFrame = window.requestAnimationFrame(animate);
        renderer.render(scene, camera);
      };

      updateLidarCamera();
      resizeLidarViewer();
      animate();
      state.lidarCloud.initialized = true;
      renderLidarCloudStatus();
      return true;
    })
    .catch((error) => {
      state.lidarCloud.error = `3D 引擎加载失败：${error.message}`;
      renderLidarCloudStatus();
      return false;
    });

  return state.lidarCloud.initPromise;
}

function normalizeLidarPointRadius(value) {
  const numeric = Number(value);
  const fallback = Number.isFinite(state.lidarCloud.pointRadius) ? state.lidarCloud.pointRadius : lidarPointRadiusDefault;
  const clamped = clamp(Number.isFinite(numeric) ? numeric : fallback, lidarPointRadiusMin, lidarPointRadiusMax);
  return clamp(Math.round(clamped / lidarPointRadiusStep) * lidarPointRadiusStep, lidarPointRadiusMin, lidarPointRadiusMax);
}

function lidarPointRadiusToMaterialSize(radius) {
  return normalizeLidarPointRadius(radius) * 2;
}

function renderLidarPointRadiusControl() {
  const radius = normalizeLidarPointRadius(state.lidarCloud.pointRadius);
  const valueNode = $("#lidarPointRadiusValue");
  if (valueNode) valueNode.textContent = radius.toFixed(3);

  const input = $("#lidarPointRadiusInput");
  if (input) {
    input.min = String(lidarPointRadiusMin);
    input.max = String(lidarPointRadiusMax);
    input.step = String(lidarPointRadiusStep);
    input.value = radius.toFixed(3);
  }
}

function setLidarPointRadius(value) {
  const radius = normalizeLidarPointRadius(value);
  state.lidarCloud.pointRadius = radius;
  if (state.lidarCloud.material) {
    state.lidarCloud.material.size = lidarPointRadiusToMaterialSize(radius);
    state.lidarCloud.material.needsUpdate = true;
  }
  const robotLidarMaterial = state.robotModel.lidarOverlay.material;
  if (robotLidarMaterial) {
    robotLidarMaterial.size = lidarPointRadiusToMaterialSize(radius);
    robotLidarMaterial.needsUpdate = true;
  }
  renderLidarPointRadiusControl();
}

function createLidarPointTexture(THREE) {
  const size = 64;
  const canvas = document.createElement("canvas");
  canvas.width = size;
  canvas.height = size;
  const context = canvas.getContext("2d");
  const center = size / 2;
  const gradient = context.createRadialGradient(center, center, 0, center, center, center);
  gradient.addColorStop(0, "rgba(255, 255, 255, 1)");
  gradient.addColorStop(0.58, "rgba(255, 255, 255, 0.95)");
  gradient.addColorStop(1, "rgba(255, 255, 255, 0)");
  context.fillStyle = gradient;
  context.fillRect(0, 0, size, size);

  const texture = new THREE.CanvasTexture(canvas);
  texture.minFilter = THREE.LinearFilter;
  texture.magFilter = THREE.LinearFilter;
  texture.generateMipmaps = false;
  return texture;
}

function lidarAxisColor(xValue, yValue, zValue, colors, offset) {
  const x = clamp(xValue, 0, 1);
  const y = clamp(yValue, 0, 1);
  const z = clamp(zValue, 0, 1);
  colors[offset] = clamp(0.16 + 0.84 * x, 0, 1);
  colors[offset + 1] = clamp(0.16 + 0.84 * y, 0, 1);
  colors[offset + 2] = clamp(0.22 + 0.78 * z, 0, 1);
}

function updateLidarFrameRate() {
  const now = performance.now();
  const times = state.lidarCloud.frameTimes;
  times.push(now);
  while (times.length > 2 && now - times[0] > 3000) {
    times.shift();
  }
  if (times.length > 1) {
    const duration = (times[times.length - 1] - times[0]) / 1000;
    state.lidarCloud.frameRate = duration > 0 ? (times.length - 1) / duration : null;
  }
}

function buildLidarPointCloudAttributes(buffer) {
  const values = new Float32Array(buffer);
  const count = Math.floor(values.length / 4);
  const positions = new Float32Array(count * 3);
  const colors = new Float32Array(count * 3);
  let minX = Infinity;
  let minY = Infinity;
  let minZ = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;
  let maxZ = -Infinity;

  for (let index = 0; index < count; index += 1) {
    const source = index * 4;
    const target = index * 3;
    const x = values[source];
    const y = values[source + 1];
    const z = values[source + 2];
    positions[target] = x;
    positions[target + 1] = y;
    positions[target + 2] = z;
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    minZ = Math.min(minZ, z);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
    maxZ = Math.max(maxZ, z);
  }

  const xRange = maxX > minX ? maxX - minX : 1;
  const yRange = maxY > minY ? maxY - minY : 1;
  const zRange = maxZ > minZ ? maxZ - minZ : 1;
  for (let index = 0; index < count; index += 1) {
    const source = index * 4;
    const target = index * 3;
    lidarAxisColor(
      (values[source] - minX) / xRange,
      (values[source + 1] - minY) / yRange,
      (values[source + 2] - minZ) / zRange,
      colors,
      target,
    );
  }

  return { positions, colors, count, minX, minY, minZ, maxX, maxY, maxZ };
}

function ensureMappingMapLayer() {
  const robot = state.robotModel;
  const preview = state.mapping.mapPreview;
  if (!robot.three || !robot.scene) return false;

  if (!preview.points) {
    preview.geometry = new robot.three.BufferGeometry();
    preview.material = new robot.three.PointsMaterial({
      size: Math.max(0.012, lidarPointRadiusToMaterialSize(state.lidarCloud.pointRadius) * 0.7),
      map: createLidarPointTexture(robot.three),
      vertexColors: true,
      sizeAttenuation: true,
      transparent: true,
      alphaTest: 0.1,
      opacity: 0.9,
      depthWrite: false,
    });
    preview.points = new robot.three.Points(preview.geometry, preview.material);
    preview.points.name = "mapping_accumulated_map";
    preview.points.frustumCulled = false;
  }

  if (preview.points.parent !== robot.scene) {
    robot.scene.add(preview.points);
  }
  preview.initialized = true;
  preview.points.visible = !localizationViewActive() && preview.hasFrame;
  return true;
}

function frameMappingMapInRobotViewer(cloud) {
  const robot = state.robotModel;
  if (!robot.controls || !robot.three || !cloud || cloud.count <= 0) return;
  const centerX = (cloud.minX + cloud.maxX) / 2;
  const centerY = (cloud.minY + cloud.maxY) / 2;
  const centerZ = (cloud.minZ + cloud.maxZ) / 2;
  const dx = cloud.maxX - cloud.minX;
  const dy = cloud.maxY - cloud.minY;
  const dz = cloud.maxZ - cloud.minZ;
  const diagonal = Math.sqrt(dx * dx + dy * dy + dz * dz);
  robot.controls.target.set(centerX, centerY, centerZ);
  robot.controls.distance = clamp(diagonal * 1.35, 4, 160);
  updateRobotCamera();
}

function updateMappingMapPointCloud(buffer) {
  const robot = state.robotModel;
  const preview = state.mapping.mapPreview;
  if (!robot.three || !ensureMappingMapLayer()) return null;

  const cloud = buildLidarPointCloudAttributes(buffer);
  preview.geometry.setAttribute("position", new robot.three.BufferAttribute(cloud.positions, 3));
  preview.geometry.setAttribute("color", new robot.three.BufferAttribute(cloud.colors, 3));
  preview.geometry.computeBoundingSphere();
  preview.hasFrame = cloud.count > 0;
  preview.pointCount = cloud.count;
  syncRobotViewerLayersForView();
  if (preview.hasFrame) {
    pauseRobotLidarOverlayForMappingMap();
    frameMappingMapInRobotViewer(cloud);
  }
  return cloud;
}

function clearMappingMapPreview() {
  const preview = state.mapping.mapPreview;
  preview.hasFrame = false;
  preview.pointCount = 0;
  preview.sourcePointCount = 0;
  preview.sizeBytes = 0;
  preview.mtimeMs = null;
  preview.loadedRevision = "";
  preview.error = "";
  if (preview.points) preview.points.visible = false;
  if (state.robotModel.hasModel && state.robotModel.modelRoot && !mappingFinalTransform()) {
    frameRobotModelInViewer(state.robotModel.modelRoot);
    updateRobotModelTransforms();
  }
}

async function requestMappingMapFrame(revision = mappingMapRevision()) {
  const preview = state.mapping.mapPreview;
  if (!revision || preview.activeRequest) return null;
  preview.activeRequest = true;
  preview.error = "";
  renderMappingStatus();

  try {
    const initialized = await initializeRobotViewer();
    if (!initialized || !ensureMappingMapLayer()) throw new Error("整机 3D 视图未就绪");
    const response = await fetch(`/api/mapping/map/frame?t=${Date.now()}`, { cache: "no-store" });
    const contentType = response.headers.get("Content-Type") || "";
    if (!response.ok || contentType.includes("application/json")) {
      const payload = contentType.includes("application/json") ? await response.json() : null;
      throw new Error((payload && payload.detail) || `HTTP ${response.status}`);
    }

    const buffer = await response.arrayBuffer();
    const cloud = updateMappingMapPointCloud(buffer);
    if (!cloud) throw new Error("累计地图渲染失败");
    const pointCount = Number(response.headers.get("X-Robot-Station-PointCloud-Point-Count"));
    const sourcePointCount = Number(response.headers.get("X-Robot-Station-PointCloud-Source-Point-Count"));
    const sizeBytes = Number(response.headers.get("X-Robot-Station-Mapping-Map-Size-Bytes"));
    const mtimeMs = Number(response.headers.get("X-Robot-Station-Mapping-Map-Mtime-Ms"));
    preview.pointCount = Number.isFinite(pointCount) ? pointCount : cloud.count;
    preview.sourcePointCount = Number.isFinite(sourcePointCount) ? sourcePointCount : preview.pointCount;
    preview.sizeBytes = Number.isFinite(sizeBytes) ? sizeBytes : buffer.byteLength;
    preview.mtimeMs = Number.isFinite(mtimeMs) ? mtimeMs : Date.now();
    preview.loadedRevision = revision;
    preview.error = "";
    updateRobotModelTransforms();
    renderRobotViewStatus();
    return cloud;
  } catch (error) {
    preview.error = error.message;
    if (preview.points) preview.points.visible = false;
    return null;
  } finally {
    preview.activeRequest = false;
    renderMappingStatus();
  }
}

function syncMappingMapPreview() {
  const session = state.mapping.session;
  if (session?.status === "failed" || session?.progress?.phase === "failed") {
    if (!state.mapping.mapPreview.hasFrame) clearMappingMapPreview();
    return;
  }
  const revision = mappingMapRevision();
  if (!revision) {
    clearMappingMapPreview();
    return;
  }
  if (!state.mapping.busy && revision !== state.mapping.mapPreview.loadedRevision) {
    requestMappingMapFrame(revision);
  }
}

function ensureLocalizationMapLayer() {
  const robot = state.robotModel;
  const preview = state.localization.mapPreview;
  if (!robot.three || !robot.scene) return false;

  if (!preview.points) {
    preview.geometry = new robot.three.BufferGeometry();
    preview.material = new robot.three.PointsMaterial({
      size: Math.max(0.014, lidarPointRadiusToMaterialSize(state.lidarCloud.pointRadius) * 0.78),
      map: createLidarPointTexture(robot.three),
      vertexColors: true,
      sizeAttenuation: true,
      transparent: true,
      alphaTest: 0.1,
      opacity: 0.92,
      depthWrite: false,
    });
    preview.points = new robot.three.Points(preview.geometry, preview.material);
    preview.points.name = "localization_saved_map";
    preview.points.frustumCulled = false;
  }

  if (preview.points.parent !== robot.scene) {
    robot.scene.add(preview.points);
  }
  preview.initialized = true;
  preview.points.visible = localizationMapVisible();
  return true;
}

function frameLocalizationMapInRobotViewer(bounds = state.localization.mapPreview.bounds) {
  const robot = state.robotModel;
  if (!robot.controls || !robot.three || !bounds || bounds.count <= 0) return;
  const centerX = (bounds.minX + bounds.maxX) / 2;
  const centerY = (bounds.minY + bounds.maxY) / 2;
  const centerZ = (bounds.minZ + bounds.maxZ) / 2;
  const dx = bounds.maxX - bounds.minX;
  const dy = bounds.maxY - bounds.minY;
  const dz = bounds.maxZ - bounds.minZ;
  const diagonal = Math.sqrt(dx * dx + dy * dy + dz * dz);
  robot.controls.yaw = -2.35;
  robot.controls.pitch = 0.86;
  robot.controls.target.set(centerX, centerY, centerZ);
  robot.controls.distance = clamp(diagonal * 1.25, 5, 180);
  updateRobotCamera();
}

function updateLocalizationMapPointCloud(buffer) {
  const robot = state.robotModel;
  const preview = state.localization.mapPreview;
  if (!robot.three || !ensureLocalizationMapLayer()) return null;

  const cloud = buildLidarPointCloudAttributes(buffer);
  preview.geometry.setAttribute("position", new robot.three.BufferAttribute(cloud.positions, 3));
  preview.geometry.setAttribute("color", new robot.three.BufferAttribute(cloud.colors, 3));
  preview.geometry.computeBoundingSphere();
  preview.hasFrame = cloud.count > 0;
  preview.pointCount = cloud.count;
  preview.bounds = cloud;
  syncRobotViewerLayersForView();
  if (preview.hasFrame) {
    frameLocalizationMapInRobotViewer(cloud);
  }
  return cloud;
}

function clearLocalizationMapPreview() {
  const preview = state.localization.mapPreview;
  preview.hasFrame = false;
  preview.pointCount = 0;
  preview.sourcePointCount = 0;
  preview.sizeBytes = 0;
  preview.mtimeMs = null;
  preview.loadedName = "";
  preview.error = "";
  preview.bounds = null;
  if (preview.points) preview.points.visible = false;
}

async function requestLocalizationMapFrame(mapName = state.localization.selectedMapName) {
  const preview = state.localization.mapPreview;
  const targetName = String(mapName || "").trim();
  if (!targetName || preview.activeRequest) return null;
  preview.activeRequest = true;
  preview.error = "";
  renderLocalizationStatus();

  try {
    await ensureLocalizationRobotModel();
    if (!ensureLocalizationMapLayer()) throw new Error("定位 3D 视图未就绪");
    syncRobotViewerMount();
    const response = await fetch(`/api/localization/maps/${encodeURIComponent(targetName)}/frame?t=${Date.now()}`, { cache: "no-store" });
    const contentType = response.headers.get("Content-Type") || "";
    if (!response.ok || contentType.includes("application/json")) {
      const payload = contentType.includes("application/json") ? await response.json() : null;
      throw new Error((payload && payload.detail) || `HTTP ${response.status}`);
    }

    const buffer = await response.arrayBuffer();
    const cloud = updateLocalizationMapPointCloud(buffer);
    if (!cloud) throw new Error("定位地图渲染失败");
    const pointCount = Number(response.headers.get("X-Robot-Station-PointCloud-Point-Count"));
    const sourcePointCount = Number(response.headers.get("X-Robot-Station-PointCloud-Source-Point-Count"));
    const sizeBytes = Number(response.headers.get("X-Robot-Station-Localization-Map-Size-Bytes"));
    const mtimeMs = Number(response.headers.get("X-Robot-Station-Localization-Map-Mtime-Ms"));
    preview.pointCount = Number.isFinite(pointCount) ? pointCount : cloud.count;
    preview.sourcePointCount = Number.isFinite(sourcePointCount) ? sourcePointCount : preview.pointCount;
    preview.sizeBytes = Number.isFinite(sizeBytes) ? sizeBytes : buffer.byteLength;
    preview.mtimeMs = Number.isFinite(mtimeMs) ? mtimeMs : Date.now();
    preview.loadedName = targetName;
    preview.error = "";
    updateRobotModelTransforms();
    syncRobotViewerLayersForView();
    renderRobotViewStatus();
    addLog("定位", `地图点云已加载：${targetName} / ${preview.pointCount.toLocaleString("zh-CN")} 点`);
    return cloud;
  } catch (error) {
    preview.error = error.message;
    if (preview.points) preview.points.visible = false;
    addLog("定位", `地图点云加载失败：${error.message}`);
    return null;
  } finally {
    preview.activeRequest = false;
    renderLocalizationStatus();
  }
}

function resetLocalizationView() {
  if (state.localization.mapPreview.bounds) {
    frameLocalizationMapInRobotViewer();
    return;
  }
  requestLocalizationMapFrame();
}

function centerLocalizationRobot() {
  ensureLocalizationRobotModel().then(() => {
    const robot = state.robotModel;
    if (!robot.controls) return;
    robot.controls.target.set(0, 0, 0.6);
    robot.controls.distance = clamp(robot.controls.distance || 7.2, 3, 18);
    updateRobotCamera();
  });
}

function updateLidarPointCloud(buffer) {
  const lidar = state.lidarCloud;
  const THREE = lidar.three;
  if (!THREE || !lidar.geometry) return;

  const cloud = buildLidarPointCloudAttributes(buffer);
  if (lidar.points) lidar.points.visible = true;
  const firstFrame = !lidar.hasFrame && cloud.count > 0;
  lidar.geometry.setAttribute("position", new THREE.BufferAttribute(cloud.positions, 3));
  lidar.geometry.setAttribute("color", new THREE.BufferAttribute(cloud.colors, 3));
  lidar.geometry.computeBoundingSphere();

  if (firstFrame && lidar.controls) {
    const centerX = (cloud.minX + cloud.maxX) / 2;
    const centerY = (cloud.minY + cloud.maxY) / 2;
    const centerZ = (cloud.minZ + cloud.maxZ) / 2;
    const dx = cloud.maxX - cloud.minX;
    const dy = cloud.maxY - cloud.minY;
    const dz = cloud.maxZ - cloud.minZ;
    const diagonal = Math.sqrt(dx * dx + dy * dy + dz * dz);
    lidar.controls.target.set(centerX, centerY, centerZ);
    lidar.controls.distance = clamp(diagonal * 1.4, 5, 120);
    updateLidarCamera();
  }

  lidar.hasFrame = cloud.count > 0;
  updateLidarFrameRate();
}

function updateRobotLidarPointCloud(positions, colors, count) {
  const robot = state.robotModel;
  const overlay = robot.lidarOverlay;
  if (!overlay.enabled) return;
  if (mappingMapVisible()) {
    pauseRobotLidarOverlayForMappingMap();
    return;
  }
  if (!robotLidarFrameMatches()) {
    overlay.error = `点云 frame=${overlay.lastFrameId || "--"} 与模型 frame=${robotLidarFrameName()} 不匹配`;
    if (overlay.points) overlay.points.visible = false;
    renderRobotLidarButton();
    return;
  }
  if (!ensureRobotLidarOverlay() || !overlay.geometry || !robot.three) return;

  overlay.geometry.setAttribute("position", new robot.three.BufferAttribute(new Float32Array(positions), 3));
  overlay.geometry.setAttribute("color", new robot.three.BufferAttribute(new Float32Array(colors), 3));
  overlay.geometry.computeBoundingSphere();
  overlay.points.visible = count > 0;
  overlay.error = "";
  renderRobotLidarButton();
}

function applyLidarCloudPayload(payload) {
  const clouds = payload && Array.isArray(payload.clouds) ? payload.clouds : [];
  const cloud = clouds.find((entry) => entry.key === lidarViewerCloudKey) || clouds[0];
  state.lidarCloud.clouds = clouds;
  if (!cloud) return false;
  state.lidarCloud.hasFrame = Boolean(cloud.hasFrame) || state.lidarCloud.hasFrame;
  state.lidarCloud.stale = cloud.stale !== undefined ? Boolean(cloud.stale) : state.lidarCloud.stale;
  state.lidarCloud.ageMs = Number.isFinite(Number(cloud.ageMs)) ? Number(cloud.ageMs) : state.lidarCloud.ageMs;
  state.lidarCloud.pointCount = Number.isFinite(Number(cloud.pointCount)) ? Number(cloud.pointCount) : state.lidarCloud.pointCount;
  state.lidarCloud.sourcePointCount = Number.isFinite(Number(cloud.sourcePointCount))
    ? Number(cloud.sourcePointCount)
    : state.lidarCloud.sourcePointCount;
  state.lidarCloud.frameId = cloud.frameId || state.lidarCloud.frameId;
  state.lidarCloud.receivedAt = cloud.receivedAt || state.lidarCloud.receivedAt;
  state.lidarCloud.sequence = Number.isFinite(Number(cloud.sequence)) ? Number(cloud.sequence) : state.lidarCloud.sequence;
  state.lidarCloud.error = cloud.parseError || (payload.ok ? "" : payload.detail || state.lidarCloud.error);
  renderLidarCloudStatus();
  renderRobotLidarButton();
  return true;
}

async function fetchLidarCloudStatus(options = {}) {
  if (!state.lidarCloud.previewEnabled) {
    renderLidarCloudStatus();
    return null;
  }
  try {
    const response = await fetch("/api/sensors/lidar", { cache: "no-store" });
    const payload = await response.json();
    if (!payload || !Array.isArray(payload.clouds)) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    applyLidarCloudPayload(payload);
    if (!payload.ok && !options.silent) {
      addLog("LiDAR", `点云状态异常：${payload.detail || payload.code}`);
    }
    return payload;
  } catch (error) {
    state.lidarCloud.error = error.message;
    renderLidarCloudStatus();
    if (!options.silent) {
      addLog("LiDAR", `点云状态查询失败：${error.message}`);
    }
    return null;
  }
}

function lidarFrameUrl(key = lidarViewerCloudKey, options = {}) {
  const params = new URLSearchParams({
    wait: String(options.waitSec ?? lidarFrameWaitSec),
    max_points: String(lidarMaxPoints),
    t: String(Date.now()),
  });
  const sequence = Number(options.afterSequence ?? state.lidarCloud.sequence);
  if (Number.isFinite(sequence)) {
    params.set("after", String(sequence));
  }
  return `/api/sensors/lidar/${encodeURIComponent(key)}/frame?${params.toString()}`;
}

function scheduleLidarFrame(delayMs = lidarFrameIntervalMs) {
  if (!state.lidarCloud.previewEnabled) return;
  window.clearTimeout(state.lidarCloud.frameTimer);
  state.lidarCloud.frameTimer = window.setTimeout(() => {
    requestLidarFrame();
  }, delayMs);
}

function scheduleRobotLidarFrame(delayMs = lidarFrameIntervalMs) {
  const overlay = state.robotModel.lidarOverlay;
  window.clearTimeout(overlay.frameTimer);
  if (!overlay.enabled) return;
  overlay.frameTimer = window.setTimeout(() => {
    requestRobotLidarFrame();
  }, delayMs);
}

async function requestLidarFrame() {
  if (!state.lidarCloud.previewEnabled) return;
  if (state.lidarCloud.activeRequest) return;
  const startedAt = performance.now();
  state.lidarCloud.activeRequest = true;
  try {
    await initializeLidarViewer();
    const response = await fetch(lidarFrameUrl(lidarViewerCloudKey), { cache: "no-store" });
    const contentType = response.headers.get("Content-Type") || "";
    if (!response.ok || contentType.includes("application/json")) {
      const payload = contentType.includes("application/json") ? await response.json() : null;
      throw new Error((payload && payload.detail) || `HTTP ${response.status}`);
    }

    const buffer = await response.arrayBuffer();
    if (!state.lidarCloud.previewEnabled) return;
    const sequence = Number(response.headers.get("X-Robot-Station-PointCloud-Sequence"));
    const ageMs = Number(response.headers.get("X-Robot-Station-PointCloud-Age-Ms"));
    const stale = response.headers.get("X-Robot-Station-PointCloud-Stale") === "1";
    const pointCount = Number(response.headers.get("X-Robot-Station-PointCloud-Point-Count"));
    const sourcePointCount = Number(response.headers.get("X-Robot-Station-PointCloud-Source-Point-Count"));
    state.lidarCloud.sequence = Number.isFinite(sequence) ? sequence : state.lidarCloud.sequence;
    state.lidarCloud.ageMs = Number.isFinite(ageMs) ? ageMs : state.lidarCloud.ageMs;
    state.lidarCloud.stale = stale;
    state.lidarCloud.pointCount = Number.isFinite(pointCount) ? pointCount : Math.floor(buffer.byteLength / 16);
    state.lidarCloud.sourcePointCount = Number.isFinite(sourcePointCount) ? sourcePointCount : state.lidarCloud.pointCount;
    state.lidarCloud.frameId = response.headers.get("X-Robot-Station-PointCloud-Frame-Id") || state.lidarCloud.frameId;
    state.lidarCloud.error = "";
    state.robotModel.lidarOverlay.error = "";
    updateLidarPointCloud(buffer);
    renderLidarCloudStatus();
  } catch (error) {
    state.lidarCloud.error = error.message;
    renderLidarCloudStatus();
  } finally {
    state.lidarCloud.activeRequest = false;
    const elapsed = performance.now() - startedAt;
    const delay = state.lidarCloud.error ? 1000 : Math.max(60, lidarFrameIntervalMs - elapsed);
    scheduleLidarFrame(delay);
  }
}

async function requestRobotLidarFrame() {
  const overlay = state.robotModel.lidarOverlay;
  if (!overlay.enabled || overlay.activeRequest) return;
  if (!ensureRobotLidarOverlay()) return;

  const startedAt = performance.now();
  overlay.activeRequest = true;
  try {
    const response = await fetch(
      lidarFrameUrl(robotLidarCloudKey, {
        afterSequence: overlay.sequence,
        waitSec: lidarFrameWaitSec,
      }),
      { cache: "no-store" },
    );
    const contentType = response.headers.get("Content-Type") || "";
    if (!response.ok || contentType.includes("application/json")) {
      const payload = contentType.includes("application/json") ? await response.json() : null;
      throw new Error((payload && payload.detail) || `HTTP ${response.status}`);
    }

    const buffer = await response.arrayBuffer();
    const sequence = Number(response.headers.get("X-Robot-Station-PointCloud-Sequence"));
    const frameId = response.headers.get("X-Robot-Station-PointCloud-Frame-Id") || "";
    overlay.sequence = Number.isFinite(sequence) ? sequence : overlay.sequence;
    overlay.lastFrameId = frameId;
    overlay.error = "";
    const cloud = buildLidarPointCloudAttributes(buffer);
    updateRobotLidarPointCloud(cloud.positions, cloud.colors, cloud.count);
  } catch (error) {
    overlay.error = error.message;
    if (overlay.points) overlay.points.visible = false;
    renderRobotLidarButton();
  } finally {
    overlay.activeRequest = false;
    const elapsed = performance.now() - startedAt;
    const delay = overlay.error ? 1000 : Math.max(60, lidarFrameIntervalMs - elapsed);
    scheduleRobotLidarFrame(delay);
  }
}

function renderLidarCloudStatus() {
  const lidar = state.lidarCloud;
  const selectedCloud = lidar.clouds.find((entry) => entry.key === lidarViewerCloudKey) || lidar.clouds[0];
  const topic = (selectedCloud && selectedCloud.topic) || "/rslidar_points";
  const topicNode = $("#lidarCloudTopic");
  if (topicNode) topicNode.textContent = topic;
  renderLidarPreviewToggle();

  if (!lidar.previewEnabled) {
    setStateBadge("#lidarCloudStatus", "回显关闭", "idle");
    const pointCount = $("#lidarPointCount");
    if (pointCount) pointCount.textContent = "0";
    const age = $("#lidarFrameAge");
    if (age) age.textContent = "--";
    const rate = $("#lidarFrameRate");
    if (rate) rate.textContent = "--";
    const frameId = $("#lidarFrameId");
    if (frameId) frameId.textContent = "--";
    renderLidarPointRadiusControl();
    renderRobotLidarButton();
    const overlay = $("#lidarOverlay");
    if (overlay) overlay.textContent = "回显关闭";
    return;
  }

  let badgeText = "等待点云";
  let badgeLevel = "idle";
  if (lidar.error) {
    badgeText = "异常";
    badgeLevel = "danger";
  } else if (lidar.hasFrame && lidar.stale) {
    badgeText = "过期";
    badgeLevel = "warn";
  } else if (lidar.hasFrame) {
    badgeText = "实时";
    badgeLevel = "ok";
  }
  setStateBadge("#lidarCloudStatus", badgeText, badgeLevel);

  const pointCount = $("#lidarPointCount");
  if (pointCount) pointCount.textContent = Math.max(0, Math.round(lidar.pointCount || 0)).toLocaleString("zh-CN");
  const age = $("#lidarFrameAge");
  if (age) age.textContent = lidarAgeText(lidar.ageMs);
  const rate = $("#lidarFrameRate");
  if (rate) rate.textContent = Number.isFinite(lidar.frameRate) ? lidar.frameRate.toFixed(1) : "--";
  const frameId = $("#lidarFrameId");
  if (frameId) frameId.textContent = lidar.frameId || "--";
  renderLidarPointRadiusControl();
  renderRobotLidarButton();

  const overlay = $("#lidarOverlay");
  if (overlay) {
    overlay.textContent = lidar.error || (lidar.hasFrame ? "" : `等待 ${topic}`);
  }
}

function bindEvents() {
  $("#authLoginForm").addEventListener("submit", (event) => {
    event.preventDefault();
    submitAuthLogin(false);
  });
  $("#authForceButton").addEventListener("click", () => submitAuthLogin(true));
  $("#authPauseButton").addEventListener("click", () => {
    const active = authActiveUserLabel(state.auth.conflict);
    state.auth.conflict = null;
    setAuthMessage(`已暂停登录，等待 ${active} 退出。`, "idle");
    renderAuth();
  });
  $("#authLogoutButton").addEventListener("click", logoutAuth);

  $$(".nav-item").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));
  $$("[data-view-jump]").forEach((button) => button.addEventListener("click", () => showView(button.dataset.viewJump)));

  $("#drawerToggle").addEventListener("click", () => $("#eventDrawer").classList.toggle("is-open"));
  $("#clearEventsButton").addEventListener("click", () => {
    state.logs = [];
    renderLogs();
  });

  $$(".drawer-tabs button").forEach((button) => {
    button.addEventListener("click", () => {
      $$(".drawer-tabs button").forEach((item) => item.classList.toggle("is-active", item === button));
      $$(".drawer-panel").forEach((panel) => panel.classList.toggle("is-active", panel.dataset.drawerPanel === button.dataset.drawerTab));
    });
  });

  $$(".segmented button").forEach((button) => {
    button.addEventListener("click", () => {
      $$(".segmented button").forEach((item) => item.classList.toggle("is-active", item === button));
      $$(".sensor-panel").forEach((panel) => panel.classList.toggle("is-active", panel.dataset.sensorPanel === button.dataset.sensorTab));
      if (button.dataset.sensorTab === "lidar") {
        window.setTimeout(resizeLidarViewer, 0);
      }
    });
  });

  $("#runSelfCheckButton").addEventListener("click", runSelfCheck);
  $("#rerunProblemChecksButton").addEventListener("click", rerunProblemChecks);
  $("#canStatus").addEventListener("click", () => activateCanInterface(currentCanCheckResult(), { confirm: false }));
  $("#piperRuntimeStatus").addEventListener("click", togglePiperRuntime);
  $("#liftingRuntimeStatus").addEventListener("click", toggleLiftingRuntime);
  $("#chassisRuntimeStatus").addEventListener("click", toggleChassisRuntime);
  $("#localizationRuntimeStatus").addEventListener("click", toggleLocalizationRuntime);
  $("#chassisKeyboardButton").addEventListener("click", toggleChassisKeyboardListening);
  $("#baseOdomResetButton").addEventListener("click", resetChassisOdometry);
  document.addEventListener("keydown", handleChassisKeyboardKeyDown);
  document.addEventListener("keyup", handleChassisKeyboardKeyUp);
  window.addEventListener("blur", () => {
    if (state.chassisControl.keyboardListening) {
      stopChassisKeyboardControl("窗口失焦，键盘监听停止", { deactivate: true });
    }
  });
  $("#cameraRuntimeStatus").addEventListener("click", toggleCameraRuntime);
  $("#lidarRuntimeStatus").addEventListener("click", toggleLidarRuntime);
  $("#cameraPreviewToggleButton").addEventListener("click", toggleCameraPreview);
  $("#lidarPreviewToggleButton").addEventListener("click", toggleLidarPreview);
  const lidarPointRadiusInput = $("#lidarPointRadiusInput");
  if (lidarPointRadiusInput) {
    lidarPointRadiusInput.addEventListener("input", (event) => setLidarPointRadius(event.currentTarget.value));
    renderLidarPointRadiusControl();
  }
  $("#robotModelSelect").addEventListener("change", (event) => {
    state.robotModel.selectedKey = event.currentTarget.value;
    const selected = state.robotModel.models.find((model) => model.key === state.robotModel.selectedKey);
    if (state.robotModel.loadedKey === state.robotModel.selectedKey && state.robotModel.hasModel) {
      setRobotLoadProgress({
        active: false,
        value: 100,
        label: "加载完成",
        detail: `${selected?.name || state.robotModel.selectedKey} 已显示在整机视图`,
        level: "ok",
      });
      setRobotModelStatus("ready", `${selected?.name || state.robotModel.selectedKey} 已加载到整机视图`);
      return;
    }
    setRobotLoadProgress({
      active: false,
      value: 0,
      label: "等待加载",
      detail: selected ? "点击加载读取 URDF 与 mesh" : "请选择整机模型",
      level: "idle",
      meshLoaded: 0,
      meshTotal: 0,
    });
    setRobotModelStatus("available", selected ? `已选择 ${selected.name || selected.key}，点击加载显示 URDF` : "请选择整机模型");
  });
  $("#robotModelLoadButton").addEventListener("click", () => {
    loadRobotModel();
  });
  $("#robotPoseSyncButton").addEventListener("click", toggleRobotPoseSync);
  $("#robotLidarToggleButton").addEventListener("click", toggleRobotLidarOverlay);
  $("#mappingStartButton").addEventListener("click", startMappingSession);
  $("#mappingCaptureButton").addEventListener("click", captureMappingKeyframe);
  $("#mappingSaveButton").addEventListener("click", saveMappingMap);
  $("#mappingDeleteLastButton").addEventListener("click", deleteLastMappingKeyframe);
  $("#mappingResetButton").addEventListener("click", resetMappingSession);
  $("#mappingChassisKeyboardButton").addEventListener("click", toggleChassisKeyboardListening);
  $("#mappingConfigForm").addEventListener("input", () => {
    Object.assign(state.mapping, readMappingSettings());
    renderMappingStatus();
  });
  $("#localizationMapSelect").addEventListener("change", (event) => {
    selectLocalizationMap(event.currentTarget.value);
  });
  $("#localizationRefreshMapsButton").addEventListener("click", () => fetchLocalizationMaps());
  $("#localizationResetViewButton").addEventListener("click", resetLocalizationView);
  $("#localizationCenterRobotButton").addEventListener("click", centerLocalizationRobot);
  $("#armCompareList").addEventListener("input", (event) => {
    const input = event.target.closest("[data-action-kind]");
    if (!input) return;
    updateArmActionFromInput(input, { render: false });
  });
  $("#armCompareList").addEventListener("change", (event) => {
    const input = event.target.closest("[data-action-kind]");
    if (!input) return;
    updateArmActionFromInput(input, { render: false });
    renderArmComparisons({ force: true });
  });
  $("#copyAllArmStateButton").addEventListener("click", copyAllStatesToActions);
  $("#armControlToggleButton").addEventListener("click", toggleArmDirectControl);
  $("#armHomeButton").addEventListener("click", zeroAllArmActions);
  $("#jointSpeedInput").addEventListener("input", (event) => updateJointSpeedFromInput(event.currentTarget));
  const startHomingButton = $("#startHomingButton");
  if (startHomingButton) startHomingButton.addEventListener("click", startHoming);
  $("#startCollectionButton").addEventListener("click", startCollection);
  $("#pauseCollectionButton").addEventListener("click", pauseCollection);
  $("#finishCollectionButton").addEventListener("click", () => finishCollection("完成"));
  $("#discardEpisodeButton").addEventListener("click", () => finishCollection("废弃"));
  $("#markSuccessButton").addEventListener("click", () => finishCollection("成功"));
  $("#markFailButton").addEventListener("click", () => finishCollection("失败"));
  $("#inferenceConnectButton").addEventListener("click", connectInference);
  $("#inferenceDisconnectButton").addEventListener("click", disconnectInference);
  $("#inferenceEnablePiperButton").addEventListener("click", enablePiperForInference);
  $("#requestChunkButton").addEventListener("click", requestInferenceChunk);
  $("#executeChunkButton").addEventListener("click", executeInferenceChunk);
  $("#inferenceLoopToggle").addEventListener("change", toggleInferenceLoop);
  $("#inferenceMaskPanel").addEventListener("click", handleMaskClick);
  $("#stopInferenceButton").addEventListener("click", stopInference);
  const playbackPathInput = $("#playbackPathInput");
  if (playbackPathInput) {
    playbackPathInput.addEventListener("input", (event) => {
      const wasRunning = state.playback.running;
      state.playback.path = String(event.currentTarget.value || "").trim();
      state.playback.elapsedSec = 0;
      state.playback.dataset = null;
      state.playback.loadedPath = "";
      state.playback.loadError = "";
      state.playback.lastError = "";
      if (wasRunning) {
        requestPlaybackAction("stop").catch((error) => addLog("数采", `数据回放路径变更停止失败：${error.message}`));
      }
      setPlaybackRunning(false);
      renderPlayback();
    });
  }
  const playbackJointSpeedInput = $("#playbackJointSpeedInput");
  if (playbackJointSpeedInput) {
    playbackJointSpeedInput.addEventListener("input", (event) => {
      updatePlaybackJointSpeedFromInput(event.currentTarget);
      renderPlayback();
    });
  }
  const playbackChartTabs = $("#playbackChartTabs");
  if (playbackChartTabs) {
    playbackChartTabs.addEventListener("click", (event) => {
      const button = event.target.closest("[data-playback-chart-group]");
      if (!button) return;
      state.playback.chartGroup = button.dataset.playbackChartGroup || "all";
      renderPlayback();
    });
  }
  const playbackEnableRobotButton = $("#playbackEnableRobotButton");
  if (playbackEnableRobotButton) playbackEnableRobotButton.addEventListener("click", togglePlaybackRobotEnable);
  const playbackReplayButton = $("#playbackReplayButton");
  if (playbackReplayButton) playbackReplayButton.addEventListener("click", startPlaybackRun);
  const playbackStopButton = $("#playbackStopButton");
  if (playbackStopButton) playbackStopButton.addEventListener("click", stopPlaybackRun);
  $("#stopTaskButton").addEventListener("click", stopCurrentTask);
  $("#estopButton").addEventListener("click", triggerEmergencyStop);
  $("#alertStatus").addEventListener("mouseenter", (event) => showAlertTooltip(event.currentTarget));
  $("#alertStatus").addEventListener("mouseleave", hideRichTooltip);

  $$("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.action;
      if (action === "self-check") {
        showView("self-check");
        runSelfCheck();
      }
      if (action === "homing") {
        showView("homing");
        startHoming();
      }
      if (action === "collection") {
        showView("collection");
        startCollection();
      }
      if (action === "inference") {
        showView("inference");
      }
      if (action === "device-control") {
        showView("device-control");
      }
      if (action === "platform-control") {
        showView("platform-control");
      }
    });
  });

  $("#selfCheckTable").addEventListener("mouseover", (event) => {
    const row = event.target.closest(".check-row");
    if (!row || !$("#selfCheckTable").contains(row)) return;
    showCheckTooltip(row);
  });
  $("#selfCheckTable").addEventListener("mouseout", (event) => {
    const row = event.target.closest(".check-row");
    if (!row || row.contains(event.relatedTarget)) return;
    hideRichTooltip();
  });
  $("#selfCheckTable").addEventListener("click", (event) => {
    const button = event.target.closest("[data-check-action]");
    if (!button) return;
    const item = state.selfCheckResults[Number(button.dataset.checkIndex)];
    if (!item) return;
    if (button.dataset.checkAction === "log") {
      addLog(item.source, `查看检查项日志：${item.name} / ${item.code}`);
      state.activeLogFilter = item.source;
      renderLogFilters();
      renderLogs();
      showView("logs");
    }
    if (button.dataset.checkAction === "retry") {
      addLog(item.source, `复查检查项：${item.name}`);
      runSelfCheck();
    }
    if (button.dataset.checkAction === "activate" && item.name === "CAN 接口") {
      activateCanInterface(item);
    }
  });

  $$("[data-device-drive], [data-mapping-drive]").forEach((button) => {
    const label = button.textContent.trim();
    const action = button.dataset.deviceDrive || button.dataset.mappingDrive;
    button.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      startChassisDrive(action, label);
    });
    button.addEventListener("pointerup", () => {
      stopChassisDrive("松开停止");
    });
    button.addEventListener("pointercancel", () => {
      stopChassisDrive("取消点动");
    });
    button.addEventListener("pointerleave", () => {
      stopChassisDrive("离开按钮区域，停止");
    });
  });

  $$("[data-device-stop]").forEach((button) => {
    button.addEventListener("click", () => {
      if (button.dataset.deviceStop === "lift") {
        requestLiftingControl("stop", {}, { source: "停止升降轴", mode: "停止" });
        return;
      }
      addLog("系统", `设备停止：${button.dataset.deviceStop}`);
    });
  });

  const handleBaseControlInput = (event) => {
    const input = event.target.closest("[data-base-control]");
    if (!input) return;
    const item = deviceBaseControlItems.find((entry) => entry.key === input.dataset.baseControl);
    if (!item) return;
    const value = Number(input.value);
    if (!Number.isFinite(value)) return;
    item.value = clamp(value, item.min, item.max);
    const row = input.closest(".base-speed-row");
    if (row) {
      row.style.setProperty("--speed-risk", `${clamp(item.value, 0, 1) * 100}%`);
      row.style.setProperty("--speed-color", speedRiskColor(item.value));
    }
    input.setAttribute("aria-valuetext", formatCommandSpeed(item));
    const preview = row?.querySelector("strong");
    if (preview) preview.textContent = formatCommandSpeed(item);
    renderBaseControlPanel(event.currentTarget.id === "deviceBaseControlPanel" ? "#mappingBaseControlPanel" : "#deviceBaseControlPanel");
    renderDeviceBaseMetrics();
    if (state.chassisControl.activeDrive) {
      requestChassisVelocity(chassisCommandForDrive(state.chassisControl.activeDrive), { source: "速度调整", quiet: true });
    }
  };
  $("#deviceBaseControlPanel").addEventListener("input", handleBaseControlInput);
  $("#mappingBaseControlPanel").addEventListener("input", handleBaseControlInput);

  $("#liftControlPanel").addEventListener("input", (event) => {
    const input = event.target.closest("[data-lift-control]");
    const stepInput = event.target.closest("[data-lift-step]");
    if (!input && !stepInput) return;
    if (stepInput) {
      const value = Number(stepInput.value);
      if (!Number.isFinite(value)) return;
      if (stepInput.dataset.liftStep === "up") state.liftPreview.stepUpMm = value;
      if (stepInput.dataset.liftStep === "down") state.liftPreview.stepDownMm = value;
      renderLiftPreview();
      return;
    }
    if (input.value === "") return;
    const value = Number(input.value);
    if (!Number.isFinite(value)) return;
    if (input.dataset.liftControl === "height") {
      const min = Number(input.min);
      const max = Number(input.max);
      const clampedHeight = clamp(value, Number.isFinite(min) ? min : liftPreviewLimits.min, Number.isFinite(max) ? max : liftPreviewLimits.max);
      state.liftPreview.height = clampedHeight;
      if (input.type === "number" && value !== clampedHeight) input.value = clampedHeight.toFixed(2);
      state.liftPreview.mode = "目标高度";
    }
    if (input.dataset.liftControl === "speed") {
      state.liftPreview.speed = value;
      state.liftPreview.mode = "速度已设置";
    }
    renderLiftPreview();
  });

  $$("[data-lift-move]").forEach((button) => {
    button.addEventListener("click", () => {
      commandLiftRelative(button.dataset.liftMove);
    });
  });

  $$("[data-lift-preset]").forEach((button) => {
    button.addEventListener("click", () => {
      const preset = Number(button.dataset.liftPreset);
      if (!Number.isFinite(preset)) return;
      state.liftPreview.height = preset;
      state.liftPreview.mode = `${button.textContent.trim()}目标`;
      renderLiftPreview();
      addLog("升降轴", `目标高度切换到 ${button.textContent.trim()}`);
    });
  });

  const liftApplyHeightButton = $("#liftApplyHeightButton");
  if (liftApplyHeightButton) {
    liftApplyHeightButton.addEventListener("click", () => {
      commandLiftHeight("执行升降轴目标高度");
    });
  }
  const liftInitButton = $("#liftInitButton");
  if (liftInitButton) {
    liftInitButton.addEventListener("click", () => {
      requestLiftingControl("init", {}, { source: "初始化升降轴", mode: "初始化/置零" });
    });
  }
  $("#logFilters").addEventListener("click", (event) => {
    const button = event.target.closest("[data-log-filter]");
    if (!button) return;
    state.activeLogFilter = button.dataset.logFilter;
    renderLogFilters();
    renderLogs();
  });
}

function init() {
  const activePanel = $(".view.is-active");
  document.body.dataset.activeView = activePanel ? activePanel.dataset.viewPanel : "self-check";
  bindEvents();
  renderAuth();
  renderHealth();
  renderSelfCheck();
  renderAdvice();
  renderHomingSteps();
  renderCollectionMetrics();
  renderInferenceStatus();
  renderInferenceMask();
  refreshInferenceStatus();
  refreshAuthStatus({ silent: true });
  loadInferenceChassisLimits();
  renderPreflight();
  renderDeviceBaseMetrics();
  renderDeviceControls();
  renderPiperRuntime();
  renderLiftingRuntime();
  renderChassisRuntime();
  renderLocalizationRuntime();
  renderCameraRuntime();
  renderLidarRuntime();
  renderHistory();
  renderLogFilters();
  renderActionLocks();
  renderCameraFrames();
  renderLidarCloudStatus();
  renderPlayback();
  refreshPlaybackStatus({ silent: true });
  renderRobotViewStatus();
  renderMappingStatus();
  renderLocalizationStatus();
  fetchRobotModels({ silent: true });
  refreshMappingStatus({ silent: true });
  fetchLocalizationMaps({ silent: true });
  initializeRobotViewer();
  addLog("系统", "Robot Station 前端原型已加载");
  addLog("ROS", "等待接入真实 ROS 状态");
  addLog("相机", "相机压缩图预览等待图像帧");
  refreshCanInterfaceStatus({ silent: true });
  fetchPiperRuntimeStatus({ silent: true });
  fetchLiftingLimits();
  fetchLiftingRuntimeStatus({ silent: true });
  fetchChassisRuntimeStatus({ silent: true });
  fetchChassisState({ silent: true });
  fetchCameraRuntimeStatus({ silent: true });
  fetchLidarRuntimeStatus({ silent: true });
  fetchLiftingMotorState();
  fetchPiperJointStates();
  syncClock();
  window.setInterval(syncClock, 1000);
  window.setInterval(() => refreshAuthStatus({ silent: true }), 5000);
  window.setInterval(() => runBackgroundPoll(() => fetchPiperRuntimeStatus({ silent: true })), 3000);
  window.setInterval(() => runBackgroundPoll(() => fetchLiftingRuntimeStatus({ silent: true })), 3000);
  window.setInterval(() => runBackgroundPoll(() => fetchChassisRuntimeStatus({ silent: true })), 3000);
  window.setInterval(() => runBackgroundPoll(() => fetchCameraRuntimeStatus({ silent: true })), 3000);
  window.setInterval(() => {
    if (state.cameraFrames.previewEnabled) runBackgroundPoll(() => fetchCameraFrames({ silent: true }));
  }, 1000);
  window.setInterval(() => runBackgroundPoll(() => fetchLidarRuntimeStatus({ silent: true })), 3000);
  window.setInterval(() => {
    if (state.lidarCloud.previewEnabled) runBackgroundPoll(() => fetchLidarCloudStatus({ silent: true }));
  }, 1000);
  window.setInterval(() => runBackgroundPoll(fetchLiftingMotorState), 500);
  window.setInterval(() => runBackgroundPoll(() => fetchChassisState({ silent: true })), 500);
  window.setInterval(() => runBackgroundPoll(fetchPiperJointStates), piperJointPollIntervalMs);
}

init();
