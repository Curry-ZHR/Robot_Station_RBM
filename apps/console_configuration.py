"""Validated connection profiles and recoverable configuration history."""
from __future__ import annotations
import copy
import hashlib
import json
from pathlib import Path
import threading
import uuid

from console_driver import default_config
from console_support import ConsoleError, atomic_json, now, read_json


class ConfigurationStore:
    def __init__(self, driver):
        self.driver=driver
        self.directory=driver.directory/'configuration'
        self.directory.mkdir(parents=True,exist_ok=True)
        self.lock=threading.RLock()

    def document(self):
        return {mode:self.driver.config(mode) for mode in ('sim','real')}

    @staticmethod
    def revision(document):
        return hashlib.sha256(json.dumps(document,sort_keys=True,ensure_ascii=False).encode()).hexdigest()

    def validate(self, document):
        if not isinstance(document,dict) or set(document)!={'sim','real'}:
            raise ConsoleError('连接配置必须包含 sim 和 real')
        for mode,row in document.items():
            if not isinstance(row,dict) or set(row)-set(default_config(mode)):
                raise ConsoleError('连接配置含未支持的字段')
        return {mode:self.driver.config(mode,document=document) for mode in ('sim','real')}

    def view(self):
        doc=self.document()
        def entries(kind):
            rows=[]
            for p in (self.directory/kind).glob('*.json'):
                row=read_json(p)
                rows.append({k:row.get(k) for k in ('id','name','created_at')})
            return sorted(rows,key=lambda r:r.get('created_at') or '',reverse=True)[:50]
        return {'ok':True,'document':doc,'config_revision':self.revision(doc),
                'profiles':entries('profiles'),'backups':entries('backups')}

    def write(self, payload, busy=False):
        with self.lock:
            action=payload.get('action','save')
            if action=='validate':
                return {'ok':True,'document':self.validate(payload.get('document')),'message':'配置校验通过'}
            if busy:raise ConsoleError('采集、手动控制或准备任务活动时不能更改连接配置',409,'task_conflict')
            current=self.document()
            if payload.get('expected_revision')!=self.revision(current):
                raise ConsoleError('连接配置已变化，请刷新后重试',409,'config_conflict')
            if action in {'load_profile','restore'}:
                ident=payload.get('id')
                if not isinstance(ident,str) or not ident.isalnum() or len(ident)!=32:raise ConsoleError('配置条目不存在',404)
                row=read_json(self.directory/('profiles' if action=='load_profile' else 'backups')/(ident+'.json'))
                if not row:raise ConsoleError('配置条目不存在',404)
                document=row['document']
            else:document=payload.get('document')
            doc=self.validate(document)
            if action=='save_profile':
                name=payload.get('name','')
                if not isinstance(name,str) or not 1<=len(name.strip())<=80:raise ConsoleError('配置名称应为 1～80 个字符')
                ident=uuid.uuid4().hex
                atomic_json(self.directory/'profiles'/(ident+'.json'),{'id':ident,'name':name.strip(),'created_at':now(),'document':doc})
                return {**self.view(),'message':'连接配置方案已保存'}
            if action not in {'save','load_profile','restore'}:raise ConsoleError('未知配置操作')
            ident=uuid.uuid4().hex
            atomic_json(self.directory/'backups'/(ident+'.json'),{'id':ident,'name':'配置修改前备份','created_at':now(),'document':current})
            atomic_json(self.driver.config_path,doc)
            return {**self.view(),'requires_reconnect':True,'message':'连接配置已保存，可点击重新接入应用；修改前配置已备份'}
