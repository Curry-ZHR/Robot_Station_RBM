# Robot Station 开发交接

最后更新：2026-10-20，Asia/Shanghai。此文件是本项目后续开发的首读入口；历史部署说明保留在 [handoff_deploy_1015.md](handoff_deploy_1015.md)。

## 0P. 2026-10-20 补齐容器/XRoboToolkit停止与源码交付说明（最新）

用户要求补齐“整机管理”中SONIC容器与XRoboToolkit的实际停止，并将4070的`/home/harry/workspace/robot_station`更新commit/push到`Curry-ZHR/Robot_Station_RBM`。仓库origin与该目标一致，按现有README在main维护；本轮包含此前未提交的工作台、SDK、相机/采集/回放/转换、启停入口、交接与部署分工更新。

- 已实现`services.docker.stop`与`services.pc_service.stop`，仍用`POST /api/v1/console/services/actions`。前者核对项目标签、不可变容器ID与待命进程后停止并保留容器/模型；后者停止本项目PC Service与Unity 3D，核对路径、用户、启动时间与Linux pidfd，确认退出才报告成功，不对其他安装执行信号、不自动强杀未退出的XR进程。
- 采集、手动控制、准备任务、其他模式的SONIC反馈及可见控制/遥操作/采集进程会阻止停止。前后端均校验，快照提供stop_allowed/stop_reason；按钮显示“停止中…”，失败给出原因。保留原授权/CSRF、revision及幂等协议；基础服务停止不代表机器人硬件急停。
- XR新增`run_xrobotoolkit.sh stop`与持久service.stopped标记，阻止隐式SDK/PICO准备自动重启，显式service/3d启动会清除标记。扩展源码及带备份/基线校验的安装器随本仓库提供：[integrations/sonic](integrations/sonic/README.md)、`scripts/install_xrobotoolkit_lifecycle.sh`。4070的SONIC工作副本已安装；无需把本次代码散落为不可复现的外部改动。
- **验收通过：112项后端、19项前端。** 在4070真实HTTP接口完成两项stop→实际进程/容器停止→start任务成功；gRPC/Unity退出及恢复、隐式重启被拒绝、响应schema均已核对。最终恢复原有待命容器、PC Service和Unity；SONIC控制器始终离线，没有执行真机运动。Docker进程核验已适配该机要求的PID列。
- OpenAPI **1.6.0，34 paths / 43 schemas**。操作、升级依赖与接口见 [service_lifecycle.md](docs/service_lifecycle.md)，验收见 [service-lifecycle-20261020](docs/references/service-lifecycle-20261020)。网页侧栏Connecting仍只表示后台可达，设备状态独立显示。
- 提交范围为源码、静态资源、依赖清单、说明与脱敏验收材料；运行密钥/会话/真机授权、虚拟环境、采集输出与.deb不纳入。真实标定、任务模型/后台状态机和最终.deb待办不变，不能把本轮提交当作整机最终交付完成。

## 0O. 2026-10-20 侧栏连接标识替换 LOCAL

用户要求侧栏底部原“● LOCAL”按连接状态变化。已改为网页与4070执行端snapshot接口连接成功时绿色圆点及绿色文字“Connecting”（按用户指定文案），连接失败/接口不可用时红色圆点及红色“Failed”；首次检查中灰色“Checking”，本地界面预演黄色“Preview”，不把合成状态标成真实连接成功。沿用现有轮询，失败后恢复会自动切回绿色。该标识仅表示工作台后台连接，G1真实反馈/电量和相机就绪仍分别显示。改动仅涉及静态前端，不更改控制或运动权限。

## 0N. 2026-10-20 新增计算部署与执行分工规划

用户要求将后续分工单独记录在根目录 [handoff_distribution.md](handoff_distribution.md)：大模型可放HPC、4090或当前4070；4070统一负责网页预览、相机/数据采集、观测上传、动作校验调度和有线下发；目标由G1侧兼容SONIC执行器接收motion token及手部动作，遥操作采集与模型推理共用执行路径。尽量复用G1板卡与环境，不要求机载Orin运行GR00T。

**这是后续架构规划，不表示已实现。** 当前验证基础主要是4070运行SONIC/C++，经Unitree DDS向G1发底层命令；要按新目标让G1接token，还须核验/部署G1侧SONIC解码执行器，不能假定原厂板卡原生识别token。文档已区分目标与现状、三种模型位置、动作合同/网络、采集与推理路径及待验收事项。4070 GR00T环境/CUDA导入与小矩阵运算通过，但未发现可用模型权重或运行服务，12GB显存下完整N1.7推理未验证。第0M的自动姿态交接暂缓、第0L的.deb交付提醒和实机门槛保持。

## 0M. 2026-10-20 范围调整：暂不做手动姿态到 SONIC 的自动交接

用户说明SONIC启动时会自行进入初始姿态，因此**暂不开发“工作台先设置初始姿态，再交给SONIC”的自动交接功能**，不再将其列为当前交付缺项。本节覆盖0F及其他旧节中的相关交接要求；这项需求是暂缓，不是已实现或已完成真机验收。

- 独立SDK滑条控制、具名姿态库和目标/反馈对照继续保留，用于SONIC未运行时验证工作台到G1的链路及机械支撑下的关节调试；预先应用工作台姿态不作为启动SONIC的必经步骤。
- SONIC运动程序的初始姿态进入由其自身流程负责，按用户说明记录；本轮未实测该启动动作。Docker/网页软件准备仍为allow_motion:false，不等于启动SONIC运动程序，更不自动触发机器人初始化。
- 继续保持控制源互斥：使用SONIC运动前须结束独立手动控制并确认其停止发布；SONIC控制期间不允许滑条同时向真机下发。这里保留的是退出与互斥要求，不新增无缝交接、姿态匹配或自动抢占功能。
- 真实反馈/BMS、逐轴方向、增益/限幅、支撑/停止及控制周期仍须现场标定验收；不因本次范围调整而跳过。任务模型推理、后台状态机及.deb交付待办不变。

## 0L. 2026-10-20 交付待办：Ubuntu .deb 安装包与收尾提醒

用户明确要求将 `.deb` 安装包列入项目最终交付，并在开发完成但仍未打包时主动提醒。**当前状态：待制作，尚未生成、验收或上传发布安装包；本次仅记录和设置提醒，不启动打包。**

- [ ] 功能开发及约定验收完成后，制作可供其他Ubuntu工作站安装的 `.deb` 运行端；安装/启动后通过浏览器访问。SONIC镜像、模型等大资源允许单独配套分发。
- [ ] 完成交付验收并在本节记录包版本、文件路径、SHA-256、支持的Ubuntu/架构，以及干净系统安装、启动、停止、自启动、升级/回滚和保留数据卸载的结果；详情见 [分发方案](docs/distribution_plan.md)。
- **提醒规则：**后续会话在汇报“开发完成”、准备收尾或交付前，必须检查本节。若安装包仍未制作或未完成验收，应明确提醒用户“功能开发已完成，Ubuntu .deb 安装包仍待制作/验收”，列为下一步；不能把当前run.sh或源码目录当作已交付安装包。检查以本项目整体开发状态为准，单个功能完成不触发收尾提醒。
- 只有核对上述产物与验收证据后才能勾选安装包完成；提醒本身不代表用户要求立即打包或上传。条件提醒每天检查一次，开发仍在进行时不触发安装包催办；同一未变化事项不重复催办。后续开发者也应执行上述收尾检查，不只依赖自动提醒。

## 0K. 2026-10-20 真机SDK适配软件完成，实机标定待现场

用户要求按Unitree SDK完善独立真机关节适配，并确认本台是完整29自由度、腰部roll/pitch未锁定。本轮完成HG/PR LowCmd、35槽位/29身体电机映射、官方CRC与LowState校验、C2轨迹及限位/速度/加速度、单次步幅、超时/模式/数据源/控制器互斥、私有租约和受支撑场景停止流程，已接入现有真机命令和网页标定状态。**这覆盖0J的“真机驱动尚未实现”状态；实机增益、支撑和停止效果未验证，当前不启用运动。**

