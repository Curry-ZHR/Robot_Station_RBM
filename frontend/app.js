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
  collectionSeconds: 0,
  inferenceTicks: 0,
  activeLogFilter: "全部",
  selfCheckResults: [],
  canActivation: {
    busy: false,
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
  cameraRuntime: {
    status: "stopped",
  },
  cameraFrames: {
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
    controls: null,
    animationFrame: null,
    resizeObserver: null,
  },
  armControl: {
    active: false,
    busy: false,
    publishTimer: null,
    maxJointSpeedDegS: 10,
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
    activeDrive: null,
    busy: false,
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
      positions: [],
      ageMs: null,
      stale: true,
      receivedAt: null,
    },
    right: {
      ok: false,
      code: "ROS-R-WAITING",
      detail: "等待右臂关节反馈。",
      positions: [],
      ageMs: null,
      stale: true,
      receivedAt: null,
    },
  },
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
  { key: "linear", label: "前向速度", value: 0, min: 0, max: 1, step: 0.01, unit: "", commandMax: 0.2, commandUnit: "m/s" },
  { key: "lateral", label: "横向速度", value: 0, min: 0, max: 1, step: 0.01, unit: "", commandMax: 0.15, commandUnit: "m/s" },
  { key: "angular", label: "旋转速度", value: 0, min: 0, max: 1, step: 0.01, unit: "", commandMax: 0.5, commandUnit: "rad/s" },
];

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
const lidarCloudKey = "rslidar_points";
const lidarFrameIntervalMs = 120;
const lidarMaxPoints = 60000;
const threeModuleUrl = "./vendor/three.module.min.js";
let threeModulePromise = null;

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

const chassisMotionModeLabels = {
  0: "阿克曼",
  1: "蟹行",
  2: "旋转",
  3: "侧滑",
};

const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => Array.from(document.querySelectorAll(selector));

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
  $("#ownerLabel").textContent = owner;
  $("#taskStatus").textContent = `当前任务：${label}`;
  $("#drawerTask").textContent = label === "空闲" ? "当前空闲" : `当前任务：${label}`;
  renderActionLocks();
}

