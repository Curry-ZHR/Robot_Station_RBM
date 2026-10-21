import { CAMERAS, SERVICE_DEFS, STAGES, emptySnapshot, clone, uid, day } from './console-core.js';

export const PREVIEW_COMMANDS = ['self_check.run', 'deployment.prepare', 'deployment.cancel', 'robot.connect', 'robot.initialize', 'robot.claim', 'robot.release', 'robot.set_mode', 'robot.apply_pose', 'inference.connect', 'inference.disconnect', 'inference.start', 'inference.stop', 'collection.prepare', 'collection.start', 'collection.save', 'collection.discard', 'collection.end', 'safety.stop', ...SERVICE_DEFS.flatMap(([id]) => [`services.${id}.start`, `services.${id}.stop`]), 'workflows.run'];
export class PreviewRuntime {
  constructor(profile, saved = {}) {
    this.profile = profile; this.startedAt = Date.now(); this.recordStart = 0; this.taskStart = 0; this.fault = '';
    this.state = emptySnapshot(); this.state.source = 'preview'; this.state.backend_connected = true;
    this.state.capabilities.commands = PREVIEW_COMMANDS; this.state.robot = { connected: true, owner: null, mode: 'OFF', initialized: true, initialization_profile_id:'preview-only', joints: [] };
    this.state.battery = { percent: 72, low_percent: 20, critical_percent: 10, source: '界面预演', charging: false };
    this.state.model = { connected: false, state: 'disconnected', steps: 0, latency_ms: null, frequency_hz: null, recording: false };
    this.state.deployment = { state: 'ready', steps: STAGES.map(([id, label]) => ({ id, label, state: 'succeeded' })) };
    this.state.checks = [['gpu', 'GPU 与推理运行时'], ['docker', 'Docker 与镜像'], ['models', '模型文件'], ['storage', '存储空间'], ['network', '网络与网卡'], ['input', '输入源与追踪']].map(([id, label]) => ({ id, label, status: 'passed', detail: '仅用于界面预演', scope: '界面预演', source: '本地预演' }));
    this.targets = Object.fromEntries(profile.body_joints.map(name => [name, 0]));
    this.episodes = Array.isArray(saved.episodes) ? saved.episodes : [0, 1, 2].map(index => this.makeEpisode(index));
    this.state.services = Object.fromEntries(SERVICE_DEFS.map(([id]) => [id, { state: id === 'controller' ? 'ready' : 'running', label: '界面预演' }]));
    this.state.services.controller={state:'stopped',owned:true,start_allowed:true,stop_allowed:false,phase:'stopped'};
    this.state.sonic={phase:'stopped',stop_confirmed:true,feedback:{}};
    this.event('info', '界面预演已开启', '全部状态与视频均为合成演示，不向设备发送指令。');
  }
  makeEpisode(index) { return { dataset: 'frontend_preview', episode_index: index, name: `preview_${String(index + 1).padStart(3, '0')}`, frames: 90, fps: 15, duration_seconds: 6, tasks: ['合成测试片段 · 检查三路视频同步与曲线'], grade: null, state: 'saved', demo_only: true, source: '界面预演' }; }
  event(level, title, detail = '') { this.state.events.unshift({ id: uid(), level, title, detail, at: new Date().toISOString(), source: '界面预演' }); this.state.events = this.state.events.slice(0, 80); }
  snapshot() {
    const now = new Date().toISOString(), s = this.state;
    s.observed_at = now; s.robot.observed_at = this.fault === 'robot-offline' ? null : now; s.robot.connected = this.fault !== 'robot-offline'; s.battery.observed_at = now;
    s.battery.percent = this.fault === 'low-battery' ? 8 : 72;
    const running = s.model.state === 'running', t = running ? (Date.now() - this.taskStart) / 1000 : 0;
    s.robot.joints = this.profile.body_joints.map(name => ({ name, position_rad: this.targets[name] + (running && name.includes('elbow') ? .35 + .08 * Math.sin(t) : 0), velocity_rad_s: running && name.includes('elbow') ? .08 * Math.cos(t) : 0, temperature_c: 36, effort_nm: 0 }));
    s.cameras = CAMERAS.map(camera => ({ ...camera, state: this.fault === 'camera-offline' && camera.id === 'left_wrist' ? 'offline' : 'streaming', observed_at: now, fps: 15, latency_ms: 24, transport: 'video', url: `/assets/preview/${camera.id}.mp4`, source: '合成测试视频' }));
    if (running) { s.model.steps = Math.floor(t * 30); s.model.latency_ms = 42; s.model.frequency_hz = 30; }
    if(s.sonic.phase==='running'){
      s.sonic.feedback={valid:true,observed_at:now,control_index:Math.floor((Date.now()-this.sonicStart)/20),frequency_hz:50,feedback_age_seconds:0};
      s.sonic.feedback_valid=true;s.sonic.process_running=true;s.sonic.initialized=true;s.sonic.detail='合成SONIC控制反馈；仅用于界面预演';s.sonic.input_ready=true;
    }
    if (s.collection.recording) s.collection.elapsed_seconds = (Date.now() - this.recordStart) / 1000;
    const camerasOK = this.fault !== 'camera-offline', robotOK = s.robot.connected;
    s.interlocks = { can_initialize: robotOK && !running && !s.collection.recording, can_claim: robotOK && !running && !s.collection.recording, can_infer: robotOK && camerasOK && s.model.connected && s.robot.owner === 'task-model' && !s.collection.recording,
      can_collect: robotOK && camerasOK && s.collection.prepared && !running, can_apply_pose: robotOK && s.robot.owner === 'manual' && !running && !s.collection.recording,
      reasons: {can_apply_pose: !robotOK ? '机器人反馈已中断（预演）' : '请先取得手动调试控制权', can_claim: !robotOK ? '机器人反馈已中断（预演）' : '请先结束当前任务', can_collect: !camerasOK ? '相机画面未就绪（预演）' : !s.collection.prepared ? '请先准备采集任务' : '当前任务占用控制源'},
      reason: !robotOK ? '机器人反馈已中断（预演）' : !camerasOK ? '左腕相机断流（预演）' : !s.model.connected ? '请先连接任务模型' : '请确认任务准备状态与控制权' };
    s.groups = [{ name: 'frontend_preview', episodes: this.episodes.length, retained: this.episodes.length, demo_only: true, fps: 15, version: '前端合成测试', counts: { A: this.episodes.filter(e => e.grade === 'A').length, B: 0, F: 0, unreviewed: this.episodes.filter(e => !e.grade).length } }];
    s.totals = { datasets: 0, episodes: 0, demo_episodes: this.episodes.length }; s.output_root = '界面预演 / 不写入真实数据目录';
    return clone(s);
  }
  async command(scope, action, payload = {}) {
    const s = this.state;
    if (scope === 'inference') {
      if (action === 'connect') { s.model.connected = true; s.model.state = 'ready'; s.model.adapter={validated:true,semantic:'named-joint-position',dimension:29,unit:'rad',frequency_hz:payload.frequency_hz||30}; }
      if (action === 'disconnect') { s.model.connected = false; s.model.state = 'disconnected'; }
      if (action === 'start') { s.model.state = 'running'; this.taskStart = Date.now(); s.model.recording = !!payload.record; }
      if (action === 'stop') { s.model.state = s.model.connected ? 'ready' : 'disconnected'; s.model.recording = false; }
    }
    if (scope === 'robot') {
      if (action === 'initialize') s.robot.initialized = true;
      if (action === 'claim') { s.robot.owner = payload.owner || 'task-model'; s.robot.mode = 'PLANNER'; }
      if (action === 'release') { if (s.model.state === 'running' || s.collection.recording) throw new Error('请先停止当前任务，再释放控制权'); s.robot.owner = null; s.robot.mode = 'OFF'; }
      if (action === 'set_mode') s.robot.mode = payload.mode;
      if (action === 'apply_pose') {
        for (const row of payload.joints || []) {
          const spec = this.profile.joints.find(j => j.name === row.name);
          if (!spec || !Number.isFinite(row.position_rad) || row.position_rad < spec.lower || row.position_rad > spec.upper) throw new Error('目标姿态超出参考模型关节限制');
          this.targets[row.name] = row.position_rad;
        }
      }
    }
    if (scope === 'collection') {
      if (action === 'prepare') s.collection.prepared = true;
      if (action === 'start') { if (s.model.state === 'running') throw new Error('推理任务正在占用控制源'); s.collection.recording = true; this.recordStart = Date.now(); s.robot.owner = 'pico'; }
      if (action === 'save') { this.episodes.unshift(this.makeEpisode(this.episodes.length)); s.collection.recording = false; s.collection.elapsed_seconds = 0; }
      if (action === 'discard') { s.collection.recording = false; s.collection.elapsed_seconds = 0; }
      if (action === 'end') { s.collection.recording = false; s.collection.prepared = false; if (s.robot.owner === 'pico') s.robot.owner = null; }
    }
    if (scope === 'services') {
      s.services[payload.service_id] = { state: action === 'start' ? 'running' : 'stopped' };
      if(payload.service_id==='controller'){
        this.sonicStart=Date.now();s.sonic={phase:action==='start'?'running':'stopped',stop_confirmed:action==='stop',run_id:'preview-only',feedback:{}};
        s.services.controller={state:action==='start'?'running':'stopped',owned:true,start_allowed:action==='stop',stop_allowed:action==='start',detail:'合成SONIC会话'};
      }
    }
    if (scope === 'safety') { s.sonic={phase:'stopped',stop_confirmed:true,feedback:{}};s.services.controller={state:'stopped',owned:true,start_allowed:true,stop_allowed:false}; s.model.state = s.model.connected ? 'ready' : 'disconnected'; s.collection.recording = false; s.robot.owner = null; s.robot.mode = 'OFF'; s.deployment.state = 'idle'; }
    this.event('success', `${({ inference: '任务模型', robot: '机器人控制', collection: '采集', services: '服务', safety: '停止任务', deployment: '启动向导', self_check: '自检' })[scope] || scope} · ${action}`, '此操作仅改变本地界面预演状态。');
    return { ok: true, source: 'preview', message: '界面预演完成', command_id: uid(), state: 'succeeded' };
  }
  review(index) { const episode = this.episodes.find(e => e.episode_index === Number(index)); return { ok: true, episode: clone(episode), videos: CAMERAS.map(c => ({ camera: c.id, label: c.label, url: `/assets/preview/${c.id}.mp4` })), dataset_path: '本地合成测试片段' }; }
  series() {
    return { source: 'preview', joint_names: this.profile.body_joints, unit: 'rad', frames: Array.from({ length: 91 }, (_, i) => ({ time_s: i / 15, state: this.profile.body_joints.map(name => name.includes('elbow') ? .4 + .12 * Math.sin(i / 15 * 1.5) : 0), action: this.profile.body_joints.map(name => name.includes('elbow') ? .4 + .12 * Math.sin(i / 15 * 1.5 + .15) : 0) })) };
  }
}
