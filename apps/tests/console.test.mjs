import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import {emptySnapshot,normalizeSnapshot,legacySnapshot,commandAvailability,batteryReading,namedJointValues,safeMediaURL} from '../static/console-core.js';
import {ConsoleAPI} from '../static/console-api.js';
import {templateGraph,validateGraph,WorkflowRunner,executionGraph} from '../static/console-workflow.js';
import {PlaybackController} from '../static/console-playback.js';
const profile=JSON.parse(fs.readFileSync(new URL('../static/assets/g1/profile.json',import.meta.url)));
const now=new Date().toISOString();
function live(){const s=emptySnapshot();Object.assign(s,{source:'live',backend_connected:true,revision:23});s.robot={connected:true,observed_at:now,owner:'manual',joints:profile.body_joints.map((name,i)=>({name,position_rad:i/100}))};s.capabilities.commands=['robot.apply_pose','robot.claim','inference.start','collection.start'];s.interlocks={can_apply_pose:true,can_claim:true,can_infer:true,can_collect:true};return s;}
test('battery is unknown without a fresh connected robot and a fresh valid sample',()=>{
 const s=live();s.battery={observed_at:now,percent:15};assert.equal(batteryReading(s).tone,'warning');
 s.battery.percent=8;assert.equal(batteryReading(s).tone,'danger');
 for(const percent of [null,NaN,101,-1,'72']){s.battery.percent=percent;assert.equal(batteryReading(s).valid,false);}
 s.battery={observed_at:new Date(Date.now()-16000).toISOString(),percent:72};assert.equal(batteryReading(s).percent,null);
 s.battery.observed_at=now;s.robot.connected=false;assert.equal(batteryReading(s).percent,null);
 s.robot.connected=true;s.robot.observed_at=new Date(Date.now()-6000).toISOString();assert.equal(batteryReading(s).percent,null);
});
test('joint mapping follows names, requires every one of the 29 joints and rejects stale feedback',()=>{
 const s=live(),expected=s.robot.joints.map(j=>j.position_rad);s.robot.joints.reverse();assert.deepEqual(namedJointValues(s,profile),expected);
 s.robot.joints.pop();assert.equal(namedJointValues(s,profile),null);
 s.robot.joints=profile.body_joints.map(name=>({name,position_rad:0}));s.robot.observed_at='2020-01-01';assert.equal(namedJointValues(s,profile),null);
});
test('physical commands require backend capabilities, current connected robot, control owner and interlock',()=>{
 const s=live();assert.equal(commandAvailability(s,'robot.apply_pose'),'');
 s.robot.owner='pico';assert.match(commandAvailability(s,'robot.apply_pose'),/控制权/);
 s.robot.owner='manual';s.robot.connected=false;assert.match(commandAvailability(s,'robot.apply_pose'),/反馈/);
 s.robot.connected=true;s.interlocks.can_apply_pose=false;assert.notEqual(commandAvailability(s,'robot.apply_pose'),'');
 s.interlocks.can_apply_pose=true;s.capabilities.commands=[];assert.notEqual(commandAvailability(s,'robot.apply_pose'),'');
});
test('legacy fallback never invents robot, battery, camera or execution capabilities',()=>{
 const s=legacySnapshot({status:{endpoints:[{online:true}]},totals:{episodes:7},groups:[]});
 assert.equal(s.source,'legacy-readonly');assert.equal(s.backend_connected,false);assert.equal(s.robot.connected,false);assert.equal(batteryReading(s).valid,false);assert.deepEqual(s.capabilities.commands,[]);
 assert.notEqual(commandAvailability(s,'collection.start'),'');
});
test('infrastructure stops obey backend blockers without requiring robot feedback',()=>{
 const s=live();s.robot.connected=false;s.capabilities.commands=['services.docker.stop','services.pc_service.stop'];
 s.services={docker:{stop_allowed:true},pc_service:{stop_allowed:false,stop_reason:'采集任务进行中'}};
 assert.equal(commandAvailability(s,'services.docker.stop'),'');
 assert.equal(commandAvailability(s,'services.pc_service.stop'),'采集任务进行中');
 s.services.docker={};assert.notEqual(commandAvailability(s,'services.docker.stop'),'');
 s.access={authorized:false};s.services.docker.stop_allowed=true;assert.match(commandAvailability(s,'services.docker.stop'),/授权/);
});
test('snapshot normalization preserves the backend revision for conditional commands',()=>assert.equal(normalizeSnapshot({...live(),revision:64}).revision,64));
test('media URL validation rejects executable schemes and embedded credentials',()=>{
 for(const value of ['javascript:alert(1)','data:text/plain,abc','file:///tmp/a','http://user:secret@example.com/a'])assert.equal(safeMediaURL(value),'');
 assert.equal(safeMediaURL('/api/episodes/video'), 'http://localhost/api/episodes/video');
});
test('preview operations make zero network requests and obey inference/collection mutual exclusion',async()=>{
 let requests=0;const api=new ConsoleAPI({profile,preview:true,fetchImpl:()=>{requests++;throw new Error('Unexpected network');}});
 await api.loadSnapshot();await api.command('inference','connect');await api.command('robot','claim',{owner:'task-model'});await api.command('inference','start',{task:'test'});
 assert.equal(api.snapshot.model.state,'running');assert.notEqual(api.can('collection','start'),'');
 await api.command('safety','stop');await api.command('collection','prepare');await api.command('collection','start');
 assert.equal(api.snapshot.collection.recording,true);assert.notEqual(api.can('inference','start'),'');
 await api.command('collection','save');assert.equal(api.runtime.episodes.length,4);await api.listEpisodes('frontend_preview');await api.review('frontend_preview',0);await api.series('frontend_preview',0);await api.rate('frontend_preview',0,'A');assert.equal(requests,0);
});
test('unsupported v1 falls back only to read-only metadata and cannot POST legacy hardware APIs',async()=>{
 const requests=[];const api=new ConsoleAPI({profile,fetchImpl:async(path,opts)=>{requests.push([path,opts.method||'GET']);return new Response(JSON.stringify(path.startsWith('/api/v1/')?{error:'not implemented'}:{ok:true,status:{},groups:[]}),{status:path.startsWith('/api/v1/')?404:200});}});
 await api.loadSnapshot();await assert.rejects(api.command('collection','start'),/未接入/);await assert.rejects(api.command('deployment','prepare'),/未接入/);
 assert.equal(requests.length,2);assert.ok(requests.every(([,method])=>method==='GET'));assert.ok(!requests.some(([path])=>/stack|record/.test(path)));
});
test('live commands carry idempotency, environment, profile and expected revision',async()=>{
 let request;const api=new ConsoleAPI({profile,mode:'real',fetchImpl:async(path,opts)=>{request={path,opts};return new Response('{"ok":true,"command_id":"c1"}');}});
 api.snapshot=live();await api.command('robot','apply_pose',{joints:[]});const body=JSON.parse(request.opts.body);
 assert.equal(request.path,'/api/v1/console/robot/commands');assert.equal(body.expected_revision,23);assert.equal(body.mode,'real');assert.equal(body.profile_id,profile.id);assert.ok(request.opts.headers['Idempotency-Key']);
});
test('v1 snapshot failure does not reuse stale successful capabilities',async()=>{
 const api=new ConsoleAPI({profile,fetchImpl:async()=>new Response('{"error":"offline"}',{status:503})});api.snapshot=live();await assert.rejects(api.loadSnapshot());assert.equal(api.snapshot.backend_connected,false);
});
test('workflow templates are valid and malformed imports do not crash validation',()=>{
 for(const kind of ['inference','collection'])assert.deepEqual(validateGraph(templateGraph(kind)),[]);
 for(const graph of [null,{schema_version:1,nodes:[null],edges:[]},{schema_version:1,nodes:[],edges:[null]}])assert.ok(validateGraph(graph).length);
 const g=templateGraph();g.edges[0].to='missing';assert.ok(validateGraph(g).some(e=>e.includes('删除')));
});
test('workflow execution excludes UI-only fault simulation',()=>{
 const g=templateGraph();g.nodes[1].ui={preview_fail:true};assert.equal(executionGraph(g).nodes[1].ui,undefined);assert.equal(g.nodes[1].ui.preview_fail,true);
});
test('workflow dry-run has cancellation and a bounded transition count',async()=>{
 const g=templateGraph(),events=[],runner=new WorkflowRunner(e=>events.push(e),2);
 const running=runner.run(g);runner.stop();await running;assert.ok(events.some(e=>e.type==='cancelled'));
 const loop=templateGraph();loop.edges.find(e=>e.from===loop.nodes[2].id).to=loop.nodes[1].id;loop.edges.push({id:'escape',from:loop.nodes[2].id,to:loop.nodes[3].id,outcome:'failure'});loop.max_transitions=4;
 assert.deepEqual(validateGraph(loop),[]);await assert.rejects(new WorkflowRunner(()=>{},1).run(loop),/最大流转/);
});
test('playback timeseries maps named radians and rejects incomplete or nonmonotonic frames',()=>{
 const names=[...profile.body_joints].reverse(),row=names.map((name,i)=>i);
 const series={unit:'rad',joint_names:names,frames:[{time_s:0,state:row,action:row},{time_s:1,state:row,action:row}]};
 const valid=PlaybackController.prototype.validSeries(series,profile);assert.equal(valid.frames[0].state[0],28);
 assert.equal(PlaybackController.prototype.validSeries({...series,unit:'deg'},profile),null);
 assert.equal(PlaybackController.prototype.validSeries({...series,frames:[series.frames[0],series.frames[0]]},profile),null);
});


