const state = {
  status: null,
  overview: null,
  datasets: [],
  initialized: false,
  timerStartedAt: null,
  timerHandle: null,
  refreshHandle: null,
  selectedDataset: "",
  datasetFilter: "all",
  actionPending: false,
};

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];

function refreshIcons() {
  if (window.lucide) window.lucide.createIcons({ attrs: { "stroke-width": 1.8 } });
}

async function api(path, options = {}) {
  const response = await fetch(path, {
    headers: { "Content-Type": "application/json", ...(options.headers || {}) },
    ...options,
  });
  let value;
  try {
    value = await response.json();
  } catch {
    throw new Error(`服务返回了无效响应 (${response.status})`);
  }
  if (!response.ok || value.ok === false) throw new Error(value.error || `请求失败 (${response.status})`);
  return value;
}

let noticeTimer;
function showNotice(message, error = false) {
  const notice = $("#notice");
  notice.textContent = message;
  notice.classList.toggle("error", error);
  notice.hidden = false;
  clearTimeout(noticeTimer);
  noticeTimer = setTimeout(() => { notice.hidden = true; }, error ? 6000 : 3200);
}

function formatBytes(bytes) {
  if (!Number.isFinite(bytes) || bytes <= 0) return "0 B";
  const units = ["B", "KB", "MB", "GB", "TB"];
  const index = Math.min(Math.floor(Math.log(bytes) / Math.log(1024)), units.length - 1);
  return `${(bytes / (1024 ** index)).toFixed(index === 0 ? 0 : 1)} ${units[index]}`;
}

function formatDate(value) {
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return "-";
  return new Intl.DateTimeFormat("zh-CN", {
    month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit",
  }).format(date);
}

function formatDuration(seconds) {
  const minutes = Math.floor(seconds / 60).toString().padStart(2, "0");
  const remainder = Math.floor(seconds % 60).toString().padStart(2, "0");
  return `${minutes}:${remainder}`;
}

function makeIcon(name, className = "") {
  const icon = document.createElement("i");
  icon.dataset.lucide = name;
  if (className) icon.className = className;
  return icon;
}

function formConfig() {
  const data = new FormData($("#session-form"));
  return {
    mode: data.get("mode"),
    task_prompt: String(data.get("task_prompt") || "").trim(),
    dataset_name: String(data.get("dataset_name") || "").trim(),
    camera_host: String(data.get("camera_host") || "").trim(),
    camera_port: Number(data.get("camera_port")),
    frequency: Number(data.get("frequency")),
    wrist_cameras: $("#wrist-cameras").checked,
    text_to_speech: $("#text-to-speech").checked,
    camera_viewer: false,
    pico_input_source: "xrt",
    collection_date: String(data.get("collection_date") || ""),
    scene_id: Number(data.get("scene_id")),
  };
}

function populateForm(config) {
  const mode = $(`input[name="mode"][value="${config.mode}"]`);
  if (mode) mode.checked = true;
  $("#task-prompt").value = config.task_prompt || "demo";
  $("#dataset-name").value = config.dataset_name || "";
  $("#camera-host").value = config.camera_host || "localhost";
  $("#camera-port").value = config.camera_port || 5555;
  $("#frequency").value = config.frequency || 50;
  $("#wrist-cameras").checked = Boolean(config.wrist_cameras);
  $("#text-to-speech").checked = config.text_to_speech !== false;
  CollectionWorkspaceUI.populate(config);
}

function setPhase(status) {
  const badge = $("#phase-badge");
  const labels = { idle: "未启动", starting: "启动中", running: "运行中", recording: "录制中" };
  badge.className = `phase-badge ${status.phase}`;
  $("span:last-child", badge).textContent = labels[status.phase] || status.phase;
  $("#episode-state").textContent = status.recording ? "正在录制" : (status.session_running ? "等待开始" : "等待采集栈");

  const indicator = $("#record-indicator");
  indicator.classList.toggle("active", status.recording);
  indicator.lastChild.textContent = status.recording ? " 正在录制当前片段" : status.session_running ? " 会话就绪，等待录制" : " 等待会话启动";
  updateTimer(status.recording, status.elapsed_seconds);
}

