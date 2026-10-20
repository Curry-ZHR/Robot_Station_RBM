"""Explicit SDK checks: HG IDL/CRC and isolated lo/Domain232 DDS roundtrip.
Never uses the configured robot interface/domain; no production approval file.
"""
import ast
import json
from pathlib import Path
import struct
import threading
import time
import unittest
from unittest.mock import patch
from console_support import ConsoleError
from unitree_g1_control import Feedback,REFERENCE_KP,REFERENCE_KD,encode_lowcmd
from test_unitree_g1_control import parameters
APP=Path(__file__).resolve().parents[1];SDK=APP.parents[1]/'sonic_deploy/external_dependencies/unitree_sdk2_python'

def python_crc(words):
    crc=0xffffffff
    for word in words:
        for bit in range(31,-1,-1):
            high=bool(crc&0x80000000);crc=(crc<<1)&0xffffffff
            if high:crc^=0x04c11db7
            if word&(1<<bit):crc^=0x04c11db7
    return crc

class SDKChecks(unittest.TestCase):
    def test_reference_gains_match_official_g1_example(self):
        tree=ast.parse((SDK/'example/g1/low_level/g1_low_level_example.py').read_text());values={}
        for node in tree.body:
            if isinstance(node,ast.Assign) and isinstance(node.targets[0],ast.Name) and node.targets[0].id in {'Kp','Kd'}:values[node.targets[0].id]=ast.literal_eval(node.value)
        self.assertEqual(values['Kp'],REFERENCE_KP);self.assertEqual(values['Kd'],REFERENCE_KD)
    def test_actual_hg_idl_crc_matches_independent_wire_layout(self):
        from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
        from unitree_sdk2py.utils.crc import CRC
        from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_
        p=parameters();msg=encode_lowcmd(unitree_hg_msg_dds__LowCmd_,CRC(),[.1]*29,[.01]*29,p['joints'],5)
        values=[0,5]
        for m in msg.motor_cmd:values.extend([m.mode,m.q,m.dq,m.tau,m.kp,m.kd,m.reserve])
        values.extend([0,0,0,0,0]);packed=struct.pack('<2B2x'+'B3x5fI'*35+'5I',*values)
        self.assertEqual(len(packed),1004);self.assertEqual(msg.crc,python_crc(struct.unpack('<250I',packed[:-4])))
        restored=LowCmd_.deserialize(msg.serialize());self.assertEqual(restored.crc,msg.crc);self.assertEqual(len(restored.motor_cmd),35)
        self.assertTrue(all(m.mode==0 for m in restored.motor_cmd[29:]))
    def test_actual_hg_lowstate_crc_and_modes(self):
        from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_
        from unitree_sdk2py.utils.crc import CRC
        p=parameters();msg=unitree_hg_msg_dds__LowState_();msg.mode_machine=5;msg.mode_pr=0;msg.tick=1
        for m in msg.motor_state:m.temperature=[25,25]
        msg.crc=CRC().Crc(msg);feedback=Feedback(p['joints'],5,CRC());self.assertTrue(feedback.accept(msg));self.assertEqual(len(feedback.view(.1)['positions']),29)
        msg.tick=2;msg.crc^=1;self.assertFalse(feedback.accept(msg))
    def test_sdk_dds_loopback_and_foreign_writer_detection(self):
        from unitree_g1_transport import UnitreeTransport
        from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowState_
        from unitree_sdk2py.idl.unitree_hg.msg.dds_ import LowCmd_,LowState_
        from unitree_sdk2py.core.channel import ChannelSubscriber
        from cyclonedds.domain import DomainParticipant
        from cyclonedds.pub import DataWriter
        from cyclonedds.topic import Topic
        class EmptySwitcher:
            def SetTimeout(self,t):pass
            def Init(self):pass
            def CheckMode(self):return 0,{'name':''}
        p=parameters();p['_sdk_root']=str(SDK);stop=threading.Event();transport=None;sub=None;received=[]
        with patch('unitree_sdk2py.comm.motion_switcher.motion_switcher_client.MotionSwitcherClient',EmptySwitcher):
            try:
                transport=UnitreeTransport({'interface':'lo','dds_domain':232},p);self.assertIsNone(transport.publisher)
                participant=DomainParticipant(232);state_writer=DataWriter(participant,Topic(participant,'rt/lowstate',LowState_))
                msg=unitree_hg_msg_dds__LowState_();msg.mode_machine=5;msg.mode_pr=0
                for motor in msg.motor_state:motor.temperature=[25,25]
                def send():
                    while not stop.wait(.005):msg.tick+=1;msg.crc=transport.crc.Crc(msg);state_writer.write(msg)
                thread=threading.Thread(target=send,daemon=True);thread.start();deadline=time.monotonic()+6
                while time.monotonic()<deadline:
                    try:data=transport.observe(p);break
                    except ConsoleError:time.sleep(.02)
                else:self.fail('SDK loopback LowState/discovery not ready')
                self.assertEqual(len(data['positions']),29);self.assertEqual(data['foreign_publishers'],0)
                p['lowstate_source_guid']=data['source_guid'];transport.observe(p)
                with self.assertRaises(ConsoleError):transport.observe({**p,'lowstate_source_guid':'different'})
                sub=ChannelSubscriber('rt/lowcmd',LowCmd_);sub.Init(received.append,1)
                transport.arm();command=encode_lowcmd(transport.factory,transport.crc,[.1]*29,[0.]*29,p['joints'],5)
                for _ in range(20):
                    transport.write(command)
                    if received:break
                    time.sleep(.03)
                self.assertTrue(received);self.assertEqual(received[-1].crc,transport.crc.Crc(received[-1]))
                foreign=DataWriter(participant,Topic(participant,'rt/lowcmd',LowCmd_));deadline=time.monotonic()+3
                while time.monotonic()<deadline:
                    try:transport.observe(p)
                    except ConsoleError as exc:
                        if exc.code=='foreign_publisher':break
                    time.sleep(.02)
                else:self.fail('foreign LowCmd writer not detected')
                transport.disarm();self.assertIsNone(transport.publisher)
            finally:
                stop.set()
                if 'thread' in locals():thread.join(timeout=1)
                if sub:sub.Close()
                if transport:transport.close()

if __name__=='__main__':unittest.main()
