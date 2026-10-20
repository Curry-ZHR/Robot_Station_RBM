import { VIEWS, CAMERAS, SERVICE_DEFS, STAGES, esc, clone, finite, clock, duration, degree, uid, fresh, batteryReading, namedJointValues, jointLabel, safeMediaURL, emptySnapshot } from './console-core.js';
import { StationTools, toolsView, posesPanel, realCommissioningPanel } from './console-tools.js';
import { ConsoleAPI } from './console-api.js';
import { conversionView, DataConversionPage } from './console-conversion.js';
import { NODE_TYPES, templateGraph, validateGraph, executionGraph, WorkflowEditor, WorkflowRunner } from './console-workflow.js';
import { PlaybackController } from './console-playback.js';

const $ = (selector, root = document) => root.querySelector(selector);
const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
const icon = name => `<i data-lucide="${name}" aria-hidden="true"></i>`;
const badge = (text, tone = '') => `<span class="badge ${tone}">${esc(text)}</span>`;
const ownerLabel = owner => ({manual:'手动调试', pico:'PICO 遥操作', 'task-model':'任务模型', workflow:'状态机'})[owner] || '未接管';
const statusLabel = state => ({running:'运行中',ready:'就绪',stopped:'已停止',offline:'离线',streaming:'视频就绪',disconnected:'未连接',idle:'待启动',pending:'排队中',waiting:'等待设备',preparing:'准备中',saving:'保存中',ended:'已结束',failed:'失败',succeeded:'已完成',passed:'通过',blocked:'待处理',cancelled:'已取消'})[state] || '未知';
const readStore = (key, fallback) => { try { return JSON.parse(localStorage.getItem(key)) ?? fallback; } catch { return fallback; } };
const saveStore = (key, value) => { try { localStorage.setItem(key, JSON.stringify(value)); } catch { toast('浏览器未允许保存本地草稿', 'danger'); } };
let profile;
try { const response = await fetch('/assets/g1/profile.json'); if (!response.ok) throw new Error(); profile = await response.json(); }
catch { $('#app').innerHTML='<div class="boot"><h1>模型配置无法加载</h1><p>请检查工作台静态资源，然后刷新页面。</p><button onclick="location.reload()">重新加载</button></div>'; throw new Error('G1 profile missing'); }
profile.groups = Object.fromEntries(profile.groups.map(group => [group.id, group.joints]));
const app = {
  view: VIEWS.some(v=>v[0]===location.hash.slice(1)) ? location.hash.slice(1) : 'inference',
  preview: new URLSearchParams(location.search).get('preview') === '1', mode:'sim', snapshot:emptySnapshot(),
  group:'left_arm', sensor:'head', target:false, targets:Object.fromEntries(profile.body_joints.map(n=>[n,0])),
  config: readStore('robot-station-console-config-v1', { endpoint:'', model:'', protocol:'named-joint-rad-v1', hz:30, prompt:'', record:false, dataset:'g1_teleop', task:'', fps:30 }),
  dataset:'', episodes:[], total:0, offset:0, search:'', loadingEpisodes:false, episodeError:'', playback:null,
  graph:readStore('robot-station-workflow-v1',null), flowSelection:null, flowLog:[], busy:false, job:null, localEvents:[], renderId:0,
};
if (!app.graph || validateGraph(app.graph).length) app.graph=templateGraph('inference');
const api = new ConsoleAPI({profile,preview:app.preview,mode:app.mode});
let robotScene=null, playback=null, editor=null, runner=null, pollBusy=false, conversionPage=null, stationTools=null;
const commandButton = (scope, action, label, type='', payload={}) => `<button class="btn ${type}" data-command="${scope}" data-op="${action}" data-payload="${esc(JSON.stringify(payload))}" title="${esc(api.can(scope,action,payload))}" ${api.can(scope,action,payload)?'disabled':''}>${label}</button>`;
const textBinding = (id, initial='--') => `<span data-text="${id}">${esc(initial)}</span>`;
const field = (label,name,type='text',extra='') => `<label class="field">${label}<input type="${type}" data-config="${name}" value="${esc(app.config[name]??'')}" ${extra}></label>`;
const cameraHTML = (id,replay=false) => {
 const c=CAMERAS.find(c=>c.id===id);
 return `<article class="camera-card" data-camera="${id}"><div class="camera-picture"><video muted playsinline ${replay?'':'loop autoplay'} ${replay?`data-replay-camera="${id}" data-has-video="false"`:''}></video><img alt="${c.label}实时画面"><div class="camera-placeholder">${icon('video-off')}<span data-camera-message>等待相机连接</span></div><span class="camera-tag">${c.short}</span><span class="camera-source" ${app.preview?'':'hidden'}>合成预演</span>${replay?'':`<button class="camera-max" data-action="camera-expand" data-id="${id}" title="放大${c.label}" aria-label="放大${c.label}">${icon('maximize')}</button>`}</div><footer class="camera-foot"><b>${c.label}</b><small data-camera-stat>-- FPS · 未连接</small></footer></article>`;
};
const camerasHTML = () => `<div class="camera-grid">${CAMERAS.map(c=>cameraHTML(c.id)).join('')}</div>`;
const cardHead = (title,ico,right='') => `<div class="card-head"><h2 class="card-title">${icon(ico)}${title}</h2>${right}</div>`;
const notices = () => !app.preview&&app.view==='conversion' ? `<div class="notice">${icon('file-check-2')}离线数据转换 · 从已保存的 SONIC 数据生成新副本，不占用机器人控制权。</div>` : app.preview ? `<div class="notice preview">${icon('flask-conical')}<div><b>界面预演</b> · 电量、姿态、视频与执行结果均为合成数据，所有操作只在浏览器内运行。<span class="muted"> 退出预演后恢复真实连接状态。</span><div class="row wrap" style="margin-top:7px"><label class="tiny" for="preview-fault">预演场景</label><select id="preview-fault" data-preview-fault style="width:160px;min-height:28px;padding:4px 8px;font-size:10px"><option value="">设备正常</option><option value="low-battery">低电量</option><option value="camera-offline">左腕相机断流</option><option value="robot-offline">机器人反馈中断</option></select></div></div></div>` : `<div class="notice" data-live-notice>${icon('info')}<span data-text="connection-message">正在检查执行端接口…</span></div>`;
function shell(){
 $('#app').innerHTML=`<aside class="sidebar"><div class="brand"><span class="brand-mark">R</span><div><b>ROBOT STATION</b><small>EMBODIED WORKSPACE</small></div></div><div class="nav-label">WORKSPACE</div><nav>${VIEWS.map((v,i)=>`${i===5?'<div class="nav-split"></div>':''}<a class="nav-link ${v[0]===app.view?'active':''}" href="#${v[0]}" data-nav="${v[0]}">${icon(v[2])}<span>${v[1]}</span></a>`).join('')}</nav><div class="sidebar-bottom"><div class="workstation">${icon('monitor')}<div><b>Ubuntu · RTX 4070</b><span>G1 / SONIC 工作空间</span></div></div><div class="side-version"><span>CONSOLE v1.0</span><span class="side-connection" data-console-connection data-state="checking" role="status" aria-live="polite" title="正在检查网页与4070执行端的连接"><span class="dot" aria-hidden="true"></span><span data-console-connection-label>Checking</span></span></div></div></aside><div class="shell"><header class="topbar"><button class="icon-button mobile-menu" data-action="menu" aria-label="展开导航">${icon('menu')}</button><div class="breadcrumb">工作空间 <span>/</span> <strong data-page-name>推理工作台</strong></div><div class="top-spacer"></div><div class="top-status top-optional"><span class="dot" data-backend-dot></span><span data-text="backend">接口检查中</span></div><select class="mode-select" data-mode aria-label="运行环境"><option value="sim">仿真环境</option><option value="real">真机环境</option></select><span class="top-divider"></span><div class="top-status top-robot-status">${icon('bot')}<span data-text="robot">G1 未连接</span></div><div class="battery muted" data-battery title="电池反馈尚未接入"><span class="battery-icon"><span style="width:0%"></span></span><b data-text="battery">--%</b></div><span class="top-divider"></span><button class="icon-button top-optional" data-action="events" aria-label="事件与日志" title="事件与日志">${icon('bell')}</button><button class="stop-button" data-command="safety" data-op="stop" data-payload="{}" title="执行端接口尚未接入" disabled>${icon('square')}停止任务</button></header><main id="main"></main></div><div class="toast-stack" aria-live="polite" aria-atomic="false"></div><div id="overlay-root"></div>`;
 document.addEventListener('click',handleClick);
 document.addEventListener('input',handleInput);
 document.addEventListener('change',handleChange);
 window.addEventListener('popstate',()=>{const view=location.hash.slice(1);if(VIEWS.some(v=>v[0]===view)){app.view=view;render();}});
 window.addEventListener('hashchange',()=>{const v=location.hash.slice(1);if(VIEWS.some(row=>row[0]===v)&&v!==app.view){app.view=v;render();}});
 document.addEventListener('keydown',event=>{if(event.key==='Escape'){closeModal();$('.sidebar')?.classList.remove('open');if(editor){editor.linkFrom=null;editor.root.dataset.linking='false';}}});
 render();
}
function heading(){
 const v=VIEWS.find(row=>row[0]===app.view);
 return `<div class="page-heading"><div><div class="eyebrow">G1 WORKSPACE / ${app.view.toUpperCase()}</div><h1>${v[1]}</h1><p>${({inference:'从任务模型到 SONIC，全流程查看与执行',startup:'连接设备之前，先把每一步准备清楚',machine:'掌握设备运行状态与唯一控制源',body:'观察 G1 身体关节，预览目标姿态',sensors:'头部、左腕与右腕，同步观察现场',collection:'用 PICO 遥操作采集，管理每一段数据',playback:'让视频、机器人姿态与动作曲线在同一时间轴对齐',workflow:'把准备、推理与采集编排为清晰的流程',connections:'配置接入参数，诊断实际链路并恢复连接方案',conversion:'校验 SONIC 原生数据，导出 HDF5 或 LeRobot 训练数据'})[app.view]}</p></div><div class="row"><button class="btn" data-action="unlock" hidden>授权操作</button><button class="btn preview-toggle ${app.preview?'enabled':''}" data-action="preview">${icon('flask-conical')}${app.preview?'退出界面预演':'界面预演'}</button><button class="btn" data-action="refresh">${icon('refresh-cw')}刷新状态</button></div></div>${notices()}`;
}
function goView(view){app.view=view;history.pushState(null,'','#'+view);render();window.scrollTo({top:0});}
function render(){
 app.renderId++; const id=app.renderId;
 conversionPage?.dispose();conversionPage=null;stationTools?.dispose();stationTools=null;
 robotScene?.dispose();robotScene=null;playback?.dispose();playback=null;editor?.dispose();editor=null;runner?.stop();runner=null;
 $$('video[data-camera-live]').forEach(v=>{v.pause();v.removeAttribute('src');v.load();});
 $$('.nav-link').forEach(el=>{el.classList.toggle('active',el.dataset.nav===app.view);if(el.dataset.nav===app.view)el.setAttribute('aria-current','page');else el.removeAttribute('aria-current');});
 $('[data-page-name]').textContent=VIEWS.find(v=>v[0]===app.view)[1];
 $('.sidebar').classList.remove('open');
 const templates={inference:inferenceView,startup:startupView,machine:machineView,body:bodyView,sensors:sensorsView,collection:collectionView,playback:playbackView,workflow:workflowView,conversion:conversionView,connections:toolsView};
 $('#main').innerHTML=heading()+templates[app.view]()+`<footer class="footer-note"><span>ROBOT STATION · G1 29 DOF / SONIC</span><span>${app.preview?'本地界面预演 · 合成数据':'状态与控制以执行端反馈为准'} · 最后更新 ${textBinding('updated')}</span></footer>`;
 $$('[data-config]').forEach(el=>{if(el.tagName==='SELECT')el.value=app.config[el.dataset.config];});
 if($('[data-preview-fault]'))$('[data-preview-fault]').value=api.runtime.fault;
 icons();update();
 if(['body','connections'].includes(app.view))stationTools=new StationTools($('#main'),{api,app,profile,toast,setTargets:rows=>{for(const row of rows)app.targets[row.name]=row.position_rad;app.target=true;render();},previewFrame:values=>{app.target=true;profile.body_joints.forEach((n,i)=>app.targets[n]=values[i]);robotScene?.setPose(values);for(const el of $$('[data-target-joint],[data-target-slider]'))el.value=degree(app.targets[el.dataset.targetJoint||el.dataset.targetSlider]);}});
 if(app.view==='body')initRobot('[data-robot-scene]',id);
 if(app.view==='collection'||app.view==='playback')loadEpisodes();
 if(app.view==='playback'&&app.playback)setupPlayback(id);
 if(app.view==='workflow')setupWorkflow();
 if(app.view==='conversion'){app.conversionState??={};conversionPage=new DataConversionPage($('#main'),api,app.preview,app.conversionState);}
}
function inferenceView(){return `<div class="inference-layout"><div class="stack"><section class="card">${cardHead('现场观测','scan-eye',badge('3 路相机','blue'))}<div class="card-body">${camerasHTML()}<div class="pipeline"><span class="pipeline-box">三路图像 + 机器人状态</span>${icon('arrow-right')}<span class="pipeline-box">任务模型</span>${icon('arrow-right')}<span class="pipeline-box">动作适配</span>${icon('arrow-right')}<span class="pipeline-box">SONIC → G1</span></div></div></section><section class="card">${cardHead('任务模型','sparkles',`<span data-model-badge>${badge('未连接')}</span>`)}<div class="card-body"><div class="section-label"><span>01</span> 模型连接</div><div class="fields">${field('模型服务地址','endpoint','url','placeholder="http://工作站地址:端口" autocomplete="off"')}${field('模型 / 检查点标识','model','text','placeholder="由后端配置的模型标识"')}<label class="field">动作协议<select data-config="protocol"><option value="named-joint-rad-v1">具名关节 · rad</option><option value="body-command-v1">SONIC 身体指令</option><option value="custom-adapter-v1">自定义动作适配器</option></select></label>${field('期望执行频率（Hz）','hz','number','min="1" max="200" step="1"')}</div><div class="row between section-gap"><span class="help" style="margin:0">协议、维度和单位由执行端握手校验</span><div class="row">${commandButton('inference','disconnect','断开','sm')}${commandButton('inference','connect',icon('plug')+'连接模型','soft sm')}</div></div><div class="divider"></div><div class="section-label"><span>02</span> 任务指令</div><label class="field"><span class="sr-label">描述机器人需要完成的任务</span><textarea class="model-prompt" data-config="prompt" placeholder="例如：将桌面上的物体放入右侧收纳盒">${esc(app.config.prompt)}</textarea></label><div class="row between section-gap"><label class="check-label"><input type="checkbox" data-config="record" ${app.config.record?'checked':''}> 同时记录推理过程</label><span class="tiny muted">记录能力由后端提供</span></div></div></section><section class="card">${cardHead('动作接口约定','git-compare-arrows',badge('适配器校验','blue'))}<div class="card-body"><div class="contract-line"><span>输入</span><b>camera × 3 + named state + task</b></div><div class="contract-line"><span>输出</span><b>具名关节 / 身体指令 → 适配器</b></div><div class="contract-line"><span>全身执行</span><b>SONIC 策略 → G1 · 29 DOF</b></div><div class="contract-line"><span>握手结果</span><b data-text="adapter-status">待校验</b></div><div class="contract-line"><span>输出维度 / 单位 / 频率</span><b data-text="adapter-schema">-- / -- / --</b></div><p class="help">执行端需核对动作语义、关节名称、单位、频率与限幅，并确认控制权后开放运行。</p></div></section></div><div class="stack"><section class="card">${cardHead('任务执行','play',`<span data-inference-badge>${badge('待准备')}</span>`)}<div class="card-body"><div class="execution-block"><div class="row between"><span class="tiny muted">TASK MODEL</span><span class="dot" data-model-dot></span></div><div class="big" data-text="model-state">未连接 <small>任务模型</small></div><p class="help" data-text="model-detail">连接模型并取得任务控制权后开始</p></div><div class="metric-grid"><div class="metric"><b data-text="steps">0</b><small>执行步数</small></div><div class="metric"><b data-text="latency">--</b><small>延迟 / ms</small></div><div class="metric"><b data-text="frequency">--</b><small>反馈 / Hz</small></div></div><div class="row">${commandButton('inference','start',icon('play')+'开始推理','primary full')}${commandButton('inference','stop',icon('square')+'停止','full')}</div><p class="help" data-infer-reason>等待执行端就绪</p></div></section><section class="card">${cardHead('SONIC 全身执行','cpu',badge('LOWER LAYER','purple'))}<div class="card-body"><div class="kv"><span>控制器</span><strong data-text="controller">未接入</strong></div><div class="kv"><span>机器人反馈</span><strong data-text="feedback">未连接</strong></div><div class="kv"><span>身体关节</span><strong data-text="joint-count">-- / 29</strong></div><div class="kv"><span>控制源</span><strong data-text="owner">未接管</strong></div><div class="kv"><span>执行模式</span><strong data-text="robot-mode">OFF</strong></div><div class="divider"></div>${commandButton('robot','claim',icon('shield-check')+'申请任务模型控制权','soft full',{owner:'task-model'})}<div class="row between" style="margin-top:10px"><a href="#startup" class="tiny">前往自检与启动 →</a><a href="#body" class="tiny">查看全身关节 →</a></div></div></section><section class="card">${cardHead('最近事件','activity',`<button class="btn text sm" data-action="events">全部事件</button>`)}<div class="card-body" data-events-mini>${empty('等待执行端事件','activity')}</div></section></div></div>`;}
function empty(message,ico='inbox'){return `<div class="empty">${icon(ico)}${esc(message)}</div>`;}
function summaryCard(ico,label,value,unit=''){return `<div class="card summary"><div class="summary-icon">${icon(ico)}</div><div><b>${value}<span class="unit">${unit}</span></b><small>${label}</small></div></div>`;}
function startupView(){return `<div class="summary-strip">${summaryCard('list-checks','检查通过',textBinding('check-count'),'项')}${summaryCard('camera','相机画面',textBinding('camera-count'),'/ 3')}${summaryCard('person-standing','关节反馈',textBinding('joint-count-small'),'/ 29')}${summaryCard('shield','控制源',textBinding('owner-short'))}</div><section class="card">${cardHead('启动向导','route',`<span data-deployment-badge>${badge('等待自检')}</span>`)}<div class="card-body"><div class="stage-list" data-stages></div><div class="row wrap section-gap">${commandButton('self_check','run',icon('list-checks')+'重新自检','')}${commandButton('deployment','prepare',icon('play')+'按步骤准备 SONIC','primary',{allow_motion:false})}${commandButton('deployment','cancel','取消准备','')}<span class="tiny muted" data-text="job-message">准备过程不申请运动控制权</span></div><p class="help">向导准备容器、PC Service 和只读订阅，不启动运动控制。设备未连接时显示等待设备，接入后可重新检查。</p><details class="section-gap"><summary>查看准备日志</summary><pre class="runtime-log" data-deployment-log>尚无准备任务</pre></details></div></section><section class="card section-gap">${cardHead('自检清单','clipboard-check',`<small>真实状态由 4070 执行端返回</small>`)}<div class="table-scroll"><table class="check-table"><thead><tr><th>检查项</th><th>状态</th><th>说明 / 下一步</th><th>来源</th></tr></thead><tbody data-checks></tbody></table></div></section><section class="card section-gap">${cardHead('到现场后的连接顺序','cable')}<div class="card-body steps-help"><div><b>01 · 连接网络与设备</b><p>4070 有线接 G1 的 192.168.123 网段；另一网卡与 PICO 4 接入同一局域网，确认路由与发现接口。</p></div><div><b>02 · 检查 PICO 与三路相机</b><p>打开 XRoboToolkit，完成腿部追踪器配对、标定与姿态检查，确认头部和左右腕画面。</p></div><div><b>03 · 选择任务并申请控制权</b><p>先验证只读反馈，再进行现场初始化与控制源切换。采集和推理分别运行，各自确认就绪条件。</p></div></div></section>`;}
function machineView(){return `<div class="equal-columns"><section class="card">${cardHead('G1 电池与连接','battery-medium',`<span data-robot-badge>${badge('未连接')}</span>`)}<div class="card-body"><div class="battery-large muted" data-battery-large><span class="battery-icon"><span style="width:0"></span></span><div><strong data-text="battery-large">--</strong><span class="unit"> %</span><p class="tiny muted" style="margin-top:7px" data-text="battery-detail">等待电池反馈</p></div></div><div class="kv"><span>采样时间</span><strong data-text="battery-time">--</strong></div><div class="kv"><span>电压 / 电流</span><strong data-text="battery-electrical">-- / --</strong></div><div class="kv"><span>机器人反馈</span><strong data-text="feedback">未连接</strong></div><p class="help">电池读数过期或机器人断连时显示未知。低于后端配置的阈值时高亮提醒。</p></div></section><section class="card">${cardHead('整机控制权','shield-check',badge('单一控制源','blue'))}<div class="card-body"><div class="owner-card"><div class="kv"><span>当前控制源</span><strong data-text="owner">未接管</strong></div><div class="kv"><span>执行模式</span><strong data-text="robot-mode">OFF</strong></div></div><div class="row wrap section-gap">${commandButton('robot','connect',icon('link')+'只读连接','')}${commandButton('robot','initialize','初始化机器人','')}${commandButton('robot','claim','任务模型接管','soft',{owner:'task-model'})}${commandButton('robot','claim','手动调试接管','',{owner:'manual'})}${commandButton('robot','release','释放控制权','')}</div><div class="divider"></div><div class="row wrap"><span class="tiny muted">执行模式</span>${['OFF','PLANNER','MIMIC'].map(mode=>commandButton('robot','set_mode',mode,'sm',{mode})).join('')}</div><p class="help">模式切换和接管须通过后端互锁。正在采集或推理时，应先结束当前任务。</p></div></section></div><section class="section-gap"><div class="row between" style="margin-bottom:13px"><h2 class="card-title">${icon('server')}运行服务</h2><span class="tiny muted">4070 / sonic_deploy</span></div><div class="service-grid">${SERVICE_DEFS.map(([id,label,ico,description])=>`<article class="card service-card">${icon(ico)}<div class="row between"><h3>${label}</h3><span data-service-badge="${id}">${badge('待接入')}</span></div><p>${description}</p><div class="row between"><span class="tiny muted" data-service-detail="${id}">接口待接入</span><div class="row">${commandButton('services','start','启动','sm',{service_id:id})}${commandButton('services','stop','停止','sm',{service_id:id})}</div></div></article>`).join('')}</div></section>`;}
function jointTargetPercent(spec,value){return Math.max(0,Math.min(100,(value-spec.lower)/(spec.upper-spec.lower)*100));}
function bodyView(){const group=profile.groups[app.group]||profile.body_joints;return `<div class="notice warning">${icon('move-3d')}<span>滑条默认只预览目标。仿真可直接初始化 MuJoCo 并接管。真机适配已接入，须完成本地现场标定并通过只读预检，取得控制权后才能启用联动。</span></div><div class="body-layout"><div class="stack"><section class="card">${cardHead('Unitree G1 · 29 DOF','person-standing',badge('URDF 参考模型','blue'))}<div class="robot-viewer" data-robot-scene><div class="model-note"><span class="badge" data-pose-label>参考姿态 · 无实时反馈</span></div><div class="viewer-toolbar"><span>拖动旋转 · 滚轮缩放</span><button class="btn sm" data-action="reset-view">${icon('rotate-ccw')}视角复位</button></div></div></section><section class="card"><div class="card-body"><div class="row between"><label class="check-label"><input type="checkbox" data-target-preview ${app.target?'checked':''}> 显示目标预览</label><span class="tiny muted">输入单位：度（°）</span></div><div class="row wrap section-gap">${commandButton('robot','initialize',app.mode==='real'?'初始化真机连接':'初始化 MuJoCo','sm')}${commandButton('robot','claim','手动接管','soft sm',{owner:'manual'})}${commandButton('robot','release','释放控制权','sm')}<button class="btn sm" data-action="copy-pose">复制当前反馈</button><button class="btn sm" data-action="zero-pose">参考零姿态</button>${commandButton('robot','apply_pose','下发目标姿态','primary sm')}</div><label class="check-label section-gap"><input type="checkbox" data-live-manual ${app.liveManual?'checked':''}> 滑条实时联动${app.mode==='real'?'真机':'物理仿真'}（取得手动控制权后可用）</label><p class="help" data-manual-state>尚未发送目标</p><p class="help">${app.mode==='real'?'仅用于机械支撑下的关节调试，不支持自由站立平衡。租约过期按已核定的阻尼/禁用策略退出；反馈失效或控制源冲突会停止本适配器输出。':'MuJoCo 使用固定基座和真实惯性、重力、扭矩步进，不验证站立平衡。心跳中断 3 秒释放控制并保持当前位置。'}</p></div></section>${posesPanel()}${app.mode==='real'?realCommissioningPanel():''}</div><section class="card">${cardHead('身体关节','sliders-horizontal',`<span class="tiny muted">${textBinding('joint-count')} · 反馈 rad → °</span>`)}<div class="card-body"><div class="joint-tabs">${Object.keys(profile.groups).map(id=>`<button class="${app.group===id?'active':''}" data-action="joint-group" data-id="${id}">${({left_arm:'左臂 · 7',right_arm:'右臂 · 7',waist:'腰部 · 3',left_leg:'左腿 · 6',right_leg:'右腿 · 6'})[id]||id}</button>`).join('')}</div></div><div class="joint-scroll table-scroll"><table class="joint-table"><thead><tr><th>关节</th><th>反馈 °</th><th>目标 °</th><th>参考范围 °</th><th>温度 °C</th></tr></thead><tbody>${group.map(name=>{const spec=profile.joints.find(j=>j.name===name);return `<tr><td>${jointLabel(name)}<small>${esc(name)}</small></td><td data-joint-feedback="${name}">--</td><td><div class="joint-target-control"><div class="joint-target-value"><input type="number" step="0.1" min="${degree(spec.lower)}" max="${degree(spec.upper)}" value="${degree(app.targets[name])}" data-target-joint="${name}" aria-label="${jointLabel(name)}目标角度"><span aria-hidden="true">°</span></div><input type="range" class="joint-target-slider" min="${degree(spec.lower)}" max="${degree(spec.upper)}" step="0.1" value="${degree(app.targets[name])}" data-target-slider="${name}" aria-label="${jointLabel(name)}目标角度滑条" aria-valuetext="${degree(app.targets[name])} 度，仅本地预览" style="--joint-fill:${jointTargetPercent(spec,app.targets[name])}%" title="拖动仅更新本地目标姿态"></div></td><td class="tiny">${degree(spec.lower)} ~ ${degree(spec.upper)}</td><td data-joint-temperature="${name}">--</td></tr>`;}).join('')}</tbody></table></div><div class="card-foot">29 个身体关节，不含手指。实际反馈和目标分开显示；实时联动仅在显式开启后发送。</div></section></div>`;}
function sensorsView(){return `<div class="sensor-layout"><section class="card">${cardHead('实时画面','camera',`<span class="tiny muted">${textBinding('camera-count')} / 3 路就绪</span>`)}<div class="card-body"><div class="sensor-main">${cameraHTML(app.sensor)}</div><div class="sensor-small">${CAMERAS.filter(c=>c.id!==app.sensor).map(c=>cameraHTML(c.id)).join('')}</div><div class="row wrap section-gap">${CAMERAS.map(c=>`<button class="btn sm ${app.sensor===c.id?'soft':''}" data-action="sensor-main" data-id="${c.id}">${c.label}设为主视角</button>`).join('')}</div></div></section><div class="stack"><section class="card">${cardHead('传感器状态','radio')}<div class="card-body">${CAMERAS.map(c=>`<div class="kv"><span>${c.label}</span><strong data-camera-health="${c.id}">未连接</strong></div>`).join('')}<div class="divider"></div><div class="kv"><span>机器人状态流</span><strong data-text="feedback">未连接</strong></div><div class="kv"><span>XRoboToolkit</span><strong data-text="xr-status">未接入</strong></div><p class="help">画面和时间戳由相机服务提供。断流、格式不支持或帧时间过期会在对应视角中提示。</p></div></section><section class="card">${cardHead('画面接入','plug')}<div class="card-body"><div class="contract-line"><span>图像来源</span><b data-text="camera-source">等待状态</b></div><div class="contract-line"><span>桥接状态</span><b data-text="camera-bridge-state">--</b></div><p class="help mono" data-text="camera-ros-topics" style="overflow-wrap:anywhere"></p><div class="contract-line"><span>相机标识</span><b>head / left_wrist / right_wrist</b></div><div class="contract-line"><span>当前播放器</span><b>MJPEG / 浏览器原生视频</b></div><p class="help">视频代理通过工作台同源接口提供，执行端负责设备地址、转码和时间同步。</p></div></section></div></div>`;}
function collectionView(){return `<div class="summary-strip">${summaryCard('database','正式片段',textBinding('episodes'),'段')}${summaryCard('folder','正式数据集',textBinding('datasets'),'个')}${summaryCard('flask-conical','演示片段',textBinding('demo-episodes'),'段')}${summaryCard('circle-dot','当前录制',textBinding('recording-short'))}</div><div class="two-column"><div class="stack"><section class="card">${cardHead('PICO 遥操作采集','circle-dot',badge('独立采集任务','blue'))}<div class="card-body"><div class="fields">${field('数据集名称','dataset','text','pattern="[A-Za-z0-9_-]+" placeholder="g1_teleop"')}${field('目标录制帧率','fps','number','min="1" max="120"')}<label class="field wide">任务描述<textarea data-config="task" placeholder="描述本次遥操作采集的任务">${esc(app.config.task)}</textarea></label></div><div class="row between section-gap"><span class="help" style="margin:0" data-text="collection-ready">等待 PICO、相机和机器人反馈</span>${commandButton('collection','prepare',icon('settings-2')+'准备采集','soft')}</div><div class="divider"></div><div class="record-hero"><div><span class="record-light" data-record-light><span class="dot"></span><span data-text="recording-state">尚未录制</span></span><div class="record-time" data-text="record-time">00:00</div><small class="tiny">三路图像 + 完整状态 / 动作（含手部）</small></div><div class="record-actions">${commandButton('collection','start',icon('circle-dot')+'开始录制','primary')}<div class="row">${commandButton('collection','save','保存','success full')}${commandButton('collection','discard','舍弃','danger full')}</div>${commandButton('collection','end','结束采集任务','sm')}</div></div><p class="help">本页管理录制任务，SONIC 运动控制需先在现场启动。保存后可评级并回放；舍弃保留当前片段并标记为舍弃。</p><details class="section-gap"><summary>采集进程与日志</summary><p class="help" data-text="collection-worker-state">待启动</p><button class="btn sm" data-action="collection-logs">读取采集日志</button><pre class="runtime-log" data-collection-log>尚未读取</pre></details></div></section><section class="card">${cardHead('采集视角','camera',badge('CAMERA × 3'))}<div class="card-body">${camerasHTML()}</div></section></div><div class="stack"><section class="card">${cardHead('采集就绪条件','clipboard-check')}<div class="card-body"><div class="kv"><span>机器人反馈</span><strong data-text="feedback">未连接</strong></div><div class="kv"><span>相机</span><strong>${textBinding('camera-count')} / 3 路</strong></div><div class="kv"><span>XRoboToolkit</span><strong data-text="xr-status">未接入</strong></div><div class="kv"><span>控制源</span><strong data-text="owner">未接管</strong></div><div class="kv"><span>任务模型</span><strong data-text="model-state">未连接</strong></div><div class="divider"></div><p class="help">PICO 4 与两个腿部追踪器需现场配对、完成全身标定，先在 Unity 3D 中确认重定向姿态。</p><a class="btn full section-gap" href="#startup">${icon('list-checks')}前往自检与启动</a></div></section><section class="card">${cardHead('数据位置','folder')}<div class="card-body"><p class="mono muted" data-text="output-root" style="overflow-wrap:anywhere;line-height:1.9">等待数据目录</p><p class="help">正式数据和演示数据在列表中明确标识；界面预演不会写入真实目录。</p></div></section></div></div>${episodeBrowser()}`;}
function episodeBrowser(){return `<section class="card section-gap">${cardHead(app.view==='playback'?'选择回放片段':'片段管理','film',`<button class="btn text sm" data-action="episodes-refresh">${icon('refresh-cw')}刷新列表</button>`)}<div class="dataset-grid"><div class="dataset-sidebar" data-datasets></div><div class="episode-list"><div class="episode-toolbar"><input type="search" data-episode-search placeholder="搜索当前页片段或任务" aria-label="搜索片段" value="${esc(app.search)}"><span class="tiny muted" data-episode-total>-- 段</span></div><div data-episodes></div><div class="pagination"><button class="btn sm" data-action="episodes-prev">上一页</button><span data-page-number>1</span><button class="btn sm" data-action="episodes-next">下一页</button></div></div></div></section>`;}
function playbackView(){return `${app.playback?`<div class="row between" style="margin-bottom:14px"><div class="row wrap"><span class="card-title">${icon('film')}${esc(app.playback.review.episode.name)}</span>${badge(app.playback.review.episode.demo_only?'演示片段':'正式数据',app.playback.review.episode.demo_only?'purple':'success')}<span class="tiny muted">仅可视化回放</span></div><button class="btn sm" data-action="close-playback">关闭片段</button></div><div class="replay-layout"><div class="stack"><section class="card">${cardHead('同步视频','clapperboard',`<small>帧号 <span data-replay-frame>0</span></small>`)}<div class="card-body"><div class="camera-grid replay-cameras">${CAMERAS.map(c=>cameraHTML(c.id,true)).join('')}</div><div class="playback-controls"><button class="btn sm" data-action="replay-step" data-direction="-1" aria-label="上一帧">${icon('skip-back')}</button><button class="btn primary sm" data-action="replay-toggle">播放</button><button class="btn sm" data-action="replay-step" data-direction="1" aria-label="下一帧">${icon('skip-forward')}</button><input type="range" min="0" max="6" step="0.001" value="0" data-replay-progress aria-label="回放时间"><span class="time-code" data-replay-time>00:00 / 00:00</span><select data-replay-speed aria-label="回放速度">${[.25,.5,1,1.5,2].map(v=>`<option value="${v}" ${v===1?'selected':''}>${v}×</option>`).join('')}</select></div><div class="notice warning compact" data-playback-error hidden></div><p class="help">视频以首个可用视角为主时钟，其余视角和关节曲线跟随时间轴。</p></div></section><section class="card">${cardHead('关节 State / Action','chart-no-axes-combined',`<small>实线 State · 虚线 Action · °</small>`)}<div class="card-body"><div class="channel-select">${profile.body_joints.map((name,i)=>`<label class="channel-chip"><input type="checkbox" data-channel="${i}" ${name.includes('elbow')?'checked':''}>${jointLabel(name)}</label>`).join('')}</div><canvas class="chart" data-chart aria-label="关节状态与动作随时间的曲线"></canvas>${app.playback.series?(app.playback.series.sampled?`<p class="help">曲线预览 ${app.playback.series.returned_frames} / ${app.playback.series.original_frames} 帧，保留首尾；原始文件未修改。</p>`:''):`<p class="help">${esc(app.playback.seriesError||'此片段暂无具名关节序列，仍可查看录像。')}</p>`}</div></section></div><div class="stack"><section class="card">${cardHead('同步姿态','person-standing')}<div class="robot-viewer replay-pose" data-robot-scene><div class="model-note"><span class="badge" data-pose-label>${app.playback.series?'片段 State 姿态':'参考姿态 · 暂无关节序列'}</span></div><div class="viewer-toolbar"><span>State / rad → 3D</span><button class="btn sm" data-action="reset-view">复位</button></div></div></section><section class="card">${cardHead('片段信息','file-text')}<div class="card-body"><div class="kv"><span>帧数</span><strong>${esc(app.playback.review.episode.frames)}</strong></div><div class="kv"><span>采样频率</span><strong>${esc(app.playback.review.episode.fps)} FPS</strong></div><div class="kv"><span>时长</span><strong>${duration(app.playback.review.episode.duration_seconds)}</strong></div><div class="divider"></div><p class="help">${esc((app.playback.review.episode.tasks||[]).join(' / '))}</p><div class="row between section-gap"><span class="tiny muted">片段评级</span>${ratingHTML(app.playback.review.episode)}</div></div></section></div></div>`:`<section class="card replay-empty">${empty('选择下方片段，查看三路视频、关节姿态与动作曲线','clapperboard')}<div class="notice compact">${icon('info')}回放仅用于查看数据，不向机器人发送动作。</div></section>`}${episodeBrowser()}`;}
function workflowView(){return `<div class="flow-layout"><div class="card"><div class="flow-toolbar"><input value="${esc(app.graph.name)}" data-flow-name aria-label="流程名称"><select data-flow-template aria-label="流程模板"><option value="">加载模板…</option><option value="inference">任务模型推理</option><option value="collection">PICO 遥操作采集</option></select><button class="btn sm" data-action="flow-save">${icon('save')}保存</button><button class="btn sm" data-action="flow-import">导入</button><button class="btn sm" data-action="flow-export">导出</button><span class="grow"></span><button class="btn sm" data-action="flow-zoom" data-delta="-0.1" aria-label="缩小画布">−</button><span class="tiny muted" data-flow-zoom>100%</span><button class="btn sm" data-action="flow-zoom" data-delta="0.1" aria-label="放大画布">＋</button></div><div class="flow-canvas" data-flow-root><div data-flow-space style="width:1550px;height:1320px"><div class="flow-world" data-flow-world><svg class="flow-edges" data-flow-edges></svg><div class="flow-nodes" data-flow-nodes></div></div></div></div><div class="flow-hint" data-flow-hint>拖动节点标题移动；点击 ＋ 再点击目标节点连接；点击节点或连线编辑。Esc 取消连线。</div></div><div class="stack flow-inspector"><section class="card">${cardHead('流程运行','workflow',textBinding('workflow-state','未提交'))}<div class="card-body"><div class="row between"><span class="tiny muted">任务类型</span>${badge(app.graph.task_kind==='collection'?'数据采集':'任务推理','blue')}</div><div class="kv"><span>节点 / 连线</span><strong data-flow-count></strong></div><div class="row section-gap"><button class="btn soft sm full" data-action="flow-validate">校验</button><button class="btn primary sm full" data-action="flow-preview">${icon('play')}本地预演</button></div><div class="row" style="margin-top:9px"><button class="btn sm full" data-action="flow-stop">停止预演</button>${commandButton('workflows','run','提交执行','sm full')}</div><div style="margin-top:9px">${commandButton('workflows','cancel','停止后台执行','sm full')}</div><p class="help">本地预演只检查流转，不执行节点操作。提交执行使用独立的后端运行接口。</p></div><div class="flow-log" data-flow-log></div></section><section class="card">${cardHead('属性编辑','settings-2')}<div class="card-body" data-flow-inspector><p class="help">选择节点或连线查看属性。</p></div></section><section class="card">${cardHead('添加节点','plus')}<div class="card-body node-palette">${NODE_TYPES.filter(n=>!['start','end'].includes(n[0])).map(n=>`<button data-action="flow-add" data-id="${n[0]}">${icon(n[2])}${n[1]}</button>`).join('')}</div></section></div></div>`;}


