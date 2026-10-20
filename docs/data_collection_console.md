# Robot Station 统一工作台与后端接入

更新：2026-10-19，Asia/Shanghai。当前开发范围为用户确认的 ①状态/自检、②SONIC 软件启动管理、③数据回放、④采集任务管理。任务模型推理与状态机后台执行按用户要求留到真机采集之后。

## 接续入口与运行

- 项目交接：[HANDOFF.md](../HANDOFF.md)，以最上方最新阶段为准。
- [OpenAPI 3.1 接口规范](../apps/contracts/console-v1.openapi.json)，当前版本 1.3.0，27 个路径、34 个数据结构；[生成器](../apps/contracts/build_contract.py)。各命令的 `x-implementation` 明确已实现和保留部分。
- 4070 主目录 `/home/harry/workspace/robot_station`；SONIC 在同级 `/home/harry/workspace/sonic_deploy`。
- 固定网页入口 `http://192.168.123.100:9999/`；Mac 当前转发入口 `http://127.0.0.1:12947/`。
- 仅管理网页：在 Robot Station 根目录使用 `./run.sh apps start`、`status`、`stop`、`restart`、`logs`。根目录不带参数的 `./run.sh` 是旧 ROS 启动器，包含其他硬件/构建逻辑。
- 网络静态配置和 NO-CARRIER 的历史说明见交接 0A；现场须确认 .100 无冲突、有线链路接通及浏览器路由。

网页仍有九页：两层推理、自检与启动、整机管理、全身控制、三相机传感器、采集、回放、转换、状态机。实际 G1 URDF / 50 个 STL 与 29 身体关节可视化沿用现有资源；源模型包含手部共 43 维。可视化顺序不是 DDS 电机索引。

`?preview=1` 仍为隔离的浏览器预演。预演视频、电量、姿态与任务结果均为合成，不调用设备接口或写正式目录。正常入口读取本轮实现的 v1 后端；缺少硬件时电量、关节和相机保持未知/离线。

## ① 状态、自检和只读设备接入

`GET /api/v1/console/snapshot?mode=sim&profile_id=unitree-g1-29` 返回统一快照。`POST /self-check` 执行真实环境检查，包括磁盘、GPU、Docker 镜像/容器归属、模型、构建产物、遥操作 SDK 和独立采集环境。采集环境以实际导入官方导出器成功为准，不按目录存在判断。

只读订阅由 `robot.connect` 或 SONIC 准备任务启动：

- G1：Unitree HG `rt/lowstate`，按 SDK 示例的显式电机名称映射 29 关节；只订阅，没有 LowCmd/控制发布器。真机网卡等待链路在线后连接，仿真使用 `lo`。
- 电池：HG `BmsState_` 的 `soc`，默认订阅 `rt/bmsstate` 与 `rt/lf/bmsstate`。实际发布主题和固件须现场确认；无真实 BMS 数据时保持未知。机器人 TTL 5 秒、电池 TTL 15 秒。
- SONIC：订阅 `g1_debug` 与 `robot_config`，以持续变化的控制序号判断控制器反馈；仿真状态使用模型给出的具名身体关节映射。
- PICO：通过本机 SDK 读取 `get_body_timestamp_ns()`，要求身体数据可用、24×7 姿态有效及连续新帧。头显通用时间戳不能替代身体追踪时间戳。PICO 数据 TTL 2 秒；人体/腿部标定由现场确认配置控制。
- 相机：读取 SONIC ComposedCamera 的 msgpack/JPEG ZMQ 协议，输出同源 MJPEG 和 JPEG；只以新的源帧时间戳刷新状态，重复帧/过期时钟不能维持在线。相机 TTL 5 秒，HTTP 预览连接有上限，前端读取失败后有间隔重试。

`GET /cameras/{head|left_wrist|right_wrist}/stream?mode=...` 和 `/frame?mode=...` 提供浏览器画面。相机接入按钮启动只读接收器；实际相机发布服务的硬件类型、设备 ID 与运行位置须现场核实，本轮未猜测或启动未知相机驱动。