function updateTimer(recording, elapsed = 0) {
  if (recording) state.timerStartedAt = performance.now() - Math.max(0, elapsed || 0) * 1000;
  if (!recording) state.timerStartedAt = null;
  if (!state.timerHandle) {
    state.timerHandle = setInterval(() => {
      const elapsed = state.timerStartedAt ? (performance.now() - state.timerStartedAt) / 1000 : 0;
      const minutes = Math.floor(elapsed / 60).toString().padStart(2, "0");
      const seconds = Math.floor(elapsed % 60).toString().padStart(2, "0");
      const tenths = Math.floor((elapsed % 1) * 10);
      $("#record-timer").textContent = `${minutes}:${seconds}.${tenths}`;
    }, 100);
  }
}

function renderStatus(status) {
  state.status = status;
  if (!state.initialized) {
    populateForm(status.config);
    state.initialized = true;
  }
  setPhase(status);
  $("#live-frequency").textContent = status.config.frequency || 50;
  $("#camera-endpoint-label").textContent = `${status.config.camera_host}:${status.config.camera_port}`;
  $("#output-root").textContent = status.output_root;

  for (const endpoint of status.endpoints) {
    const item = $(`[data-endpoint="${endpoint.id}"]`);
    if (!item) continue;
    const dot = $(".status-dot", item);
    dot.className = `status-dot ${endpoint.online ? "online" : "offline"}`;
    item.title = `${endpoint.label}: ${endpoint.online ? "在线" : "离线"}`;
  }

  const ready = status.ready_to_launch;
  const readiness = $("#readiness-label");
  readiness.textContent = ready ? "环境就绪" : "环境未就绪";
  readiness.classList.toggle("not-ready", !ready);

  const locked = status.session_running || status.phase === "starting";
  $$("#session-form input, #session-form textarea, #session-form select").forEach((input) => { input.disabled = locked || state.actionPending; });
  $("#start-stack").disabled = state.actionPending || locked || !ready;
  $("#start-stack span").textContent = locked ? "会话进行中" : "启动采集";
  $("#stop-stack-header").disabled = state.actionPending || !locked;
  $("#record-start").disabled = state.actionPending || !status.session_running || status.recording;
  $("#record-save").disabled = state.actionPending || !status.session_running || !status.recording;
  $("#record-discard").disabled = state.actionPending || !status.session_running || !status.recording;

  renderPrerequisites(status.prerequisites);
  renderEndpoints(status.endpoints);
  renderPanes(status.panes);
}

function renderPrerequisites(items) {
  const list = $("#prerequisite-list");
  list.replaceChildren();
  let count = 0;
  for (const item of items) {
    if (item.ok) count += 1;
    const row = document.createElement("div");
    row.className = "check-row";
    const iconWrap = document.createElement("span");
    iconWrap.className = `check-icon ${item.ok ? "" : "missing"}`;
    iconWrap.append(makeIcon(item.ok ? "check" : "x"));
    const text = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = item.label;
    const detail = document.createElement("code");
    detail.textContent = item.detail;
    text.append(title, detail);
    const itemStatus = document.createElement("span");
    itemStatus.textContent = item.ok ? "正常" : "缺失";
    row.append(iconWrap, text, itemStatus);
    list.append(row);
  }
  $("#check-count").textContent = `${count} / ${items.length}`;
  refreshIcons();
}

function renderEndpoints(items) {
  const list = $("#endpoint-list");
  list.replaceChildren();
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "endpoint-row";
    const dot = document.createElement("span");
    dot.className = `status-dot ${item.online ? "online" : "offline"}`;
    const text = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = item.label;
    const address = document.createElement("code");
    address.textContent = `${item.host}:${item.port}`;
    text.append(title, address);
    const endpointState = document.createElement("span");
    endpointState.textContent = item.online ? "在线" : "离线";
    row.append(dot, text, endpointState);
    list.append(row);
  }
}

