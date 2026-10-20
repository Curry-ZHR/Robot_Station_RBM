# G1 工作台运行与接入说明（2026-10-19）

部署目录：`/home/harry/workspace/robot_station`。入口：[工作台](http://192.168.123.100:9999/)。本地 SSH 转发仍可使用 `http://127.0.0.1:12947/`。

## 日常启动与关闭

在 4070 项目根目录运行：

```sh
./run.sh
./stop.sh
```

`run.sh` 默认启动 systemd 用户服务并等待网页健康检查，重复运行不会建立第二份服务；`stop.sh` 有序关闭本工作台拥有的网页、采集、MuJoCo、DDS/PICO/ZMQ 只读订阅和 ROS 图像桥接。采集中关闭会保留有效缓冲帧并标记当前片段舍弃；转换任务通过取消标记保留源数据和未完成输出。不接管或停止外部 PC Service、Docker/SONIC 运动控制器，不使用全局进程清理。

服务为 `robot-station.service`，已设置 enabled 与 `Linger=yes`，无需用户登录即可随系统启动。`Restart=on-failure` 恢复主管进程，主管进程单独恢复网页进程。开机仅提供网页和只读接入，不自动初始化仿真、不取得控制权、不启动真机运动、采集或推理。现场网卡暂未就绪时网页仍可启动；监听 `0.0.0.0:9999`，允许的公开 Host 为 `192.168.123.100`，LAN 操作仍需原有授权和同源 CSRF。

```sh
./run.sh status
./run.sh logs
./run.sh restart
./run.sh disable-autostart
```

`stop.sh` 不取消下次开机自启；`disable-autostart` 不停止当前服务。恢复自启可再次运行 `./run.sh`。用户服务定义位于 `~/.config/systemd/user/robot-station.service`，重新安装用 `bash scripts/install_station_service.sh`。网页日志位于 `apps/.runtime/station-processes/web.log`；托管子进程在 `apps/.runtime/console/processes/*.log`，主管每 20 秒检查日志，超过 8 MiB 滚动，保留 4 份历史。不要同时直接运行 `apps/run.sh` 建立另一份网页。

旧根目录 ROS 启动器完整保留为 `run_legacy_ros.sh`，同目录位置保持其相对路径可用；只有明确需要旧 ROS/Piper/底盘流程时才运行。`./run.sh apps start|stop|restart|status|logs` 和 `scripts/apps.sh` 为新入口兼容别名。历史启动器仍包含原先的清理逻辑，不用于 G1 工作台日常开关。

## SONIC容器与XRoboToolkit启停

“整机管理→运行服务”的两项停止已接入：停止本项目待命容器，或同时停止本项目PC Service与Unity 3D。采集、手动控制、准备任务或SONIC/遥操作控制仍在运行时拒绝停止；按钮悬停显示原因。停止与重新启动均已在4070实际验收，保留模型与采集文件。当前已恢复原待命容器、PC Service和Unity，未启动机器人运动。

XR停止标记阻止隐式SDK准备自动重启，点击启动只恢复后台PC Service；Unity仍可从桌面入口单独开启。旧部署先安装仓库随附的XR生命周期扩展。具体命令、依赖和接口见 [service_lifecycle.md](service_lifecycle.md)。根stop.sh保持既有工作台/托管任务关闭职责；基础服务管理不等于机器人硬件急停。

## 连接配置与诊断

侧栏“连接与诊断”可编辑当前 real/sim 模式的网卡、Unitree DDS Domain、SONIC 状态/姿态地址、ZMQ 图像地址、ROS Domain、三路 topic/type/QoS/depth、图像尺寸/帧率/质量和时间阈值，提供校验、保存、配置方案、导入/导出和修改前备份恢复。

ROS 图像默认 Domain **99**，Unitree DDS 默认 **0**。不要把两个通信域混用。默认话题 `/camera/{head,left_wrist,right_wrist}/image_raw` 是待现场确认的配置，不是已经发现的相机。PICO 标定确认只能在现场实际完成后勾选。

保存、加载方案和恢复备份均需最新 `config_revision`，采集、准备和手动控制占用期间拒绝修改。实际修改先备份旧配置，再停止旧读流；点击“按已保存配置重新接入”启动所选模式的只读进程。修改配置不会恢复任何运动控制权。只读接入的所选模式持久化，主管恢复同一模式（首次默认 real）；相机服务手动停止后不会被主管自动拉起，显式启动或重新接入才恢复。

诊断检查 ROS 发布者、实际类型和 offered QoS，与订阅配置比对；可靠订阅对 best_effort 发布者报不兼容。显示帧率、源帧龄、三路时间差、接受/拒绝计数和最近桥接异常，以及网卡 carrier、G1/BMS 新鲜度。诊断 ZIP 仅含明确列出的配置/状态/版本，不含操作密钥、会话、租约、环境变量、原始日志和数据集内容。

## 独立手动控制和姿态库

在“仿真环境 → 全身控制”操作：

1. 点击“初始化 MuJoCo”，等待 29 / 29 有效反馈。
2. 点击“手动接管”。默认滑条仍仅预览；勾选“滑条实时联动物理仿真”后，拖动滑条或输入角度会向仿真发送目标。
3. 通过“保存当前目标”保存完整具名初始姿态。支持加载到滑条、平滑过渡预览、JSON 导入/导出和归档。保存或加载不等于下发。
4. 也可单次点击“下发目标姿态”并核对目标。反馈区分过渡中、跟踪中、已到位和保持姿态；到位为过渡完成且最大误差小于 0.03 rad。
5. 点击“释放控制权”或顶部“停止调试”结束操作。

物理模型直接加载 SONIC 的 `gear_sonic_deploy/g1/g1_29dof.xml` 及 meshes，固定 floating base，具名映射 29 个关节/电机，运行 MuJoCo 惯性、重力、接触与有界 PD 步进。采用 implicitfast、0.002s 步长、仿真阻尼 8、身体/腕部扭矩上限分别 40/10 Nm。这些是离线仿真参数，不是已验证的真机控制增益。浏览器 URDF 显示目标或实际物理反馈；不制造仿真 BMS 电量。固定基座结果不代表能站立、平衡或在真机安全执行。

目标要求完整、唯一具名 29 维、rad 和模型限位；姿态文件还验证 profile、model_hash、版本冲突。轨迹使用五次 minimum-jerk，按最大关节变化自动延长过渡以满足速度上限（默认 0.5 rad/s，可设 0.05～1）。UI 最新目标优先、最多 10 Hz 且只允许一个请求在途；后端序号严格递增。

每次接管返回私有 `lease_token`，浏览器约 0.9 秒心跳，3 秒未续租即释放。物理进程独立检查租约，过期后保持当前位置；Web 重启也撤销旧租约，不能自动恢复手动控制。采集、准备和手动控制互斥；已观察到 SONIC 控制器在线时拒绝接管。

**独立真机SDK适配软件已完成，当前仍受现场标定门槛限制，未执行真机运动。** 先现场确认硬件29维配置、支撑/控制器互斥、真实反馈、增益/限幅与停止方式，详见 [SDK适配说明](g1_sdk_adapter.md)。不能只改网页开关或伪造标定解除门槛。手动姿态自动交给SONIC已按用户要求暂缓；任务模型、后台状态机及第⑤项采集质量评分按原规划后置。

## 后端接口补充

完整机器可读规范：`apps/contracts/console-v1.openapi.json`，版本 **1.6.0**，34 paths / 43 schemas；生成源为 `apps/contracts/build_contract.py`。

| 接口 | 用途与约束 |
| --- | --- |
| `GET /api/v1/console/configuration` | 完整 real/sim 配置、config_revision、方案及备份索引 |
| `POST /api/v1/console/configuration` | action=validate/save/save_profile/load_profile/restore；写入需 expected_revision=config_revision |
| `GET /api/v1/console/diagnostics?mode=real` | 有界 ROS 图与设备诊断；独立 ROS context/domain，授权访问 |
| `GET /api/v1/console/diagnostics/download?mode=real` | 下载脱敏 ZIP；授权访问 |
| `GET /api/v1/console/poses` | 返回姿态库与 model_hash |
| `POST /api/v1/console/poses` | save：name/joints/profile_id/unit/model_hash；archive：id/expected_revision；覆盖需当前姿态版本 |
| `POST /api/v1/console/poses/preview` | joints、可选完整 start、mode、transition_seconds、velocity_limit_rad_s → 121 个平滑轨迹采样；无设备 IO |
| `POST /api/v1/console/robot/commands` | 原有命令信封；sim initialize/claim(owner=manual)/release/apply_pose 已接入；real 运动拒绝 |
| `POST /api/v1/console/robot/manual` | 低延迟 heartbeat/apply_pose 通道，mode/lease_token；目标再带 sequence/joints/unit/transition_seconds/velocity_limit_rad_s |

机器人普通命令信封继续使用 action、mode、profile_id、expected_revision 和 payload，附唯一 `Idempotency-Key`；claim 的返回结果含 lease_token。高频 manual 通道不使用全局快照版本，使用私有租约加严格递增 sequence。浏览器写入仍需 `X-Console-CSRF`，取自已授权 snapshot.access；LAN 操作会话通过原有 `/session` 获得。不得把操作密钥或租约写入前端配置、日志、诊断包。

配置保存在 `apps/.runtime/console/runtime-config.json`，方案/备份在 `configuration/{profiles,backups}`，姿态在 `poses`；这些持久目录不会因正常启动/关闭或 Web 恢复被清空。
