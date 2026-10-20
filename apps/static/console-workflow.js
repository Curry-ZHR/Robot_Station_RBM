import { esc, uid } from './console-core.js';

export const NODE_TYPES = [
  ['start', '开始', 'play', 'system'], ['self_check', '运行前自检', 'list-checks', 'prepare'],
  ['prepare_runtime', '准备运行环境', 'container', 'prepare'], ['wait_sensors', '等待相机就绪', 'camera', 'prepare'],
  ['wait_robot', '等待机器人反馈', 'bot', 'prepare'], ['model_connect', '连接任务模型', 'plug', 'inference'],
  ['claim_control', '申请任务控制权', 'shield-check', 'prepare'], ['collection_prepare', '准备采集任务', 'settings-2', 'collection'],
  ['inference', '运行任务推理', 'sparkles', 'inference'], ['collection_start', '开始录制', 'circle-dot', 'collection'],
  ['collection_save', '保存片段', 'save', 'collection'], ['wait', '等待', 'timer', 'prepare'],
  ['stop', '停止当前任务', 'square', 'system'], ['end', '结束', 'flag', 'system'],
];
export function templateGraph(kind = 'inference') {
  const kinds = kind === 'collection' ? ['start', 'self_check', 'prepare_runtime', 'wait_sensors', 'wait_robot', 'collection_prepare', 'collection_start', 'wait', 'collection_save', 'end'] : ['start', 'self_check', 'prepare_runtime', 'wait_sensors', 'wait_robot', 'model_connect', 'claim_control', 'inference', 'stop', 'end'];
  const nodes = kinds.map((type, index) => ({ id: `node-${index + 1}`, type, label: NODE_TYPES.find(row => row[0] === type)[1], x: 42 + index % 4 * 245, y: 48 + Math.floor(index / 4) * 158, timeout_s: 30, params: type === 'wait' ? { seconds: 2 } : type === 'claim_control' ? {owner:'task-model'} : {} }));
  return { schema_version: 1, id: uid(), name: kind === 'collection' ? 'PICO 遥操作采集' : '任务模型推理', task_kind: kind, max_transitions: 100, nodes, edges: nodes.slice(0, -1).map((node, index) => ({ id: uid(), from: node.id, to: nodes[index + 1].id, outcome: 'success' })) };
}
export function validateGraph(graph) {
  const errors = [];
  if (graph?.schema_version !== 1 || !Array.isArray(graph.nodes) || !Array.isArray(graph.edges)) return ['流程格式不正确，需要 schema_version: 1、nodes 和 edges'];
  if (graph.nodes.some(node => !node || typeof node !== 'object' || Array.isArray(node)) || graph.edges.some(edge => !edge || typeof edge !== 'object' || Array.isArray(edge))) return ['节点或连线格式无效'];
  if (graph.nodes.length > 100 || graph.edges.length > 300) return ['流程最多支持 100 个节点、300 条连线'];
  if (!Number.isInteger(graph.max_transitions) || graph.max_transitions < 1 || graph.max_transitions > 1000) errors.push('最大流转次数应为 1～1000 的整数');
  if(typeof graph.name!=='string'||!graph.name.trim()||!['inference','collection'].includes(graph.task_kind))errors.push('流程名称或任务类型无效');
  const ids = new Set(), kinds = new Set(NODE_TYPES.map(row => row[0]));
  for (const node of graph.nodes) {
    if (typeof node.id !== 'string' || !node.id || node.id.length > 80 || ids.has(node.id)) errors.push('节点编号为空或重复');
    if(typeof node.label!=='string'||!node.label.trim()||node.label.length>80)errors.push('节点名称应为 1～80 个字符');
    if(!node.params||typeof node.params!=='object'||Array.isArray(node.params))errors.push('节点参数应为对象');
    ids.add(node.id); if (!kinds.has(node.type)) errors.push(`未知节点类型：${node.type}`);
    if (!Number.isFinite(node.x) || !Number.isFinite(node.y) || Math.abs(node.x) > 10000 || Math.abs(node.y) > 10000) errors.push('节点坐标无效');
    if (!Number.isFinite(node.timeout_s) || node.timeout_s <= 0 || node.timeout_s > 3600) errors.push('节点超时应在 1～3600 秒之间');
  }
  const starts = graph.nodes.filter(node => node.type === 'start'), ends = graph.nodes.filter(node => node.type === 'end');
  if (starts.length !== 1 || ends.length !== 1) errors.push('流程需要且只能有一个开始和一个结束节点');
  const branches = new Set(),edgeIds=new Set();
  for (const edge of graph.edges) {
    if(typeof edge.id!=='string'||!edge.id||edgeIds.has(edge.id))errors.push('连线编号为空或重复');edgeIds.add(edge.id);
    if (!ids.has(edge.from) || !ids.has(edge.to)) errors.push('存在指向已删除节点的连线');
    if (!['success', 'failure', 'stop'].includes(edge.outcome)) errors.push('连线结果必须是 success / failure / stop');
    const key = `${edge.from}:${edge.outcome}`; if (branches.has(key)) errors.push('同一节点的同类结果只能有一个出口'); branches.add(key);
    if (edge.from === ends[0]?.id || edge.to === starts[0]?.id) errors.push('结束节点不能有出口，开始节点不能有入口');
  }
  if (starts.length === 1) {
    const reachable = new Set(), queue = [starts[0].id];
    while (queue.length) { const id = queue.shift(); if (reachable.has(id)) continue; reachable.add(id); graph.edges.filter(edge => edge.from === id).forEach(edge => queue.push(edge.to)); }
    if (graph.nodes.some(node => !reachable.has(node.id))) errors.push('存在无法从开始节点到达的节点');
    if (!reachable.has(ends[0]?.id)) errors.push('流程无法到达结束节点');
  }
  return [...new Set(errors)];
}
export function executionGraph(graph) {
  return { ...graph, nodes: graph.nodes.map(({ ui, ...node }) => ({ ...node, params: { ...node.params } })) };
}
export class WorkflowRunner {
  constructor(onEvent, delay = 420) { this.onEvent = onEvent; this.delay = delay; this.running = false; this.cancelled = false; }
  async run(graph) {
    const errors = validateGraph(graph); if (errors.length) throw new Error(errors[0]);
    if (this.running) throw new Error('流程预演已经在运行'); this.running = true; this.cancelled = false;
    let current = graph.nodes.find(node => node.type === 'start'), transitions = 0;
    try {
      while (current && !this.cancelled) {
        if (transitions++ >= graph.max_transitions) throw new Error('已达到最大流转次数，预演停止');
        this.onEvent({ type: 'node', id: current.id, state: 'running', label: current.label });
        await new Promise(resolve => { this.wake = resolve; this.timer = setTimeout(resolve, this.delay); });
        if (this.cancelled) break;
        const outcome = current.ui?.preview_fail ? 'failure' : 'success';
        this.onEvent({ type: 'node', id: current.id, state: outcome === 'success' ? 'succeeded' : 'failed', label: current.label });
        if (current.type === 'end') { this.onEvent({ type: 'complete' }); return; }
        const edge = graph.edges.find(row => row.from === current.id && row.outcome === outcome);
        if (!edge) throw new Error(`${current.label} 没有${outcome === 'failure' ? '失败' : '成功'}出口`);
        current = graph.nodes.find(node => node.id === edge.to);
      }
      this.onEvent({ type: 'cancelled' });
    } finally { this.running = false; this.wake = null; }
  }
  stop() { this.cancelled = true; clearTimeout(this.timer); this.wake?.(); }
}
export class WorkflowEditor {
  constructor(root, graph, onSelect, onChange) {
    this.root = root; this.graph = graph; this.onSelect = onSelect; this.onChange = onChange; this.selected = null; this.linkFrom = null; this.zoom = 1; this.states = {};
    this.world = root.querySelector('[data-flow-world]'); this.edgeLayer = root.querySelector('[data-flow-edges]'); this.nodeLayer = root.querySelector('[data-flow-nodes]');
    this.pointerDown = event => {
      const handle = event.target.closest('[data-drag-node]'); if (!handle || event.button !== 0) return;
      const node = this.graph.nodes.find(row => row.id === handle.dataset.dragNode); this.drag = { node, x: event.clientX, y: event.clientY, ox: node.x, oy: node.y };
      this.root.setPointerCapture(event.pointerId); event.preventDefault();
    };
    this.pointerMove = event => { if (!this.drag) return; this.drag.node.x = Math.max(0, Math.min(1350, this.drag.ox + (event.clientX - this.drag.x) / this.zoom)); this.drag.node.y = Math.max(0, Math.min(1100, this.drag.oy + (event.clientY - this.drag.y) / this.zoom)); this.paintPositions(); };
    this.pointerUp = () => { if (this.drag) { this.drag = null; this.onChange(this.graph); } };
    this.click = event => {
      const link = event.target.closest('[data-flow-link]'), select = event.target.closest('[data-flow-select]'), edge = event.target.closest('[data-flow-edge]');
      if (link) { this.linkFrom = link.dataset.flowLink; this.root.dataset.linking = 'true'; this.onSelect(this.graph.nodes.find(n => n.id === this.linkFrom), 'link'); return; }
      if (select) {
        const id = select.dataset.flowSelect;
        if (this.linkFrom) {
          if (this.linkFrom !== id && !this.graph.edges.some(e => e.from === this.linkFrom && e.outcome === 'success')) { this.graph.edges.push({ id: uid(), from: this.linkFrom, to: id, outcome: 'success' }); this.onChange(this.graph); }
          else if (this.linkFrom !== id) this.onSelect(this.graph.nodes.find(n => n.id === this.linkFrom), 'replace-link');
          this.linkFrom = null; this.root.dataset.linking = 'false'; this.paint();
        } else { this.selected = id; this.paint(); this.onSelect(this.graph.nodes.find(n => n.id === id)); }
      }
      if (edge) this.onSelect(this.graph.edges.find(e => e.id === edge.dataset.flowEdge), 'edge');
    };
    root.addEventListener('pointerdown', this.pointerDown); root.addEventListener('pointermove', this.pointerMove); root.addEventListener('pointerup', this.pointerUp); root.addEventListener('pointercancel', this.pointerUp); root.addEventListener('click', this.click);
    this.paint();
  }
  paint() {
    this.nodeLayer.innerHTML = this.graph.nodes.map(node => { const type = NODE_TYPES.find(row => row[0] === node.type); return `<article class="flow-node ${esc(type?.[3])} ${this.selected === node.id ? 'selected' : ''} ${esc(this.states[node.id] || '')}" data-node="${esc(node.id)}" style="left:${node.x}px;top:${node.y}px"><div class="node-drag" data-drag-node="${esc(node.id)}"><span>${esc(node.type === 'start' || node.type === 'end' ? '流程边界' : type?.[1])}</span><span>⠿</span></div><button class="node-body" data-flow-select="${esc(node.id)}"><i data-lucide="${esc(type?.[2] || 'box')}"></i><span>${esc(node.label)}</span></button><footer><span>${esc(this.states[node.id] ? { running: this.execution==='live'?'执行中':'预演中', succeeded: '已完成', failed: '失败', cancelled:'已取消', skipped:'已跳过', pending:'等待中' }[this.states[node.id]] : `${node.timeout_s} 秒超时`)}</span>${node.type !== 'end' ? `<button class="node-port" data-flow-link="${esc(node.id)}" title="从此节点连线" aria-label="从${esc(node.label)}连线">＋</button>` : ''}</footer></article>`; }).join('');
    this.paintEdges(); globalThis.lucide?.createIcons();
  }
  paintPositions() { this.graph.nodes.forEach(node => { const element = this.nodeLayer.querySelector(`[data-node="${CSS.escape(node.id)}"]`); if (element) { element.style.left = `${node.x}px`; element.style.top = `${node.y}px`; } }); this.paintEdges(); }
  paintEdges() {
    this.edgeLayer.innerHTML = `<defs><marker id="flow-arrow" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8" fill="#8ba5c5"/></marker></defs>` + this.graph.edges.map(edge => {
      const from = this.graph.nodes.find(n => n.id === edge.from), to = this.graph.nodes.find(n => n.id === edge.to); if (!from || !to) return '';
      const x1 = from.x + 200, y1 = from.y + 65, x2 = to.x, y2 = to.y + 65, bend = Math.max(45, Math.abs(x2 - x1) / 2);
      return `<g data-flow-edge="${esc(edge.id)}" class="flow-edge ${edge.outcome}"><path d="M${x1},${y1} C${x1 + bend},${y1} ${x2 - bend},${y2} ${x2},${y2}" marker-end="url(#flow-arrow)"/><text x="${(x1 + x2) / 2}" y="${(y1 + y2) / 2 - 8}">${esc({ success: '成功', failure: '失败', stop: '停止' }[edge.outcome])}</text></g>`;
    }).join('');
  }
  setZoom(value) { this.zoom = Math.max(.5, Math.min(1.4, value)); this.world.style.transform = `scale(${this.zoom})`; this.root.querySelector('[data-flow-space]').style.width = `${1550 * this.zoom}px`; this.root.querySelector('[data-flow-space]').style.height = `${1320 * this.zoom}px`; }
  setNodeState(id, state) { this.states[id] = state; this.paint(); }
  dispose() { this.root.removeEventListener('pointerdown', this.pointerDown); this.root.removeEventListener('pointermove', this.pointerMove); this.root.removeEventListener('pointerup', this.pointerUp); this.root.removeEventListener('pointercancel', this.pointerUp); this.root.removeEventListener('click', this.click); }
}
