import {esc, duration} from './console-core.js';
const icon = name => `<i data-lucide="${name}" aria-hidden="true"></i>`;
const label = format => format==='hdf5'?'HDF5 · SONIC v1':'LeRobot v2.1';
const states = {queued:'待启动',running:'转换中',succeeded:'已完成',failed:'失败',cancelled:'已取消'};
const bytes = value => value>=1024**3?(value/1024**3).toFixed(2)+' GB':value>=1024**2?(value/1024**2).toFixed(1)+' MB':Math.round(value/1024)+' KB';
const active = job => job&&['queued','running'].includes(job.state);
const pill = (text,tone='') => `<span class="badge ${tone}">${esc(text)}</span>`;
export function conversionView(){
 return `<div class="summary-strip conversion-summary"><div class="card summary"><span class="summary-icon">${icon('file-stack')}</span><div><b style="font-size:16px">LeRobot v2.1</b><small>SONIC 原生采集格式</small></div></div><div class="card summary"><span class="summary-icon">${icon('folder-open')}</span><div><b data-convert-source-count>--</b><small>已发现正式数据集</small></div></div><div class="card summary"><span class="summary-icon">${icon('repeat-2')}</span><div><b data-convert-job-count>0</b><small>转换任务</small></div></div><div class="card summary"><span class="summary-icon">${icon('hard-drive')}</span><div><b style="font-size:16px" data-convert-environment>检查中</b><small>离线转换环境</small></div></div></div><div class="conversion-layout"><div class="stack"><section class="card"><header class="card-head"><h2 class="card-title">${icon('folder-input')}转换来源</h2><button class="btn text sm" data-convert-action="refresh">${icon('refresh-cw')}刷新来源</button></header><div class="card-body"><div class="section-label"><span>01</span> 选择已保存的数据集</div><label class="field">SONIC 采集数据<select data-convert-dataset aria-label="转换来源"><option value="">正在读取目录…</option></select></label><div class="row between section-gap"><span class="help" style="margin:0">读取 Parquet、视频与元数据，校验不修改文件</span><button class="btn soft sm" data-convert-action="inspect">${icon('scan-line')}校验来源</button></div><div data-convert-inspection class="section-gap"></div></div></section><section class="card"><header class="card-head"><h2 class="card-title">${icon('replace-all')}输出配置</h2>${pill('另存为新目录','blue')}</header><div class="card-body"><div class="section-label"><span>02</span> 选择目标格式</div><div class="format-options"><button class="format-option selected" data-convert-format="hdf5" aria-pressed="true">${icon('file-box')}<strong>HDF5</strong><span>每个片段一个 .hdf5 文件</span><small>保留原始数值、时间戳与视频</small></button><button class="format-option" data-convert-format="lerobot_v21" aria-pressed="false">${icon('database')}<strong>LeRobot v2.1</strong><span>校验原生格式并导出完整副本</span><small>Parquet + MP4 + JSON</small></button></div><div class="fields section-gap"><label class="field wide">输出名称<input data-convert-output aria-label="输出名称" maxlength="80" placeholder="例如 g1_session_hdf5" autocomplete="off"></label><label class="field wide">视频存储方式<select data-convert-video aria-label="视频存储方式"><option value="embedded_mp4">内嵌原始 MP4 · 保持压缩视频</option><option value="rgb">逐帧 RGB · 便于读取图像，体积更大</option></select></label></div><div class="conversion-path section-gap"><span class="tiny muted">输出根目录</span><code data-convert-root>正在读取…</code></div><div class="notice compact section-gap">${icon('info')}完整导出全部已保存片段，保留舍弃标记；不改采样率，不重新排列身体或手部关节。</div><div class="row between section-gap"><span class="tiny muted" data-convert-reason>请先选择并校验来源</span><button class="btn primary" data-convert-action="start" disabled>${icon('repeat-2')}开始转换</button></div></div></section><section class="card"><header class="card-head"><h2 class="card-title">${icon('activity')}转换任务</h2><span data-convert-status>${pill('尚未提交')}</span></header><div class="card-body" data-convert-current></div><div class="card-foot">只处理离线文件，不申请机器人控制权。</div></section></div><div class="stack"><section class="card"><header class="card-head"><h2 class="card-title">${icon('files')}原生数据是什么？</h2></header><div class="card-body"><p class="conversion-copy">当前 SONIC VLA 采集器直接写入 <b>LeRobot v2.1</b>，并附带 GR00T 模态与机器人配置。</p><div class="conversion-tree">data/…/*.parquet<br><span>状态、动作、追踪和时间戳</span><br><br>videos/…/*.mp4<br><span>实际录制的相机视频</span><br><br>meta/*.json / *.jsonl<br><span>字段、任务、片段、统计与模态</span></div><p class="help">C++ 控制器的 CSV 属于单独的调试日志，不能自动视为含三路视频的完整训练数据集。</p></div></section><section class="card"><header class="card-head"><h2 class="card-title">${icon('braces')}HDF5 输出结构</h2>${pill('SONIC v1','purple')}</header><div class="card-body"><div class="conversion-tree">episodes/episode_000000.hdf5<br><br>/frames/原始字段名称<br><span>按原始形状保存数值与时间戳</span><br><br>/videos/原始相机名称<br><span>encoded_mp4 或 rgb</span><br><br>/meta/*<br><span>任务、片段、字段与机器人配置</span></div><p class="help">HDF5 是存储容器；本页提供保留 SONIC 语义的通用结构。ACT、Robomimic 等训练器若有专用字段要求，需再配置相应映射。</p></div></section><section class="card"><header class="card-head"><h2 class="card-title">${icon('history')}最近任务</h2><button class="btn text sm" data-convert-action="jobs">刷新</button></header><div class="card-body" data-convert-history></div></section></div></div>`;
}
export class DataConversionPage{
 constructor(root,api,preview,shared={}){
  this.root=root;this.api=api;this.preview=preview;this.shared=shared;this.dead=false;this.loading=false;this.busy=false;this.inspectToken=0;
  if(shared.preview!==preview)Object.assign(shared,{preview,dataset:'',format:'hdf5',video_mode:'embedded_mp4',output_name:'',inspection:null,jobs:[],current:null,sources:[],environment:{}});
  this.s=shared;
  this.click=event=>{const format=event.target.closest('[data-convert-format]'),button=event.target.closest('[data-convert-action]');if(format){this.s.format=format.dataset.convertFormat;if(!this.s.userNamedOutput)this.s.output_name='';this.s.userNamedOutput=false;this.syncConfig();this.paint();return;}if(button&&!button.disabled)this.action(button.dataset.convertAction).catch(error=>this.error(error.message));};
  this.change=event=>{const el=event.target;if(el.hasAttribute('data-convert-dataset')){this.s.dataset=el.value;this.s.inspection=null;this.s.output_name='';this.s.userNamedOutput=false;this.syncConfig();this.inspect();}if(el.hasAttribute('data-convert-video'))this.s.video_mode=el.value;};
  this.input=event=>{if(event.target.hasAttribute('data-convert-output')){this.s.output_name=event.target.value;this.s.userNamedOutput=true;this.paintGate();}};
  root.addEventListener('click',this.click);root.addEventListener('change',this.change);root.addEventListener('input',this.input);
  this.refresh().catch(error=>this.error(error.message));
  this.timer=setInterval(()=>this.refreshJobs().catch(error=>this.error(error.message)),1500);
 }
 $(selector){return this.root.querySelector(selector);}
 all(selector){return [...this.root.querySelectorAll(selector)];}
 async request(path,body){return this.api.request('/api/conversions'+path,body?{method:'POST',body:JSON.stringify(body)}:{});}
 async refresh(){
  this.loading=true;
  try{
   let result;
   if(this.preview)result={datasets:[{name:'synthetic_sonic_session',version:'v2.1',episodes:3,frames:270,fps:15,demo_only:true}],environment:{ready:true,ffmpeg:true,ffprobe:true,output_root:'界面预演 / 不写入磁盘'}};
   else result=await this.request('/sources');
   if(this.dead)return;
   this.s.sources=result.datasets;this.s.environment=result.environment;
   if(!this.s.sources.some(d=>d.name===this.s.dataset)){this.s.dataset=this.s.sources.find(d=>!d.demo_only)?.name||this.s.sources[0]?.name||'';this.s.inspection=null;}
   this.$('[data-convert-dataset]').innerHTML=this.s.sources.length?this.s.sources.map(d=>`<option value="${esc(d.name)}">${esc(d.name)} · ${esc(d.episodes)} 段${d.demo_only?(this.preview?' · 合成预演':' · 演示元数据'):''}</option>`).join(''):'<option value="">暂无已保存的数据集</option>';
   this.$('[data-convert-dataset]').value=this.s.dataset;this.syncConfig();await this.refreshJobs();await this.inspect();
  }finally{this.loading=false;if(!this.dead)this.paint();}
 }
 syncConfig(){
  if(!this.s.output_name&&this.s.dataset)this.s.output_name=(this.s.dataset.slice(0,46)+'_'+(this.s.format==='hdf5'?'hdf5':'lerobot')+'_'+Date.now().toString(36)).slice(0,80);
  this.$('[data-convert-output]').value=this.s.output_name;
  this.$('[data-convert-video]').value=this.s.format==='lerobot_v21'?'embedded_mp4':this.s.video_mode;
  this.$('[data-convert-video]').disabled=this.s.format!=='hdf5';
  this.all('[data-convert-format]').forEach(button=>{button.classList.toggle('selected',button.dataset.convertFormat===this.s.format);button.setAttribute('aria-pressed',button.dataset.convertFormat===this.s.format);});
 }
 async inspect(){
  if(!this.s.dataset)return;
  const token=++this.inspectToken;this.inspectionSignature='';this.$('[data-convert-inspection]').innerHTML='<p class="help">正在校验文件与元数据…</p>';
  try{
   const result=this.preview?{inspection:{dataset:this.s.dataset,native_format:'LeRobot v2.1 / SONIC VLA',episodes:3,frames:270,fps:15,bytes:1024*1024*4,video_keys:['observation.images.ego_view','observation.images.left_wrist','observation.images.right_wrist'],can_convert:true,errors:[],warnings:['此结果仅用于界面预演，文件和转换结果均为模拟'],fingerprint:'preview',features:[{name:'observation.state',dtype:'float32',shape:[43]},{name:'action.wbc',dtype:'float32',shape:[43]},{name:'timestamp',dtype:'float32',shape:[1]},{name:'teleop.smpl_pose',dtype:'float32',shape:[72]}]}}:await this.request('/inspect',{dataset:this.s.dataset});
   if(this.dead||token!==this.inspectToken)return;this.s.inspection=result.inspection;this.paint();
  }catch(error){if(token===this.inspectToken)this.error(error.message);}
 }
 async refreshJobs(){
  if(this.dead||this.jobsLoading)return;this.jobsLoading=true;
  try{
  if(this.preview){
   for(const job of this.s.jobs){if(active(job)){job.progress=Math.min(100,Math.floor((Date.now()-job.started)/45));job.state=job.progress===100?'succeeded':'running';job.message=job.state==='succeeded'?'界面预演完成 · 未生成实际文件':'正在预演字段校验和格式转换';job.episodes_done=Math.floor(job.progress/100*3);if(job.progress===100)job.result={episodes:3,frames:270};}}
  }else{
   const result=await this.request('/jobs');if(this.dead)return;this.s.jobs=result.jobs;
  }
  if(this.s.current)this.s.current=this.s.jobs.find(j=>j.id===this.s.current.id)||this.s.current;
  else this.s.current=this.s.jobs[0]||null;
  this.paint();
  }finally{this.jobsLoading=false;}
 }
 gate(){
  if(this.busy||this.loading)return '正在处理请求';
  if(!this.s.environment.ready)return '离线转换环境未就绪';
  if(!this.s.inspection?.can_convert)return '先校验完整的来源文件';
  if(this.s.jobs.some(active))return '请等待当前转换完成或取消';
  if(!/^[A-Za-z0-9_-]{1,80}$/.test(this.s.output_name))return '输出名称请使用字母、数字、下划线或短横线';
  return '';
 }
 paintGate(){if(this.dead)return;const reason=this.gate();this.$('[data-convert-action="start"]').disabled=!!reason;this.$('[data-convert-reason]').textContent=reason||'来源完整，可以开始'+(this.preview?'本地预演':'离线转换');}
 paint(){
  if(this.dead)return;
  this.$('[data-convert-source-count]').textContent=this.s.sources.filter(d=>!d.demo_only).length;
  this.$('[data-convert-job-count]').textContent=this.s.jobs.length;
  this.$('[data-convert-environment]').textContent=this.preview?'界面预演':this.s.environment.ready?'已就绪':'待准备';
  this.$('[data-convert-root]').textContent=this.s.environment.output_root||'待连接转换服务';
  const i=this.s.inspection;
  const inspectionSignature=JSON.stringify(i);if(i&&this.inspectionSignature!==inspectionSignature){this.inspectionSignature=inspectionSignature;this.$('[data-convert-inspection]').innerHTML=`<div class="row between">${pill(i.can_convert?'文件完整':'暂不可转换',i.can_convert?'success':'warning')}<span class="tiny muted">${esc(i.native_format)}</span></div><div class="metric-grid"><div class="metric"><b>${i.episodes}</b><small>片段</small></div><div class="metric"><b>${i.frames?.toLocaleString()}</b><small>帧</small></div><div class="metric"><b>${i.fps||'--'}</b><small>FPS</small></div></div>${[...(i.errors||[]),...(i.warnings||[])].map(message=>`<div class="notice warning compact" style="margin-bottom:8px">${icon('info')}${esc(message)}</div>`).join('')}<div class="row between"><span class="tiny muted">实际文件体积 ${bytes(i.bytes||0)}</span><span class="tiny muted">${i.video_keys?.length||0} 路录制视频</span></div>${i.features?.length?`<details class="conversion-features section-gap"><summary>查看原始字段与维度（${i.features.length} 项）</summary><div class="table-scroll"><table class="check-table"><thead><tr><th>字段</th><th>类型 / 形状</th></tr></thead><tbody>${i.features.map(f=>`<tr><td class="mono">${esc(f.name)}</td><td>${esc(f.dtype)} · [${esc((f.shape||[]).join(', '))}]</td></tr>`).join('')}</tbody></table></div></details>`:''}`;
  }
  const job=this.s.current;
  this.$('[data-convert-status]').innerHTML=pill(job?states[job.state]||job.state:'尚未提交',job?.state==='succeeded'?'success':job?.state==='failed'?'danger':active(job)?'blue':'');
  const jobSignature=JSON.stringify(job);if(this.jobSignature!==jobSignature){this.jobSignature=jobSignature;this.$('[data-convert-current]').innerHTML=job?`<div class="row between"><b style="font-size:12px">${esc(job.dataset)}</b><span class="tiny muted">${label(job.format)}</span></div><div class="conversion-progress"><span style="width:${Math.min(100,Math.max(0,Number(job.progress)||0))}%"></span></div><div class="row between"><span class="help" style="margin:0">${esc(job.message)}</span><b class="tiny">${Math.floor(job.progress||0)}%</b></div><div class="row between section-gap"><span class="tiny muted">${job.episodes_done||0} / ${job.episodes_total||0} 段</span>${active(job)?'<button class="btn danger sm" data-convert-action="cancel">取消转换</button>':''}</div>${job.output?`<label class="field section-gap">${this.preview?'模拟输出位置':'输出位置'}<input readonly value="${esc(job.output)}" aria-label="转换输出位置"></label>`:''}${job.state==='succeeded'&&!this.preview?`<div class="conversion-downloads section-gap">${(job.files||[]).slice(0,12).map(file=>`<a href="/api/conversions/jobs/${encodeURIComponent(job.id)}/download?path=${encodeURIComponent(file.path)}" download>${icon('download')}${esc(file.path)}<span>${bytes(file.bytes)}</span></a>`).join('')}${job.files?.length>12?'<p class="help">其余文件可在输出目录查看。</p>':''}</div>`:''}`:'<div class="empty">选择来源并完成校验后，即可创建转换任务。</div>';
  }
  const historySignature=JSON.stringify(this.s.jobs);if(this.historySignature!==historySignature){this.historySignature=historySignature;this.$('[data-convert-history]').innerHTML=this.s.jobs.length?this.s.jobs.slice(0,8).map(j=>`<button class="conversion-history-item" data-convert-job="${esc(j.id)}"><span>${esc(j.dataset)}<small>${label(j.format)} · ${new Date((j.created_at||Date.now()/1000)*1000).toLocaleTimeString('zh-CN')}</small></span>${pill(states[j.state]||j.state,j.state==='succeeded'?'success':j.state==='failed'?'danger':'')}</button>`).join(''):'<p class="help">暂无任务记录</p>';
  this.all('[data-convert-job]').forEach(button=>button.onclick=()=>{this.s.current=this.s.jobs.find(j=>j.id===button.dataset.convertJob);this.paint();});
  }
  this.paintGate();globalThis.lucide?.createIcons();
 }
 error(message){if(this.dead)return;this.$('[data-convert-inspection]').innerHTML=`<div class="notice warning compact">${esc(message)}</div>`;this.s.inspection=null;this.paintGate();}
 async action(action){
  if(action==='refresh')return this.refresh();
  if(action==='inspect')return this.inspect();
  if(action==='jobs')return this.refreshJobs();
  if(action==='start'){
   const reason=this.gate();if(reason)throw new Error(reason);
   this.busy=true;this.paintGate();
   try{
    if(this.preview){const job={id:'preview-'+Date.now(),dataset:this.s.dataset,format:this.s.format,state:'running',progress:0,started:Date.now(),created_at:Date.now()/1000,message:'界面预演 · 不写磁盘',output:'界面预演/'+this.s.output_name,episodes_total:3};this.s.jobs.unshift(job);this.s.current=job;}
    else{const result=await this.request('/jobs',{dataset:this.s.dataset,format:this.s.format,output_name:this.s.output_name,video_mode:this.s.format==='lerobot_v21'?'embedded_mp4':this.s.video_mode,fingerprint:this.s.inspection.fingerprint});if(this.dead)return;this.s.current=result.job;this.s.jobs.unshift(result.job);}
    this.paint();
   }finally{this.busy=false;this.paintGate();}
  }
  if(action==='cancel'&&this.s.current){
   if(this.preview){this.s.current.state='cancelled';this.s.current.message='界面预演已取消';}
   else await this.request('/jobs/'+this.s.current.id+'/cancel',{});
   await this.refreshJobs();
  }
 }
 dispose(){this.dead=true;clearInterval(this.timer);this.inspectToken++;this.root.removeEventListener('click',this.click);this.root.removeEventListener('change',this.change);this.root.removeEventListener('input',this.input);}
}