### ROS 2 三相机接入（2026-10-19，已实现）

正式运行配置 `apps/.runtime/console/runtime-config.json` 的 real/sim 均为 `camera_source:"ros2"`、`ros2_camera.domain_id:99`；G1 的 `dds_domain` 默认仍为 0。完整模板见 [console-runtime.example.json](../apps/console-runtime.example.json)。ROS 2 在独立进程/context 中运行，不要求 SONIC 控制器、机器人或 PICO 在线。

默认话题仅为可修改的接线模板，尚未发现真实相机：

| 视角 | ROS 2 话题 | 默认消息 |
| --- | --- | --- |
| head | `/camera/head/image_raw` | `sensor_msgs/msg/Image` |
| left_wrist | `/camera/left_wrist/image_raw` | `sensor_msgs/msg/Image` |
| right_wrist | `/camera/right_wrist/image_raw` | `sensor_msgs/msg/Image` |

逐路配置 `topics.<视角>.topic/message_type/reliability/depth`。消息支持 Image/CompressedImage，reliability 支持 best_effort/reliable，durability 为 volatile；默认 best_effort、depth 5。接压缩话题时同时改 topic 和 message_type。配置必须与发布端匹配；Domain 99 本身不打通 VLAN/子网，仍需正确路由和 DDS 发现。默认 RMW 为 rmw_fastrtps_cpp，可改为已安装的 rmw_cyclonedds_cpp；ROS 版本/网卡/发现与源时钟须现场核对。

安装与启动入口（Robot Station 根目录）：

```sh
bash scripts/install_ros2_camera.sh
bash scripts/run_ros2_camera_bridge.sh --config apps/.runtime/console/camera-bridge/config.json --directory apps/.runtime/console/camera-bridge
```

常规使用网页“整机管理 → 相机接入 → 启动/停止”，由托管器生成上述桥接 config，避免重复手动启动占用端口；“只读连接”和完整准备也会按配置准备来源。传感器页显示 Domain/话题/桥接状态，日志在 `apps/.runtime/console/processes/camera-bridge.log`，逐路计数/错误在 `apps/.runtime/console/camera-bridge/status.json`。相机单项启动不会启动 Docker、PC Service 或 SONIC 运动控制。采集任务活动时相机启停返回 409。配置修改后结束采集，再重新启动相机来源即可；共享桥接由 sim/real 复用，不允许双进程争用端口。

桥接默认绑定 `tcp://127.0.0.1:5555`，只供本机网页接收器和录制器使用；ROS 发布端可在可达的局域网主机上。`camera_source:"zmq"` 仍可接既有外部流，此模式不接管外部发布器的生命周期。生产启动使用独立 `.venv_ros2_camera`，系统 ROS Humble/CPython 3.10 与 numpy 1.21.5 保持 ABI 一致；固定依赖见 `apps/requirements-ros2-camera.txt`，不替换 SONIC/采集环境。

图像按 encoding 解码成彩色，默认 letterbox 到 640×480、JPEG 质量 85；resize_mode 另支持 reject/stretch，处理方式显式配置。源 `header.stamp` 必须为与工作站同步的 Unix 时间，零、回退、重复、过期、未来超限帧被拒绝；ROS 仿真时钟/相对 bag 时间须先形成有效的统一时间轴，不重写接收时间伪装成源更新。默认源有效期 0.5 s、三路时间差 0.1 s、ZMQ 发布上限 30 Hz，实际跟随最慢输入。缺路时其余视角仍可预览，录制器遇缺图/过期将按既有规则终止并保留舍弃/不完整标记；不生成假帧补齐录像。

原始大图 best_effort 在负载/网络拥塞时可能丢包；已验证 raw rgb8/bgr8 与压缩 JPEG 的解码和视角颜色，正式导出闭环使用三路 CompressedImage 测试源。现场应选择合适的压缩、频率和 QoS，核对带宽与时间同步；离线结果不等于任意现场图像链路均能达到 30 Hz。