function icons(){globalThis.lucide?.createIcons();}
function bindText(key,value){$$('[data-text="'+key+'"]').forEach(el=>{el.textContent=value;});}
function reasonFor(scope,action,payload={}){
 let reason=api.can(scope,action,payload);if(reason)return reason;
 const s=app.snapshot;
 if(scope==='inference'&&action==='start'&&!app.config.prompt.trim())return '请先填写任务指令';
 if(scope==='inference'&&action==='start'&&s.model.state==='running')return '任务推理已经运行';
 if(scope==='inference'&&action==='stop'&&s.model.state!=='running')return '当前没有运行中的推理';
 if(scope==='inference'&&action==='disconnect'&&s.model.state==='running')return '请先停止推理';
 if(scope==='robot'&&['initialize','claim','release','set_mode'].includes(action)&&(s.collection.recording||s.model.state==='running'))return '请先结束当前采集或推理';
 if(scope==='robot'&&action==='release'&&!s.robot.owner)return '当前没有控制源';
 if(scope==='robot'&&action==='initialize'&&!s.robot.initialization_profile_id)return '执行端尚未提供初始化配置';
 if(scope==='collection'&&action==='prepare'&&!app.preview&&!s.interlocks.can_collect)return s.interlocks.reasons?.can_collect||'设备尚未就绪';
 if(scope==='collection'&&s.collection.busy)return '导出器正在处理上一条操作';
 if(scope==='collection'&&action==='start'&&!s.collection.prepared)return '请先准备采集并等待导出器就绪';
 if(scope==='collection'&&action==='prepare'&&s.collection.prepared)return '当前已有采集任务，请先结束';
 if(scope==='collection'&&action==='end'&&s.collection.recording)return '请先保存或舍弃当前片段';
 if(scope==='collection'&&action==='end'&&!s.collection.prepared&&!s.collection.recording&&!s.collection.busy)return '当前没有采集任务';
 if(scope==='collection'&&['save','discard'].includes(action)&&!s.collection.recording)return '当前没有待保存的录制';
 if(scope==='collection'&&['start','prepare'].includes(action)&&s.collection.recording)return '当前片段正在录制';
 if(scope==='deployment'&&action==='cancel'&&!['running','pending','waiting'].includes(s.deployment.state))return '当前没有准备中的任务';
 if(scope==='workflows'&&action==='cancel'&&!app.workflowJob?.run_id)return '当前没有后台运行中的流程';
 if(scope==='workflows'&&app.preview)return '界面预演中请使用“本地预演”';
 return '';
}
function update(){
 const s=app.snapshot, r=s.robot, robotOK=r.connected&&fresh(r), joints=namedJointValues(s,profile), b=batteryReading(s);
 const stopButton=$('.stop-button');if(stopButton){stopButton.lastChild.textContent=app.preview?'停止任务':s.robot.owner==='manual'?'停止调试':['pending','running'].includes(s.deployment.state)?'取消准备':'停止采集';stopButton.title=app.preview?'本地预演停止':'停止本工作台的准备、采集与手动仿真；不停止外部真机控制器';}
 const cams=(s.cameras||[]).filter(c=>c.state==='streaming'&&fresh(c));
 const commands=$$('[data-command]');
 commands.forEach(el=>{let payload={};try{payload=JSON.parse(el.dataset.payload||'{}');}catch{}const reason=reasonFor(el.dataset.command,el.dataset.op,payload);el.disabled=(app.busy&&el.dataset.command!=='safety')||!!reason;el.title=reason||(app.preview?'仅在界面预演中执行':el.dataset.command==='safety'?'停止本工作台的准备、采集与手动仿真；不停止外部真机控制器':'发送到 4070 执行端');});
 $$('[data-command=services][data-op=stop]').forEach(el=>{let payload={};try{payload=JSON.parse(el.dataset.payload||'{}');}catch{}if(['docker','pc_service'].includes(payload.service_id))el.textContent=app.stoppingService===payload.service_id?'停止中…':'停止';});
 bindText('backend',app.preview?'界面预演':s.backend_connected?'执行端已连接':s.source==='legacy-readonly'?'数据目录已连接':'执行端未连接');
 $('[data-backend-dot]').className='dot '+(app.preview?'warning':s.backend_connected?'success':'');
 const connectionState=app.preview?'preview':s.backend_connected?'connected':s.source==='unavailable'&&!s.message?'checking':'failed';
 const connectionStatus={connected:['Connecting','网页与4070执行端已连接；G1连接状态见顶栏'],failed:['Failed','网页与4070执行端连接失败，等待恢复'],checking:['Checking','正在检查网页与4070执行端的连接'],preview:['Preview','本地界面预演，不表示已连接4070执行端']}[connectionState];
 const connection=$('[data-console-connection]');connection.dataset.state=connectionState;connection.title=connectionStatus[1];$('[data-console-connection-label]',connection).textContent=connectionStatus[0];
 bindText('connection-message',s.backend_connected?'执行端已连接，操作权限由设备就绪条件决定。':s.message||'设备执行接口待接入。可查看现有数据，也可开启界面预演检查操作流程。');
 bindText('robot',robotOK?'G1 已连接':'G1 未连接');
 bindText('battery',b.valid?Math.round(b.percent)+'%':'--%');bindText('battery-large',b.valid?Math.round(b.percent):'--');
 $$('[data-battery], [data-battery-large]').forEach(el=>{el.className=(el.hasAttribute('data-battery')?'battery ':'battery-large ')+b.tone;el.querySelector('.battery-icon span').style.width=b.valid?b.percent+'%':'0';el.title=b.valid?`${app.preview?'合成预演电量':'G1 电量'} ${b.percent}% · ${clock(b.observed_at)}`:'电池状态未知：反馈缺失、已过期或机器人未连接';});
 bindText('battery-detail',b.valid?(b.charging?'充电中':b.tone==='danger'?'电量过低，请结束任务并检查电源':b.tone==='warning'?'低电量提醒':'电池反馈正常'):'电量未知 · 等待有效反馈');
 bindText('battery-time',b.valid?clock(b.observed_at):'--');
 bindText('battery-electrical',b.valid?`${finite(b.voltage_v)?b.voltage_v.toFixed(1)+' V':'--'} / ${finite(b.current_a)?b.current_a.toFixed(1)+' A':'--'}`:'-- / --');
 bindText('feedback',robotOK?'已连接 · '+clock(r.observed_at):r.connected?'反馈已过期':'未连接');
 bindText('owner',robotOK?ownerLabel(r.owner):'未知');bindText('owner-short',robotOK?ownerLabel(r.owner):'未知');
 bindText('robot-mode',robotOK?r.mode||'未知':'--');
 bindText('joint-count',joints?'29 / 29':'-- / 29');bindText('joint-count-small',joints?'29':'--');
 const cameraSource=s.camera_source;bindText('camera-source',cameraSource?.kind==='ros2'?`ROS 2 · Domain ${cameraSource.domain_id}`:app.preview?'合成图像 · 界面预演':'外部 ZMQ 图像流');
 bindText('camera-bridge-state',cameraSource?.kind==='ros2'?({streaming:'接收图像中',waiting:'等待相机话题',starting:'启动中',stopped:'已停止',failed:'启动失败'})[cameraSource.state]||cameraSource.state:app.preview?'本地预演':'由外部发布端管理');
 bindText('camera-ros-topics',cameraSource?.kind==='ros2'?Object.entries(cameraSource.topics||{}).map(([id,row])=>`${CAMERAS.find(c=>c.id===id)?.label||id}：${row.topic}`).join(' · '):'');
 bindText('camera-count',cams.length);bindText('check-count',(s.checks||[]).filter(c=>c.status==='passed').length);
 bindText('updated',clock(s.observed_at));
 const modelState=statusLabel(s.model.state);
 bindText('model-state',modelState);bindText('model-detail',s.model.state==='running'?'任务动作经适配器交由 SONIC 执行':s.model.connected?'模型已连接，等待任务与控制权就绪':'连接模型并取得任务控制权后开始');
 bindText('adapter-status',s.model.adapter?.validated?'已通过执行端校验':'待执行端校验');bindText('adapter-schema',s.model.adapter?.validated?`${s.model.adapter.dimension??'--'} / ${s.model.adapter.unit??'--'} / ${s.model.adapter.frequency_hz??'--'} Hz`:'-- / -- / --');
 bindText('steps',s.model.steps??0);bindText('latency',finite(s.model.latency_ms)?Math.round(s.model.latency_ms):'--');bindText('frequency',finite(s.model.frequency_hz)?s.model.frequency_hz.toFixed(0):'--');
 if($('[data-model-badge]'))$('[data-model-badge]').innerHTML=badge(modelState,s.model.connected?'success':'');
 if($('[data-inference-badge]'))$('[data-inference-badge]').innerHTML=badge(s.model.state==='running'?'推理中':s.interlocks.can_infer?'可以运行':'待准备',s.model.state==='running'?'blue':s.interlocks.can_infer?'success':'');
 if($('[data-model-dot]'))$('[data-model-dot]').className='dot '+(s.model.connected?'success':'');
 if($('[data-infer-reason]'))$('[data-infer-reason]').textContent=reasonFor('inference','start')||'模型、观测与控制权已就绪';
 bindText('controller',s.services.controller?statusLabel(s.services.controller.state):'待接入');
 bindText('xr-status',s.services.pc_service?statusLabel(s.services.pc_service.state):'待接入');
 const events=[...app.localEvents,...(s.events||[])].sort((a,b)=>Date.parse(b.at)-Date.parse(a.at));
 if($('[data-events-mini]'))$('[data-events-mini]').innerHTML=eventHTML(events.slice(0,3));
 if($('[data-stages]'))$('[data-stages]').innerHTML=STAGES.map(([id,label,detail],i)=>{const state=s.deployment.steps?.find(row=>row.id===id)?.state||'pending';return `<article class="stage ${esc(state)}"><div class="stage-number">${state==='succeeded'?'✓':i+1}</div><b>${label}</b><small>${detail}<br>${statusLabel(state)}</small></article>`;}).join('');
 if($('[data-deployment-badge]'))$('[data-deployment-badge]').innerHTML=badge(statusLabel(s.deployment.state),s.deployment.state==='ready'?'success':s.deployment.state==='running'?'blue':'');
 bindText('job-message',s.deployment.message||'准备过程不申请运动控制权');
 if($('[data-deployment-log]'))$('[data-deployment-log]').textContent=app.job?.log||s.deployment.message||'尚无准备任务';
 const unlock=$('[data-action="unlock"]');if(unlock)unlock.hidden=app.preview||s.access?.authorized!==false;
 if($('[data-checks]'))$('[data-checks]').innerHTML=s.checks.length?s.checks.map(c=>`<tr><td>${esc(c.label)}</td><td>${badge(statusLabel(c.status),c.status==='passed'?'success':c.status==='blocked'?'warning':'')}</td><td>${esc(c.detail||'等待执行端检查')}</td><td>${esc(c.source||'执行端')}</td></tr>`).join(''):'<tr><td colspan="4">自检接口待接入。可在界面预演中查看向导流程。</td></tr>';
 if($('[data-robot-badge]'))$('[data-robot-badge]').innerHTML=badge(robotOK?'反馈有效':'未连接',robotOK?'success':'');
 SERVICE_DEFS.forEach(([id])=>{const service=s.services[id];const holder=$('[data-service-badge="'+id+'"]');if(holder)holder.innerHTML=badge(service?statusLabel(service.state):'待接入',service&&['running','ready'].includes(service.state)?'success':service?.state==='failed'?'danger':'');const detail=$('[data-service-detail="'+id+'"]');if(detail)detail.textContent=service?.label||service?.detail||'接口待接入';});
 const workflow=app.workflowJob||s.workflow;bindText('workflow-state',workflow&&workflow.state!=='idle'?statusLabel(workflow.state):'未提交');
 if(editor&&workflow?.graph_id===app.graph.id&&workflow.node_states&&editor.liveSignature!==JSON.stringify(workflow)){editor.execution='live';editor.states=workflow.node_states;editor.liveSignature=JSON.stringify(workflow);editor.paint();if(workflow.message)flowLog(workflow.message);}
 if(app.view!=='playback')updateCameras();
 if(app.view==='body'){const manual=app.snapshot.manual||{};$$('[data-target-slider]').forEach(el=>el.title=app.liveManual?(app.mode==='real'?'已启用真机实时联动':'已启用 MuJoCo 实时联动'):'拖动仅更新本地目标姿态');const status=$('[data-manual-state]');if(status)status.textContent=(manual.owner==='manual'?'控制权有效 · ':'无手动控制权 · ')+({sent:'已发送',moving:'过渡中',tracking:'跟踪中',reached:'已到位',held:'保持姿态'}[manual.target_state]||'尚未发送')+(finite(manual.max_error_rad)?' · 最大误差 '+degree(manual.max_error_rad)+'°':'')+(app.mode==='real'?' · '+(manual.reason||manual.gate?.message||''): '');const rows=new Map((robotOK?r.joints:[]).map(row=>[row.name,row]));$$('[data-joint-feedback]').forEach(el=>el.textContent=joints?degree(rows.get(el.dataset.jointFeedback)?.position_rad):'--');$$('[data-joint-temperature]').forEach(el=>{const v=rows.get(el.dataset.jointTemperature)?.temperature_c;el.textContent=joints&&finite(v)?v.toFixed(0):'--';});robotScene?.setPose(app.target?profile.body_joints.map(n=>app.targets[n]):joints);if($('[data-pose-label]'))$('[data-pose-label]').textContent=app.target?(app.liveManual?(app.mode==='real'?'目标姿态 · 真机联动':'目标姿态 · MuJoCo 联动'):'目标预览 · 本地'):joints?(app.preview?'合成姿态 · 界面预演':'实时反馈姿态'):'参考姿态 · 无实时反馈';}
 const demo=s.totals.demo_episodes||0;
 bindText('episodes',Math.max(0,s.totals.episodes||0).toLocaleString());bindText('datasets',s.groups.filter(g=>!g.demo_only).length.toLocaleString());bindText('demo-episodes',demo.toLocaleString());
 bindText('recording-short',s.collection.recording?'录制中':'待机');bindText('recording-state',s.collection.recording?'正在录制':'尚未录制');bindText('record-time',duration(s.collection.elapsed_seconds));$('[data-record-light]')?.classList.toggle('active',s.collection.recording);
 bindText('collection-ready',s.collection.message||(s.collection.prepared?'采集任务已准备':s.source==='legacy-readonly'?'新采集执行接口待接入':'等待采集任务准备'));
 bindText('collection-worker-state',statusLabel(s.collection.state||'idle'));
 if(app.view==='collection')$$('[data-config="dataset"],[data-config="task"],[data-config="fps"]').forEach(el=>el.disabled=!!(s.collection.prepared||s.collection.busy));bindText('output-root',s.output_root||'等待执行端提供数据目录');
 if($('[data-datasets]'))renderDatasets();
}
function updateCameras(){
 $$('[data-camera]').forEach(card=>{
  const c=app.snapshot.cameras.find(row=>row.id===card.dataset.camera),picture=$('.camera-picture',card),video=$('video',card),img=$('img',card);
  const freshFrame=c?.state==='streaming'&&fresh(c),url=freshFrame?safeMediaURL(c.url):'',supported=['video','mjpeg'].includes(c?.transport);
  const active=!!url&&supported;
  const key=active?c.transport+':'+url:'';
  if(picture.dataset.media!==key||(active&&picture.dataset.failed==='true'&&Date.now()-Number(picture.dataset.failedAt||0)>5000)){video.pause();video.removeAttribute('src');video.classList.remove('active');video.load();img.removeAttribute('src');img.classList.remove('active');picture.dataset.media=key;picture.dataset.failed='';if(active){const el=c.transport==='mjpeg'?img:video;el.src=url;el.classList.add('active');if(c.transport==='video'){video.dataset.cameraLive='true';video.play().catch(()=>{});}el.onerror=()=>{picture.dataset.failed='true';picture.dataset.failedAt=String(Date.now());picture.classList.remove('has-media');$('[data-camera-message]',card).textContent='画面读取失败';};}}
  picture.classList.toggle('has-media',active&&picture.dataset.failed!=='true');
  $('[data-camera-message]',card).textContent=picture.dataset.failed==='true'?'画面读取失败':c&&!freshFrame?'画面未就绪 / 已过期':c&&!supported?'视频格式待接入':'等待相机连接';
  $('[data-camera-stat]',card).textContent=active?`${finite(c.fps)?c.fps.toFixed(0):'--'} FPS · ${finite(c.latency_ms)?c.latency_ms+' ms':'-- ms'}`:'-- FPS · 未就绪';
 });
 CAMERAS.forEach(c=>{const el=$('[data-camera-health="'+c.id+'"]'),row=app.snapshot.cameras.find(r=>r.id===c.id);if(el)el.textContent=row?.state==='streaming'&&fresh(row)?`${row.fps??'--'} FPS · ${clock(row.observed_at)}`:'未就绪';});
}
function eventHTML(events){return events.length?`<div class="event-list">${events.map(e=>`<div class="event"><span class="dot ${esc(e.level==='error'?'danger':e.level==='success'?'success':'')}"></span><div><p>${esc(e.title)}</p><small>${esc(e.detail)}</small></div><time>${clock(e.at)}</time></div>`).join('')}</div>`:empty('暂无运行事件','activity');}
function toast(message,tone=''){const el=document.createElement('div');el.className='toast '+tone;el.setAttribute('role',tone==='danger'?'alert':'status');el.textContent=message;$('.toast-stack').append(el);setTimeout(()=>el.remove(),6500);}
function localEvent(title,detail='',level='info'){app.localEvents.unshift({id:uid(),at:new Date().toISOString(),title,detail,level});app.localEvents=app.localEvents.slice(0,60);}
function modal(title,content,footer='',wide=false){$('#overlay-root').innerHTML=`<div class="overlay" data-overlay><section class="modal ${wide?'wide':''}" role="dialog" aria-modal="true" aria-label="${esc(title)}"><header class="modal-header"><h2>${esc(title)}</h2><button class="icon-button" data-action="close-modal" aria-label="关闭弹窗">${icon('x')}</button></header><div class="modal-body">${content}</div>${footer?`<footer class="modal-footer">${footer}</footer>`:''}</section></div>`;icons();$('.modal button,.modal textarea,.modal input')?.focus();}
function closeModal(){$$('#overlay-root video').forEach(v=>{v.pause();v.removeAttribute('src');v.load();});$('#overlay-root').innerHTML='';}
async function poll(){
 if(pollBusy||app.busy||document.hidden)return;pollBusy=true;
 const previewAtStart=app.preview,modeAtStart=app.mode;
 try{
  const previousGroups=app.snapshot.groups.map(g=>g.name).join('|');
  const snapshot=await api.loadSnapshot();
  if(previewAtStart!==app.preview||modeAtStart!==app.mode){api.snapshot=app.snapshot;return;}
  app.snapshot=snapshot;
  if(!app.preview&&snapshot.deployment?.id&&app.job?.id!==snapshot.deployment.id)app.job={id:snapshot.deployment.id,state:'pending'};
  const acknowledged=snapshot.collection.last_command;if(acknowledged?.id&&acknowledged.id!==app.lastCollectionCommandId){app.lastCollectionCommandId=acknowledged.id;toast(acknowledged.ok?'采集操作已确认':acknowledged.message||'采集操作失败',acknowledged.ok?'success':'danger');if(['save','discard','end','stop'].includes(acknowledged.action))loadEpisodes();}
  if(app.job&&!['ready','waiting','succeeded','failed','cancelled'].includes(app.job.state)&&!app.preview){
   const response=await api.deploymentJob(app.job.id);app.job=response.job||response;
   if(app.job.steps)app.snapshot.deployment={...app.job};
   if(app.job.state==='failed'){toast(app.job.message||'准备任务失败','danger');localEvent('准备任务失败',app.job.message||'请查看执行端日志','error');}
  }
  if(app.workflowJob?.run_id&&!['succeeded','failed','cancelled'].includes(app.workflowJob.state)&&!app.preview){const result=await api.workflowRun(app.workflowJob.run_id);app.workflowJob=result.run||result;}
  app.lastPollError=false;update();
  if(['collection','playback'].includes(app.view)&&!app.dataset&&app.snapshot.groups.length)loadEpisodes();
  if(previousGroups!==app.snapshot.groups.map(g=>g.name).join('|'))renderDatasets();
 }catch(error){if(previewAtStart!==app.preview||modeAtStart!==app.mode)return;app.snapshot=emptySnapshot();app.snapshot.message=error.message||'连接暂时中断，等待执行端恢复。';update();if(!app.lastPollError){localEvent('执行端连接中断','当前控制按钮已禁用。','error');app.lastPollError=true;}}
 finally{pollBusy=false;if(previewAtStart!==app.preview||modeAtStart!==app.mode)queueMicrotask(poll);}
}
async function initRobot(selector,id){
 const container=$(selector);if(!container)return;
 try{const {RobotScene}=await import('./console-robot.js');if(id!==app.renderId||!container.isConnected)return;robotScene=new RobotScene(container,profile);if(app.view==='body')update();else robotScene.setPose(playback?.frame()?.state);await robotScene.loading;if(container.dataset.modelError){toast('部分 G1 模型资源未加载，可刷新重试','danger');}}
 catch{if(id!==app.renderId)return;container.insertAdjacentHTML('beforeend',empty('3D 渲染不可用，请使用关节表和曲线查看数据','person-standing'));}
}
function renderDatasets(){
 const root=$('[data-datasets]');if(!root)return;
 const groups=app.snapshot.groups;
 if(groups.length&&!groups.some(g=>g.name===app.dataset))app.dataset=groups[0].name;
 const signature=JSON.stringify(groups.map(g=>[g.name,g.episodes,g.demo_only]))+app.dataset;
 if(root.dataset.signature===signature)return;root.dataset.signature=signature;
 root.innerHTML=groups.length?groups.map(g=>`<button class="dataset-button ${app.dataset===g.name?'active':''}" data-action="dataset" data-name="${esc(g.name)}"><b>${esc(g.name)}</b><small>${Number(g.episodes||0).toLocaleString()} 段 · ${g.fps||'--'} FPS</small>${badge(g.demo_only?'演示数据':'正式数据',g.demo_only?'purple':'success')}</button>`).join(''):empty('暂无数据集','folder');
}
let episodeRequest=0;
async function loadEpisodes(){
 if(!['collection','playback'].includes(app.view))return;
 renderDatasets();const id=++episodeRequest,dataset=app.dataset;
 if(!dataset){app.episodes=[];app.total=0;renderEpisodes();return;}
 app.loadingEpisodes=true;app.episodeError='';renderEpisodes();
 try{const result=await api.listEpisodes(dataset,app.offset);if(id!==episodeRequest||dataset!==app.dataset)return;app.episodes=result.episodes||[];app.total=result.total||0;}
 catch(error){if(id!==episodeRequest)return;app.episodes=[];app.episodeError=error.message;}
 finally{if(id===episodeRequest){app.loadingEpisodes=false;renderEpisodes();}}
}
function ratingHTML(row){return `<div class="rating" aria-label="片段评级">${['A','B','F'].map(g=>`<button data-action="rate" data-dataset="${esc(row.dataset||app.dataset)}" data-episode="${row.episode_index}" data-grade="${g}" class="${row.grade===g?'selected':''}" title="${g} 级 · 再次点击清除" aria-label="评级 ${g}" aria-pressed="${row.grade===g}" ${row.state==='discarded'?'disabled':''}>${g}</button>`).join('')}</div>`;}
function renderEpisodes(){
 const root=$('[data-episodes]');if(!root)return;
 $('[data-episode-total]').textContent=`${app.total.toLocaleString()} 段${app.snapshot.groups.find(g=>g.name===app.dataset)?.demo_only?' · 演示数据':''}`;
 $('[data-page-number]').textContent=`${Math.floor(app.offset/30)+1} / ${Math.max(1,Math.ceil(app.total/30))}`;
 $('[data-action="episodes-prev"]').disabled=app.offset<=0||app.loadingEpisodes;
 $('[data-action="episodes-next"]').disabled=app.offset+30>=app.total||app.loadingEpisodes;
 if(app.loadingEpisodes){root.innerHTML=empty('正在读取片段…','loader');icons();return;}
 if(app.episodeError){root.innerHTML=empty(app.episodeError,'circle-alert');icons();return;}
 const filter=app.search.trim().toLowerCase(),rows=app.episodes.filter(row=>(row.name+' '+(row.tasks||[]).join(' ')).toLowerCase().includes(filter));
 root.innerHTML=rows.length?rows.map(row=>`<article class="episode-row"><div class="episode-thumb">${icon('film')}</div><div class="grow"><div class="episode-name">${esc(row.name||'episode_'+row.episode_index)} ${row.demo_only?badge('演示','purple'):''} ${row.state==='discarded'?badge('已舍弃','warning'):''}</div><div class="episode-meta">${row.frames||0} 帧 · ${duration(row.duration_seconds)} · ${esc((row.tasks||[]).join(' / '))}</div></div>${ratingHTML(row)}<button class="btn sm" data-action="review" data-episode="${row.episode_index}">${icon('play')}回放</button></article>`).join(''):empty(app.search?'当前页没有匹配片段':'此数据集暂无片段','film');icons();
}
async function openReview(index){
 const dataset=app.dataset,preview=app.preview;toast('正在读取片段…');
 try{const [review,result]=await Promise.all([api.review(dataset,index),api.series(dataset,index).catch(error=>({unavailable_reason:error.message}))]);const series=result?.unavailable_reason?null:result;if(preview!==app.preview||dataset!==app.dataset)return;app.playback={review,series,seriesError:result?.unavailable_reason||''};if(app.view!=='playback')goView('playback');else render();}
 catch(error){toast(error.message,'danger');}
}
function setupPlayback(id){
 const {review,series}=app.playback;
 $$('.replay-cameras [data-camera]').forEach(card=>{const v=$('video',card),row=review.videos.find(row=>row.camera===card.dataset.camera);v.dataset.hasVideo=safeMediaURL(row?.url)?'true':'false';if(v.dataset.hasVideo==='true'){$('.camera-picture',card).classList.add('has-media');v.classList.add('active');$('[data-camera-stat]',card).textContent='片段录像';}else $('[data-camera-message]',card).textContent='此片段无该视角';});
 playback=new PlaybackController($('#main'),review,series,profile,frame=>robotScene?.setPose(frame?.state));
 initRobot('[data-robot-scene]',id);
}