- 官方依据为4070内SDK commit `4141c34280abb67c82e115342a8720f4a83d750d` 的G1示例、HG IDL、CRC及MotionSwitcher。PR=0，2ms周期，mode_machine须匹配现场反馈。不自动ReleaseMode，不自动归零，不复用SDK示例里的脚踝摆动。
- `unitree_g1_control.py`负责协议/标定门槛/解析轨迹边界，`unitree_g1_transport.py`负责SDK只读预检和显式创建发布器，`console_real_worker.py`独立检查反馈/租约并发送，`console_real.py`管理普通命令/私有租约/IPC，`unitree_commission.py`提供本地template/inspect/validate/approve/revoke工具。高频通道只允许heartbeat/apply_pose，无法绕过普通接管流程。
- 正式 `apps/.runtime/console/real-control/commissioning.json` 权限0600、approved=false；已记录用户确认的机型，增益仅参考、实测参数未填、现场确认项均未伪造。授权须本地现场完成，最长4小时，绑定本机/本次开机/网卡域/模型/SDK/控制代码/唯一LowState来源；网页不能批准，分发包不能携带该授权。无授权时所有真机运动capabilities关闭。
- initialize只做预检；claim须明确机械支撑已就绪才创建LowCmd发布器，从实时姿态开始。完整目标按具名rad与实际反馈校验；普通释放/租约过期在机械支撑前提下阻尼后禁用。CRC/反馈/模式/来源/竞争控制器或调度异常会停止本适配器输出；**不能宣称机器人已经硬件急停，也不支持自由站立平衡或自动SONIC交接。** 开机不会启动manual-real；错误后不自动恢复运动。
- 网页“真机环境→全身控制”新增真机适配与标定面板、参考参数映射和未批准模板下载；保留真机显式接管确认。OpenAPI 1.5.0，34 paths / 43 schemas。
- 离线验收：后端100项、前端18项、SDK/IPC/MuJoCo集成8项。实际SDK测试比对官方参考增益、独立1004字节CRC布局/IDL、Lo/Domain232收发、竞争LowCmd与数据源绑定；IPC内存传输跑通初始化/接管/目标到位/心跳/释放/网页重启撤销。测试没有向实际机器人域发布，未执行实机动作。证据见 [unitree-adapter-20261020](docs/references/unitree-adapter-20261020)。
- 现场剩余详见 [G1 SDK适配说明](docs/g1_sdk_adapter.md)：真实LowState/BMS、逐轴映射/方向、硬件支撑、实际增益/力矩边界、停止效果及重负载周期。SONIC自动交接按第0M节暂缓，控制源互斥仍须核验。上次检查有线口仍NO-CARRIER，不能把用户确认机型或离线测试说成实机标定完成。
- 用户希望最终能打包分发。记录为功能稳定后制作Ubuntu `.deb` 运行端（可另附SONIC模型/镜像资源包）+浏览器访问；访问已有4070无需客户端安装。首启配置/版本清单/干净环境安装回滚验收/不携带密钥和真机授权为打包要求。**本轮未制作或上传安装包。** 详见 [distribution_plan.md](docs/distribution_plan.md)。⑤采集质量、任务推理和后台状态机仍按先前规划后置。

## 0J. 2026-10-19 连接配置、诊断、姿态库、物理仿真与常驻入口（最新）

本轮按用户要求实现六项计划中的①连接配置、②链路诊断、③初始姿态、④独立控制后端/离线物理仿真、⑥常驻服务；**⑤采集质量评分暂不处理。** 此节覆盖旧节中“滑条永远仅本地、运动命令全部501、根入口仍为旧ROS”的状态。真机实际关节输出尚未实现/启用，不能把 MuJoCo 验收说成本台 G1 已验收。

- 新增侧栏“连接与诊断”：real/sim 连接表单、配置校验/方案/导入导出、修改前自动备份与恢复、明确重新接入；ROS图像99与Unitree DDS0分开。准备/采集/手动控制期间拒绝改配置。
- 诊断使用独立 ROS Humble 子进程/context，扫描三路实际发布者、类型、offered QoS及兼容性，提供帧率/帧龄/三路时间差/接受拒绝计数/桥接异常、网卡、G1/BMS新鲜度与版本。ZIP只导出明确列出的状态和配置；排除凭据、会话、租约、环境、原始日志、数据集内容。
- 初始姿态库支持完整具名29维、rad、URDF限位、profile/model_hash校验、命名保存、加载、JSON导入导出、归档及五次平滑轨迹预览。保存/加载、已发送和实际到位明确区分。
- **仿真环境**新增独立 MuJoCo 控制：真实G1 MJCF惯性/重力/接触，固定基座物理步进与有界PD，浏览器URDF显示目标/反馈。初始化→手动接管→显式开启实时联动后，滑条/数值可下发；单次应用也可用。3秒租约、独立worker超时保持、严格递增序号、具名限位/速度约束、任务互斥与Web重启撤销控制权。物理仿真不提供虚构电量，不证明站立平衡，也不包含本台G1的LowCmd发布器。
- 根目录现为 `./run.sh` 启动整套工作台、`./stop.sh` 有序关闭；systemd用户服务 `robot-station.service` 已 enabled，harry `Linger=yes`，无需登录随开机启动。开机只提供网页/只读服务，不启动仿真初始化、运动、采集、推理或控制权。网页异常独立恢复，主管异常由systemd恢复；自有进程PID/start-ticks核对、日志滚动、配置/姿态持久化。相机显式停止不会被看护重启。旧根ROS脚本完整保留 `run_legacy_ros.sh`。
- OpenAPI **1.4.0 / 33 paths / 41 schemas**。详细启动方法、接口字段、持久路径、实现边界与现场事项见 [station_operations.md](docs/station_operations.md)。新增API为configuration、diagnostics/download、poses/preview与robot/manual，原有授权/CSRF/命令版本协议继续有效。
- 自动检查 **106项通过**：后端82、真实ROS通信/诊断4、MuJoCo物理2、前端18；另有生产服务生命周期与API验收JSON。验收包含：配置冲突/备份恢复/非法输入、具名姿态与轨迹速度、租约/序号/真机门禁；实际MuJoCo步进/跟踪/掉心跳保持；真实ROS Domain99图发现/类型/QoS不兼容、原三项桥接通信；前端初始化互锁；网页退出恢复、run/stop清空自有进程、开机服务配置与用户驻留。浏览器已实测左肘目标25°→物理反馈25°→已到位，并保存“离线验收 · 左肘25°”。证据目录：[station-release-20261019](docs/references/station-release-20261019)。未重启4070或执行任何真机动作。
- 现场剩余：三相机实际topic/type/QoS/时钟与带宽；PICO4/腿部追踪器全身标定；真实G1反馈/BMS；实际LowCmd手动驱动、支撑/停止策略和SONIC控制权交接。任务模型推理与后台状态机执行仍按原决定后置。

## 0I. 2026-10-19 ROS 2 → ZMQ 三相机桥接完成并启用 Domain 99（最新状态）

用户授权先配置 99 并实现图像订阅到 ZMQ。**本节覆盖下方 0H 的“桥接待实现”状态：桥接、独立环境、托管启停和离线验收已完成，真实相机话题/网络仍待现场核对。** 现有真机关节运动、⑤推理与⑥状态机执行的边界不变。

