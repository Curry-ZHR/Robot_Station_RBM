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
      detail: "开始归位或推理前建议先完成一次自检。",
    },
  ],
  logs: [],
  selfCheckRanAt: null,
  selfCheckSummary: null,
  inferenceTimer: null,
  homingTimer: null,
  playbackTimer: null,
  inferenceTicks: 0,
  selfCheckResults: [],
  runtimePrepBusy: {},
  canActivation: {
    busy: false,
  },
  piperRuntime: {
    status: "stopped",
  },
  piperRemoteRuntime: {
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
    activeKind: "color",
    previewEnabled: false,
    previewEnabledByKind: {
      color: false,
      depth: false,
      ir: false,
    },
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
  cameraCalibration: {
    projectionBusy: false,
    sampleBusyCamera: "",
    sampleClearBusyCamera: "",
    statusLoading: false,
    statusPayload: null,
    statusError: "",
    configDirty: false,
    configSaving: false,
    serviceBusy: false,
    solveBusy: false,
    solveResult: null,
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
    worldRoot: null,
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
  robotWork: {
    mode: "mapping",
    modal: null,
  },
  navigation: {
    status: "idle",
    phase: "idle",
    statusLoading: false,
    statusTimer: null,
    statusPayload: null,
    goalEditMode: false,
    goalDrag: {
      active: false,
      pointerId: null,
    },
    targetPose: {
      x: null,
      y: null,
      z: 0,
      yawDeg: null,
    },
    localTargetDirty: false,
    localParamsDirty: false,
    goalMarker: {
      group: null,
      arrow: null,
      ring: null,
    },
    pathLayer: {
      line: null,
      geometry: null,
      material: null,
    },
    plan: {
      status: "empty",
      points: [],
      distanceM: null,
      etaSec: null,
      plannedAt: null,
      startPose: null,
      targetSignature: "",
      stale: false,
      staleReason: "",
      planner: "straight-line-preview",
      cost: null,
    },
    running: false,
    paused: false,
    progress: 0,
    remainingDistanceM: null,
    currentSpeedMps: 0,
    command: { linearX: 0, linearY: 0, angularZ: 0 },
    errors: null,
    translationYawDeg: null,
    currentPose: null,
    params: {
      mode: "lateral",
      maxLinearMps: 0.2,
      maxLateralMps: 0.15,
      maxAngularRadS: 0.5,
      positionToleranceM: 0.05,
      yawToleranceDeg: 3,
      localizationStaleSec: 0.8,
      controlRateHz: 20,
    },
    runTimer: null,
    startedAt: null,
    completedAt: null,
    canceledAt: null,
    stoppedAt: null,
    failedAt: null,
    localizationWaitStartedAt: null,
    lastLocalizationError: "",
    lastError: "",
  },
  stateMachine: {
    mode: "graph",
    name: "未命名状态机",
    selectedId: "sm_start",
    connectingFromId: "",
    draggingNode: null,
    library: [],
    libraryLoaded: false,
    graphs: [],
    selectedGraphId: "",
    modal: null,
    draftSyncTimer: null,
    realRun: {
      active: false,
      status: "idle",
      pollTimer: null,
      taskStatus: null,
      taskStatusPanelOpen: false,
    },
    run: {
      active: false,
      status: "idle",
      currentId: null,
      completedIds: [],
      activeEdge: null,
      edgePath: [],
      path: [],
      loop: false,
      iteration: 0,
      completedIterations: 0,
      startedAt: null,
      completedAt: null,
    },
    nodes: [
      {
        id: "sm_start",
        type: "start",
        title: "Start",
        x: 70,
        y: 250,
        params: {},
        outgoingIds: [],
      },
      {
        id: "sm_end",
        type: "end",
        title: "End",
        x: 760,
        y: 250,
        params: {},
        outgoingIds: [],
      },
    ],
    eventSequence: {
      name: "完整任务序列",
      selectedId: "",
      sequences: [],
      selectedSequenceId: "",
      draggingId: "",
      run: {
        active: false,
        status: "idle",
        currentEventId: null,
        currentEventIndex: -1,
        completedEventIds: [],
        path: [],
        loop: false,
        iteration: 0,
        completedIterations: 0,
        eventStatus: null,
        childRun: null,
        error: "",
      },
      realRun: {
        active: false,
        status: "idle",
        pollTimer: null,
      },
      events: [],
    },
  },
  localization: {
    status: "idle",
    processStatus: "stopped",
    running: false,
    statusLoading: false,
    statusTimer: null,
    statusUpdatedAt: null,
    statusPayload: null,
    selectedMap: "",
    maps: [],
    mapsLoading: false,
    mapsLoadedAt: null,
    mapLoadBusy: false,
    loadedMap: "",
    backend: "cpu",
    activeBackend: "cpu",
    availableBackends: [],
    mapPointCount: 0,
    mapSizeBytes: 0,
    mapMtimeMs: null,
    pose: {
      x: null,
      y: null,
      z: 0,
      yawDeg: null,
    },
    fitness: null,
    ndtFitness: null,
    frequencyHz: null,
    converged: null,
    failedFrameCount: 0,
    lastError: "",
    initialPoseEditMode: false,
    initialPosePublishing: false,
    initialPoseLastPublishedAt: null,
    initialPoseDrag: {
      active: false,
      pointerId: null,
    },
    initialPoseMarker: {
      group: null,
      arrow: null,
      ring: null,
    },
    initialPose: {
      x: 0,
      y: 0,
      z: 0,
      yawDeg: 0,
    },
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
      source: "",
      mapName: "",
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
    isSuccess: false,
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
  ["机械臂", "ok", "反馈 100 Hz", 92, "状态待确认"],
  ["底盘", "ok", "里程计在线", 86, "速度 0.00 m/s"],
  ["相机", "idle", "服务状态", 0, "按需启动"],
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
    name: "CAN 接口",
    status: "未检测",
    source: "系统",
    code: "CAN-I-000",
    advice: "can_left/can_right/can_chassis 未就绪时先激活 CAN。",
    detail: "检查机械臂和底盘 CAN 接口是否存在、是否 UP、bitrate 是否正确。",
    metric: { label: "CAN", value: "--", percent: 0, level: "idle" },
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

const runtimePrepItems = [
  { key: "piper", name: "Piper", source: "机械臂", view: "device-control" },
  { key: "piper_remote", name: "主从直通", source: "机械臂", view: "device-control" },
  { key: "lifting", name: "升降轴", source: "升降轴", view: "platform-control" },
  { key: "chassis", name: "底盘", source: "底盘", view: "platform-control" },
  { key: "camera", name: "Camera", source: "相机", view: "sensors" },
  { key: "lidar", name: "LiDAR", source: "LiDAR", view: "sensors" },
];

const homingSteps = [
  "确认安全区域",
  "使能机械臂",
  "夹爪到默认状态",
  "机械臂回 home",
  "底盘停止",
  "传感器在线确认",
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

const piperJointTopicCandidates = {
  left: [
    { key: "piper_left_joint_state_double", topic: "/joint_states_single_l" },
    { key: "piper_left_joint_state", topic: "/puppet/joint_left" },
  ],
  right: [
    { key: "piper_right_joint_state_double", topic: "/joint_states_single_r" },
    { key: "piper_right_joint_state", topic: "/puppet/joint_right" },
  ],
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

const piperRemoteRuntimeLabels = {
  stopped: { title: "主从直通未启动，点击启动", level: "idle", pressed: false },
  starting: { title: "主从直通启动中", level: "warn", pressed: false, busy: true },
  running: { title: "主从直通运行中，点击清理关闭", level: "ok", pressed: true },
  stopping: { title: "主从直通清理关闭中", level: "warn", pressed: true, busy: true },
  external: { title: "检测到旧主从直通 ROS，点击清理", level: "warn", pressed: true },
  failed: { title: "主从直通启动失败，点击重试", level: "danger", pressed: false },
  error: { title: "主从直通异常，点击重试", level: "danger", pressed: false },
  unknown: { title: "主从直通状态未知，点击刷新", level: "idle", pressed: false },
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
const cameraKindOrder = ["color", "depth", "ir"];
const cameraKindMeta = {
  color: { label: "RGB", title: "RGB 相机", hint: "三路 RGB 压缩图" },
  depth: { label: "深度", title: "深度相机", hint: "三路深度压缩图" },
  ir: { label: "IR", title: "IR 相机", hint: "三路 IR 压缩图" },
};
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

const robotWorkModalMeta = {
  "mapping-config": { title: "采集参数", kicker: "建图作业", mode: "mapping" },
  "mapping-details": { title: "建图详情", kicker: "建图作业", mode: "mapping" },
  "model-load": { title: "模型加载详情", kicker: "3D 视口" },
  "localization-advanced": { title: "定位高级信息", kicker: "定位作业", mode: "localization" },
  "navigation-details": { title: "导航详情", kicker: "导航作业", mode: "navigation" },
};

const stateMachineDraftStorageKey = "robotStation.stateMachineDraft.v1";
const stateMachineEventDraftStorageKey = "robotStation.stateMachineEventDraft.v1";
const stateMachineDraftGraphId = "__draft__";
const stateMachineDraftSyncDelayMs = 800;
const stateMachineCanvasSize = {
  width: 980,
  height: 620,
};
const stateMachineCanvasNodeMargin = 180;
const stateMachineNodeSize = {
  width: 168,
  height: 94,
};
const stateMachineSystemTypes = {
  start: {
    label: "起始",
    summary: "固定起始状态，不执行任务",
  },
  end: {
    label: "终止",
    summary: "固定终止状态，不执行任务",
  },
};

function stateMachinePiperJointSideFields(side) {
  const sideLabel = piperArmLabels[side] || side;
  const showWhen = { key: "side", values: [side, "both"] };
  return [
    ...armJointLimitsFor(side).map((limit, index) => ({
      key: `${side}Joint${index + 1}Deg`,
      label: `${sideLabel} ${limit.name}`,
      type: "number",
      step: "0.1",
      min: String(limit.min),
      max: String(limit.max),
      unit: "deg",
      showWhen,
    })),
    {
      key: `${side}GripperM`,
      label: `${sideLabel} 夹爪`,
      type: "number",
      step: "0.001",
      min: "0",
      max: "0.1",
      unit: "m",
      showWhen,
    },
  ];
}

function stateMachinePiperJointFields() {
  return [
    {
      key: "side",
      label: "控制臂",
      type: "select",
      refresh: true,
      options: [
        { value: "both", label: "双臂" },
        { value: "left", label: "左臂" },
        { value: "right", label: "右臂" },
      ],
    },
    ...stateMachinePiperJointSideFields("left"),
    ...stateMachinePiperJointSideFields("right"),
    { key: "maxJointSpeedDegS", label: "最大关节速度", type: "number", step: "0.5", min: "0.5", max: "30", unit: "deg/s", advanced: true },
    { key: "gripperEffort", label: "夹爪 effort", type: "number", step: "0.1", min: "0.5", max: "3", advanced: true },
    { key: "toleranceDeg", label: "关节到位容差", type: "number", step: "0.1", min: "0.01", max: "30", unit: "deg", advanced: true },
    { key: "stableSec", label: "到位保持时间", type: "number", step: "0.1", min: "0", max: "10", unit: "s", advanced: true },
    { key: "timeoutSec", label: "到位超时", type: "number", step: "1", min: "0.1", max: "600", unit: "s", advanced: true },
  ];
}

function stateMachinePiperJointDefaults() {
  const defaults = {
    side: "both",
    maxJointSpeedDegS: 5,
    gripperEffort: PIPER_GRIPPER_EFFORT,
    toleranceDeg: 2,
    stableSec: 2,
    timeoutSec: 20,
  };
  ["left", "right"].forEach((side) => {
    for (let index = 1; index <= 6; index += 1) {
      defaults[`${side}Joint${index}Deg`] = 0;
    }
    defaults[`${side}GripperM`] = 0;
  });
  return defaults;
}

const stateMachineTaskTypes = {
  navigation: {
    label: "导航",
    summary: "移动到底盘目标点",
    fields: [
      { key: "targetName", label: "目标名称", type: "text", placeholder: "工作台 / 货架 A" },
      { key: "x", label: "x", type: "number", step: "0.01", unit: "m" },
      { key: "y", label: "y", type: "number", step: "0.01", unit: "m" },
      { key: "yawDeg", label: "yaw", type: "number", step: "1", unit: "deg" },
      {
        key: "mode",
        label: "导航模式",
        type: "select",
        options: [
          { value: "lateral", label: "横向优先" },
          { value: "omni", label: "全向" },
        ],
      },
      { key: "maxLinearMps", label: "最大前进速度", type: "number", step: "0.01", min: "0.01", unit: "m/s", advanced: true },
      { key: "maxLateralMps", label: "最大横移速度", type: "number", step: "0.01", min: "0.01", unit: "m/s", advanced: true },
      { key: "maxAngularRadS", label: "最大角速度", type: "number", step: "0.01", min: "0.02", unit: "rad/s", advanced: true },
      { key: "positionToleranceM", label: "位置容差", type: "number", step: "0.01", min: "0.02", unit: "m", advanced: true },
      { key: "yawToleranceDeg", label: "yaw 容差", type: "number", step: "0.5", min: "1", unit: "deg", advanced: true },
      { key: "localizationStaleSec", label: "定位超时", type: "number", step: "0.1", min: "0.1", unit: "s", advanced: true },
      { key: "controlRateHz", label: "控制频率", type: "number", step: "1", min: "5", unit: "Hz", advanced: true },
    ],
  },
  reset_odom: {
    label: "/odom 归零",
    summary: "将底盘里程计重置为 0",
    fields: [],
    allowCreate: false,
  },
  inference: {
    label: "推理",
    summary: "远程推理闭环直到完成",
    fields: [
      { key: "remoteUrl", label: "远端地址", type: "text", placeholder: "ws://192.168.1.154:8888/infer" },
      { key: "prompt", label: "任务指令 prompt", type: "text", placeholder: "Target: item. Pick it and place it into the cart." },
      { key: "steps", label: "执行步数 N", type: "number", step: "1", min: "1", unit: "steps" },
      { key: "frequencyHz", label: "发送频率", type: "number", step: "1", min: "1", unit: "Hz" },
      { key: "maxJointSpeedDegS", label: "关节速度", type: "number", step: "0.5", min: "0.5", unit: "deg/s" },
      {
        key: "autoEnablePiper",
        label: "自动使能 Piper",
        type: "select",
        options: [
          { value: "true", label: "自动使能" },
          { value: "false", label: "不自动使能" },
        ],
      },
      { key: "maxLinearMps", label: "底盘 vx 上限", type: "number", step: "0.01", min: "0", unit: "m/s", advanced: true },
      { key: "maxLateralMps", label: "底盘 vy 上限", type: "number", step: "0.01", min: "0", unit: "m/s", advanced: true },
      { key: "maxAngularRadS", label: "底盘 wz 上限", type: "number", step: "0.01", min: "0", unit: "rad/s", advanced: true },
    ],
  },
  piper_joint: {
    label: "机械臂控制",
    summary: "发布关节目标并等待到位",
    fields: stateMachinePiperJointFields(),
  },
  grasp: {
    label: "抓取",
    summary: "推理抓取或末端位姿抓取",
    fields: [
      {
        key: "graspMethod",
        label: "抓取方式",
        type: "select",
        refresh: true,
        options: [
          { value: "inference", label: "推理抓取" },
          { value: "auto", label: "自动抓取（末端位姿）" },
        ],
      },
      { key: "leftTarget", label: "左臂目标", type: "text", placeholder: "留空表示左臂不参与" },
      { key: "rightTarget", label: "右臂目标", type: "text", placeholder: "留空表示右臂不参与" },
      {
        key: "prompt",
        label: "抓取提示",
        type: "text",
        placeholder: "grasp the item",
        showWhen: { key: "graspMethod", value: "inference" },
      },
      {
        key: "leftPose",
        label: "左臂末端位姿",
        type: "text",
        placeholder: "x, y, z, roll, pitch, yaw",
        showWhen: { key: "graspMethod", value: "auto" },
      },
      {
        key: "rightPose",
        label: "右臂末端位姿",
        type: "text",
        placeholder: "x, y, z, roll, pitch, yaw",
        showWhen: { key: "graspMethod", value: "auto" },
      },
    ],
  },
  wait: {
    label: "等待静止",
    summary: "运动后等待关节静止",
    fields: [
      { key: "stableSec", label: "静止等待时间", type: "number", step: "0.1", min: "0.1", unit: "s" },
    ],
  },
  topic_publish: {
    label: "发布消息",
    summary: "发布一次 true 信号",
    fields: [
      { key: "topicName", label: "发布话题名", type: "text", placeholder: "/state_machine/start" },
    ],
  },
  topic_wait: {
    label: "监听消息",
    summary: "收到 true 信号后继续",
    fields: [
      { key: "topicName", label: "监听话题名", type: "text", placeholder: "/data_collection/start" },
    ],
  },
};
const stateMachineTaskTypeDefaults = {
  navigation: {
    targetName: "",
    x: 0,
    y: 0,
    yawDeg: 0,
    mode: "lateral",
    maxLinearMps: 0.2,
    maxLateralMps: 0.15,
    maxAngularRadS: 0.5,
    positionToleranceM: 0.05,
    yawToleranceDeg: 3,
    localizationStaleSec: 0.8,
    controlRateHz: 20,
  },
  grasp: { graspMethod: "inference", leftTarget: "", rightTarget: "", prompt: "", leftPose: "", rightPose: "" },
  inference: {
    remoteUrl: "ws://192.168.1.154:8888/infer",
    prompt: "",
    steps: 20,
    frequencyHz: 10,
    maxJointSpeedDegS: 20,
    autoEnablePiper: true,
    maxLinearMps: 0.2,
    maxLateralMps: 0.15,
    maxAngularRadS: 0.5,
  },
  piper_joint: stateMachinePiperJointDefaults(),
  reset_odom: {},
  wait: { stableSec: 2 },
  topic_publish: { topicName: "" },
  topic_wait: { topicName: "", timeoutSec: 0 },
};
const stateMachineBuiltInLibraryEntries = [
  {
    id: "sm_builtin_reset_odom",
    title: "/odom 归零",
    taskType: "reset_odom",
    params: {},
    builtIn: true,
  },
];

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
  setText("#ownerLabel", owner);
  setText("#taskStatus", `当前任务：${label}`);
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

function setStatusPill(selector, text, level) {
  const node = $(selector);
  if (!node) return;
  node.textContent = text;
  node.className = `status-pill ${level}`;
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

function piperRemoteReady() {
  return state.piperRemoteRuntime.status === "running" || state.piperRemoteRuntime.status === "external";
}

function piperRemoteBlocksControl() {
  return ["starting", "running", "stopping", "external"].includes(state.piperRemoteRuntime.status);
}

function piperFeedbackReady() {
  return piperReady() || piperRemoteReady();
}

function piperControlAvailable() {
  return piperReady() && !piperRemoteBlocksControl();
}

function piperControlUnavailableDetail() {
  if (piperRemoteReady()) return "主从直通正在运行";
  if (state.piperRemoteRuntime.status === "starting") return "主从直通正在启动";
  if (state.piperRemoteRuntime.status === "stopping") return "主从直通正在清理";
  if (!piperReady()) return "Piper 控制节点未运行";
  return "";
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

function getPiperRemoteRuntimeLabel() {
  return piperRemoteRuntimeLabels[state.piperRemoteRuntime.status] || piperRemoteRuntimeLabels.error;
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
  if (!piperControlAvailable() && state.armControl.active) {
    window.clearTimeout(state.armControl.publishTimer);
    state.armControl.active = false;
    state.armControl.busy = false;
  }
  renderPiperRuntime();
  renderPiperJointFeedback();
  renderInferenceStatus();
  renderActionLocks();
  renderRuntimePrep();
}

function setPiperRemoteRuntime(status) {
  state.piperRemoteRuntime.status = piperRemoteRuntimeLabels[status] ? status : "unknown";
  if (!piperControlAvailable() && state.armControl.active) {
    window.clearTimeout(state.armControl.publishTimer);
    state.armControl.active = false;
    state.armControl.busy = false;
  }
  renderPiperRemoteRuntime();
  renderPiperJointFeedback();
  renderInferenceStatus();
  renderActionLocks();
  renderRuntimePrep();
}

function setLiftingRuntime(status) {
  state.liftingRuntime.status = liftingRuntimeLabels[status] ? status : "unknown";
  renderLiftingRuntime();
  renderLiftPreview();
  renderRuntimePrep();
}

function setChassisRuntime(status) {
  state.chassisRuntime.status = chassisRuntimeLabels[status] ? status : "unknown";
  if (!chassisReady() && state.chassisControl.keyboardListening) {
    stopChassisKeyboardControl("Chassis 服务未运行，键盘监听停止", { deactivate: true });
  }
  renderChassisRuntime();
  renderDeviceBaseMetrics();
  renderRuntimePrep();
}

function setCameraRuntime(status) {
  state.cameraRuntime.status = cameraRuntimeLabels[status] ? status : "unknown";
  renderCameraRuntime();
  renderRuntimePrep();
}

function setLidarRuntime(status) {
  state.lidarRuntime.status = lidarRuntimeLabels[status] ? status : "unknown";
  renderLidarRuntime();
  renderRuntimePrep();
}

function showView(view) {
  if (!["platform-control", "robot-view"].includes(view) && state.chassisControl.keyboardListening) {
    stopChassisKeyboardControl("离开底盘控制视图，键盘监听停止", { deactivate: true });
  }
  if (view !== "robot-view") closeRobotModal();
  document.body.dataset.activeView = view;
  $$(".nav-item").forEach((item) => item.classList.toggle("is-active", item.dataset.view === view));
  $$(".view").forEach((panel) => panel.classList.toggle("is-active", panel.dataset.viewPanel === view));
  if (view === "sensors") {
    window.setTimeout(resizeLidarViewer, 0);
  }
  if (view === "data-playback") {
    renderPlayback();
  }
  if (view === "state-machine") {
    renderStateMachine();
    refreshStateMachineLibrary({ silent: true });
    refreshStateMachineGraphs({ silent: true });
    refreshStateMachineEventSequences({ silent: true });
  }
  if (view === "camera-calibration") {
    refreshCameraCalibrationStatus({ silent: true });
  }
  if (view === "robot-view") {
    fetchRobotModels({ silent: true });
    refreshMappingStatus({ silent: true });
    initializeRobotViewer();
    window.setTimeout(resizeRobotViewer, 0);
  }
  window.setTimeout(() => {
    syncRobotViewerMount();
    syncRobotViewerLayersForView();
    resizeRobotViewer();
    updateRobotModelTransforms();
  }, 0);
}

function cloneStateMachineValue(value) {
  return JSON.parse(JSON.stringify(value));
}

function stateMachineNodeById(id) {
  return state.stateMachine.nodes.find((node) => node.id === id) || null;
}

function stateMachineSelectedNode() {
  return stateMachineNodeById(state.stateMachine.selectedId);
}

function stateMachineTaskMeta(taskType) {
  return stateMachineTaskTypes[taskType] || stateMachineTaskTypes.navigation;
}

function stateMachineTaskEditable(taskType) {
  return Boolean((stateMachineTaskMeta(taskType).fields || []).length);
}

function stateMachineBuiltInLibraryById(libraryId) {
  return stateMachineBuiltInLibraryEntries.find((entry) => entry.id === libraryId) || null;
}

function stateMachineLibraryById(libraryId) {
  return stateMachineBuiltInLibraryById(libraryId) || state.stateMachine.library.find((entry) => entry.id === libraryId) || null;
}

function stateMachineLibraryForTask(taskType) {
  return [
    ...stateMachineBuiltInLibraryEntries.filter((entry) => entry.taskType === taskType),
    ...state.stateMachine.library.filter((entry) => entry.taskType === taskType),
  ];
}

async function stateMachineApiGet(path) {
  const response = await fetch(`/api/state-machine/${path}`, { cache: "no-store" });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  return payload;
}

async function stateMachineApiPost(path, body = {}) {
  const response = await fetch(`/api/state-machine/${path}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json().catch(() => ({}));
  if (!response.ok || payload.ok === false) {
    throw new Error(payload.detail || `HTTP ${response.status}`);
  }
  return payload;
}

async function refreshStateMachineLibrary(options = {}) {
  try {
    const payload = await stateMachineApiGet("states");
    state.stateMachine.library = Array.isArray(payload.states) ? payload.states : [];
    state.stateMachine.libraryLoaded = true;
    renderStateMachine();
  } catch (error) {
    if (!options.silent) addLog("状态机", `状态库加载失败：${error.message}`);
  }
}

async function refreshStateMachineGraphs(options = {}) {
  try {
    const payload = await stateMachineApiGet("graphs");
    state.stateMachine.graphs = Array.isArray(payload.graphs) ? payload.graphs : [];
    if (!state.stateMachine.graphs.some((graph) => graph.id === state.stateMachine.selectedGraphId)) {
      state.stateMachine.selectedGraphId =
        state.stateMachine.graphs.find((graph) => graph.id !== stateMachineDraftGraphId)?.id || "";
    }
    renderStateMachine();
  } catch (error) {
    if (!options.silent) addLog("状态机", `流程列表加载失败：${error.message}`);
  }
}

async function refreshStateMachineEventSequences(options = {}) {
  try {
    const payload = await stateMachineApiGet("event-sequences");
    const sequenceState = state.stateMachine.eventSequence;
    sequenceState.sequences = Array.isArray(payload.eventSequences) ? payload.eventSequences : [];
    if (!sequenceState.sequences.some((sequence) => sequence.id === sequenceState.selectedSequenceId)) {
      sequenceState.selectedSequenceId = sequenceState.sequences[0]?.id || "";
    }
    renderStateMachine();
  } catch (error) {
    if (!options.silent) addLog("状态机", `事件序列加载失败：${error.message}`);
  }
}

function setStateMachineMode(mode) {
  state.stateMachine.mode = mode === "events" ? "events" : "graph";
  renderStateMachine();
}

function stateMachineGraphById(graphId) {
  return state.stateMachine.graphs.find((graph) => graph.id === graphId) || null;
}

function stateMachineGraphTaskCount(graph) {
  return Array.isArray(graph?.nodes) ? graph.nodes.filter((node) => node?.type === "task").length : 0;
}

function stateMachineGraphTaskTypes(graph) {
  const labels = [];
  (Array.isArray(graph?.nodes) ? graph.nodes : []).forEach((node) => {
    if (node?.type !== "task") return;
    const label = stateMachineTaskMeta(node.taskType).label;
    if (!labels.includes(label)) labels.push(label);
  });
  return labels;
}

function stateMachineGraphSummary(graph) {
  if (!graph) return "流程已丢失";
  const taskCount = stateMachineGraphTaskCount(graph);
  const labels = stateMachineGraphTaskTypes(graph).slice(0, 3).join(" / ");
  return `${taskCount} 个任务${labels ? ` / ${labels}` : ""}`;
}

function normalizeEventSequenceEvent(event, index) {
  const graphId = String(event?.graphId || "").trim();
  const graph = stateMachineGraphById(graphId);
  return {
    id: String(event?.id || `sm_event_${Date.now()}_${index}_${Math.random().toString(36).slice(2, 6)}`),
    title: String(event?.title || graph?.name || graphId || `事件 ${index + 1}`).trim(),
    graphId,
    enabled: event?.enabled !== false,
  };
}

function normalizeEventSequenceEvents(events) {
  return (Array.isArray(events) ? events : [])
    .map((event, index) => normalizeEventSequenceEvent(event, index))
    .filter((event) => event.graphId);
}

function eventSequenceSnapshot() {
  const sequenceState = state.stateMachine.eventSequence;
  return {
    version: 1,
    name: sequenceState.name || "未命名事件序列",
    events: sequenceState.events.map((event) => ({
      id: event.id,
      title: event.title,
      graphId: event.graphId,
      enabled: event.enabled !== false,
    })),
  };
}

function saveEventSequenceDraft() {
  try {
    localStorage.setItem(stateMachineEventDraftStorageKey, JSON.stringify(eventSequenceSnapshot()));
  } catch (error) {
    console.warn("Failed to save event sequence draft", error);
  }
}

function applyEventSequenceSnapshot(snapshot) {
  if (!snapshot || typeof snapshot !== "object" || !Array.isArray(snapshot.events)) return false;
  const sequenceState = state.stateMachine.eventSequence;
  sequenceState.name = String(snapshot.name || "未命名事件序列");
  sequenceState.events = normalizeEventSequenceEvents(snapshot.events);
  sequenceState.selectedId = sequenceState.events[0]?.id || "";
  resetEventSequenceRun();
  return true;
}

function loadEventSequenceState() {
  try {
    const draft = JSON.parse(localStorage.getItem(stateMachineEventDraftStorageKey) || "null");
    return applyEventSequenceSnapshot(draft);
  } catch (error) {
    console.warn("Failed to load event sequence draft", error);
  }
  return false;
}

function resetEventSequenceRun() {
  const sequenceState = state.stateMachine.eventSequence;
  sequenceState.run = {
    active: false,
    status: "idle",
    currentEventId: null,
    currentEventIndex: -1,
    completedEventIds: [],
    path: [],
    loop: false,
    iteration: 0,
    completedIterations: 0,
    eventStatus: null,
    childRun: null,
    error: "",
  };
  sequenceState.realRun.active = false;
  sequenceState.realRun.status = "idle";
}

function mutateEventSequence() {
  if (!state.stateMachine.eventSequence.realRun.active) resetEventSequenceRun();
  saveEventSequenceDraft();
  renderStateMachine();
}

function createEventSequenceEventFromGraph(graphId) {
  const graph = stateMachineGraphById(graphId);
  if (!graph) return null;
  return {
    id: `sm_event_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    title: graph.name || graph.id,
    graphId: graph.id,
    enabled: true,
  };
}

function addGraphToEventSequence(graphId, insertIndex = null) {
  const event = createEventSequenceEventFromGraph(graphId);
  if (!event) return;
  const sequenceState = state.stateMachine.eventSequence;
  const index = Number.isInteger(insertIndex) ? clamp(insertIndex, 0, sequenceState.events.length) : sequenceState.events.length;
  sequenceState.events.splice(index, 0, event);
  sequenceState.selectedId = event.id;
  addLog("状态机", `事件已加入序列：${event.title}`);
  mutateEventSequence();
}

function selectedEventSequenceEvent() {
  const sequenceState = state.stateMachine.eventSequence;
  return sequenceState.events.find((event) => event.id === sequenceState.selectedId) || sequenceState.events[0] || null;
}

function selectEventSequenceEvent(eventId) {
  const sequenceState = state.stateMachine.eventSequence;
  if (sequenceState.events.some((event) => event.id === eventId)) {
    sequenceState.selectedId = eventId;
    renderStateMachine();
  }
}

function removeEventSequenceEvent(eventId) {
  const sequenceState = state.stateMachine.eventSequence;
  const event = sequenceState.events.find((item) => item.id === eventId);
  if (!event) return;
  sequenceState.events = sequenceState.events.filter((item) => item.id !== eventId);
  sequenceState.selectedId = sequenceState.events[0]?.id || "";
  addLog("状态机", `已移除事件：${event.title}`);
  mutateEventSequence();
}

function moveEventSequenceEvent(eventId, direction) {
  const sequenceState = state.stateMachine.eventSequence;
  const from = sequenceState.events.findIndex((event) => event.id === eventId);
  if (from < 0) return;
  const to = clamp(from + direction, 0, sequenceState.events.length - 1);
  if (from === to) return;
  const [event] = sequenceState.events.splice(from, 1);
  sequenceState.events.splice(to, 0, event);
  sequenceState.selectedId = event.id;
  mutateEventSequence();
}

function toggleEventSequenceEvent(eventId) {
  const event = state.stateMachine.eventSequence.events.find((item) => item.id === eventId);
  if (!event) return;
  event.enabled = event.enabled === false;
  mutateEventSequence();
}

function duplicateEventSequenceEvent(eventId) {
  const sequenceState = state.stateMachine.eventSequence;
  const index = sequenceState.events.findIndex((event) => event.id === eventId);
  if (index < 0) return;
  const copy = {
    ...cloneStateMachineValue(sequenceState.events[index]),
    id: `sm_event_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    title: `${sequenceState.events[index].title} 副本`,
  };
  sequenceState.events.splice(index + 1, 0, copy);
  sequenceState.selectedId = copy.id;
  mutateEventSequence();
}

function stateMachineNodeMeta(node) {
  if (!node) return { label: "--", summary: "" };
  if (node.type === "start" || node.type === "end") return stateMachineSystemTypes[node.type];
  return stateMachineTaskMeta(node.taskType);
}

function createStateMachineSystemNode(type) {
  return {
    id: type === "end" ? "sm_end" : "sm_start",
    type,
    title: type === "end" ? "End" : "Start",
    x: type === "end" ? 760 : 70,
    y: 250,
    params: {},
    outgoingIds: [],
  };
}

function stateMachineDefaultTaskPosition() {
  const count = state.stateMachine.nodes.filter((node) => node.type === "task").length;
  return {
    x: 260 + (count % 3) * 210,
    y: 110 + (Math.floor(count / 3) % 3) * 150,
  };
}

function clampStateMachineNodePosition(position) {
  const x = Number(position?.x);
  const y = Number(position?.y);
  return {
    x: Math.max(20, Number.isFinite(x) ? x : 0),
    y: Math.max(20, Number.isFinite(y) ? y : 0),
  };
}

function stateMachineWorkspaceSize() {
  const canvas = $("#stateMachineCanvas");
  const visibleWidth = canvas ? Math.max(0, canvas.clientWidth - 24) : 0;
  const visibleHeight = canvas ? Math.max(0, canvas.clientHeight - 24) : 0;
  const size = {
    width: Math.max(stateMachineCanvasSize.width, visibleWidth),
    height: Math.max(stateMachineCanvasSize.height, visibleHeight),
  };
  state.stateMachine.nodes.forEach((node) => {
    const x = Number(node?.x);
    const y = Number(node?.y);
    if (Number.isFinite(x)) size.width = Math.max(size.width, x + stateMachineNodeSize.width + stateMachineCanvasNodeMargin);
    if (Number.isFinite(y)) size.height = Math.max(size.height, y + stateMachineNodeSize.height + stateMachineCanvasNodeMargin);
  });
  return {
    width: Math.ceil(size.width),
    height: Math.ceil(size.height),
  };
}

function createStateMachineNodeFromLibrary(entry, position = null) {
  const point = clampStateMachineNodePosition(position || stateMachineDefaultTaskPosition());
  return {
    id: `sm_node_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    type: "task",
    taskType: entry.taskType,
    libraryId: entry.id,
    title: entry.title,
    x: point.x,
    y: point.y,
    params: cloneStateMachineValue(entry.params || {}),
    outgoingIds: [],
  };
}

function legacyStateMachineTaskType(type) {
  if (stateMachineTaskTypes[type]) return type;
  if (type === "arm_control" || type === "piper") return "piper_joint";
  if (type === "inference" || type === "arm") return "grasp";
  if (type === "check") return "wait";
  return "navigation";
}

function normalizeStateMachineNode(node, index) {
  const id = String(node?.id || `sm_node_${index}_${Date.now()}`);
  const position = clampStateMachineNodePosition({
    x: Number.isFinite(Number(node?.x)) ? Number(node.x) : 240 + (index % 4) * 190,
    y: Number.isFinite(Number(node?.y)) ? Number(node.y) : 100 + Math.floor(index / 4) * 140,
  });
  const outgoingIds = Array.isArray(node?.outgoingIds)
    ? node.outgoingIds.map(String)
    : node?.nextId
      ? [String(node.nextId)]
      : [];

  if (node?.type === "start" || id === "sm_start") {
    return {
      id: "sm_start",
      type: "start",
      title: "Start",
      x: position.x,
      y: position.y,
      params: {},
      outgoingIds,
    };
  }
  if (node?.type === "end" || id === "sm_end") {
    return {
      id: "sm_end",
      type: "end",
      title: "End",
      x: position.x,
      y: position.y,
      params: {},
      outgoingIds: [],
    };
  }

  const taskType = legacyStateMachineTaskType(node?.taskType || node?.type);
  const params = {
    ...cloneStateMachineValue(stateMachineTaskTypeDefaults[taskType] || {}),
    ...(node && typeof node.params === "object" && node.params ? node.params : {}),
  };
  return {
    id,
    type: "task",
    taskType,
    libraryId: String(node?.libraryId || ""),
    title: String(node?.title || stateMachineTaskMeta(taskType).label),
    x: position.x,
    y: position.y,
    params,
    outgoingIds,
  };
}

function normalizeStateMachineNodes(nodes) {
  const rawNodes = Array.isArray(nodes) ? nodes : [];
  const normalized = rawNodes.map((node, index) => normalizeStateMachineNode(node, index));
  const byId = new Map();
  normalized.forEach((node) => {
    if (!byId.has(node.id)) byId.set(node.id, node);
  });
  if (!byId.has("sm_start")) byId.set("sm_start", createStateMachineSystemNode("start"));
  if (!byId.has("sm_end")) byId.set("sm_end", createStateMachineSystemNode("end"));

  const result = Array.from(byId.values());
  const ids = new Set(result.map((node) => node.id));
  result.forEach((node) => {
    node.outgoingIds = node.type === "end"
      ? []
      : Array.from(new Set((node.outgoingIds || []).filter((id) => ids.has(id) && id !== node.id && id !== "sm_start")));
  });
  return result;
}

function ensureStateMachineGraph() {
  state.stateMachine.nodes = normalizeStateMachineNodes(state.stateMachine.nodes);
  if (!stateMachineNodeById(state.stateMachine.selectedId)) state.stateMachine.selectedId = "sm_start";
  if (!stateMachineNodeById(state.stateMachine.connectingFromId)) state.stateMachine.connectingFromId = "";
}

function stateMachineSnapshot() {
  ensureStateMachineGraph();
  return {
    version: 2,
    name: state.stateMachine.name || "未命名状态机",
    semantics: {
      multipleOutgoing: "random",
      fixedStates: ["sm_start", "sm_end"],
    },
    canvas: stateMachineWorkspaceSize(),
    nodes: state.stateMachine.nodes.map((node) => ({
      id: node.id,
      type: node.type,
      taskType: node.taskType || null,
      libraryId: node.libraryId || null,
      title: node.title,
      x: node.x,
      y: node.y,
      params: cloneStateMachineValue(node.params || {}),
      outgoingIds: [...(node.outgoingIds || [])],
    })),
  };
}

function saveStateMachineDraft() {
  try {
    localStorage.setItem(stateMachineDraftStorageKey, JSON.stringify(stateMachineSnapshot()));
  } catch (error) {
    console.warn("Failed to save state machine draft", error);
  }
  scheduleStateMachineDraftSync();
}

function scheduleStateMachineDraftSync() {
  window.clearTimeout(state.stateMachine.draftSyncTimer);
  state.stateMachine.draftSyncTimer = window.setTimeout(async () => {
    try {
      const snapshot = stateMachineSnapshot();
      await stateMachineApiPost("graphs/save", {
        id: stateMachineDraftGraphId,
        name: snapshot.name,
        nodes: snapshot.nodes,
      });
    } catch (error) {
      console.warn("Failed to sync state machine draft to backend", error);
    }
  }, stateMachineDraftSyncDelayMs);
}

function applyStateMachineSnapshot(snapshot) {
  if (!snapshot || typeof snapshot !== "object" || !Array.isArray(snapshot.nodes)) return false;
  state.stateMachine.name = String(snapshot.name || "未命名状态机");
  state.stateMachine.nodes = normalizeStateMachineNodes(snapshot.nodes);
  state.stateMachine.selectedId = stateMachineNodeById(snapshot.selectedId)?.id || "sm_start";
  return true;
}

function loadStateMachineState() {
  let hadLocalDraft = false;
  try {
    const draft = JSON.parse(localStorage.getItem(stateMachineDraftStorageKey) || "null");
    hadLocalDraft = applyStateMachineSnapshot(draft);
  } catch (error) {
    console.warn("Failed to load state machine draft", error);
  }
  ensureStateMachineGraph();
  return hadLocalDraft;
}

async function restoreStateMachineDraftFromBackend() {
  try {
    const payload = await stateMachineApiGet("graphs");
    state.stateMachine.graphs = Array.isArray(payload.graphs) ? payload.graphs : [];
    if (!state.stateMachine.selectedGraphId) {
      state.stateMachine.selectedGraphId =
        state.stateMachine.graphs.find((graph) => graph.id !== stateMachineDraftGraphId)?.id || "";
    }
    const draft = state.stateMachine.graphs.find((graph) => graph.id === stateMachineDraftGraphId);
    if (draft && applyStateMachineSnapshot(draft)) {
      ensureStateMachineGraph();
      try {
        localStorage.setItem(stateMachineDraftStorageKey, JSON.stringify(stateMachineSnapshot()));
      } catch (error) {
        console.warn("Failed to cache state machine draft", error);
      }
    }
    renderStateMachine();
  } catch (error) {
    console.warn("Failed to restore state machine draft from backend", error);
  }
}

function resetStateMachineRun() {
  state.stateMachine.run = {
    active: false,
    status: "idle",
    currentId: null,
    completedIds: [],
    activeEdge: null,
    edgePath: [],
    path: [],
    loop: false,
    iteration: 0,
    completedIterations: 0,
    startedAt: null,
    completedAt: null,
  };
}

function mutateStateMachine(options = {}) {
  if (!options.keepRun && !state.stateMachine.realRun.active) resetStateMachineRun();
  ensureStateMachineGraph();
  saveStateMachineDraft();
  renderStateMachine();
}

function addStateMachineTaskNode(libraryId, position = null) {
  const entry = stateMachineLibraryById(libraryId);
  if (!entry) return;
  const node = createStateMachineNodeFromLibrary(entry, position);
  state.stateMachine.nodes.push(node);
  state.stateMachine.selectedId = node.id;
  addLog("状态机", `已添加 ${stateMachineTaskMeta(node.taskType).label}状态：${node.title}`);
  mutateStateMachine();
}

function deleteStateMachineNode(id) {
  const node = stateMachineNodeById(id);
  if (!node || node.type !== "task") return;
  state.stateMachine.nodes.forEach((item) => {
    item.outgoingIds = (item.outgoingIds || []).filter((targetId) => targetId !== id);
  });
  state.stateMachine.nodes = state.stateMachine.nodes.filter((item) => item.id !== id);
  state.stateMachine.selectedId = "sm_start";
  addLog("状态机", `已删除任务 state：${node.title}`);
  mutateStateMachine();
}

function duplicateStateMachineNode(id) {
  const node = stateMachineNodeById(id);
  if (!node || node.type !== "task") return;
  const point = clampStateMachineNodePosition({ x: node.x + 44, y: node.y + 44 });
  const copy = {
    ...cloneStateMachineValue(node),
    id: `sm_node_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`,
    title: `${node.title} 副本`,
    x: point.x,
    y: point.y,
    outgoingIds: [],
  };
  state.stateMachine.nodes.push(copy);
  state.stateMachine.selectedId = copy.id;
  addLog("状态机", `已复制任务 state：${node.title}`);
  mutateStateMachine();
}

function connectStateMachineNodes(fromId, toId, options = {}) {
  const source = stateMachineNodeById(fromId);
  const target = stateMachineNodeById(toId);
  if (!source || !target || source.id === target.id || source.type === "end" || target.type === "start") return false;
  source.outgoingIds = Array.isArray(source.outgoingIds) ? source.outgoingIds : [];
  if (!source.outgoingIds.includes(target.id)) {
    source.outgoingIds.push(target.id);
    addLog("状态机", `${source.title} → ${target.title}`);
  }
  if (!options.keepConnecting) state.stateMachine.connectingFromId = "";
  state.stateMachine.selectedId = target.id;
  mutateStateMachine();
  return true;
}

function disconnectStateMachineNodes(fromId, toId) {
  const source = stateMachineNodeById(fromId);
  const target = stateMachineNodeById(toId);
  if (!source) return;
  source.outgoingIds = (source.outgoingIds || []).filter((id) => id !== toId);
  addLog("状态机", `已移除连线：${source.title} → ${target?.title || toId}`);
  mutateStateMachine();
}

function updateStateMachineName(value) {
  state.stateMachine.name = String(value || "").trim() || "未命名状态机";
  saveStateMachineDraft();
  renderStateMachine();
}

function parseStateMachineParamValue(input) {
  if (input.type === "number") {
    if (input.value === "") return null;
    const parsed = Number(input.value);
    return Number.isFinite(parsed) ? parsed : null;
  }
  return input.value;
}

function normalizeStateMachinePiperJointSide(value) {
  const side = String(value || "both").trim();
  if (["left", "right", "both"].includes(side)) return side;
  return "";
}

function stateMachinePiperJointSides(side) {
  return side === "both" ? ["left", "right"] : [side];
}

function validateStateMachinePiperJointParams(rawParams) {
  const merged = rawParams || {};
  const side = normalizeStateMachinePiperJointSide(merged.side);
  if (!side) {
    return { ok: false, field: "side", detail: "控制臂必须选择左臂、右臂或双臂" };
  }

  const params = { side };
  const readRequired = (key, label, min, max) => {
    const raw = merged[key];
    if (raw === null || raw === undefined || raw === "") {
      return { ok: false, field: key, detail: `${label} 必须填写` };
    }
    const value = Number(raw);
    if (!Number.isFinite(value)) {
      return { ok: false, field: key, detail: `${label} 必须是数字` };
    }
    if (Number.isFinite(min) && value < min) {
      return { ok: false, field: key, detail: `${label} 不能小于 ${min}` };
    }
    if (Number.isFinite(max) && value > max) {
      return { ok: false, field: key, detail: `${label} 不能大于 ${max}` };
    }
    params[key] = value;
    return { ok: true, value };
  };
  const readOptional = (key, label, fallback, min, max) => {
    const raw = merged[key];
    if (raw === null || raw === undefined || raw === "") {
      params[key] = fallback;
      return { ok: true, value: fallback };
    }
    return readRequired(key, label, min, max);
  };

  for (const sideName of stateMachinePiperJointSides(side)) {
    const sideLabel = piperArmLabels[sideName] || sideName;
    const jointLimits = armJointLimitsFor(sideName);
    for (let index = 1; index <= 6; index += 1) {
      const limit = jointLimits[index - 1];
      const key = `${sideName}Joint${index}Deg`;
      const result = readRequired(key, `${sideLabel} ${limit.name}`, limit.min, limit.max);
      if (!result.ok) return result;
    }
    const gripper = readRequired(`${sideName}GripperM`, `${sideLabel} 夹爪`, 0, 0.1);
    if (!gripper.ok) return gripper;
  }

  for (const item of [
    ["maxJointSpeedDegS", "最大关节速度", 5, PIPER_JOINT_SPEED_MIN, PIPER_JOINT_SPEED_MAX],
    ["gripperEffort", "夹爪 effort", PIPER_GRIPPER_EFFORT, 0.5, 3],
    ["toleranceDeg", "关节到位容差", 2, 0.01, 30],
    ["stableSec", "到位保持时间", 2, 0, 10],
    ["timeoutSec", "到位超时", 20, 0.1, 600],
  ]) {
    const result = readOptional(...item);
    if (!result.ok) return result;
  }

  return { ok: true, params };
}

function stateMachineParamSummary(node) {
  if (!node) return "--";
  if (node.type === "start") return "固定起始项";
  if (node.type === "end") return "固定终止项";
  const params = node.params || {};
  if (node.taskType === "navigation") {
    const target = params.targetName || "目标点";
    const x = Number(params.x);
    const y = Number(params.y);
    const yaw = Number(params.yawDeg);
    const pose = [x, y, yaw].every(Number.isFinite) ? `${x.toFixed(2)}, ${y.toFixed(2)}, ${yaw.toFixed(1)} deg` : "pose 未完整";
    return `${target} / ${pose}`;
  }
  if (node.taskType === "grasp") {
    const method = params.graspMethod === "auto" ? "自动(位姿)" : "推理";
    const arms = [
      params.leftTarget ? `左:${params.leftTarget}` : "",
      params.rightTarget ? `右:${params.rightTarget}` : "",
    ]
      .filter(Boolean)
      .join(" ") || "未配置目标";
    return `${method} / ${arms}`;
  }
  if (node.taskType === "inference") {
    const steps = Number(params.steps) || 20;
    const frequencyHz = Number(params.frequencyHz) || 10;
    const remote = params.remoteUrl || "--";
    return `${steps} 步 @ ${frequencyHz} Hz / ${remote}`;
  }
  if (node.taskType === "piper_joint") {
    const side = params.side === "left" ? "左臂" : params.side === "right" ? "右臂" : "双臂";
    const speed = Number(params.maxJointSpeedDegS) || 5;
    const tolerance = Number(params.toleranceDeg) || 2;
    return `${side} / ${formatNumber(speed, 1)} deg/s / 容差 ${formatNumber(tolerance, 1)} deg`;
  }
  if (node.taskType === "reset_odom") return "调用 /reset_odom，将 /odom 重置为 0";
  if (node.taskType === "wait") return `运动后静止 ${params.stableSec ?? "--"}s`;
  if (node.taskType === "topic_publish") return `发布 true：${params.topicName || params.actionKey || "--"}`;
  if (node.taskType === "topic_wait") return `等待 true：${params.topicName || params.topicKey || "--"}`;
  return stateMachineTaskMeta(node.taskType).summary;
}

function stateMachineRunState(node) {
  const run = state.stateMachine.run;
  if (run.currentId === node.id && run.status === "failed") return { label: "失败", className: "is-failed" };
  if (run.currentId === node.id && run.status === "stopped") return { label: "停止", className: "is-stopped" };
  if (run.currentId === node.id) return { label: "运行中", className: "is-running" };
  if (run.completedIds.includes(node.id)) return { label: "完成", className: "is-complete" };
  return { label: node.type === "task" ? "待执行" : "固定", className: "is-pending" };
}

function stateMachineVisibleTaskStatus() {
  const sm = state.stateMachine;
  const taskStatus = sm.realRun.taskStatus;
  if (!taskStatus?.nodeId) return null;
  if (sm.realRun.active || sm.realRun.status === "failed") return taskStatus;
  return null;
}

function stateMachineCanShowTaskDetail(node) {
  const taskStatus = stateMachineVisibleTaskStatus();
  return Boolean(node?.type === "task" && taskStatus && taskStatus.nodeId === node.id);
}

function openStateMachineTaskStatusPanel(nodeId) {
  const node = stateMachineNodeById(nodeId);
  if (!stateMachineCanShowTaskDetail(node)) return;
  state.stateMachine.realRun.taskStatusPanelOpen = true;
  renderStateMachine();
}

function closeStateMachineTaskStatusPanel() {
  state.stateMachine.realRun.taskStatusPanelOpen = false;
  renderStateMachine();
}

function stateMachineTaskPoseText(pose) {
  if (!pose || typeof pose !== "object") return "--";
  return [
    formatLocalizationNumber(pose.x, 2, " m"),
    formatLocalizationNumber(pose.y, 2, " m"),
    formatLocalizationNumber(pose.yawDeg, 1, " deg"),
  ].join(" / ");
}

function stateMachineTaskCommandText(command) {
  if (!command || typeof command !== "object") return "--";
  return [
    formatLocalizationNumber(command.linearX, 3),
    formatLocalizationNumber(command.linearY, 3),
    formatLocalizationNumber(command.angularZ, 3),
  ].join(" / ");
}

function stateMachineTaskStatusRows(taskStatus) {
  const data = taskStatus?.data && typeof taskStatus.data === "object" ? taskStatus.data : {};
  const rows = [
    ["状态", taskStatus?.status || "--"],
    ["说明", taskStatus?.detail || data.detail || "--"],
    ["更新时间", taskStatus?.updatedAt || "--"],
  ];
  if (taskStatus?.taskType === "navigation") {
    const errors = data.errors || {};
    const params = data.params || {};
    rows.push(
      ["阶段", navigationPhaseText(data.phase)],
      ["当前位姿", stateMachineTaskPoseText(data.currentPose)],
      ["距离误差", formatLocalizationNumber(errors.distance, 3, " m")],
      ["车体系误差", `${formatLocalizationNumber(errors.bodyX, 3)} / ${formatLocalizationNumber(errors.bodyY, 3)} m`],
      ["Yaw 误差", formatLocalizationNumber(errors.yawDeg, 2, " deg")],
      ["速度指令", stateMachineTaskCommandText(data.command)],
      ["限速", `${formatLocalizationNumber(params.maxLinearMps, 2)} / ${formatLocalizationNumber(params.maxLateralMps, 2)} / ${formatLocalizationNumber(params.maxAngularRadS, 2)}`],
      ["容差", `${formatLocalizationNumber(params.positionToleranceM, 2)} m / ${formatLocalizationNumber(params.yawToleranceDeg, 1)} deg`],
    );
  }
  if (taskStatus?.taskType === "wait") {
    rows.push(
      ["阶段", data.phase || "--"],
      ["静止计时", `${formatLocalizationNumber(data.stableElapsedSec, 1)} / ${formatLocalizationNumber(data.stableSec, 1)} s`],
      ["关节变化", formatLocalizationNumber(data.maxDeltaRad, 4, " rad")],
      ["夹爪变化", formatLocalizationNumber(data.maxGripperDeltaM, 4, " m")],
    );
  }
  if (taskStatus?.taskType === "reset_odom") {
    rows.push(
      ["阶段", data.phase || "--"],
      ["服务", data.service || "/reset_odom"],
      ["结果", data.code || "--"],
    );
  }
  if (taskStatus?.taskType === "inference") {
    const chunkTiming = data.chunkTiming || {};
    const executionTiming = data.executionTiming || {};
    rows.push(
      ["阶段", data.phase || "--"],
      ["轮次", data.round ?? "--"],
      ["远端", data.remoteUrl || "--"],
      ["完成信号", data.isSuccess === true ? "true" : data.isSuccess === false ? "false" : "--"],
      ["chunk", data.chunkId ? `${data.chunkId} (${data.chunkSteps || 0} 步)` : "--"],
      ["本轮执行", `${data.executedSteps ?? 0} / ${data.requestedSteps ?? data.steps ?? "--"} 步`],
      ["累计执行", `${data.totalExecutedSteps ?? 0} 步`],
      ["执行参数", `${data.steps ?? "--"} 步 @ ${formatLocalizationNumber(data.frequencyHz, 1)} Hz / ${formatLocalizationNumber(data.maxJointSpeedDegS, 1)} deg/s`],
      ["Piper 使能", data.autoEnablePiper ? data.enableCode || "自动" : "关闭"],
      ["请求耗时", formatLocalizationNumber(chunkTiming.totalMs, 1, " ms")],
      ["执行耗时", formatLocalizationNumber(executionTiming.totalMs, 1, " ms")],
      ["结果", data.executeCode || data.requestCode || data.connectCode || "--"],
    );
  }
  if (taskStatus?.taskType === "piper_joint") {
    const sideText = Array.isArray(data.sides)
      ? data.sides.map((side) => piperArmLabels[side] || side).join(" / ")
      : data.side || "--";
    rows.push(
      ["阶段", data.phase || "--"],
      ["控制臂", sideText],
      ["关节误差", `${formatLocalizationNumber(data.maxJointErrorDeg, 2, " deg")} / ${formatLocalizationNumber(data.maxJointErrorRad, 4, " rad")}`],
      ["夹爪误差", formatLocalizationNumber(data.maxGripperErrorM, 4, " m")],
      ["稳定计时", `${formatLocalizationNumber(data.stableElapsedSec, 1)} / ${formatLocalizationNumber(data.stableSec, 1)} s`],
      ["执行耗时", formatLocalizationNumber(data.elapsedSec, 1, " s")],
      ["速度", formatLocalizationNumber(data.maxJointSpeedDegS, 1, " deg/s")],
      ["关节容差", formatLocalizationNumber(data.toleranceDeg, 2, " deg")],
      ["发布 Topic", Array.isArray(data.topics) && data.topics.length ? data.topics.join(" / ") : "--"],
      ["反馈异常", data.lastFeedbackError || "--"],
      ["结果", data.publishCode || data.holdCode || "--"],
    );
  }
  if (taskStatus?.taskType === "topic_wait") {
    rows.push(
      ["阶段", data.phase || "--"],
      ["话题名", data.topic || data.key || "--"],
      ["Topic", data.topic || "--"],
      ["消息类型", data.messageType || "--"],
      ["Sequence", data.sequence ?? "--"],
      ["结果", data.code || "--"],
    );
  }
  if (taskStatus?.taskType === "topic_publish") {
    rows.push(
      ["阶段", data.phase || "--"],
      ["话题名", data.topic || data.key || "--"],
      ["Topic", data.topic || "--"],
      ["消息类型", data.messageType || "--"],
      ["发布时间", data.publishedAt || "--"],
      ["结果", data.code || "--"],
    );
  }
  return rows;
}

function renderStateMachineTaskStatusPanel() {
  const sm = state.stateMachine;
  const taskStatus = stateMachineVisibleTaskStatus();
  if (!sm.realRun.taskStatusPanelOpen || !taskStatus) return "";
  const node = stateMachineNodeById(taskStatus.nodeId);
  if (!stateMachineCanShowTaskDetail(node)) return "";
  const rows = stateMachineTaskStatusRows(taskStatus)
    .map(
      ([label, value]) => `
        <div>
          <span>${escapeHtml(label)}</span>
          <strong>${escapeHtml(value)}</strong>
        </div>
      `,
    )
    .join("");
  return `
    <aside class="state-machine-task-status-panel">
      <div class="state-machine-task-status-head">
        <div>
          <span>${escapeHtml(stateMachineTaskMeta(taskStatus.taskType).label)}</span>
          <strong>${escapeHtml(taskStatus.title || node?.title || "当前任务")}</strong>
        </div>
        <button type="button" data-sm-task-detail-close aria-label="关闭">×</button>
      </div>
      <div class="state-machine-task-status-grid">${rows}</div>
    </aside>
  `;
}

function stateMachineNodeCenter(node) {
  return {
    x: node.x + stateMachineNodeSize.width / 2,
    y: node.y + stateMachineNodeSize.height / 2,
  };
}

const stateMachineSideNormals = {
  left: { x: -1, y: 0 },
  right: { x: 1, y: 0 },
  top: { x: 0, y: -1 },
  bottom: { x: 0, y: 1 },
};

function stateMachineAnchorPoint(node, side, gap = 0) {
  const width = stateMachineNodeSize.width;
  const height = stateMachineNodeSize.height;
  if (side === "left") return { x: node.x - gap, y: node.y + height / 2 };
  if (side === "right") return { x: node.x + width + gap, y: node.y + height / 2 };
  if (side === "top") return { x: node.x + width / 2, y: node.y - gap };
  return { x: node.x + width / 2, y: node.y + height + gap };
}

function stateMachineEdgeGeometry(source, target) {
  const sourceCenter = stateMachineNodeCenter(source);
  const targetCenter = stateMachineNodeCenter(target);
  const dx = targetCenter.x - sourceCenter.x;
  const dy = targetCenter.y - sourceCenter.y;
  // Attach to the side facing the other node so the curve (and the arrow head)
  // stays outside the cards instead of getting covered by them.
  let sourceSide;
  let targetSide;
  if (Math.abs(dx) >= Math.abs(dy)) {
    sourceSide = dx >= 0 ? "right" : "left";
    targetSide = dx >= 0 ? "left" : "right";
  } else {
    sourceSide = dy >= 0 ? "bottom" : "top";
    targetSide = dy >= 0 ? "top" : "bottom";
  }
  const start = stateMachineAnchorPoint(source, sourceSide, 2);
  const end = stateMachineAnchorPoint(target, targetSide, 9);
  const reach = clamp(Math.hypot(end.x - start.x, end.y - start.y) * 0.45, 40, 170);
  const sourceNormal = stateMachineSideNormals[sourceSide];
  const targetNormal = stateMachineSideNormals[targetSide];
  const c1 = { x: start.x + sourceNormal.x * reach, y: start.y + sourceNormal.y * reach };
  const c2 = { x: end.x + targetNormal.x * reach, y: end.y + targetNormal.y * reach };
  const mid = {
    x: (start.x + 3 * c1.x + 3 * c2.x + end.x) / 8,
    y: (start.y + 3 * c1.y + 3 * c2.y + end.y) / 8,
  };
  return {
    path: `M ${start.x} ${start.y} C ${c1.x} ${c1.y}, ${c2.x} ${c2.y}, ${end.x} ${end.y}`,
    mid,
  };
}

function renderStateMachineEdges(workspaceSize = stateMachineWorkspaceSize()) {
  const sm = state.stateMachine;
  const edgePathKeys = new Set((sm.run.edgePath || []).map((edge) => `${edge.from}->${edge.to}`));
  const activeEdgeKey = sm.run.activeEdge ? `${sm.run.activeEdge.from}->${sm.run.activeEdge.to}` : "";
  const edges = [];
  sm.nodes.forEach((source) => {
    const outgoing = Array.isArray(source.outgoingIds) ? source.outgoingIds : [];
    outgoing.forEach((targetId) => {
      const target = stateMachineNodeById(targetId);
      if (!target) return;
      const key = `${source.id}->${target.id}`;
      const geometry = stateMachineEdgeGeometry(source, target);
      const randomLabel = outgoing.length > 1
        ? `<text x="${geometry.mid.x}" y="${geometry.mid.y - 16}" class="state-machine-edge-label">random</text>`
        : "";
      edges.push(`
        <g class="state-machine-edge-line ${edgePathKeys.has(key) ? "is-taken" : ""} ${activeEdgeKey === key ? "is-active" : ""}">
          <path class="state-machine-edge-hit" d="${geometry.path}"></path>
          <path class="state-machine-edge-visible" d="${geometry.path}" marker-end="url(#stateMachineArrow)"></path>
          ${randomLabel}
          <g
            class="state-machine-edge-delete"
            data-sm-edge-from="${escapeHtml(source.id)}"
            data-sm-edge-to="${escapeHtml(target.id)}"
            role="button"
            aria-label="删除连线"
          >
            <circle cx="${geometry.mid.x}" cy="${geometry.mid.y}" r="9"></circle>
            <text x="${geometry.mid.x}" y="${geometry.mid.y + 1}">×</text>
          </g>
        </g>
      `);
    });
  });
  return `
    <svg class="state-machine-edge-layer" viewBox="0 0 ${workspaceSize.width} ${workspaceSize.height}">
      <defs>
        <marker id="stateMachineArrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto">
          <path d="M0,0 L9,4.5 L0,9 z"></path>
        </marker>
      </defs>
      ${edges.join("")}
    </svg>
  `;
}

function renderStateMachineNodeCard(node) {
  const meta = stateMachineNodeMeta(node);
  const selected = state.stateMachine.selectedId === node.id;
  const connecting = state.stateMachine.connectingFromId === node.id;
  const runState = stateMachineRunState(node);
  const outgoing = Array.isArray(node.outgoingIds) ? node.outgoingIds : [];
  const nodeClass = node.type === "task" ? `is-${node.taskType}` : `is-${node.type}`;
  const canConnect = node.type !== "end";
  const canShowTaskDetail = stateMachineCanShowTaskDetail(node);
  const canEdit = node.type === "task" && stateMachineTaskEditable(node.taskType);
  const outputText = node.type === "end"
    ? "无出口"
    : outgoing.length > 1
      ? `${outgoing.length} 个随机出口`
      : outgoing.length === 1
        ? "1 个出口"
        : "未连接";
  return `
    <div
      class="state-machine-node ${nodeClass} ${selected ? "is-selected" : ""} ${connecting ? "is-connecting" : ""} ${runState.className}"
      data-sm-node-id="${escapeHtml(node.id)}"
      style="left:${node.x}px; top:${node.y}px; width:${stateMachineNodeSize.width}px; min-height:${stateMachineNodeSize.height}px;"
    >
      <button class="state-machine-node-drag" type="button" data-sm-drag-handle="${escapeHtml(node.id)}" title="拖动">⠿</button>
      <button class="state-machine-node-main" type="button" data-sm-select="${escapeHtml(node.id)}">
        <span class="state-machine-node-kicker">${escapeHtml(meta.label)}</span>
        <strong>${escapeHtml(node.title)}</strong>
        <small>${escapeHtml(stateMachineParamSummary(node))}</small>
      </button>
      <div class="state-machine-node-footer">
        <span class="state-machine-node-status">${escapeHtml(runState.label)}</span>
        <span class="state-machine-node-outputs">${escapeHtml(outputText)}</span>
      </div>
      <div class="state-machine-node-tools" aria-label="state 操作">
        ${canConnect ? `<button type="button" data-sm-connect-from="${escapeHtml(node.id)}">${connecting ? "选择目标" : "连线"}</button>` : ""}
        ${canShowTaskDetail ? `<button type="button" data-sm-task-detail="${escapeHtml(node.id)}">详情</button>` : ""}
        ${canEdit ? `<button type="button" data-sm-edit="${escapeHtml(node.id)}">编辑</button>` : ""}
        ${node.type === "task" ? `<button type="button" data-sm-duplicate="${escapeHtml(node.id)}">复制</button>` : ""}
        ${node.type === "task" ? `<button type="button" data-sm-delete="${escapeHtml(node.id)}">删除</button>` : ""}
      </div>
    </div>
  `;
}

function renderStateMachineModalField(field, value) {
  const label = `${field.label}${field.unit ? ` (${field.unit})` : ""}`;
  const fieldValue = value ?? "";
  if (field.type === "select") {
    const options = (field.options || [])
      .map((option) => `<option value="${escapeHtml(option.value)}" ${String(fieldValue) === String(option.value) ? "selected" : ""}>${escapeHtml(option.label)}</option>`)
      .join("");
    return `
      <label>
        <span class="field-label">${escapeHtml(label)}</span>
        <select data-sm-modal-field="${escapeHtml(field.key)}">${options}</select>
      </label>
    `;
  }
  return `
    <label>
      <span class="field-label">${escapeHtml(label)}</span>
      <input
        data-sm-modal-field="${escapeHtml(field.key)}"
        type="${field.type === "number" ? "number" : "text"}"
        value="${escapeHtml(fieldValue)}"
        ${field.step ? `step="${escapeHtml(field.step)}"` : ""}
        ${field.min ? `min="${escapeHtml(field.min)}"` : ""}
        ${field.max ? `max="${escapeHtml(field.max)}"` : ""}
        ${field.placeholder ? `placeholder="${escapeHtml(field.placeholder)}"` : ""}
        ${field.type === "number" ? "inputmode=\"decimal\"" : ""}
      >
    </label>
  `;
}

function renderStateMachineModalFields(fields, params) {
  return fields.map((field) => renderStateMachineModalField(field, params?.[field.key])).join("");
}

function stateMachineModalVisibleFields(taskType, params) {
  return (stateMachineTaskMeta(taskType).fields || []).filter((field) => {
    if (!field.showWhen) return true;
    const defaultParams = stateMachineTaskTypeDefaults[taskType] || {};
    const value = String(params?.[field.showWhen.key] ?? defaultParams[field.showWhen.key] ?? "");
    if (Array.isArray(field.showWhen.values)) {
      return field.showWhen.values.map(String).includes(value);
    }
    return value === String(field.showWhen.value);
  });
}

function renderStateMachineModalForm() {
  const config = state.stateMachine.modal;
  const form = $("#stateMachineModalForm");
  if (!config || !form) return;
  const fields = stateMachineModalVisibleFields(config.taskType, config.params);
  const baseFields = fields.filter((field) => !field.advanced);
  const advancedFields = fields.filter((field) => field.advanced);
  const advancedSection = advancedFields.length
    ? `
      <details class="state-machine-param-group" open>
        <summary>高级参数</summary>
        <div class="state-machine-param-grid">
          ${renderStateMachineModalFields(advancedFields, config.params)}
        </div>
      </details>
    `
    : "";
  form.innerHTML = `
    <label class="state-machine-modal-title-field">
      <span class="field-label">状态名</span>
      <input data-sm-modal-field="__title" type="text" value="${escapeHtml(config.title || "")}" placeholder="例如：靠近货柜">
    </label>
    ${renderStateMachineModalFields(baseFields, config.params)}
    ${advancedSection}
  `;
}

function openStateMachineModal(config) {
  state.stateMachine.modal = config;
  const modal = $("#stateMachineModal");
  if (!modal) return;
  const meta = stateMachineTaskMeta(config.taskType);
  const modalTitle = config.mode === "edit-node" ? "编辑状态" : config.mode === "edit-library" ? "编辑已保存状态" : "新建状态";
  setText("#stateMachineModalKicker", `${meta.label} / ${meta.summary}`);
  setText("#stateMachineModalTitle", modalTitle);
  renderStateMachineModalForm();
  modal.hidden = false;
  window.setTimeout(() => $("#stateMachineModalForm [data-sm-modal-field='__title']")?.focus(), 0);
}

function handleStateMachineModalChange(event) {
  const config = state.stateMachine.modal;
  const target = event.target;
  if (!config || !target?.dataset?.smModalField) return;
  const values = readStateMachineModalValues();
  if (values) {
    config.title = values.title;
    config.params = { ...config.params, ...values.params };
  }
  const field = (stateMachineTaskMeta(config.taskType).fields || []).find((item) => item.key === target.dataset.smModalField);
  if (field?.refresh) renderStateMachineModalForm();
}

function closeStateMachineModal() {
  state.stateMachine.modal = null;
  const modal = $("#stateMachineModal");
  if (modal) modal.hidden = true;
}

function readStateMachineModalValues() {
  const form = $("#stateMachineModalForm");
  if (!form) return null;
  const titleInput = form.querySelector("[data-sm-modal-field='__title']");
  const title = String(titleInput?.value || "").trim();
  const params = {};
  form.querySelectorAll("[data-sm-modal-field]").forEach((input) => {
    const key = input.dataset.smModalField;
    if (key === "__title") return;
    params[key] = parseStateMachineParamValue(input);
  });
  return { title, params };
}

async function submitStateMachineModal() {
  const config = state.stateMachine.modal;
  if (!config) return;
  const values = readStateMachineModalValues();
  if (!values) return;
  if (!values.title) {
    addLog("状态机", "状态名不能为空");
    $("#stateMachineModalForm [data-sm-modal-field='__title']")?.focus();
    return;
  }
  // Merge over the modal params so values of fields hidden by the current
  // graspMethod selection are preserved instead of dropped.
  let params = { ...config.params, ...values.params };
  if (config.taskType === "wait") {
    const stableSec = Number(values.params.stableSec);
    if (!Number.isFinite(stableSec) || stableSec < 0.1) {
      addLog("状态机", "静止等待时间必须 >= 0.1s");
      $("#stateMachineModalForm [data-sm-modal-field='stableSec']")?.focus();
      return;
    }
    params = { stableSec };
  }
  if (config.taskType === "topic_publish") {
    const topicName = String(values.params.topicName || "").trim();
    if (!topicName) {
      addLog("状态机", "发布话题名不能为空");
      $("#stateMachineModalForm [data-sm-modal-field='topicName']")?.focus();
      return;
    }
    params = { topicName };
  }
  if (config.taskType === "topic_wait") {
    const topicName = String(values.params.topicName || "").trim();
    if (!topicName) {
      addLog("状态机", "监听话题名不能为空");
      $("#stateMachineModalForm [data-sm-modal-field='topicName']")?.focus();
      return;
    }
    params = { topicName, timeoutSec: Number(config.params.timeoutSec) || 0 };
  }
  if (config.taskType === "inference") {
    const merged = { ...config.params, ...values.params };
    const remoteUrl = String(merged.remoteUrl || "").trim();
    if (!remoteUrl) {
      addLog("状态机", "推理远端地址不能为空");
      $("#stateMachineModalForm [data-sm-modal-field='remoteUrl']")?.focus();
      return;
    }
    const steps = clamp(Math.round(Number(merged.steps) || 20), 1, 200);
    const frequencyHz = clamp(Number(merged.frequencyHz) || 10, 1, 30);
    const maxJointSpeedDegS = clamp(Number(merged.maxJointSpeedDegS) || 20, 0.5, 30);
    const limit = (key, fallback) => {
      const value = Number(merged[key]);
      return Number.isFinite(value) && value >= 0 ? value : fallback;
    };
    params = {
      remoteUrl,
      prompt: String(merged.prompt || ""),
      steps,
      frequencyHz,
      maxJointSpeedDegS,
      autoEnablePiper: String(merged.autoEnablePiper ?? "true") !== "false",
      maxLinearMps: limit("maxLinearMps", 0.2),
      maxLateralMps: limit("maxLateralMps", 0.15),
      maxAngularRadS: limit("maxAngularRadS", 0.5),
    };
  }
  if (config.taskType === "piper_joint") {
    const validated = validateStateMachinePiperJointParams({ ...config.params, ...values.params });
    if (!validated.ok) {
      addLog("状态机", validated.detail);
      if (validated.field) {
        $("#stateMachineModalForm [data-sm-modal-field='" + validated.field + "']")?.focus();
      }
      return;
    }
    params = validated.params;
  }

  if (config.mode === "edit-node") {
    const node = stateMachineNodeById(config.nodeId);
    if (node && node.type === "task") {
      node.title = values.title;
      node.params = params;
      addLog("状态机", `状态已更新：${node.title}`);
      mutateStateMachine();
    }
    closeStateMachineModal();
    return;
  }

  try {
    const savePayload = {
      taskType: config.taskType,
      title: values.title,
      params,
    };
    if (config.mode === "edit-library" && config.libraryId) savePayload.id = config.libraryId;
    const payload = await stateMachineApiPost("states/save", savePayload);
    if (payload.state) {
      const existingIndex = state.stateMachine.library.findIndex((entry) => entry.id === payload.state.id);
      if (existingIndex >= 0) {
        state.stateMachine.library.splice(existingIndex, 1, payload.state);
      } else {
        state.stateMachine.library.push(payload.state);
      }
    }
    addLog("状态机", `${config.mode === "edit-library" ? "状态库已更新" : "状态已保存到状态库"}：${values.title}`);
    closeStateMachineModal();
    renderStateMachine();
  } catch (error) {
    addLog("状态机", `状态保存失败：${error.message}`);
  }
}

function openStateMachineLibraryEditor(libraryId) {
  const entry = stateMachineLibraryById(libraryId);
  if (!entry || entry.builtIn) return;
  openStateMachineModal({
    mode: "edit-library",
    libraryId: entry.id,
    taskType: entry.taskType,
    title: entry.title,
    params: cloneStateMachineValue(entry.params || {}),
  });
}

async function deleteStateMachineLibraryEntry(libraryId) {
  const entry = stateMachineLibraryById(libraryId);
  if (!entry) return;
  try {
    await stateMachineApiPost("states/delete", { id: libraryId });
    state.stateMachine.library = state.stateMachine.library.filter((item) => item.id !== libraryId);
    addLog("状态机", `已从状态库删除：${entry.title}`);
    renderStateMachine();
  } catch (error) {
    addLog("状态机", `状态删除失败：${error.message}`);
  }
}

function stateMachineLibrarySummary(entry) {
  return stateMachineParamSummary({ type: "task", taskType: entry.taskType, params: entry.params || {} });
}

function renderStateMachineTaskLibrary() {
  const library = $("#stateMachineNodeLibrary");
  if (!library) return;
  library.innerHTML = Object.entries(stateMachineTaskTypes)
    .map(([taskType, taskMeta]) => {
      const entries = stateMachineLibraryForTask(taskType)
        .map(
          (entry) => `
            <div class="state-machine-library-item">
              <button type="button" draggable="true" data-sm-library-id="${escapeHtml(entry.id)}">
                <strong>${escapeHtml(entry.title)}</strong>
                <span>${escapeHtml(stateMachineLibrarySummary(entry))}</span>
              </button>
              ${
                entry.builtIn
                  ? ""
                  : `
                    <button type="button" class="state-machine-library-edit" data-sm-library-edit="${escapeHtml(entry.id)}" title="编辑已保存状态" aria-label="编辑已保存状态">✎</button>
                    <button type="button" class="state-machine-library-remove" data-sm-library-remove="${escapeHtml(entry.id)}" title="从状态库删除" aria-label="从状态库删除">×</button>
                  `
              }
            </div>
          `,
        )
        .join("");
      const addButton = taskMeta.allowCreate === false
        ? ""
        : `<button type="button" class="state-machine-task-add" data-sm-add-type="${escapeHtml(taskType)}" title="新建${escapeHtml(taskMeta.label)}状态" aria-label="新建${escapeHtml(taskMeta.label)}状态">＋</button>`;
      const emptyHint = state.stateMachine.libraryLoaded
        ? `<div class="state-machine-library-empty">点击 + 新建${taskMeta.label}状态</div>`
        : `<div class="state-machine-library-empty">状态库加载中…</div>`;
      return `
        <section class="state-machine-task-group">
          <div class="state-machine-task-group-title">
            <div>
              <strong>${escapeHtml(taskMeta.label)}</strong>
              <span>${escapeHtml(taskMeta.summary)}</span>
            </div>
            ${addButton}
          </div>
          <div class="state-machine-task-buttons">${entries || emptyHint}</div>
        </section>
      `;
    })
    .join("");
}

function renderStateMachineGraphBar() {
  const sm = state.stateMachine;
  const select = $("#stateMachineGraphSelect");
  if (!select) return;
  const graphs = sm.graphs.filter((graph) => graph.id !== stateMachineDraftGraphId);
  select.innerHTML = graphs.length
    ? graphs
        .map((graph) => `<option value="${escapeHtml(graph.id)}" ${sm.selectedGraphId === graph.id ? "selected" : ""}>${escapeHtml(graph.name || graph.id)}</option>`)
        .join("")
    : `<option value="">暂无已保存流程</option>`;
  select.disabled = graphs.length === 0;
  const loadButton = $("#stateMachineGraphLoadButton");
  if (loadButton) loadButton.disabled = !graphs.length || !sm.selectedGraphId;
  const deleteButton = $("#stateMachineGraphDeleteButton");
  if (deleteButton) deleteButton.disabled = !graphs.length || !sm.selectedGraphId;
}

function eventSequenceRunState(event) {
  const run = state.stateMachine.eventSequence.run;
  if (run.currentEventId === event.id && run.status === "failed") return { label: "失败", className: "is-failed" };
  if (run.currentEventId === event.id && run.status === "stopped") return { label: "停止", className: "is-stopped" };
  if (run.currentEventId === event.id && run.status === "running") return { label: "运行中", className: "is-running" };
  if (run.completedEventIds.includes(event.id)) return { label: "完成", className: "is-complete" };
  if (event.enabled === false) return { label: "禁用", className: "is-disabled" };
  return { label: "待执行", className: "is-pending" };
}

function renderEventSequenceLibrary() {
  const library = $("#stateMachineEventLibrary");
  if (!library) return;
  const graphs = state.stateMachine.graphs.filter((graph) => graph.id !== stateMachineDraftGraphId);
  library.innerHTML = graphs.length
    ? graphs
        .map(
          (graph) => `
            <button
              type="button"
              draggable="true"
              data-sm-event-graph-id="${escapeHtml(graph.id)}"
              class="state-machine-event-library-item"
            >
              <strong>${escapeHtml(graph.name || graph.id)}</strong>
              <span>${escapeHtml(stateMachineGraphSummary(graph))}</span>
            </button>
          `,
        )
        .join("")
    : `<div class="state-machine-library-empty">暂无已保存流程</div>`;
}

function renderEventSequenceSelect() {
  const sequenceState = state.stateMachine.eventSequence;
  const select = $("#eventSequenceSelect");
  if (!select) return;
  select.innerHTML = sequenceState.sequences.length
    ? sequenceState.sequences
        .map(
          (sequence) => `<option value="${escapeHtml(sequence.id)}" ${sequenceState.selectedSequenceId === sequence.id ? "selected" : ""}>${escapeHtml(sequence.name || sequence.id)}</option>`,
        )
        .join("")
    : `<option value="">暂无已保存序列</option>`;
  select.disabled = sequenceState.sequences.length === 0;
  const loadButton = $("#eventSequenceLoadButton");
  const deleteButton = $("#eventSequenceDeleteButton");
  if (loadButton) loadButton.disabled = !sequenceState.sequences.length || !sequenceState.selectedSequenceId;
  if (deleteButton) deleteButton.disabled = !sequenceState.sequences.length || !sequenceState.selectedSequenceId;
}

function renderEventSequenceList() {
  const list = $("#stateMachineEventSequenceList");
  if (!list) return;
  const sequenceState = state.stateMachine.eventSequence;
  if (!sequenceState.events.length) {
    list.innerHTML = `<div class="state-machine-event-empty">从事件库拖入流程</div>`;
    return;
  }
  list.innerHTML = sequenceState.events
    .map((event, index) => {
      const graph = stateMachineGraphById(event.graphId);
      const selected = sequenceState.selectedId === event.id;
      const runState = eventSequenceRunState(event);
      return `
        <div
          class="state-machine-event-row ${selected ? "is-selected" : ""} ${runState.className}"
          data-sm-event-id="${escapeHtml(event.id)}"
          draggable="true"
        >
          <button class="state-machine-event-main" type="button" data-sm-event-select="${escapeHtml(event.id)}">
            <span class="state-machine-event-index">${index + 1}</span>
            <span class="state-machine-event-copy">
              <strong>${escapeHtml(event.title)}</strong>
              <small>${escapeHtml(graph ? stateMachineGraphSummary(graph) : "引用流程已丢失")}</small>
            </span>
            <span class="state-machine-node-status">${escapeHtml(runState.label)}</span>
          </button>
          <div class="state-machine-event-tools">
            <button type="button" data-sm-event-move="${escapeHtml(event.id)}" data-sm-event-dir="-1" ${index === 0 ? "disabled" : ""}>上移</button>
            <button type="button" data-sm-event-move="${escapeHtml(event.id)}" data-sm-event-dir="1" ${index === sequenceState.events.length - 1 ? "disabled" : ""}>下移</button>
            <button type="button" data-sm-event-toggle="${escapeHtml(event.id)}">${event.enabled === false ? "启用" : "禁用"}</button>
            <button type="button" data-sm-event-duplicate="${escapeHtml(event.id)}">复制</button>
            <button type="button" data-sm-event-remove="${escapeHtml(event.id)}">移除</button>
          </div>
        </div>
      `;
    })
    .join("");
}

function renderEventSequenceGraphTasks(graph) {
  const tasks = (Array.isArray(graph?.nodes) ? graph.nodes : []).filter((node) => node?.type === "task");
  if (!tasks.length) return `<div class="state-machine-event-task-empty">无任务节点</div>`;
  return tasks
    .slice(0, 8)
    .map(
      (node, index) => `
        <div class="state-machine-event-task-row">
          <span>${index + 1}</span>
          <strong>${escapeHtml(node.title || stateMachineTaskMeta(node.taskType).label)}</strong>
          <small>${escapeHtml(stateMachineTaskMeta(node.taskType).label)}</small>
        </div>
      `,
    )
    .join("");
}

function renderEventSequenceChildRun(childRun) {
  if (!childRun) return `<div class="state-machine-event-task-empty">未运行子流程</div>`;
  const taskStatus = childRun.taskStatus || null;
  const rows = taskStatus
    ? stateMachineTaskStatusRows(taskStatus)
        .slice(0, 10)
        .map(
          ([label, value]) => `
            <div>
              <span>${escapeHtml(label)}</span>
              <strong>${escapeHtml(value)}</strong>
            </div>
          `,
        )
        .join("")
    : "";
  return `
    <div class="state-machine-event-run-summary">
      <div>
        <span>子流程</span>
        <strong>${escapeHtml(childRun.graphName || "--")}</strong>
      </div>
      <div>
        <span>当前节点</span>
        <strong>${escapeHtml(childRun.currentId || "--")}</strong>
      </div>
      <div>
        <span>状态</span>
        <strong>${escapeHtml(childRun.status || "--")}</strong>
      </div>
    </div>
    ${rows ? `<div class="state-machine-task-status-grid state-machine-event-child-grid">${rows}</div>` : ""}
  `;
}

function renderEventSequenceDetail() {
  const detail = $("#stateMachineEventDetail");
  if (!detail) return;
  const sequenceState = state.stateMachine.eventSequence;
  const activeEvent = sequenceState.events.find((event) => event.id === sequenceState.run.currentEventId);
  const event = activeEvent || selectedEventSequenceEvent();
  if (!event) {
    detail.innerHTML = `<div class="state-machine-event-empty">未选择事件</div>`;
    return;
  }
  const graph = stateMachineGraphById(event.graphId);
  const runState = eventSequenceRunState(event);
  const eventStatus = sequenceState.run.eventStatus;
  detail.innerHTML = `
    <div class="state-machine-event-detail-head ${runState.className}">
      <span>${escapeHtml(runState.label)}</span>
      <strong>${escapeHtml(event.title)}</strong>
      <small>${escapeHtml(graph?.name || event.graphId || "--")}</small>
    </div>
    <div class="state-machine-event-detail-actions">
      <button class="secondary-button" type="button" data-sm-event-open-graph="${escapeHtml(event.graphId)}" ${graph ? "" : "disabled"}>打开编辑</button>
      <button class="secondary-button" type="button" data-sm-event-add-copy="${escapeHtml(event.graphId)}" ${graph ? "" : "disabled"}>追加一次</button>
    </div>
    <div class="state-machine-event-run-summary">
      <div>
        <span>事件</span>
        <strong>${escapeHtml(eventStatus?.title || event.title)}</strong>
      </div>
      <div>
        <span>轮次</span>
        <strong>${escapeHtml(sequenceState.run.loop ? `${sequenceState.run.iteration || 1} / 完成 ${sequenceState.run.completedIterations || 0}` : "--")}</strong>
      </div>
      <div>
        <span>说明</span>
        <strong>${escapeHtml(eventStatus?.detail || stateMachineGraphSummary(graph))}</strong>
      </div>
    </div>
    <section class="state-machine-event-detail-section">
      <strong>子流程任务</strong>
      <div class="state-machine-event-task-list">${renderEventSequenceGraphTasks(graph)}</div>
    </section>
    <section class="state-machine-event-detail-section">
      <strong>运行详情</strong>
      ${renderEventSequenceChildRun(sequenceState.run.childRun)}
    </section>
  `;
}

function renderEventSequence() {
  const sequenceState = state.stateMachine.eventSequence;
  const nameInput = $("#eventSequenceNameInput");
  if (nameInput && document.activeElement !== nameInput) nameInput.value = sequenceState.name || "";
  setText("#eventSequenceTitle", sequenceState.name || "事件序列草稿");
  const enabledCount = sequenceState.events.filter((event) => event.enabled !== false).length;
  const summaryParts = [`${sequenceState.events.length} 个事件`, `${enabledCount} 个启用`];
  if (sequenceState.run.loop) {
    summaryParts.push(`循环第 ${sequenceState.run.iteration || 1} 轮`);
    summaryParts.push(`已完成 ${sequenceState.run.completedIterations || 0} 轮`);
  }
  setText("#eventSequenceSummary", summaryParts.join(" / "));
  if (sequenceState.realRun.active && sequenceState.run.loop) {
    setStateBadge("#eventSequenceBadge", "循环运行中", "ok");
  } else if (sequenceState.realRun.active) {
    setStateBadge("#eventSequenceBadge", "运行中", "ok");
  } else if (sequenceState.run.status === "completed") {
    setStateBadge("#eventSequenceBadge", "运行完成", "ok");
  } else if (sequenceState.run.status === "failed") {
    setStateBadge("#eventSequenceBadge", "运行失败", "danger");
  } else if (sequenceState.run.status === "stopped") {
    setStateBadge("#eventSequenceBadge", "已停止", "warn");
  } else {
    setStateBadge("#eventSequenceBadge", "编辑中", "idle");
  }

  const runButton = $("#eventSequenceRunButton");
  if (runButton) {
    const canRerun = ["completed", "failed", "stopped"].includes(sequenceState.run.status);
    runButton.disabled = sequenceState.realRun.active || enabledCount === 0;
    runButton.textContent = sequenceState.realRun.active ? "运行中" : canRerun ? "重新运行序列" : "运行序列";
  }
  const loopButton = $("#eventSequenceLoopButton");
  if (loopButton) {
    loopButton.disabled = sequenceState.realRun.active || enabledCount === 0;
    loopButton.textContent = sequenceState.realRun.active && sequenceState.run.loop ? "循环中" : "循环运行";
  }
  const stopButton = $("#eventSequenceStopButton");
  if (stopButton) stopButton.disabled = !sequenceState.realRun.active;

  renderEventSequenceSelect();
  renderEventSequenceLibrary();
  renderEventSequenceList();
  renderEventSequenceDetail();
}

async function saveStateMachineGraphToBackend() {
  const snapshot = stateMachineSnapshot();
  try {
    const payload = await stateMachineApiPost("graphs/save", {
      name: snapshot.name,
      nodes: snapshot.nodes,
    });
    if (payload.graph?.id) state.stateMachine.selectedGraphId = payload.graph.id;
    addLog("状态机", `流程已保存到后端：${snapshot.name}`);
    await refreshStateMachineGraphs({ silent: true });
  } catch (error) {
    addLog("状态机", `流程保存失败：${error.message}`);
  }
}

function loadStateMachineGraphFromBackend() {
  const sm = state.stateMachine;
  const graph = sm.graphs.find((item) => item.id === sm.selectedGraphId);
  if (!graph) return;
  applyStateMachineSnapshot(graph);
  sm.connectingFromId = "";
  resetStateMachineRun();
  addLog("状态机", `流程已载入：${graph.name || graph.id}`);
  saveStateMachineDraft();
  renderStateMachine();
}

async function deleteStateMachineGraphFromBackend() {
  const sm = state.stateMachine;
  const graph = sm.graphs.find((item) => item.id === sm.selectedGraphId);
  if (!graph) return;
  try {
    await stateMachineApiPost("graphs/delete", { id: graph.id });
    addLog("状态机", `流程已删除：${graph.name || graph.id}`);
    await refreshStateMachineGraphs({ silent: true });
  } catch (error) {
    addLog("状态机", `流程删除失败：${error.message}`);
  }
}

function updateEventSequenceName(value) {
  state.stateMachine.eventSequence.name = String(value || "").trim() || "未命名事件序列";
  saveEventSequenceDraft();
  renderStateMachine();
}

async function saveEventSequenceToBackend() {
  const snapshot = eventSequenceSnapshot();
  if (!snapshot.events.length) {
    addLog("状态机", "事件序列不能为空");
    return;
  }
  try {
    const payload = await stateMachineApiPost("event-sequences/save", {
      id: state.stateMachine.eventSequence.selectedSequenceId || undefined,
      name: snapshot.name,
      events: snapshot.events,
    });
    if (payload.eventSequence?.id) state.stateMachine.eventSequence.selectedSequenceId = payload.eventSequence.id;
    addLog("状态机", `事件序列已保存：${snapshot.name}`);
    await refreshStateMachineEventSequences({ silent: true });
  } catch (error) {
    addLog("状态机", `事件序列保存失败：${error.message}`);
  }
}

function loadEventSequenceFromBackend() {
  const sequenceState = state.stateMachine.eventSequence;
  const sequence = sequenceState.sequences.find((item) => item.id === sequenceState.selectedSequenceId);
  if (!sequence) return;
  applyEventSequenceSnapshot(sequence);
  sequenceState.selectedSequenceId = sequence.id;
  addLog("状态机", `事件序列已载入：${sequence.name || sequence.id}`);
  saveEventSequenceDraft();
  renderStateMachine();
}

async function deleteEventSequenceFromBackend() {
  const sequenceState = state.stateMachine.eventSequence;
  const sequence = sequenceState.sequences.find((item) => item.id === sequenceState.selectedSequenceId);
  if (!sequence) return;
  try {
    await stateMachineApiPost("event-sequences/delete", { id: sequence.id });
    addLog("状态机", `事件序列已删除：${sequence.name || sequence.id}`);
    sequenceState.selectedSequenceId = "";
    await refreshStateMachineEventSequences({ silent: true });
  } catch (error) {
    addLog("状态机", `事件序列删除失败：${error.message}`);
  }
}

function clearEventSequence() {
  const sequenceState = state.stateMachine.eventSequence;
  sequenceState.events = [];
  sequenceState.selectedId = "";
  sequenceState.selectedSequenceId = "";
  resetEventSequenceRun();
  addLog("状态机", "事件序列已清空");
  saveEventSequenceDraft();
  renderStateMachine();
}

function applyEventSequenceBackendRun(run) {
  const sequenceState = state.stateMachine.eventSequence;
  const status = run.status || "idle";
  sequenceState.realRun.active = !!run.active;
  sequenceState.realRun.status = status;
  sequenceState.run = {
    ...sequenceState.run,
    active: !!run.active,
    status,
    currentEventId: run.currentEventId || null,
    currentEventIndex: Number.isFinite(Number(run.currentEventIndex)) ? Number(run.currentEventIndex) : -1,
    completedEventIds: Array.isArray(run.completedEventIds) ? run.completedEventIds : [],
    path: Array.isArray(run.path) ? run.path : [],
    loop: run.loop === true,
    iteration: Number.isFinite(Number(run.iteration)) ? Number(run.iteration) : 0,
    completedIterations: Number.isFinite(Number(run.completedIterations)) ? Number(run.completedIterations) : 0,
    eventStatus: run.eventStatus || null,
    childRun: run.childRun || null,
    error: run.error || "",
  };
  if (run.currentEventId && sequenceState.events.some((event) => event.id === run.currentEventId)) {
    sequenceState.selectedId = run.currentEventId;
  }
}

function stopEventSequenceRunPolling() {
  window.clearInterval(state.stateMachine.eventSequence.realRun.pollTimer);
  state.stateMachine.eventSequence.realRun.pollTimer = null;
}

async function pollEventSequenceRunStatus() {
  const sequenceState = state.stateMachine.eventSequence;
  try {
    const payload = await stateMachineApiGet("event-run/status");
    const run = payload.run || {};
    applyEventSequenceBackendRun(run);
    if (!run.active) {
      stopEventSequenceRunPolling();
      if (run.status === "completed") addLog("状态机", "事件序列运行完成");
      if (run.status === "failed") addLog("状态机", `事件序列运行失败：${run.error || "未知原因"}`);
      if (run.status === "stopped") {
        const completedText = run.loop ? `，已完成 ${run.completedIterations || 0} 轮` : "";
        addLog("状态机", `事件序列已停止${completedText}`);
      }
    }
    renderStateMachine();
  } catch (error) {
    stopEventSequenceRunPolling();
    sequenceState.realRun.active = false;
    addLog("状态机", `事件序列状态查询失败：${error.message}`);
    renderStateMachine();
  }
}

async function startEventSequenceRun(options = {}) {
  const sequenceState = state.stateMachine.eventSequence;
  if (sequenceState.realRun.active) return;
  const snapshot = eventSequenceSnapshot();
  const enabledEvents = snapshot.events.filter((event) => event.enabled !== false);
  if (!enabledEvents.length) {
    addLog("状态机", "事件序列没有启用事件");
    return;
  }
  const loop = options.loop === true;
  try {
    const payload = await stateMachineApiPost("event-run/start", { name: snapshot.name, events: snapshot.events, loop });
    applyEventSequenceBackendRun(payload.run || { active: true, status: "running", currentEventId: enabledEvents[0].id, path: [enabledEvents[0].id], loop });
    addLog("状态机", `${loop ? "循环运行事件序列" : "事件序列运行"}已启动：${snapshot.name}`);
    stopEventSequenceRunPolling();
    sequenceState.realRun.pollTimer = window.setInterval(pollEventSequenceRunStatus, 1000);
    pollEventSequenceRunStatus();
    renderStateMachine();
  } catch (error) {
    addLog("状态机", `事件序列启动失败：${error.message}`);
  }
}

async function stopEventSequenceRun() {
  try {
    await stateMachineApiPost("event-run/stop");
    addLog("状态机", "已请求停止事件序列");
    pollEventSequenceRunStatus();
  } catch (error) {
    addLog("状态机", `事件序列停止失败：${error.message}`);
  }
}

function openEventGraphInEditor(graphId) {
  const graph = stateMachineGraphById(graphId);
  if (!graph) return;
  applyStateMachineSnapshot(graph);
  state.stateMachine.selectedGraphId = graph.id;
  state.stateMachine.connectingFromId = "";
  setStateMachineMode("graph");
  addLog("状态机", `已打开事件流程：${graph.name || graph.id}`);
  saveStateMachineDraft();
}

function renderStateMachineCanvas() {
  const canvas = $("#stateMachineCanvas");
  if (!canvas) return;
  ensureStateMachineGraph();
  const scrollLeft = canvas.scrollLeft;
  const scrollTop = canvas.scrollTop;
  const workspaceSize = stateMachineWorkspaceSize();
  canvas.innerHTML = `
    <div class="state-machine-workspace" style="width:${workspaceSize.width}px; height:${workspaceSize.height}px;">
      ${renderStateMachineEdges(workspaceSize)}
      ${state.stateMachine.nodes.map((node) => renderStateMachineNodeCard(node)).join("")}
    </div>
    ${renderStateMachineTaskStatusPanel()}
  `;
  canvas.scrollLeft = scrollLeft;
  canvas.scrollTop = scrollTop;
}

function renderStateMachine() {
  const sm = state.stateMachine;
  ensureStateMachineGraph();
  const mode = sm.mode === "events" ? "events" : "graph";
  $$("[data-sm-mode-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.smModePanel !== mode;
  });
  $$("[data-sm-actions-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.smActionsPanel !== mode;
  });
  $$("[data-sm-mode]").forEach((button) => {
    button.classList.toggle("is-active", button.dataset.smMode === mode);
  });
  renderStateMachineTaskLibrary();
  const taskCount = sm.nodes.filter((node) => node.type === "task").length;
  const edgeCount = sm.nodes.reduce((total, node) => total + (node.outgoingIds || []).length, 0);
  const selected = stateMachineSelectedNode();
  const nameInput = $("#stateMachineNameInput");
  if (nameInput && document.activeElement !== nameInput) nameInput.value = sm.name || "";
  setText("#stateMachineTitle", sm.name || "状态机草稿");
  const summaryParts = [`${taskCount} 个任务 state`, `${edgeCount} 条连线`, "多出口随机执行"];
  if (sm.run.loop) {
    summaryParts.push(`循环第 ${sm.run.iteration || 1} 轮`);
    summaryParts.push(`已完成 ${sm.run.completedIterations || 0} 轮`);
  }
  setText("#stateMachineSummary", summaryParts.join(" / "));

  if (sm.realRun.active && sm.run.loop) {
    setStateBadge("#stateMachineBadge", "循环运行中", "ok");
  } else if (sm.realRun.active) {
    setStateBadge("#stateMachineBadge", "运行中", "ok");
  } else if (sm.run.status === "completed") {
    setStateBadge("#stateMachineBadge", "运行完成", "ok");
  } else if (sm.run.status === "failed") {
    setStateBadge("#stateMachineBadge", "运行失败", "danger");
  } else if (sm.run.status === "stopped") {
    setStateBadge("#stateMachineBadge", "已停止", "warn");
  } else if (sm.connectingFromId) {
    setStateBadge("#stateMachineBadge", "选择目标", "warn");
  } else {
    setStateBadge("#stateMachineBadge", selected ? "编辑中" : "待添加", selected ? "idle" : "warn");
  }

  const hasStartExit = Boolean(stateMachineNodeById("sm_start")?.outgoingIds?.length);
  const realRunButton = $("#stateMachineRealRunButton");
  if (realRunButton) {
    const canRerun = ["completed", "failed", "stopped"].includes(sm.run.status);
    realRunButton.disabled = sm.realRun.active || !hasStartExit;
    realRunButton.textContent = sm.realRun.active ? "运行中" : canRerun ? "重新运行" : "运行";
  }
  const realLoopButton = $("#stateMachineRealLoopButton");
  if (realLoopButton) {
    realLoopButton.disabled = sm.realRun.active || !hasStartExit;
    realLoopButton.textContent = sm.realRun.active && sm.run.loop ? "循环中" : "循环运行";
  }
  const realStopButton = $("#stateMachineRealStopButton");
  if (realStopButton) realStopButton.disabled = !sm.realRun.active;

  renderStateMachineCanvas();
  renderStateMachineGraphBar();
  renderEventSequence();
}

function applyStateMachineBackendRun(run) {
  const sm = state.stateMachine;
  const status = run.status || "idle";
  sm.realRun.active = !!run.active;
  sm.realRun.status = status;
  sm.realRun.taskStatus = run.taskStatus || null;
  if (!stateMachineVisibleTaskStatus()) sm.realRun.taskStatusPanelOpen = false;
  sm.run = {
    ...sm.run,
    active: false,
    status,
    currentId: run.currentId || null,
    completedIds: Array.isArray(run.completedIds) ? run.completedIds : [],
    activeEdge: null,
    edgePath: Array.isArray(run.edgePath) ? run.edgePath : [],
    path: Array.isArray(run.path) ? run.path : [],
    loop: run.loop === true,
    iteration: Number.isFinite(Number(run.iteration)) ? Number(run.iteration) : 0,
    completedIterations: Number.isFinite(Number(run.completedIterations)) ? Number(run.completedIterations) : 0,
  };
}

function stopStateMachineRunPolling() {
  window.clearInterval(state.stateMachine.realRun.pollTimer);
  state.stateMachine.realRun.pollTimer = null;
}

async function pollStateMachineRunStatus() {
  const sm = state.stateMachine;
  try {
    const payload = await stateMachineApiGet("run/status");
    const run = payload.run || {};
    applyStateMachineBackendRun(run);
    if (!run.active) {
      stopStateMachineRunPolling();
      if (run.status === "completed") addLog("状态机", "运行完成");
      if (run.status === "failed") addLog("状态机", `运行失败：${run.error || "未知原因"}`);
      if (run.status === "stopped") {
        const completedText = run.loop ? `，已完成 ${run.completedIterations || 0} 轮` : "";
        addLog("状态机", `运行已停止${completedText}`);
      }
    }
    renderStateMachine();
  } catch (error) {
    stopStateMachineRunPolling();
    sm.realRun.active = false;
    addLog("状态机", `运行状态查询失败：${error.message}`);
    renderStateMachine();
  }
}

async function startStateMachineRealRun(options = {}) {
  const sm = state.stateMachine;
  if (sm.realRun.active) return;
  const snapshot = stateMachineSnapshot();
  const loop = options.loop === true;
  try {
    const payload = await stateMachineApiPost("run/start", { name: snapshot.name, nodes: snapshot.nodes, loop });
    applyStateMachineBackendRun(payload.run || { active: true, status: "running", currentId: "sm_start", path: ["sm_start"], loop });
    addLog("状态机", `${loop ? "循环运行" : "运行"}已启动：${snapshot.name}`);
    stopStateMachineRunPolling();
    sm.realRun.pollTimer = window.setInterval(pollStateMachineRunStatus, 1000);
    pollStateMachineRunStatus();
    renderStateMachine();
  } catch (error) {
    addLog("状态机", `运行启动失败：${error.message}`);
  }
}

async function stopStateMachineRealRun() {
  try {
    await stateMachineApiPost("run/stop");
    addLog("状态机", "已请求停止运行");
    pollStateMachineRunStatus();
  } catch (error) {
    addLog("状态机", `停止运行失败：${error.message}`);
  }
}

async function copyStateMachineJson() {
  const payload = JSON.stringify(stateMachineSnapshot(), null, 2);
  try {
    await navigator.clipboard.writeText(payload);
    addLog("状态机", "状态机 JSON 已复制");
  } catch (error) {
    addLog("状态机", `JSON 复制失败：${error.message}`);
  }
}

function clearStateMachine() {
  state.stateMachine.nodes = [createStateMachineSystemNode("start"), createStateMachineSystemNode("end")];
  state.stateMachine.selectedId = "sm_start";
  state.stateMachine.connectingFromId = "";
  resetStateMachineRun();
  addLog("状态机", "任务 state 已清空，保留 Start / End");
  saveStateMachineDraft();
  renderStateMachine();
}

function stateMachineCanvasPointFromEvent(event) {
  const rect = stateMachineWorkspaceRect();
  if (!rect) return stateMachineDefaultTaskPosition();
  return clampStateMachineNodePosition({
    x: event.clientX - rect.left - stateMachineNodeSize.width / 2,
    y: event.clientY - rect.top - stateMachineNodeSize.height / 2,
  });
}

function openStateMachineNodeEditor(nodeId) {
  const node = stateMachineNodeById(nodeId);
  if (!node || node.type !== "task") return;
  if (!stateMachineTaskEditable(node.taskType)) return;
  state.stateMachine.selectedId = node.id;
  openStateMachineModal({
    mode: "edit-node",
    taskType: node.taskType,
    nodeId: node.id,
    title: node.title,
    params: cloneStateMachineValue(node.params || {}),
  });
}

function handleStateMachineCanvasClick(event) {
  const detailCloseButton = event.target.closest("[data-sm-task-detail-close]");
  if (detailCloseButton) {
    closeStateMachineTaskStatusPanel();
    return;
  }

  const detailButton = event.target.closest("[data-sm-task-detail]");
  if (detailButton) {
    openStateMachineTaskStatusPanel(detailButton.dataset.smTaskDetail);
    return;
  }

  const edgeDelete = event.target.closest("[data-sm-edge-from]");
  if (edgeDelete) {
    disconnectStateMachineNodes(edgeDelete.dataset.smEdgeFrom, edgeDelete.dataset.smEdgeTo);
    return;
  }

  const connectButton = event.target.closest("[data-sm-connect-from]");
  if (connectButton) {
    const source = stateMachineNodeById(connectButton.dataset.smConnectFrom);
    if (source && source.type !== "end") {
      state.stateMachine.connectingFromId = state.stateMachine.connectingFromId === source.id ? "" : source.id;
      state.stateMachine.selectedId = source.id;
      renderStateMachine();
    }
    return;
  }

  const editButton = event.target.closest("[data-sm-edit]");
  if (editButton) {
    openStateMachineNodeEditor(editButton.dataset.smEdit);
    return;
  }
  const duplicateButton = event.target.closest("[data-sm-duplicate]");
  if (duplicateButton) {
    duplicateStateMachineNode(duplicateButton.dataset.smDuplicate);
    return;
  }
  const deleteButton = event.target.closest("[data-sm-delete]");
  if (deleteButton) {
    deleteStateMachineNode(deleteButton.dataset.smDelete);
    return;
  }
  const selectButton = event.target.closest("[data-sm-select]");
  if (selectButton) {
    const targetId = selectButton.dataset.smSelect;
    if (state.stateMachine.connectingFromId && state.stateMachine.connectingFromId !== targetId) {
      connectStateMachineNodes(state.stateMachine.connectingFromId, targetId);
      return;
    }
    // Skip the re-render when the node is already selected so the second
    // click of a double-click still lands on the same DOM element.
    if (state.stateMachine.selectedId !== targetId) {
      state.stateMachine.selectedId = targetId;
      renderStateMachine();
    }
  }
}

function handleStateMachineCanvasDoubleClick(event) {
  const selectButton = event.target.closest("[data-sm-select]");
  if (!selectButton) return;
  openStateMachineNodeEditor(selectButton.dataset.smSelect);
}

function handleStateMachineLibraryClick(event) {
  const addButton = event.target.closest("[data-sm-add-type]");
  if (addButton) {
    const taskType = addButton.dataset.smAddType;
    openStateMachineModal({
      mode: "create-library",
      taskType,
      title: "",
      params: cloneStateMachineValue(stateMachineTaskTypeDefaults[taskType] || {}),
    });
    return;
  }
  const editButton = event.target.closest("[data-sm-library-edit]");
  if (editButton) {
    openStateMachineLibraryEditor(editButton.dataset.smLibraryEdit);
    return;
  }
  const removeButton = event.target.closest("[data-sm-library-remove]");
  if (removeButton) {
    deleteStateMachineLibraryEntry(removeButton.dataset.smLibraryRemove);
    return;
  }
  const entryButton = event.target.closest("[data-sm-library-id]");
  if (!entryButton) return;
  addStateMachineTaskNode(entryButton.dataset.smLibraryId);
}

function handleStateMachineLibraryDragStart(event) {
  const button = event.target.closest("[data-sm-library-id]");
  if (!button || !event.dataTransfer) return;
  event.dataTransfer.effectAllowed = "copy";
  event.dataTransfer.setData("application/x-robot-state-library", button.dataset.smLibraryId);
  event.dataTransfer.setData("text/plain", button.dataset.smLibraryId);
}

function handleStateMachineEventLibraryClick(event) {
  const button = event.target.closest("[data-sm-event-graph-id]");
  if (!button) return;
  addGraphToEventSequence(button.dataset.smEventGraphId);
}

function handleStateMachineEventLibraryDragStart(event) {
  const button = event.target.closest("[data-sm-event-graph-id]");
  if (!button || !event.dataTransfer) return;
  event.dataTransfer.effectAllowed = "copy";
  event.dataTransfer.setData("application/x-robot-event-graph", button.dataset.smEventGraphId);
  event.dataTransfer.setData("text/plain", button.dataset.smEventGraphId);
}

function eventSequenceDropIndex(event) {
  const sequenceState = state.stateMachine.eventSequence;
  const row = event.target.closest("[data-sm-event-id]");
  if (!row) return sequenceState.events.length;
  const index = sequenceState.events.findIndex((item) => item.id === row.dataset.smEventId);
  return index >= 0 ? index : sequenceState.events.length;
}

function handleEventSequenceListClick(event) {
  const selectButton = event.target.closest("[data-sm-event-select]");
  if (selectButton) {
    selectEventSequenceEvent(selectButton.dataset.smEventSelect);
    return;
  }
  const moveButton = event.target.closest("[data-sm-event-move]");
  if (moveButton) {
    moveEventSequenceEvent(moveButton.dataset.smEventMove, Number(moveButton.dataset.smEventDir) || 0);
    return;
  }
  const toggleButton = event.target.closest("[data-sm-event-toggle]");
  if (toggleButton) {
    toggleEventSequenceEvent(toggleButton.dataset.smEventToggle);
    return;
  }
  const duplicateButton = event.target.closest("[data-sm-event-duplicate]");
  if (duplicateButton) {
    duplicateEventSequenceEvent(duplicateButton.dataset.smEventDuplicate);
    return;
  }
  const removeButton = event.target.closest("[data-sm-event-remove]");
  if (removeButton) {
    removeEventSequenceEvent(removeButton.dataset.smEventRemove);
  }
}

function handleEventSequenceListDragStart(event) {
  const row = event.target.closest("[data-sm-event-id]");
  if (!row || !event.dataTransfer) return;
  event.dataTransfer.effectAllowed = "move";
  event.dataTransfer.setData("application/x-robot-event-sequence-id", row.dataset.smEventId);
  state.stateMachine.eventSequence.draggingId = row.dataset.smEventId;
}

function handleEventSequenceListDragOver(event) {
  if (
    event.dataTransfer?.types?.includes("application/x-robot-event-graph") ||
    event.dataTransfer?.types?.includes("application/x-robot-event-sequence-id")
  ) {
    event.preventDefault();
    event.dataTransfer.dropEffect = event.dataTransfer.types.includes("application/x-robot-event-graph") ? "copy" : "move";
  }
}

function handleEventSequenceListDrop(event) {
  const graphId = event.dataTransfer?.getData("application/x-robot-event-graph") || "";
  const eventId = event.dataTransfer?.getData("application/x-robot-event-sequence-id") || "";
  if (!graphId && !eventId) return;
  event.preventDefault();
  const insertIndex = eventSequenceDropIndex(event);
  const sequenceState = state.stateMachine.eventSequence;
  if (graphId) {
    addGraphToEventSequence(graphId, insertIndex);
    return;
  }
  const from = sequenceState.events.findIndex((item) => item.id === eventId);
  if (from < 0) return;
  const [moved] = sequenceState.events.splice(from, 1);
  const to = from < insertIndex ? insertIndex - 1 : insertIndex;
  sequenceState.events.splice(clamp(to, 0, sequenceState.events.length), 0, moved);
  sequenceState.selectedId = moved.id;
  sequenceState.draggingId = "";
  mutateEventSequence();
}

function handleEventSequenceDetailClick(event) {
  const openButton = event.target.closest("[data-sm-event-open-graph]");
  if (openButton) {
    openEventGraphInEditor(openButton.dataset.smEventOpenGraph);
    return;
  }
  const copyButton = event.target.closest("[data-sm-event-add-copy]");
  if (copyButton) {
    addGraphToEventSequence(copyButton.dataset.smEventAddCopy);
  }
}

function handleStateMachineCanvasDrop(event) {
  const libraryId =
    event.dataTransfer?.getData("application/x-robot-state-library") ||
    event.dataTransfer?.getData("text/plain") ||
    "";
  if (!libraryId) return;
  event.preventDefault();
  addStateMachineTaskNode(libraryId, stateMachineCanvasPointFromEvent(event));
}

function handleStateMachineCanvasDragOver(event) {
  if (!event.dataTransfer?.types?.includes("application/x-robot-state-library") && !event.dataTransfer?.types?.includes("text/plain")) return;
  event.preventDefault();
  event.dataTransfer.dropEffect = "copy";
}

function stateMachineWorkspaceRect() {
  // Measure the workspace element itself: its rect already moves with the
  // canvas scroll position, so pointer math stays correct no matter how or
  // when the canvas scrolls (scrollbars, scroll anchoring, re-renders).
  return $("#stateMachineCanvas")?.querySelector(".state-machine-workspace")?.getBoundingClientRect() || null;
}

function resizeStateMachineWorkspace(canvas) {
  const workspace = canvas?.querySelector(".state-machine-workspace");
  const workspaceSize = stateMachineWorkspaceSize();
  if (workspace) {
    workspace.style.width = `${workspaceSize.width}px`;
    workspace.style.height = `${workspaceSize.height}px`;
  }
  return workspaceSize;
}

function startStateMachineNodeDrag(event) {
  const handle = event.target.closest("[data-sm-drag-handle]");
  if (!handle || event.button !== 0) return;
  const node = stateMachineNodeById(handle.dataset.smDragHandle);
  if (!node) return;
  event.preventDefault();
  const rect = stateMachineWorkspaceRect();
  state.stateMachine.draggingNode = {
    id: node.id,
    offsetX: rect ? event.clientX - rect.left - node.x : 0,
    offsetY: rect ? event.clientY - rect.top - node.y : 0,
  };
  if (state.stateMachine.selectedId !== node.id) {
    state.stateMachine.selectedId = node.id;
    renderStateMachine();
  }
}

function updateStateMachineNodeDrag(event) {
  const drag = state.stateMachine.draggingNode;
  if (!drag) return;
  const rect = stateMachineWorkspaceRect();
  const node = stateMachineNodeById(drag.id);
  if (!rect || !node) return;
  const next = clampStateMachineNodePosition({
    x: event.clientX - rect.left - drag.offsetX,
    y: event.clientY - rect.top - drag.offsetY,
  });
  node.x = next.x;
  node.y = next.y;
  // Move the card in place and redraw only the edge layer; rebuilding the
  // whole canvas mid-drag would reset the scroll position and break dragging.
  const canvas = $("#stateMachineCanvas");
  const card = canvas?.querySelector(`[data-sm-node-id="${node.id}"]`);
  if (card) {
    card.style.left = `${next.x}px`;
    card.style.top = `${next.y}px`;
  }
  const workspaceSize = resizeStateMachineWorkspace(canvas);
  const edgeLayer = canvas?.querySelector(".state-machine-edge-layer");
  if (edgeLayer) edgeLayer.outerHTML = renderStateMachineEdges(workspaceSize);
}

function finishStateMachineNodeDrag() {
  if (!state.stateMachine.draggingNode) return;
  state.stateMachine.draggingNode = null;
  saveStateMachineDraft();
  renderStateMachine();
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

function summarizeSelfCheckResults(items) {
  const hardBlockerNames = new Set(["ROS2 daemon", "CAN 接口", "磁盘空间"]);
  const blockers = items.filter((item) => hardBlockerNames.has(item.name) && item.status === "错误");
  const warnings = items.filter((item) => item.status !== "正常" && !blockers.includes(item) && item.status !== "未检测");
  if (blockers.length) {
    return {
      state: "blocked",
      level: "danger",
      label: "存在阻塞",
      nextAction: blockers[0].advice || "请处理阻塞项后重新执行自检。",
      blockers,
      warnings,
    };
  }
  if (warnings.length) {
    return {
      state: "warn",
      level: "warn",
      label: "可继续，有警告",
      nextAction: warnings[0].advice || "存在非阻塞警告，请按任务需要确认。",
      blockers: [],
      warnings,
    };
  }
  if (items.every((item) => item.status === "未检测")) {
    return {
      state: "idle",
      level: "idle",
      label: "未自检",
      nextAction: "请执行一键检查。",
      blockers: [],
      warnings: [],
    };
  }
  return {
    state: "ready",
    level: "ok",
    label: "可继续",
    nextAction: "放行检查已通过，可以继续后续运行。",
    blockers: [],
    warnings: [],
  };
}

function renderSelfCheckOverview(items) {
  const summary = state.selfCheckSummary || summarizeSelfCheckResults(items);
  const checkedAt = state.selfCheckRanAt ? formatTime(state.selfCheckRanAt) : "--";
  const blockerCount = Array.isArray(summary.blockers) ? summary.blockers.length : 0;
  const warningCount = Array.isArray(summary.warnings) ? summary.warnings.length : 0;
  $("#selfCheckOverview").innerHTML = `
    <article class="self-gate-card ${escapeHtml(summary.level || "idle")}">
      <div>
        <span>放行状态</span>
        <strong>${escapeHtml(summary.label || "未自检")}</strong>
        <small>${state.selfCheckRanAt ? `最近检查 ${escapeHtml(checkedAt)}` : "后端重启后需要重新检查"}</small>
      </div>
      <p>${escapeHtml(summary.nextAction || "请执行一键检查。")}</p>
      <dl>
        <div><dt>阻塞</dt><dd>${blockerCount}</dd></div>
        <div><dt>警告</dt><dd>${warningCount}</dd></div>
      </dl>
    </article>
  `;
}

function renderSelfCheck(items = selfCheckItems) {
  state.selfCheckResults = cloneCheckItems(items);
  renderSelfCheckOverview(state.selfCheckResults);
  $("#selfCheckTable").innerHTML = items
    .map((item, index) => {
      const level = statusClass(item.status);
      const checkedAt = item.checkedAt || "--";
      const canActivate = item.name === "CAN 接口" && item.status !== "正常";
      return `
        <div
          class="check-row"
          data-check-index="${index}"
          data-tooltip-title="${escapeHtml(item.name)}"
          data-tooltip-code="${escapeHtml(item.code)}"
          data-tooltip-time="${escapeHtml(checkedAt)}"
          data-tooltip-detail="${escapeHtml(item.detail)}"
          data-tooltip-advice="${escapeHtml(item.advice)}"
        >
          <strong>${escapeHtml(item.name)}</strong>
          <span class="status-text ${level}">${escapeHtml(item.status)}</span>
          <span>${escapeHtml(item.advice)}</span>
          <div class="check-actions" aria-label="${item.name}操作">
            ${canActivate ? `<button data-check-action="activate" data-check-index="${index}">激活</button>` : ""}
            <button data-check-action="retry" data-check-index="${index}">复查</button>
          </div>
        </div>
      `;
    })
    .join("");
  renderRuntimePrep();
}

function runtimePrepState(item) {
  const runtimeStates = {
    piper: state.piperRuntime,
    piper_remote: state.piperRemoteRuntime,
    lifting: state.liftingRuntime,
    chassis: state.chassisRuntime,
    camera: state.cameraRuntime,
    lidar: state.lidarRuntime,
  };
  const status = runtimeStates[item.key]?.status || "unknown";
  const labelGetters = {
    piper: getPiperRuntimeLabel,
    piper_remote: getPiperRemoteRuntimeLabel,
    lifting: getLiftingRuntimeLabel,
    chassis: getChassisRuntimeLabel,
    camera: getCameraRuntimeLabel,
    lidar: getLidarRuntimeLabel,
  };
  const label = labelGetters[item.key]?.() || { title: "服务状态未知", level: "idle" };
  const textByStatus = {
    stopped: "未启动",
    starting: "启动中",
    running: "运行中",
    stopping: "停止中",
    external: "外部运行",
    failed: "启动失败",
    error: "异常",
    unknown: "未知",
  };
  return {
    ...item,
    status,
    text: textByStatus[status] || status,
    level: label.level || "idle",
    title: label.title || "服务状态未知",
    busy: Boolean(label.busy || state.runtimePrepBusy[item.key]),
    canStart: ["stopped", "failed", "error", "unknown"].includes(status),
  };
}

function renderRuntimePrep() {
  const table = $("#runtimePrepTable");
  if (!table) return;
  const entries = runtimePrepItems.map(runtimePrepState);
  const runningCount = entries.filter((item) => item.status === "running" || item.status === "external").length;
  const problemCount = entries.filter((item) => item.level === "danger").length;
  const badgeLevel = problemCount ? "warn" : runningCount ? "ok" : "idle";
  setStateBadge("#runtimePrepBadge", `${runningCount}/${entries.length} 运行`, badgeLevel);
  setText("#runtimePrepSummary", problemCount ? "存在服务异常，但不阻塞放行" : "服务按任务需要启动，未启动不阻塞放行");
  table.innerHTML = entries
    .map((item, index) => `
      <div
        class="check-row runtime-prep-row"
        data-runtime-index="${index}"
        data-tooltip-title="${escapeHtml(item.name)}"
        data-tooltip-code="SVC-${escapeHtml(item.key.toUpperCase())}"
        data-tooltip-time="${escapeHtml(formatTime())}"
        data-tooltip-detail="${escapeHtml(item.title)}"
        data-tooltip-advice="服务未启动不阻塞放行；需要该设备时可在此启动或前往对应页面。"
      >
        <strong>${escapeHtml(item.name)}</strong>
        <span class="status-text ${escapeHtml(item.level)}">${escapeHtml(item.text)}</span>
        <span>${escapeHtml(item.title)}</span>
        <div class="check-actions" aria-label="${escapeHtml(item.name)}操作">
          ${item.canStart ? `<button data-runtime-action="start" data-runtime-key="${escapeHtml(item.key)}" ${item.busy ? "disabled" : ""}>启动</button>` : ""}
          <button data-runtime-action="view" data-runtime-view="${escapeHtml(item.view)}">前往</button>
        </div>
      </div>
    `)
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
  setText("#alertStatus", `告警 ${state.alerts.length}`);
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

const INFERENCE_STATUS_LABELS = {
  disconnected: "未连接",
  connected: "已连接",
  requesting: "请求中",
  chunk_ready: "chunk 就绪",
  executing: "执行中",
  completed: "已完成",
  stopped: "已停止",
  error: "错误",
};
const INFERENCE_STATUS_LEVELS = {
  disconnected: "idle",
  connected: "ok",
  requesting: "warn",
  chunk_ready: "ok",
  executing: "warn",
  completed: "ok",
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
  if ("isSuccess" in result) info.isSuccess = result.isSuccess === true;
  renderInferenceStatus();
}

function renderInferenceStatus() {
  const info = state.inference;
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
  if (connectButton) connectButton.disabled = info.busy;
  const disconnectButton = $("#inferenceDisconnectButton");
  if (disconnectButton) disconnectButton.disabled = info.busy || !info.connected;
  const requestButton = $("#requestChunkButton");
  if (requestButton) requestButton.disabled = info.busy || !info.connected || info.looping;
  const executeButton = $("#executeChunkButton");
  if (executeButton) executeButton.disabled = info.busy || !info.chunkId || info.looping || !piperControlAvailable();
  const enableButton = $("#inferenceEnablePiperButton");
  if (enableButton) {
    enableButton.disabled = info.busy || state.piperEnableBusy || !piperControlAvailable();
    enableButton.textContent = state.piperEnableBusy ? "使能中" : "使能 Piper";
  }
  renderInferenceMetrics();
}

function renderPreflight() {
  const selfCheckFresh = Boolean(state.selfCheckRanAt);
  const idle = state.task === "idle";
  const runtimeReady = piperControlAvailable();
  const piperControlDetail = piperControlUnavailableDetail();
  $("#preflightList").innerHTML = [
    ["任务控制权", idle ? "正常" : "警告", idle ? "当前空闲。" : "已有任务占用机器人。"],
    ["Piper 控制", runtimeReady ? "正常" : "警告", runtimeReady ? "双臂控制节点运行中。" : `${piperControlDetail || "Piper 控制不可用"}。`],
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
  if (!piperFeedbackReady()) {
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
  setStateBadge("#armCompareBadge", piperFeedbackReady() ? "等待反馈" : "未启动", piperFeedbackReady() ? "warn" : "idle");
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
  const feedback = state.piperJoints[side];
  const status = armStatusText(side);
  const jointRows = armJointLimitsFor(side).map((limit, index) => renderJointCompareRow(side, limit, index)).join("");
  const stateTopic = feedback && feedback.topic ? feedback.topic : piperJointTopicNames[side];

  return `
    <section class="arm-inline-card" data-arm-panel="${side}">
      <div class="arm-inline-head">
        <div>
          <h3>${label}</h3>
          <p>
            <span class="status-text ${status.level}">${status.text}</span>
            <span>${status.detail}</span>
            <span>State ${stateTopic}</span>
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
    controlButton.disabled = state.armControl.busy || (!state.armControl.active && !piperControlAvailable());
    controlButton.classList.toggle("is-active", state.armControl.active);
  }
  const homeButton = $("#armHomeButton");
  if (homeButton) homeButton.disabled = state.armControl.busy || !piperControlAvailable();
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
  const unavailableDetail = piperControlUnavailableDetail();
  if (unavailableDetail) {
    if (logSuccess) addLog("机械臂", `${source}未启动：${unavailableDetail}`);
    renderArmComparisons();
    return null;
  }
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
    fetchPiperRemoteRuntimeStatus({ silent: true });
    fetchLiftingRuntimeStatus({ silent: true });
    fetchChassisRuntimeStatus({ silent: true });
    fetchCameraRuntimeStatus({ silent: true });
    if (cameraPreviewEnabled()) fetchCameraFrames({ silent: true });
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
  const unavailableDetail = piperControlUnavailableDetail();
  if (!state.armControl.active && unavailableDetail) {
    addLog("机械臂", `接管控制未启动：${unavailableDetail}`);
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
      setStatusPill("#enableStatus", "已使能", "ok");
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
  const command = state.chassisControl.command || { linearX: 0, linearY: 0, angularZ: 0 };
  const system = state.chassisState.system || {};
  const odom = state.chassisState.odom || {};
  const feedbackLinear = nestedNumber(odom, ["twist", "twist", "linear", "x"]);
  const feedbackLateral = nestedNumber(odom, ["twist", "twist", "linear", "y"]);
  const feedbackAngular = nestedNumber(odom, ["twist", "twist", "angular", "z"]);
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
  const modeText = chassisMotionModeText(motionMode);
  setStatusText("#baseModeText", modeText, modeText === "--" ? "idle" : feedbackLevel);
  $$("[data-device-drive], [data-mapping-drive]").forEach((button) => {
    const action = button.dataset.deviceDrive || button.dataset.mappingDrive;
    button.disabled = !chassisReady() && action !== "stop";
  });
  renderChassisKeyboardControl();
  const speedRows = [
    { axis: "vx", unit: "m/s", command: Number(command.linearX) || 0, feedback: feedbackLinear, threshold: 0.03 },
    { axis: "vy", unit: "m/s", command: Number(command.linearY) || 0, feedback: feedbackLateral, threshold: 0.03 },
    { axis: "wz", unit: "rad/s", command: Number(command.angularZ) || 0, feedback: feedbackAngular, threshold: 0.05 },
  ];
  node.innerHTML = `
    <div class="base-speed-row base-speed-head" role="row">
      <span>轴</span>
      <span>指令</span>
      <span>反馈</span>
      <span>差值</span>
    </div>
    ${speedRows.map(renderBaseSpeedRow).join("")}
  `;
  renderBaseOdomReadout(odom);
  renderRobotViewStatus();
}

function formatBaseSpeedValue(value, digits = 2) {
  const number = Number(value);
  return Number.isFinite(number) ? number.toFixed(digits) : "--";
}

function formatBaseSpeedDelta(value, digits = 2) {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  return `${number > 0 ? "+" : ""}${number.toFixed(digits)}`;
}

function baseSpeedDeltaLevel(delta, threshold) {
  if (!Number.isFinite(delta)) return "idle";
  const magnitude = Math.abs(delta);
  if (magnitude >= threshold * 2) return "danger";
  if (magnitude >= threshold) return "warn";
  return "ok";
}

function renderBaseSpeedRow(row) {
  const feedback = row.feedback === null ? null : Number(row.feedback);
  const hasFeedback = Number.isFinite(feedback);
  const delta = hasFeedback ? feedback - row.command : NaN;
  const deltaLevel = baseSpeedDeltaLevel(delta, row.threshold);
  return `
    <div class="base-speed-row" role="row">
      <span class="base-speed-axis"><strong>${escapeHtml(row.axis)}</strong><small>${escapeHtml(row.unit)}</small></span>
      <span class="base-speed-value">${escapeHtml(formatBaseSpeedValue(row.command))}</span>
      <span class="base-speed-value">${escapeHtml(hasFeedback ? formatBaseSpeedValue(feedback) : "--")}</span>
      <span class="base-speed-value base-speed-delta" data-level="${escapeHtml(deltaLevel)}">${escapeHtml(formatBaseSpeedDelta(delta))}</span>
    </div>
  `;
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

function localizationPoseForRobotModel() {
  const localization = state.localization || {};
  const preview = state.mapping.mapPreview;
  if (!["localization", "navigation"].includes(state.robotWork.mode) || !localization.loadedMap || preview.source !== "localization") return null;
  const pose = localization.pose || {};
  const x = localizationNumber(pose.x);
  const y = localizationNumber(pose.y);
  const z = localizationNumber(pose.z) ?? 0;
  const yawDeg = normalizeInitialPoseYawDeg(pose.yawDeg);
  if (x === null || y === null || yawDeg === null) return null;
  return {
    x,
    y,
    z,
    yaw: (yawDeg * Math.PI) / 180,
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

function visibleMapPointCloudText() {
  const preview = state.mapping.mapPreview;
  if (preview.source === "localization" && preview.mapName) return `定位地图 ${preview.mapName}`;
  return "地图点云";
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
      title: `${visibleMapPointCloudText()}显示中，实时 LiDAR 叠加层已暂停`,
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
    overlay.error = `${visibleMapPointCloudText()}显示中`;
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
    overlay.error = `${visibleMapPointCloudText()}显示中`;
    if (overlay.points) overlay.points.visible = false;
    renderRobotLidarButton();
    addLog("模型", `${visibleMapPointCloudText()}显示中，实时 LiDAR 点云叠加已暂停`);
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
  overlay.error = `${visibleMapPointCloudText()}显示中`;
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
  return $("#robotViewStage");
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
    mappingPreview.points.visible = Boolean(mappingPreview.hasFrame);
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
    if (handleInitialPosePointerDown(event, surface)) return;
    if (handleNavigationGoalPointerDown(event, surface)) return;
    event.preventDefault();
    controls.dragging = true;
    controls.dragMode = viewerDragMode(event);
    controls.lastX = event.clientX;
    controls.lastY = event.clientY;
    surface.setPointerCapture(event.pointerId);
  });

  surface.addEventListener("pointermove", (event) => {
    if (handleInitialPosePointerMove(event, surface)) return;
    if (handleNavigationGoalPointerMove(event, surface)) return;
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
    if (handleInitialPosePointerRelease(event, surface)) return;
    if (handleNavigationGoalPointerRelease(event, surface)) return;
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

      const worldRoot = new THREE.Group();
      worldRoot.name = "robot_metric_world";
      scene.add(worldRoot);

      const grid = new THREE.GridHelper(12, 24, 0x64748b, 0x1e293b);
      grid.rotation.x = Math.PI / 2;
      worldRoot.add(grid);
      worldRoot.add(new THREE.AxesHelper(1.2));

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
      robot.displayRoot = worldRoot;
      robot.worldRoot = worldRoot;
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
      robot.resizeObserver.observe(container);
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

function robotMetricWorldRoot() {
  const robot = state.robotModel;
  return robot.worldRoot || robot.displayRoot || robot.scene;
}

function frameRobotModelInViewer(modelRoot) {
  const robot = state.robotModel;
  const THREE = robot.three;
  if (!THREE || !modelRoot || !robot.controls) return;

  modelRoot.scale.setScalar(1);
  if (!mappingPoseFromTransform() && !localizationPoseForRobotModel()) modelRoot.position.set(0, 0, 0);
  modelRoot.updateMatrixWorld(true);

  const box = new THREE.Box3().setFromObject(modelRoot);
  if (box.isEmpty()) return;
  const size = new THREE.Vector3();
  const center = new THREE.Vector3();
  box.getSize(size);
  box.getCenter(center);
  const diagonal = Math.max(size.length(), 1);
  robot.controls.target.copy(center);
  robot.controls.distance = clamp(diagonal * 1.45, 2.4, 24);
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

  robot.modelRoot.scale.setScalar(1);
  const localizationPose = localizationPoseForRobotModel();
  const mappingPose = mappingPoseFromTransform();
  if (localizationPose) {
    robot.modelRoot.position.set(localizationPose.x, localizationPose.y, Number.isFinite(localizationPose.z) ? localizationPose.z : 0);
    robot.modelRoot.rotation.z = localizationPose.yaw;
  } else if (mappingPose) {
    robot.modelRoot.position.set(mappingPose.x, mappingPose.y, Number.isFinite(mappingPose.z) ? mappingPose.z : 0);
    robot.modelRoot.rotation.z = mappingPose.yaw;
  } else {
    const yaw = yawFromOdom(state.chassisState.odom || {});
    robot.modelRoot.position.set(0, 0, 0);
    robot.modelRoot.rotation.z = yaw === null ? 0 : yaw;
  }
  robot.modelRoot.updateMatrixWorld(true);
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
      robotMetricWorldRoot()?.remove(state.robotModel.modelRoot);
    }
    robotMetricWorldRoot()?.add(root);
    state.robotModel.modelRoot = root;
    state.robotModel.joints = joints;
    state.robotModel.colliders = colliders;
    state.robotModel.metadata = model;
    state.robotModel.loadedKey = key;
    state.robotModel.hasModel = true;
    if (state.robotModel.poseSyncEnabled || mappingFinalTransform() || localizationPoseForRobotModel()) updateRobotModelTransforms();
    frameRobotModelInViewer(root);
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
  renderRobotFooterStatus();
}

function localizationStatusLabel(value = state.localization.converged) {
  if (value === true) return "已收敛";
  if (value === false) return "未收敛";
  return "待接入";
}

function cleanLocalizationBackend(value, fallback = "cpu") {
  const text = String(value || fallback).trim().toLowerCase();
  return text === "gpu" ? "gpu" : "cpu";
}

function localizationBackendLabel(value = state.localization.activeBackend || state.localization.backend) {
  return cleanLocalizationBackend(value) === "gpu" ? "GPU / CUDA" : "CPU / PCL";
}

function localizationNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : null;
}

function formatLocalizationNumber(value, digits = 2, suffix = "") {
  const parsed = localizationNumber(value);
  return parsed === null ? "--" : `${parsed.toFixed(digits)}${suffix}`;
}

function normalizeInitialPoseYawDeg(value) {
  const parsed = localizationNumber(value);
  if (parsed === null) return null;
  const normalized = ((((parsed + 180) % 360) + 360) % 360) - 180;
  return Object.is(normalized, -0) ? 0 : normalized;
}

function initialPoseMapReady() {
  const preview = state.mapping.mapPreview;
  return Boolean(
    state.robotWork.mode === "localization" &&
      state.localization.loadedMap &&
      preview.hasFrame &&
      preview.source === "localization",
  );
}

function initialPoseValues() {
  const pose = state.localization.initialPose || {};
  const x = localizationNumber(pose.x);
  const y = localizationNumber(pose.y);
  const yawDeg = normalizeInitialPoseYawDeg(pose.yawDeg);
  if (x === null || y === null || yawDeg === null) return null;
  return {
    x,
    y,
    z: 0,
    yawDeg,
  };
}

function initialPoseCanPublish() {
  return Boolean(initialPoseMapReady() && initialPoseValues() && !state.localization.initialPosePublishing);
}

function resetInitialPoseDrag() {
  state.localization.initialPoseDrag = {
    active: false,
    pointerId: null,
  };
}

function setInitialPoseEditMode(enabled) {
  const active = Boolean(enabled && initialPoseMapReady());
  state.localization.initialPoseEditMode = active;
  if (!active) resetInitialPoseDrag();
  renderInitialPoseControls();
}

function initialPoseStatusText() {
  const localization = state.localization;
  if (!localization.loadedMap) return "待加载地图";
  if (localization.initialPosePublishing) return "发布中";
  if (localization.initialPoseEditMode) return "设定中";
  if (localization.initialPoseLastPublishedAt) return `已发布 ${localization.initialPoseLastPublishedAt}`;
  return "初值待发布";
}

function localizationMapByName(name = state.localization.selectedMap) {
  const maps = Array.isArray(state.localization.maps) ? state.localization.maps : [];
  return maps.find((item) => item && item.name === name) || null;
}

function localizationMapRevision(map = localizationMapByName()) {
  if (!map?.name) return "";
  return [map.name, map.sizeBytes || "", map.mtimeMs || "", map.savedAt || "", map.updatedAt || ""].join(":");
}

function localizationMapMetaText(map) {
  if (!map) return "--";
  const keyframeCount = Number(map.keyframeCount);
  const parts = [
    formatBytes(map.sizeBytes),
    Number.isFinite(keyframeCount) && keyframeCount > 0 ? `${keyframeCount} keyframes` : "",
    map.savedAt || map.updatedAt || "",
  ].filter(Boolean);
  return parts.join(" / ") || map.mapPath || map.path || "--";
}

function localizationMapTitleText(map) {
  if (!map?.name) return "";
  const detail = localizationMapMetaText(map);
  return detail && detail !== "--" ? `${map.name} - ${detail}` : map.name;
}

function localizationWorkSummaryText() {
  const localization = state.localization;
  const maps = Array.isArray(localization.maps) ? localization.maps : [];
  if (localization.mapsLoading) return "正在读取地图列表";
  if (localization.mapLoadBusy) return "正在加载定位地图";
  if (localization.lastError) return localization.lastError;
  if (localization.loadedMap) return `已加载 ${localization.loadedMap}`;
  if (localization.selectedMap) return `已选择 ${localization.selectedMap}`;
  if (maps.length) return `${maps.length} 张可用地图`;
  return "暂无可用定位地图";
}

function localizationBadgeMeta() {
  const localization = state.localization;
  const maps = Array.isArray(localization.maps) ? localization.maps : [];
  if (localization.running && localization.status === "error") return { text: "定位异常", level: "danger" };
  if (localization.running && localization.status === "recovering") return { text: "恢复确认", level: "warn" };
  if (localization.running && localization.status === "lost") return { text: "定位恢复中", level: "warn" };
  if (localization.running && localization.status === "degraded") return { text: "定位退化", level: "warn" };
  if (localization.running && localization.status === "waiting_initial_pose") return { text: "待初值", level: "warn" };
  if (localization.running) return { text: "定位中", level: "ok" };
  if (localization.mapsLoading || localization.mapLoadBusy) return { text: "加载中", level: "warn" };
  if (localization.lastError) return { text: "异常", level: "danger" };
  if (localization.loadedMap) return { text: "地图已加载", level: "ok" };
  if (localization.selectedMap) return { text: "待加载", level: "idle" };
  return { text: maps.length ? "待选择" : "无地图", level: "idle" };
}

function localizationStatusText(stateValue = state.localization.status) {
  const mapping = {
    stopped: "未启动",
    idle: "未启动",
    starting: "启动中",
    waiting_initial_pose: "等待初值",
    localizing: "定位中",
    degraded: "定位退化",
    recovering: "恢复确认",
    lost: "定位恢复中",
    error: "定位异常",
    failed: "进程异常",
  };
  return mapping[stateValue] || stateValue || "--";
}

function yawFromPoseData(poseData) {
  const x = nestedNumber(poseData, ["pose", "orientation", "x"]);
  const y = nestedNumber(poseData, ["pose", "orientation", "y"]);
  const z = nestedNumber(poseData, ["pose", "orientation", "z"]);
  const w = nestedNumber(poseData, ["pose", "orientation", "w"]);
  if ([x, y, z, w].some((value) => value === null)) return null;
  return Math.atan2(2 * (w * z + x * y), 1 - 2 * (y * y + z * z));
}

function poseFromLocalizationResponse(result = {}) {
  const statusPose = result.localizationStatus?.data?.pose;
  const poseFromStatus = {
    x: localizationNumber(statusPose?.x),
    y: localizationNumber(statusPose?.y),
    z: localizationNumber(statusPose?.z) ?? 0,
    yawDeg: localizationNumber(statusPose?.yawDeg),
  };
  if (poseFromStatus.x !== null && poseFromStatus.y !== null && poseFromStatus.yawDeg !== null) {
    return poseFromStatus;
  }

  const poseData = result.pose?.data;
  const x = nestedNumber(poseData, ["pose", "position", "x"]);
  const y = nestedNumber(poseData, ["pose", "position", "y"]);
  const z = nestedNumber(poseData, ["pose", "position", "z"]) ?? 0;
  const yaw = yawFromPoseData(poseData);
  if (x === null || y === null || yaw === null) return null;
  return { x, y, z, yawDeg: radToDeg(yaw) };
}

function localizationCanStart() {
  const localization = state.localization;
  const preview = state.mapping.mapPreview;
  return Boolean(
    !localization.running &&
      localization.loadedMap &&
      localization.selectedMap === localization.loadedMap &&
      preview.hasFrame &&
      preview.source === "localization",
  );
}

function applyLocalizationStatus(result = {}) {
  const localization = state.localization;
  const process = result.process || {};
  const statusData = result.localizationStatus?.data || null;
  const map = result.map || {};
  const settings = map.settings || {};
  localization.statusPayload = result;
  localization.statusUpdatedAt = Date.now();
  localization.running = Boolean(result.running || process.running);
  localization.processStatus = process.status || (localization.running ? "running" : "stopped");
  localization.status = result.state || statusData?.state || localization.processStatus || "stopped";
  if (!localization.running && localization.status === "running") localization.status = "stopped";
  if (localization.running && map.name) {
    localization.loadedMap = map.name;
  }
  localization.availableBackends = Array.isArray(result.availableBackends) ? result.availableBackends : localization.availableBackends;
  const responseBackend = result.backend || statusData?.backend || settings.backend;
  if (responseBackend) {
    localization.activeBackend = cleanLocalizationBackend(responseBackend, localization.activeBackend);
    if (localization.running) localization.backend = localization.activeBackend;
  }

  const pose = poseFromLocalizationResponse(result);
  if (pose) {
    localization.pose = pose;
    updateRobotModelTransforms();
  }
  localization.fitness = localizationNumber(statusData?.fitness);
  localization.ndtFitness = localizationNumber(statusData?.ndtFitness);
  localization.frequencyHz = localizationNumber(statusData?.frequencyHz);
  localization.converged = typeof statusData?.converged === "boolean" ? statusData.converged : localization.converged;
  localization.failedFrameCount = Number.isFinite(Number(statusData?.failedFrameCount)) ? Number(statusData.failedFrameCount) : 0;
  if (!localization.running) {
    localization.frequencyHz = null;
    localization.converged = null;
    localization.failedFrameCount = 0;
  }
  localization.lastError =
    statusData?.lastError ||
    process.lastError ||
    (result.ok === false ? result.detail || result.code || "定位状态异常" : "");

  renderLocalizationStatus();
  if (state.robotWork.mode === "navigation") {
    refreshNavigationPlanFreshness();
    renderNavigationStatus();
  }
  if (state.robotWork.mode === "localization") renderRobotWorkMode();
  scheduleLocalizationStatusPoll();
}

async function refreshLocalizationStatus(options = {}) {
  const localization = state.localization;
  if (localization.statusLoading) return null;
  localization.statusLoading = true;
  try {
    const response = await fetch("/api/localization/status", { cache: "no-store" });
    const result = await response.json();
    localization.statusLoading = false;
    applyLocalizationStatus(result);
    return result;
  } catch (error) {
    localization.statusLoading = false;
    if (!options.silent) addLog("定位", `状态刷新失败：${error.message}`);
    return null;
  }
}

function scheduleLocalizationStatusPoll(delayMs = null) {
  const localization = state.localization;
  window.clearTimeout(localization.statusTimer);
  const shouldPoll = state.robotWork.mode === "localization" || state.robotWork.mode === "navigation" || localization.running;
  if (!shouldPoll) {
    localization.statusTimer = null;
    return;
  }
  const delay = delayMs ?? (localization.running ? 700 : 1600);
  localization.statusTimer = window.setTimeout(() => refreshLocalizationStatus({ silent: true }), delay);
}

async function localizationPost(action, payload = {}) {
  const response = await fetch(`/api/localization/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
  const result = await response.json().catch(() => ({}));
  applyLocalizationStatus(result);
  if (!response.ok || result.ok === false) {
    throw new Error(result.detail || result.code || `HTTP ${response.status}`);
  }
  return result;
}

async function startLocalization() {
  const localization = state.localization;
  if (!localizationCanStart()) return;
  localization.lastError = "";
  localization.status = "starting";
  localization.running = true;
  localization.activeBackend = cleanLocalizationBackend(localization.backend);
  renderLocalizationStatus();
  try {
    const result = await localizationPost("start", {
      mapName: localization.loadedMap,
      backend: localization.activeBackend,
    });
    addLog(
      "定位",
      result.ok
        ? `定位节点已启动：${localization.loadedMap} / ${localizationBackendLabel(result.backend || localization.activeBackend)}`
        : `定位启动失败：${result.detail || result.code}`,
    );
  } catch (error) {
    localization.running = false;
    localization.status = "error";
    localization.lastError = `定位启动失败：${error.message}`;
    addLog("定位", localization.lastError);
    renderLocalizationStatus();
  } finally {
    scheduleLocalizationStatusPoll(500);
  }
}

async function stopLocalization() {
  if (!state.localization.running) return;
  try {
    const result = await localizationPost("stop", {});
    addLog("定位", result.ok ? "定位节点已停止" : `定位停止失败：${result.detail || result.code}`);
  } catch (error) {
    state.localization.lastError = `定位停止失败：${error.message}`;
    addLog("定位", state.localization.lastError);
  } finally {
    await refreshLocalizationStatus({ silent: true });
  }
}

async function restartLocalization() {
  if (!state.localization.running) return;
  try {
    const result = await localizationPost("restart", {});
    addLog("定位", result.ok ? "定位节点已重启" : `定位重启失败：${result.detail || result.code}`);
  } catch (error) {
    state.localization.lastError = `定位重启失败：${error.message}`;
    addLog("定位", state.localization.lastError);
  } finally {
    scheduleLocalizationStatusPoll(500);
  }
}

function renderLocalizationMapControls() {
  const localization = state.localization;
  const maps = Array.isArray(localization.maps) ? localization.maps : [];
  const selected = localizationMapByName();

  setText("#localizationMapSummary", localizationWorkSummaryText());

  const select = $("#localizationMapSelect");
  if (select) {
    const selectedName = selected ? selected.name : "";
    select.disabled = localization.running || localization.mapsLoading || maps.length === 0;
    select.innerHTML = maps.length
      ? maps
          .map((map) => {
            const title = localizationMapTitleText(map);
            return `<option value="${escapeHtml(map.name)}" title="${escapeHtml(title)}">${escapeHtml(map.name)}</option>`;
          })
          .join("")
      : `<option value="">${localization.mapsLoading ? "正在读取地图列表" : "暂无可用地图"}</option>`;
    select.value = selectedName;
    select.title = selected ? localizationMapTitleText(selected) : "";
  }

  const loadButton = $("#localizationLoadMapButton");
  if (loadButton) {
    loadButton.disabled = localization.running || localization.mapsLoading || localization.mapLoadBusy || !selected;
    loadButton.textContent = localization.mapLoadBusy ? "加载中" : localization.loadedMap === selected?.name ? "重新加载" : "加载地图";
  }

  const backendSelect = $("#localizationBackendSelect");
  if (backendSelect) {
    backendSelect.disabled = localization.running || localization.status === "starting";
    backendSelect.value = cleanLocalizationBackend(localization.running ? localization.activeBackend : localization.backend);
    backendSelect.title = localizationBackendLabel(backendSelect.value);
  }

  const startButton = $("#localizationStartButton");
  if (startButton) {
    startButton.disabled = !localizationCanStart() || localization.statusLoading;
    startButton.textContent = localization.status === "starting" ? "启动中" : "开始定位";
  }

  const stopButton = $("#localizationStopButton");
  if (stopButton) {
    stopButton.disabled = !localization.running;
    stopButton.textContent = localization.running ? "停止定位" : "未启动";
  }

  const restartButton = $("#localizationRestartButton");
  if (restartButton) {
    restartButton.disabled = !localization.running || localization.status === "starting";
    restartButton.textContent = "重启定位";
  }

  const info = $("#localizationMapInfo");
  if (info) {
    const titleNode = info.querySelector("strong");
    const detailNode = info.querySelector("span");
    let title = "暂无可用地图";
    let detail = "modules/map/data 下没有包含 map.pcd 的地图包";
    let infoLevel = "empty";
    if (localization.mapsLoading) {
      title = "正在读取地图列表";
      detail = "来源：modules/map/data，tmp 已过滤";
      infoLevel = "loading";
    } else if (localization.lastError && !maps.length) {
      title = "地图列表异常";
      detail = localization.lastError;
      infoLevel = "error";
    } else if (selected) {
      title = selected.name;
      detail = localizationMapMetaText(selected);
      infoLevel = localization.loadedMap === selected.name ? "loaded" : "selected";
    } else if (maps.length) {
      title = "请选择地图";
      detail = `${maps.length} 张可用地图`;
      infoLevel = "available";
    }
    info.dataset.level = infoLevel;
    info.title = selected ? localizationMapTitleText(selected) : detail;
    if (titleNode) titleNode.textContent = title;
    if (detailNode) detailNode.textContent = detail;
  }
}

function selectLocalizationMap(name) {
  const localization = state.localization;
  if (localization.running) return;
  const nextName = String(name || "");
  if (localization.selectedMap === nextName) return;
  localization.selectedMap = nextName;
  localization.lastError = "";
  localization.status = nextName ? "selected" : "idle";
  resetNavigationForMapChange();
  if (state.mapping.mapPreview.source === "localization") clearMappingMapPreview();
  renderLocalizationStatus();
  if (state.robotWork.mode === "localization" || state.robotWork.mode === "navigation") renderRobotWorkMode();
}

function selectLocalizationBackend(value) {
  const localization = state.localization;
  if (localization.running) return;
  localization.backend = cleanLocalizationBackend(value);
  localization.activeBackend = localization.backend;
  localization.lastError = "";
  renderLocalizationStatus();
  if (state.robotWork.mode === "localization" || state.robotWork.mode === "navigation") renderRobotWorkMode();
}

function robotOdomPoseText() {
  const odom = state.chassisState.odom || {};
  const x = nestedNumber(odom, ["pose", "pose", "position", "x"]);
  const y = nestedNumber(odom, ["pose", "pose", "position", "y"]);
  const yaw = yawFromOdom(odom);
  if (x === null || y === null || yaw === null) return "--";
  return `${x.toFixed(2)}, ${y.toFixed(2)}, ${radToDeg(yaw).toFixed(1)} deg`;
}

function robotFooterFrequencyText(value = state.lidarCloud.frameRate) {
  const parsed = localizationNumber(value);
  return parsed === null ? "--" : `${parsed.toFixed(1)} Hz`;
}

function mappingMapStateText() {
  const mapping = state.mapping;
  const preview = mapping.mapPreview;
  const session = mapping.session;
  if (preview.activeRequest) return "加载中";
  if (preview.error) return "异常";
  if (preview.hasFrame) return `${Math.max(0, Math.round(preview.pointCount || 0)).toLocaleString("zh-CN")} 点`;
  if (session?.tmpMapPath) return "待加载";
  return "--";
}

function renderRobotFooterRows(rows) {
  const strip = $("#mappingMetrics");
  if (!strip) return;
  strip.innerHTML = rows
    .map(([name, value]) => `<div class="metric-card"><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
    .join("");
}

function renderRobotFooterStatus() {
  if (state.robotWork.mode === "navigation") {
    const navigation = state.navigation;
    const target = navigationTargetValues();
    const start = navigationStartPose();
    const pathState = navigation.plan?.stale
      ? "需重新规划"
      : navigation.plan?.status === "planned"
        ? formatNavigationDistance(navigation.plan.distanceM)
        : "--";
    renderRobotFooterRows([
      ["地图", state.localization.loadedMap || state.localization.selectedMap || "--"],
      ["当前位姿", navigationPoseText(start)],
      ["目标", navigationPoseText(target)],
      ["路径", pathState],
      ["状态", navigationStatusText()],
    ]);
    return;
  }

  if (state.robotWork.mode === "localization") {
    const localization = state.localization;
    const pose = localization.pose || {};
    const poseX = localizationNumber(pose.x);
    const poseY = localizationNumber(pose.y);
    const poseYaw = localizationNumber(pose.yawDeg);
    const poseText =
      poseX !== null && poseY !== null && poseYaw !== null
        ? `${poseX.toFixed(2)}, ${poseY.toFixed(2)}, ${poseYaw.toFixed(1)} deg`
        : "--";
    const statusText = localization.mapLoadBusy
      ? "加载地图"
      : localization.running
        ? localizationStatusText(localization.status)
        : localization.loadedMap
          ? "地图已加载"
          : localizationStatusLabel(localization.converged);
    renderRobotFooterRows([
      ["地图", localization.loadedMap || localization.selectedMap || "--"],
      ["位姿", poseText],
      ["Fitness", formatLocalizationNumber(localization.fitness, 5)],
      ["频率", robotFooterFrequencyText(localization.frequencyHz)],
      ["状态", statusText],
    ]);
    return;
  }

  const mapping = state.mapping;
  const session = mapping.session;
  const statusKey = session?.status || mapping.status || "idle";
  const meta = mappingStatusMeta[statusKey] || mappingStatusMeta.idle;
  const progress = session?.progress || null;
  const progressMeta = mappingProgressMeta[progress?.phase] || null;
  const busy = Boolean(mapping.busy || session?.busy);
  const registration = session?.lastResult?.registration || {};
  renderRobotFooterRows([
    ["地图", mappingMapStateText()],
    ["位姿", robotOdomPoseText()],
    ["Fitness", Number.isFinite(Number(registration.fitness)) ? Number(registration.fitness).toFixed(5) : "--"],
    ["频率", robotFooterFrequencyText()],
    ["状态", busy ? progress?.label || progressMeta?.label || "采集中" : meta.label],
  ]);
}

function robotModalAllowed(modalKey) {
  const meta = robotWorkModalMeta[modalKey];
  if (!meta) return false;
  return !meta.mode || meta.mode === state.robotWork.mode;
}

function renderRobotModal() {
  const active = state.robotWork.modal && robotModalAllowed(state.robotWork.modal) ? state.robotWork.modal : null;
  state.robotWork.modal = active;
  const modal = $("#robotWorkModal");
  const isOpen = Boolean(active);
  if (modal) modal.hidden = !isOpen;
  document.body.classList.toggle("robot-modal-open", isOpen);
  $("#robotViewStage")?.classList.toggle("is-modal-open", isOpen);

  $$("[data-robot-modal-toggle]").forEach((button) => {
    const buttonActive = button.dataset.robotModalToggle === active;
    button.classList.toggle("is-active", buttonActive);
    button.setAttribute("aria-expanded", buttonActive ? "true" : "false");
  });
  $$("[data-robot-modal-panel]").forEach((panel) => {
    panel.hidden = panel.dataset.robotModalPanel !== active;
  });

  if (!active) return;
  const meta = robotWorkModalMeta[active];
  setText("#robotWorkModalKicker", meta.kicker);
  setText("#robotWorkModalTitle", meta.title);
}

function closeRobotModal() {
  if (!state.robotWork.modal) return;
  state.robotWork.modal = null;
  renderRobotModal();
}

function toggleRobotModal(modalKey) {
  if (!robotModalAllowed(modalKey)) return;
  state.robotWork.modal = state.robotWork.modal === modalKey ? null : modalKey;
  renderRobotModal();
}

function ensureInitialPoseMarker() {
  const robot = state.robotModel;
  const marker = state.localization.initialPoseMarker;
  if (!robot.three || !robot.scene) return false;
  const THREE = robot.three;

  if (!marker.group) {
    marker.group = new THREE.Group();
    marker.group.name = "localization_initial_pose_marker";

    const ringMaterial = new THREE.MeshBasicMaterial({
      color: 0x2563eb,
      transparent: true,
      opacity: 0.92,
      depthTest: false,
    });
    marker.ring = new THREE.Mesh(new THREE.TorusGeometry(0.22, 0.012, 8, 36), ringMaterial);
    marker.ring.renderOrder = 9;
    marker.group.add(marker.ring);

    marker.arrow = new THREE.ArrowHelper(
      new THREE.Vector3(1, 0, 0),
      new THREE.Vector3(0, 0, 0.04),
      0.9,
      0x2563eb,
      0.22,
      0.14,
    );
    marker.arrow.renderOrder = 10;
    marker.arrow.line.renderOrder = 10;
    marker.arrow.cone.renderOrder = 10;
    marker.group.add(marker.arrow);
  }

  if (marker.group.parent !== robot.scene) {
    robot.scene.add(marker.group);
  }
  return true;
}

function renderInitialPoseMarker() {
  const marker = state.localization.initialPoseMarker;
  const pose = initialPoseValues();
  const visible = Boolean(state.localization.initialPoseEditMode && initialPoseMapReady() && pose && ensureInitialPoseMarker());
  if (!marker.group) return;
  marker.group.visible = visible;
  if (!visible) return;

  const yawRad = (pose.yawDeg * Math.PI) / 180;
  marker.group.position.set(pose.x, pose.y, 0.08);
  marker.arrow.setDirection(new state.robotModel.three.Vector3(Math.cos(yawRad), Math.sin(yawRad), 0).normalize());
  marker.arrow.setLength(0.9, 0.22, 0.14);
}

function initialPosePointFromPointer(event, surface) {
  const robot = state.robotModel;
  if (!robot.three || !robot.camera || !surface) return null;
  const rect = surface.getBoundingClientRect();
  const width = Math.max(rect.width, 1);
  const height = Math.max(rect.height, 1);
  const pointer = new robot.three.Vector2(
    ((event.clientX - rect.left) / width) * 2 - 1,
    -((event.clientY - rect.top) / height) * 2 + 1,
  );
  const raycaster = new robot.three.Raycaster();
  const plane = new robot.three.Plane(new robot.three.Vector3(0, 0, 1), 0);
  const point = new robot.three.Vector3();
  robot.camera.updateMatrixWorld();
  raycaster.setFromCamera(pointer, robot.camera);
  return raycaster.ray.intersectPlane(plane, point) ? point : null;
}

function setInitialPosePositionFromPoint(point) {
  if (!point) return;
  const pose = state.localization.initialPose;
  pose.x = point.x;
  pose.y = point.y;
  pose.z = 0;
  if (normalizeInitialPoseYawDeg(pose.yawDeg) === null) pose.yawDeg = 0;
  state.localization.lastError = "";
}

function setInitialPoseYawFromPoint(point) {
  if (!point) return;
  const pose = state.localization.initialPose;
  const x = localizationNumber(pose.x);
  const y = localizationNumber(pose.y);
  if (x === null || y === null) return;
  const dx = point.x - x;
  const dy = point.y - y;
  if (Math.hypot(dx, dy) < 0.02) return;
  pose.yawDeg = normalizeInitialPoseYawDeg((Math.atan2(dy, dx) * 180) / Math.PI);
}

function handleInitialPosePointerDown(event, surface) {
  if (!state.localization.initialPoseEditMode || !initialPoseMapReady() || event.button !== 0) return false;
  event.preventDefault();
  const point = initialPosePointFromPointer(event, surface);
  if (!point) return true;
  setInitialPosePositionFromPoint(point);
  state.localization.initialPoseDrag = {
    active: true,
    pointerId: event.pointerId,
  };
  surface.setPointerCapture(event.pointerId);
  renderLocalizationStatus();
  return true;
}

function handleInitialPosePointerMove(event, surface) {
  const drag = state.localization.initialPoseDrag;
  if (!drag.active || drag.pointerId !== event.pointerId) return false;
  event.preventDefault();
  setInitialPoseYawFromPoint(initialPosePointFromPointer(event, surface));
  renderInitialPoseControls();
  renderRobotFooterStatus();
  return true;
}

function handleInitialPosePointerRelease(event, surface) {
  const drag = state.localization.initialPoseDrag;
  if (!drag.active || drag.pointerId !== event.pointerId) return false;
  event.preventDefault();
  setInitialPoseYawFromPoint(initialPosePointFromPointer(event, surface));
  resetInitialPoseDrag();
  if (surface.hasPointerCapture(event.pointerId)) {
    surface.releasePointerCapture(event.pointerId);
  }
  renderLocalizationStatus();
  return true;
}

function renderInitialPoseControls() {
  const pose = state.localization.initialPose || {};
  if (!initialPoseMapReady() && state.localization.initialPoseEditMode) {
    state.localization.initialPoseEditMode = false;
    resetInitialPoseDrag();
  }
  [
    ["#initialPoseXInput", pose.x, 2],
    ["#initialPoseYInput", pose.y, 2],
    ["#initialPoseYawInput", normalizeInitialPoseYawDeg(pose.yawDeg), 1],
  ].forEach(([selector, value, digits]) => {
    const input = $(selector);
    if (!input || document.activeElement === input) return;
    const parsed = localizationNumber(value);
    input.value = parsed === null ? "" : parsed.toFixed(digits);
  });
  setText("#initialPoseZText", `XY 平面 / Z=${formatLocalizationNumber(pose.z ?? 0, 0)}`);

  const yaw = localizationNumber(pose.yawDeg);
  const arrow = $(".initial-pose-arrow");
  if (arrow) {
    arrow.style.transform = `translate(-50%, -50%) rotate(${yaw === null ? 0 : yaw}deg)`;
    arrow.classList.toggle("is-disabled", yaw === null);
  }

  const editButton = $("#initialPoseEditButton");
  const mapReady = initialPoseMapReady();
  if (editButton) {
    editButton.disabled = !mapReady || state.localization.initialPosePublishing;
    editButton.classList.toggle("is-active", state.localization.initialPoseEditMode);
    editButton.setAttribute("aria-pressed", state.localization.initialPoseEditMode ? "true" : "false");
    editButton.textContent = state.localization.initialPoseEditMode ? "设定中" : "设定初值";
  }

  const publishButton = $("#initialPosePublishButton");
  if (publishButton) {
    publishButton.disabled = !initialPoseCanPublish();
    publishButton.textContent = state.localization.initialPosePublishing ? "发布中" : "发布初值";
  }

  const stageLabel = $(".initial-pose-stage-label");
  if (stageLabel) stageLabel.textContent = initialPoseStatusText();
  $("#robotViewStage")?.classList.toggle("is-initial-pose-editing", Boolean(state.localization.initialPoseEditMode && mapReady));
  renderInitialPoseMarker();
}

function updateInitialPoseFromInputs() {
  const pose = state.localization.initialPose;
  [
    ["#initialPoseXInput", "x"],
    ["#initialPoseYInput", "y"],
    ["#initialPoseYawInput", "yawDeg"],
  ].forEach(([selector, key]) => {
    const input = $(selector);
    if (!input) return;
    pose[key] = key === "yawDeg" ? normalizeInitialPoseYawDeg(input.value) : localizationNumber(input.value);
  });
  pose.z = 0;
  renderInitialPoseControls();
  renderLocalizationStatus();
}

function navigationMapReady() {
  const preview = state.mapping.mapPreview;
  return Boolean(
    state.robotWork.mode === "navigation" &&
      state.localization.loadedMap &&
      preview.hasFrame &&
      preview.source === "localization",
  );
}

function navigationTargetValues() {
  const pose = state.navigation.targetPose || {};
  const x = localizationNumber(pose.x);
  const y = localizationNumber(pose.y);
  const yawDeg = normalizeInitialPoseYawDeg(pose.yawDeg);
  if (x === null || y === null || yawDeg === null) return null;
  return {
    x,
    y,
    z: 0,
    yawDeg,
  };
}

function navigationBackendTargetValues(target) {
  if (!target || typeof target !== "object") return null;
  const x = localizationNumber(target.x);
  const y = localizationNumber(target.y);
  const yawDeg = normalizeInitialPoseYawDeg(target.yawDeg);
  if (x === null || y === null || yawDeg === null) return null;
  return {
    x,
    y,
    z: localizationNumber(target.z) ?? 0,
    yawDeg,
  };
}

function navigationStartPose() {
  const localization = state.localization;
  const pose = localization.pose || {};
  const x = localizationNumber(pose.x);
  const y = localizationNumber(pose.y);
  const yawDeg = normalizeInitialPoseYawDeg(pose.yawDeg);
  if (!localization.running || x === null || y === null || yawDeg === null) return null;
  return {
    x,
    y,
    z: localizationNumber(pose.z) ?? 0,
    yawDeg,
  };
}

function navigationPoseText(pose, emptyText = "--") {
  if (!pose) return emptyText;
  const x = localizationNumber(pose.x);
  const y = localizationNumber(pose.y);
  const yawDeg = normalizeInitialPoseYawDeg(pose.yawDeg);
  if (x === null || y === null || yawDeg === null) return emptyText;
  return `${x.toFixed(2)}, ${y.toFixed(2)}, ${yawDeg.toFixed(1)} deg`;
}

function navigationPoseSignature(pose) {
  if (!pose) return "";
  const x = localizationNumber(pose.x);
  const y = localizationNumber(pose.y);
  const yawDeg = normalizeInitialPoseYawDeg(pose.yawDeg);
  if (x === null || y === null || yawDeg === null) return "";
  return `${x.toFixed(3)}:${y.toFixed(3)}:${yawDeg.toFixed(1)}`;
}

function navigationPoseDriftMeters(a, b) {
  if (!a || !b) return Infinity;
  const ax = localizationNumber(a.x);
  const ay = localizationNumber(a.y);
  const bx = localizationNumber(b.x);
  const by = localizationNumber(b.y);
  if ([ax, ay, bx, by].some((value) => value === null)) return Infinity;
  return Math.hypot(ax - bx, ay - by);
}

function navigationYawDriftDeg(a, b) {
  const ayaw = normalizeInitialPoseYawDeg(a?.yawDeg);
  const byaw = normalizeInitialPoseYawDeg(b?.yawDeg);
  if (ayaw === null || byaw === null) return Infinity;
  return Math.abs(normalizeInitialPoseYawDeg(ayaw - byaw));
}

function navigationCanEditGoal() {
  return Boolean(navigationMapReady() && !state.navigation.running);
}

function navigationCanPlan() {
  return Boolean(
    navigationMapReady() &&
      navigationTargetValues() &&
      navigationStartPose() &&
      !state.navigation.running,
  );
}

function navigationPlanIsFresh() {
  const navigation = state.navigation;
  const plan = navigation.plan || {};
  if (plan.status !== "planned" || plan.stale) return false;
  if (navigationPoseSignature(navigationTargetValues()) !== plan.targetSignature) return false;
  const start = navigationStartPose();
  if (!start || !plan.startPose) return false;
  return navigationPoseDriftMeters(start, plan.startPose) <= 0.15 && navigationYawDriftDeg(start, plan.startPose) <= 8;
}

function navigationCanStart() {
  return Boolean(
    navigationMapReady() &&
      navigationTargetValues() &&
      state.localization.running &&
      !state.navigation.running &&
      !state.navigation.statusLoading,
  );
}

function resetNavigationGoalDrag() {
  state.navigation.goalDrag = {
    active: false,
    pointerId: null,
  };
}

function stopNavigationRunTimer() {
  window.clearInterval(state.navigation.runTimer);
  state.navigation.runTimer = null;
}

function resetNavigationPlan() {
  stopNavigationRunTimer();
  Object.assign(state.navigation, {
    status: navigationTargetValues() ? "goal-set" : "idle",
    running: false,
    paused: false,
    progress: 0,
    remainingDistanceM: null,
    currentSpeedMps: 0,
    startedAt: null,
    completedAt: null,
    canceledAt: null,
    lastError: "",
  });
  state.navigation.plan = {
    status: "empty",
    points: [],
    distanceM: null,
    etaSec: null,
    plannedAt: null,
    startPose: null,
    targetSignature: "",
    stale: false,
    staleReason: "",
    planner: "straight-line-preview",
    cost: null,
  };
}

function markNavigationPlanStale(reason = "起点或终点已变化") {
  const navigation = state.navigation;
  if (!navigation.plan?.points?.length || navigation.running || navigation.paused) return;
  navigation.plan.stale = true;
  navigation.plan.staleReason = reason;
  if (!["completed", "canceled", "failed"].includes(navigation.status)) {
    navigation.status = "stale";
  }
}

function refreshNavigationPlanFreshness() {
  const navigation = state.navigation;
  if (!navigation.plan?.points?.length || navigation.running || navigation.paused || ["completed", "canceled", "failed"].includes(navigation.status)) {
    return;
  }
  if (navigation.plan.status === "planned" && !navigationPlanIsFresh()) {
    markNavigationPlanStale("当前定位位姿或目标已变化");
  }
}

function resetNavigationForMapChange() {
  stopNavigationRunTimer();
  state.navigation.goalEditMode = false;
  state.navigation.localTargetDirty = true;
  resetNavigationGoalDrag();
  state.navigation.targetPose = { x: null, y: null, z: 0, yawDeg: null };
  resetNavigationPlan();
  renderNavigationGoalMarker();
  renderNavigationPathLayer();
}

function clearNavigationTarget() {
  if (state.navigation.running) return;
  state.navigation.goalEditMode = false;
  state.navigation.localTargetDirty = true;
  resetNavigationGoalDrag();
  state.navigation.targetPose = { x: null, y: null, z: 0, yawDeg: null };
  resetNavigationPlan();
  addLog("导航", "导航目标已清除");
  renderNavigationStatus();
}

function setNavigationGoalEditMode(enabled) {
  const active = Boolean(enabled && navigationCanEditGoal());
  state.navigation.goalEditMode = active;
  if (!active) resetNavigationGoalDrag();
  renderNavigationStatus();
}

function navigationTargetChanged(reason = "目标已变化") {
  const navigation = state.navigation;
  navigation.localTargetDirty = true;
  navigation.completedAt = null;
  navigation.canceledAt = null;
  navigation.lastError = "";
  if (navigation.plan?.points?.length) {
    markNavigationPlanStale(reason);
    if (!navigation.running && !navigation.paused) navigation.status = "stale";
  } else if (!navigation.running && !navigation.paused) {
    navigation.status = navigationTargetValues() ? "goal-set" : "idle";
  }
}

function navigationGoalStatusText() {
  const navigation = state.navigation;
  if (!state.localization.loadedMap) return "待加载地图";
  if (!navigationMapReady()) return "地图未显示";
  if (navigation.goalEditMode) return "设定中";
  if (navigationTargetValues()) return "目标已设置";
  return "目标待设置";
}

function navigationStatusText(value = state.navigation.status) {
  const mapping = {
    idle: "待设置目标",
    "goal-set": "目标已设置",
    planned: "路径已规划",
    stale: "需重新规划",
    running: "导航中",
    paused: "已暂停",
    completed: "已完成",
    canceled: "已取消",
    stopped: "已停止",
    failed: "失败",
  };
  return mapping[value] || value || "--";
}

function navigationPhaseText(value = state.navigation.phase) {
  const mapping = {
    idle: "空闲",
    lateral_translate: "横向平移",
    forward_translate: "前后平移",
    omni_translate: "全向平移",
    rotate: "旋转对齐",
    waiting_localization: "等待定位",
    completed: "已完成",
    stopped: "已停止",
    failed: "失败",
  };
  return mapping[value] || value || "--";
}

function navigationBadgeMeta() {
  const navigation = state.navigation;
  if (navigation.running && navigation.phase === "waiting_localization") return { text: "等定位", level: "warn" };
  if (navigation.status === "running") return { text: "导航中", level: "ok" };
  if (navigation.status === "paused") return { text: "已暂停", level: "warn" };
  if (navigation.status === "completed") return { text: "已完成", level: "ok" };
  if (navigation.status === "failed") return { text: "失败", level: "danger" };
  if (navigation.status === "stopped") return { text: "已停止", level: "warn" };
  if (navigation.status === "canceled" || navigation.status === "stale" || navigation.plan?.stale) {
    return { text: "需规划", level: "warn" };
  }
  if (navigation.plan?.status === "planned") return { text: "已规划", level: "ok" };
  if (navigationTargetValues()) return { text: "待规划", level: "idle" };
  if (state.localization.loadedMap) return { text: "待目标", level: "idle" };
  return { text: "待地图", level: "idle" };
}

function navigationWorkSummaryText() {
  const navigation = state.navigation;
  if (!state.localization.loadedMap) return "请先在定位作业加载地图";
  if (!navigationMapReady()) return "定位地图未显示";
  if (!navigationTargetValues()) return "设置终止 pose";
  if (navigation.running && navigation.phase === "waiting_localization") {
    return navigation.lastLocalizationError ? `等待定位：${navigation.lastLocalizationError}` : "等待定位恢复";
  }
  if (!navigationStartPose()) return "等待当前定位位姿";
  if (navigation.plan?.stale) return navigation.plan.staleReason || "路径需重新规划";
  if (navigation.status === "completed" && navigation.completedAt) return `导航完成：${navigation.completedAt}`;
  if (navigation.status === "canceled" && navigation.canceledAt) return `导航已取消：${navigation.canceledAt}`;
  return navigationStatusText();
}

function formatNavigationDistance(value) {
  const parsed = localizationNumber(value);
  if (parsed === null) return "--";
  return parsed >= 1000 ? `${(parsed / 1000).toFixed(2)} km` : `${parsed.toFixed(2)} m`;
}

function formatNavigationDuration(value) {
  const parsed = localizationNumber(value);
  if (parsed === null) return "--";
  if (parsed < 60) return `${Math.max(0, Math.round(parsed))} s`;
  const minutes = Math.floor(parsed / 60);
  const seconds = Math.round(parsed % 60);
  return `${minutes} min ${seconds} s`;
}

function navigationModeLabel(value = state.navigation.params?.mode) {
  return value === "omni" ? "全向" : "横向";
}

function navigationInputNumber(selector, fallback) {
  const input = $(selector);
  const parsed = localizationNumber(input?.value);
  return parsed === null ? fallback : parsed;
}

function readNavigationParams() {
  const current = state.navigation.params || {};
  const mode = $("#navigationModeSelect")?.value === "omni" ? "omni" : "lateral";
  return {
    mode,
    maxLinearMps: navigationInputNumber("#navigationMaxLinearInput", current.maxLinearMps ?? 0.2),
    maxLateralMps: navigationInputNumber("#navigationMaxLateralInput", current.maxLateralMps ?? 0.15),
    maxAngularRadS: navigationInputNumber("#navigationMaxAngularInput", current.maxAngularRadS ?? 0.5),
    positionToleranceM: navigationInputNumber("#navigationPositionToleranceInput", current.positionToleranceM ?? 0.05),
    yawToleranceDeg: navigationInputNumber("#navigationYawToleranceInput", current.yawToleranceDeg ?? 3),
    localizationStaleSec: navigationInputNumber("#navigationLocalizationStaleInput", current.localizationStaleSec ?? 0.8),
    controlRateHz: navigationInputNumber("#navigationControlRateInput", current.controlRateHz ?? 20),
  };
}

function updateNavigationParamsFromInputs() {
  if (state.navigation.running) {
    syncNavigationParamInputs();
    return;
  }
  state.navigation.params = {
    ...state.navigation.params,
    ...readNavigationParams(),
  };
  state.navigation.localParamsDirty = true;
  if (state.navigation.plan?.points?.length) {
    markNavigationPlanStale("导航参数已变化");
  }
  renderNavigationStatus();
}

function syncNavigationParamInputs() {
  const params = state.navigation.params || {};
  const fields = [
    ["#navigationModeSelect", params.mode || "lateral", null],
    ["#navigationMaxLinearInput", params.maxLinearMps, 2],
    ["#navigationMaxLateralInput", params.maxLateralMps, 2],
    ["#navigationMaxAngularInput", params.maxAngularRadS, 2],
    ["#navigationPositionToleranceInput", params.positionToleranceM, 2],
    ["#navigationYawToleranceInput", params.yawToleranceDeg, 0],
    ["#navigationLocalizationStaleInput", params.localizationStaleSec, 1],
    ["#navigationControlRateInput", params.controlRateHz, 0],
  ];
  fields.forEach(([selector, value, digits]) => {
    const input = $(selector);
    if (!input || document.activeElement === input) return;
    if (selector === "#navigationModeSelect") {
      input.value = value === "omni" ? "omni" : "lateral";
      return;
    }
    const parsed = localizationNumber(value);
    if (parsed !== null) input.value = parsed.toFixed(digits);
  });
}

function navigationCommandText(command = state.navigation.command || {}) {
  const linearX = localizationNumber(command.linearX) ?? 0;
  const linearY = localizationNumber(command.linearY) ?? 0;
  const angularZ = localizationNumber(command.angularZ) ?? 0;
  return `${linearX.toFixed(2)} / ${linearY.toFixed(2)} / ${angularZ.toFixed(2)}`;
}

function applyNavigationBackendStatus(result = {}, options = {}) {
  const navigation = state.navigation;
  const backendRunning = Boolean(result.running);
  const fromAction = options.source === "action";
  const preserveLocalDraft = Boolean(
    !fromAction && !backendRunning && (navigation.localTargetDirty || navigation.localParamsDirty),
  );
  navigation.statusPayload = result;
  if (!preserveLocalDraft && typeof result.status === "string") navigation.status = result.status;
  if (!preserveLocalDraft && typeof result.phase === "string") navigation.phase = result.phase;
  navigation.running = backendRunning;
  navigation.paused = false;
  const backendTarget = navigationBackendTargetValues(result.target);
  if (
    backendTarget &&
    (backendRunning || fromAction || (!navigation.localTargetDirty && !navigationTargetValues())) &&
    !navigation.goalEditMode &&
    !navigation.goalDrag?.active
  ) {
    navigation.targetPose = backendTarget;
    navigation.localTargetDirty = false;
  }
  if (result.params && typeof result.params === "object" && (backendRunning || fromAction || !navigation.localParamsDirty)) {
    navigation.params = {
      ...navigation.params,
      ...result.params,
      mode: result.target?.mode || result.params.mode || navigation.params.mode,
    };
    navigation.localParamsDirty = false;
  }
  navigation.currentPose = result.currentPose || null;
  navigation.errors = result.errors || null;
  navigation.command = result.command || { linearX: 0, linearY: 0, angularZ: 0 };
  navigation.translationYawDeg = localizationNumber(result.translationYawDeg);
  navigation.remainingDistanceM = localizationNumber(result.errors?.distance);
  navigation.currentSpeedMps = Math.hypot(
    localizationNumber(result.command?.linearX) ?? 0,
    localizationNumber(result.command?.linearY) ?? 0,
  );
  navigation.startedAt = result.startedAt || navigation.startedAt;
  navigation.completedAt = result.completedAt || navigation.completedAt;
  navigation.stoppedAt = result.stoppedAt || navigation.stoppedAt;
  navigation.failedAt = result.failedAt || navigation.failedAt;
  navigation.localizationWaitStartedAt = result.localizationWaitStartedAt || null;
  navigation.lastLocalizationError = result.lastLocalizationError || "";
  navigation.lastError = result.lastError || (result.ok === false ? result.detail || result.code || "导航状态异常" : "");
  if (navigation.running && !navigation.plan?.points?.length && navigationStartPose() && navigationTargetValues()) {
    planNavigationPath({ quiet: true });
  }
  renderNavigationStatus();
  scheduleNavigationStatusPoll();
}

async function refreshNavigationStatus(options = {}) {
  const navigation = state.navigation;
  if (navigation.statusLoading) return null;
  navigation.statusLoading = true;
  try {
    const response = await fetch("/api/navigation/status", { cache: "no-store" });
    const result = await response.json();
    navigation.statusLoading = false;
    applyNavigationBackendStatus(result, { source: "poll" });
    return result;
  } catch (error) {
    navigation.statusLoading = false;
    if (!options.silent) addLog("导航", `状态刷新失败：${error.message}`);
    return null;
  }
}

function scheduleNavigationStatusPoll(delayMs = null) {
  const navigation = state.navigation;
  window.clearTimeout(navigation.statusTimer);
  const shouldPoll = state.robotWork.mode === "navigation" || navigation.running;
  if (!shouldPoll) {
    navigation.statusTimer = null;
    return;
  }
  const delay = delayMs ?? (navigation.running ? 500 : 1500);
  navigation.statusTimer = window.setTimeout(() => refreshNavigationStatus({ silent: true }), delay);
}

async function navigationPost(action, payload = {}) {
  const response = await fetch(`/api/navigation/${action}`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
    cache: "no-store",
  });
  const result = await response.json().catch(() => ({}));
  applyNavigationBackendStatus(result, { source: "action" });
  if (!response.ok || result.ok === false) {
    throw new Error(result.detail || result.code || `HTTP ${response.status}`);
  }
  return result;
}

function ensureNavigationGoalMarker() {
  const robot = state.robotModel;
  const marker = state.navigation.goalMarker;
  if (!robot.three || !robot.scene) return false;
  const THREE = robot.three;

  if (!marker.group) {
    marker.group = new THREE.Group();
    marker.group.name = "navigation_goal_marker";

    const ringMaterial = new THREE.MeshBasicMaterial({
      color: 0x059669,
      transparent: true,
      opacity: 0.94,
      depthTest: false,
    });
    marker.ring = new THREE.Mesh(new THREE.TorusGeometry(0.24, 0.014, 8, 36), ringMaterial);
    marker.ring.renderOrder = 11;
    marker.group.add(marker.ring);

    marker.arrow = new THREE.ArrowHelper(
      new THREE.Vector3(1, 0, 0),
      new THREE.Vector3(0, 0, 0.05),
      1.05,
      0x059669,
      0.26,
      0.16,
    );
    marker.arrow.renderOrder = 12;
    marker.arrow.line.renderOrder = 12;
    marker.arrow.cone.renderOrder = 12;
    marker.group.add(marker.arrow);
  }

  if (marker.group.parent !== robot.scene) {
    robot.scene.add(marker.group);
  }
  return true;
}

function renderNavigationGoalMarker() {
  const marker = state.navigation.goalMarker;
  const pose = navigationTargetValues();
  const visible = Boolean(state.robotWork.mode === "navigation" && navigationMapReady() && pose && ensureNavigationGoalMarker());
  if (!marker.group) return;
  marker.group.visible = visible;
  if (!visible) return;

  const yawRad = (pose.yawDeg * Math.PI) / 180;
  marker.group.position.set(pose.x, pose.y, 0.09);
  marker.arrow.setDirection(new state.robotModel.three.Vector3(Math.cos(yawRad), Math.sin(yawRad), 0).normalize());
  marker.arrow.setLength(1.05, 0.26, 0.16);
}

function ensureNavigationPathLayer() {
  const robot = state.robotModel;
  const layer = state.navigation.pathLayer;
  if (!robot.three || !robot.scene) return false;
  const THREE = robot.three;

  if (!layer.line) {
    layer.geometry = new THREE.BufferGeometry();
    layer.material = new THREE.LineBasicMaterial({
      color: 0x0f766e,
      transparent: true,
      opacity: 0.92,
      depthTest: false,
    });
    layer.line = new THREE.Line(layer.geometry, layer.material);
    layer.line.name = "navigation_preview_path";
    layer.line.renderOrder = 8;
  }

  if (layer.line.parent !== robot.scene) {
    robot.scene.add(layer.line);
  }
  return true;
}

function navigationPathColor() {
  const navigation = state.navigation;
  if (navigation.plan?.stale || ["canceled", "failed"].includes(navigation.status)) return 0x64748b;
  if (navigation.status === "running" || navigation.status === "paused") return 0x16a34a;
  if (navigation.status === "completed") return 0x2563eb;
  return 0x0f766e;
}

function renderNavigationPathLayer() {
  const layer = state.navigation.pathLayer;
  const points = Array.isArray(state.navigation.plan?.points) ? state.navigation.plan.points : [];
  const visible = Boolean(state.robotWork.mode === "navigation" && navigationMapReady() && points.length >= 2 && ensureNavigationPathLayer());
  if (!layer.line) return;
  layer.line.visible = visible;
  if (!visible) return;

  const THREE = state.robotModel.three;
  layer.geometry.setFromPoints(points.map((point) => new THREE.Vector3(point.x, point.y, point.z ?? 0.07)));
  layer.geometry.computeBoundingSphere();
  layer.material.color.setHex(navigationPathColor());
  layer.material.opacity = state.navigation.plan?.stale ? 0.48 : 0.92;
}

function navigationPointFromPointer(event, surface) {
  return initialPosePointFromPointer(event, surface);
}

function setNavigationTargetPositionFromPoint(point) {
  if (!point) return;
  const pose = state.navigation.targetPose;
  pose.x = point.x;
  pose.y = point.y;
  pose.z = 0;
  if (normalizeInitialPoseYawDeg(pose.yawDeg) === null) pose.yawDeg = 0;
  navigationTargetChanged("目标点已变化");
}

function setNavigationTargetYawFromPoint(point) {
  if (!point) return;
  const pose = state.navigation.targetPose;
  const x = localizationNumber(pose.x);
  const y = localizationNumber(pose.y);
  if (x === null || y === null) return;
  const dx = point.x - x;
  const dy = point.y - y;
  if (Math.hypot(dx, dy) < 0.02) return;
  pose.yawDeg = normalizeInitialPoseYawDeg((Math.atan2(dy, dx) * 180) / Math.PI);
  navigationTargetChanged("目标朝向已变化");
}

function handleNavigationGoalPointerDown(event, surface) {
  if (!state.navigation.goalEditMode || !navigationCanEditGoal() || event.button !== 0) return false;
  event.preventDefault();
  const point = navigationPointFromPointer(event, surface);
  if (!point) return true;
  setNavigationTargetPositionFromPoint(point);
  state.navigation.goalDrag = {
    active: true,
    pointerId: event.pointerId,
  };
  surface.setPointerCapture(event.pointerId);
  renderNavigationStatus();
  return true;
}

function handleNavigationGoalPointerMove(event, surface) {
  const drag = state.navigation.goalDrag;
  if (!drag.active || drag.pointerId !== event.pointerId) return false;
  event.preventDefault();
  setNavigationTargetYawFromPoint(navigationPointFromPointer(event, surface));
  renderNavigationStatus();
  return true;
}

function handleNavigationGoalPointerRelease(event, surface) {
  const drag = state.navigation.goalDrag;
  if (!drag.active || drag.pointerId !== event.pointerId) return false;
  event.preventDefault();
  setNavigationTargetYawFromPoint(navigationPointFromPointer(event, surface));
  resetNavigationGoalDrag();
  if (surface.hasPointerCapture(event.pointerId)) {
    surface.releasePointerCapture(event.pointerId);
  }
  renderNavigationStatus();
  return true;
}

function updateNavigationGoalFromInputs() {
  const pose = state.navigation.targetPose;
  [
    ["#navigationGoalXInput", "x"],
    ["#navigationGoalYInput", "y"],
    ["#navigationGoalYawInput", "yawDeg"],
  ].forEach(([selector, key]) => {
    const input = $(selector);
    if (!input) return;
    pose[key] = key === "yawDeg" ? normalizeInitialPoseYawDeg(input.value) : localizationNumber(input.value);
  });
  pose.z = 0;
  navigationTargetChanged("目标输入已变化");
  renderNavigationStatus();
}

function buildNavigationPreviewPath(start, target) {
  const dx = target.x - start.x;
  const dy = target.y - start.y;
  const distance = Math.hypot(dx, dy);
  const steps = Math.max(2, Math.min(24, Math.ceil(distance / 0.35) + 1));
  const points = Array.from({ length: steps }, (_, index) => {
    const t = steps <= 1 ? 1 : index / (steps - 1);
    return {
      x: start.x + dx * t,
      y: start.y + dy * t,
      z: 0.07,
    };
  });
  return {
    points,
    distance,
    etaSec: distance / 0.35,
  };
}

function planNavigationPath(options = {}) {
  if (!navigationCanPlan()) return;
  const start = navigationStartPose();
  const target = navigationTargetValues();
  const preview = buildNavigationPreviewPath(start, target);
  const navigation = state.navigation;
  navigation.plan = {
    status: "planned",
    points: preview.points,
    distanceM: preview.distance,
    etaSec: preview.etaSec,
    plannedAt: formatTime(),
    startPose: { ...start },
    targetSignature: navigationPoseSignature(target),
    stale: false,
    staleReason: "",
    planner: "straight-line-preview",
    cost: preview.distance,
  };
  Object.assign(navigation, {
    status: "planned",
    running: false,
    paused: false,
    progress: 0,
    remainingDistanceM: preview.distance,
    currentSpeedMps: 0,
    startedAt: null,
    completedAt: null,
    canceledAt: null,
    lastError: "",
  });
  if (!options.quiet) {
    addLog("导航", `路径预览已生成：${formatNavigationDistance(preview.distance)} / ${formatNavigationDuration(preview.etaSec)}`);
  }
  renderNavigationStatus();
}

async function startNavigation() {
  if (!navigationCanStart()) return;
  const navigation = state.navigation;
  const target = navigationTargetValues();
  const params = readNavigationParams();
  if (!navigation.plan?.points?.length || !navigationPlanIsFresh()) {
    planNavigationPath({ quiet: true });
  }
  navigation.status = "running";
  navigation.running = true;
  navigation.progress = 0;
  navigation.startedAt = formatTime();
  navigation.completedAt = null;
  navigation.stoppedAt = null;
  navigation.failedAt = null;
  navigation.lastError = "";
  renderNavigationStatus();
  try {
    const result = await navigationPost("start", {
      mode: params.mode,
      x: target.x,
      y: target.y,
      yawDeg: target.yawDeg,
      maxLinearMps: params.maxLinearMps,
      maxLateralMps: params.maxLateralMps,
      maxAngularRadS: params.maxAngularRadS,
      positionToleranceM: params.positionToleranceM,
      yawToleranceDeg: params.yawToleranceDeg,
      localizationStaleSec: params.localizationStaleSec,
      controlRateHz: params.controlRateHz,
    });
    addLog("导航", result.ok ? `导航已开始：${navigationModeLabel(params.mode)}` : `导航启动失败：${result.detail || result.code}`);
    scheduleNavigationStatusPoll(250);
  } catch (error) {
    navigation.status = "failed";
    navigation.running = false;
    navigation.lastError = `导航启动失败：${error.message}`;
    addLog("导航", navigation.lastError);
    renderNavigationStatus();
  }
}

function pauseNavigation() {
  addLog("导航", "第一版导航不支持暂停，请使用停止");
}

function resumeNavigation() {
  addLog("导航", "第一版导航不支持继续，请重新开始");
}

async function cancelNavigation() {
  const navigation = state.navigation;
  if (!navigation.running) return;
  try {
    const result = await navigationPost("stop", {});
    addLog("导航", result.ok ? "导航已停止" : `导航停止失败：${result.detail || result.code}`);
  } catch (error) {
    navigation.lastError = `导航停止失败：${error.message}`;
    addLog("导航", navigation.lastError);
    renderNavigationStatus();
  } finally {
    scheduleNavigationStatusPoll(300);
  }
}

function renderNavigationStatus() {
  const navigation = state.navigation;
  const target = navigationTargetValues();
  const start = navigationStartPose();
  const mapReady = navigationMapReady();
  refreshNavigationPlanFreshness();

  if (!mapReady && navigation.goalEditMode) {
    navigation.goalEditMode = false;
    resetNavigationGoalDrag();
  }
  syncNavigationParamInputs();

  if (state.robotWork.mode === "navigation") {
    const meta = navigationBadgeMeta();
    setText("#mappingSummary", navigationWorkSummaryText());
    setStateBadge("#mappingBadge", meta.text, meta.level);
  }

  setText(
    "#navigationContextSummary",
    mapReady ? "复用定位地图与当前位姿" : state.localization.loadedMap ? "定位地图未显示" : "等待定位地图",
  );
  const context = $("#navigationContextList");
  if (context) {
    context.innerHTML = [
      ["地图", state.localization.loadedMap || state.localization.selectedMap || "--"],
      ["当前位姿", navigationPoseText(start)],
      ["定位状态", state.localization.running ? localizationStatusText(state.localization.status) : "未启动"],
      ["目标", navigationPoseText(target)],
      ["导航模式", navigationModeLabel()],
    ]
      .map(([name, value]) => `<div><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");
  }

  [
    ["#navigationGoalXInput", target?.x, 2],
    ["#navigationGoalYInput", target?.y, 2],
    ["#navigationGoalYawInput", target?.yawDeg, 1],
  ].forEach(([selector, value, digits]) => {
    const input = $(selector);
    if (!input || document.activeElement === input) return;
    const parsed = localizationNumber(value);
    input.value = parsed === null ? "" : parsed.toFixed(digits);
  });

  setText("#navigationGoalZText", `XY 平面 / Z=${formatLocalizationNumber(state.navigation.targetPose?.z ?? 0, 0)}`);
  const arrow = $(".navigation-goal-arrow");
  if (arrow) {
    arrow.style.transform = `translate(-50%, -50%) rotate(${target ? target.yawDeg : 0}deg)`;
    arrow.classList.toggle("is-disabled", !target);
  }
  const stageLabel = $(".navigation-goal-stage-label");
  if (stageLabel) stageLabel.textContent = navigationGoalStatusText();

  const editButton = $("#navigationGoalEditButton");
  if (editButton) {
    editButton.disabled = !navigationCanEditGoal();
    editButton.classList.toggle("is-active", navigation.goalEditMode);
    editButton.setAttribute("aria-pressed", navigation.goalEditMode ? "true" : "false");
    editButton.textContent = navigation.goalEditMode ? "设定中" : "设定目标";
  }
  const clearButton = $("#navigationGoalClearButton");
  if (clearButton) {
    clearButton.disabled = !target || navigation.running;
  }

  const planStatusText = navigation.plan?.stale
    ? navigation.plan.staleReason || "需重新规划"
    : navigation.plan?.status === "planned"
      ? "路径预览已生成"
      : target
        ? "目标已设置"
        : "目标点待设置";
  const backendSummary =
    navigation.running || ["completed", "stopped", "failed"].includes(navigation.status)
      ? `${navigationPhaseText()} / ${navigationStatusText()}`
      : planStatusText;
  setText("#navigationPlanSummary", backendSummary);

  const metrics = $("#navigationMetrics");
  if (metrics) {
    const errors = navigation.errors || {};
    const metricRows =
      navigation.status === "running" || ["completed", "stopped", "failed"].includes(navigation.status)
        ? [
            ["阶段", navigationPhaseText()],
            ["距离误差", formatNavigationDistance(errors.distance)],
            ["车体系误差", `${formatLocalizationNumber(errors.bodyX, 2)} / ${formatLocalizationNumber(errors.bodyY, 2)} m`],
            ["Yaw 误差", formatLocalizationNumber(errors.yawDeg, 1, " deg")],
            ["当前命令", navigationCommandText()],
            ["模式", navigationModeLabel()],
          ]
        : [
            ["距离", formatNavigationDistance(navigation.plan?.distanceM)],
            ["预计耗时", formatNavigationDuration(navigation.plan?.etaSec)],
            ["预览状态", navigation.plan?.stale ? "需重新预览" : navigationStatusText()],
            ["目标 pose", navigationPoseText(target)],
            ["模式", navigationModeLabel()],
          ];
    metrics.innerHTML = metricRows
      .map(([name, value]) => `<div class="metric-card"><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");
  }

  const planButton = $("#navigationPlanButton");
  if (planButton) planButton.disabled = !navigationCanPlan();
  const startButton = $("#navigationStartButton");
  if (startButton) startButton.disabled = !navigationCanStart();
  const cancelButton = $("#navigationCancelButton");
  if (cancelButton) cancelButton.disabled = !navigation.running;

  const detailList = $("#navigationDetailList");
  if (detailList) {
    const errors = navigation.errors || {};
    const params = navigation.params || {};
    detailList.innerHTML = [
      ["地图", state.localization.loadedMap || state.localization.selectedMap || "--"],
      ["起点", navigationPoseText(navigation.plan?.startPose || start)],
      ["目标", navigationPoseText(target)],
      ["模式", navigationModeLabel(params.mode)],
      ["阶段", navigationPhaseText()],
      ["路径点数", String(navigation.plan?.points?.length || 0)],
      ["距离", formatNavigationDistance(navigation.plan?.distanceM)],
      ["预计耗时", formatNavigationDuration(navigation.plan?.etaSec)],
      ["当前位置", navigationPoseText(navigation.currentPose || start)],
      ["距离误差", formatNavigationDistance(errors.distance)],
      ["车体系误差", `${formatLocalizationNumber(errors.bodyX, 3)} / ${formatLocalizationNumber(errors.bodyY, 3)} m`],
      ["Yaw 误差", formatLocalizationNumber(errors.yawDeg, 2, " deg")],
      ["命令 vx/vy/wz", navigationCommandText()],
      ["平移参考 yaw", formatLocalizationNumber(navigation.translationYawDeg, 1, " deg")],
      ["限速", `${formatLocalizationNumber(params.maxLinearMps, 2)} / ${formatLocalizationNumber(params.maxLateralMps, 2)} / ${formatLocalizationNumber(params.maxAngularRadS, 2)}`],
      ["误差阈值", `${formatLocalizationNumber(params.positionToleranceM, 2)} m / ${formatLocalizationNumber(params.yawToleranceDeg, 1)} deg`],
      ["定位超时", formatLocalizationNumber(params.localizationStaleSec, 1, " s")],
      ["控制频率", formatLocalizationNumber(params.controlRateHz, 0, " Hz")],
      ["开始时间", navigation.startedAt || "--"],
      ["等待定位开始", navigation.localizationWaitStartedAt || "--"],
      ["定位等待错误", navigation.lastLocalizationError || "--"],
      ["完成时间", navigation.completedAt || "--"],
      ["停止时间", navigation.stoppedAt || "--"],
      ["失败时间", navigation.failedAt || "--"],
      ["错误", navigation.lastError || "--"],
    ]
      .map(([name, value]) => `<div><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");
  }

  $("#robotViewStage")?.classList.toggle("is-navigation-goal-editing", Boolean(navigation.goalEditMode && mapReady));
  renderNavigationGoalMarker();
  renderNavigationPathLayer();
  renderRobotFooterStatus();
}

function renderLocalizationStatus() {
  const localization = state.localization;
  const pose = localization.pose || {};
  const selectedMap = localizationMapByName();
  const poseX = localizationNumber(pose.x);
  const poseY = localizationNumber(pose.y);
  const poseYaw = localizationNumber(pose.yawDeg);
  const frequencyHz = localizationNumber(localization.frequencyHz);
  const poseText =
    poseX !== null && poseY !== null && poseYaw !== null
      ? `${poseX.toFixed(2)}, ${poseY.toFixed(2)}, ${poseYaw.toFixed(1)} deg`
      : "--";
  const fitnessText = formatLocalizationNumber(localization.fitness, 5);
  const ndtFitnessText = formatLocalizationNumber(localization.ndtFitness, 5);
  const frequencyText = frequencyHz === null ? "--" : `${frequencyHz.toFixed(1)} Hz`;
  const convergenceText = localizationStatusLabel(localization.converged);
  const backendText = localizationBackendLabel(localization.activeBackend || localization.backend);

  renderLocalizationMapControls();
  setText(
    "#localizationStatusSummary",
    localization.lastError || (localization.running ? localizationStatusText(localization.status) : "定位节点未启动"),
  );

  const statusMetrics = $("#localizationStatusMetrics");
  if (statusMetrics) {
    statusMetrics.innerHTML = [
      ["位姿 x / y / yaw", poseText],
      ["Fitness", fitnessText],
      ["频率", frequencyText],
      ["收敛", convergenceText],
      ["失败帧", String(localization.failedFrameCount || 0)],
    ]
      .map(([name, value]) => `<div class="metric-card"><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");
  }

  const detailList = $("#localizationDetailList");
  if (detailList) {
    const initialPose = localization.initialPose || {};
    detailList.innerHTML = [
      ["坐标系", "map / base_link"],
      ["地图", localization.loadedMap || localization.selectedMap || "--"],
      ["定位后端", backendText],
      ["地图包", selectedMap?.path || "--"],
      ["地图大小", selectedMap ? formatBytes(selectedMap.sizeBytes) : "--"],
      ["结果来源", localization.running ? "/localization/status" : "--"],
      ["更新时间", localization.statusUpdatedAt ? formatTime(new Date(localization.statusUpdatedAt)) : "--"],
      ["频率", frequencyText],
      ["收敛", convergenceText],
      ["状态", localizationStatusText(localization.status)],
      ["NDT fitness", ndtFitnessText],
      ["GICP fitness", fitnessText],
      ["连续失败", String(localization.failedFrameCount || 0)],
      ["Initial x", formatLocalizationNumber(initialPose.x, 2, " m")],
      ["Initial y", formatLocalizationNumber(initialPose.y, 2, " m")],
      ["Initial z", "0 m"],
      ["Initial yaw", formatLocalizationNumber(initialPose.yawDeg, 1, " deg")],
      ["Initial 发布", localization.initialPoseLastPublishedAt || "--"],
    ]
      .map(([name, value]) => `<div><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");
  }

  renderInitialPoseControls();
  renderRobotFooterStatus();
}

function renderRobotWorkMode() {
  const mode = ["mapping", "localization", "navigation"].includes(state.robotWork.mode) ? state.robotWork.mode : "mapping";
  const localizationMode = mode === "localization";
  const navigationMode = mode === "navigation";
  const modeLabel = navigationMode ? "导航" : localizationMode ? "定位" : "建图";
  document.body.dataset.robotWorkMode = mode;

  $$("#robotWorkModeTabs [data-robot-work-mode]").forEach((button) => {
    const active = button.dataset.robotWorkMode === mode;
    button.classList.toggle("is-active", active);
    button.setAttribute("aria-selected", active ? "true" : "false");
  });
  $$("[data-work-content]").forEach((node) => {
    const hidden = node.dataset.workContent !== mode;
    node.hidden = hidden;
    node.setAttribute("aria-hidden", hidden ? "true" : "false");
    node.toggleAttribute("inert", hidden);
    node.querySelectorAll(".robot-collapse, .robot-collapse > summary").forEach((child) => {
      child.hidden = hidden;
      child.setAttribute("aria-hidden", hidden ? "true" : "false");
      child.toggleAttribute("inert", hidden);
    });
  });

  setText("#robotWorkStatusText", `当前作业：${modeLabel}`);
  setText("#robotWorkTitle", `${modeLabel}作业`);

  if (localizationMode) {
    const meta = localizationBadgeMeta();
    setText("#mappingSummary", localizationWorkSummaryText());
    setStateBadge("#mappingBadge", meta.text, meta.level);
    renderLocalizationStatus();
  } else if (navigationMode) {
    renderNavigationStatus();
  }
  renderRobotModal();
}

function setRobotWorkMode(mode) {
  const nextMode = ["mapping", "localization", "navigation"].includes(mode) ? mode : "mapping";
  if ((state.navigation.running || state.navigation.paused) && nextMode !== "navigation") {
    addLog("导航", "导航运行中，取消或完成后再切换作业");
    renderRobotWorkMode();
    return;
  }
  const changed = state.robotWork.mode !== nextMode;
  if (nextMode !== "mapping" && state.chassisControl.keyboardListening) {
    stopChassisKeyboardControl(`切换到${nextMode === "navigation" ? "导航" : "定位"}作业，键盘监听停止`, { deactivate: true });
  }
  if (changed) state.robotWork.modal = null;
  state.robotWork.mode = nextMode;
  if (changed && nextMode === "mapping" && state.mapping.mapPreview.source === "localization") {
    clearMappingMapPreview();
  }
  if (changed && (nextMode === "localization" || nextMode === "navigation")) {
    if (state.mapping.mapPreview.source === "mapping") clearMappingMapPreview();
    refreshLocalizationMaps({ silent: true });
    refreshLocalizationStatus({ silent: true });
    if (nextMode === "navigation") refreshNavigationStatus({ silent: true });
  }
  if (nextMode === "mapping") {
    renderMappingStatus();
  } else {
    renderRobotWorkMode();
  }
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

  setStateBadge("#mappingBadge", busy ? busyLabel : meta.label, busy ? (progressMeta?.level || "warn") : meta.level);
  const rawSummary = session?.detail || mapping.lastError || "等待创建建图会话";
  const summaryNode = $("#mappingSummary");
  if (summaryNode) {
    const savedPackageName = String(session?.savedPackagePath || "")
      .split(/[\\/]/)
      .filter(Boolean)
      .pop();
    summaryNode.textContent = statusKey === "saved" && savedPackageName ? `地图包已保存：${savedPackageName}` : rawSummary;
    summaryNode.title = rawSummary;
  }
  const sessionText = $("#mappingSessionText");
  if (sessionText) {
    sessionText.textContent = session?.id || "未创建 session";
    sessionText.title = session?.sessionDir ? `${session.id}\n${session.sessionDir}` : "";
  }

  const frameInput = $("#mappingFrameCountInput");
  if (frameInput && document.activeElement !== frameInput) frameInput.value = String(mapping.frameCount || 10);
  const cloudInput = $("#mappingCloudTopicInput");
  if (cloudInput && document.activeElement !== cloudInput) cloudInput.value = mapping.cloudTopic || "/rslidar_points";
  const odomInput = $("#mappingOdomTopicInput");
  if (odomInput && document.activeElement !== odomInput) odomInput.value = mapping.odomTopic || "/odom";
  const baseInput = $("#mappingBaseFrameInput");
  if (baseInput && document.activeElement !== baseInput) baseInput.value = mapping.baseFrame || "base_link";
  const configSummary = $("#mappingConfigSummary");
  if (configSummary) {
    configSummary.textContent = `${mapping.frameCount || 10} frames / ${mapping.cloudTopic || "/rslidar_points"} / ${mapping.odomTopic || "/odom"} / ${mapping.baseFrame || "base_link"}`;
  }

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

  renderRobotFooterStatus();

  const detailList = $("#mappingDetailList");
  if (detailList) {
    detailList.innerHTML = [
      ["点云 topic", mapping.cloudTopic || "--"],
      ["里程计 topic", mapping.odomTopic || "--"],
      ["base frame", mapping.baseFrame || "--"],
      ["地图", mapState],
      ["session", session?.id || "--"],
      ["keyframes", String(keyframes.length)],
      ["最后结果", lastResult?.detail || registration.stage || "--"],
    ]
      .map(([name, value]) => `<div><span>${escapeHtml(name)}</span><strong>${escapeHtml(value)}</strong></div>`)
      .join("");
  }

  const list = $("#mappingKeyframeList");
  if (list) {
    const showEmptyState = Boolean(session?.lastError);
    list.hidden = false;
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
      : showEmptyState
        ? `<div class="mapping-keyframe-empty">${escapeHtml(session.lastError)}</div>`
        : `<div class="mapping-keyframe-empty">暂无 keyframes</div>`;
  }

  renderChassisKeyboardControl();
  renderRobotWorkMode();
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

function renderMappingSpeedSummary() {
  const summary = $("#mappingSpeedSummary");
  if (!summary) return;
  const compactLabels = { linear: "vx", lateral: "vy", angular: "wz" };
  summary.textContent = deviceBaseControlItems
    .map((item) => `${compactLabels[item.key] || item.label} ${formatCommandSpeed(item)}`)
    .join(" / ");
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
  if (selector === "#mappingBaseControlPanel") renderMappingSpeedSummary();
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

function renderPiperRemoteRuntime() {
  const label = getPiperRemoteRuntimeLabel();
  renderStatusSwitch("#piperRemoteRuntimeStatus", "主从直通", label.level, {
    pressed: label.pressed,
    busy: label.busy,
    title: label.title,
  });
}

function renderLogs() {
  // Logs remain in memory; the realtime event drawer was removed from the UI.
}

function renderActionLocks() {
  const busy = state.task !== "idle";
  const runtimeReady = piperControlAvailable();
  $$("[data-action]").forEach((button) => {
    const action = button.dataset.action;
    const requiresPiper = action === "homing" || action === "inference";
    button.disabled = busy || (requiresPiper && !runtimeReady);
  });
  const startHomingButton = $("#startHomingButton");
  if (startHomingButton) startHomingButton.disabled = busy || !runtimeReady;
  renderPreflight();
}

function syncClock() {
  setText("#clockStatus", formatTime());
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
    addLog("回放", `数据回放已加载：${dataset.name} / ${dataset.sourceType} / state ${dataset.stateDim} / action ${dataset.actionDim}`);
    return dataset;
  } catch (error) {
    state.playback.dataset = null;
    state.playback.loadedPath = "";
    state.playback.loadError = error.message;
    addLog("回放", `数据回放加载失败：${error.message}`);
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
    if (!options.silent) addLog("回放", `数据回放状态同步失败：${error.message}`);
    return null;
  }
}

function renderPlaybackExecution() {
  const enableButton = $("#playbackEnableRobotButton");
  const replayButton = $("#playbackReplayButton");
  const stopButton = $("#playbackStopButton");
  const speedInput = $("#playbackJointSpeedInput");

  if (enableButton) enableButton.textContent = state.playback.robotEnabled ? "清除回放准备" : "回放准备";
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
      ? "回放已准备"
      : "回放未准备";
  setText("#playbackExecutionStatus", status);
  setStateBadge(
    "#playbackSourceBadge",
    state.playback.loading ? "加载中" : state.playback.running ? "回放中" : state.playback.robotEnabled ? "已准备" : "待准备",
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
  setStateBadge("#playbackBadge", state.playback.running ? "回放中" : state.playback.robotEnabled ? "已准备" : "待准备", state.playback.running ? "warn" : state.playback.robotEnabled ? "ok" : "idle");

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
    setStatusPill("#enableStatus", enabled ? "已使能" : "保持使能", enabled ? "ok" : "idle");
    addLog("回放", enabled ? "数据回放 Piper 使能已打开" : "数据回放准备已清除，Piper 保持使能");
    await refreshPlaybackStatus({ silent: true });
  } catch (error) {
    state.playback.lastError = error.message;
    addLog("回放", `数据回放使能切换失败：${error.message}`);
  } finally {
    state.playback.busy = false;
    renderPlayback();
  }
}

async function startPlaybackRun() {
  if (!state.playback.robotEnabled) {
    addLog("回放", "数据回放未启动：回放未准备");
    renderPlayback();
    return;
  }
  if (!String(state.playback.path || "").trim()) {
    addLog("回放", "数据回放未启动：未选择数据文件");
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
    addLog("回放", `数据回放开始：${file.name} / ${formatNumber(maxJointSpeedDegS, 1)} deg/s`);
    setPlaybackRunning(true);
    await refreshPlaybackStatus({ silent: true });
  } catch (error) {
    state.playback.lastError = error.message;
    addLog("回放", `数据回放启动失败：${error.message}`);
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
    addLog("回放", `数据回放停止：${file.name}`);
  } catch (error) {
    state.playback.lastError = error.message;
    addLog("回放", `数据回放停止失败：${error.message}`);
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
  return fetchSelfCheckApi(path, selfCheckItems[1], "CAN 接口");
}

function fetchDiskSpaceCheck() {
  return fetchSelfCheckApi("/api/self-check/disk-space", selfCheckItems[2], "磁盘空间");
}

function fetchGpuStatusCheck() {
  return fetchSelfCheckApi("/api/self-check/gpu-status", selfCheckItems[3], "GPU 可用性");
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

function selfCheckFallbackFor(result) {
  return selfCheckItems.find((item) => item.name === result?.name) || selfCheckItems[0];
}

function normalizeSelfCheckResults(results) {
  if (!Array.isArray(results) || !results.length) return cloneCheckItems(selfCheckItems);
  return results.map((result) => normalizeCheckResult(result, selfCheckFallbackFor(result)));
}

function selfCheckDateFromPayload(payload) {
  const ranAtMs = Number(payload && payload.ranAtMs);
  if (Number.isFinite(ranAtMs) && ranAtMs > 0) return new Date(ranAtMs);
  if (payload && payload.ranAt) {
    const parsed = new Date(payload.ranAt);
    if (!Number.isNaN(parsed.getTime())) return parsed;
  }
  return new Date();
}

function alertsFromSelfCheckSummary(summary) {
  return [
    ...((summary && summary.blockers) || []).map((item) => ({
      level: "danger",
      title: `${item.name} ${item.status}`,
      detail: item.advice,
    })),
    ...((summary && summary.warnings) || []).map((item) => ({
      level: "warn",
      title: `${item.name} ${item.status}`,
      detail: item.advice,
    })),
  ];
}

function applySelfCheckPayload(payload) {
  const ran = Boolean(payload && payload.ran);
  const results = ran ? normalizeSelfCheckResults(payload.results) : cloneCheckItems(selfCheckItems);
  state.selfCheckRanAt = ran ? selfCheckDateFromPayload(payload) : null;
  state.selfCheckSummary = payload?.summary || summarizeSelfCheckResults(results);
  renderSelfCheck(results);
  if (ran) {
    state.alerts = alertsFromSelfCheckSummary(state.selfCheckSummary);
    renderAdvice();
  }
  const rosResult = results.find((item) => item.name === "ROS2 daemon");
  const canResult = results.find((item) => item.name === "CAN 接口");
  if (rosResult) updateRosTopbar(rosResult);
  if (canResult) updateCanTopbar(canResult);
  return { ran, results, summary: state.selfCheckSummary };
}

async function fetchCachedSelfCheckStatus(options = {}) {
  try {
    const response = await fetch("/api/self-check/status", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    const applied = applySelfCheckPayload(payload);
    if (!options.silent && applied.ran) {
      addLog("系统", `已恢复后端自检缓存：${applied.summary.label}`);
    }
    return payload;
  } catch (error) {
    if (!options.silent) {
      addLog("系统", `自检缓存读取失败：${error.message}`);
    }
    return null;
  }
}

function updateRosTopbar(rosResult) {
  const level = statusClass(rosResult.status);
  renderStatusSwitch("#rosStatus", "ROS", level, {
    readonly: true,
    title: level === "ok" ? "ROS 在线" : level === "warn" ? "ROS 警告" : "ROS 错误",
  });
}

function currentCanCheckResult() {
  return state.selfCheckResults.find((item) => item.name === "CAN 接口") || selfCheckItems[1];
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
  state.selfCheckSummary = summarizeSelfCheckResults(items);
  renderSelfCheck(items);
}

async function refreshCanInterfaceStatus(options = {}) {
  const canResult = await fetchCanInterfaceCheck({ autoActivate: false });
  if (options.updateSelfCheck !== false) {
    updateSingleSelfCheckResult(canResult);
  }
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
  state.selfCheckSummary = {
    state: "running",
    level: "warn",
    label: "检查中",
    nextAction: "正在检查并自动修复 ROS daemon 与 CAN。",
    blockers: [],
    warnings: [],
  };
  renderSelfCheck(state.selfCheckResults.length ? state.selfCheckResults : selfCheckItems);
  $("#selfCheckSummary").textContent = "正在检查并自动修复 ROS/CAN";
  addLog("系统", "开始整机自检");

  try {
    const response = await fetch("/api/self-check/run?auto_activate=1", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const payload = await response.json();
    if (!response.ok || !payload.ok) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    const { results, summary } = applySelfCheckPayload(payload);
    const counts = countCheckStatuses(results);
    $("#selfCheckSummary").textContent = `自检完成：${summary.label}`;
    setStateBadge("#selfCheckBadge", summary.label, summary.level === "danger" ? "danger" : summary.level);
    state.alerts = alertsFromSelfCheckSummary(summary);
    renderAdvice();
    results.forEach((result) => addLog(result.source, `${result.name} 自检：${result.status} / ${result.code}`));
    addLog("系统", `整机自检完成：${counts.ok} 正常，${counts.warn} 警告，${counts.danger} 错误`);
  } catch (error) {
    state.selfCheckSummary = {
      state: "blocked",
      level: "danger",
      label: "自检失败",
      nextAction: "请确认 Robot Station 后端服务是否运行。",
      blockers: [],
      warnings: [],
    };
    renderSelfCheck(state.selfCheckResults.length ? state.selfCheckResults : selfCheckItems);
    $("#selfCheckSummary").textContent = `自检请求失败：${error.message}`;
    setStateBadge("#selfCheckBadge", "请求失败", "danger");
    addLog("系统", `整机自检请求失败：${error.message}`);
  }
}

async function rerunProblemChecks() {
  const problems = state.selfCheckResults.filter((item) => item.status === "警告" || item.status === "错误");
  if (!problems.length) {
    addLog("系统", "复查异常项：当前没有异常项，重新执行放行检查");
  } else {
    problems.forEach((item) => addLog(item.source, `复查异常项：${item.name}`));
  }
  await runSelfCheck();
}

async function startHoming() {
  if (state.task !== "idle") return;
  const unavailableDetail = piperControlUnavailableDetail();
  if (unavailableDetail) {
    addLog("机械臂", `归位未启动：${unavailableDetail}`);
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
      setStatusPill("#enableStatus", "已使能", "ok");
      addLog("系统", "归位流程完成");
    }
  }, 700);
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
    if (result.ok) refreshLocalizationMaps({ silent: true });
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

function applyLocalizationMaps(result = {}) {
  const localization = state.localization;
  const maps = Array.isArray(result.maps) ? result.maps : [];
  localization.maps = maps;
  localization.mapsLoadedAt = Date.now();
  localization.lastError = result.ok === false ? result.detail || result.code || "地图列表读取失败" : "";

  const hasSelected = maps.some((map) => map.name === localization.selectedMap);
  if (!hasSelected) {
    localization.selectedMap = maps[0]?.name || "";
  }
  if (localization.loadedMap && !maps.some((map) => map.name === localization.loadedMap)) {
    localization.loadedMap = "";
    localization.mapPointCount = 0;
    localization.mapSizeBytes = 0;
    localization.mapMtimeMs = null;
    resetNavigationForMapChange();
    if (state.mapping.mapPreview.source === "localization") clearMappingMapPreview();
  }
  renderLocalizationStatus();
  if (state.robotWork.mode === "localization" || state.robotWork.mode === "navigation") renderRobotWorkMode();
}

async function refreshLocalizationMaps(options = {}) {
  const localization = state.localization;
  if (localization.mapsLoading) return null;
  localization.mapsLoading = true;
  if (!options.silent) localization.lastError = "";
  renderLocalizationStatus();
  if (state.robotWork.mode === "localization" || state.robotWork.mode === "navigation") renderRobotWorkMode();

  try {
    const response = await fetch("/api/mapping/maps", { cache: "no-store" });
    const result = await response.json();
    if (!response.ok || result.ok === false) {
      throw new Error(result.detail || result.code || `HTTP ${response.status}`);
    }
    localization.mapsLoading = false;
    applyLocalizationMaps(result);
    if (!options.silent) addLog("定位", `地图列表已刷新：${result.maps?.length || 0} 张`);
    return result;
  } catch (error) {
    localization.mapsLoading = false;
    localization.lastError = `地图列表刷新失败：${error.message}`;
    renderLocalizationStatus();
    if (state.robotWork.mode === "localization" || state.robotWork.mode === "navigation") renderRobotWorkMode();
    if (!options.silent) addLog("定位", localization.lastError);
    return null;
  }
}

async function loadLocalizationMapFrame() {
  const localization = state.localization;
  const mapName = localization.selectedMap;
  const selectedMap = localizationMapByName(mapName);
  const previousMapName = localization.loadedMap;
  if (localization.running) return;
  if (!selectedMap || localization.mapLoadBusy) return;

  localization.mapLoadBusy = true;
  localization.status = "loading";
  localization.lastError = "";
  if (state.mapping.mapPreview.source !== "localization" || state.mapping.mapPreview.mapName !== mapName) {
    clearMappingMapPreview();
  }
  renderLocalizationStatus();
  renderRobotWorkMode();

  try {
    const initialized = await initializeRobotViewer();
    if (!initialized || !ensureMappingMapLayer()) throw new Error("整机 3D 视图未就绪");
    const response = await fetch(`/api/mapping/maps/${encodeURIComponent(mapName)}/frame?t=${Date.now()}`, { cache: "no-store" });
    const contentType = response.headers.get("Content-Type") || "";
    if (!response.ok || contentType.includes("application/json")) {
      const payload = contentType.includes("application/json") ? await response.json() : null;
      throw new Error((payload && payload.detail) || `HTTP ${response.status}`);
    }

    const buffer = await response.arrayBuffer();
    const cloud = updateMappingMapPointCloud(buffer, { source: "localization", mapName });
    if (!cloud) throw new Error("定位地图渲染失败");
    const preview = state.mapping.mapPreview;
    const pointCount = Number(response.headers.get("X-Robot-Station-PointCloud-Point-Count"));
    const sourcePointCount = Number(response.headers.get("X-Robot-Station-PointCloud-Source-Point-Count"));
    const sizeBytes = Number(response.headers.get("X-Robot-Station-Mapping-Map-Size-Bytes"));
    const mtimeMs = Number(response.headers.get("X-Robot-Station-Mapping-Map-Mtime-Ms"));
    preview.pointCount = Number.isFinite(pointCount) ? pointCount : cloud.count;
    preview.sourcePointCount = Number.isFinite(sourcePointCount) ? sourcePointCount : preview.pointCount;
    preview.sizeBytes = Number.isFinite(sizeBytes) ? sizeBytes : selectedMap.sizeBytes || buffer.byteLength;
    preview.mtimeMs = Number.isFinite(mtimeMs) ? mtimeMs : selectedMap.mtimeMs || Date.now();
    preview.loadedRevision = localizationMapRevision(selectedMap) || `${mapName}:${preview.sizeBytes}:${preview.mtimeMs}`;
    preview.error = "";
    localization.status = "map-loaded";
    localization.loadedMap = mapName;
    localization.mapPointCount = preview.pointCount;
    localization.mapSizeBytes = preview.sizeBytes;
    localization.mapMtimeMs = preview.mtimeMs;
    localization.lastError = "";
    if (previousMapName !== mapName) resetNavigationForMapChange();
    updateRobotModelTransforms();
    renderRobotViewStatus();
    addLog("定位", `定位地图已加载：${mapName}`);
  } catch (error) {
    localization.status = "error";
    localization.lastError = `地图加载失败：${error.message}`;
    if (state.mapping.mapPreview.source === "localization") clearMappingMapPreview();
    addLog("定位", localization.lastError);
  } finally {
    localization.mapLoadBusy = false;
    renderLocalizationStatus();
    renderRobotWorkMode();
  }
}

async function publishInitialPose() {
  const localization = state.localization;
  const pose = initialPoseValues();
  if (!initialPoseMapReady() || !pose || localization.initialPosePublishing) return;

  localization.initialPosePublishing = true;
  localization.lastError = "";
  renderLocalizationStatus();

  const payload = {
    ...pose,
    frameId: "map",
    mapName: localization.loadedMap,
  };

  try {
    const response = await fetch("/api/localization/initial-pose", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
      cache: "no-store",
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok || result.ok === false) {
      throw new Error(result.detail || result.code || `HTTP ${response.status}`);
    }
    localization.status = "initial-pose-published";
    localization.initialPoseLastPublishedAt = result.publishedAt || formatTime();
    localization.initialPoseEditMode = false;
    resetInitialPoseDrag();
    localization.lastError = "";
    updateRobotModelTransforms();
    refreshLocalizationStatus({ silent: true });
    addLog(
      "定位",
      `Initial pose 已发布：${pose.x.toFixed(2)}, ${pose.y.toFixed(2)}, ${pose.yawDeg.toFixed(1)} deg`,
    );
  } catch (error) {
    localization.status = "error";
    localization.lastError = `初值发布失败：${error.message}`;
    addLog("定位", localization.lastError);
  } finally {
    localization.initialPosePublishing = false;
    renderLocalizationStatus();
    renderRobotWorkMode();
  }
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
  const unavailableDetail = piperControlUnavailableDetail();
  if (unavailableDetail) {
    addLog("推理", `Piper 使能失败：${unavailableDetail}`);
    showView("device-control");
    return;
  }
  state.piperEnableBusy = true;
  renderInferenceStatus();
  try {
    await publishPiperEnable(true, { repeat: 3, intervalMs: 80 });
    setStatusPill("#enableStatus", "已使能", "ok");
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
  const unavailableDetail = piperControlUnavailableDetail();
  if (unavailableDetail) {
    addLog("推理", `提示：${unavailableDetail}，执行前请切换到 Piper 控制`);
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
    if (result.ok && result.isSuccess === true) {
      if (writeLog) addLog("推理", "远端报告任务已完成");
    } else if (result.ok && writeLog) {
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
    if (chunk.isSuccess === true) {
      addLog("推理", `闭环 #${loopSeq} 完成：远端报告任务成功`);
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
  const estopStatus = $("#estopStatus");
  if (estopStatus) {
    estopStatus.textContent = "急停触发";
    estopStatus.className = "status-pill danger";
  }
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

async function startPiperRemoteRuntime() {
  if (state.piperRemoteRuntime.status === "running" || state.piperRemoteRuntime.status === "starting") return;
  await requestPiperRemoteRuntimeAction("start");
}

async function stopPiperRemoteRuntime() {
  if (state.piperRemoteRuntime.status === "stopped" || state.piperRemoteRuntime.status === "stopping") return;
  await requestPiperRemoteRuntimeAction("stop");
}

function togglePiperRemoteRuntime() {
  if (state.piperRemoteRuntime.status === "starting" || state.piperRemoteRuntime.status === "stopping") return;
  if (state.piperRemoteRuntime.status === "running" || state.piperRemoteRuntime.status === "external") {
    stopPiperRemoteRuntime();
    return;
  }
  startPiperRemoteRuntime();
}

function applyPiperServicePayload(payload) {
  const service = payload && payload.service;
  if (!service || !service.status) return false;
  setPiperRuntime(service.status);
  return true;
}

function applyPiperRemoteServicePayload(payload) {
  const service = payload && payload.service;
  if (!service || !service.status) return false;
  setPiperRemoteRuntime(service.status);
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

async function fetchPiperRemoteRuntimeStatus(options = {}) {
  try {
    const response = await fetch("/api/runtime/services/piper_remote", { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok || !applyPiperRemoteServicePayload(payload)) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    return payload;
  } catch (error) {
    if (!options.silent) {
      setPiperRemoteRuntime("error");
      addLog("机械臂", `主从直通状态查询失败：${error.message}`);
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

async function startRuntimePrepService(key) {
  if (state.runtimePrepBusy[key]) return;
  const actions = {
    piper: () => requestPiperRuntimeAction("start"),
    piper_remote: () => requestPiperRemoteRuntimeAction("start"),
    lifting: () => requestLiftingRuntimeAction("start"),
    chassis: () => requestChassisRuntimeAction("start"),
    camera: () => requestCameraRuntimeAction("start"),
    lidar: () => requestLidarRuntimeAction("start"),
  };
  const action = actions[key];
  if (!action) return;
  state.runtimePrepBusy[key] = true;
  renderRuntimePrep();
  try {
    await action();
  } finally {
    state.runtimePrepBusy[key] = false;
    renderRuntimePrep();
  }
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
  if (state.robotWork.modal) return;
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

function piperJointPayloadHasPositions(payload) {
  const positions = payload && payload.data && Array.isArray(payload.data.position) ? payload.data.position : [];
  return Boolean(payload && payload.ok && positions.length > 0);
}

async function fetchPiperJointCandidate(candidate) {
  try {
    const response = await fetch(`/api/ros/topics/${candidate.key}?wait=${piperJointReadWaitSec}`, { cache: "no-store" });
    const payload = await response.json();
    if (!response.ok && !payload.code) {
      payload.ok = false;
      payload.code = `HTTP-${response.status}`;
      payload.detail = `HTTP ${response.status}`;
    }
    if (!payload.topic) payload.topic = candidate.topic;
    return payload;
  } catch (error) {
    return {
      ok: false,
      code: "ROS-R-FETCH",
      detail: error.message,
      topic: candidate.topic,
    };
  }
}

async function fetchPiperJointSide(side) {
  const candidates = piperJointTopicCandidates[side] || [{ key: piperJointTopicKeys[side], topic: piperJointTopicNames[side] }];
  let firstPayload = null;
  let stalePayload = null;
  for (const candidate of candidates) {
    const payload = await fetchPiperJointCandidate(candidate);
    if (!firstPayload) firstPayload = payload;
    if (piperJointPayloadHasPositions(payload)) {
      if (!payload.stale) return [side, payload];
      if (!stalePayload) stalePayload = payload;
    }
  }
  return [side, stalePayload || firstPayload || { ok: false, code: "ROS-R-NODATA", detail: `${piperArmLabels[side]}关节反馈无可用候选。` }];
}

async function fetchPiperJointStates() {
  if (state.piperJointPolling) {
    return null;
  }
  state.piperJointPolling = true;
  try {
    const results = await Promise.all(
      Object.keys(piperJointTopicCandidates).map((side) => fetchPiperJointSide(side)),
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
    window.setTimeout(() => {
      fetchPiperRuntimeStatus({ silent: true });
      fetchPiperRemoteRuntimeStatus({ silent: true });
    }, 800);
  }
}

async function requestPiperRemoteRuntimeAction(action) {
  const nextStatus = action === "stop" ? "stopping" : "starting";
  setPiperRemoteRuntime(nextStatus);
  addLog("机械臂", action === "stop" ? "请求清理主从直通 ROS" : "请求启动主从直通服务");
  try {
    const response = await fetch(`/api/runtime/services/piper_remote/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const payload = await response.json();
    applyPiperRemoteServicePayload(payload);
    if (!response.ok || !payload.ok) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    addLog("机械臂", `主从直通服务动作完成：${payload.code}`);
    return payload;
  } catch (error) {
    setPiperRemoteRuntime("error");
    addLog("机械臂", `主从直通服务动作失败：${error.message}`);
    return null;
  } finally {
    window.setTimeout(() => {
      fetchPiperRuntimeStatus({ silent: true });
      fetchPiperRemoteRuntimeStatus({ silent: true });
    }, 800);
  }
}

function normalizeCameraKind(kind) {
  return cameraKindMeta[kind] ? kind : "color";
}

function currentCameraKind() {
  state.cameraFrames.activeKind = normalizeCameraKind(state.cameraFrames.activeKind);
  return state.cameraFrames.activeKind;
}

function currentCameraKindMeta() {
  return cameraKindMeta[currentCameraKind()];
}

function cameraPreviewEnabled(kind = currentCameraKind()) {
  const normalized = normalizeCameraKind(kind);
  return Boolean(state.cameraFrames.previewEnabledByKind?.[normalized]);
}

function syncCameraPreviewEnabled() {
  state.cameraFrames.previewEnabled = cameraPreviewEnabled(currentCameraKind());
}

function setCameraPreviewFlag(kind, enabled) {
  const targetKind = normalizeCameraKind(kind);
  if (!state.cameraFrames.previewEnabledByKind) {
    state.cameraFrames.previewEnabledByKind = {};
  }
  cameraKindOrder.forEach((entry) => {
    state.cameraFrames.previewEnabledByKind[entry] = entry === targetKind ? Boolean(enabled) : false;
  });
  syncCameraPreviewEnabled();
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

function activeCameraFeeds(feeds = state.cameraFrames.feeds) {
  const kind = currentCameraKind();
  const allFeeds = feeds.length ? feeds : mergeCameraFeeds();
  return allFeeds.filter((feed) => normalizeCameraKind(feed.kind) === kind);
}

function isCameraFeedPreviewActive(feed) {
  const kind = normalizeCameraKind(feed.kind);
  return kind === currentCameraKind() && cameraPreviewEnabled(kind);
}

function renderCameraKindTabs() {
  const activeKind = currentCameraKind();
  const meta = currentCameraKindMeta();
  $$("#cameraKindTabs [data-camera-kind-tab]").forEach((button) => {
    const isActive = normalizeCameraKind(button.dataset.cameraKindTab) === activeKind;
    button.classList.toggle("is-active", isActive);
    button.setAttribute("aria-selected", isActive ? "true" : "false");
  });
  setText("#cameraKindTitle", meta.title);
  setText("#cameraKindHint", meta.hint);
}

function renderCameraPreviewToggle() {
  const button = $("#cameraPreviewToggleButton");
  if (!button) return;
  syncCameraPreviewEnabled();
  const enabled = cameraPreviewEnabled();
  const meta = currentCameraKindMeta();
  button.textContent = enabled ? "回显开启" : "回显关闭";
  button.title = enabled ? `关闭${meta.label}相机图像回显` : `开启${meta.label}相机图像回显`;
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

function setCameraKind(kind) {
  const nextKind = normalizeCameraKind(kind);
  if (currentCameraKind() === nextKind) return;
  state.cameraFrames.activeKind = nextKind;
  setCameraPreviewFlag(nextKind, false);
  clearCameraFrameDisplay();
  renderCameraFrames();
  addLog("相机", `切换到${cameraKindMeta[nextKind].label}相机，回显已关闭`);
}

function setCameraPreviewEnabled(enabled, options = {}) {
  const nextEnabled = Boolean(enabled);
  const kind = currentCameraKind();
  const meta = currentCameraKindMeta();
  if (cameraPreviewEnabled(kind) === nextEnabled && !options.force) return;
  setCameraPreviewFlag(kind, nextEnabled);
  renderCameraPreviewToggle();
  if (!nextEnabled) {
    clearCameraFrameDisplay();
    renderCameraFrames();
    if (!options.silent) addLog("相机", `${meta.label}相机图像回显已关闭`);
    return;
  }
  clearCameraFrameDisplay();
  renderCameraFrames();
  fetchCameraFrames({ silent: true, kind });
  if (!options.silent) addLog("相机", `${meta.label}相机图像回显已开启`);
}

function toggleCameraPreview() {
  setCameraPreviewEnabled(!cameraPreviewEnabled());
}

function cameraFrameAgeText(feed) {
  const ageMs = Number(feed.ageMs);
  if (!Number.isFinite(ageMs)) return "无帧";
  if (ageMs < 1000) return `${Math.max(0, Math.round(ageMs))} ms`;
  return `${(ageMs / 1000).toFixed(1)} s`;
}

function cameraFrameStatus(feed) {
  if (!isCameraFeedPreviewActive(feed)) return { text: "关闭", level: "idle" };
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
  if (!isCameraFeedPreviewActive(feed)) return;
  const key = cameraFeedKey(feed);
  window.clearTimeout(state.cameraFrames.frameTimers[key]);
  state.cameraFrames.frameTimers[key] = window.setTimeout(() => {
    requestCameraFrame(feed);
  }, delayMs);
}

async function requestCameraFrame(feed) {
  if (!isCameraFeedPreviewActive(feed)) return;
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

    if (!isCameraFeedPreviewActive(feed)) {
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
    if (isCameraFeedPreviewActive(feed) && card && card.isConnected) {
      const elapsed = performance.now() - startedAt;
      scheduleCameraFrame(feed, Math.max(40, cameraFrameIntervalMs - elapsed));
    }
  }
}

function ensureCameraFrameLoop(feed) {
  if (!isCameraFeedPreviewActive(feed)) return;
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
          <span class="camera-frame-placeholder">${isCameraFeedPreviewActive(feed) ? "等待画面" : "回显关闭"}</span>
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
    const text = !isCameraFeedPreviewActive(feed) ? "回显关闭" : feed.hasFrame ? `${cameraFrameAgeText(feed)} / ${format}` : feed.topic || "";
    detail.textContent = text;
    detail.title = feed.topic || "";
  }

  const image = card.querySelector("img[data-camera-frame]");
  if (image && image.alt !== feed.label) {
    image.alt = feed.label;
  }
  const placeholder = card.querySelector(".camera-frame-placeholder");
  if (placeholder) {
    placeholder.textContent = isCameraFeedPreviewActive(feed) ? "等待画面" : "回显关闭";
  }
}

function renderCameraFrames() {
  const feeds = activeCameraFeeds();
  const enabled = cameraPreviewEnabled();
  renderCameraKindTabs();
  renderCameraPreviewToggle();
  const summary = $("#cameraFeedSummary");
  if (summary) {
    const liveCount = feeds.filter((feed) => feed.hasFrame && !feed.stale).length;
    const frameCount = feeds.filter((feed) => feed.hasFrame).length;
    const meta = currentCameraKindMeta();
    summary.textContent = !enabled
      ? `${meta.label} 回显关闭`
      : state.cameraFrames.error
      ? `${meta.label} 异常：${state.cameraFrames.error}`
      : `${meta.label}：${liveCount} 路实时 / ${frameCount} 路有帧 / 共 ${feeds.length} 路`;
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
  const kind = normalizeCameraKind(options.kind || currentCameraKind());
  if (kind !== currentCameraKind() || !cameraPreviewEnabled(kind)) {
    renderCameraFrames();
    return null;
  }
  try {
    const params = new URLSearchParams({ kind });
    const response = await fetch(`/api/sensors/cameras?${params.toString()}`, { cache: "no-store" });
    const payload = await response.json();
    if (!payload || !Array.isArray(payload.feeds)) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    if (kind !== currentCameraKind() || !cameraPreviewEnabled(kind)) {
      return payload;
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
  const worldRoot = robotMetricWorldRoot();
  if (!robot.three || !worldRoot) return false;

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

  if (preview.points.parent !== worldRoot) {
    worldRoot.add(preview.points);
  }
  preview.initialized = true;
  preview.points.visible = preview.hasFrame;
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

function updateMappingMapPointCloud(buffer, options = {}) {
  const robot = state.robotModel;
  const preview = state.mapping.mapPreview;
  if (!robot.three || !ensureMappingMapLayer()) return null;

  const cloud = buildLidarPointCloudAttributes(buffer);
  preview.source = options.source || "mapping";
  preview.mapName = options.mapName || "";
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
  const previousSource = preview.source;
  preview.hasFrame = false;
  preview.pointCount = 0;
  preview.sourcePointCount = 0;
  preview.sizeBytes = 0;
  preview.mtimeMs = null;
  preview.loadedRevision = "";
  preview.error = "";
  preview.source = "";
  preview.mapName = "";
  if (previousSource === "localization" && !state.localization.running) {
    state.localization.loadedMap = "";
    state.localization.mapPointCount = 0;
    state.localization.mapSizeBytes = 0;
    state.localization.mapMtimeMs = null;
    state.localization.initialPoseEditMode = false;
    resetInitialPoseDrag();
    resetNavigationForMapChange();
  }
  if (preview.points) preview.points.visible = false;
  $("#robotViewStage")?.classList.remove("is-initial-pose-editing");
  $("#robotViewStage")?.classList.remove("is-navigation-goal-editing");
  renderInitialPoseMarker();
  renderNavigationGoalMarker();
  renderNavigationPathLayer();
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
    const cloud = updateMappingMapPointCloud(buffer, { source: "mapping" });
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
  const preview = state.mapping.mapPreview;
  if (preview.source === "localization") {
    if (state.robotWork.mode === "localization" || state.robotWork.mode === "navigation") return;
    clearMappingMapPreview();
  }
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

const cameraCalibrationServiceLabels = {
  running: "运行中",
  external: "外部运行",
  starting: "启动中",
  stopping: "停止中",
  stopped: "已停止",
  failed: "失败",
  error: "异常",
  unavailable: "未注册",
  unknown: "未知",
};

function cameraCalibrationPayload() {
  return state.cameraCalibration.statusPayload || null;
}

function cameraCalibrationConfig(payload = cameraCalibrationPayload()) {
  return payload?.extrinsics?.config || null;
}

function cameraCalibrationTransforms(config = cameraCalibrationConfig()) {
  return Array.isArray(config?.transforms) ? config.transforms : [];
}

function cameraCalibrationSampling(payload = cameraCalibrationPayload()) {
  return payload?.sampling || null;
}

function cameraCalibrationSamples(payload = cameraCalibrationPayload()) {
  const samples = cameraCalibrationSampling(payload)?.samples;
  return Array.isArray(samples) ? samples : [];
}

function cameraCalibrationPerCameraSamples(payload = cameraCalibrationPayload()) {
  const perCamera = cameraCalibrationSampling(payload)?.perCamera;
  return perCamera && typeof perCamera === "object" ? perCamera : {};
}

function formatCameraCalibrationConfig(config) {
  const fallback = { enabled: false, transforms: [] };
  const serializable = config ? JSON.parse(JSON.stringify(config)) : fallback;
  delete serializable.path;
  return JSON.stringify(serializable, null, 2);
}

function cameraCalibrationDependenciesReady(payload = cameraCalibrationPayload()) {
  const dependencies = Array.isArray(payload?.dependencies) ? payload.dependencies : [];
  return dependencies.every((item) => !item.required || item.available);
}

function cameraCalibrationService(payload = cameraCalibrationPayload()) {
  return payload?.extrinsics?.service || null;
}

function cameraCalibrationServiceStatus(payload = cameraCalibrationPayload()) {
  const service = cameraCalibrationService(payload);
  if (service?.status) return service.status;
  if (payload?.extrinsics?.serviceAvailable) return "unknown";
  return "unavailable";
}

function cameraCalibrationStatusSummary(payload = cameraCalibrationPayload()) {
  if (state.cameraCalibration.statusLoading && !payload) return { label: "读取中", level: "idle" };
  if (!payload) {
    return state.cameraCalibration.statusError
      ? { label: "读取失败", level: "danger" }
      : { label: "未读取", level: "idle" };
  }
  if (!payload.ok) return { label: "配置异常", level: "danger" };
  if (!cameraCalibrationDependenciesReady(payload)) return { label: "依赖缺失", level: "danger" };

  const config = cameraCalibrationConfig(payload);
  const transforms = cameraCalibrationTransforms(config);
  const cameras = Array.isArray(payload?.extrinsics?.cameras) ? payload.extrinsics.cameras : [];
  const allConfigured = cameras.length > 0 && cameras.every((camera) => camera.configured && camera.bridgeConfigured);
  if (!config?.enabled) return { label: "未发布", level: "warn" };
  if (!transforms.length || !allConfigured) return { label: "外参缺失", level: "warn" };

  const serviceStatus = cameraCalibrationServiceStatus(payload);
  if (serviceStatus === "running" || serviceStatus === "external") return { label: "TF 发布中", level: "ok" };
  if (serviceStatus === "starting" || serviceStatus === "stopping") {
    return { label: cameraCalibrationServiceLabels[serviceStatus], level: "warn" };
  }
  if (serviceStatus === "failed" || serviceStatus === "error") return { label: "服务异常", level: "danger" };
  return { label: "待启动", level: "warn" };
}

function cameraCalibrationInitial(cameraKey) {
  return String(cameraKey || "?").replace(/^camera_/, "").slice(0, 1).toUpperCase() || "?";
}

function readCameraCalibrationBoard() {
  const typeText = $("#calibrationBoardType")?.value || "Checkerboard";
  const normalizedType = String(typeText).toLowerCase().includes("charuco")
    ? "charuco"
    : String(typeText).toLowerCase().includes("april")
      ? "apriltag-grid"
      : "checkerboard";
  return {
    type: normalizedType,
    columns: Number($("#calibrationBoardColumns")?.value || 11),
    rows: Number($("#calibrationBoardRows")?.value || 8),
    squareSizeMm: Number($("#calibrationBoardSquareSize")?.value || 3.0),
    tagSizeMm: Number($("#calibrationBoardTagSize")?.value || 0),
    dictionary: $("#calibrationBoardDictionary")?.value || "DICT_4X4_50",
  };
}

function formatCalibrationSampleMetric(value, suffix = "") {
  const number = Number(value);
  if (!Number.isFinite(number)) return "--";
  return `${number.toFixed(number >= 10 ? 0 : 2)}${suffix}`;
}

function formatCalibrationAge(ageMs) {
  const number = Number(ageMs);
  if (!Number.isFinite(number)) return "--";
  return number < 1000 ? `${Math.round(number)} ms` : `${(number / 1000).toFixed(1)} s`;
}

function selectedCameraCalibrationMethod() {
  const active = $("[data-camera-calibration-method].is-active");
  return active?.dataset.cameraCalibrationMethod || "tsai";
}

function selectedCameraCalibrationSolveCamera() {
  return $("#cameraCalibrationSolveCamera")?.value || "all";
}

function aggregateCameraCalibrationSolveMetrics(result = state.cameraCalibration.solveResult) {
  const cameraResults = Array.isArray(result?.cameraResults) ? result.cameraResults : [];
  const solved = cameraResults.filter((item) => item?.ok && item.metrics);
  const average = (key) => {
    const values = solved.map((item) => Number(item.metrics?.[key])).filter((value) => Number.isFinite(value));
    if (!values.length) return null;
    return values.reduce((sum, value) => sum + value, 0) / values.length;
  };
  return {
    reprojectionRmsPx: average("reprojectionRmsPx"),
    boardRotationRmsDeg: average("boardRotationRmsDeg"),
    sampleCount: solved.reduce((sum, item) => sum + (Number(item.metrics?.sampleCount) || 0), 0),
  };
}

function renderCameraCalibrationSolve(payload = cameraCalibrationPayload()) {
  const result = state.cameraCalibration.solveResult;
  const dependenciesReady = cameraCalibrationDependenciesReady(payload);
  const sampling = cameraCalibrationSampling(payload);
  const totalSamples = Number(sampling?.total) || 0;
  const selectedCamera = selectedCameraCalibrationSolveCamera();
  const perCamera = cameraCalibrationPerCameraSamples(payload);
  const selectedSamples = selectedCamera === "all"
    ? totalSamples
    : Number(perCamera[selectedCamera]?.count) || 0;

  if (state.cameraCalibration.solveBusy) {
    setStateBadge("#cameraCalibrationSolveBadge", "求解中", "warn");
  } else if (result?.ok) {
    setStateBadge("#cameraCalibrationSolveBadge", "已求解", "ok");
  } else if (result && result.ok === false) {
    setStateBadge("#cameraCalibrationSolveBadge", "求解失败", "danger");
  } else if (!dependenciesReady && payload) {
    setStateBadge("#cameraCalibrationSolveBadge", "依赖缺失", "danger");
  } else if (selectedSamples > 0) {
    setStateBadge("#cameraCalibrationSolveBadge", "待求解", "warn");
  } else {
    setStateBadge("#cameraCalibrationSolveBadge", "待采样", "idle");
  }

  setText("#cameraCalibrationMinSamplesMetric", "12");
  setText("#cameraCalibrationRecommendedSamplesMetric", selectedCamera === "all" ? "24 / 路" : "24");
  const metrics = aggregateCameraCalibrationSolveMetrics(result);
  setText(
    "#cameraCalibrationReprojectionMetric",
    Number.isFinite(metrics.reprojectionRmsPx) ? `${metrics.reprojectionRmsPx.toFixed(2)} px` : "-- px",
  );
  setText(
    "#cameraCalibrationRotationResidualMetric",
    Number.isFinite(metrics.boardRotationRmsDeg) ? `${metrics.boardRotationRmsDeg.toFixed(2)} deg` : "-- deg",
  );

  const button = $("#cameraCalibrationSolveButton");
  if (button) {
    button.disabled = state.cameraCalibration.solveBusy || !payload?.ok || !dependenciesReady || selectedSamples <= 0;
    button.textContent = state.cameraCalibration.solveBusy ? "求解中" : "开始求解";
    button.title = selectedSamples <= 0 ? "请先采集标定样本" : "使用已采集样本求解 camera_extrinsics.json";
  }
}

function renderCameraCalibrationCameraList(cameras, payload = cameraCalibrationPayload()) {
  const list = $("#calibrationCameraList");
  if (!list) return;
  const items = Array.isArray(cameras) ? cameras : [];
  if (!items.length) {
    list.innerHTML = `<section class="calibration-camera-card is-missing"><p class="calibration-projection-result">后端暂未返回相机标定目标。</p></section>`;
    return;
  }
  const perCamera = cameraCalibrationPerCameraSamples(payload);
  const dependenciesReady = cameraCalibrationDependenciesReady(payload);
  list.innerHTML = items.map((camera) => {
    const ready = camera.configured && camera.bridgeConfigured;
    const partial = camera.configured || camera.bridgeConfigured;
    const badge = ready ? "已配置" : partial ? "缺桥接" : "未配置";
    const sampleStats = perCamera[camera.camera] || {};
    const sampleCount = Number(sampleStats.count) || 0;
    const targetCount = Number(sampleStats.targetCount || cameraCalibrationSampling(payload)?.targetCount || 24) || 24;
    const sampleLevel = sampleCount >= targetCount ? "ok" : sampleCount > 0 ? "warn" : "idle";
    const sampleBusy = state.cameraCalibration.sampleBusyCamera === camera.camera;
    const clearBusy = state.cameraCalibration.sampleClearBusyCamera === camera.camera;
    const calibrationSampleBusy = Boolean(state.cameraCalibration.sampleBusyCamera || state.cameraCalibration.sampleClearBusyCamera);
    const canSample = Boolean(payload?.ok && dependenciesReady && !calibrationSampleBusy);
    const canClear = Boolean(payload?.ok && sampleCount > 0 && !calibrationSampleBusy);
    const buttonTitle = !payload?.ok
      ? "等待标定状态可用"
      : !dependenciesReady
        ? "缺少 OpenCV/NumPy 依赖"
        : `采集 ${camera.camera} 棋盘样本`;
    const clearTitle = sampleCount > 0 ? `清除 ${camera.camera} 已采样本` : "没有可清除样本";
    const classes = ["calibration-camera-card", ready ? "is-configured" : "is-missing"];
    return `
      <section class="${classes.join(" ")}">
        <div class="calibration-camera-title">
          <span>${escapeHtml(cameraCalibrationInitial(camera.camera))}</span>
          <div>
            <strong>${escapeHtml(camera.displayName || camera.label || camera.camera)}</strong>
            <small>${escapeHtml(camera.camera || "")}</small>
          </div>
        </div>
        <dl>
          <div><dt>父级 link</dt><dd>${escapeHtml(camera.parentFrame || "--")}</dd></div>
          <div><dt>外参 link</dt><dd>${escapeHtml(camera.extrinsicFrame || "--")}</dd></div>
          <div><dt>驱动 link</dt><dd>${escapeHtml(camera.driverFrame || "--")}</dd></div>
          <div><dt>Optical frame</dt><dd>${escapeHtml(camera.targetFrame || "--")}</dd></div>
          <div><dt>CameraInfo</dt><dd>${escapeHtml(camera.cameraInfoTopic || "--")}</dd></div>
        </dl>
        <div class="calibration-card-footer">
          <span class="state-badge ${sampleLevel}" title="${escapeHtml(badge)}">${sampleCount} / ${targetCount}</span>
          <div class="calibration-card-actions">
            <button class="secondary-button" type="button" data-camera-calibration-sample="${escapeHtml(camera.camera)}" title="${escapeHtml(buttonTitle)}" ${canSample ? "" : "disabled"}>${sampleBusy ? "采样中" : "采样"}</button>
            <button class="secondary-button calibration-clear-button" type="button" data-camera-calibration-clear="${escapeHtml(camera.camera)}" title="${escapeHtml(clearTitle)}" ${canClear ? "" : "disabled"}>${clearBusy ? "清除中" : "清除"}</button>
          </div>
        </div>
      </section>
    `;
  }).join("");
}

function renderCameraCalibrationTfPreview(payload = cameraCalibrationPayload()) {
  const preview = $("#cameraCalibrationTfPreview");
  if (!preview) return;
  const cameras = Array.isArray(payload?.extrinsics?.cameras) ? payload.extrinsics.cameras : [];
  if (!cameras.length) {
    preview.textContent = "等待后端返回 TF 链路";
    return;
  }
  preview.textContent = cameras.map((camera) => {
    const chain = Array.isArray(camera.chain) && camera.chain.length
      ? camera.chain.join(" -> ")
      : [camera.parentFrame, camera.extrinsicFrame, camera.driverFrame, camera.targetFrame].filter(Boolean).join(" -> ");
    const primary = camera.configured ? "OK" : "missing";
    const bridge = camera.bridgeConfigured ? "OK" : "missing";
    return `${camera.camera}: ${chain}\n  ${camera.parentFrame} -> ${camera.extrinsicFrame}: ${primary}\n  ${camera.extrinsicFrame} -> ${camera.driverFrame}: ${bridge}`;
  }).join("\n");
}

function renderCameraCalibrationEditor(payload = cameraCalibrationPayload()) {
  const config = cameraCalibrationConfig(payload);
  const textarea = $("#cameraExtrinsicsConfigEditor");
  const toggle = $("#cameraExtrinsicsEnabledToggle");
  const saveButton = $("#cameraExtrinsicsSaveButton");
  const resetButton = $("#cameraExtrinsicsResetButton");
  const result = $("#cameraExtrinsicsConfigResult");

  if (textarea && !state.cameraCalibration.configDirty && !state.cameraCalibration.configSaving) {
    textarea.value = formatCameraCalibrationConfig(config);
  }
  if (toggle) {
    toggle.checked = Boolean(config?.enabled);
    toggle.disabled = state.cameraCalibration.configSaving || !config;
  }
  if (saveButton) {
    saveButton.disabled = state.cameraCalibration.configSaving || !textarea;
    saveButton.textContent = state.cameraCalibration.configSaving ? "保存中" : "保存配置";
  }
  if (resetButton) {
    resetButton.disabled = state.cameraCalibration.configSaving || !payload;
  }
  if (result) {
    if (state.cameraCalibration.configSaving) {
      result.textContent = "正在保存 camera_extrinsics.json";
    } else if (state.cameraCalibration.configDirty) {
      result.textContent = "配置已修改，尚未保存";
    } else if (state.cameraCalibration.statusError && !payload) {
      result.textContent = state.cameraCalibration.statusError;
    } else {
      const path = config?.path || payload?.extrinsics?.config?.path || "";
      result.textContent = path ? `已加载 ${path}` : "等待后端配置";
    }
  }
}

function renderCameraCalibrationServiceButton(payload = cameraCalibrationPayload()) {
  const button = $("#cameraExtrinsicsServiceButton");
  if (!button) return;
  const config = cameraCalibrationConfig(payload);
  const transforms = cameraCalibrationTransforms(config);
  const serviceStatus = cameraCalibrationServiceStatus(payload);
  const serviceLabel = cameraCalibrationServiceLabels[serviceStatus] || serviceStatus;
  const running = serviceStatus === "running" || serviceStatus === "external";
  const canUse = Boolean(config?.enabled && transforms.length && payload?.extrinsics?.serviceAvailable);
  button.textContent = state.cameraCalibration.serviceBusy
    ? "处理中"
    : running
      ? "重启外参发布"
      : "启动外参发布";
  button.disabled = state.cameraCalibration.serviceBusy || state.cameraCalibration.statusLoading || !canUse;
  if (!config?.enabled) {
    button.title = "先启用并保存 camera_extrinsics.json";
  } else if (!transforms.length) {
    button.title = "camera_extrinsics.json 中没有 transforms";
  } else if (!payload?.extrinsics?.serviceAvailable) {
    button.title = "后端尚未注册 camera_extrinsics 服务";
  } else {
    button.title = `当前状态：${serviceLabel}`;
  }
}

function renderCameraProjectionPreview(item) {
  const preview = $("#cameraProjectionPreview");
  if (!preview) return;
  if (!item) {
    preview.innerHTML = "<span>暂无投影质检图</span>";
    return;
  }
  const imageUrl = item.imageUrl || "";
  const summary = cameraProjectionPointSummary(item);
  const meta = [
    item.camera,
    item.cloud,
    summary,
    item.createdAt,
    item.targetFrame ? `target ${item.targetFrame}` : "",
    item.sourceFrame ? `source ${item.sourceFrame}` : "",
  ].filter(Boolean).join(" | ");
  preview.innerHTML = `
    ${imageUrl
      ? `<img src="${escapeHtml(imageUrl)}" alt="${escapeHtml(item.camera || "camera")} projection check">`
      : "<span>暂无预览图</span>"}
    <small>${escapeHtml(meta || item.imagePath || "")}</small>
  `;
}

function renderCameraCalibrationSampleQueue(payload = cameraCalibrationPayload()) {
  const table = $("#cameraCalibrationSampleTable");
  const progress = $("#cameraCalibrationSampleProgress");
  const samples = cameraCalibrationSamples(payload);
  const perCamera = cameraCalibrationPerCameraSamples(payload);
  const sampling = cameraCalibrationSampling(payload);
  const total = Number(sampling?.total) || 0;
  const totalTarget = Number(sampling?.totalTargetCount) || 72;
  if (progress) {
    const percent = totalTarget > 0 ? Math.min(100, Math.round(total * 100 / totalTarget)) : 0;
    progress.style.width = `${percent}%`;
  }
  if (!table) return;

  const cameras = Array.isArray(payload?.extrinsics?.cameras) ? payload.extrinsics.cameras : [
    { camera: "camera_l", displayName: "左相机" },
    { camera: "camera_r", displayName: "右相机" },
    { camera: "camera_f", displayName: "中间相机" },
  ];
  const rows = cameras.map((camera) => {
    const stats = perCamera[camera.camera] || {};
    const latest = stats.latest || samples.find((sample) => sample.camera === camera.camera) || null;
    const count = Number(stats.count) || 0;
    const target = Number(stats.targetCount || sampling?.targetCount || 24) || 24;
    const clearBusy = state.cameraCalibration.sampleClearBusyCamera === camera.camera;
    const calibrationSampleBusy = Boolean(state.cameraCalibration.sampleBusyCamera || state.cameraCalibration.sampleClearBusyCamera);
    const imageText = latest ? `${count}/${target} | ${formatCalibrationAge(latest.imageAgeMs)}` : `${count}/${target}`;
    const tfText = latest?.parentTfStamp ? latest.parentTfStamp : latest ? "已记录" : "等待";
    const cornersText = latest
      ? `${Number(latest.cornerCount) || 0}/${Number(latest.expectedCornerCount) || 0}`
      : "--";
    const rms = latest?.reprojectionRmsPx == null ? "" : ` | ${formatCalibrationSampleMetric(latest.reprojectionRmsPx, " px")}`;
    const canClear = Boolean(count > 0 && !calibrationSampleBusy);
    return `
      <div role="row">
        <span>${escapeHtml(camera.camera || "")}</span>
        <strong>${escapeHtml(imageText)}</strong>
        <strong>${escapeHtml(tfText || "--")}</strong>
        <strong>${escapeHtml(`${cornersText}${rms}`)}</strong>
        <span><button class="secondary-button calibration-table-button calibration-clear-button" type="button" data-camera-calibration-clear="${escapeHtml(camera.camera || "")}" ${canClear ? "" : "disabled"}>${clearBusy ? "清除中" : "清除"}</button></span>
      </div>
    `;
  }).join("");

  table.innerHTML = `
    <div role="row">
      <span role="columnheader">相机</span>
      <span role="columnheader">图像</span>
      <span role="columnheader">父级 TF</span>
      <span role="columnheader">角点</span>
      <span role="columnheader">操作</span>
    </div>
    ${rows}
  `;
}

function renderCameraCalibrationStatus(payload = cameraCalibrationPayload()) {
  const summary = cameraCalibrationStatusSummary(payload);
  setStateBadge("#cameraCalibrationStatusBadge", summary.label, summary.level);

  const config = cameraCalibrationConfig(payload);
  const transforms = cameraCalibrationTransforms(config);
  const cameras = Array.isArray(payload?.extrinsics?.cameras) ? payload.extrinsics.cameras : [];
  const allConfigured = cameras.length > 0 && cameras.every((camera) => camera.configured && camera.bridgeConfigured);
  if (!payload && state.cameraCalibration.statusLoading) {
    setStateBadge("#cameraCalibrationConfigBadge", "读取中", "idle");
  } else if (!payload) {
    setStateBadge("#cameraCalibrationConfigBadge", state.cameraCalibration.statusError ? "读取失败" : "未读取", state.cameraCalibration.statusError ? "danger" : "idle");
  } else if (!payload?.ok) {
    setStateBadge("#cameraCalibrationConfigBadge", "配置异常", "danger");
  } else if (!transforms.length || !allConfigured) {
    setStateBadge("#cameraCalibrationConfigBadge", "外参缺失", "warn");
  } else {
    setStateBadge("#cameraCalibrationConfigBadge", config?.enabled ? "已启用" : "未启用", config?.enabled ? "ok" : "warn");
  }

  const dependencies = Array.isArray(payload?.dependencies) ? payload.dependencies : [];
  const missingDeps = dependencies.filter((item) => item.required && !item.available);
  if (!payload && state.cameraCalibration.statusLoading) {
    setStateBadge("#cameraCalibrationDependencyBadge", "读取中", "idle");
  } else if (missingDeps.length) {
    setStateBadge("#cameraCalibrationDependencyBadge", `缺 ${missingDeps.length} 项`, "danger");
  } else if (dependencies.length) {
    setStateBadge("#cameraCalibrationDependencyBadge", "依赖可用", "ok");
  } else {
    setStateBadge("#cameraCalibrationDependencyBadge", "未读取", "idle");
  }

  if (!payload && state.cameraCalibration.statusLoading) {
    setStateBadge("#cameraCalibrationCaptureBadge", "读取中", "idle");
  } else if (!payload) {
    setStateBadge("#cameraCalibrationCaptureBadge", state.cameraCalibration.statusError ? "读取失败" : "未读取", state.cameraCalibration.statusError ? "danger" : "idle");
  } else if (missingDeps.length) {
    setStateBadge("#cameraCalibrationCaptureBadge", "依赖缺失", "danger");
  } else if (state.cameraCalibration.sampleBusyCamera) {
    setStateBadge("#cameraCalibrationCaptureBadge", "采样中", "warn");
  } else if (state.cameraCalibration.sampleClearBusyCamera) {
    setStateBadge("#cameraCalibrationCaptureBadge", "清除中", "warn");
  } else {
    const sampling = cameraCalibrationSampling(payload);
    const total = Number(sampling?.total) || 0;
    const target = Number(sampling?.totalTargetCount) || 72;
    setStateBadge("#cameraCalibrationCaptureBadge", total > 0 ? `${total} / ${target}` : "可采样", total >= target ? "ok" : total > 0 ? "warn" : "idle");
  }

  renderCameraCalibrationCameraList(cameras, payload);
  renderCameraCalibrationSampleQueue(payload);
  renderCameraCalibrationTfPreview(payload);
  renderCameraCalibrationEditor(payload);
  renderCameraCalibrationServiceButton(payload);
  renderCameraCalibrationSolve(payload);
  const latestProjection = Array.isArray(payload?.projectionChecks) ? payload.projectionChecks[0] : null;
  if (latestProjection) renderCameraProjectionPreview(latestProjection);
}

async function refreshCameraCalibrationStatus(options = {}) {
  if (state.cameraCalibration.statusLoading && !options.force) return state.cameraCalibration.statusPayload;
  state.cameraCalibration.statusLoading = true;
  state.cameraCalibration.statusError = "";
  renderCameraCalibrationStatus();
  try {
    const response = await fetch("/api/calibration/status", { cache: "no-store" });
    const payload = await response.json().catch(() => ({}));
    if (!payload || !Object.keys(payload).length) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    state.cameraCalibration.statusPayload = payload;
    state.cameraCalibration.statusError = response.ok && payload.ok ? "" : (payload.detail || `HTTP ${response.status}`);
    return payload;
  } catch (error) {
    state.cameraCalibration.statusError = error.message || "相机标定状态读取失败";
    if (!options.silent) addLog("相机标定", `状态读取失败：${state.cameraCalibration.statusError}`);
    return null;
  } finally {
    state.cameraCalibration.statusLoading = false;
    renderCameraCalibrationStatus();
  }
}

function readCameraExtrinsicsEditorConfig() {
  const textarea = $("#cameraExtrinsicsConfigEditor");
  const raw = textarea ? textarea.value.trim() : "";
  if (!raw) return { enabled: false, transforms: [] };
  try {
    return JSON.parse(raw);
  } catch (error) {
    setStateBadge("#cameraCalibrationConfigBadge", "JSON 错误", "danger");
    setText("#cameraExtrinsicsConfigResult", `JSON 解析失败：${error.message}`);
    throw error;
  }
}

function markCameraExtrinsicsConfigDirty() {
  state.cameraCalibration.configDirty = true;
  renderCameraCalibrationEditor();
}

function syncCameraExtrinsicsEnabledFromToggle() {
  const toggle = $("#cameraExtrinsicsEnabledToggle");
  const textarea = $("#cameraExtrinsicsConfigEditor");
  if (!toggle || !textarea) return;
  let config;
  try {
    config = readCameraExtrinsicsEditorConfig();
  } catch (error) {
    return;
  }
  config.enabled = toggle.checked;
  textarea.value = formatCameraCalibrationConfig(config);
  state.cameraCalibration.configDirty = true;
  renderCameraCalibrationStatus();
}

function resetCameraExtrinsicsEditor() {
  state.cameraCalibration.configDirty = false;
  renderCameraCalibrationStatus();
}

async function saveCameraExtrinsicsConfig() {
  if (state.cameraCalibration.configSaving) return;
  let config;
  try {
    config = readCameraExtrinsicsEditorConfig();
  } catch (error) {
    return;
  }
  state.cameraCalibration.configSaving = true;
  renderCameraCalibrationStatus();
  try {
    const response = await fetch("/api/calibration/camera-extrinsics", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(config),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok) {
      throw new Error(payload.detail || `HTTP ${response.status}`);
    }
    if (state.cameraCalibration.statusPayload?.extrinsics && payload.config) {
      state.cameraCalibration.statusPayload.extrinsics.config = payload.config;
    }
    state.cameraCalibration.configDirty = false;
    setText("#cameraExtrinsicsConfigResult", payload.detail || "配置已保存");
    addLog("相机标定", "camera_extrinsics.json 已保存");
    await refreshCameraCalibrationStatus({ silent: true, force: true });
  } catch (error) {
    setText("#cameraExtrinsicsConfigResult", `保存失败：${error.message}`);
    addLog("相机标定", `camera_extrinsics.json 保存失败：${error.message}`);
  } finally {
    state.cameraCalibration.configSaving = false;
    renderCameraCalibrationStatus();
  }
}

async function requestCameraExtrinsicsServiceAction() {
  if (state.cameraCalibration.serviceBusy) return;
  const payload = cameraCalibrationPayload() || await refreshCameraCalibrationStatus({ silent: true, force: true });
  const config = cameraCalibrationConfig(payload);
  if (!config?.enabled || !cameraCalibrationTransforms(config).length || !payload?.extrinsics?.serviceAvailable) {
    renderCameraCalibrationServiceButton(payload);
    return;
  }
  const status = cameraCalibrationServiceStatus(payload);
  const action = status === "running" || status === "external" ? "restart" : "start";
  state.cameraCalibration.serviceBusy = true;
  renderCameraCalibrationServiceButton(payload);
  addLog("相机标定", action === "restart" ? "请求重启 camera_extrinsics TF 发布" : "请求启动 camera_extrinsics TF 发布");
  try {
    const response = await fetch(`/api/runtime/services/camera_extrinsics/${action}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: "{}",
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok || !result.ok) {
      throw new Error(result.detail || `HTTP ${response.status}`);
    }
    addLog("相机标定", `camera_extrinsics 服务动作完成：${result.code}`);
    await refreshCameraCalibrationStatus({ silent: true, force: true });
  } catch (error) {
    addLog("相机标定", `camera_extrinsics 服务动作失败：${error.message}`);
    setText("#cameraExtrinsicsConfigResult", `服务动作失败：${error.message}`);
  } finally {
    state.cameraCalibration.serviceBusy = false;
    renderCameraCalibrationStatus();
  }
}

async function requestCameraCalibrationSample(cameraKey) {
  const camera = String(cameraKey || "").trim();
  if (!camera || state.cameraCalibration.sampleBusyCamera || state.cameraCalibration.sampleClearBusyCamera) return;
  const payload = cameraCalibrationPayload() || await refreshCameraCalibrationStatus({ silent: true, force: true });
  if (!payload?.ok || !cameraCalibrationDependenciesReady(payload)) {
    renderCameraCalibrationStatus(payload);
    return;
  }

  state.cameraCalibration.sampleBusyCamera = camera;
  renderCameraCalibrationStatus(payload);
  addLog("相机标定", `开始采集 ${camera} 标定样本`);

  try {
    const response = await fetch("/api/calibration/sample", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        camera,
        board: readCameraCalibrationBoard(),
        baseFrame: "base_link",
        waitSec: 1.0,
      }),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok || !result.ok) {
      const error = new Error(result.detail || `HTTP ${response.status}`);
      error.payload = result;
      throw error;
    }
    if (state.cameraCalibration.statusPayload && result.sampling) {
      state.cameraCalibration.statusPayload.sampling = result.sampling;
    }
    const corners = result.sample
      ? `${Number(result.sample.cornerCount) || 0}/${Number(result.sample.expectedCornerCount) || 0}`
      : "";
    addLog("相机标定", `${camera} 标定样本已保存${corners ? `，角点 ${corners}` : ""}`);
    await refreshCameraCalibrationStatus({ silent: true, force: true });
  } catch (error) {
    const detail = error.payload?.detail || error.message || "采样失败";
    addLog("相机标定", `${camera} 标定样本采集失败：${detail}`);
  } finally {
    state.cameraCalibration.sampleBusyCamera = "";
    renderCameraCalibrationStatus();
  }
}

async function requestCameraCalibrationClearSamples(cameraKey) {
  const camera = String(cameraKey || "").trim();
  if (!camera || state.cameraCalibration.sampleBusyCamera || state.cameraCalibration.sampleClearBusyCamera) return;
  const payload = cameraCalibrationPayload() || await refreshCameraCalibrationStatus({ silent: true, force: true });
  const sampleStats = cameraCalibrationPerCameraSamples(payload)[camera] || {};
  const sampleCount = Number(sampleStats.count) || 0;
  if (sampleCount <= 0) return;
  if (!window.confirm(`清除 ${camera} 的 ${sampleCount} 个标定样本？`)) return;

  state.cameraCalibration.sampleClearBusyCamera = camera;
  renderCameraCalibrationStatus(payload);
  addLog("相机标定", `开始清除 ${camera} 标定样本`);

  try {
    const response = await fetch("/api/calibration/samples/clear", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ camera }),
    });
    const result = await response.json().catch(() => ({}));
    if (!response.ok || !result.ok) {
      const error = new Error(result.detail || `HTTP ${response.status}`);
      error.payload = result;
      throw error;
    }
    if (state.cameraCalibration.statusPayload && result.sampling) {
      state.cameraCalibration.statusPayload.sampling = result.sampling;
    }
    addLog("相机标定", `${camera} 标定样本已清除：${Number(result.deletedSampleCount) || 0} 个样本`);
    await refreshCameraCalibrationStatus({ silent: true, force: true });
  } catch (error) {
    const detail = error.payload?.detail || error.message || "清除失败";
    addLog("相机标定", `${camera} 标定样本清除失败：${detail}`);
  } finally {
    state.cameraCalibration.sampleClearBusyCamera = "";
    renderCameraCalibrationStatus();
  }
}

async function requestCameraCalibrationSolve() {
  if (state.cameraCalibration.solveBusy) return;
  const payload = cameraCalibrationPayload() || await refreshCameraCalibrationStatus({ silent: true, force: true });
  if (!payload?.ok || !cameraCalibrationDependenciesReady(payload)) {
    renderCameraCalibrationStatus(payload);
    return;
  }

  const camera = selectedCameraCalibrationSolveCamera();
  const method = selectedCameraCalibrationMethod();
  state.cameraCalibration.solveBusy = true;
  state.cameraCalibration.solveResult = null;
  renderCameraCalibrationStatus(payload);
  addLog("相机标定", `开始求解 ${camera === "all" ? "全部相机" : camera} 外参，方法 ${method}`);

  try {
    const requestBody = {
      camera,
      method,
      minSamples: 12,
      waitSec: 0.5,
      save: true,
    };
    if (camera === "all") requestBody.enable = true;
    const response = await fetch("/api/calibration/solve", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(requestBody),
    });
    const result = await response.json().catch(() => ({}));
    state.cameraCalibration.solveResult = result;
    if (!response.ok || !result.ok) {
      const error = new Error(result.detail || `HTTP ${response.status}`);
      error.payload = result;
      throw error;
    }
    state.cameraCalibration.configDirty = false;
    if (state.cameraCalibration.statusPayload?.extrinsics && result.config) {
      state.cameraCalibration.statusPayload.extrinsics.config = result.config;
    }
    const solved = Array.isArray(result.solvedCameras) ? result.solvedCameras.join(", ") : camera;
    addLog("相机标定", `外参求解完成：${solved}`);
    if (Array.isArray(result.warnings) && result.warnings.length) {
      addLog("相机标定", result.warnings[0]);
    }
    await refreshCameraCalibrationStatus({ silent: true, force: true });
  } catch (error) {
    const result = error.payload || state.cameraCalibration.solveResult || {};
    const failed = Array.isArray(result.failedCameras) && result.failedCameras.length
      ? ` (${result.failedCameras.join(", ")})`
      : "";
    const detail = result.detail || error.message || "求解失败";
    setText("#cameraExtrinsicsConfigResult", `求解失败：${detail}${failed}`);
    addLog("相机标定", `外参求解失败：${detail}${failed}`);
  } finally {
    state.cameraCalibration.solveBusy = false;
    renderCameraCalibrationStatus();
  }
}

async function copyCameraExtrinsicsConfig() {
  const textarea = $("#cameraExtrinsicsConfigEditor");
  const payload = textarea?.value || $("#cameraCalibrationTfPreview")?.textContent || "";
  if (!payload) return;
  try {
    await navigator.clipboard.writeText(payload);
    addLog("相机标定", "外参配置 JSON 已复制");
  } catch (error) {
    if (textarea) {
      textarea.focus();
      textarea.select();
      document.execCommand("copy");
      addLog("相机标定", "外参配置 JSON 已复制");
    } else {
      addLog("相机标定", `外参配置复制失败：${error.message}`);
    }
  }
}

function setCameraProjectionBusy(busy) {
  state.cameraCalibration.projectionBusy = Boolean(busy);
  const button = $("#cameraProjectionCheckButton");
  if (button) {
    button.disabled = state.cameraCalibration.projectionBusy;
    button.textContent = state.cameraCalibration.projectionBusy ? "生成中" : "保存投影质检图";
  }
}

function cameraProjectionPointSummary(payload) {
  const projected = Number(payload?.projectedPointCount);
  const input = Number(payload?.inputPointCount);
  if (!Number.isFinite(projected) || !Number.isFinite(input)) return "";
  return `${projected.toLocaleString("zh-CN")} / ${input.toLocaleString("zh-CN")} 点`;
}

async function requestCameraProjectionCheck() {
  if (state.cameraCalibration.projectionBusy) return;

  const camera = $("#cameraProjectionCheckCamera")?.value || "camera_f";
  const cloud = "rslidar_points";
  setCameraProjectionBusy(true);
  setStateBadge("#cameraProjectionCheckBadge", "生成中", "warn");
  setText("#cameraProjectionCheckResult", `${camera} / ${cloud}`);

  try {
    const response = await fetch("/api/calibration/camera-projection-check", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        camera,
        cloud,
        maxPoints: 60000,
        waitSec: 1.0,
      }),
    });
    const payload = await response.json().catch(() => ({}));
    if (!response.ok || !payload.ok) {
      const error = new Error(payload.detail || `HTTP ${response.status}`);
      error.payload = payload;
      throw error;
    }

    const summary = cameraProjectionPointSummary(payload);
    const projected = Number(payload.projectedPointCount);
    const level = projected === 0 ? "warn" : "ok";
    const badge = projected === 0 ? "无点入图" : "已保存";
    setStateBadge("#cameraProjectionCheckBadge", badge, level);
    renderCameraProjectionPreview(payload);
    setText("#cameraProjectionCheckResult", [payload.imageUrl || payload.imagePath, summary].filter(Boolean).join(" | "));
    addLog("相机标定", `投影质检图已保存：${payload.imagePath || payload.detail}`);
    refreshCameraCalibrationStatus({ silent: true, force: true });
  } catch (error) {
    const payload = error.payload || {};
    const detail = payload.detail || error.message || "投影质检图生成失败";
    setStateBadge("#cameraProjectionCheckBadge", "失败", "danger");
    setText("#cameraProjectionCheckResult", detail);
    addLog("相机标定", `投影质检图生成失败：${detail}`);
  } finally {
    setCameraProjectionBusy(false);
  }
}

function bindEvents() {
  $$(".nav-item").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));
  $$("[data-view-jump]").forEach((button) => button.addEventListener("click", () => showView(button.dataset.viewJump)));

  $("#stateMachineNodeLibrary")?.addEventListener("click", handleStateMachineLibraryClick);
  $("#stateMachineNodeLibrary")?.addEventListener("dragstart", handleStateMachineLibraryDragStart);
  $("#stateMachineCanvas")?.addEventListener("click", handleStateMachineCanvasClick);
  $("#stateMachineCanvas")?.addEventListener("dblclick", handleStateMachineCanvasDoubleClick);
  $("#stateMachineCanvas")?.addEventListener("dragover", handleStateMachineCanvasDragOver);
  $("#stateMachineCanvas")?.addEventListener("drop", handleStateMachineCanvasDrop);
  $("#stateMachineCanvas")?.addEventListener("pointerdown", startStateMachineNodeDrag);
  document.addEventListener("pointermove", updateStateMachineNodeDrag);
  document.addEventListener("pointerup", finishStateMachineNodeDrag);
  $$("[data-sm-mode]").forEach((button) => button.addEventListener("click", () => setStateMachineMode(button.dataset.smMode)));
  $("#stateMachineNameInput")?.addEventListener("change", (event) => updateStateMachineName(event.currentTarget.value));
  $("#stateMachineClearButton")?.addEventListener("click", clearStateMachine);
  $("#stateMachineCopyJsonButton")?.addEventListener("click", copyStateMachineJson);
  $("#stateMachineGraphSaveButton")?.addEventListener("click", saveStateMachineGraphToBackend);
  $("#stateMachineGraphLoadButton")?.addEventListener("click", loadStateMachineGraphFromBackend);
  $("#stateMachineGraphDeleteButton")?.addEventListener("click", deleteStateMachineGraphFromBackend);
  $("#stateMachineGraphSelect")?.addEventListener("change", (event) => {
    state.stateMachine.selectedGraphId = event.currentTarget.value;
    renderStateMachine();
  });
  $("#stateMachineRealRunButton")?.addEventListener("click", startStateMachineRealRun);
  $("#stateMachineRealLoopButton")?.addEventListener("click", () => startStateMachineRealRun({ loop: true }));
  $("#stateMachineRealStopButton")?.addEventListener("click", stopStateMachineRealRun);
  $("#stateMachineEventLibrary")?.addEventListener("click", handleStateMachineEventLibraryClick);
  $("#stateMachineEventLibrary")?.addEventListener("dragstart", handleStateMachineEventLibraryDragStart);
  $("#stateMachineEventSequenceList")?.addEventListener("click", handleEventSequenceListClick);
  $("#stateMachineEventSequenceList")?.addEventListener("dragstart", handleEventSequenceListDragStart);
  $("#stateMachineEventSequenceList")?.addEventListener("dragover", handleEventSequenceListDragOver);
  $("#stateMachineEventSequenceList")?.addEventListener("drop", handleEventSequenceListDrop);
  $("#stateMachineEventDetail")?.addEventListener("click", handleEventSequenceDetailClick);
  $("#eventSequenceNameInput")?.addEventListener("change", (event) => updateEventSequenceName(event.currentTarget.value));
  $("#eventSequenceSelect")?.addEventListener("change", (event) => {
    state.stateMachine.eventSequence.selectedSequenceId = event.currentTarget.value;
    renderStateMachine();
  });
  $("#eventSequenceLoadButton")?.addEventListener("click", loadEventSequenceFromBackend);
  $("#eventSequenceDeleteButton")?.addEventListener("click", deleteEventSequenceFromBackend);
  $("#eventSequenceClearButton")?.addEventListener("click", clearEventSequence);
  $("#eventSequenceSaveButton")?.addEventListener("click", saveEventSequenceToBackend);
  $("#eventSequenceRunButton")?.addEventListener("click", startEventSequenceRun);
  $("#eventSequenceLoopButton")?.addEventListener("click", () => startEventSequenceRun({ loop: true }));
  $("#eventSequenceStopButton")?.addEventListener("click", stopEventSequenceRun);
  $("#stateMachineModalClose")?.addEventListener("click", closeStateMachineModal);
  $("#stateMachineModalCancelButton")?.addEventListener("click", closeStateMachineModal);
  $("#stateMachineModalSaveButton")?.addEventListener("click", submitStateMachineModal);
  $("#stateMachineModalForm")?.addEventListener("change", handleStateMachineModalChange);
  $("#stateMachineModal")?.addEventListener("click", (event) => {
    if (event.target === event.currentTarget) closeStateMachineModal();
  });
  $("#stateMachineModalForm")?.addEventListener("submit", (event) => {
    event.preventDefault();
    submitStateMachineModal();
  });

  $$(".segmented button").forEach((button) => {
    button.addEventListener("click", () => {
      const group = button.closest(".segmented");
      if (group) group.querySelectorAll("button").forEach((item) => item.classList.toggle("is-active", item === button));
      if (button.dataset.robotWorkMode) {
        setRobotWorkMode(button.dataset.robotWorkMode);
      }
      if (button.dataset.sensorTab) {
        $$(".sensor-panel").forEach((panel) => panel.classList.toggle("is-active", panel.dataset.sensorPanel === button.dataset.sensorTab));
      }
      if (button.dataset.cameraKindTab) {
        setCameraKind(button.dataset.cameraKindTab);
      }
      if (button.dataset.sensorTab === "lidar") {
        window.setTimeout(resizeLidarViewer, 0);
      }
    });
  });

  $("#runSelfCheckButton").addEventListener("click", runSelfCheck);
  $("#rerunProblemChecksButton").addEventListener("click", rerunProblemChecks);
  $("#canStatus").addEventListener("click", () => activateCanInterface(currentCanCheckResult(), { confirm: false }));
  $("#piperRuntimeStatus").addEventListener("click", togglePiperRuntime);
  $("#piperRemoteRuntimeStatus").addEventListener("click", togglePiperRemoteRuntime);
  $("#liftingRuntimeStatus").addEventListener("click", toggleLiftingRuntime);
  $("#chassisRuntimeStatus").addEventListener("click", toggleChassisRuntime);
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
  $("#cameraCalibrationRefreshButton")?.addEventListener("click", () => refreshCameraCalibrationStatus({ force: true }));
  $("#calibrationCameraList")?.addEventListener("click", (event) => {
    const button = event.target.closest("[data-camera-calibration-sample]");
    if (button) {
      requestCameraCalibrationSample(button.dataset.cameraCalibrationSample);
      return;
    }
    const clearButton = event.target.closest("[data-camera-calibration-clear]");
    if (clearButton) requestCameraCalibrationClearSamples(clearButton.dataset.cameraCalibrationClear);
  });
  $("#cameraCalibrationSampleTable")?.addEventListener("click", (event) => {
    const clearButton = event.target.closest("[data-camera-calibration-clear]");
    if (clearButton) requestCameraCalibrationClearSamples(clearButton.dataset.cameraCalibrationClear);
  });
  $("#cameraExtrinsicsServiceButton")?.addEventListener("click", requestCameraExtrinsicsServiceAction);
  $("#cameraExtrinsicsSaveButton")?.addEventListener("click", saveCameraExtrinsicsConfig);
  $("#cameraExtrinsicsResetButton")?.addEventListener("click", resetCameraExtrinsicsEditor);
  $("#cameraExtrinsicsCopyButton")?.addEventListener("click", copyCameraExtrinsicsConfig);
  $("#cameraExtrinsicsEnabledToggle")?.addEventListener("change", syncCameraExtrinsicsEnabledFromToggle);
  $("#cameraExtrinsicsConfigEditor")?.addEventListener("input", markCameraExtrinsicsConfigDirty);
  $("#cameraCalibrationSolveButton")?.addEventListener("click", requestCameraCalibrationSolve);
  $("#cameraCalibrationSolveCamera")?.addEventListener("change", () => renderCameraCalibrationSolve());
  $("#cameraProjectionCheckButton")?.addEventListener("click", requestCameraProjectionCheck);
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
  $("#localizationMapSelect")?.addEventListener("change", (event) => selectLocalizationMap(event.currentTarget.value));
  $("#localizationBackendSelect")?.addEventListener("change", (event) => selectLocalizationBackend(event.currentTarget.value));
  $("#localizationLoadMapButton")?.addEventListener("click", loadLocalizationMapFrame);
  $("#localizationStartButton")?.addEventListener("click", startLocalization);
  $("#localizationStopButton")?.addEventListener("click", stopLocalization);
  $("#localizationRestartButton")?.addEventListener("click", restartLocalization);
  $("#navigationGoalForm")?.addEventListener("input", updateNavigationGoalFromInputs);
  $("#navigationParamsForm")?.addEventListener("input", updateNavigationParamsFromInputs);
  $("#navigationParamsForm")?.addEventListener("change", updateNavigationParamsFromInputs);
  $("#navigationGoalEditButton")?.addEventListener("click", () => setNavigationGoalEditMode(!state.navigation.goalEditMode));
  $("#navigationGoalClearButton")?.addEventListener("click", clearNavigationTarget);
  $("#navigationPlanButton")?.addEventListener("click", planNavigationPath);
  $("#navigationStartButton")?.addEventListener("click", startNavigation);
  $("#navigationPauseButton")?.addEventListener("click", pauseNavigation);
  $("#navigationResumeButton")?.addEventListener("click", resumeNavigation);
  $("#navigationCancelButton")?.addEventListener("click", cancelNavigation);
  $$("[data-robot-modal-toggle]").forEach((button) => {
    button.addEventListener("click", () => toggleRobotModal(button.dataset.robotModalToggle));
  });
  $("#robotWorkModalClose")?.addEventListener("click", closeRobotModal);
  $("#robotWorkModal")?.addEventListener("click", (event) => {
    if (event.target === event.currentTarget) closeRobotModal();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && state.robotWork.modal) {
      event.preventDefault();
      closeRobotModal();
    }
  });
  $("#mappingConfigForm").addEventListener("input", () => {
    Object.assign(state.mapping, readMappingSettings());
    renderMappingStatus();
  });
  $("#initialPoseForm")?.addEventListener("input", updateInitialPoseFromInputs);
  $("#initialPoseEditButton")?.addEventListener("click", () => setInitialPoseEditMode(!state.localization.initialPoseEditMode));
  $("#initialPosePublishButton")?.addEventListener("click", publishInitialPose);
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
        requestPlaybackAction("stop").catch((error) => addLog("回放", `数据回放路径变更停止失败：${error.message}`));
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
  const alertStatus = $("#alertStatus");
  if (alertStatus) {
    alertStatus.addEventListener("mouseenter", (event) => showAlertTooltip(event.currentTarget));
    alertStatus.addEventListener("mouseleave", hideRichTooltip);
  }

  $$("[data-action]").forEach((button) => {
    button.addEventListener("click", () => {
      const action = button.dataset.action;
      if (action === "self-check") {
        showView("self-check");
      }
      if (action === "homing") {
        showView("homing");
        startHoming();
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
    if (button.dataset.checkAction === "retry") {
      addLog(item.source, `复查检查项：${item.name}`);
      runSelfCheck();
    }
    if (button.dataset.checkAction === "activate" && item.name === "CAN 接口") {
      activateCanInterface(item);
    }
  });
  $("#runtimePrepTable").addEventListener("mouseover", (event) => {
    const row = event.target.closest(".check-row");
    if (!row || !$("#runtimePrepTable").contains(row)) return;
    showCheckTooltip(row);
  });
  $("#runtimePrepTable").addEventListener("mouseout", (event) => {
    const row = event.target.closest(".check-row");
    if (!row || row.contains(event.relatedTarget)) return;
    hideRichTooltip();
  });
  $("#runtimePrepTable").addEventListener("click", (event) => {
    const button = event.target.closest("[data-runtime-action]");
    if (!button) return;
    if (button.dataset.runtimeAction === "start") {
      startRuntimePrepService(button.dataset.runtimeKey);
    }
    if (button.dataset.runtimeAction === "view") {
      showView(button.dataset.runtimeView);
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
    renderMappingSpeedSummary();
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
}

function init() {
  const activePanel = $(".view.is-active");
  document.body.dataset.activeView = activePanel ? activePanel.dataset.viewPanel : "self-check";
  const hadLocalDraft = loadStateMachineState();
  loadEventSequenceState();
  refreshStateMachineLibrary({ silent: true });
  if (hadLocalDraft) {
    refreshStateMachineGraphs({ silent: true });
  } else {
    restoreStateMachineDraftFromBackend();
  }
  refreshStateMachineEventSequences({ silent: true });
  bindEvents();
  renderHealth();
  renderSelfCheck();
  renderAdvice();
  renderHomingSteps();
  renderInferenceStatus();
  renderInferenceMask();
  refreshInferenceStatus();
  loadInferenceChassisLimits();
  renderPreflight();
  renderDeviceBaseMetrics();
  renderDeviceControls();
  renderPiperRuntime();
  renderPiperRemoteRuntime();
  renderLiftingRuntime();
  renderChassisRuntime();
  renderCameraRuntime();
  renderLidarRuntime();
  renderActionLocks();
  renderCameraFrames();
  renderLidarCloudStatus();
  renderCameraCalibrationStatus();
  renderPlayback();
  renderStateMachine();
  refreshPlaybackStatus({ silent: true });
  renderRobotViewStatus();
  renderMappingStatus();
  renderLocalizationStatus();
  renderNavigationStatus();
  fetchRobotModels({ silent: true });
  refreshMappingStatus({ silent: true });
  refreshLocalizationStatus({ silent: true });
  if (document.body.dataset.activeView === "camera-calibration") {
    refreshCameraCalibrationStatus({ silent: true });
  }
  initializeRobotViewer();
  addLog("系统", "Robot Station 前端原型已加载");
  addLog("ROS", "等待接入真实 ROS 状态");
  addLog("相机", "相机压缩图预览等待图像帧");
  fetchCachedSelfCheckStatus({ silent: true });
  refreshCanInterfaceStatus({ silent: true, updateSelfCheck: false });
  fetchPiperRuntimeStatus({ silent: true });
  fetchPiperRemoteRuntimeStatus({ silent: true });
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
  window.setInterval(() => runBackgroundPoll(() => fetchPiperRuntimeStatus({ silent: true })), 3000);
  window.setInterval(() => runBackgroundPoll(() => fetchPiperRemoteRuntimeStatus({ silent: true })), 3000);
  window.setInterval(() => runBackgroundPoll(() => fetchLiftingRuntimeStatus({ silent: true })), 3000);
  window.setInterval(() => runBackgroundPoll(() => fetchChassisRuntimeStatus({ silent: true })), 3000);
  window.setInterval(() => runBackgroundPoll(() => fetchCameraRuntimeStatus({ silent: true })), 3000);
  window.setInterval(() => {
    if (cameraPreviewEnabled()) runBackgroundPoll(() => fetchCameraFrames({ silent: true }));
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
