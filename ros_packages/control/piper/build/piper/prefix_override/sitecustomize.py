import sys
if sys.prefix == '/usr':
    sys.real_prefix = sys.prefix
    sys.prefix = sys.exec_prefix = '/home/zhuzl/workspace/robot_station/ros_packages/control/piper/install/piper'
