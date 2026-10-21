import { commandAvailability, emptySnapshot, legacySnapshot, normalizeSnapshot, uid } from './console-core.js';
import { PreviewRuntime } from './console-preview.js';

export const API_PREFIX = '/api/v1/console';
export const ENDPOINTS = {
  snapshot: `${API_PREFIX}/snapshot`, self_check: `${API_PREFIX}/self-check`, deployment: `${API_PREFIX}/deployment/jobs`,
  robot: `${API_PREFIX}/robot/commands`, inference: `${API_PREFIX}/inference/commands`, collection: `${API_PREFIX}/collection/commands`,
  services: `${API_PREFIX}/services/actions`, safety: `${API_PREFIX}/safety/stop`, workflows: `${API_PREFIX}/workflows/runs`,
};
export class ConsoleAPI {
  constructor({ profile, fetchImpl = globalThis.fetch?.bind(globalThis), preview = false, mode = 'sim' } = {}) {
    this.profile = profile; this.fetchImpl = fetchImpl; this.preview = preview; this.mode = mode;
    this.runtime = new PreviewRuntime(profile); this.snapshot = emptySnapshot(); this.v1Unavailable = false;
  }
  async request(path, options = {}) {
    const timeoutMs=path.includes('/episodes/timeseries')?65000:path.includes('/services/actions')||path.includes('/safety/stop')?45000:path.includes('/diagnostics')?15000:/\/(snapshot|self-check|robot\/commands)(\?|$)/.test(path)?20000:8000;
    const controller = new AbortController(), timeout = setTimeout(() => controller.abort(), timeoutMs);
    try {
      const response = await this.fetchImpl(path, { ...options, signal: controller.signal, cache: 'no-store', headers: { Accept: 'application/json', ...(options.body ? { 'Content-Type': 'application/json', ...(this.csrfToken ? {'X-Console-CSRF':this.csrfToken} : {}) } : {}), ...(options.headers || {}) } });
      let data; try { data = await response.json(); } catch { throw Object.assign(new Error('接口返回格式不正确'), { status: response.status }); }
      if (!response.ok || data?.ok === false) throw Object.assign(new Error(data?.error?.message || data?.error || data?.message || `请求失败 (${response.status})`), { status: response.status });
      return data;
    } finally { clearTimeout(timeout); }
  }
  async loadSnapshot() {
    if (this.preview) return this.snapshot = this.runtime.snapshot();
    if (!this.v1Unavailable) {
      try { const raw = await this.request(`${ENDPOINTS.snapshot}?${new URLSearchParams({mode:this.mode,profile_id:this.profile.id})}`); this.snapshot = normalizeSnapshot(raw.snapshot || raw); this.csrfToken=this.snapshot.access?.csrf_token; this.snapshot.source = 'live'; this.snapshot.backend_connected = true; return this.snapshot; }
      catch (error) { if (![404, 501].includes(error.status)) { this.snapshot = emptySnapshot(); throw error; } this.v1Unavailable = true; }
    }
    const data = await this.request(`/api/collection?mode=${encodeURIComponent(this.mode)}`);
    return this.snapshot = legacySnapshot(data);
  }
  can(scope, action, payload = {}) { return commandAvailability(this.snapshot, scope === 'services' ? `services.${payload.service_id}.${action}` : `${scope}.${action}`); }
  async command(scope, action, payload = {}) {
    const reason = this.can(scope, action, payload); if (reason) throw new Error(reason);
    if (this.preview) { const result = await this.runtime.command(scope, action, payload); this.snapshot = this.runtime.snapshot(); return result; }
    const path = ENDPOINTS[scope]; if (!path) throw new Error('未定义的操作接口');
    // Hardware commands have no fallback to legacy /api/stack/* or /api/record/*.
    return this.request(path, { method: 'POST', headers: { 'Idempotency-Key': uid() }, body: JSON.stringify({ action, mode: this.mode, profile_id: this.profile.id, expected_revision: this.snapshot.revision ?? null, payload }) });
  }
  async workflowRun(id) { return this.request(`${ENDPOINTS.workflows}/${encodeURIComponent(id)}`); }
  async deploymentJob(id) { return this.request(`${ENDPOINTS.deployment}/${encodeURIComponent(id)}`); }
  async listEpisodes(dataset, offset = 0) {
    if (this.preview) return { ok: true, episodes: this.runtime.episodes.slice(offset, offset + 30), total: this.runtime.episodes.length, offset, limit: 30 };
    return this.request(`/api/episodes?${new URLSearchParams({ dataset, offset, limit: 30 })}`);
  }
  async review(dataset, episode) {
    if(this.preview)return this.runtime.review(episode);
    const result=await this.request(`/api/episodes/review?${new URLSearchParams({ dataset, episode })}`);
    const seen=new Set();result.videos=(result.videos||[]).flatMap(row=>{const key=String(row.camera||'').toLowerCase(),camera=['head','left_wrist','right_wrist'].includes(key)?key:key.includes('left')||row.label==='左腕'?'left_wrist':key.includes('right')||row.label==='右腕'?'right_wrist':key.includes('head')||row.label==='主视角'?'head':null;if(!camera||seen.has(camera))return [];seen.add(camera);return [{...row,original_camera:row.camera,camera}];});
    return result;
  }
  async series(dataset, episode) {
    if (this.preview) return this.runtime.series();
    if (this.v1Unavailable) return null;
    try { return await this.request(`${API_PREFIX}/episodes/timeseries?${new URLSearchParams({ dataset, episode })}`); }
    catch (error) { if ([404, 501].includes(error.status)) return null; throw error; }
  }
  async rate(dataset, episode, grade) {
    if (this.preview) { const row = this.runtime.episodes.find(e => e.episode_index === Number(episode)); if (row) row.grade = grade; return { ok: true, source: 'preview' }; }
    return this.request('/api/episodes/rate', { method: 'POST', body: JSON.stringify({ dataset, episode, grade }) });
  }
  async refreshChecks() {
    if (this.preview) { await this.runtime.command('self_check', 'run'); return this.loadSnapshot(); }
    if (!this.can('self_check', 'run')) await this.command('self_check', 'run', { read_only: true });
    return this.loadSnapshot();
  }
}
