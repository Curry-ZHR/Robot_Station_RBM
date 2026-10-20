"""Test-only real worker harness: actual SDK IDL/CRC, memory transport, NO DDS."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from unittest.mock import patch
import copy
from console_real_worker import main
from console_support import read_json
from unitree_g1_control import control_fingerprint
from unitree_sdk2py.idl.default import unitree_hg_msg_dds__LowCmd_
from unitree_sdk2py.utils.crc import CRC
class MemoryTransport:
    def __init__(self,connection,config):
        assert connection['interface']=='lo' and connection['dds_domain']==231
        self.factory=unitree_hg_msg_dds__LowCmd_;self.crc=CRC();self.publisher=None
        self.data={'positions':[0.]*29,'velocities':[0.]*29,'torques':[0.]*29,'temperatures':[25.]*29,'rpy':[0.]*3,'feedback_age_seconds':0.,'source_guid':'memory-no-dds','foreign_publishers':0}
    def observe(self,config):return copy.deepcopy(self.data)
    def arm(self):self.publisher=True
    def write(self,msg):
        assert msg.crc==self.crc.Crc(msg)
        self.data['positions']=[m.q for m in msg.motor_cmd[:29]];self.data['velocities']=[m.dq for m in msg.motor_cmd[:29]]
    def disarm(self):self.publisher=None
    def close(self):self.disarm()
folder=Path(sys.argv[sys.argv.index('--directory')+1]);config=read_json(folder/'test-parameters.json');config.update(control_fingerprint=control_fingerprint(),file_fingerprint='test-only')
with patch('console_real_worker.load_commissioning',return_value=config),patch('unitree_g1_transport.UnitreeTransport',MemoryTransport):main()
