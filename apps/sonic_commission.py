"""SONIC-specific local onsite approval. This module never creates a motion publisher."""
from __future__ import annotations
import argparse
import hashlib
import json
import os
from pathlib import Path
import stat
import time
import uuid
from console_support import ConsoleError, atomic_json, finite, read_json
from unitree_g1_control import boot_id, digest, machine_fingerprint, sdk_fingerprint

FLAGS = ('hardware_29_unlocked_verified', 'sonic_startup_pose_verified', 'sonic_gains_limits_verified',
         'dex3_hand_configuration_verified', 'normal_stop_verified', 'physical_estop_ready')
FILES = ('target/release/g1_deploy_onnx_ref', 'policy/release/model_decoder.onnx',
         'policy/release/model_encoder.onnx', 'policy/release/observation_config.yaml',
         'planner/target_vel/V2/planner_sonic.onnx')
CACHE = {}


def file_hash(path):
    path = Path(path)
    info = path.stat()
    key = (str(path.resolve()), info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)
    if key not in CACHE:
        hasher = hashlib.sha256()
        with path.open('rb') as handle:
            for chunk in iter(lambda: handle.read(1024 * 1024), b''): hasher.update(chunk)
        CACHE.clear() if len(CACHE) > 50 else None
        CACHE[key] = hasher.hexdigest()
    return CACHE[key]


def runtime_fingerprint(root, app):
    root, app = Path(root), Path(app)
    versions = {name: file_hash(root / 'gear_sonic_deploy' / name) for name in FILES}
    versions['manager'] = file_hash(root / 'gear_sonic/scripts/pico_manager_thread_server.py')
    for name in ('console_sonic.py', 'console_sonic_worker.py', 'sonic_container.py', 'sonic_feedback.py', 'sonic_commission.py'):
        versions[name] = file_hash(app / name)
    return digest(versions)


def template(connection, profile):
    return {'schema_version': 1, 'approved': False, 'scope': 'sonic_real_teleoperation',
            'profile_id': profile['id'], 'model_hash': digest(profile),
            'interface': connection['interface'], 'dds_domain': connection['dds_domain'], 'mode_machine': None,
            **{flag: False for flag in FLAGS},
            'notice': 'SONIC启动会释放原控制模式、进入默认站姿并动作手部；独立SDK关节标定不能替代SONIC专项现场验收。'}


def load_gate(path, root, app, connection, profile):
    path = Path(path)
    try:
        info = path.lstat()
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) & 0o077:
            raise ConsoleError('SONIC现场授权须为本用户拥有的0600普通文件', 412, 'sonic_approval_permissions')
        document = json.loads(path.read_text())
    except (OSError, ValueError):
        raise ConsoleError('尚未完成SONIC真机专项现场验收；仿真可独立使用', 412, 'sonic_onsite_required')
    if document.get('schema_version') != 1 or document.get('scope') != 'sonic_real_teleoperation' or document.get('approved') is not True or any(document.get(flag) is not True for flag in FLAGS):
        raise ConsoleError('SONIC真机启动姿态、手部、增益和停止流程尚未现场确认', 412, 'sonic_onsite_required')
    if document.get('profile_id') != profile['id'] or document.get('model_hash') != digest(profile):
        raise ConsoleError('SONIC现场授权模型版本不匹配', 412, 'sonic_approval_model')
    if document.get('interface') != connection['interface'] or document.get('dds_domain') != connection['dds_domain']:
        raise ConsoleError('网卡或DDS域与SONIC现场授权不一致', 412, 'sonic_approval_connection')
    if type(document.get('mode_machine')) is not int or not 0 <= document['mode_machine'] <= 255:
        raise ConsoleError('缺少现场确认的机器人模式', 412, 'sonic_approval_mode')
    try: uuid.UUID(document.get('lowstate_source_guid', ''))
    except (ValueError, TypeError, AttributeError): raise ConsoleError('现场授权缺少唯一LowState来源', 412, 'sonic_approval_source')
    if document.get('machine_fingerprint') != machine_fingerprint() or document.get('boot_id') != boot_id():
        raise ConsoleError('SONIC现场授权仅适用于原工作站及本次开机', 412, 'sonic_approval_host')
    approved, expires = document.get('approved_at_unix'), document.get('expires_at_unix')
    if not finite(approved) or not finite(expires) or not approved <= time.time() < expires <= approved + 4 * 3600:
        raise ConsoleError('SONIC现场授权已过期（最长4小时）', 412, 'sonic_approval_expired')
    if document.get('sdk_fingerprint') != sdk_fingerprint(root) or document.get('runtime_fingerprint') != runtime_fingerprint(root, app):
        raise ConsoleError('SONIC控制程序、模型或SDK已变化，须重新现场验收', 412, 'sonic_approval_version')
    return document