function setupWorkflow(){
 editor=new WorkflowEditor($('[data-flow-root]'),app.graph,(item,kind)=>selectFlow(item,kind),()=>flowChanged());
 flowChanged();
}
function flowChanged(){if($('[data-flow-count]'))$('[data-flow-count]').textContent=`${app.graph.nodes.length} / ${app.graph.edges.length}`;}
function flowLog(message){app.flowLog.unshift(`${clock(new Date().toISOString())}  ${message}`);app.flowLog=app.flowLog.slice(0,30);if($('[data-flow-log]'))$('[data-flow-log]').innerHTML=app.flowLog.map(line=>`<div>${esc(line)}</div>`).join('');}
function selectFlow(item,kind='node'){
 if(!item)return;app.flowSelection={id:item.id,kind};
 const root=$('[data-flow-inspector]');
 if(kind==='link'||kind==='replace-link'){root.innerHTML=`<p class="help">${kind==='replace-link'?'此节点已有成功出口，请选择连线修改目标或删除旧连线。':'点击目标节点建立成功连线。按 Esc 取消。'}</p>`;return;}
 if(kind==='edge'){root.innerHTML=`<label class="field">连线结果<select data-edge-outcome>${['success','failure','stop'].map(v=>`<option value="${v}" ${v===item.outcome?'selected':''}>${({success:'成功',failure:'失败',stop:'停止'})[v]}</option>`).join('')}</select></label><label class="field">目标节点<select data-edge-to>${app.graph.nodes.filter(n=>n.type!=='start').map(n=>`<option value="${esc(n.id)}" ${n.id===item.to?'selected':''}>${esc(n.label)}</option>`).join('')}</select></label><button class="btn sm full" data-action="flow-property-save">保存连线</button><button class="btn danger sm full" style="margin-top:8px" data-action="flow-delete">删除连线</button>`;return;}
 root.innerHTML=`<label class="field">节点名称<input data-node-label value="${esc(item.label)}" maxlength="80"></label><label class="field">超时（秒）<input type="number" min="1" max="3600" data-node-timeout value="${item.timeout_s}"></label><label class="field">节点参数（JSON）<textarea data-node-params style="min-height:80px;font-size:10px">${esc(JSON.stringify(item.params||{},null,2))}</textarea></label><label class="check-label" style="margin-bottom:14px"><input type="checkbox" data-node-fail ${item.ui?.preview_fail?'checked':''}> 本地预演时模拟失败</label><button class="btn sm full" data-action="flow-property-save">保存节点属性</button>${['start','end'].includes(item.type)?'':`<button class="btn danger sm full" style="margin-top:8px" data-action="flow-delete">删除节点与相关连线</button>`}`;
}
async function runCommand(scope,action,payload={}){
 if(app.busy&&scope!=='safety')return;
 const reason=reasonFor(scope,action,payload);if(reason){toast(reason,'danger');return;}
 if(scope==='inference'){
  if(['connect','start'].includes(action)){
   if(!app.preview){const url=safeMediaURL(app.config.endpoint);if(!url)throw new Error('请填写有效的模型 HTTP(S) 服务地址');if(!app.config.model.trim())throw new Error('请填写模型标识');}
   if(!Number.isInteger(Number(app.config.hz))||Number(app.config.hz)<1||Number(app.config.hz)>200)throw new Error('执行频率应为 1～200 的整数');
   payload={...payload,endpoint:app.config.endpoint,model_id:app.config.model,action_schema:app.config.protocol,frequency_hz:Number(app.config.hz),task:app.config.prompt.trim(),record:app.config.record};
  }
 }
 if(scope==='collection'&&['prepare','start'].includes(action)){
  if(!/^[A-Za-z0-9_-]{1,80}$/.test(app.config.dataset))throw new Error('数据集名使用 1～80 位字母、数字、下划线或短横线');
  if(!Number.isInteger(Number(app.config.fps))||Number(app.config.fps)<1||Number(app.config.fps)>120)throw new Error('录制帧率应为 1～120 的整数');
  if(!app.config.task.trim())throw new Error('请填写本次采集的任务描述');
  payload={...payload,dataset:app.config.dataset,task:app.config.task.trim(),fps:Number(app.config.fps),camera_ids:CAMERAS.map(c=>c.id)};
 }
 if(scope==='robot'&&action==='apply_pose'){
  if(!app.target)throw new Error('请先开启目标预览，并检查目标姿态');
  const joints=profile.body_joints.map(name=>({name,position_rad:app.targets[name]}));
  if(joints.some(row=>{const spec=profile.joints.find(j=>j.name===row.name);return !finite(row.position_rad)||row.position_rad<spec.lower||row.position_rad>spec.upper;}))throw new Error('目标关节超出参考范围，请修正');
  payload={joints,unit:'rad',transition_seconds:3,lease_token:app.leaseToken,sequence:++manualSequence};
  if(!app.preview&&!payload.confirmed){app.pendingPose=payload;modal('核对目标姿态',`<p>将向${app.mode==='sim'?' MuJoCo 物理仿真':' G1 真机'}发送 29 个具名关节目标，按速度上限平滑过渡。是否到位以反馈为准。</p><div class="table-scroll" style="max-height:260px"><table class="joint-table"><tbody>${joints.map(row=>`<tr><td>${jointLabel(row.name)}</td><td>${degree(row.position_rad)}°</td></tr>`).join('')}</tbody></table></div>`,'<button class="btn" data-action="close-modal">取消</button><button class="btn primary" data-action="confirm-pose">确认下发</button>');return;}
 }
 if(scope==='self_check')payload={read_only:true};
 if(scope==='robot'&&action==='claim'&&app.mode==='real'&&!app.preview&&!payload.supported_operation_confirmed){modal('真机手动接管','<p>仅用于完整29自由度、腰部未锁定、可靠机械支撑下的关节调试。请确认现场已核定增益及停止方式，且其他控制器已退出。接管从当前反馈姿态开始，不自动归零。</p>','<button class="btn" data-action="close-modal">取消</button><button class="btn primary" data-action="confirm-real-claim">确认支撑就绪并接管</button>');return;}
 if(scope==='robot'&&action==='initialize'){payload={initialization_profile_id:app.snapshot.robot.initialization_profile_id};if(!app.preview&&app.mode==='real'){app.pendingInitialize=payload;modal('机器人初始化','<p>启动真机只读预检，核对标定授权、LowState CRC、机器模式及控制源。此步骤不创建运动发布器；之后还需显式手动接管。</p>','<button class="btn" data-action="close-modal">取消</button><button class="btn primary" data-action="confirm-initialize">确认初始化</button>');return;}}
 if(scope==='robot'&&action==='release'){payload={lease_token:app.leaseToken};app.leaseToken=null;app.liveManual=false;manualPending=false;}
 if(scope==='workflows'&&action==='cancel')payload={run_id:app.workflowJob?.run_id};
 if(scope==='workflows'&&action==='run'){const errors=validateGraph(app.graph);if(errors.length)throw new Error(errors[0]);payload={graph:executionGraph(app.graph)};}
 const commandEpoch=app.commandEpoch||0;if(scope==='safety')app.commandEpoch=commandEpoch+1;
 if(scope==='services'&&action==='stop')app.stoppingService=payload.service_id;
 app.activeCommands=(app.activeCommands||0)+1;app.busy=true;update();
 try{
  let result;
  if(scope==='deployment'&&action==='cancel')payload={...payload,job_id:app.job?.id||app.snapshot.deployment.id};
  if(scope==='deployment'&&action==='prepare'&&app.preview){
   api.runtime.state.deployment={state:'running',steps:STAGES.map(([id,label])=>({id,label,state:'pending'}))};
   for(const step of api.runtime.state.deployment.steps){if(commandEpoch!==(app.commandEpoch||0))return;step.state='running';app.snapshot=api.runtime.snapshot();update();await new Promise(resolve=>setTimeout(resolve,380));step.state='succeeded';}
   if(commandEpoch!==(app.commandEpoch||0))return;api.runtime.state.deployment.state='ready';result=await api.command(scope,action,{...payload,allow_motion:false});
  }else result=await api.command(scope,action,scope==='deployment'?{...payload,allow_motion:false}:payload);
  if(scope==='robot'&&action==='claim'&&result.lease_token){app.leaseToken=result.lease_token;manualSequence=0;}
  if(scope==='robot'&&action==='release'||scope==='safety'){app.leaseToken=null;app.liveManual=false;manualPending=false;}
  if(scope==='workflows'&&result.run_id)app.workflowJob={run_id:result.run_id,graph_id:app.graph.id,state:'pending',node_states:{}};
  if(result.job_id)app.job={id:result.job_id,state:'pending'};
  app.snapshot=await api.loadSnapshot();app.lastPollError=false;
  toast(app.preview?'界面预演：操作完成':result.job_id?'执行端已接收，正在处理':result.message||'执行端已接收操作');
  localEvent(app.preview?'本地预演操作完成':'执行端接收操作',`${scope}.${action}${result.command_id?' · '+result.command_id:''}`,'success');
 if(scope==='collection'&&['save','discard','end'].includes(action))loadEpisodes();
 }finally{if(scope==='services'&&action==='stop')app.stoppingService=null;app.activeCommands--;app.busy=app.activeCommands>0;update();}
}
async function confirmPose(){
 const payload=app.pendingPose;if(!payload)return;closeModal();app.pendingPose=null;
 const reason=api.can('robot','apply_pose');if(reason)throw new Error(reason);
 app.activeCommands=(app.activeCommands||0)+1;app.busy=true;update();try{await api.command('robot','apply_pose',payload);toast('执行端已接收目标姿态');app.snapshot=await api.loadSnapshot();}finally{app.activeCommands--;app.busy=app.activeCommands>0;update();}
}
async function switchPreview(){
 if(app.busy){toast('当前操作处理中，请稍后切换');return;}
 runner?.stop();api.runtime.command('safety','stop');
 app.liveManual=false;app.leaseToken=null;manualPending=false;app.preview=!app.preview;api.preview=app.preview;api.v1Unavailable=false;app.snapshot=emptySnapshot();api.snapshot=app.snapshot;app.playback=null;app.dataset='';app.offset=0;app.job=null;app.workflowJob=null;app.target=false;app.episodes=[];app.lastPollError=false;episodeRequest++;
 const url=new URL(location.href);if(app.preview)url.searchParams.set('preview','1');else url.searchParams.delete('preview');history.replaceState(null,'',url);
 render();await poll();
}
async function handleClick(event){
 const target=event.target.closest('button,a[href^="#"]');if(!target)return;
 if(target.tagName==='A'){const view=target.getAttribute('href').slice(1);if(VIEWS.some(v=>v[0]===view)){event.preventDefault();goView(view);}return;}
 if(target.disabled)return;
 try{
  if(target.dataset.command){await runCommand(target.dataset.command,target.dataset.op,JSON.parse(target.dataset.payload||'{}'));return;}
  const action=target.dataset.action;
  if(action==='unlock')modal('授权操作','<p class="help">输入工作站本地保存的操作密钥。授权在本浏览器中有效 8 小时。</p><label class="field">操作密钥<input type="password" data-operation-key autocomplete="off"></label>','<button class="btn" data-action="close-modal">取消</button><button class="btn primary" data-action="confirm-unlock">授权</button>');
  if(action==='confirm-unlock'){const key=$('[data-operation-key]')?.value||'';await api.request('/api/v1/console/session',{method:'POST',body:JSON.stringify({operation_key:key})});closeModal();await poll();toast('已授权操作');}
  if(action==='menu')$('.sidebar').classList.toggle('open');
  if(action==='preview')await switchPreview();
  if(action==='refresh'){api.v1Unavailable=false;await poll();toast('状态已刷新');}
  if(action==='close-modal')closeModal();
  if(action==='collection-logs'){const data=app.preview?{log:'界面预演：未启动真实采集进程'}:await api.request('/api/v1/console/collection/logs');$('[data-collection-log]').textContent=data.log||'暂无采集日志';}
  if(action==='events'){const events=[...app.localEvents,...app.snapshot.events].sort((a,b)=>Date.parse(b.at)-Date.parse(a.at));$('#overlay-root').innerHTML=`<div class="overlay" data-overlay><section class="drawer" role="dialog" aria-modal="true" aria-label="事件与日志"><header class="modal-header"><h2>事件与日志</h2><button class="icon-button" data-action="close-modal" aria-label="关闭日志">${icon('x')}</button></header><div class="card-body"><div class="notice compact">${icon('info')}${app.preview?'此处为本地界面预演事件。':'显示执行端事件和浏览器操作结果。'}</div>${eventHTML(events)}</div></section></div>`;icons();}
  if(action==='camera-expand'){modal(CAMERAS.find(c=>c.id===target.dataset.id).label,cameraHTML(target.dataset.id),'',true);updateCameras();}
  if(action==='sensor-main'){app.sensor=target.dataset.id;render();}
  if(action==='joint-group'){app.group=target.dataset.id;render();}
  if(action==='reset-view')robotScene?.resetView();
  if(action==='copy-pose'){const values=namedJointValues(app.snapshot,profile);if(!values)throw new Error('当前没有完整、有效的 29 维反馈');profile.body_joints.forEach((name,i)=>app.targets[name]=values[i]);app.target=true;render();}
  if(action==='zero-pose'){profile.body_joints.forEach(n=>app.targets[n]=0);app.target=true;render();}
  if(action==='confirm-pose')await confirmPose();
  if(action==='confirm-real-claim'){closeModal();await runCommand('robot','claim',{owner:'manual',supported_operation_confirmed:true});}
  if(action==='confirm-initialize'){const payload=app.pendingInitialize;closeModal();app.pendingInitialize=null;if(payload){await api.command('robot','initialize',payload);toast('执行端已接收初始化请求');await poll();}}
  if(action==='dataset'){app.dataset=target.dataset.name;app.offset=0;app.search='';const input=$('[data-episode-search]');if(input)input.value='';await loadEpisodes();}
  if(action==='episodes-refresh')await loadEpisodes();
  if(action==='episodes-prev'){app.offset=Math.max(0,app.offset-30);await loadEpisodes();}
  if(action==='episodes-next'){app.offset+=30;await loadEpisodes();}
  if(action==='review')await openReview(Number(target.dataset.episode));
  if(action==='close-playback'){app.playback=null;render();}
  if(action==='rate'){const index=Number(target.dataset.episode),dataset=target.dataset.dataset,row=app.episodes.find(r=>r.episode_index===index&&dataset===app.dataset)||app.playback?.review.episode;if(!row)return;const grade=row.grade===target.dataset.grade?null:target.dataset.grade;await api.rate(dataset,index,grade);row.grade=grade;if(app.playback?.review.episode.episode_index===index&&app.playback.review.episode.dataset===dataset)app.playback.review.episode.grade=grade;renderEpisodes();if(app.playback){$$('.replay-layout .rating').forEach(el=>el.innerHTML=ratingHTML(app.playback.review.episode).replace(/^<div[^>]*>|<\/div>$/g,''));}toast(app.preview?'预演评级已更新':'片段评级已保存');}
  if(action==='replay-toggle'){if(playback?.primary&&!playback.primary.paused)playback.pause();else await playback?.play();}
  if(action==='replay-step')playback?.step(Number(target.dataset.direction));
  if(action?.startsWith('flow-'))await handleFlowAction(action,target);
 }catch(error){toast(error.message||'操作未完成','danger');localEvent('操作未完成',error.message||'请检查当前状态','error');}
}
function handleInput(event){
 const el=event.target;
 if(el.dataset.config){app.config[el.dataset.config]=el.type==='checkbox'?el.checked:el.value;saveStore('robot-station-console-config-v1',app.config);update();}
 if(el.hasAttribute('data-episode-search')){app.search=el.value;renderEpisodes();}
 if(el.hasAttribute('data-target-joint')||el.hasAttribute('data-target-slider')){
  const name=el.dataset.targetJoint||el.dataset.targetSlider,spec=profile.joints.find(j=>j.name===name);
  const degrees=Number(el.value),valid=el.value!==''&&finite(degrees)&&degrees>=Number(degree(spec.lower))&&degrees<=Number(degree(spec.upper));
  el.setCustomValidity(valid?'':'请输入参考范围内的角度');el.setAttribute('aria-invalid',String(!valid));
  if(valid){
   if(app.liveManual)manualPending=true;
   const value=Math.max(spec.lower,Math.min(spec.upper,degrees*Math.PI/180));app.targets[name]=value;
   const control=el.closest('.joint-target-control'),number=control.querySelector('[data-target-joint]'),slider=control.querySelector('[data-target-slider]');
   if(el!==number)number.value=degree(value);if(el!==slider)slider.value=degree(value);
   number.setCustomValidity('');number.setAttribute('aria-invalid','false');
   slider.setAttribute('aria-valuetext',`${degree(value)} 度，仅本地预览`);slider.style.setProperty('--joint-fill',`${jointTargetPercent(spec,value)}%`);
   app.target=true;const toggle=$('[data-target-preview]');if(toggle)toggle.checked=true;
   robotScene?.setPose(profile.body_joints.map(n=>app.targets[n]));const label=$('[data-pose-label]');if(label)label.textContent=app.liveManual?(app.mode==='real'?'目标姿态 · 真机联动':'目标姿态 · MuJoCo 联动'):'目标预览 · 本地';
  }
 }
 if(el.hasAttribute('data-replay-progress'))playback?.seek(Number(el.value));
 if(el.hasAttribute('data-flow-name'))app.graph.name=el.value;
}
async function handleChange(event){
 const el=event.target;
 if(el.hasAttribute('data-mode')){if(app.busy){el.value=app.mode;return;}if(app.preview)await api.runtime.command('safety','stop');app.liveManual=false;app.leaseToken=null;manualPending=false;app.mode=el.value;api.mode=app.mode;api.v1Unavailable=false;app.snapshot=emptySnapshot();app.playback=null;app.dataset='';app.offset=0;render();await poll();}
 if(el.hasAttribute('data-preview-fault')){if(el.value==='robot-offline'||el.value==='camera-offline')await api.runtime.command('safety','stop');api.runtime.fault=el.value;app.snapshot=await api.loadSnapshot();update();}
 if(el.hasAttribute('data-live-manual')){if(el.checked&&(!app.leaseToken||app.snapshot.robot.owner!=='manual')){el.checked=false;toast('请先初始化并手动接管','danger');return;}app.liveManual=el.checked;manualPending=false;}
 if(el.hasAttribute('data-target-preview')){app.target=el.checked;update();}
 if(el.hasAttribute('data-replay-speed'))playback?.speed(Number(el.value));
 if(el.hasAttribute('data-channel')){const selected=$$('[data-channel]:checked');if(selected.length>6){el.checked=false;toast('最多同时查看 6 个关节');return;}playback?.setChannels(selected.map(e=>Number(e.dataset.channel)));}
 if(el.hasAttribute('data-flow-template')&&el.value){app.graph=templateGraph(el.value);app.flowLog=[];render();}
}
async function handleFlowAction(action,target){
 if(action==='flow-save'){const errors=validateGraph(app.graph);if(errors.length)throw new Error(errors[0]);saveStore('robot-station-workflow-v1',app.graph);toast('流程已保存到当前浏览器');}
 if(action==='flow-validate'){const errors=validateGraph(app.graph);if(errors.length){modal('流程校验',`<p>${errors.map(esc).join('<br>')}</p>`);}else toast('流程校验通过：节点、分支、可达性与流转上限有效');}
 if(action==='flow-export'){const errors=validateGraph(app.graph);if(errors.length)throw new Error(errors[0]);const url=URL.createObjectURL(new Blob([JSON.stringify(app.graph,null,2)],{type:'application/json'}));const link=document.createElement('a');link.href=url;link.download='robot-station-workflow.json';link.click();setTimeout(()=>URL.revokeObjectURL(url),1000);}
 if(action==='flow-import')modal('导入流程 JSON','<p>粘贴 Robot Station schema_version 1 流程。导入会替换当前画布，可先导出保留。</p><textarea data-import-json aria-label="流程 JSON" placeholder="粘贴流程 JSON"></textarea>','<button class="btn" data-action="close-modal">取消</button><button class="btn primary" data-action="flow-import-confirm">校验并导入</button>');
 if(action==='flow-import-confirm'){const text=$('[data-import-json]').value;if(text.length>128000)throw new Error('流程文件超过 128 KB');let graph;try{graph=JSON.parse(text);}catch{throw new Error('JSON 格式不正确');}const errors=validateGraph(graph);if(errors.length)throw new Error(errors[0]);app.graph=graph;closeModal();render();toast('流程已导入，请保存草稿');}
 if(action==='flow-zoom'){editor.setZoom(editor.zoom+Number(target.dataset.delta));$('[data-flow-zoom]').textContent=Math.round(editor.zoom*100)+'%';}
 if(action==='flow-add'){if(app.graph.nodes.length>=100)throw new Error('最多支持 100 个节点');const type=NODE_TYPES.find(n=>n[0]===target.dataset.id);const node={id:uid(),type:type[0],label:type[1],x:55+(app.graph.nodes.length%4)*245,y:48+Math.floor(app.graph.nodes.length/4)*158,timeout_s:30,params:{}};app.graph.nodes.push(node);editor.paint();flowChanged();selectFlow(node);}
 if(action==='flow-delete'){
  const selected=app.flowSelection;if(!selected)return;
  if(selected.kind==='edge')app.graph.edges=app.graph.edges.filter(e=>e.id!==selected.id);
  else {app.graph.nodes=app.graph.nodes.filter(n=>n.id!==selected.id);app.graph.edges=app.graph.edges.filter(e=>e.from!==selected.id&&e.to!==selected.id);}
  editor.paint();flowChanged();app.flowSelection=null;$('[data-flow-inspector]').innerHTML='<p class="help">选择节点或连线查看属性。</p>';
 }
 if(action==='flow-property-save'){
  const selected=app.flowSelection;if(!selected)return;
  if(selected.kind==='edge'){const edge=app.graph.edges.find(e=>e.id===selected.id),outcome=$('[data-edge-outcome]').value;if(app.graph.edges.some(e=>e.id!==edge.id&&e.from===edge.from&&e.outcome===outcome))throw new Error('此节点已有相同结果的出口');edge.outcome=outcome;edge.to=$('[data-edge-to]').value;}
  else{const node=app.graph.nodes.find(n=>n.id===selected.id),label=$('[data-node-label]').value.trim(),timeout=Number($('[data-node-timeout]').value);if(!label||timeout<1||timeout>3600)throw new Error('填写节点名称，并设置 1～3600 秒超时');let params;try{params=JSON.parse($('[data-node-params]').value);}catch{throw new Error('节点参数不是有效 JSON');}if(!params||typeof params!=='object'||Array.isArray(params))throw new Error('节点参数应为 JSON 对象');Object.assign(node,{label,timeout_s:timeout,params,ui:{preview_fail:$('[data-node-fail]').checked}});}
  editor.paint();flowChanged();toast('画布属性已更新');
 }
 if(action==='flow-preview'){if(runner?.running)throw new Error('预演正在运行');const errors=validateGraph(app.graph);if(errors.length)throw new Error(errors[0]);editor.execution='preview';editor.states={};editor.paint();runner=new WorkflowRunner(e=>{if(e.type==='node'){editor?.setNodeState(e.id,e.state);if(e.state==='running')flowLog('进入 '+e.label);}if(e.type==='complete'){flowLog('预演完成 · 未向设备发送指令');toast('流程本地预演完成');}if(e.type==='cancelled')flowLog('预演已停止');});flowLog('开始本地预演');runner.run(clone(app.graph)).catch(error=>{flowLog(error.message);toast(error.message,'danger');});}
 if(action==='flow-stop')runner?.stop();
}
shell();
$$('[data-config]').forEach(el=>{if(el.tagName==='SELECT')el.value=app.config[el.dataset.config];});
await poll();
setInterval(poll,2000);
setInterval(()=>{if(!document.hidden)update();},1000);
window.addEventListener('beforeunload',()=>{runner?.stop();robotScene?.dispose();playback?.dispose();});


