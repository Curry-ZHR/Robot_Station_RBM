export const VIEWS = [
  ['inference', '推理工作台', 'sparkles', '任务模型与全身执行'],
  ['startup', '自检与启动', 'list-checks', '逐步准备运行环境'],
  ['teleop', 'SONIC 遥操作', 'gamepad-2', '仿真与真机遥操作'],
  ['machine', '整机管理', 'server', '相机接入与数据导出'],
  ['body', '全身控制', 'person-standing', '29 维身体关节'],
  ['sensors', '传感器', 'scan-eye', '三路相机与数据状态'],
  ['collection', '数据采集', 'circle-dot', '遥操作录制与片段管理'],
  ['playback', '数据回放', 'clapperboard', '视频、姿态与动作曲线'],
  ['conversion', '数据转换', 'repeat-2', 'HDF5 与 LeRobot 导出'],
  ['connections', '连接与诊断', 'cable', '参数方案、话题与恢复'],
  ['workflow', '状态机编辑器', 'workflow', '编排任务与运行流程'],
];
export const CAMERAS = [
  { id: 'head', label: '头部相机', short: 'HEAD', icon: 'scan-eye' },
  { id: 'left_wrist', label: '左腕相机', short: 'LEFT WRIST', icon: 'hand' },
  { id: 'right_wrist', label: '右腕相机', short: 'RIGHT WRIST', icon: 'hand' },
];
export const SERVICE_DEFS = [
  ['docker', 'SONIC 容器', 'container', 'GPU 与模型运行环境'],
  ['pc_service', 'XRoboToolkit', 'radio-tower', 'PICO 连接与本机 SDK'],
  ['controller', 'SONIC 控制器', 'cpu', '全身策略与机器人执行'],
  ['cameras', '相机接入', 'camera', '接收头部与左右腕视频'],
  ['exporter', '数据导出', 'database', '片段保存与 LeRobot 输出'],
];
export const STAGES = [
  ['environment', '环境自检', '主机、GPU、模型与存储'],
  ['runtime', '准备 SONIC', '容器与控制运行时'],
  ['sensors', '相机就绪', '三路视频与帧时间'],
  ['input', '输入源就绪', '任务模型或 PICO 追踪'],
  ['robot', '机器人反馈', '只读连接与状态新鲜度'],
];
export const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
export const clone = value => JSON.parse(JSON.stringify(value));
export const finite = value => typeof value === 'number' && Number.isFinite(value);
export const clock = value => value && Number.isFinite(Date.parse(value)) ? new Intl.DateTimeFormat('zh-CN', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit', timeZone: 'Asia/Shanghai' }).format(new Date(value)) : '--';
export const day = () => new Intl.DateTimeFormat('en-CA', { timeZone: 'Asia/Shanghai', year: 'numeric', month: '2-digit', day: '2-digit' }).format(new Date());
export const duration = seconds => `${String(Math.floor(Math.max(0, seconds || 0) / 60)).padStart(2, '0')}:${String(Math.floor(Math.max(0, seconds || 0) % 60)).padStart(2, '0')}`;
export const degree = rad => finite(rad) ? (rad * 180 / Math.PI).toFixed(1) : '--';
export const uid = () => globalThis.crypto?.randomUUID?.() || `ui-${Date.now()}-${Math.random().toString(16).slice(2)}`;
export const fresh = (value, maxAge = 5000, now = Date.now()) => {
  const time = Date.parse(value?.observed_at || '');
  return Number.isFinite(time) && now - time >= -2000 && now - time <= maxAge && value?.stale !== true;
};
export function batteryReading(snapshot, now = Date.now()) {
  const b = snapshot?.battery || {};
  const valid = snapshot?.robot?.connected === true && fresh(snapshot.robot, 5000, now) && fresh(b, 15000, now)
    && finite(b.percent) && b.percent >= 0 && b.percent <= 100;
  return { ...b, percent: valid ? b.percent : null, valid, tone: !valid ? 'muted' : b.percent <= (b.critical_percent ?? 10) ? 'danger' : b.percent <= (b.low_percent ?? 20) ? 'warning' : 'success' };
}
export function safeMediaURL(value) {
  if (typeof value !== 'string' || !value) return '';
  try { const url = new URL(value, globalThis.location?.origin || 'http://localhost'); return ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password ? url.href : ''; } catch { return ''; }
}
export function namedJointValues(snapshot, profile) {
  const rows = snapshot?.robot?.joints;
  if (!snapshot?.robot?.connected || !fresh(snapshot.robot) || !Array.isArray(rows)) return null;
  const map = new Map(rows.map(row => [row.name, row.position_rad]));
  const values = profile.body_joints.map(name => map.get(name));
  return values.every(finite) ? values : null;
}
export function emptySnapshot() {
  return { source: 'unavailable', backend_connected: false, observed_at: null, capabilities: { commands: [] },
    robot: { connected: false, owner: null, mode: 'OFF', observed_at: null, joints: [] }, battery: { percent: null },
    services: {}, sonic: {}, pico: {}, cameras: [], model: { connected: false, state: 'disconnected', steps: 0 },
    collection: { recording: false, prepared: false, elapsed_seconds: 0 }, interlocks: {}, checks: [], events: [],
    deployment: { state: 'idle', steps: [] }, workflow: {state:'idle',node_states:{}}, totals: { episodes: 0, datasets: 0, demo_episodes: 0 }, groups: [] };
}
export function normalizeSnapshot(raw) {
  const base = emptySnapshot();
  if (!raw || typeof raw !== 'object' || Array.isArray(raw)) return base;
  for (const key of ['robot', 'battery', 'model', 'collection', 'interlocks', 'deployment', 'workflow', 'totals', 'capabilities']) base[key] = { ...base[key], ...(raw[key] || {}) };
  for (const key of ['source', 'backend_connected', 'observed_at', 'message', 'output_root', 'services', 'revision', 'active_task', 'access', 'camera_source', 'mode', 'manual', 'sonic', 'pico']) if (raw[key] != null) base[key] = raw[key];
  for (const key of ['cameras', 'events', 'checks', 'groups']) base[key] = Array.isArray(raw[key]) ? raw[key].filter(row=>row&&typeof row==='object'&&!Array.isArray(row)) : [];
  base.robot.joints = Array.isArray(base.robot.joints)?base.robot.joints.filter(row=>row&&typeof row==='object'):[];
  if(!base.services||typeof base.services!=='object'||Array.isArray(base.services))base.services={};
  base.capabilities.commands = Array.isArray(base.capabilities.commands) ? base.capabilities.commands : [];
  return base;
}
export function legacySnapshot(data) {
  const snapshot = emptySnapshot(), status = data?.status || {};
  snapshot.source = 'legacy-readonly'; snapshot.backend_connected = false; snapshot.observed_at = data?.generated_at || null;
  snapshot.message = '数据目录已连接，设备与执行接口待接入';
  snapshot.groups = data?.groups || []; snapshot.totals = { ...snapshot.totals, ...data?.totals };
  snapshot.output_root = status.output_root || '';
  snapshot.checks = (status.prerequisites || []).map(row => ({ id: row.id, label: row.label, status: row.ok ? 'passed' : 'blocked', detail: row.detail, scope: '采集', source: '现有采集服务' }));
  snapshot.collection = { ...snapshot.collection, recording: status.recording === true, prepared: status.session_running === true, elapsed_seconds: status.elapsed_seconds || 0 };
  // A listening port is deliberately not promoted to a camera frame or fresh robot telemetry.
  return snapshot;
}
const CONTROL_INTERLOCKS = { 'robot.initialize':'can_initialize', 'inference.start': 'can_infer', 'collection.start': 'can_collect', 'robot.claim': 'can_claim', 'robot.apply_pose': 'can_apply_pose' };
export function commandAvailability(snapshot, command) {
  if (!snapshot?.backend_connected || !['live', 'preview'].includes(snapshot.source)) return '执行端接口尚未接入';
  if(snapshot.access?.authorized===false)return '请先授权操作';
  if (!snapshot.capabilities?.commands?.includes(command)) return '当前执行端未开放此操作';
  if(command==='services.controller.start'&&snapshot.source!=='preview'&&snapshot.services?.controller?.start_allowed!==true)return snapshot.services?.controller?.start_reason||'控制器启动条件尚未确认';
  const serviceStop=command.match(/^services\.(docker|pc_service|controller)\.stop$/);
  if(serviceStop&&snapshot.source!=='preview'){
    const service=snapshot.services?.[serviceStop[1]];
    if(service?.stop_allowed!==true)return service?.stop_reason||'尚未确认服务可停止，请刷新状态';
  }
  if(command==='collection.start'&&snapshot.collection?.busy)return '导出器正在处理上一条操作';
  const gate = CONTROL_INTERLOCKS[command];
  if (gate && snapshot.interlocks?.[gate] !== true) return snapshot.interlocks?.reasons?.[gate] || snapshot.interlocks?.reason || '设备或控制权尚未就绪';
  if (['robot.initialize', 'inference.start', 'collection.start', 'robot.claim', 'robot.apply_pose'].includes(command) && !(command==='robot.initialize'&&snapshot.mode==='sim') && (!snapshot.robot?.connected || !fresh(snapshot.robot))) return '机器人反馈缺失或已过期';
  if (command === 'robot.apply_pose' && snapshot.robot?.owner !== 'manual') return '请先取得手动调试控制权';
  return '';
}
export function jointLabel(name) {
  const words = { left: '左', right: '右', hip: '髋', knee: '膝', ankle: '踝', waist: '腰', shoulder: '肩', elbow: '肘', wrist: '腕', pitch: '俯仰', roll: '横滚', yaw: '偏航' };
  return name.replace(/_joint$/, '').split('_').map(word => words[word] || word).join(' ');
}