- 正式配置已保存到 `apps/.runtime/console/runtime-config.json`，real/sim 均选择 `camera_source:ros2`、`ros2_camera.domain_id:99`；G1 SDK2 的 `dds_domain` 继续按现有配置，默认 0，没有全局改成 99。桥接目前运行并等待相机话题，不需要 SONIC/PICO/G1 在线。
- 默认三路占位配置：`head→/camera/head/image_raw`、`left_wrist→/camera/left_wrist/image_raw`、`right_wrist→/camera/right_wrist/image_raw`；类型均为 `sensor_msgs/msg/Image`，QoS best_effort / volatile / depth 5。**这些是可编辑默认值，不是已经发现的现场话题。** 每路也支持 `sensor_msgs/msg/CompressedImage` 和 reliable QoS。
- `apps/ros2_camera_bridge.py` 在独立 ROS 2 Humble 进程/context 中订阅，按消息 encoding 转成彩色，默认 letterbox 归一为 640×480、JPEG 质量 85，保持 head→ego_view / left_wrist / right_wrist 的 ZMQ msgpack/JPEG 协议，供现有预览和官方录制器共用；不发布任何机器人控制消息。
- 保留 ROS `header.stamp`，要求 Unix/墙钟时间与工作站同步；零/回退/重复/过期/未来超限时间戳拒绝，不用接收时间覆盖源时间。默认源帧有效期 0.5 s、三路最大时间差 0.1 s，发布上限 30 Hz，实际跟随输入；全包要求三路均更新且时间差合格。缺路时只发送其余真实有效视角，录制器不会补造缺图，断流会触发原有失败/舍弃处理。
- `apps/console_camera_source.py` 与 SystemDriver 管理唯一共享桥接进程：PID/start-ticks 归属、配置/代码版本、新进程状态核对、端口冲突报错、sim/real 复用、正常停止与重启。Web 重启不自动杀死独立桥接。相机服务启动不依赖 Docker/PC Service 或 SONIC 运动程序；采集期间拒绝相机服务启停。
- 依赖隔离为 `apps/.venv_ros2_camera`，基于系统 Python 3.10 + ROS Humble；固定 numpy 1.21.5（匹配 cv_bridge/OpenCV ABI）、pyzmq 26.4.0、msgpack 1.1.0、msgpack-numpy 0.4.8。未改已有 teleop/collection/conversion 环境。安装入口 `bash scripts/install_ros2_camera.sh`，执行入口 `bash scripts/run_ros2_camera_bridge.sh`；复用安装不删除现有环境。
- 网页“整机管理 → 相机接入”可启动/停止自有桥接；“只读连接”或完整准备也会按配置准备相机来源。传感器页显示 ROS 2 Domain 99、桥接状态和三路配置话题。v1 快照新增 `camera_source`，OpenAPI 版本 **1.3.0，27 路径 / 34 数据结构**，现有接口路径保持一致。
- **验证共 94 项通过：后端 74 + 真实 ROS 2 通信 3 + 前端 17。** 通信测试用独立测试话题、临时 loopback ZMQ，验证 Image(rgb8/bgr8) / CompressedImage、颜色映射、冻结/断流与恢复、Domain 100 与 99 隔离、端口冲突及托管复用/重启。没有使用真实机器人或污染正式相机话题。
- 官方导出器闭环已实际通过：三路 ROS 2 JPEG 测试图像 → 桥接 → HTTP 录制/保存/舍弃 → 三 MP4/43 维 Parquet → 新 Web 进程恢复 → 回放与 HDF5。原始大帧 best_effort 在测试负载下曾丢包，断流保护按预期触发；原始/压缩兼容性由独立混合类型测试覆盖，录制闭环采用三路压缩图像。现场需按带宽、QoS 和帧率选取图像传输方式，不承诺任意原始图链路都达 30 Hz。
- 正式入口已实际验证相机 start→stop→start、快照 schema；当前为 Domain 99 / waiting、0/3 有效画面、G1/BMS 无真实样本，正式 0 / 演示 1075；运动能力未开放。离线测试全部输出在 /tmp，不能当作真机/真实相机验收。
- 接入步骤、配置及命令见 [后端接入说明](docs/data_collection_console.md)；证据：[后端 74 项](docs/references/ros2-camera-20261019/backend-tests.log)、[ROS 2 通信 3 项](docs/references/ros2-camera-20261019/ros2-wire-tests.log)、[正式入口核对](docs/references/ros2-camera-20261019/release-verification.json)、[正式传感器页](docs/references/ros2-camera-20261019/ros2-source-status.png)。原文件有备份，未提交/推送。

## 0H. 2026-10-19 三路相机采用 ROS 2 订阅接入（新方向，桥接待实现）

- 用户明确后续三路摄像头画面使用 ROS 2 话题订阅；可能使用 `ROS_DOMAIN_ID=99`。**99 当前是候选配置值，并非已确认现场值，也未在机器上设置。** 头部、左腕、右腕的实际话题名、消息类型、QoS、帧率及来源主机待提供/现场核对，不臆造设备 ID 或话题名。
- 建议由独立相机桥接进程/ROS 2 context 使用相机域（候选 99），发布端与订阅端使用相同域；G1 关节/BMS 的 Unitree SDK2 DDS 域继续按机器人配置维护（现有默认 0），不全局改成 99。两路数据在工作台后端汇合，不能因使用相机域而丢失 G1 状态/电量。
- 计划链路：ROS 2 三路图像 → 独立相机桥接 → 现有 SONIC ComposedCamera 兼容的 ZMQ msgpack/JPEG 数据流 → 工作台三路预览和官方录制器。复用已验证的预览/录制消费者；桥接保持现有 head→ego_view、left_wrist、right_wrist 逻辑映射，实际 ROS 话题另行配置。**当前代码仅实现 ZMQ 图像消费者，ROS 2 图像桥接尚未实现。**
- 消息优先按现场发布类型适配 `sensor_msgs/msg/Image` 或 `sensor_msgs/msg/CompressedImage`；QoS 必须与发布端兼容，不能只因 Domain ID 相同就判定可收流。按 encoding 解码和转换颜色；导出器所需 640×480 RGB 的输入适配方式须明确，不能默默交换三路视角或错解颜色。
- 保留源 `header.stamp` 及帧的新鲜度信息，记录接收时间；核对 ROS 时钟、相机主机/4070 时钟与机器人录像时间轴。断流、重复/冻结帧和不兼容时钟需要报告，不能用当前时间伪装源仍在更新。按实际采集频率验证三视频与数值帧同步。
- 相机读取应独立于 SONIC 运动控制运行，便于先验证传感器，再采集或推理。跨主机时网络与 DDS 发现需可达；跨 VLAN/子网不会因设置相同 Domain ID 自动互通，需现场确认路由、组播/显式发现配置和带宽。
- 待开发/验收：独立 ROS 2 桥接进程与配置、依赖隔离和进程归属管理、三路 topic/消息/QoS 映射、时钟与冻结检测、桥接到原生录制器格式；分别验证预览、保存/舍弃三路录像、断线恢复和同步回放。相机域变更不得触发机器人运动或改写 Unitree DDS 配置。

## 0G. 2026-10-19 电量要求：连接真机后持续读取，不依赖 SONIC