function renderPanes(items) {
  const list = $("#pane-list");
  list.replaceChildren();
  if (!items.length) {
    const empty = document.createElement("div");
    empty.className = "pane-empty";
    empty.textContent = "当前没有运行中的采集进程";
    list.append(empty);
    return;
  }
  for (const item of items) {
    const row = document.createElement("div");
    row.className = "pane-row";
    const dot = document.createElement("span");
    dot.className = `status-dot ${item.alive ? "online" : "offline"}`;
    const text = document.createElement("div");
    const name = document.createElement("strong");
    name.textContent = item.name;
    const command = document.createElement("code");
    command.textContent = item.command || "shell";
    text.append(name, command);
    row.append(dot, text);
    list.append(row);
  }
}

async function refreshStatus(silent = true) {
  try {
    const mode = $("input[name=mode]:checked")?.value || "real";
    const workspace = await api(`/api/collection?mode=${encodeURIComponent(mode)}`);
    renderStatus(workspace.status);
    CollectionWorkspaceUI.render(workspace);
    if (!silent) showNotice("系统状态已更新");
  } catch (error) {
    CollectionWorkspaceUI.offline(error);
    if (!silent) showNotice(error.message, true);
  }
}

async function refreshLog() {
  try {
    const result = await api("/api/logs?pane=2&lines=120");
    const log = $("#event-log");
    log.textContent = result.log || "暂无运行事件。";
    log.scrollTop = log.scrollHeight;
  } catch (error) {
    $("#event-log").textContent = error.message;
  }
}

function setProgress(id, value) {
  const element = $(id);
  element.style.width = `${Math.max(0, Math.min(100, value))}%`;
}

function renderOverview(overview) {
  state.overview = overview;
  $$(".overview-source").forEach((item) => { item.textContent = overview.source_label; });
  $("#monitor-latency").textContent = `${overview.system.network_latency_ms.toFixed(1)} ms`;
  $("#monitor-cpu").textContent = `${overview.system.cpu_percent.toFixed(1)}%`;
  const maxTemp = Math.max(...overview.joints.map((item) => item.temperature));
  $("#monitor-max-temp").textContent = `${maxTemp.toFixed(1)}°C`;

  for (const camera of overview.cameras) {
    const card = $(`[data-camera="${camera.id}"]`);
    if (!card) continue;
    $("[data-camera-fps]", card).textContent = camera.fps.toFixed(1);
    $("[data-camera-latency]", card).textContent = camera.latency_ms;
    $("[data-camera-drop]", card).textContent = `${camera.drop_rate.toFixed(2)}%`;
  }

  const jointBody = $("#joint-table-body");
  jointBody.replaceChildren();
  for (const joint of overview.joints) {
    const row = document.createElement("tr");
    const values = [joint.name, joint.position.toFixed(3), joint.velocity.toFixed(2), joint.torque.toFixed(1)];
    for (const value of values) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    const temperature = document.createElement("td");
    temperature.textContent = `${joint.temperature.toFixed(1)}°C`;
    temperature.className = joint.temperature >= 50 ? "temperature-warm" : "";
    const limit = document.createElement("td");
    const limitBar = document.createElement("span");
    limitBar.className = "limit-bar";
    const fill = document.createElement("i");
    fill.style.width = `${joint.limit_ratio}%`;
    limitBar.append(fill);
    const limitLabel = document.createElement("small");
    limitLabel.textContent = `${joint.limit_ratio.toFixed(0)}%`;
    limit.append(limitBar, limitLabel);
    const jointState = document.createElement("td");
    const badge = document.createElement("span");
    badge.className = `status-label ${joint.status}`;
    badge.textContent = joint.status === "normal" ? "正常" : "关注";
    jointState.append(badge);
    row.append(temperature, limit, jointState);
    jointBody.append(row);
  }

  const system = overview.system;
  $("#system-cpu").textContent = `${system.cpu_percent.toFixed(1)}%`;
  $("#system-cpu-temp").textContent = `核心温度 ${system.cpu_temperature.toFixed(1)}°C`;
  $("#system-gpu").textContent = `${system.gpu_percent.toFixed(1)}%`;
  $("#system-gpu-temp").textContent = `核心温度 ${system.gpu_temperature.toFixed(1)}°C`;
  $("#system-memory").textContent = `${system.memory_percent.toFixed(1)}%`;
  $("#system-memory-detail").textContent = `${formatBytes(system.memory_used_bytes)} / ${formatBytes(system.memory_total_bytes)}`;
  $("#system-disk").textContent = `${system.disk_percent.toFixed(1)}%`;
  $("#system-disk-detail").textContent = `剩余 ${formatBytes(system.disk_free_bytes)}`;
  setProgress("#system-cpu-bar", system.cpu_percent);
  setProgress("#system-gpu-bar", system.gpu_percent);
  setProgress("#system-memory-bar", system.memory_percent);
  setProgress("#system-disk-bar", system.disk_percent);

  renderQuality(overview.quality);
  renderReport(overview.report, overview.alerts, overview.generated_at);
  refreshIcons();
}

