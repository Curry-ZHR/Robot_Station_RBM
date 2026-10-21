import test from 'node:test';
import assert from 'node:assert/strict';
import {ViewerMetrics} from '../static/console-viewer-metrics.js';
const sample=(seconds,source='sim')=>({valid:true,source,observedAt:new Date(seconds*1000).toISOString()});
test('draw FPS is measured independently from slowly arriving, unchanged joint samples',()=>{
 const meter=new ViewerMetrics();
 for(let i=0;i<=120;i++)meter.rendered(i*1000/30);
 for(let i=0;i<=4;i++){meter.pose(sample(Math.floor(i/2)*2),i*1000);}
 const rates=meter.read(4000);
 assert.ok(Math.abs(rates.fps-30)<.01);
 assert.equal(rates.poseHz,.5);
});
test('duplicate source timestamps and stalled streams do not invent fresh pose updates',()=>{
 const meter=new ViewerMetrics();meter.pose(sample(0),0);meter.pose(sample(2),2000);
 for(let t=3000;t<=7000;t+=1000)meter.pose(sample(2),t);
 assert.equal(meter.read(4000).poseHz,.5);
 assert.equal(meter.read(7100).poseHz,0);
 meter.pose({valid:false},7200);assert.equal(meter.read(7200).poseHz,null);
});
test('mode/source switches, clock resets and visibility resets discard old rate history',()=>{
 const meter=new ViewerMetrics();meter.pose(sample(10),0);meter.pose(sample(12),2000);
 meter.pose(sample(14,'real'),2100);assert.equal(meter.read(2100).poseHz,null);
 meter.pose(sample(16,'real'),4100);assert.equal(meter.read(4100).poseHz,.5);
 meter.pose(sample(0,'real'),4200);assert.equal(meter.read(4200).poseHz,null);
 meter.rendered(4200);meter.rendered(4233);meter.reset();
 assert.equal(meter.read(4300).fps,0);assert.equal(meter.read(4300).poseHz,null);
});
