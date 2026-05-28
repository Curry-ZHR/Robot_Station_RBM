#!/usr/bin/env python3

import subprocess
import sys
import shutil
from pathlib import Path
import re
import os

START_SH = "start_orbbec_camera.sh"


def run_command(command):
    """运行命令并返回输出"""
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.stderr
    except Exception as e:
        print(f"执行命令时出错: {str(e)}")
        return None


def get_device_info():
    """获取设备信息"""
    # 运行 rs-enumerate-devices 命令
    rs_output = run_command("ros2 run orbbec_camera list_devices_node")
    if not rs_output:
        print("无法获取到深度摄像头数据")
        return None
    # 解析输出获取序列号
    count = rs_output.count("usb port:")
    if count > 1:
        print("检测到多个 Orbbec 设备，请只保留一个（拔掉其他设备）后重试。")
        return None
    if count == 0:
        print("未检测到 Orbbec 设备，请插入指定相机后重试。")
        return None
    serial = rs_output.split("serial: ")[1].split()[0]
    print("serial: ", serial)
    return serial


def prompt_one(role: str) -> str:
    while True:
        input(f"请仅插入【{role}】相机，准备好后按回车继续...")
        serial = get_device_info()
        if serial is None:
            continue
        else:
            return serial


def update_start_sh(front: str, left: str, right: str) -> None:
    # Overwrite start script with minimal, directly runnable content
    content = f"""#!/usr/bin/env bash
exec ros2 launch orbbec_camera multi_camera.launch.py \\
  front_serial:=\"{front}\" \\
  left_serial:=\"{left}\" \\
  right_serial:=\"{right}\"
"""
    with open(START_SH, "w") as f:
        f.write(content)


def main() -> int:
    print("将按照顺序采集序列号：前（front）→ 左（left）→ 右（right）。")
    print("每一步请仅连接指定的相机，其余请拔出，然后按回车继续。")

    front = prompt_one("前/front")
    left = prompt_one("左/left")
    right = prompt_one("右/right")

    update_start_sh(front, left, right)
    print("完成。可运行start_orbbec_camera.sh启动摄像头")
    return 0


if __name__ == "__main__":
    sys.exit(main())