let manualSequence=0,manualPending=false,manualInFlight=false,heartbeatBusy=false;
setInterval(async()=>{if(!app.leaseToken||app.preview||heartbeatBusy)return;heartbeatBusy=true;const heartbeatToken=app.leaseToken;try{await api.request('/api/v1/console/robot/manual',{method:'POST',body:JSON.stringify({mode:app.mode,action:'heartbeat',lease_token:heartbeatToken})});}catch(e){if(app.leaseToken!==heartbeatToken)return;app.leaseToken=null;app.liveManual=false;manualPending=false;const el=$('[data-live-manual]');if(el)el.checked=false;toast('手动控制已释放：'+e.message,'danger');}finally{heartbeatBusy=false;}},900);
setInterval(async()=>{if(!app.liveManual||!app.leaseToken||!manualPending||manualInFlight)return;manualPending=false;manualInFlight=true;try{await api.request('/api/v1/console/robot/manual',{method:'POST',body:JSON.stringify({mode:app.mode,action:'apply_pose',lease_token:app.leaseToken,sequence:++manualSequence,unit:'rad',transition_seconds:.25,velocity_limit_rad_s:.5,joints:profile.body_joints.map(name=>({name,position_rad:app.targets[name]}))})});}catch(e){app.liveManual=false;const el=$('[data-live-manual]');if(el)el.checked=false;toast(e.message,'danger');}finally{manualInFlight=false;}},100);