function renderQuality(quality) {
  $("#quality-score").textContent = quality.score;
  $("#quality-score-ring").style.setProperty("--score", `${quality.score * 3.6}deg`);
  const verdict = $("#quality-verdict");
  verdict.className = `quality-chip ${quality.verdict}`;
  verdict.lastChild.textContent = quality.verdict === "qualified" ? "合格" : "需要复核";
  $("#quality-recommendation").textContent = quality.recommendation;
  const episode = quality.episode;
  $("#quality-episode-index").textContent = `#${episode.index}`;
  $("#quality-frame-count").textContent = `${episode.frames.toLocaleString("zh-CN")} / ${episode.target_frames.toLocaleString("zh-CN")}`;
  $("#quality-duration").textContent = formatDuration(episode.elapsed_seconds);
  $("#quality-progress-text").textContent = `${episode.progress.toFixed(1)}%`;
  setProgress("#quality-progress-bar", episode.progress);

  const metrics = $("#quality-metrics");
  metrics.replaceChildren();
  for (const metric of quality.metrics) {
    const card = document.createElement("article");
    card.className = `quality-metric ${metric.status}`;
    const heading = document.createElement("div");
    const label = document.createElement("span");
    label.textContent = metric.label;
    heading.append(makeIcon(metric.status === "normal" ? "circle-check" : "triangle-alert"), label);
    const value = document.createElement("strong");
    value.textContent = metric.value;
    const target = document.createElement("small");
    target.textContent = `规则 ${metric.target}`;
    card.append(heading, value, target);
    metrics.append(card);
  }

  const history = $("#quality-history-body");
  history.replaceChildren();
  const labels = { qualified: "合格", warning: "复核", discard: "建议丢弃" };
  for (const episodeItem of quality.recent_episodes) {
    const row = document.createElement("tr");
    for (const value of [`#${episodeItem.index}`, episodeItem.frames.toLocaleString("zh-CN"), episodeItem.duration, episodeItem.score]) {
      const cell = document.createElement("td");
      cell.textContent = value;
      row.append(cell);
    }
    const result = document.createElement("td");
    const chip = document.createElement("span");
    chip.className = `quality-chip compact ${episodeItem.status}`;
    chip.textContent = labels[episodeItem.status];
    result.append(chip);
    const reason = document.createElement("td");
    reason.textContent = episodeItem.reason;
    row.append(result, reason);
    history.append(row);
  }
}