test('legacy video keys normalize to the three UI views without changing signed video URLs',async()=>{
 const videos=[{camera:'observation.images.head',label:'主视角',url:'/api/episodes/video?camera=observation.images.head'},{camera:'observation.images.left_wrist',label:'左腕',url:'/left'},{camera:'observation.images.right_wrist',label:'右腕',url:'/right'}];
 const api=new ConsoleAPI({profile,fetchImpl:async()=>new Response(JSON.stringify({ok:true,episode:{},videos}))});const result=await api.review('real',0);assert.deepEqual(result.videos.map(v=>v.camera),['head','left_wrist','right_wrist']);assert.equal(result.videos[0].url,videos[0].url);
});
test('demo counts remain separate from real collection totals in the legacy adapter',()=>{
 const s=legacySnapshot({totals:{episodes:12,demo_episodes:1075,datasets:2},groups:[],status:{}});assert.equal(s.totals.episodes,12);assert.equal(s.totals.demo_episodes,1075);
});

test('authorized snapshot supplies CSRF to browser writes while unauthorized actions stay disabled',async()=>{
 const requests=[];
 const api=new ConsoleAPI({profile,fetchImpl:async(path,options)=>{
  requests.push({path,options});
  return new Response(JSON.stringify(path.includes('/snapshot')?{ok:true,snapshot:{...live(),access:{authorized:true,csrf_token:'test-session-csrf'}}}:{ok:true}));
 }});
 await api.loadSnapshot();await api.command('robot','apply_pose',{joints:[]});
 assert.equal(requests.at(-1).options.headers['X-Console-CSRF'],'test-session-csrf');
 api.snapshot.access.authorized=false;
 assert.match(api.can('robot','apply_pose'),/授权/);
 await assert.rejects(api.command('robot','apply_pose',{}),/授权/);
});

test('MuJoCo initialization can start without feedback while targets still require ownership and fresh feedback', () => {
  const snapshot=emptySnapshot();Object.assign(snapshot,{source:'live',backend_connected:true,mode:'sim',capabilities:{commands:['robot.initialize','robot.apply_pose']},interlocks:{can_initialize:true,can_apply_pose:true}});
  assert.equal(commandAvailability(snapshot,'robot.initialize'),'');
  assert.match(commandAvailability(snapshot,'robot.apply_pose'),/反馈/);
  snapshot.mode='real';assert.match(commandAvailability(snapshot,'robot.initialize'),/反馈/);
  const normalized=normalizeSnapshot({...snapshot,manual:{state:'running',steps:123,owner:'manual'}});
  assert.equal(normalized.manual.steps,123);assert.equal(normalized.mode,'real');
});
