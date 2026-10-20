import { safeMediaURL, duration, degree } from './console-core.js';

export class PlaybackController {
  constructor(root, review, series, profile, onTime = () => {}) {
    this.root = root; this.review = review; this.series = this.validSeries(series, profile); this.profile = profile; this.onTime = onTime; this.time = 0;
    this.videos = [...root.querySelectorAll('video[data-replay-camera]')]; this.primary = this.videos.find(video => video.dataset.hasVideo === 'true'); this.listeners = [];
    this.channels = profile.body_joints.map((name, index) => name.includes('elbow') ? index : -1).filter(index => index >= 0);
    this.videos.forEach(video => { video.muted = true; video.playsInline = true; video.preload = 'metadata'; const record = review.videos.find(row => row.camera === video.dataset.replayCamera); const url = safeMediaURL(record?.url); if (url) video.src = url; });
    if (this.primary) {
      this.listen(this.primary, 'timeupdate', () => { this.time = this.primary.currentTime; this.sync(); this.update(); });
      this.listen(this.primary, 'ended', () => { this.pause(); this.update(); });
      this.listen(this.primary, 'loadedmetadata', () => this.update());
      this.listen(this.primary, 'error', () => { this.pause(); const note = root.querySelector('[data-playback-error]'); if (note) { note.hidden = false; note.textContent = '视频无法读取，请检查文件与视频接口。'; } });
    }
    this.resize = new ResizeObserver(() => this.draw()); const canvas = root.querySelector('[data-chart]'); if (canvas) this.resize.observe(canvas);
    this.update();
  }
  validSeries(series, profile) {
    if (!series || series.unit !== 'rad' || !Array.isArray(series.joint_names) || !Array.isArray(series.frames)) return null;
    const order = profile.body_joints.map(name => series.joint_names.indexOf(name)); if (order.some(index => index < 0)) return null;
    const frames = series.frames.filter(frame => Number.isFinite(frame.time_s) && frame.time_s >= 0 && [frame.state, frame.action].every(values => Array.isArray(values) && order.every(index => Number.isFinite(values[index]))))
      .map(frame => ({ time_s: frame.time_s, state: order.map(index => frame.state[index]), action: order.map(index => frame.action[index]) }));
    if (!frames.length || frames.some((frame, i) => i && frame.time_s <= frames[i - 1].time_s)) return null;
    return { ...series, frames, joint_names: profile.body_joints };
  }
  listen(target, event, listener) { target.addEventListener(event, listener); this.listeners.push(() => target.removeEventListener(event, listener)); }
  get length() { return Number.isFinite(this.primary?.duration) ? this.primary.duration : this.review.episode?.duration_seconds || this.series?.frames.at(-1)?.time_s || 0; }
  sync(force = false) { this.videos.forEach(video => { if (video !== this.primary && video.dataset.hasVideo === 'true' && (force || Math.abs(video.currentTime - this.time) > .09)) video.currentTime = this.time; }); }
  async play() {
    if (!this.primary) throw new Error('此片段没有可播放的视频');
    this.sync(true);
    try { await Promise.all(this.videos.filter(video => video.dataset.hasVideo === 'true').map(video => video.play())); } catch { this.pause(); throw new Error('视频尚未就绪或格式不支持，请重试'); }
    this.update();
  }
  pause() { this.videos.forEach(video => video.pause()); this.update(); }
  seek(time) { this.time = Math.max(0, Math.min(this.length, time)); if (this.primary) this.primary.currentTime = this.time; this.sync(true); this.update(); }
  step(direction) { this.pause(); this.seek(this.time + direction / (this.review.episode.fps || 30)); }
  speed(rate) { if (![.25, .5, 1, 1.5, 2].includes(rate)) return; this.videos.forEach(video => { video.playbackRate = rate; }); }
  setChannels(indices) { this.channels = indices.slice(0, 6); this.draw(); }
  frame() { if(!this.series)return null;const frames=this.series.frames;let low=0,high=frames.length-1;while(low<high){const middle=Math.floor((low+high)/2);if(frames[middle].time_s<this.time)low=middle+1;else high=middle;}const next=frames[low],previous=frames[Math.max(0,low-1)];return Math.abs(previous.time_s-this.time)<=Math.abs(next.time_s-this.time)?previous:next; }
  update() {
    const slider = this.root.querySelector('[data-replay-progress]'); if (slider) { slider.max = this.length; slider.value = this.time; }
    const time = this.root.querySelector('[data-replay-time]'); if (time) time.textContent = `${duration(this.time)} / ${duration(this.length)}`;
    const counter = this.root.querySelector('[data-replay-frame]'); if (counter) counter.textContent = Math.min(Math.max(0,(this.review.episode.frames||Infinity)-1), Math.round(this.time * (this.review.episode.fps || 30)));
    const toggle = this.root.querySelector('[data-action="replay-toggle"]'); if (toggle) toggle.innerHTML = this.primary && !this.primary.paused ? '暂停' : '播放';
    this.draw(); this.onTime(this.frame(), this.time);
  }
  draw() {
    const canvas = this.root.querySelector('[data-chart]'); if (!canvas) return;
    const rect = canvas.getBoundingClientRect(), ratio = Math.min(devicePixelRatio || 1, 2), width = Math.max(rect.width, 100), height = Math.max(rect.height, 100);
    canvas.width = width * ratio; canvas.height = height * ratio; const ctx = canvas.getContext('2d'); ctx.scale(ratio, ratio); ctx.clearRect(0, 0, width, height);
    const pad = { l: 44, r: 20, t: 24, b: 30 }, w = width - pad.l - pad.r, h = height - pad.t - pad.b;
    ctx.font = '11px system-ui'; ctx.fillStyle = '#8290a3'; ctx.strokeStyle = '#e9edf3'; ctx.lineWidth = 1;
    for (let i = 0; i <= 4; i++) { const y = pad.t + h * i / 4; ctx.beginPath(); ctx.moveTo(pad.l, y); ctx.lineTo(width - pad.r, y); ctx.stroke(); }
    if (!this.series || !this.channels.length) { ctx.textAlign = 'center'; ctx.fillText(this.series ? '选择关节查看 State / Action 曲线' : '尚无关节序列 · 等待回放数据接口', width / 2, height / 2); return; }
    const frames = this.series.frames, maxTime = Math.max(this.length, frames.at(-1).time_s, .01), colors = ['#3068df', '#0d9a8c', '#b57a16', '#8862d6', '#c6537c', '#497c9d'];
    let min = Infinity, max = -Infinity; for (const frame of frames) for (const index of this.channels) { min = Math.min(min, frame.state[index], frame.action[index]); max = Math.max(max, frame.state[index], frame.action[index]); } if (max - min < .12) { min -= .1; max += .1; } const margin = (max - min) * .15; min -= margin; max += margin;
    ctx.textAlign = 'right'; [min, (min + max) / 2, max].forEach(value => ctx.fillText(`${degree(value)}°`, pad.l - 8, pad.t + h - (value - min) / (max - min) * h + 4));
    this.channels.forEach((index, channel) => { ['state', 'action'].forEach(kind => { ctx.beginPath(); ctx.strokeStyle = colors[channel]; ctx.lineWidth = kind === 'state' ? 1.8 : 1.4; ctx.setLineDash(kind === 'action' ? [4, 4] : []); frames.filter((frame, i) => i % Math.max(1, Math.floor(frames.length / Math.max(1, w * 2))) === 0 || i === frames.length - 1).forEach((frame, i) => { const x = pad.l + frame.time_s / maxTime * w, y = pad.t + h - (frame[kind][index] - min) / (max - min) * h; if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y); }); ctx.stroke(); }); });
    ctx.setLineDash([]); ctx.strokeStyle = '#ea8151'; const cursor = pad.l + this.time / maxTime * w; ctx.beginPath(); ctx.moveTo(cursor, pad.t); ctx.lineTo(cursor, pad.t + h); ctx.stroke();
    ctx.fillStyle = '#8290a3'; ctx.textAlign = 'left'; ctx.fillText('0 s', pad.l, height - 7); ctx.textAlign = 'right'; ctx.fillText(`${maxTime.toFixed(1)} s`, width - pad.r, height - 7);
  }
  dispose() { this.pause(); this.listeners.forEach(remove => remove()); this.resize.disconnect(); this.videos.forEach(video => { video.removeAttribute('src'); video.load(); }); }
}