function renderReport(report, alerts, generatedAt) {
  $("#report-date").textContent = new Intl.DateTimeFormat("zh-CN", { dateStyle: "long", timeStyle: "short" }).format(new Date(generatedAt));
  $("#report-datasets").textContent = report.datasets.toLocaleString("zh-CN");
  $("#report-episodes").textContent = report.episodes.toLocaleString("zh-CN");
  $("#report-frames").textContent = report.frames.toLocaleString("zh-CN");
  $("#report-pass-rate").textContent = `${report.pass_rate.toFixed(1)}%`;
  $("#report-hours").textContent = `${report.valid_hours.toFixed(2)} h`;
  $("#report-active-alerts").textContent = report.active_alerts;

  const trend = $("#trend-chart");
  trend.replaceChildren();
  const maximum = Math.max(...report.trends.map((item) => item.episodes), 1);
  for (const item of report.trends) {
    const column = document.createElement("div");
    column.className = "trend-column";
    const value = document.createElement("strong");
    value.textContent = item.episodes;
    const barWrap = document.createElement("div");
    const bar = document.createElement("span");
    bar.style.height = `${Math.max(12, item.episodes / maximum * 100)}%`;
    const rate = document.createElement("i");
    rate.style.bottom = `${Math.max(8, Math.min(94, (item.pass_rate - 90) * 10))}%`;
    rate.title = `质量通过率 ${item.pass_rate}%`;
    barWrap.append(bar, rate);
    const day = document.createElement("small");
    day.textContent = item.day;
    column.append(value, barWrap, day);
    trend.append(column);
  }

  const list = $("#alert-list");
  list.replaceChildren();
  for (const alert of alerts) {
    const row = document.createElement("article");
    row.className = `alert-row ${alert.level}`;
    const icon = document.createElement("span");
    icon.append(makeIcon(alert.level === "warning" ? "triangle-alert" : (alert.level === "resolved" ? "circle-check" : "info")));
    const text = document.createElement("div");
    const title = document.createElement("strong");
    title.textContent = alert.title;
    const detail = document.createElement("p");
    detail.textContent = alert.detail;
    text.append(title, detail);
    const meta = document.createElement("div");
    const alertState = document.createElement("strong");
    alertState.textContent = alert.state;
    const alertTime = document.createElement("small");
    alertTime.textContent = alert.time;
    meta.append(alertState, alertTime);
    row.append(icon, text, meta);
    list.append(row);
  }
  $("#alert-count").textContent = `${alerts.length} 条`;
}

async function refreshOverview(silent = true) {
  try {
    const overview = await api("/api/overview");
    renderOverview(overview);
    if (!silent) showNotice("监控与质量数据已更新");
  } catch (error) {
    if (!silent) showNotice(error.message, true);
  }
}

function filteredDatasets() {
  const query = $("#dataset-search").value.trim().toLowerCase();
  return state.datasets.filter((dataset) => {
    const matchesFilter = state.datasetFilter === "all" || dataset.quality_status === state.datasetFilter;
    const haystack = `${dataset.name} ${(dataset.tasks || []).join(" ")}`.toLowerCase();
    return matchesFilter && (!query || haystack.includes(query));
  });
}

function renderDatasets() {
  const body = $("#dataset-table-body");
  body.replaceChildren();
  const template = $("#dataset-row-template");
  const visible = filteredDatasets();
  let episodes = 0;
  let bytes = 0;
  let qualified = 0;
  for (const dataset of state.datasets) {
    episodes += dataset.episodes;
    bytes += dataset.size_bytes;
    if (dataset.quality_status === "qualified") qualified += 1;
  }
  for (const dataset of visible) {
    const row = template.content.firstElementChild.cloneNode(true);
    $(".dataset-name strong", row).textContent = dataset.name;
    $(".dataset-name span", row).textContent = `${dataset.valid ? dataset.version : "目录未完成"}${dataset.demo_only ? " · DEMO" : ""}`;
    $(".dataset-name small", row).textContent = dataset.tasks?.[0] || "未填写任务描述";
    $("[data-col=episodes]", row).textContent = dataset.episodes;
    $("[data-col=frames]", row).textContent = dataset.frames.toLocaleString("zh-CN");
    const qualityCell = $("[data-col=quality]", row);
    const quality = document.createElement("span");
    quality.className = `quality-chip compact ${dataset.quality_status}`;
    quality.textContent = `${dataset.quality_score} ${dataset.quality_status === "qualified" ? "合格" : "复核"}`;
    qualityCell.append(quality);
    $("[data-col=fps]", row).textContent = dataset.fps ? `${dataset.fps} Hz` : "-";
    $("[data-col=size]", row).textContent = formatBytes(dataset.size_bytes);
    $("[data-col=modified]", row).textContent = formatDate(dataset.modified_at);
    $(".process-dataset", row).dataset.name = dataset.name;
    $(".trace-dataset", row).dataset.name = dataset.name;
    body.append(row);
  }
  $("#dataset-empty").hidden = visible.length > 0;
  $("#dataset-total").textContent = state.datasets.length;
  $("#episode-total").textContent = episodes.toLocaleString("zh-CN");
  $("#storage-total").textContent = formatBytes(bytes);
  $("#dataset-pass-rate").textContent = state.datasets.length ? `${(qualified / state.datasets.length * 100).toFixed(0)}%` : "--";
  $("#dataset-visible-count").textContent = visible.length;
  refreshIcons();
}