function setStateBadge(selector, text, level) {
  const node = $(selector);
  if (!node) return;
  node.textContent = text;
  node.className = `state-badge ${level}`;
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

function speedRiskColor(value) {
  const percent = clamp(Number(value), 0, 1) * 100;
  if (percent <= 50) {
    const mix = percent / 50;
    return `rgb(${Math.round(22 + 223 * mix)}, ${Math.round(163 - 5 * mix)}, ${Math.round(74 - 63 * mix)})`;
  }
  const mix = (percent - 50) / 50;
  return `rgb(${Math.round(245 - 25 * mix)}, ${Math.round(158 - 120 * mix)}, ${Math.round(11 + 27 * mix)})`;
}

function normalizeJointSpeedDegS(value) {
  const parsed = Number(value);
  if (!Number.isFinite(parsed)) return state.armControl.maxJointSpeedDegS;
  const stepped = Math.round(parsed / PIPER_JOINT_SPEED_STEP) * PIPER_JOINT_SPEED_STEP;
  return clamp(stepped, PIPER_JOINT_SPEED_MIN, PIPER_JOINT_SPEED_MAX);
}

function formatNumber(value, digits = 3) {
  return Number.isFinite(value) ? value.toFixed(digits) : "--";
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
  renderActionLocks();
}

function setLiftingRuntime(status) {
  state.liftingRuntime.status = liftingRuntimeLabels[status] ? status : "unknown";
  renderLiftingRuntime();
  renderLiftPreview();
}

function setChassisRuntime(status) {
  state.chassisRuntime.status = chassisRuntimeLabels[status] ? status : "unknown";
  renderChassisRuntime();
  renderDeviceBaseMetrics();
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
  document.body.dataset.activeView = view;
  $$(".nav-item").forEach((item) => item.classList.toggle("is-active", item.dataset.view === view));
  $$(".view").forEach((panel) => panel.classList.toggle("is-active", panel.dataset.viewPanel === view));
  if (view === "sensors") {
    window.setTimeout(resizeLidarViewer, 0);
  }
}

function renderHealth() {
  $("#healthGrid").innerHTML = healthItems
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
  $("#adviceList").innerHTML = html;
  $("#drawerAlerts").innerHTML = html;
  $("#alertStatus").textContent = `告警 ${state.alerts.length}`;
}

function renderHomingSteps(activeIndex = -1, failedIndex = -1) {
  $("#homingSteps").innerHTML = homingSteps
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
  $("#homeFlowSteps").innerHTML = steps
    .map((step, index) => {
      const cls = index < activeIndex ? "is-done" : index === activeIndex ? "is-current" : "";
      return `<li class="${cls}">${step}</li>`;
    })
    .join("");
  $("#taskProgressBar").style.width = `${progress}%`;
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

function renderInferenceMetrics() {
  const freq = state.task === "inference" ? (12 + (state.inferenceTicks % 4)).toFixed(1) : "--";
  const device = state.task === "inference" ? "GPU" : "--";
  const latency = state.task === "inference" ? `${(78 + state.inferenceTicks * 3) % 96} ms` : "--";
  $("#inferenceMetrics").innerHTML = [
    ["模型", state.task === "inference" ? "已加载" : "未加载"],
    ["设备", device],
    ["频率", `${freq} Hz`],
    ["延迟", latency],
    ["控制权", state.owner],
    ["安全接管", "可用"],
  ]
    .map(([label, value]) => `<div class="metric-card"><span>${label}</span><strong>${value}</strong></div>`)
    .join("");
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

function feedbackLevel(feedback) {
  if (feedback.ok && feedback.stale) return "warn";
  if (feedback.ok) return "ok";
  if (feedback.code === "ROS-R-WAITING") return "idle";
  if (feedback.code === "ROS-R-NODATA") return "warn";
  return "danger";
}

function armStatusText(side) {
  const feedback = state.piperJoints[side];
  if (!feedback) return { level: "idle", text: "等待反馈", detail: "无数据" };
  if (feedback.ok) {
    return {
      level: feedback.stale ? "warn" : "ok",
      text: feedback.stale ? "反馈延迟" : "在线",
      detail: feedback.ageMs === null ? "已接收" : `${feedback.ageMs} ms`,
    };
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
  if (onlineCount === sides.length) {
    setStateBadge("#armCompareBadge", "双臂在线", "ok");
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
    const response = await fetch("/api/control/piper/joint-targets", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
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
  fetch("/api/control/piper/joint-targets", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ hold: true }),
  })
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
  if (state.chassisState.ok && state.chassisState.stale) return "warn";
  if (state.chassisState.ok) return "ok";
  if (state.chassisState.code === "ROS-R-WAITING") return "idle";
  if (state.chassisState.code === "ROS-R-NODATA") return "warn";
  return chassisReady() ? "danger" : "idle";
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
  const feedbackText = state.chassisState.ok
    ? state.chassisState.stale
      ? "延迟"
      : "在线"
    : chassisReady()
      ? "等待"
      : "未启动";
  const feedbackLevel = chassisFeedbackLevel();
  const odomText = state.chassisState.odom
    ? state.chassisState.stale
      ? "延迟"
      : "在线"
    : "未接入";
  const serviceExternal = state.chassisRuntime.status === "external";
  const serviceText = serviceExternal ? "外部运行" : chassisReady() ? feedbackText : "未启动";
  const serviceLevel = serviceExternal ? "warn" : chassisReady() ? feedbackLevel : "idle";
  setStatusText("#baseControlText", serviceText, serviceLevel);
  setStatusText("#baseOdomText", odomText, state.chassisState.odom ? feedbackLevel : "idle");
  $$("[data-device-drive]").forEach((button) => {
    button.disabled = !chassisReady() && button.dataset.deviceDrive !== "stop";
  });
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
  if (state.liftingState.ok && state.liftingState.stale) return "warn";
  if (state.liftingState.ok) return "ok";
  if (state.liftingState.code === "ROS-R-WAITING") return "idle";
  if (state.liftingState.code === "ROS-R-NODATA") return "warn";
  return liftingReady() ? "danger" : "idle";
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
  const age = Number(state.liftingState.ageMs);
  const ageText = Number.isFinite(age) ? `${Math.round(age)} ms` : "--";
  const actualMetaText = state.liftingState.ok
    ? state.liftingState.stale
      ? `延迟 ${ageText}`
      : `反馈 ${ageText}`
    : "等待反馈";
  const reachText = state.liftingState.ok ? (state.liftingState.reachTarget ? "已到位" : "运动中") : "--";
  const serviceExternal = state.liftingRuntime.status === "external";
  const serviceText = serviceExternal ? "外部运行" : liftingReady() ? "运行中" : "未启动";
  const serviceLevel = serviceExternal ? "warn" : liftingReady() ? "ok" : "idle";
  const feedbackLevel = liftingFeedbackLevel();
  const feedbackText = state.liftingState.ok
    ? state.liftingState.stale
      ? "延迟"
      : "在线"
    : liftingReady()
      ? "等待"
      : "未启动";
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

  setStateBadge("#liftStateBadge", feedbackText, feedbackLevel);
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
}

function renderDeviceControls() {
  renderPiperJointFeedback();

  const baseNode = $("#deviceBaseControlPanel");
  if (baseNode) {
    baseNode.innerHTML = deviceBaseControlItems
      .map((item) => {
        const value = normalizedSpeedValue(item);
        const percent = clamp(value, 0, 1) * 100;
        const color = speedRiskColor(value);
        return `
          <label class="slider-row base-slider-row base-speed-row" style="--speed-risk: ${percent}%; --speed-color: ${color};">
            <span>${item.label}</span>
            <small>${item.min}</small>
            <input
              type="range"
              min="${item.min}"
              max="${item.max}"
              step="${item.step}"
              value="${value.toFixed(2)}"
              data-base-control="${item.key}"
              aria-label="${item.label}"
            />
            <small>${item.max}</small>
            <strong id="basePreview${item.key}">${value.toFixed(2)}</strong>
          </label>
        `;
      })
      .join("");
  }
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
  const runtimeReady = piperReady();
  $$("[data-action]").forEach((button) => {
    const action = button.dataset.action;
    const requiresPiper = action === "homing" || action === "collection" || action === "inference";
    button.disabled = busy || (requiresPiper && !runtimeReady);
  });
  $("#startHomingButton").disabled = busy || !runtimeReady;
  $("#startCollectionButton").disabled = busy || !runtimeReady;
  $("#startInferenceButton").disabled = busy || !runtimeReady;
  renderPreflight();
}

function syncClock() {
  $("#clockStatus").textContent = formatTime();
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
  $("#taskSubtitle").textContent = "正在执行归位准备";
  $("#homingSummary").textContent = "归位流程正在执行";
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
      $("#taskSubtitle").textContent = "最近任务：归位完成";
      $("#homingSummary").textContent = "归位完成，机器人处于准备状态";
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
  $("#taskSubtitle").textContent = "正在采集 episode_043";
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

async function startInference() {
  if (state.task !== "idle") return;
  if (!piperReady()) {
    addLog("推理", "推理未启动：Piper 控制节点未运行");
    showView("device-control");
    return;
  }
  const ok = await confirmAction("开始推理执行", "推理会加载模型并接管机器人动作输出，运行期间保留顶部停止和低速接管入口。");
  if (!ok) return;
  state.inferenceTicks = 0;
  setTask("inference", "推理任务", "推理中");
  setStateBadge("#inferenceBadge", "加载中", "warn");
  setStateBadge("#stateBadge", "运行中", "warn");
  $("#inferenceSummary").textContent = "模型加载中";
  $("#taskSubtitle").textContent = "正在运行推理任务";
  renderHomeFlow(["运行前检查", "加载模型", "输出动作", "人工监控"], 1, 45);
  renderInferenceMetrics();
  addLog("推理", `加载模型：${$("#modelSelect").value}`);
  window.clearInterval(state.inferenceTimer);
  state.inferenceTimer = window.setInterval(() => {
    state.inferenceTicks += 1;
    setStateBadge("#inferenceBadge", "已加载", "ok");
    $("#inferenceSummary").textContent = "模型已加载，推理运行中";
    $("#lastActionOutput").textContent = `最近动作：x=${(0.02 * state.inferenceTicks).toFixed(2)}, y=0.00, z=${(0.18 + 0.01 * (state.inferenceTicks % 3)).toFixed(2)}, gripper=${state.inferenceTicks % 2 ? "open" : "close"}`;
    renderHomeFlow(["运行前检查", "加载模型", "输出动作", "人工监控"], 2, 72);
    renderInferenceMetrics();
  }, 900);
}

function pauseInference() {
  if (state.task !== "inference") return;
  window.clearInterval(state.inferenceTimer);
  setTask("inference-paused", "推理任务暂停", "推理暂停");
  setStateBadge("#inferenceBadge", "暂停", "idle");
  $("#inferenceSummary").textContent = "推理已暂停";
  addLog("推理", "推理暂停");
}

function stopInference() {
  if (state.task !== "inference" && state.task !== "inference-paused") return;
  window.clearInterval(state.inferenceTimer);
  setTask("idle", "空闲", "空闲");
  setStateBadge("#inferenceBadge", "停止", "idle");
  $("#inferenceSummary").textContent = "推理已停止";
  renderHomeFlow(["运行前检查", "加载模型", "停止输出", "任务停止"], 3, 100);
  addLog("推理", "推理任务停止");
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
  setTask("idle", "空闲", "空闲");
  setStateBadge("#stateBadge", "停止", "idle");
  $("#taskSubtitle").textContent = "当前任务已停止";
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

function applyChassisStatePayloads(results) {
  const byKind = {};
  results.forEach((item) => {
    byKind[item.kind] = item.payload;
  });
  const okPayloads = Object.values(byKind).filter((payload) => payload && payload.ok);
  state.chassisState.system = byKind.system && byKind.system.ok ? byKind.system.data || null : null;
  state.chassisState.motion = byKind.motion && byKind.motion.ok ? byKind.motion.data || null : null;
  state.chassisState.battery = byKind.battery && byKind.battery.ok ? byKind.battery.data || null : null;
  state.chassisState.odom = byKind.odom && byKind.odom.ok ? byKind.odom.data || null : null;
  state.chassisState.ok = okPayloads.length > 0;
  state.chassisState.code = state.chassisState.ok
    ? okPayloads.some((payload) => payload.stale) ? "ROS-R-STALE" : "ROS-R-OK"
    : (byKind.system && byKind.system.code) || "ROS-R-NODATA";
  state.chassisState.detail = state.chassisState.ok
    ? "底盘反馈在线。"
    : (byKind.system && byKind.system.detail) || "等待底盘反馈。";
  state.chassisState.stale = !state.chassisState.ok || okPayloads.every((payload) => payload.stale);
  const ages = okPayloads.map((payload) => Number(payload.ageMs)).filter(Number.isFinite);
  state.chassisState.ageMs = ages.length ? Math.max(...ages) : null;
  state.chassisState.receivedAt = okPayloads.find((payload) => payload.receivedAt)?.receivedAt || null;
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
  const results = await Promise.all(
    Object.entries(chassisTopicKeys).map(([kind, key]) => fetchChassisTopic(kind, key)),
  );
  applyChassisStatePayloads(results);
  if (!options.silent && !state.chassisState.ok) {
    addLog("底盘", state.chassisState.detail);
  }
  return results;
}

function chassisBaseValue(key, fallback) {
  const item = deviceBaseControlItems.find((entry) => entry.key === key);
  if (!item) return fallback;
  const value = normalizedSpeedValue(item);
  const commandMax = Number(item.commandMax);
  return Number.isFinite(commandMax) ? value * commandMax : value;
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

async function requestChassisVelocity(command, options = {}) {
  if (!chassisReady()) {
    addLog("底盘", "Chassis 服务未启动，速度指令未发送");
    renderDeviceBaseMetrics();
    return null;
  }
  try {
    const response = await fetch("/api/control/chassis/cmd_vel", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(command),
    });
    const result = await response.json();
    if (!response.ok || !result.ok) {
      throw new Error(result.detail || `HTTP ${response.status}`);
    }
    state.chassisControl.command = {
      linearX: Number(command.linearX) || 0,
      linearY: Number(command.linearY) || 0,
      angularZ: Number(command.angularZ) || 0,
    };
    renderDeviceBaseMetrics();
    if (!options.quiet) addLog("底盘", `${options.source || "速度指令"}：${result.code}`);
    return result;
  } catch (error) {
    addLog("底盘", `${options.source || "速度指令"}失败：${error.message}`);
    return null;
  }
}

async function requestChassisStop(source = "底盘停止") {
  try {
    const response = await fetch("/api/control/chassis/stop", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const result = await response.json();
    if (!response.ok || !result.ok) {
      throw new Error(result.detail || `HTTP ${response.status}`);
    }
    state.chassisControl.command = { linearX: 0, linearY: 0, angularZ: 0 };
    renderDeviceBaseMetrics();
    addLog("底盘", `${source}：${result.code}`);
    return result;
  } catch (error) {
    addLog("底盘", `${source}失败：${error.message}`);
    return null;
  }
}

function startChassisDrive(action, label) {
  if (action === "stop") {
    stopChassisDrive("底盘停止");
    return;
  }
  if (!chassisReady()) {
    requestChassisVelocity(chassisCommandForDrive(action), { source: `点动${label}`, quiet: true });
    return;
  }
  if (state.chassisControl.driveTimer) {
    window.clearInterval(state.chassisControl.driveTimer);
  }
  const command = chassisCommandForDrive(action);
  state.chassisControl.activeDrive = action;
  addLog("底盘", `点动开始：${label}`);
  requestChassisVelocity(command, { source: `点动${label}`, quiet: true });
  state.chassisControl.driveTimer = window.setInterval(() => {
    requestChassisVelocity(command, { source: `点动${label}`, quiet: true });
  }, 100);
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
    const response = await fetch(`/api/control/lifting/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
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

function applyPiperJointPayload(side, payload) {
  const feedback = state.piperJoints[side];
  if (!feedback) return;

  if (!payload || !payload.ok) {
    feedback.ok = false;
    feedback.code = payload && payload.code ? payload.code : "ROS-R-ERROR";
    feedback.detail = payload && payload.detail ? payload.detail : `${piperArmLabels[side]}关节反馈读取失败。`;
    feedback.positions = [];
    feedback.ageMs = payload && payload.ageMs !== undefined ? payload.ageMs : null;
    feedback.stale = true;
    feedback.receivedAt = payload && payload.receivedAt ? payload.receivedAt : null;
    return;
  }

  const data = payload.data || {};
  const positions = Array.isArray(data.position) ? data.position : [];
  feedback.ok = positions.length > 0;
  feedback.code = feedback.ok ? payload.code || "ROS-R-OK" : "ROS-R-NODATA";
  feedback.detail = feedback.ok ? payload.detail || "" : `${piperArmLabels[side]} JointState 中没有 position 数据。`;
  feedback.positions = positions;
  feedback.velocity = Array.isArray(data.velocity) ? data.velocity : [];
  feedback.effort = Array.isArray(data.effort) ? data.effort : [];
  feedback.ageMs = Number.isFinite(Number(payload.ageMs)) ? Number(payload.ageMs) : null;
  feedback.stale = Boolean(payload.stale);
  feedback.receivedAt = payload.receivedAt || null;
  feedback.topic = payload.topic || "";
}

function renderPiperJointFeedback() {
  renderArmComparisons();
}

async function fetchPiperJointStates() {
  const entries = Object.entries(piperJointTopicKeys);
  const results = await Promise.all(
    entries.map(async ([side, key]) => {
      try {
        const response = await fetch(`/api/ros/topics/${key}?wait=0.1`, { cache: "no-store" });
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

function cameraFrameAgeText(feed) {
  const ageMs = Number(feed.ageMs);
  if (!Number.isFinite(ageMs)) return "无帧";
  if (ageMs < 1000) return `${Math.max(0, Math.round(ageMs))} ms`;
  return `${(ageMs / 1000).toFixed(1)} s`;
}

function cameraFrameStatus(feed) {
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
  const key = cameraFeedKey(feed);
  window.clearTimeout(state.cameraFrames.frameTimers[key]);
  state.cameraFrames.frameTimers[key] = window.setTimeout(() => {
    requestCameraFrame(feed);
  }, delayMs);
}

async function requestCameraFrame(feed) {
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
    if (card && card.isConnected) {
      const elapsed = performance.now() - startedAt;
      scheduleCameraFrame(feed, Math.max(40, cameraFrameIntervalMs - elapsed));
    }
  }
}

function ensureCameraFrameLoop(feed) {
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
          <span class="camera-frame-placeholder">等待画面</span>
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
    const text = feed.hasFrame ? `${cameraFrameAgeText(feed)} / ${format}` : feed.topic || "";
    detail.textContent = text;
    detail.title = feed.topic || "";
  }

  const image = card.querySelector("img[data-camera-frame]");
  if (image && image.alt !== feed.label) {
    image.alt = feed.label;
  }
}

function renderCameraFrames() {
  const feeds = state.cameraFrames.feeds.length ? state.cameraFrames.feeds : mergeCameraFeeds();
  const summary = $("#cameraFeedSummary");
  if (summary) {
    const liveCount = feeds.filter((feed) => feed.hasFrame && !feed.stale).length;
    const frameCount = feeds.filter((feed) => feed.hasFrame).length;
    summary.textContent = state.cameraFrames.error
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
    controls.dragging = true;
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
    controls.yaw -= dx * 0.006;
    controls.pitch = clamp(controls.pitch + dy * 0.006, -1.2, 1.35);
    updateLidarCamera();
  });

  const release = (event) => {
    controls.dragging = false;
    if (surface.hasPointerCapture(event.pointerId)) {
      surface.releasePointerCapture(event.pointerId);
    }
  };
  surface.addEventListener("pointerup", release);
  surface.addEventListener("pointercancel", release);
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
        size: 0.055,
        vertexColors: true,
        sizeAttenuation: true,
        transparent: true,
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

function lidarColor(value, colors, offset) {
  const t = clamp(value, 0, 1);
  colors[offset] = clamp(1.45 * t - 0.12, 0.05, 1);
  colors[offset + 1] = clamp(1.3 - Math.abs(t - 0.55) * 2.1, 0.16, 1);
  colors[offset + 2] = clamp(1.18 - 1.25 * t, 0.18, 1);
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

function updateLidarPointCloud(buffer) {
  const lidar = state.lidarCloud;
  const THREE = lidar.three;
  if (!THREE || !lidar.geometry) return;

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
  let minIntensity = Infinity;
  let maxIntensity = -Infinity;

  for (let index = 0; index < count; index += 1) {
    const source = index * 4;
    const target = index * 3;
    const x = values[source];
    const y = values[source + 1];
    const z = values[source + 2];
    const intensity = values[source + 3];
    positions[target] = x;
    positions[target + 1] = y;
    positions[target + 2] = z;
    minX = Math.min(minX, x);
    minY = Math.min(minY, y);
    minZ = Math.min(minZ, z);
    maxX = Math.max(maxX, x);
    maxY = Math.max(maxY, y);
    maxZ = Math.max(maxZ, z);
    minIntensity = Math.min(minIntensity, intensity);
    maxIntensity = Math.max(maxIntensity, intensity);
  }

  const useIntensity = maxIntensity > minIntensity;
  const zRange = maxZ > minZ ? maxZ - minZ : 1;
  const intensityRange = maxIntensity > minIntensity ? maxIntensity - minIntensity : 1;
  for (let index = 0; index < count; index += 1) {
    const source = index * 4;
    const target = index * 3;
    const value = useIntensity
      ? (values[source + 3] - minIntensity) / intensityRange
      : (values[source + 2] - minZ) / zRange;
    lidarColor(value, colors, target);
  }

  const firstFrame = !lidar.hasFrame && count > 0;
  lidar.geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
  lidar.geometry.setAttribute("color", new THREE.BufferAttribute(colors, 3));
  lidar.geometry.computeBoundingSphere();

  if (firstFrame && lidar.controls) {
    const centerX = (minX + maxX) / 2;
    const centerY = (minY + maxY) / 2;
    const centerZ = (minZ + maxZ) / 2;
    const dx = maxX - minX;
    const dy = maxY - minY;
    const dz = maxZ - minZ;
    const diagonal = Math.sqrt(dx * dx + dy * dy + dz * dz);
    lidar.controls.target.set(centerX, centerY, centerZ);
    lidar.controls.distance = clamp(diagonal * 1.4, 5, 120);
    updateLidarCamera();
  }

  lidar.hasFrame = count > 0;
  updateLidarFrameRate();
}

function applyLidarCloudPayload(payload) {
  const clouds = payload && Array.isArray(payload.clouds) ? payload.clouds : [];
  const cloud = clouds.find((entry) => entry.key === lidarCloudKey) || clouds[0];
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
  return true;
}

async function fetchLidarCloudStatus(options = {}) {
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

function lidarFrameUrl() {
  const params = new URLSearchParams({
    wait: "0.8",
    max_points: String(lidarMaxPoints),
    t: String(Date.now()),
  });
  const sequence = Number(state.lidarCloud.sequence);
  if (Number.isFinite(sequence)) {
    params.set("after", String(sequence));
  }
  return `/api/sensors/lidar/${encodeURIComponent(lidarCloudKey)}/frame?${params.toString()}`;
}

function scheduleLidarFrame(delayMs = lidarFrameIntervalMs) {
  window.clearTimeout(state.lidarCloud.frameTimer);
  state.lidarCloud.frameTimer = window.setTimeout(() => {
    requestLidarFrame();
  }, delayMs);
}

async function requestLidarFrame() {
  if (state.lidarCloud.activeRequest) return;
  const startedAt = performance.now();
  state.lidarCloud.activeRequest = true;
  try {
    await initializeLidarViewer();
    const response = await fetch(lidarFrameUrl(), { cache: "no-store" });
    const contentType = response.headers.get("Content-Type") || "";
    if (!response.ok || contentType.includes("application/json")) {
      const payload = contentType.includes("application/json") ? await response.json() : null;
      throw new Error((payload && payload.detail) || `HTTP ${response.status}`);
    }

    const buffer = await response.arrayBuffer();
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

function renderLidarCloudStatus() {
  const lidar = state.lidarCloud;
  const topic = (lidar.clouds[0] && lidar.clouds[0].topic) || "/rslidar_points";
  const topicNode = $("#lidarCloudTopic");
  if (topicNode) topicNode.textContent = topic;

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

  const overlay = $("#lidarOverlay");
  if (overlay) {
    overlay.textContent = lidar.error || (lidar.hasFrame ? "" : `等待 ${topic}`);
  }
}

function bindEvents() {
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
  $("#cameraRuntimeStatus").addEventListener("click", toggleCameraRuntime);
  $("#lidarRuntimeStatus").addEventListener("click", toggleLidarRuntime);
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
  $("#startHomingButton").addEventListener("click", startHoming);
  $("#startCollectionButton").addEventListener("click", startCollection);
  $("#pauseCollectionButton").addEventListener("click", pauseCollection);
  $("#finishCollectionButton").addEventListener("click", () => finishCollection("完成"));
  $("#discardEpisodeButton").addEventListener("click", () => finishCollection("废弃"));
  $("#markSuccessButton").addEventListener("click", () => finishCollection("成功"));
  $("#markFailButton").addEventListener("click", () => finishCollection("失败"));
  $("#startInferenceButton").addEventListener("click", startInference);
  $("#pauseInferenceButton").addEventListener("click", pauseInference);
  $("#stopInferenceButton").addEventListener("click", stopInference);
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
        startInference();
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

  $$("[data-device-drive]").forEach((button) => {
    const label = button.textContent.trim();
    button.addEventListener("pointerdown", (event) => {
      event.preventDefault();
      startChassisDrive(button.dataset.deviceDrive, label);
    });
    button.addEventListener("pointerup", () => stopChassisDrive("松开停止"));
    button.addEventListener("pointercancel", () => stopChassisDrive("取消点动"));
    button.addEventListener("pointerleave", () => stopChassisDrive("离开按钮区域，停止"));
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

  $("#deviceBaseControlPanel").addEventListener("input", (event) => {
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
    const preview = $(`#basePreview${item.key}`);
    if (preview) preview.textContent = item.value.toFixed(2);
    renderDeviceBaseMetrics();
  });

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
  renderHealth();
  renderSelfCheck();
  renderAdvice();
  renderHomingSteps();
  renderCollectionMetrics();
  renderInferenceMetrics();
  renderPreflight();
  renderDeviceBaseMetrics();
  renderDeviceControls();
  renderPiperRuntime();
  renderLiftingRuntime();
  renderChassisRuntime();
  renderCameraRuntime();
  renderLidarRuntime();
  renderHistory();
  renderLogFilters();
  renderActionLocks();
  renderCameraFrames();
  renderLidarCloudStatus();
  initializeLidarViewer();
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
  fetchCameraFrames({ silent: true });
  fetchLidarRuntimeStatus({ silent: true });
  fetchLidarCloudStatus({ silent: true });
  requestLidarFrame();
  fetchLiftingMotorState();
  fetchPiperJointStates();
  syncClock();
  window.setInterval(syncClock, 1000);
  window.setInterval(() => fetchPiperRuntimeStatus({ silent: true }), 3000);
  window.setInterval(() => fetchLiftingRuntimeStatus({ silent: true }), 3000);
  window.setInterval(() => fetchChassisRuntimeStatus({ silent: true }), 3000);
  window.setInterval(() => fetchCameraRuntimeStatus({ silent: true }), 3000);
  window.setInterval(() => fetchCameraFrames({ silent: true }), 1000);
  window.setInterval(() => fetchLidarRuntimeStatus({ silent: true }), 3000);
  window.setInterval(() => fetchLidarCloudStatus({ silent: true }), 1000);
  window.setInterval(fetchLiftingMotorState, 500);
  window.setInterval(() => fetchChassisState({ silent: true }), 500);
  window.setInterval(fetchPiperJointStates, 250);
}

init();