离线验证：

```sh
cd apps
PYTHONPATH="$PWD:$PWD/tests" .venv_collection/bin/python -m unittest discover -s tests -v
source /opt/ros/humble/setup.bash
PYTHONPATH="$PWD:$PWD/tests${PYTHONPATH:+:$PYTHONPATH}" .venv_ros2_camera/bin/python -m unittest tests/ros2_camera_checks.py -v
```

74 个后端测试、3 个真实 ROS 2 通信测试和 17 个前端测试均通过；ROS 测试只使用 `/_robot_station_test_*` 独立话题、临时端口和 /tmp 文件，不向正式相机话题发送合成图像，不连接物理机器人。v1 快照新增 `camera_source`，OpenAPI 为 1.3.0 / 27 路径 / 34 数据结构。

## ② SONIC 软件启动管理

`POST /deployment/jobs` 的 `prepare` 固定要求 `payload.allow_motion:false`。后台按五阶段检查环境、准备运行时、等待相机、PICO 和机器人反馈：

1. 复用项目 `gear_sonic_deploy/docker/sonic-runtime.sh start`，检查容器标签/挂载归属。
2. 需要时在项目容器构建 C++ 目标；构建使用独立进程组和共享取消标记，取消不停止复用容器。
3. 检查 GPU、动态库、控制程序；通过共享 `run_xrobotoolkit.sh service` / `ensure_service()` 复用或准备 PC Service。
4. 启动本工作台的只读订阅器，等待新鲜设备数据。

准备不会运行 `deploy.sh real`、启动运动控制器、初始化机器人、抢占运动控制权或启动未知相机发布器。软件检查通过而设备缺失时，任务进入 `waiting`，步骤显示 `blocked`；连接设备后重新准备即可核对。`ready` 表示观察到各数据源就绪，仍不代表运动已初始化。

通过 `GET /deployment/jobs/{job_id}` 查看进度、结果和有长度上限的日志。取消中间步骤会保留已有运行环境和日志；失败可修复后以新命令重试。Web 重启时未完成准备任务会明确标记中断，真实服务按实际状态重新检查。

`services.actions` 当前支持启动 Docker、PC Service、相机来源与只读接入，停止自有 ROS 2 相机桥接，以及停止本项目待命SONIC容器和XRoboToolkit PC Service/Unity。两项基础服务停止会检查跨模式任务、控制器/进程占用及资源归属，快照给出`stop_allowed/stop_reason`；只有确认停止才返回`state:stopped`。详见 [服务启停](service_lifecycle.md)，OpenAPI 1.6.0。外部SONIC运动控制器的启停仍不开放；独立真机初始化/接管/关节目标走本地现场标定门槛，见 [SDK适配](g1_sdk_adapter.md)，不能绕过门槛启用运动。

## ③ 真实数据回放

现有片段分页、评级和 MP4 Range 接口继续使用。`GET /episodes/timeseries?dataset=NAME&episode=0` 从 LeRobot v2.1 Parquet 读取 `observation.state` 与 `action.wbc`：

- 必须有唯一、完整的具名关节及明确形状；按名称对齐 State / Action，不猜 DDS 顺序。
- 保留完整声明维度，包括手部；网页再按 29 个身体关节名称选出显示。
- 校验浮点数组、有限值、帧数/索引与严格递增时间戳；单位为 rad。官方 SONIC VLA 字段布局可识别旧 exporter 未填写 robot_type 的数据。
- 第一条录制数据对应视频零点；保留源时间原点供核对。
- 默认最多返回 6000 个预览点，可用 `max_points=2..10000` 调整。长片段明确报告 `sampled`、原始/返回帧数，保留首尾，不修改或重采样源文件。
- 独立读取进程使用 `.venv_conversion`；结果按来源文件变化缓存。源在读取期间变化会拒绝本次结果。