async function refreshDatasets(silent = true) {
  try {
    const result = await api("/api/datasets");
    state.datasets = result.datasets;
    renderDatasets();
    if (!silent) showNotice("数据资产清单已更新");
  } catch (error) {
    showNotice(error.message, true);
  }
}

function confirmAction({ title, message, confirmLabel = "确认", danger = true }) {
  const dialog = $("#confirm-dialog");
  $("#dialog-title").textContent = title;
  $("#dialog-message").textContent = message;
  const confirmButton = $("#dialog-confirm");
  confirmButton.textContent = confirmLabel;
  confirmButton.className = `button ${danger ? "danger" : "primary"}`;
  dialog.returnValue = "cancel";
  dialog.showModal();
  return new Promise((resolve) => {
    dialog.addEventListener("close", () => resolve(dialog.returnValue === "confirm"), { once: true });
  });
}

async function postAction(path, payload = {}, successMessage = "操作完成") {
  if (state.actionPending) return;
  state.actionPending = true;
  if (state.status) renderStatus(state.status);
  try {
    const result = await api(path, { method: "POST", body: JSON.stringify(payload) });
    showNotice(result.message || successMessage);
    await Promise.all([refreshStatus(), refreshDatasets(), refreshLog()]);
    if (["monitoring", "quality", "reports"].includes(activeView())) await refreshOverview();
  } catch (error) {
    showNotice(error.message, true);
  } finally {
    state.actionPending = false;
    await refreshStatus();
  }
}

function activeView() {
  return $(".view.active")?.id.replace("view-", "") || "collection";
}

function activateView(viewName, updateUrl = false) {
  const button = $(`.tab-button[data-view="${viewName}"]`) || $(".tab-button[data-view=collection]");
  const selected = button.dataset.view;
  $$(".tab-button").forEach((item) => item.classList.toggle("active", item === button));
  $$(".view").forEach((view) => {
    const active = view.id === `view-${selected}`;
    view.classList.toggle("active", active);
    view.hidden = !active;
  });
  if (updateUrl) history.replaceState({}, "", `${location.pathname}?view=${selected}`);
  if (selected === "datasets") refreshDatasets();
  if (["monitoring", "quality", "reports"].includes(selected)) refreshOverview();
  if (selected === "diagnostics") refreshStatus();
  if (selected === "collection" && state.initialized) refreshStatus();
}

function bindTabs() {
  $$(".tab-button").forEach((button) => {
    button.addEventListener("click", () => activateView(button.dataset.view, true));
  });
}

function downloadJson(filename, value) {
  const blob = new Blob([JSON.stringify(value, null, 2)], { type: "application/json" });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  link.click();
  URL.revokeObjectURL(url);
}

function showTrace(dataset) {
  $("#trace-name").textContent = dataset.name;
  $("#trace-id").textContent = dataset.trace_id;
  $("#trace-robot").textContent = dataset.robot_type;
  $("#trace-version").textContent = dataset.version;
  $("#trace-quality").textContent = `${dataset.quality_score} / 100`;
  $("#trace-task").textContent = dataset.tasks?.[0] || "未填写";
  $("#trace-path").textContent = dataset.path;
  $("#trace-dialog").showModal();
}

