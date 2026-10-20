/* Collection view: real service status, metadata records and local human reviews. */
const CollectionWorkspaceUI = (() => {
  const groupNodes = new Map();
  const records = new Map();
  const loading = new Set();
  const pendingRatings = new Set();
  let snapshot = null;
  let appliedSignature = "";
  let applying = false;
  let reviewGeneration = 0;
  let videos = [];
  let playing = false;
  let syncTimer = null;
  const esc = value => String(value ?? "").replace(/[&<>"']/g, char => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[char]));
  const localDate = () => { const date = new Date(); return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`; };
  const signature = () => JSON.stringify(formConfig());
  const groupSignature = group => JSON.stringify([group.modified_at, group.episodes, group.frames, group.counts]);

  function populate(config) {
    $("#collection-date").value = config.collection_date || localDate();
    $("#scene-id").value = config.scene_id || 1;
    appliedSignature = config.dataset_name ? signature() : "";
    updateDraft();
  }

  function updateDraft() {
    const date = $("#collection-date").value.replaceAll("-", "");
    const scene = $("#scene-id").value;
    const name = $("#dataset-name").value.trim() || `${date}_scene${scene}`;
    $("#dataset-name").placeholder = `${date}_scene${scene}`;
    const root = snapshot?.status.output_root || state.status?.output_root;
    const directory = root ? `${root}/${name}` : "正在读取采集目录…";
    $("#collection-directory").textContent = directory;
    $("#collection-directory").title = directory;
    $("#copy-collection-path").disabled = !root;
    $("#scene-applied").textContent = applying ? "应用中…" : snapshot?.status.session_running ? "会话中" : signature() === appliedSignature ? "已应用" : "待应用";
    $("#apply-scene").disabled = applying || Boolean(snapshot?.status.session_running) || Boolean(state.actionPending);
  }

  function render(payload) {
    snapshot = payload;
    const status = payload.status;
    const connection = $("#collection-connection");
    connection.textContent = "已连接";
    connection.className = "connection-pill online";
    $("#episode-count").textContent = payload.totals.episodes.toLocaleString("zh-CN");
    $("#collection-dataset-count").textContent = payload.totals.datasets.toLocaleString("zh-CN");
    $("#collection-demo-count").textContent = payload.totals.demo_episodes.toLocaleString("zh-CN");
    $("#collection-record-count").textContent = `${payload.totals.episodes.toLocaleString("zh-CN")} 条真实片段`;
    $("#collection-date").disabled = status.session_running || state.actionPending;
    $("#scene-id").disabled = status.session_running || state.actionPending;
    const missing = status.prerequisites.filter(item => item.blocking && !item.ok);
    const phase = status.recording ? "正在采集" : status.session_running ? "等待录制" : "准备采集";
    $("#collection-title").textContent = phase;
    $("#collection-phase-hint").textContent = status.recording ? "当前片段正在录制，完成动作后点击保存。" : status.session_running ? "采集会话已启动，点击开始录制新片段。" : "应用场景配置，开始一次新的采集。";
    $("#collection-record-hint").textContent = status.recording ? "完成本次动作后，保存片段或丢弃重录。" : status.session_running ? "每次录制对应一条独立的采集记录。" : "采集服务就绪后，可以开始录制新片段。";
    const blocker = $("#collection-blocker");
    blocker.hidden = !missing.length;
    $("span", blocker).textContent = `启动前还需准备：${missing.map(item => item.label).join("、")}。`;
    const endpoints = new Map(status.endpoints.map(item => [item.id, item]));
    const prereqs = new Map(status.prerequisites.map(item => [item.id, item]));
    const checks = [
      { label: "采集接口", ok: true, detail: "工作台服务已连接" },
      { label: "采集环境", ...prereqs.get("data_venv") },
      { label: "tmux", ...prereqs.get("tmux") },
      ...["robot", "teleop", "camera", "exporter"].map(id => ({ ...endpoints.get(id), ok: endpoints.get(id)?.online, detail: endpoints.get(id)?.online ? "端点在线" : "尚未连接" })),
    ];
    $("#collection-checks").innerHTML = checks.map(item => `<button class="collection-check-chip ${item.ok ? "good" : "missing"}" type="button" title="${esc(item.detail)}" data-check-detail="${esc(item.detail)}">${esc(item.label)}<span class="chip-status">${item.ok ? "✓" : "—"}</span></button>`).join("");
    for (const endpoint of status.endpoints) {
      const label = $(`[data-endpoint="${endpoint.id}"] .endpoint-state`);
      if (label) label.textContent = endpoint.online ? "已连接" : "未连接";
    }
    $$(".collection-steps li").forEach((item, index) => item.classList.toggle("current", index === (status.recording ? 2 : status.session_running ? 1 : 0)));
    updateDraft();
    renderGroups();
    refreshIcons();
  }

  function offline(error) {
    $("#collection-connection").textContent = "连接中断";
    $("#collection-connection").className = "connection-pill offline";
    $("#collection-title").textContent = "等待连接";
    $("#collection-phase-hint").textContent = error.message || "请检查服务连接后重试。";
    $$("#start-stack, #stop-stack-header, #record-start, #record-save, #record-discard, #apply-scene").forEach(button => { button.disabled = true; });
  }

  function renderGroups() {
    if (!snapshot) return;
    const query = $("#collection-record-search").value.trim().toLowerCase();
    const includeDemo = $("#collection-include-demo").checked;
    const groups = snapshot.groups.filter(group => (includeDemo || !group.demo_only) && group.name.toLowerCase().includes(query));
    const visibleNames = new Set(groups.map(group => group.name));
    for (const [name, node] of groupNodes) {
      if (!visibleNames.has(name)) { node.remove(); groupNodes.delete(name); }
    }
    groups.forEach((group, index) => {
      let node = groupNodes.get(group.name);
      const isCurrent = snapshot.status.config.dataset_name === group.name;
      if (!node) {
        node = document.createElement("details");
        node.className = "collection-group";
        node.dataset.name = group.name;
        node.innerHTML = '<summary><span class="collection-group-name"></span><span class="collection-tag demo" hidden>演示数据</span><span class="collection-tag current" hidden>当前目录</span><span class="collection-group-total"></span></summary><div class="collection-group-body"></div>';
        node.open = isCurrent || index === 0;
        node.addEventListener("toggle", () => { if (node.open) loadRecords(group.name); });
        groupNodes.set(group.name, node);
      }
      $(".collection-group-name", node).textContent = group.name;
      $(".collection-tag.demo", node).hidden = !group.demo_only;
      $(".collection-tag.current", node).hidden = !isCurrent;
      $(".collection-group-total", node).textContent = `${group.retained} 条保留记录`;
      if (query && groups.length === 1) node.open = true;
      const container = $("#collection-groups");
      if (container.children[index] !== node) container.insertBefore(node, container.children[index] || null);
      if (node.open) loadRecords(group.name);
    });
    const empty = $("#collection-records-empty");
    empty.hidden = Boolean(groups.length);
    $("strong", empty).textContent = query ? "没有匹配的采集记录" : "还没有真实采集记录";
    $("span", empty).textContent = query ? "换一个数据集名称，或调整演示记录筛选。" : snapshot.totals.demo_episodes ? `现有 ${snapshot.totals.demo_episodes.toLocaleString("zh-CN")} 条演示记录，可勾选「显示演示记录」查看。` : "完成录制后，片段会按数据集显示在这里。";
  }

  async function loadRecords(name, append = false, force = false) {
    const node = groupNodes.get(name);
    const group = snapshot?.groups.find(group => group.name === name);
    if (!node?.open || !group || loading.has(name)) return;
    const cached = records.get(name);
    if (!force && !append && cached?.signature === groupSignature(group)) { renderRows(name); return; }
    const offset = append ? cached?.rows.length || 0 : 0;
    loading.add(name);
    const body = $(".collection-group-body", node);
    if (!cached) body.innerHTML = '<div class="collection-empty">正在读取记录…</div>';
    try {
      const data = await api(`/api/episodes?${new URLSearchParams({ dataset: name, offset, limit: 30 })}`);
      records.set(name, { rows: append ? [...cached.rows, ...data.episodes] : data.episodes, total: data.total, signature: groupSignature(group) });
      renderRows(name);
    } catch (error) {
      body.dataset.signature = "";
      body.innerHTML = `<div class="collection-empty"><span>${esc(error.message)}</span><button type="button" class="collection-text-button" data-records-retry="${esc(name)}">重新加载</button></div>`;
    } finally { loading.delete(name); }
  }

  function renderRows(name) {
    const node = groupNodes.get(name), cached = records.get(name), group = snapshot?.groups.find(group => group.name === name);
    if (!node?.open || !cached || !group) return;
    const body = $(".collection-group-body", node);
    const currentSignature = JSON.stringify([cached.rows, cached.total, group.counts, [...pendingRatings]]);
    if (body.dataset.signature === currentSignature) return;
    body.dataset.signature = currentSignature;
    const counts = group.counts;
    const rows = cached.rows.map(row => {
      const disabled = row.state === "discarded" || pendingRatings.has(`${name}:${row.episode_index}`);
      const grades = ["A", "B", "F"].map(grade => `<button type="button" data-rate="${grade}" data-episode="${row.episode_index}" data-dataset="${esc(name)}" aria-label="${esc(row.name)} 评为 ${grade}" aria-pressed="${row.grade === grade}" ${disabled ? "disabled" : ""}>${grade}</button>`).join("");
      return `<tr><td><strong>${esc(row.name)}</strong><small title="${esc(row.tasks.join(" · "))}">${esc(row.tasks.join(" · ") || "未记录任务描述")}</small></td><td><div class="collection-grades" role="group" aria-label="${esc(row.name)} 评级">${grades}</div>${!row.grade ? '<span class="collection-grade-note">未评级</span>' : ""}</td><td><span class="collection-saved ${row.state === "discarded" ? "discarded" : ""}">${row.state === "discarded" ? "已丢弃" : "已保存"}</span></td><td>${row.duration_seconds == null ? "—" : formatDuration(row.duration_seconds)} · ${row.frames} 帧</td><td>${row.fps ? `${row.fps} Hz` : "—"}</td><td><button class="collection-text-button" type="button" data-review-episode="${row.episode_index}" data-dataset="${esc(name)}">查看</button></td></tr>`;
    }).join("");
    body.innerHTML = `<div class="collection-group-meta"><code title="${esc(group.path)}">${esc(group.path)}</code><span>A ${counts.A} · B ${counts.B} · F ${counts.F} · 未评级 ${counts.unreviewed}</span><button type="button" class="collection-text-button" data-copy-group="${esc(group.path)}">复制路径</button></div><div class="collection-record-table-wrap"><table class="collection-record-table"><thead><tr><th>片段 / 任务</th><th>评级</th><th>状态</th><th>时长 / 帧数</th><th>频率</th><th>操作</th></tr></thead><tbody>${rows}</tbody></table></div>${cached.rows.length < cached.total ? `<button class="collection-text-button collection-load-more" type="button" data-load-more="${esc(name)}">加载更多 · 已显示 ${cached.rows.length} / ${cached.total} 条</button>` : ""}`;
  }

  async function copyPath(value) {
    try {
      if (navigator.clipboard?.writeText) await navigator.clipboard.writeText(value);
      else {
        const field = document.createElement("textarea");
        field.value = value; field.style.position = "fixed"; field.style.opacity = "0";
        document.body.append(field); field.select();
        const copied = document.execCommand("copy"); field.remove();
        if (!copied) throw new Error("复制失败，请手动复制目录文字。");
      }
      showNotice("目录已复制");
    } catch (error) { showNotice(error.message, true); }
  }

  function pauseReview() {
    playing = false;
    videos.forEach(video => video.pause());
    $("#collection-review-play").textContent = "三路播放";
  }

  function cleanupReview() {
    reviewGeneration += 1;
    pauseReview(); clearInterval(syncTimer); syncTimer = null;
    videos.forEach(video => { video.removeAttribute("src"); video.load(); });
    videos = [];
  }

  function usableVideos() { return videos.filter(video => !video.error && Number.isFinite(video.duration)); }

  function updateReview() {
    const usable = usableVideos();
    const ready = usable.length > 0;
    $("#collection-review-play").disabled = !ready;
    $("#collection-review-seek").disabled = !ready;
    const duration = ready ? Math.min(...usable.map(video => video.duration)) : 0;
    const current = usable[0]?.currentTime || 0;
    $("#collection-review-seek").max = duration || 1;
    $("#collection-review-seek").value = current;
    $("#collection-review-time").textContent = `${formatDuration(current)} / ${formatDuration(duration)}`;
    if (playing && usable.length > 1) usable.slice(1).forEach(video => { if (!video.seeking && Math.abs(video.currentTime - current) > 0.15) video.currentTime = current; });
    if (playing && current >= duration - 0.05) pauseReview();
  }

  async function openReview(name, index) {
    cleanupReview();
    const generation = reviewGeneration;
    $("#collection-review-title").textContent = `${name} / episode_${String(index).padStart(6, "0")}`;
    $("#collection-review-meta").textContent = "";
    $("#collection-review-videos").replaceChildren();
    $("#collection-review-status").textContent = "正在读取片段…";
    $("#collection-review-dialog").showModal();
    updateReview();
    try {
      const data = await api(`/api/episodes/review?${new URLSearchParams({ dataset: name, episode: index })}`);
      if (generation !== reviewGeneration) return;
      const episode = data.episode;
      $("#collection-review-meta").textContent = `${episode.demo_only ? "演示数据 · " : ""}${episode.frames} 帧 · ${episode.fps || "—"} Hz · ${episode.tasks.join(" · ") || "未记录任务描述"}`;
      if (!data.videos.length) {
        $("#collection-review-videos").innerHTML = '<div class="collection-empty"><i data-lucide="video-off"></i><strong>该片段没有可回放视频</strong><span>记录中仅包含元数据；接入相机并录制后，可在此查看多视角视频。</span></div>';
        $("#collection-review-status").textContent = "片段元数据已加载。"; refreshIcons(); return;
      }
      for (const info of data.videos.slice(0, 3)) {
        const card = document.createElement("div"); card.className = "collection-review-video";
        const video = document.createElement("video"); video.muted = true; video.playsInline = true; video.preload = "metadata";
        const message = document.createElement("span"); message.textContent = "正在加载画面…";
        const label = document.createElement("strong"); label.textContent = info.label;
        card.append(video, message, label); $("#collection-review-videos").append(card); videos.push(video);
        video.addEventListener("loadedmetadata", () => { message.hidden = true; updateReview(); });
        video.addEventListener("error", () => { message.hidden = false; message.textContent = "视频读取失败"; updateReview(); $("#collection-review-status").textContent = "部分视频读取失败，可播放已就绪的画面。"; });
        video.addEventListener("ended", pauseReview);
        video.src = info.url;
      }
      $("#collection-review-status").textContent = `${data.videos.length} 路视频 · 支持同步播放、拖动进度与倍速。`;
      syncTimer = setInterval(updateReview, 150);
    } catch (error) { if (generation === reviewGeneration) $("#collection-review-status").textContent = error.message; }
  }

  function initialize() {
    $$("[data-open-diagnostics]").forEach(button => button.addEventListener("click", () => activateView("diagnostics", true)));
    $("#collection-check").addEventListener("click", async () => { await refreshStatus(false); if (state.status?.prerequisites.some(item => !item.ok && item.blocking)) activateView("diagnostics", true); });
    $("#collection-checks").addEventListener("click", event => { const button = event.target.closest("[data-check-detail]"); if (button) showNotice(button.dataset.checkDetail); });
    $$("#session-form input, #session-form textarea, #collection-date, #scene-id").forEach(input => input.addEventListener("input", updateDraft));
    $$("input[name=mode]").forEach(input => input.addEventListener("change", () => refreshStatus()));
    $("#copy-collection-path").addEventListener("click", () => copyPath($("#collection-directory").textContent));
    $("#collection-record-search").addEventListener("input", renderGroups);
    $("#collection-include-demo").addEventListener("change", renderGroups);
    $("#refresh-collection-records").addEventListener("click", async () => { records.clear(); await refreshStatus(false); });
    $("#apply-scene").addEventListener("click", async () => {
      if (applying || !$("#session-form").reportValidity()) return;
      applying = true; updateDraft();
      try {
        const result = await api("/api/collection/config", { method: "POST", body: JSON.stringify(formConfig()) });
        populateForm(result.config); appliedSignature = signature();
        await refreshStatus(); showNotice(result.message);
      } catch (error) { showNotice(error.message, true); }
      finally { applying = false; updateDraft(); }
    });
    $("#collection-groups").addEventListener("click", async event => {
      const button = event.target.closest("button");
      if (!button || button.disabled) return;
      if (button.dataset.loadMore) return loadRecords(button.dataset.loadMore, true);
      if (button.dataset.recordsRetry) return loadRecords(button.dataset.recordsRetry, false, true);
      if (button.dataset.copyGroup) return copyPath(button.dataset.copyGroup);
      if (button.dataset.reviewEpisode != null) return openReview(button.dataset.dataset, Number(button.dataset.reviewEpisode));
      if (!button.dataset.rate) return;
      const name = button.dataset.dataset, index = Number(button.dataset.episode), key = `${name}:${index}`;
      if (pendingRatings.has(key)) return;
      pendingRatings.add(key); renderRows(name);
      try {
        await api("/api/episodes/rate", { method: "POST", body: JSON.stringify({ dataset: name, episode: index, grade: button.getAttribute("aria-pressed") === "true" ? null : button.dataset.rate }) });
        records.delete(name); await refreshStatus(); showNotice("评级已保存");
      } catch (error) { showNotice(error.message, true); }
      finally { pendingRatings.delete(key); renderRows(name); }
    });
    $("#collection-review-close").addEventListener("click", () => $("#collection-review-dialog").close());
    $("#collection-review-dialog").addEventListener("close", cleanupReview);
    $("#collection-review-play").addEventListener("click", async () => {
      if (playing) return pauseReview();
      const usable = usableVideos(); if (!usable.length) return;
      const duration = Math.min(...usable.map(video => video.duration));
      if (usable[0].currentTime >= duration - .05) usable.forEach(video => { video.currentTime = 0; });
      usable.forEach(video => { video.playbackRate = Number($("#collection-review-speed").value); });
      const outcomes = await Promise.allSettled(usable.map(video => video.play()));
      if (outcomes.every(outcome => outcome.status === "rejected")) { $("#collection-review-status").textContent = "当前浏览器无法播放这些视频。"; return; }
      playing = true; $("#collection-review-play").textContent = "暂停";
    });
    $("#collection-review-seek").addEventListener("input", event => { pauseReview(); usableVideos().forEach(video => { video.currentTime = Math.min(Number(event.target.value), video.duration); }); });
    $("#collection-review-speed").addEventListener("change", event => { videos.forEach(video => { video.playbackRate = Number(event.target.value); }); });
  }

  return { initialize, populate, render, offline, updateDraft };
})();