前端三视频、State/Action 曲线和 3D 姿态联动；缺失/错误序列会显示原因，视频仍可查看。可视化回放不会向机器人发送动作。视频接口 `/api/episodes/video` 支持 GET/HEAD、Range 和 206/416。

## ④ 采集任务管理

`POST /collection/commands` 支持 `prepare/start/save/discard/end`。本页管理录制任务，连接现场已启动并完成初始化的 SONIC/PICO/相机数据流，不代替运动控制器启动和物理控制权交接。

- `prepare` 校验数据集名称、任务、帧率、三相机、机器人/控制器反馈、PICO 追踪及现场标定确认；分配唯一任务并启动独立导出进程。
- 使用官方 SONIC `GrootDataCollector`、`Gr00tDataExporter` 和官方固定的 LeRobot v2.1 提交，保存 Parquet + 三路 MP4 + 元数据。完整状态/动作是模型维度，当前含手部为 43 维。
- 新环境 `apps/.venv_collection` 使用 CPU PyTorch，未改动 SONIC `.venv_teleop`。安装脚本 `bash scripts/install_collection.sh` 使用已验证的 `requirements-collection.lock`，不删除或重建已有环境。
- 显式命令通过持久队列送入导出器并等待确认，替代 `c/x` 切换；当前托管导出器忽略旧键盘及 PICO 的录制切换标志，避免重复触发。
- 一个工作目录只允许运行一个执行后端；采集跨 sim/real 互斥，并检测旧 tmux/外部官方导出器。后台只拥有录制任务；`robot.owner` 不会虚构运动接管状态。
- 不覆盖已有数据集。保存/舍弃只操作当前未保存片段；舍弃按官方 `discarded_episode_indices` 保留数据和标记，不删除录像。界面也兼容旧 `discarded_episodes`。
- 视频编码、结束与关闭由同一编码线程串行完成，确认三路文件完成后才报告保存成功；不创建或递归删除上游临时 images 目录。
- 录制中监测机器人、身体姿态和三相机更新时间；断流/冻结会在可能时将当前有效帧保存为舍弃，并报告失败。无法完整结束的文件保留 `.incomplete`，不伪装成功。
- `.incomplete` 在正常结束任务后移除；未结束或待核验的数据不能直接进入离线转换。
- 导出进程独立于 Web，网页重启可恢复会话、待确认命令和实际录制状态。进程退出会释放任务占用，并把未确认命令标记为未确认/失败。
- `GET /collection/logs` 提供有限长度的采集日志。保存/舍弃确认后前端刷新片段列表。

顶部“停止采集”（准备运行时显示“取消准备”）调用 `safety.stop`，可跨当前选中的运行模式取消准备、舍弃并结束当前采集。返回 `motion_stop_supported:false`：本轮尚未接入外部机器人运动停止，不能据该按钮推断机器人已经停机。

## 运行配置与现场接入

配置模板：[console-runtime.example.json](../apps/console-runtime.example.json)。需要调整时，在结束采集任务后保存到 `apps/.runtime/console/runtime-config.json`，分别配置 real/sim，再重新只读连接/准备。

- 真机默认 `eno1`、状态 `127.0.0.1:5557`、姿态 `127.0.0.1:5556`。
- 仿真默认 `lo`、状态 `127.0.0.1:15557`、姿态 `127.0.0.1:15556`，沿用隔离测试端口；须与实际仿真发布端匹配，普通官方脚本默认端口不同。
- 相机默认 `127.0.0.1:5555`，映射 `head→ego_view`、`left_wrist→left_wrist`、`right_wrist→right_wrist`。支持本机或 RFC1918 局域网 IPv4 数据源，可接 G1/其他相机主机；不接受网页随意提交外部地址。
- `pico_calibration_confirmed` 默认 false；现场确认 PICO 4 与腿部追踪器标定后再设置 true。该确认不能替代新鲜的 SDK 身体数据。
- 三路采集图像按 SONIC 原生要求为 640×480 RGB；相机主机与 4070 时钟需要同步。实际设备映射和录像频率仍须现场验收。
- G1 BMS 主题/消息、机型/手部配置、网络链路、初始化/控制权及运动停止需要现场核实。