function bindActions() {
  $("#session-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    if (!event.currentTarget.reportValidity()) return;
    const config = formConfig();
    const approved = await confirmAction({
      title: config.mode === "real" ? "启动真机采集会话" : "启动仿真采集会话",
      message: config.mode === "real"
        ? "将启动 G1 部署、PICO 遥操作和数据导出进程。请确认机器人周围安全，急停可用。"
        : "将启动 MuJoCo 仿真、遥操作和数据导出进程。",
      confirmLabel: "确认启动",
      danger: config.mode === "real",
    });
    if (approved) await postAction("/api/stack/start", config);
  });

  $("#stop-stack-header").addEventListener("click", async () => {
    const approved = await confirmAction({
      title: "结束采集会话",
      message: "所有 tmux 采集进程将被终止。正在录制但尚未保存的片段可能被标记为丢弃。",
      confirmLabel: "停止采集栈",
    });
    if (approved) await postAction("/api/stack/stop");
  });

  $("#record-start").addEventListener("click", () => postAction("/api/record/start"));
  $("#record-save").addEventListener("click", () => postAction("/api/record/save"));
  $("#record-discard").addEventListener("click", async () => {
    const approved = await confirmAction({
      title: "丢弃当前片段",
      message: "当前片段会写入磁盘并标记为 discarded，后续数据清洗会将其移除。",
      confirmLabel: "确认丢弃",
    });
    if (approved) await postAction("/api/record/discard");
  });

  $("#refresh-log").addEventListener("click", refreshLog);
  $("#refresh-status").addEventListener("click", () => refreshStatus(false));
  $("#refresh-monitoring").addEventListener("click", () => refreshOverview(false));
  $("#refresh-datasets").addEventListener("click", () => refreshDatasets(false));
  $("#run-quality-filter").addEventListener("click", async () => {
    await refreshOverview();
    showNotice("数据质量筛选完成：当前 Episode 合格，可保存");
  });
  $("#camera-host").addEventListener("input", (event) => {
    $("#camera-endpoint-label").textContent = `${event.target.value}:${$("#camera-port").value}`;
  });
  $("#camera-port").addEventListener("input", (event) => {
    $("#camera-endpoint-label").textContent = `${$("#camera-host").value}:${event.target.value}`;
  });
  $("#frequency").addEventListener("input", (event) => { $("#live-frequency").textContent = event.target.value || "-"; });

  $("#dataset-search").addEventListener("input", renderDatasets);
  $$(".filter-chip").forEach((button) => {
    button.addEventListener("click", () => {
      state.datasetFilter = button.dataset.filter;
      $$(".filter-chip").forEach((item) => item.classList.toggle("active", item === button));
      renderDatasets();
    });
  });

  $("#dataset-table-body").addEventListener("click", (event) => {
    const traceButton = event.target.closest(".trace-dataset");
    if (traceButton) {
      const dataset = state.datasets.find((item) => item.name === traceButton.dataset.name);
      if (dataset) showTrace(dataset);
      return;
    }
    const button = event.target.closest(".process-dataset");
    if (!button) return;
    state.selectedDataset = button.dataset.name;
    $("#process-source").textContent = `源数据集：${state.selectedDataset}`;
    $("#process-output-name").value = `${state.selectedDataset}_cleaned`;
    $("#process-dialog").showModal();
  });

  $("#process-form").addEventListener("submit", async (event) => {
    event.preventDefault();
    const output = $("#process-output-name");
    if (!output.reportValidity()) return;
    $("#process-dialog").close();
    await postAction("/api/datasets/process", {
      dataset: state.selectedDataset,
      output_name: output.value.trim(),
    });
  });

  $("#export-datasets").addEventListener("click", () => {
    downloadJson(`sonic-datasets-${new Date().toISOString().slice(0, 10)}.json`, state.datasets);
    showNotice("数据资产清单已导出");
  });
  $("#export-report").addEventListener("click", () => {
    if (!state.overview) return;
    downloadJson(`sonic-report-${new Date().toISOString().slice(0, 10)}.json`, {
      generated_at: state.overview.generated_at,
      report: state.overview.report,
      alerts: state.overview.alerts,
      quality: state.overview.quality,
    });
    showNotice("汇报摘要已导出");
  });
}

async function initialize() {
  $("#access-address").textContent = window.location.host;
  refreshIcons();
  bindTabs();
  bindActions();
  CollectionWorkspaceUI.initialize();
  activateView(new URLSearchParams(location.search).get("view") || "collection");
  await Promise.all([refreshStatus(), refreshDatasets(), refreshLog()]);
  async function poll() {
    if (document.hidden) { state.refreshHandle = setTimeout(poll, 3000); return; }
    await refreshStatus();
    if (state.status?.session_running) await refreshLog();
    if (["monitoring", "quality", "reports"].includes(activeView())) await refreshOverview();
    state.refreshHandle = setTimeout(poll, 3000);
  }
  state.refreshHandle = setTimeout(poll, 3000);
}

document.addEventListener("DOMContentLoaded", initialize);
