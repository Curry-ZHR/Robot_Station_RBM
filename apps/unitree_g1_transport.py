"""Pinned Unitree SDK transport. Publisher is created only by explicit arm()."""
from __future__ import annotations
import threading
import time
from console_support import ConsoleError
from unitree_g1_control import Feedback

class UnitreeTransport:
    def __init__(self,connection,commissioning):
        from unitree_sdk2py.core.channel import ChannelFactoryInitialize,ChannelFactory,ChannelSubscriber
        from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowState_,LowCmd_
        from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
        from unitree_sdk2py.utils.crc import CRC
        from unitree_sdk2py.comm.motion_switcher.motion_switcher_client import MotionSwitcherClient
        from cyclonedds.builtin import BuiltinDataReader,BuiltinTopicDcpsPublication
        if commissioning.get('_sdk_root'):
            from pathlib import Path
            import unitree_sdk2py.core.channel as sdk_channel
            expected=Path(commissioning['_sdk_root'])/'unitree_sdk2py/core/channel.py'
            if Path(sdk_channel.__file__).resolve()!=expected.resolve():raise ConsoleError('实际导入的SDK路径与核验源不一致',412,'sdk_incompatible')
        ChannelFactoryInitialize(connection['dds_domain'],connection['interface'])
        # This SDK revision exposes no public participant accessor. This single
        # compatibility bridge is covered by source fingerprints and SDK wire tests.
        participant=getattr(ChannelFactory(),'_ChannelFactory__participant',None)
        if participant is None:raise ConsoleError('SDK participant接口不兼容',412,'sdk_incompatible')
        self.participant=participant;self.own_guid=str(participant.guid);self.graph_reader=BuiltinDataReader(participant,BuiltinTopicDcpsPublication)
        self.crc=CRC();self.factory=unitree_hg_msg_dds__LowCmd_;self.publisher=None;self.LowCmd=LowCmd_
        self.lock=threading.RLock();self.feedback=Feedback(commissioning['joints'],commissioning['mode_machine'],self.crc)
        self.subscriber=ChannelSubscriber('rt/lowstate',LowState_);self.subscriber.Init(self._receive,1)
        self.switcher=MotionSwitcherClient();self.switcher.SetTimeout(.3);self.switcher.Init()
        self.mode_at=-float('inf');self.mode_ok=False;self.mode_name=None;self.graph_at=-float('inf');self.graph_error=None;self.endpoints={};self.stopped=threading.Event();self.started=time.monotonic()
        self.monitor=threading.Thread(target=self._monitor,daemon=True);self.monitor.start()
    def _receive(self,msg):
        with self.lock:self.feedback.accept(msg)
    def _monitor(self):
        next_mode=0
        while not self.stopped.is_set():
            stamp=time.monotonic()
            try:
                for endpoint in self.graph_reader.take(100):
                    with self.lock:
                        if endpoint.sample_info.valid_data:self.endpoints[str(endpoint.key)]={'participant':str(endpoint.participant_key),'topic':endpoint.topic_name,'type':endpoint.type_name.replace('::','.')}
                        else:self.endpoints.pop(str(endpoint.key),None)
                with self.lock:self.graph_at=time.monotonic();self.graph_error=None
            except Exception:
                with self.lock:self.graph_error='DDS发布者发现失败'
            if stamp>=next_mode:
                try:
                    code,row=self.switcher.CheckMode()
                    with self.lock:
                        self.mode_ok=code==0 and isinstance(row,dict) and isinstance(row.get('name'),str)
                        self.mode_name=row.get('name') if self.mode_ok else None;self.mode_at=time.monotonic()
                except Exception:
                    with self.lock:self.mode_ok=False;self.mode_at=time.monotonic()
                next_mode=time.monotonic()+.2
            self.stopped.wait(.03)
    def observe(self,commissioning):
        stamp=time.monotonic()
        with self.lock:
            data=self.feedback.view(commissioning['feedback_timeout_seconds'])
            if self.feedback.reason:raise ConsoleError(self.feedback.reason,412,'feedback_invalid')
            if not self.mode_ok or stamp-self.mode_at>.8:raise ConsoleError('无法确认Unitree运动服务状态',412,'motion_switcher_unavailable')
            if self.mode_name:raise ConsoleError('Unitree运动服务仍在占用；请现场退出后再接管',409,'controller_conflict')
            if self.graph_error or stamp-self.graph_at>.8 or stamp-self.started<1.:raise ConsoleError('DDS控制源发现尚未完成',412,'discovery_pending')
            writers=[v for v in self.endpoints.values() if v['topic']=='rt/lowcmd' and v['participant']!=self.own_guid]
            states=[v for v in self.endpoints.values() if v['topic']=='rt/lowstate']
            if writers:raise ConsoleError('发现其他rt/lowcmd发布者，禁止争抢控制',409,'foreign_publisher')
            if len(states)!=1 or states[0]['type']!='unitree_hg.msg.dds_.LowState_':raise ConsoleError('需要唯一HG LowState来源，禁止多机混流',412,'state_source_conflict')
            source_guid=next(k for k,v in self.endpoints.items() if v is states[0])
            if commissioning.get('lowstate_source_guid') and commissioning['lowstate_source_guid']!=source_guid:raise ConsoleError('LowState来源与现场标定不一致，禁止接管其他机器人',412,'state_source_changed')
            return {**data,'feedback_age_seconds':stamp-self.feedback.at,'source_guid':source_guid,'foreign_publishers':len(writers)}
    def arm(self):
        if self.publisher is None:
            from unitree_sdk2py.core.channel import ChannelPublisher
            self.publisher=ChannelPublisher('rt/lowcmd',self.LowCmd);self.publisher.Init()
    def write(self,msg):
        if self.publisher is None or self.publisher.Write(msg)is not True:raise ConsoleError('LowCmd发送失败，已停止输出',503,'command_write_failed')
    def disarm(self):
        if self.publisher is not None:self.publisher.Close();self.publisher=None
    def close(self):
        self.disarm();self.stopped.set();self.monitor.join(timeout=1);self.subscriber.Close()