## 命令、权限与互锁

设备命令发送 `action, mode, profile_id, expected_revision, payload`，附 `Idempotency-Key`。命令受理不等于设备就绪或文件保存成功。409 为版本/任务冲突，412 为前置条件不足，501 为按规划尚未实现的能力。运动命令不会自动重试。

工作站本机和 SSH 转发访问可操作；其他 LAN 浏览器默认只读，使用页面“授权操作”输入工作站本地的 `apps/.runtime/console/operation-key` 后获得 8 小时 HttpOnly/SameSite 会话。密钥文件权限 0600，不写入浏览器草稿。浏览器写操作另带快照中的 `X-Console-CSRF`；拒绝跨来源操作和不匹配的 Host。测试/日志不得打印密钥或完整会话信息。

后端会重新校验全部互锁和命令版本。旧 `/api/stack/*`、`/api/record/*` 控制入口在当前服务中返回 410；不再绑定旧 5580 发布端口，不与托管录制器争用。旧数据查询兼容接口保留，v1 快照是当前设备和任务状态的依据。

## 离线数据转换

入口 `/#conversion`。SONIC VLA 原生已是 LeRobot v2.1，包含 Parquet、MP4、JSON/JSONL 和 GR00T 模态/机器人配置；C++ CSV 只是独立调试日志。

- HDF5：`sonic-hdf5-v1`，每片段一个文件。`/frames/<原始字段>` 保留完整形状/类型/时间戳；`/videos/<原始相机键>/encoded_mp4` 保存原 MP4 字节，或选择 `/rgb` 保存逐帧图像；`/meta` 保存任务/片段/字段等信息。此布局不是 ACT/Robomimic 专用布局。
- LeRobot：验证后另存 v2.1 的完整副本，保留手部和舍弃标记；不声称升级 v3，不自动把缺视频的 CSV 补成训练数据。
- 输出 `sonic_deploy/outputs/conversions/<新名称>/`，不覆盖、不删除源数据。源变化会拒绝/中止；失败或取消保留部分结果，成功后才提供下载。
- `/api/conversions/*` 提供来源、预检、任务、进度、取消、历史与文件下载，独立于设备控制。

## 代码与验证

执行端：`console_runtime.py`（状态/互锁/命令）、`console_driver.py`（实际检查与固定服务操作）、`console_probe_worker.py`（只读采样）、`console_collection.py` / `console_collection_worker.py`（持久采集任务）、`console_video_writer.py`（视频结束确认）、`console_timeseries.py`（回放）、`console_access.py`（操作授权）、`console_support.py`（持久化与进程身份）。HTTP 入口仍为 `apps/server.py`。

前端调用层为 `console-api.js`；`console-core.js` 负责状态归一化与门控。3D、回放、转换、流程编辑分别在对应 `console-*.js` 中。本地 Three.js/STLLoader、Lucide 与许可证沿用现有资源。

验证命令：

```bash
# 4070，Robot Station 根目录：安装测试依赖后运行后端完整回归
/home/harry/.local/bin/uv pip install --python apps/.venv_collection/bin/python -r apps/requirements-console-test.txt
cd apps
.venv_collection/bin/python -m unittest discover -s tests -v
```

前端在有 Node 的开发机运行 `node --test apps/tests/console.test.mjs`。4070 无需安装 Node。

真实官方导出器的闭环测试文件为 `apps/tests/test_collection_pipeline.py`：仅使用 /tmp、临时 loopback 发布端和合成 PICO/机器人输入，核对三路视频、保存/舍弃、Web 重启恢复、断流、软件停止、Parquet 关节读取和 HDF5 转换。它不连接物理 DDS 或启动机器人，不能替代现场采集验收。最新结果和证据位置记录在 HANDOFF 最新节。

⑤任务模型动作适配/推理与⑥后台状态机执行按用户要求继续保留接口，现场连接并取得真实采集数据后再做。
