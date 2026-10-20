"""Named pose storage and bounded minimum-jerk trajectories; no device IO."""
from __future__ import annotations
import hashlib
import json
from pathlib import Path
import uuid
import threading

from console_support import ConsoleError, atomic_json, finite, now, read_json


def joint_targets(profile, rows):
    if not isinstance(rows,list) or len(rows)!=len(profile['body_joints']):raise ConsoleError('需要完整的 29 个具名关节')
    names=profile['body_joints'];specs={j['name']:j for j in profile['joints']}
    values={}
    for row in rows:
        if not isinstance(row,dict) or set(row)!={'name','position_rad'}:raise ConsoleError('关节目标字段应为 name/position_rad')
        name=row['name'];value=row['position_rad']
        if not isinstance(name,str) or name not in names or name in values or not finite(value):raise ConsoleError('关节名称重复、缺失或数值无效')
        if not specs[name]['lower']<=value<=specs[name]['upper']:raise ConsoleError('关节目标超出模型范围：'+name)
        values[name]=float(value)
    return [{'name':name,'position_rad':values[name]} for name in names]


def trajectory(profile, start, target, duration=3., velocity=.5):
    start=joint_targets(profile,start);target=joint_targets(profile,target)
    if not finite(duration) or not .25<=duration<=60 or not finite(velocity) or not .05<=velocity<=1:
        raise ConsoleError('过渡时长或速度上限无效')
    delta=max(abs(a['position_rad']-b['position_rad']) for a,b in zip(start,target))
    actual=max(float(duration),1.875*delta/velocity)
    if actual>60:raise ConsoleError('目标过渡超过 60 秒，请分步应用')
    frames=[]
    for index in range(121):
        u=index/120;s=u*u*u*(10+u*(-15+6*u))
        frames.append({'time_s':actual*u,'positions_rad':[a['position_rad']+s*(b['position_rad']-a['position_rad']) for a,b in zip(start,target)]})
    return {'joint_names':profile['body_joints'],'duration_seconds':actual,'velocity_limit_rad_s':velocity,'frames':frames,'unit':'rad'}


class PoseStore:
    def __init__(self,directory,profile):
        self.directory=Path(directory)/'poses';self.directory.mkdir(parents=True,exist_ok=True)
        self.profile=profile;self.lock=threading.RLock()
        self.model_hash=hashlib.sha256(json.dumps(profile,sort_keys=True).encode()).hexdigest()

    def list(self):
        poses=[read_json(p) for p in self.directory.glob('*.json')]
        return {'ok':True,'poses':sorted([p for p in poses if not p.get('archived')],key=lambda p:p.get('updated_at',''),reverse=True),'model_hash':self.model_hash}

    def save(self,payload):
        with self.lock:return self._save(payload)

    def _save(self,payload):
        action=payload.get('action','save')
        ident=payload.get('id') or uuid.uuid4().hex
        if not isinstance(ident,str) or len(ident)!=32 or not ident.isalnum():raise ConsoleError('姿态标识无效')
        path=self.directory/(ident+'.json');old=read_json(path)
        if old and payload.get('expected_revision')!=old['revision']:raise ConsoleError('姿态已变化，请刷新',409,'pose_conflict')
        if action=='archive':
            if not old:raise ConsoleError('姿态不存在',404)
            old.update(archived=True,revision=old['revision']+1,updated_at=now());atomic_json(path,old)
            return self.list()
        if action!='save':raise ConsoleError('未知姿态操作')
        name=payload.get('name','')
        if not isinstance(name,str) or not 1<=len(name.strip())<=80:raise ConsoleError('请输入 1～80 个字符的姿态名称')
        if payload.get('profile_id',self.profile['id'])!=self.profile['id'] or payload.get('unit','rad')!='rad':raise ConsoleError('姿态机型或单位不兼容')
        if payload.get('model_hash',self.model_hash)!=self.model_hash:raise ConsoleError('姿态模型版本不一致')
        row={'id':ident,'name':name.strip(),'profile_id':self.profile['id'],'model_hash':self.model_hash,'unit':'rad',
             'joints':joint_targets(self.profile,payload.get('joints')),'created_at':old.get('created_at',now()),'updated_at':now(),
             'revision':old.get('revision',0)+1,'archived':False}
        atomic_json(path,row)
        return {**self.list(),'pose':row,'message':'初始姿态已保存；尚未应用到任何设备'}