- 用户明确要求工作台连接真实 G1 后自动、持续显示机器人电量；属于只读连接能力，不依赖 SONIC、PICO、手动运动接管或模型推理在线。只读连接成功以收到有效的真实数据为准，不能仅依据网线或端口可达。
- 已核对 4070 内官方 `unitree_sdk2_python`：`unitree_sdk2py.idl.unitree_hg.msg.dds_.BmsState_` 包含 `soc`、`soh`、`current`、`bmsvoltage`、`temperature` 等字段；电量从 `soc` 读取。G1 的 HG LowState_ 不含 BMS 字段，需独立订阅 BmsState_，不能套用 Go2 的 LowState.bms_state 结构。
- 当前实现位于 `apps/console_probe_worker.py`：经 SDK2 ChannelSubscriber 订阅配置中的 `rt/bmsstate` 与 `rt/lf/bmsstate`，校验 soc 0–100，记录来源与接收时间，经 v1 snapshot 提供电量。官方 G1 仿真桥使用 `rt/lf/bmsstate`，但本台真机实际主题、DDS QoS、固件兼容性和更新频率仍须现场验证，仿真数据不能证明真机电量可读。
- `robot.connect` 可启动只读订阅，不要求先准备/启动 SONIC 控制器。页面当前每 2 秒查询快照，更新顶栏电池和整机管理电量/采样时间；设备真实发布频率决定数据的新鲜度。后台持续接收 BMS 消息，不以刷新页面代替订阅。
- 现有有效性规则：G1 关节反馈需在 5 秒内，电量在 15 秒内且数值合法；缺失、断连或过期显示未知，低电量按阈值提醒，不显示虚构百分比。自动连接或重连不得启动运动或申请运动控制权。
- 本轮只读查询真实入口：robot_connected=false、battery.percent=null，eno1 报未接线或状态不可用；因此尚未取得此 G1 的实际 BMS 样本，不能声明现场链路验收通过。现场验收包括：SONIC 不运行时收到真实 soc、持续更新、断线显示未知、重连恢复，再核对充电/放电情况下显示。
- 官方依据：[Python HG BmsState_](https://github.com/unitreerobotics/unitree_sdk2_python/blob/master/unitree_sdk2py/idl/unitree_hg/msg/dds_/_BmsState_.py)、[官方 G1 仿真桥的 BMS 主题](https://github.com/unitreerobotics/unitree_rl_mjlab/blob/main/simulate/src/unitree_sdk2_bridge.h)。本次仅核对与记录，无运动控制改动。

## 0F. 2026-10-19 历史需求：独立 G1 关节联动、初始姿态与 SONIC 接管

**后续状态：**独立SDK适配已按0K实现、真机标定待现场；自动交给SONIC的部分已按0M暂缓。以下保留原始规划，不再将第5步或手动姿态到SONIC的交接验收列为当前交付待办。

**用户明确要求：在未启动/未连接 SONIC 控制器时，通过工作台滑条或数值输入，同时调整浏览器 URDF 目标模型和 G1 真机关节；借此快速验证工作台到 G1 的实际控制链路，设置初始姿态，再调用 SONIC。** 本节记录新的目标能力，不表示已经实现；0E 的“目前只在本地预览”仍是现有代码状态。本次只更新交接，没有开放运动接口或执行机器人动作。此前⑤任务模型推理、⑥后台状态机执行留待真机采集后的安排不变。

### 预期操作流程

1. 不运行 SONIC，工作台直接通过独立的 Unitree/G1 控制后端连接机器人，读取实时关节反馈和控制模式，明确显示连接状态与数据新鲜度。
2. 默认仍是本地预览。用户明确启用“真机关节联动/手动调试”并取得唯一控制权后，拖动滑条或输入角度，URDF 目标姿态与真机目标同步更新；联动模式下不要求每次滑条变化都另点“下发”。联动未启用、反馈失效或条件不足时只能本地预览，不下发。
3. 保留单关节/分组调试入口，方便先以可观察的小幅变化核对名称、方向和实际响应。页面分别显示目标值与真实反馈/误差，不能仅凭 URDF 模型变化或网口连接就宣称链路已打通。浏览器 URDF 是目标/反馈可视化，不等于物理仿真。
4. 允许设置、保存、加载和应用具名初始姿态；应用时以实时反馈为起点、通过有时长和速度限制的插值逐步到达，显示实际到位结果。模型零姿态不能默认作为真机初始姿态；应现场确定适配 G1 机型、支撑/平衡方案和 SONIC 入口的姿态配置。
5. 初始姿态就绪后提供“交给 SONIC/启动 SONIC”流程：先停止并确认独立手动控制的指令发布，再按已验证的控制模式交接，启动/接管 SONIC。两者不可同时发布底层运动命令；接管后关闭滑条真机下发，保留只读反馈和模型显示。

### 待实现与验收边界

- 独立手动调试后端不以 SONIC 控制器、PICO 或任务模型在线为前提；实际采用的 Unitree SDK 控制接口、HG 29 电机名称映射、控制模式/初始化及支撑/平衡要求需核实后实现。能读取 lowstate 不等于已具备可用的运动执行链路。
- 后端负责实时控制循环、目标更新限频/合并、角度与速度等约束、反馈超时和控制权互斥；不直接按浏览器拖动事件频率发底层 LowCmd。URDF 几何限位不能替代真机稳定性、碰撞和模式约束，尤其腰腿与站立场景。
- 应实现手动联动的明确启用/退出、现场停止行为及断连处置；网页刷新/掉线后不得自动恢复运动。沿用现有授权、版本校验和幂等约定，具体接口与实时目标通道在实现时补充合同，当前不虚构已支持的新 API。
- 初始姿态需记录具名关节、单位、机型/配置、过渡参数等，并区分“已保存”“已发送”“反馈到位”；只有满足 SONIC 实际启动条件的配置才允许后续交接。SONIC 失败时明确报告控制归属，不在未知状态下自动重发姿态或抢占。
- 现场验收顺序：只读反馈 → 独立手动小幅单关节联动 → 目标与反馈对照 → 分组/初始姿态平滑应用 → 退出/断连与停止 → 手动到 SONIC 的唯一控制源交接。正式验收必须使用真实反馈，`?preview=1` 演示不能替代。

## 0E. 2026-10-19 身体关节目标增加可拖动滑条

- 全身控制页五个分组的 29 个身体关节目标已增加滑条，保留数值输入（度，0.1° 步进）；两种输入同步，切换分组保留当前目标。
- 拖动或编辑有效角度后自动开启本地目标预览，立即更新 G1 3D 模型；参考范围沿用 URDF，内部目标仍按模型精确范围限幅。反馈值与目标值继续分开显示。
- **修改滑条或数值不自动发送设备命令。** 当前 `robot.apply_pose`、控制权接管和运动初始化后端仍未开放，即使 G1 网线已连接、未运行 SONIC，也不会由这些编辑动作驱动实体机器人。`?preview=1` 全部是浏览器合成预演。
- 若要不经 SONIC 直接调试实体关节，仍须另行实现并现场验收 Unitree 控制后端、控制权与停止行为；本次未增加该能力，未启动机器人运动。
- 已部署 `apps/static/console.js` 与 `console.css`，静态更新无需重启 Web。备份 `.local-backups/console-execution-20261019-141130-538391/`。
- 验证：17 项前端测试通过；浏览器验证五组滑条数量、角度输入双向同步、上下限操作、自动目标预览及切组保留。当前真实后端快照 `can_apply_pose:false`、`can_claim:false`，机器人能力仅只读 connect。①②③④ 后端完成范围仍见下节。

## 0D. 2026-10-16 ①②③④ 后端开发与离线验收完成（最新状态）

用户要求按顺序完成 ①状态/自检、②SONIC 启动管理、③数据回放、④采集任务管理，⑤任务模型推理与⑥后台状态机执行留到真机连接和采集之后。本节为当前状态，覆盖后文“设备 v1 尚未实现”等历史描述；**完成的是这四项远程软件开发与离线验证，真实硬件和运动行为仍须现场验收。**

### 接口与后端说明的固定入口

- **[接口规范：apps/contracts/console-v1.openapi.json](apps/contracts/console-v1.openapi.json)**：OpenAPI 3.1，当前版本 **1.2.0，27 路径 / 33 数据结构**；已标明各命令实际支持范围。
- **[后端接入说明：docs/data_collection_console.md](docs/data_collection_console.md)**：当前实现、文件职责、启动/权限、配置、现场接入和测试命令。
- **[现场配置模板](apps/console-runtime.example.json)**：复制并按现场情况配置到 `apps/.runtime/console/runtime-config.json`。默认不确认 PICO 标定；真机与仿真端口分开，不猜相机设备 ID。

| 用户规划项 | 已交付与验证 |
| --- | --- |
| ① 状态 / 自检 | 真实磁盘、GPU、Docker、镜像、模型、程序、SDK/采集依赖检查；v1 快照与只读 G1 DDS/BMS、SONIC、PICO 身体时间戳和三相机接入。缺失/过期为未知，不用端口在线伪造设备就绪 |
| ② SONIC 软件启动 | 持久后台任务、容器复用、需要时构建、GPU/库/程序检查、共享 PC Service、只读接入、进度/日志、取消与失败重试。软件完成而设备缺失显示 waiting；准备固定 allow_motion:false |
| ③ 数据回放 | 实际解析 LeRobot Parquet 的具名 State/Action，完整维度含手部，校验时间戳/帧数/类型/单位；三路 MP4、曲线和 3D 同步。长片段有明确预览采样标记，源文件不变 |
| ④ 采集任务 | 官方 SONIC 导出器的独立进程与环境；持久的 prepare/start/save/discard/end 和确认结果；跨模式互斥、进程身份、重启恢复、异常释放、三路视频串行结束确认、断流/冻结保留舍弃标记和不完整数据 |

### 已实际运行的证据

- **后端完整回归 68 项通过，前端 17 项通过，共 85 项。** 后端测试在独立采集环境运行，无跳过。包含 API 合同、权限/CSRF、幂等与版本冲突、具名关节、电量/数据过期、相机真实 ZMQ 解码/冻结、进程归属、Parquet 与转换测试。
- 4070 实际 Docker 构建验证通过（目标 g1_deploy_onnx_ref）；实际软件准备复用现有容器和 PC Service，通过 GPU/动态库检查。正式 Web 入口的 real/no-motion 准备任务完成软件步骤后进入 waiting，与没有现场设备一致。
- **官方导出器闭环 3 项通过**：临时 loopback 发布合成机器人/PICO/三相机输入 → HTTP 准备/录制 → 保存/舍弃 → Web 后端重启恢复 → 实际三 MP4 与 Parquet → 关节序列 API → HDF5。另核对三视频颜色分别映射头部/左腕/右腕、帧数与数值帧一致。
- 浏览器读取上述实际生成文件（明确标成演示片段），三路 640×480 视频逐帧到 0.2 秒保持同步，曲线和 G1 State 姿态联动；无浏览器错误。该验证使用 /tmp 的合成采集文件，不是实机数据，也不写正式 outputs。
- 数据源冻结会保存当前有效帧为舍弃并报告失败；软件停止可跨当前选中的 sim/real 模式结束录制并保留舍弃标记。未结束或待核验的 `.incomplete` 来源不能转换。
- 正式统计仍 **0**，演示 **1075**。网页 `/healthz`、v1 快照、转换来源接口正常；Snapshot / Job / Accepted 的实际响应通过 OpenAPI schema 校验。
- 证据：[正式入口验证](docs/references/backend-v1-20261016/release-verification.json)、[后端测试日志](docs/references/backend-v1-20261016/backend-tests.log)、[构建日志](docs/references/backend-v1-20261016/managed-build.log)、[实际文件回放截图（合成采集）](docs/references/backend-v1-20261016/recorded-fixture-playback.jpg)。

### 当前运行与边界

- 实际代码在 `apps/console_runtime.py`、`console_driver.py`、`console_probe_worker.py`、`console_collection.py`、`console_collection_worker.py`、`console_video_writer.py`、`console_timeseries.py`、`console_access.py`、`console_support.py`，由 `apps/server.py` 接入。
- 独立 `apps/.venv_collection` 已安装并实际导入官方导出器；CPU torch 2.6.0、numpy 1.26.4、datasets 3.6.0、LeRobot 官方提交 a445d9c9da6bea99a8972daa4fe1fdd053d711d2。已保存可复用的 requirements-collection.lock，安装脚本重复运行验证通过。原 `.venv_teleop` 未被替换。
- Web 与 SDK/运动控制隔离。启动网页不启动运动；准备只让软件就绪；采集管理只拥有录制任务，接入现场已初始化的 SONIC/PICO/相机发布流。**robot.initialize/claim/apply_pose、外部控制器运动启停仍未开放。**
- 顶部显示“停止采集”（准备运行时显示“取消准备”），仅取消本工作台准备并结束录制；接口明确 `motion_stop_supported:false`，不代表机器人已经停止运动。
- `.runtime/console` 持久保存进程身份、任务、确认结果和配置；Web 重启不自动杀死独立录制器。旧 stack/record 控制 POST 在当前服务返回 410，不再绑定旧 5580 发布端口。
- 本机/SSH 转发访问可操作，其他 LAN 访问默认只读；使用本机 operation-key 授权后可写。密钥文件 0600，浏览器写操作有同源/CSRF 校验，不在日志或交接里存放密钥。
- ⑤任务模型推理与⑥后台状态机执行按用户要求未实现（501/能力不开放）；现有前端和合同保留。现场仍要核实 BMS 主题、PICO 4 + 腿部追踪器标定、真实三相机发布服务/映射/时钟、G1 初始化与控制权及停止行为，再验收正式采集。
- 固定入口仍为 `http://192.168.123.100:9999/`；Mac 为 `http://127.0.0.1:12947/`。未修改既有网络方案，未启动真实机器人运动、真实 PICO 采集或任务推理；两库原有未提交改动保留，未提交/推送。

## 0C. 2026-10-16 当前完成范围、接口入口与后续计划（优先阅读）

**“先完成前端、预留后端接口”阶段已完成；完整真机操作链路尚未完成。** 以下为当前状态，优先于后文历史阶段的页数、接口数量和旧端口描述。设备执行后端还有代码需要开发，并非到现场连接硬件后即可全部使用。

### 接口规范与后端接入说明

这两份文件已位于 4070 的 `robot_station` 项目内，从本交接入口统一查阅：

- **[接口规范：OpenAPI 3.1](apps/contracts/console-v1.openapi.json)**：当前合同版本 1.1.0，22 个接口路径、30 个数据结构；定义请求/响应、状态、任务进度与错误。生成器为 [build_contract.py](apps/contracts/build_contract.py)。合同包含已实现的数据接口与待实现的设备接口；有规范不等于已有设备执行服务。
- **[后端接入说明](docs/data_collection_console.md)**：页面与模块职责、启动地址、接口对接规则、现场接入顺序、验证方式及数据转换布局。
- 前端调用入口：[console-api.js](apps/static/console-api.js)；转换页面调用：[console-conversion.js](apps/static/console-conversion.js)。后端 HTTP 入口：[server.py](apps/server.py)；离线转换：[dataset_conversion.py](apps/dataset_conversion.py) 与 [conversion_worker.py](apps/conversion_worker.py)。

| 接口范围 | 路径 | 当前实现状态 / 后续用途 |
| --- | --- | --- |
| 状态快照 | `GET /api/v1/console/snapshot` | 待实现；BMS 电量、具名关节、三相机/服务状态、能力与控制源 |
| 自检 | `POST /api/v1/console/self-check` | 待实现；真实只读检查及阻塞原因 |
| SONIC 准备 | `POST /api/v1/console/deployment/jobs`、`GET .../{job_id}` | 待实现；分步启动、进度和取消；准备阶段 `allow_motion:false` |
| 整机 / 全身控制 | `POST /api/v1/console/robot/commands` | 待实现；连接、初始化、模式、控制权与受限目标 |
| 两层推理 | `POST /api/v1/console/inference/commands` | 待实现；模型握手、开始/停止及 SONIC 动作适配 |
| PICO 数据采集 | `POST /api/v1/console/collection/commands` | 待实现；准备、录制、保存/舍弃和结束 |
| 服务管理 / 停止 | `POST /api/v1/console/services/actions`、`POST /api/v1/console/safety/stop` | 待实现；服务依赖、所有权与停止策略 |
| 状态机执行 | `POST /api/v1/console/workflows/runs`、`GET .../{run_id}` | 待实现；后台提交/取消、节点状态、超时和分支 |
| 关节序列回放 | `GET /api/v1/console/episodes/timeseries` | 待实现；同视频时间轴的具名 State/Action 序列 |
| 现有数据查询 | `/api/collection`、`/api/episodes`、`/api/episodes/review`、`/api/episodes/video`、`/api/episodes/rate` | 已实现；目录、片段、视频播放/Range 与评级 |
| 离线数据转换 | `/api/conversions/sources`、`/inspect`、`/jobs`、`/jobs/{id}`、`/jobs/{id}/cancel`、`/jobs/{id}/download` | 已实现；预检、HDF5/LeRobot v2.1 导出、进度/取消、历史和下载 |

设备命令公共约定为 `action, mode, profile_id, expected_revision, payload`，附 `Idempotency-Key`；精确字段以 OpenAPI 为准。后端必须再次校验能力、控制源、任务互斥、状态版本与就绪条件。受理与就绪分开，运动命令不自动重试。快照缺失/过期时不显示虚构电量或反馈：关节状态 TTL 5 秒，电量 TTL 15 秒；29 维可视化顺序不是 DDS motor index。

本次只读复核：`/healthz` 和 `/api/conversions/sources` 返回 200；`/api/v1/console/snapshot` 返回 404，符合设备 v1 尚未实现的现状。前端仅回退现有数据查询，不回退旧 `/api/stack/*` 或 `/api/record/*` 控制接口。

### 已完成的规划项

- 九页前端：两层推理、自检与启动、整机管理、全身控制、三相机传感器、独立采集、同步回放、数据转换、状态机编辑器。
- 全局电池显示、真实 G1 URDF/STL 的 3D 渲染、29 身体关节分组/目标本地预览；三视频播放器与视频/曲线/姿态联动的前端机制。
- 状态机编辑、参数/分支配置、JSON 导入导出、本地保存与有界本地试运行。
- 完整前端接口调用层、状态/错误/断连显示、隔离的界面预演和上述接口合同。
- 现有数据目录/片段/评级/视频接口；离线 HDF5 与 LeRobot v2.1 转换前后端。原生 SONIC VLA 数据已是 LeRobot v2.1，转换成 LeRobot 当前为校验并另存完整副本；HDF5 为通用 `sonic-hdf5-v1`，训练器专用布局需另作映射。
- 4070 Web 入口已配置为 `http://192.168.123.100:9999/`；网口持久地址与管理网络安排见 0A 节。Mac 当前转发入口为 `http://127.0.0.1:12947/`。
- 历次验证已通过：前端 16 项、原后端 19 项、转换 15 项；合成片段和浏览器预演不等于真机验收。SONIC SDK、PC Service、Unity 与 Docker 合成 IDLE 验证另见 [sonic_deploy/HANDOFF.md](../sonic_deploy/HANDOFF.md)。

### 尚未完成：按后续推进顺序

| 顺序 | 工作 | 尚需开发 / 现场验收内容 |
| --- | --- | --- |
| 1 | 只读状态接入 | 实现 `snapshot`/自检，接 G1 BMS、29 个具名身体关节、服务和 PICO 输入源；现场核实消息字段、时间戳和掉线行为 |
| 2 | 三路真实相机 | 实现视频服务/同源代理与状态接入；现场核实 head/left_wrist/right_wrist 设备映射、帧率、时钟、断流重连及同步录像 |
| 3 | 网页 SONIC 全流程启动 | 实现 Docker/PC Service/引擎分步任务、日志、复用、取消与失败恢复；已有命令行运行验证尚未变成网页启动后端 |
| 4 | 整机控制与停止 | 实现唯一控制源、初始化配置、模式、接管/释放、目标限制与停止；处理现有 `SonicAdapter` 的 5580 端口所有权；现场验证实际行为 |
| 5 | 真实采集闭环 | 接入新的采集命令服务；现场完成 PICO 4 + 腿部追踪器标定，验证开始→保存/舍弃→三路视频与完整状态/动作落盘 |
| 6 | 正式数据回放与转换验收 | 实现真实 `episodes/timeseries`，核对视频、关节曲线和 3D 同步；用首段正式采集数据验证 HDF5/LeRobot 输出。当前正式片段为 0，演示元数据不能用于该验收 |
| 7 | 两层真实推理 | 实现模型服务握手与任务执行，明确动作名称、维度、单位、坐标、频率，适配后交给 SONIC；验证采集/推理互斥与停止 |
| 8 | 后台状态机与部署验收 | 实现真实节点执行器、进度、超时/取消/分支，贯通准备→等待→采集或推理→停止；按接入说明落实服务端校验及认证授权，再完成断连/恢复验收 |

其中接口服务、任务管理、动作适配和状态机执行器仍可继续远程开发；真实消息与视频、PICO 标定、网络实际互通及机器人行为必须到现场核实。现场还需确认两个网段可达、`.100` 无地址冲突、有线链路接通后服务可启动。后续目标是完成这些后端与验收项，无需重做现有页面。

此节只更新交接文档，未启动设备任务、采集、推理或机器人运动。

## 0B. 2026-10-16 新增“数据转换”：前后端已实现

- 侧栏在“数据回放”下新增“数据转换”，入口 **http://192.168.123.100:9999/#conversion**，Mac 转发仍可用 http://127.0.0.1:12947/#conversion。
- 已核对当前 SONIC `gear_sonic/scripts/run_data_exporter.py`、`gear_sonic/data/exporter.py` 和 `scripts/process_dataset.py`：VLA 采集原生为 **LeRobot v2.1**，即 Parquet 数值帧 + MP4 视频 + meta JSON/JSONL，附 GR00T modality 和 script_config。C++ `StateLogger` 的分信号 CSV 是单独调试日志，不等于完整训练数据集。
- 实际离线后端已完成，不依赖待接入的设备 v1 API：来源列表/预检、HDF5 与 LeRobot v2.1 完整副本导出、单任务进度/取消/历史、结果路径和文件 Range 下载。只允许读取 SONIC outputs 的直接数据集目录，输出到 `outputs/conversions/<新名称>/`，不覆盖、不删除、不重采样源数据。
- HDF5 使用明确的 `sonic-hdf5-v1` 布局：每片段一个 .hdf5，`/frames/<原始字段>` 保留原始形状/类型/时间戳，`/videos/<原始相机键>/encoded_mp4` 内嵌原 MP4 字节，或选择 `/videos/<...>/rgb` 逐帧 RGB；`/meta` 含字段/任务/模态/机器人配置。不是 ACT/Robomimic 专用字段布局；如训练器要求另一 schema 需另行映射。完整状态/动作可能包含手部（例如 43 维），绝不截成网页 29 身体关节。
- LeRobot 目标就是校验原生 v2.1 并另存完整副本，保留原 Parquet、MP4、元数据与舍弃标记；不声称完成 v3 升级。当前不支持 debug CSV 自动补齐相机/任务，也不支持 LeRobot v3 输入。
- 后台使用独立 `apps/.venv_conversion`（numpy 2.2.6、pyarrow 19.0.1、h5py 3.13.0），ffmpeg/ffprobe 复用系统安装；未改 SONIC teleop 环境。安装入口 `bash scripts/install_conversion.sh`，依赖文件 `apps/requirements-conversion.txt`；venv 已加入 .gitignore。
- 主要新增：`apps/dataset_conversion.py`、`apps/conversion_worker.py`、`apps/static/console-conversion.js`、`apps/tests/test_dataset_conversion.py`；`apps/server.py` 新增 `/api/conversions/*` 路由。`console-core.js/console.js/console.css` 增加第九页和导航。OpenAPI 已更新为 22 路径、30 模式；设备执行 v1 部分仍待现场实现，离线转换 API 已实现。
- 校验：15 项转换测试通过（含 43 维、数值/时间戳、三视频原字节/RGB、LeRobot 原文件 SHA 一致、元数据、取消、路径边界、并发拒绝、缺帧/帧率/字段异常及 HTTP Range）；原后端 19 项、前端 16 项仍通过。测试使用独立 /tmp 合成片段，不占用真实采集通道，不计入正式统计。
- 当前正式采集仍 0，十个演示目录只有元数据/稀疏占位文件，预检会禁用真实转换；不能把它们导出后当正式数据。界面预演可操作转换进度，但明确不生成文件。等正式 SONIC 片段保存完整后即可选择导出，真实硬件采集验收仍待现场。
- 源文件变化通过 fingerprint 拒绝/中止；转换期间应保持来源静止。失败/取消的部分输出保留 `.incomplete`，成功才开放结果下载；原目录不修改。
- 改动前备份 `.local-backups/data-conversion-20261016-182900/`；只重启 apps Web 服务，未启动机器人/相机/真实采集或模型，未提交推送。

## 0A. 2026-10-16 18:24 网页固定入口与有线地址

- 用户已指定 Robot Station 使用 **http://192.168.123.100:9999/**。已将 4070 有线口 `eno1` 配置为 `192.168.123.100/24`，无网关；默认路由继续经 Wi-Fi，不改动管理网络。
- NetworkManager 新增持久配置 `robot-station-g1`，绑定 `eno1`，自动连接优先级 999、`ipv4.never-default=yes`。旧 `Profile 2`（192.168.123.88）保留，优先级 0。现场插线后应选择新的 .100 配置，不要恢复旧 .88。
- 当前有线口仍 `NO-CARRIER`；为本次无接线的本机调试已给接口临时添加同一地址。重启后持久配置在有线链路接通时自动生效；局域网访问和地址冲突检查须在接线后验证，不能把本机 HTTP 成功当作现场网络已通。
- `scripts/apps.sh`、`apps/run.sh` 和 `apps/server.py` 默认监听改为 **192.168.123.100:9999**。启动健康检查改用实际监听地址，不再固定查询 127.0.0.1。`DATA_PLATFORM_HOST/PORT` 环境覆盖仍可使用。
- 已重启同一个 apps Web 服务，实际监听、本机 `/healthz`、首页和 console.js 均返回 200，未触发机器人或采集程序。
- 本会话 Mac 转发仍使用 `127.0.0.1:12947`，目标已更新为 **4070 的 192.168.123.100:9999**。重新建立可用 `ssh -N -L 12947:192.168.123.100:9999 harry@100.104.144.88`。
- 现场同网段浏览器打开指定入口；G1 保持用户提供的 192.168.123.164，网页绑定地址与 SONIC/DDS 绑定网卡分别维护。
- 修改前备份：`.local-backups/console-address-20261016-182351/`。未改动真实控制/模型接口，未提交或推送。

## 0. 2026-10-16 本轮完成：前端先行，设备后端留待现场联调

用户最新授权：“可以先把前端实现好，接口留好，到时后端可能需要去到线下调试”。已在现有 `apps/` 入口完成并部署统一前端，不另建 SONIC 网页；下文此前“未开始前端实现”的陈述仅代表早先只读阶段。

- 八页已实现：两层推理、自检/启动向导、整机管理、29 关节全身控制、三相机传感器、独立采集、同步数据回放、可编辑状态机。全局 G1 电池图标/百分比、低电量与过期未知状态已完成。
- 使用实际 SONIC G1 URDF 层级、29 个具名身体关节及 50 个 STL 渲染 3D；参考姿态、目标本地预览和反馈姿态明确区分。原模型含手指，但身体控制只取 29 维，不能将其顺序直接当 DDS motor index。
- 可选“界面预演”包含三路合成测试视频、合成电量/姿态、推理/采集/流程交互及断连/断流场景，所有操作仅作用浏览器，不发送设备命令或写真实采集目录。正常入口默认离线/未知，不把预演冒充真实数据。
- 复用旧只读目录/片段/录像接口和评级元数据接口；正式片段仍为 0，演示 1075。新前端不调用旧 stack/record 控制 POST，也不读取 overview 的演示遥测。
- v1 控制接口**尚未实现**，由 `capabilities.commands` 和就绪条件门控；没有通过此次前端工作启动 Docker、真实采集、模型执行或机器人运动。PICO/G1/相机/动作适配、真机停止与故障恢复待现场验收。
- 主代码：`apps/static/index.html`、`console.css`、`console*.js`；资源：`assets/g1/`、`assets/preview/`、本地 Three.js/STLLoader 与许可证。旧 `app.js/styles.css/collection.js/collection.css` 保留但不再加载。
- 后端接入合同：`apps/contracts/console-v1.openapi.json`（OpenAPI 3.1，16 路径、25 模式），生成器同目录。覆盖新鲜度/BMS/具名关节、能力、异步部署、受控命令、模型握手、互斥采集、后台流程运行/取消/节点状态和回放序列。
- 验证：前端 `apps/tests/console.test.mjs` 16 项通过；现有 Python 后端 19 项通过。浏览器验证八页、两层预演推理、采集保存、三视频同钟（均 6 秒）、3D、低电量/断流/断连、状态机编辑/保存/流转，以及现有目录和分页。320 px 八页无横向溢出，另验 390/768/1024/1440 px，未发现脚本错误。
- 运行入口已按第 0A 节更新为 `192.168.123.100:9999`；Mac SSH 转发仍为 `12947`。首页 `/#inference`，预演 `/?preview=1#inference`。静态改版未重启服务；无需在 4070 安装 Node。
- 旧静态文件/服务/文档备份：`.local-backups/console-frontend-20261016-173234/`。本轮保留两库原有未提交改动，没有提交或推送。
- 详细接入顺序与文件职责：[docs/data_collection_console.md](docs/data_collection_console.md)。截图：[推理工作台](docs/references/console-v1-20261016/inference-preview.jpg)、[G1 全身模型](docs/references/console-v1-20261016/g1-body-preview.jpg)。两图明确标记合成预演。

## 1. 用户已确认的目标与边界

- 开发机：`harry@100.104.144.88`，项目根目录 `/home/harry/workspace/robot_station`。
- 通用的“推理 + 数据采集”网页与操作 API 直接维护在 `robot_station/apps/`，不再建立 `apps/sonic/`，不把产品名称限定为 SONIC，后续可接入其他机器人。
- 同级 `/home/harry/workspace/sonic_deploy` 负责 SONIC 机器人程序、运行环境、模型与原始采集输出。
- 用户最新（2026-10-16）要求 **Robot Station 前端统一承载 SONIC 的完整引导启动、三路视频、采集、回放、状态机与推理操作**；`sonic_deploy` 提供实际程序、环境、Docker 和执行能力。此前另设独立部署网页的安排按这次统一操作台目标衔接，具体服务接口尚未实现。
- 最新主要样式参考是 **`http://192.168.10.46:9999/`**；之前 `.45:8090` 采集页和 `.102:8894` 回放页保留为辅助参考。前端已参考其布局完成；G1 动作合同独立，不复用参考站 H1 设备协议。
- 早先只读审查已结束；用户随后授权前端先实现、设备后端留到现场，本轮完成情况见第 0 节。

另一项目的接续入口：[sonic_deploy/HANDOFF.md](../sonic_deploy/HANDOFF.md)。

### 2026-10-16 最新需求与本轮只读审查

用户原始目标：前端提供 SONIC 启动全流程的简单引导，能看到三路视频帧；可开启数据采集、查看采集数据回放、开启推理。明确提出自检、整机管理/查状态、全身控制（询问 G1 29 维关节接管是否容易）、传感器（三路相机）、数据回放、状态机编辑器，**最重要的是推理页**，且推理与采集要分开。

后续默认继续维护 `apps/` 的通用界面/API，原 `frontend/`、`backend/`、`modules/` 作为可审查的复用来源。本轮继续使用现有 apps 完成前端，设备后端尚未对接。统一入口的需求已同步写入 `sonic_deploy/HANDOFF.md`。

- 当前代码/服务证据：4070 `/home/harry/workspace/robot_station` 可访问，apps Web PID 58735 运行，`/healthz` 返回 ok。通过本机 SSH 转发 `127.0.0.1:12947 -> 4070:2947` 实际查看采集页；当前为 idle，真实片段 0，演示片段 1075，启动受数据采集环境/tmux 缺项阻塞，相机/PICO/机器人/导出均未连接。未点击启动、录制、保存、丢弃或设备操作。
- 可复用基础：`apps/collection_workspace.py` 与现有采集 API 的场景、片段查询、评级、MP4 Range/多路回看；原模块提供自检、状态机、推理 WebSocket 会话等实现线索。现有 apps 没有完整推理/状态机/SONIC Docker 引导 API，不能只画按钮就称已接通。
- 当前接口缺口：`apps/sonic_adapter.py` 仍调用官方采集 launcher 并持有 5580；旧推理 observation/validation 使用双臂 7+7 及平台/升降语义，不能直接按 G1 29 维使用。需统一任务控制权和运行适配，先明确推理模型 observation/action 合同，再映射到 SONIC/G1。
- 页面需求整理（待用户后续实现指令）：自检/启动向导；整机管理（连接、状态新鲜度、服务/控制源、仿真/真机与使能阶段）；G1 全身控制/状态；三路相机传感器；PICO 遥操作采集；视频/关节数据可视化回放；状态机编辑器；重点推理工作台。常驻全局状态、当前任务/控制权、停止任务和诊断信息，三路视频组件在相关页面共享。
- 2026-10-16 用户补充：Robot Station 必须可视化显示 **G1 机器人电池电量**。全局顶部常驻电池图标与电量百分比；整机管理展示数据更新时间和来源，低电量按可配置阈值变色提示。使用真实 BMS/机器人状态数据，实际消息字段与接入端点尚待确认；掉线、缺失或过期数据显示 `-- / 未连接 / 数据过期`，不得用演示值或无时间标记的旧值假装实时电量。电量前端现已完成，真实 BMS 数据接入仍待后端实现。
- G1 控制可行性说明：29 维身体关节的状态展示与模型可视化可实现；手部/夹爪按实际配置另建能力。真正的全身接管要由 SONIC/执行端的稳定控制循环完成，网页提交受控目标和模式切换；不能沿用 H1 双臂协议或将 29 个滑条直接当作行走控制。优先只读反馈、仿真与受限动作，现场验收前保持真实控制不可用。
- 采集与推理分开：至少分别呈现任务配置、运行状态和控制入口，并明确唯一运动控制源。推理过程若允许附带录制，应将记录来源标为 inference，不能把“采集任务”与“推理执行”混成一个按钮；具体业务语义待后续细化。
- 状态机编辑器目标：可配置准备、等待就绪、采集开始/保存、推理运行/停止等节点及成功/失败/停止分支；流程编排与运行态可视化分开，节点能力按机器人实际支持暴露。当前参考站含 H1、升降、导航等节点，不原样搬入 G1 页面。
- **推理页已确认（2026-10-16 用户重新选择）：“两层都要：任务模型推理与 SONIC 全身控制分区显示”。** 用户此前的单选“任务模型推理”已明确撤回，不作为需求结论。第一版需要同时呈现上层任务模型和下层 SONIC 执行的配置、运行状态与操作。
- 上层任务模型区：三路相机/机器人状态输入、任务指令、模型或推理服务连接、任务开始/停止、动作输出与时延/进度。下层 SONIC 区：Docker/引擎/控制器状态、输入源与当前模式、G1 身体 29 关节反馈、控制权与使能阶段、接管/释放/停止。两个分区分别报告真实就绪状态，不能把“模型连上”当作“机器人已可执行”。
- 期望执行链路为“相机+状态+任务指令 → 上层模型 → 动作语义/维度/坐标/频率适配与校验 → SONIC → G1”，适配合同尚未实现，不假定任意任务模型都能直接输出 SONIC 可接收的 G1 目标。状态机后续编排两层的准备、等待、运行和停止，保持唯一运动控制源。
- 参考站已在浏览器重新查看：自检、整机管理、推理及展开参数、传感器、数据回放、状态机。参考站推理显式显示 H1 RTC 动作协议，三路相机回显关闭；回放页说明其“数据回放”会执行机器人动作，新需求中的**可视化回放默认应只查看视频/状态/动作数据**，实机动作复现必须另列能力。没有修改参考站配置或触发任何设备/任务操作。
- 最新 SONIC 状态以其 HANDOFF 为准：SDK/PC Service/Unity 已安装并从项目运行，真实 Unity 窗口已截图；Docker/模型与合成 IDLE 仿真闭环已验证。PICO 4+腿部追踪器已确认、APK 已缓存；真实 PICO/G1 与三相机、断流/重连验收尚未完成。原旧交接中“没有 C++ build/PC Service 未启动”等描述为历史检查结果，不再作为当前结论。

## 2. 目前目录与入口

```text
/home/harry/workspace/
├── robot_station/
│   ├── HANDOFF.md
│   ├── apps/
│   │   ├── server.py                 # 当前工作台 HTTP API / 静态资源
│   │   ├── collection_workspace.py   # LeRobot 片段、评级、视频定位
│   │   ├── sonic_adapter.py          # 当前唯一机器人适配器
│   │   ├── static/
│   │   │   ├── index.html
│   │   │   ├── app.js
│   │   │   ├── styles.css
│   │   │   ├── collection.js
│   │   │   └── collection.css
│   │   ├── tests/
│   │   └── .runtime/                 # 会话配置、评级、PID、日志，忽略提交
│   ├── scripts/apps.sh
│   ├── run.sh                        # apps 子命令与原 ROS 工作站入口
│   ├── frontend/、backend/、modules/、ros_packages/  # 原工作站代码
│   └── docs/
└── sonic_deploy/
    ├── HANDOFF.md
    ├── gear_sonic/、gear_sonic_deploy/
    └── outputs/
```

原 `Data_platform` 已完整移动到 `apps/`，包含隐藏文件和运行数据；旧顶层目录与中间的 `apps/sonic` 均不存在。原始采集输出没有移动。代码备份位于 `.local-backups/Data_platform-20261015/`，不提交 Git。

当前工作台运行入口：

```bash
cd /home/harry/workspace/robot_station
./run.sh apps status
./run.sh apps start
# 其他操作：./run.sh apps stop | restart | logs | foreground
```

也可在 `apps/` 下执行 `./run.sh` 前台运行界面。Web 默认监听开发机 `192.168.123.100:9999`；Mac 转发 `12947 -> 4070:192.168.123.100:9999` 后访问 `http://127.0.0.1:12947/#inference`。

**区分入口**：根目录不带参数的 `./run.sh` 仍是原 ROS 工作站启动器，默认 Web 9999 / 控制 9998，并包含进程清理和构建逻辑；不要把它误当作仅启动 apps 的命令。

## 3. 已实现与已验证

上一轮已完成迁移及采集页改造：浅灰底、白色卡片、蓝色主操作；场景/目录、采集状态、任务与设备状态、分组记录四个区域。产品标题为“数据采集工作台”。

- 日期和场景在未指定名称时生成 `YYYYMMDD_sceneN`；“应用”只保存配置，不启动采集。
- 设备与环境检查读取真实端点/前置项；端口在线不等于真实相机画面或机器人反馈有效。
- 从 `sonic_deploy/outputs/*/meta/info.json`、`episodes.jsonl` 查询记录，支持分页、名称搜索和演示记录筛选。
- 人工 A/B/F 评级写入 `apps/.runtime/episode-reviews.json`，不覆盖原始 LeRobot 元数据；默认未评级。
- 多路 MP4 查看、同步播放控件、拖动和倍速；视频 HTTP 支持 Range。现有演示记录没有视频时显示明确空状态。
- 前一轮在本机及 `.88` 上均通过 **19 项后端测试**。真实网页只读检查覆盖记录分页 30 -> 60、搜索、无视频状态、模式切换及六个页面导航；在 1500 / 1280 / 900 / 768 / 390 / 320 px 屏宽未发现页面横向溢出。
- 没有通过网页启动机器人、Docker、采集或发送运动指令；上述验证不代表完整真机链路已验收。

本轮重新查询：apps 服务运行；真实保存片段 **0**，演示片段 **1075**。不要将演示记录计入真实采集成果。

接口与启动说明详见 [docs/data_collection_console.md](docs/data_collection_console.md)。主要新增接口为 `/api/collection`、`/api/collection/config`、`/api/episodes`、`/api/episodes/rate`、`/api/episodes/review`、`/api/episodes/video`；原 stack / record / datasets 接口保持兼容。

## 4. 最新参考站：192.168.10.46:9999

已通过 `.99` 开发机转发访问，在浏览器查看了“自检、推理、传感器、数据回放”并查看双手任务的前端配置区域。未点击检查、服务启停、连接推理、执行动作、评级或删除；观察到的 HTTP 请求均为只读请求。

- 页面名称 Robot Station；左侧约 **220 px 深色导航**，顶部全局状态，右侧浅灰内容区和白色卡片。
- 顶栏包含 ROS、Camera、LiDAR & Odom、电量、时钟和“停止任务”。这些是参考站的设备能力，不应原样硬编码到其他机器人。
- 推理页为“左侧运行配置、右侧推理状态”两栏；任务形态包括单手/双手，Prompt 包括顺序执行、货架选物/搜索、自定义；双手包含连续协同与依次执行。
- 配置区包含录制开关、同步/RTC 模式、远端地址与运行参数；顶部有连接/断开/停止与 A/B/F/放弃。
- 三路相机实际在“传感器”页：头部大画面 + 右侧上下排列的左腕、右腕画面。观察时回显关闭，未验证真实图像。
- 自检页包含总览、阻塞/警告计数、放行检查与运行准备；回放页包含载入、回放控制和 State / Action 曲线。
- 参考站服务状态 API 报告运行环境内目录 **`/workspace/robot_station`**。这是 HTTP 返回的 cwd/配置路径；未 SSH 登录 `.46`，未核实宿主机挂载路径。
- 观察时出现 `Cannot read properties of undefined (reading 'rackGroups')` 浏览器错误；原因未定位，不修改参考站，也不把该现象当作新项目要复制的行为。

完整样式笔记、截图与接口线索：[docs/references/station-9999-20261015/README.md](docs/references/station-9999-20261015/README.md)。

## 5. 当前限制与下一轮切入点

1. 前端功能与预演已完成，真实 v1 执行端尚未实现。先接 `snapshot`（BMS、29 具名关节、服务/输入源和三相机帧时间），然后按 OpenAPI 实现准备任务、控制权、初始化和停止。
2. 当前 `sonic_adapter.py` 仍直接启动旧官方 launcher 并持有 5580，不是 Docker 阶段编排服务。新前端不会调用该旧控制入口；后续需统一进程/控制端所有权。
3. 任务模型输出必须完成动作语义、维度、单位、坐标、频率适配与限幅后才可开放推理。旧 H1 双臂协议不可直接套用到 G1。
4. 三路真实相机、PICO 4 与腿部追踪器标定、真实采集/回放序列、整机初始化/运动和故障恢复均待现场联调。前端合成故障预演不能替代 SONIC 异常保护验证。
5. 后台流程运行/取消/节点状态合同已留好，实际节点执行器待实现。本地流程保存仅存在当前浏览器，导出 JSON 可迁移。
6. XRoboToolkit SDK/PC Service/Unity、Docker 与合成 IDLE 的已验证状态以 `sonic_deploy/HANDOFF.md` 为准，不沿用早先“PC Service 未启动/SDK 路径未修”的历史结论。

## 6. Git 与接续检查

本轮开始时分支 `main`，HEAD `f27fb9f`。上轮迁移尚未提交：`.gitignore`、`README.md`、`run.sh` 有修改，`apps/`、`scripts/apps.sh`、`docs/data_collection_console.md` 为新增。保留这些改动，未自动提交或推送。

```bash
cd /home/harry/workspace/robot_station
git status --short
./run.sh apps status
curl --noproxy '*' -sS http://192.168.123.100:9999/healthz
```

需要验证应用后端时，使用当前环境在 `apps/` 中运行 `../../sonic_deploy/.venv_teleop/bin/python -m unittest discover -s tests -v`。文档编辑不需要反复启动硬件或运行整套 ROS 工作站。

后续每轮在本文件更新用户最新决定、已实施文件、验证证据、未完成项与下一步；涉及执行端接口变化时同步更新另一项目 HANDOFF。文件中不保存密码、令牌、认证码或其他凭据。

数据转换浏览器验收补充（2026-10-16）：侧栏入口、真实来源阻止演示转换、HDF5/LeRobot 选项、进度/取消、本地预演与展开字段保持均已检查。新增页在 320 px 和默认 1280 px 无横向溢出；截图见 docs/references/console-v1-20261016/data-conversion-preview.jpg（合成预演）。