def main():
    from console_driver import SystemDriver
    from unitree_commission import inspect_hardware
    app = Path(__file__).resolve().parent
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=('template', 'inspect', 'approve', 'revoke'))
    parser.add_argument('--sonic-root', type=Path, default=app.parents[1] / 'sonic_deploy')
    parser.add_argument('--runtime-dir', type=Path, default=app / '.runtime/console')
    args = parser.parse_args()
    os.umask(0o077)
    driver = SystemDriver(args.sonic_root, args.runtime_dir, app)
    connection = driver.config('real')
    profile = read_json(app / 'static/assets/g1/profile.json')
    path = args.runtime_dir / 'sonic-control/commissioning.json'
    if args.action == 'template':
        if path.exists(): raise ConsoleError('授权文件已存在，拒绝覆盖；先核对已有文件')
        atomic_json(path, template(connection, profile)); path.chmod(0o600)
        print('已写入未批准的SONIC专项模板；没有启动控制器。'); return
    if args.action == 'inspect':
        print(json.dumps(inspect_hardware(connection, profile), ensure_ascii=False, indent=2)); return
    document = read_json(path)
    if not document: raise ConsoleError('请先生成并在现场填写SONIC专项模板')
    if args.action == 'revoke':
        document['approved'] = False; atomic_json(path, document); path.chmod(0o600)
        print('已撤销SONIC现场授权；托管会话将请求正常停止。'); return
    if any(document.get(flag) is not True for flag in FLAGS): raise ConsoleError('现场确认项尚未全部完成')
    observation = inspect_hardware(connection, profile)
    if not observation.get('stationary') or not observation.get('unique_lowstate_source') or observation.get('foreign_lowcmd_publishers') != 0 or not observation.get('unitree_motion_service_empty'):
        raise ConsoleError('机器人反馈或唯一控制源预检未通过')
    if input('仅现场验收人员：确认SONIC站姿/手部/增益/停止已核验，输入 SONIC REAL ONSITE VERIFIED：\n').strip() != 'SONIC REAL ONSITE VERIFIED':
        raise ConsoleError('未授权')
    stamp = time.time()
    document.update(approved=True, mode_machine=observation['mode_machine'], lowstate_source_guid=observation['lowstate_source_guid'],
                    approved_at_unix=stamp, expires_at_unix=stamp + 4 * 3600, machine_fingerprint=machine_fingerprint(), boot_id=boot_id(),
                    sdk_fingerprint=sdk_fingerprint(args.sonic_root), runtime_fingerprint=runtime_fingerprint(args.sonic_root, app))
    atomic_json(path, document); path.chmod(0o600)
    load_gate(path, args.sonic_root, app, connection, profile)
    print('已保存本机本次开机最长4小时SONIC专项授权；仍须网页显式确认启动，不自动运动。')


if __name__ == '__main__':
    try: main()
    except (ConsoleError, OSError, ValueError) as exc: raise SystemExit(str(exc))
