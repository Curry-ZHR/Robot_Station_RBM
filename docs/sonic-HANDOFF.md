# SONIC 执行端与部署网页开发交接

最后更新：2026-10-20，Asia/Shanghai。此文件记录当前实测状态和用户最新方向；旧安装记录仅作为历史参考。

## 0K. 2026-10-20 Robot Station托管SONIC控制器与反馈

同级Robot Station已接入SONIC控制器仿真/真机托管启动、协议正常停止、实际反馈/测量关节与日志，详见`../robot_station/docs/sonic_controller.md`及其HANDOFF第0S节。网页不再只是容器/XR启停入口。启动和停止仅管理本项目精确进程，独立SDK关节控制与跨模式会话互斥；不开机自启运动，不自动从手动姿态交接。

本目录`gear_sonic/scripts/pico_manager_thread_server.py`只增加可选`--bind-host`参数；原CLI默认`*`保留，托管模式用127.0.0.1私有上游，由工作台代理转发原协议。固定hash安装器及可复现源码在Robot Station的`integrations/sonic`，原始源已备份于`.local-backups/station-manager-bind-20261020-100328`。未修改C++控制策略、SDK或模型权重。

有效反馈以原`g1_debug.index`递增、cpp标识、29维有限测量及≤500ms帧龄判断，合法的ZMQ ros_timestamp=0不会被当冻结；robot_config只作配置心跳。进程/初始化/策略反馈分别显示。PICO追踪、Manager/反馈断流或网页父进程丢失会请求正常stop并核对退出。

实际Docker/C++ TensorRT/MuJoCo在lo/DDS0、临时回环端口及合成IDLE输入下，6种正常/异常停止场景全部通过，均确认C++正常退出；HTTP等待PICO与停止闭环也通过。未向真机下发动作、没有有效SONIC现场批准。真机启动会默认站姿/Dex3手部动作，需独立SONIC专项现场验收，不能以既有SDK标定替代。PICO4+腿部追踪及G1现场全链路仍待验证。

## 0J. 2026-10-20 工作台基础服务停止与XR生命周期扩展完成

Robot Station已接入本项目待命容器与XRoboToolkit的实际停止，跨模式采集/手动/准备、SONIC控制或遥操作进程占用时拒绝。容器按项目归属和不可变ID核验后停止；XR按完整路径/用户/启动时间/pidfd停止PC Service及Unity，确认退出才成功，不停止其他安装，不对XR自动强杀。

共享`gear_sonic/utils/teleop/xrobotoolkit_runtime.py`新增`run_xrobotoolkit.sh stop`，停止标记在`outputs/xrobotoolkit/service.stopped`，阻止隐式ensure_service重启；显式service/3d恢复。源码与升级安装器随同级Robot Station的 [integrations/sonic](../robot_station/integrations/sonic/README.md) 维护，已在本机安装并保留旧源备份；用户本轮只要求提交Robot Station仓库。

112项后端、19项前端通过，4070真实HTTP stop/start、容器/进程/gRPC/Unity及隐式重启阻止均通过，最终恢复待命容器、PC Service及Unity。SONIC控制器始终离线，未执行机器人运动。OpenAPI1.6.0；详见 [服务启停说明](../robot_station/docs/service_lifecycle.md) 与 [主handoff第0P节](../robot_station/HANDOFF.md)。HPC/4090/4070推理分工仍为后续计划，自动姿态交接继续暂缓。

## 0I. 2026-10-20 后续分工：4070统一接入，G1侧token执行为目标

用户确定大模型可在HPC、4090或当前4070推理，4070固定承担网页、相机/采集、观测上传与动作调度，目标由G1侧兼容SONIC执行器接收motion token和配套手部动作；遥操作采集与推理统一执行入口，尽量复用G1既有板卡/系统。详细计划在 [Robot Station/handoff_distribution.md](../robot_station/handoff_distribution.md)，主handoff第0N节有摘要。

该分工尚未实施：现有4070运行SONIC/C++的路径向G1发送底层DDS电机命令；让G1接token须核验/部署G1侧SONIC解码执行器，不能把token当作原厂电机接口。当前GR00T环境能导入并使用CUDA，但未发现权重/运行服务，HPC/4090/本机完整推理均未验收。本次仅写文档，不迁移控制器或启用运动；自动姿态交接仍按0H暂缓。

## 0H. 2026-10-20 范围调整：SONIC 自行初始化，暂缓手动姿态自动交接

用户说明SONIC运动程序启动时会自行进入初始姿态，因此暂不开发“工作台先设置初始姿态，再交给SONIC”的自动交接，不再将其列为当前交付缺项。独立SDK滑条与姿态库继续用于SONIC未运行时的链路验证、机械支撑下关节调试；预先应用工作台姿态不是SONIC启动必经步骤。启动SONIC运动前仍须结束独立手动控制并确认停止发布，保持唯一控制源；不新增无缝交接或自动抢占。SONIC自身启动动作按用户说明记录，未实机验证；Docker/网页准备仍为allow_motion:false，不自动触发初始化。真实反馈、标定与停止行为仍待现场。此节覆盖0A及其他旧节中的自动交接待办，详见 [Robot Station handoff第0M节](../robot_station/HANDOFF.md)。

## 0G. 2026-10-20 最终交付须检查 Ubuntu .deb 安装包

用户要求将Robot Station的 `.deb` 安装包列入最终交付待办：**当前待制作，未生成、验收或上传，本次仅记录与设置提醒。** 整体开发完成或准备收尾/交付时，若尚无已验收安装包，主动提醒用户“功能开发已完成，Ubuntu .deb 安装包仍待制作/验收”。单个功能完成不触发项目收尾提醒。不要将run.sh或源码目录当成已交付安装包；产物和干净环境验收清单见 [Robot Station handoff第0L节](../robot_station/HANDOFF.md) 与 [分发方案](../robot_station/docs/distribution_plan.md)。

## 0F. 2026-10-20 独立真机SDK适配已接入，现场标定未完成

用户确认完整29自由度且腰部未锁定。同级Robot Station完成HG/PR LowCmd、官方CRC/索引、连续轨迹及边界、控制源互斥、反馈/租约看护、受支撑场景停止流程和本地标定门槛；网页增加标定状态。SDK依据commit `4141c34280abb67c82e115342a8720f4a83d750d`。不自动释放Unitree模式、归零、平衡或接管SONIC；开机不会创建LowCmd发布器。

当前标定文件approved=false，没有实际运动/增益/停止验收，也未收到本台G1反馈。下一步在现场机械支撑及硬件停机保障下核验；软件不能把SDK示例增益冒充标定结果。接口OpenAPI1.5.0，软件/SDK/IPC/仿真126项检查；详见 [Robot Station最新handoff第0K节](../robot_station/HANDOFF.md) 和 [SDK适配说明](../robot_station/docs/g1_sdk_adapter.md)。最终Ubuntu安装包打包分发放在功能稳定后，当前未生成/上传。

## 0E. 2026-10-19 工作台常驻服务与离线物理控制完成

Robot Station 已增加连接配置/方案/备份恢复、ROS/G1/BMS链路诊断与脱敏ZIP、命名姿态库和平滑轨迹、独立固定基座MuJoCo物理控制（滑条实时联动、手动租约、限位/限速、到位反馈），以及根目录 `run.sh` / `stop.sh`。`robot-station.service` 已启用，harry用户驻留已开启；开机启动网页与只读服务，不启动任何机器人运动、仿真初始化、采集或推理。旧Robot Station ROS入口保留为 `run_legacy_ros.sh`。本项目的SONIC启动器未改成自动运动。

真机LowCmd关节驱动与停止/支撑/SONIC交接仍待现场实现和验证，当前real运动API返回412，未创建DDS运动发布器。⑤采集质量评分暂不处理，任务模型推理及后台状态机执行继续后置。完整运行/接口/现场说明见 [Robot Station最新handoff](../robot_station/HANDOFF.md) 第0J节及 [运行说明](../robot_station/docs/station_operations.md)。当前证据为离线物理/ROS合成数据和服务恢复验收，不能替代本台G1现场验收。

## 0D. 2026-10-19 ROS 2 Domain 99 相机桥接已交付

同级 Robot Station 已完成 ROS 2 Image/CompressedImage → ComposedCamera 兼容 ZMQ msgpack/JPEG 桥接，real/sim 相机域均配置为 **99**，G1 SDK2 DDS 域仍为机器人原配置（默认 0）。桥接独立于 SONIC/G1/PICO 运行，正式进程当前等待默认三路 `/camera/{head|left_wrist|right_wrist}/image_raw`，这些是待现场替换/确认的默认话题，并非已发现真实设备。

工作台已接自有桥接启停、归属/复用、状态及配置显示；三路源时间戳/时钟、冻结和缺图校验后交给现有网页及官方导出器，不补造实时数据。ROS Humble 使用独立 `.venv_ros2_camera`，不改 SONIC teleop 环境。后端 74、ROS 通信 3、前端 17，共 **94 项通过**；包含真实 ROS 合成图像 → 官方三路录制 → 回放/HDF5 和 Web 重启恢复。正式数据仍 0，未启动机器人运动。

完整说明、当前配置和验收证据见 [Robot Station handoff 第 0I 节](../robot_station/HANDOFF.md) 与 [接入说明](../robot_station/docs/data_collection_console.md)。此节覆盖下文 0C 的“待桥接”历史状态；现场仍须确认相机实际 topic/type/QoS/时钟与网络，原始大帧跨网传输需核对带宽或使用压缩图像。

## 0C. 2026-10-19 三相机来源改为 ROS 2 订阅（规划，待桥接）

用户后续用 ROS 2 发布/订阅三路相机图像，`ROS_DOMAIN_ID=99` 为候选值，实际 topic、Image/CompressedImage 类型、QoS 和时钟待核对。计划独立相机桥接进程使用相机域，把 ROS 2 图像转换为现有 ComposedCamera 兼容 ZMQ 流，供 Robot Station 预览与官方 SONIC 导出器共用；当前仅 ZMQ 消费端已实现，ROS 2 桥接尚未开发。

G1 状态/BMS 的 SDK2 DDS 域保持机器人侧配置（当前默认 0），不全局切到相机域。相机预览不以 SONIC 运动控制在线为前提。相同 Domain ID 不会自动打通不同 VLAN，现场还要确认发现/路由、QoS、图像映射/颜色、帧率及时间同步。完整要求见 [Robot Station handoff](../robot_station/HANDOFF.md) 第 0H 节。本次仅记录方向，未修改网络、DDS 配置或运行服务。

## 0B. 2026-10-19 连接真机时独立读取电量

用户要求 Robot Station 连接真实 G1 后持续显示 BMS 电量，**不以 SONIC 控制器运行作为前提**，也不需要取得运动控制权。当前工作台已用 Unitree SDK2 Python 的 HG `BmsState_.soc` 做独立 DDS 订阅，页面每 2 秒刷新，缺失/过期显示未知；实际主题、QoS 和发布频率待本台 G1 现场核实。G1 HG LowState_ 不带 BMS 字段，不能直接套用 Go2 结构。

本轮真实快照仍无机器人/BMS 数据，有线口未接线或状态不可用，尚未完成实机验收。完整接口来源、当前代码和验收要求见 [Robot Station handoff](../robot_station/HANDOFF.md) 第 0G 节。本次没有启动机器人运动。

## 0A. 2026-10-19 历史需求：独立手动初始姿态后交给 SONIC

**后续状态：**独立SDK适配已按0F完成软件实现，真机标定待现场；自动交给SONIC的部分已按0H暂缓。下文保留历史需求，不作为当前自动交接待办。

用户希望在 **SONIC 未运行时**，Robot Station 通过独立 Unitree/G1 后端，把滑条/角度输入同时作用于 URDF 目标模型和 G1 真机，验证实际控制链路，设置并平滑应用初始姿态，再启动/接管 SONIC。默认仅本地预览；明确启用手动真机联动且取得控制权后，滑条连续更新目标，不需每次另点下发。应保留真实反馈与目标对照、初始姿态保存/加载及到位结果。

**这仍是待开发需求，当前网页只做本地目标预览，运动下发与接管后端没有开放。** 独立手动控制不依赖 PICO/SONIC 在线，但必须核实 Unitree 控制模式、G1 支撑/平衡方案和真机约束；URDF 零姿态不默认等于可用站立姿态。SONIC 接管前须停止并确认独立手动指令发布，避免两个控制器同时驱动；接管后滑条停止向真机下发。初始姿态与 SONIC 启动条件须现场验证，不保证任意姿态均可直接启动。

完整需求、接口待办和现场验收顺序见同级 [Robot Station handoff](../robot_station/HANDOFF.md) 第 0F 节。此前⑤推理、⑥后台状态机留待真机采集后的安排不变。本次只记录需求，没有启动机器人运动、调整 SONIC 程序或开放设备能力。

## 0. 2026-10-16 工作台①②③④后端完成（最新状态）

用户本轮要求按顺序完成①状态与自检、②SONIC 软件启动管理、③数据回放、④采集任务管理；⑤任务模型推理与⑥后台状态机执行留到真机连接并采集之后。本节覆盖下文“工作台 v1 尚未实现”等历史描述。

- 同级 Robot Station 的 v1 快照、自检、只读 G1 DDS/BMS、PICO 身体时间戳、SONIC/三相机接入、后台准备任务/日志/取消、具名 Parquet 回放和持久采集任务已实现。OpenAPI 版本 1.2.0，27 路径 / 33 数据结构。
- Docker 准备复用本项目 sonic-runtime.sh、已有镜像和容器；实际 C++ 构建、GPU/动态库/程序检查通过，PC Service 通过共享入口复用。准备固定 allow_motion:false；软件完成但设备缺失显示 waiting，不自动运行真机 deploy、初始化或运动接管。
- Robot Station 新建独立 apps/.venv_collection，官方 LeRobot 固定提交和 CPU PyTorch 2.6.0；已有 .venv_teleop / XRoboToolkit SDK 保留。锁定依赖和安装脚本在 Robot Station，重复安装入口验证通过。
- 官方导出器作为独立进程运行，通过明确的持久命令确认 prepare/start/save/discard/end。保存完整模型状态/动作（当前含手部为 43 维）和三路视频；舍弃保留原始数据并写官方标记；新后端不再使用旧 5580 键盘发布通道，不调用旧交互式 tmux launcher。
- 后端 68 项、前端 17 项验证通过。临时 loopback 合成输入实际跑通 HTTP 采集→三 MP4/Parquet→回放 API/浏览器三视频曲线/3D→HDF5，另验证 Web 服务以新进程恢复同一录制器、数据冻结处理和跨模式软件停止。测试均在 /tmp，不是物理 PICO/G1 验收，不写正式 outputs。
- 顶部停止仅取消本工作台准备并结束录制，明确 motion_stop_supported:false；机器人初始化、接管、关节目标与外部运动停止尚未开放。相机接入为读取现有发布流，硬件类型、设备 ID 和实际发布服务须现场核实。
- 正式片段仍为 0、演示 1075。现场仍需核实两个网段、G1 BMS 主题/状态、PICO 4 + 腿部追踪器标定、三相机映射/时钟/完整录像、初始化/控制权与运动停止，然后验收正式采集；⑤⑥继续按用户要求暂缓。

完整入口：[Robot Station 最新交接](../robot_station/HANDOFF.md)、[接口规范](../robot_station/apps/contracts/console-v1.openapi.json)、[后端接入说明](../robot_station/docs/data_collection_console.md)。固定地址仍为 http://192.168.123.100:9999/，Mac 转发为 http://127.0.0.1:12947/；没有在本轮启动真实机器人运动或真实任务推理。

## 1. 用户已确认的分工

- 开发机：`harry@100.104.144.88`；项目根目录 **`/home/harry/workspace/sonic_deploy`**。
- 本目录负责 SONIC 机器人程序、Docker、运行依赖、模型、相机/遥操作链路与采集输出。
- 用户最新（2026-10-16）要求由 **Robot Station 前端**承载 SONIC 的逐步启动、自检、三路视频、采集和推理操作；本目录维护实际执行程序与运行依赖。此前单独部署网页的安排按统一操作台目标重新衔接，具体模块接口待实施。
- 同级 **`robot_station/apps/`** 负责通用“推理 + 数据采集”的可视化界面和操作 API；不保留 `apps/sonic` 子目录，后续要接入其他机器人。
- 最新主要视觉参考为 `http://192.168.10.46:9999/`。已观察其自检、推理、传感器和回放页面；当前已按第 1 节最新交接完成前端；设备执行接口仍待实现，未启动真实机器人。后续按用户要求完成了以下 XRoboToolkit SDK 升级与路径修复。

通用工作台接续入口：[robot_station/HANDOFF.md](../robot_station/HANDOFF.md)。

### 2026-10-16 Robot Station 数据转换已实现（离线，无设备依赖）

统一工作台新增第九页“数据转换”，位于数据回放下，入口 http://192.168.123.100:9999/#conversion。核对官方 exporter：SONIC VLA 原生为 LeRobot v2.1（Parquet + MP4 + JSON/JSONL，附 GR00T modality/script_config）；C++ CSV 是单独调试日志。

已实现 v2.1 → SONIC 通用 HDF5（原始数组/时间戳 + 原 MP4 内嵌或 RGB）和 v2.1 完整副本导出，含预检、进度、取消、历史、文件下载。保留完整维度/手部与舍弃标记，HDF5 不默认等于 ACT/Robomimic 布局，v3/debug CSV 未适配。来源 outputs 只读，结果另存 `outputs/conversions/<新名称>/`，不覆盖现有目录；失败/取消留 .incomplete。

执行代码在同级 robot_station/apps/dataset_conversion.py、conversion_worker.py；独立 apps/.venv_conversion，不修改 .venv_teleop。15 项转换、19 项原后端、16 项前端测试通过，使用 /tmp 合成文件验证，未启动实际采集或机器人。当前十个演示目录缺 Parquet，真实片段仍 0，页面会阻止把演示元数据转换成正式成果。设备采集与动作链路仍待现场；转换功能本身已离线验证。更多接口与布局见 robot_station/HANDOFF.md 第 0B 节和 docs/data_collection_console.md。

### 2026-10-16 18:24 工作台地址已按用户指定配置

Robot Station 固定入口现为 **http://192.168.123.100:9999/**。4070 `eno1` 保存静态 `192.168.123.100/24`，NetworkManager 配置 `robot-station-g1` 自动连接优先级 999、无网关、never-default；旧 .88 配置保留低优先级，默认路由继续经 Wi-Fi。当前未接有线（NO-CARRIER），同一地址已临时加到接口用于本机验证；插线/重启后由持久配置接管。已验证实际 .100:9999 监听和 HTTP，现场 LAN 连通性/地址冲突尚未验证。G1 地址仍按用户给定 .164，未修改机器人网络或控制程序。Mac 转发 `12947` 的目标已同步改为 `192.168.123.100:9999`。详见同级 robot_station/HANDOFF.md 第 0A 节。

### 2026-10-16 当前交接：Robot Station 前端已完成，执行端待现场联调

- 用户已授权前端先实现、接口先保留。统一工作台现已部署到同级 `robot_station/apps/static`：两层推理、自检/SONIC 准备向导、整机管理、电量、G1 29 关节 3D、三相机、独立采集、视频/关节同步回放与状态机编辑器。
- 常规入口 `http://192.168.123.100:9999/#inference`；Mac 转发后 `http://127.0.0.1:12947/#inference`。`?preview=1` 开启显式“界面预演”，三路视频、BMS/关节、任务结果均为合成数据；不向设备发命令、不写真实输出。
- 新前端只复用旧数据目录、片段/录像和评级接口。版本化执行端未接入时禁用全部设备控制，不回退旧 `/api/stack/*` 或 `/api/record/*`，不把旧 overview 演示遥测当真实状态。正式片段仍 0，演示片段 1075。
- 执行端合同已保存到 `../robot_station/apps/contracts/console-v1.openapi.json`（OpenAPI 3.1，16 路径/25 模式），接入说明在 `../robot_station/docs/data_collection_console.md`。后端 `/api/v1/console` **尚未实现**。
- 后续先接只读快照（G1 BMS + 时间戳、29 具名身体关节、相机帧时间、服务/输入源），再做 Docker 幂等准备任务与停止、唯一控制源/初始化、PICO 采集、模型动作适配与推理、后台流程。机器人反馈 TTL 5 秒、电量 TTL 15 秒；后端原子校验全部互锁。
- 继续复用项目 `ensure_service()` 和现有 Docker/模型，不调用含强制清理的安装脚本作为网页启动。处理旧 apps adapter 对 5580 的所有权，避免双后台竞争。准备阶段固定 `allow_motion:false`。
- 已验证：前端 16 项、现有后端 19 项；真实服务页面与分页、合成推理/采集/三视频同步/3D/状态机/异常提示；320～1440 px 布局。截图在 `../robot_station/docs/references/console-v1-20261016/`。
- 本轮没有启动真实采集、模型推理、机器人运动或更改网络；设备联调、真实异常恢复/停止行为、PICO 标定仍待现场。原有 SDK/Unity/IDLE 仿真证据维持，不能据前端预演声称真机链路已通。
- 两库原有未提交改动均保留；未提交、未推送。工作台改版备份在 `../robot_station/.local-backups/console-frontend-20261016-173234/`。

### 2026-10-16 早先需求审查记录（以以上最新实现状态为准）

- 用户暂时不在现场，已确认使用 **PICO 4 + 腿部追踪器**。PICO 内的系统/App 核对、追踪器配对与人体校准、真实 LAN/PICO 通信、实际姿态映射及 G1 状态/运动验收，均留待现场具备设备操作条件后完成。
- 当前远程仍可推进但尚未完成的两项软件准备：**网络/追踪只读预检与图形仿真整体启动/停止入口**；**合成数据下的断流、时间戳冻结、程序退出和重连行为测试**。现有软件部署、Unity 截图和合成 IDLE 闭环不能替代这些验证。
- 用户最新要求转到 **`/home/harry/workspace/robot_station` 的前端展示与操作台**，参考 `http://192.168.10.46:9999/`：涵盖 SONIC 全流程引导启动、三路视频、自检、整机管理/状态、G1 全身控制、传感器、数据采集、可视化回放、状态机编辑器及最重要的推理页面；采集与推理要分开管理。
- 2026-10-16 用户补充：Robot Station 必须可视化显示 **G1 机器人电池电量**。全局顶部常驻电池图标与电量百分比；整机管理展示数据更新时间和来源，低电量按可配置阈值变色提示。使用真实 BMS/机器人状态数据，实际消息字段与接入端点尚待确认；掉线、缺失或过期数据显示 `-- / 未连接 / 数据过期`，不得用演示值或无时间标记的旧值假装实时电量。现已完成电量前端，真实 BMS 数据接入仍待后端实现。
- 界面入口以本次 Robot Station 需求为准，SONIC 本目录继续提供实际运行程序、Docker、SDK、模型、原始数据和执行能力；原先“另建独立部署网页”的安排须按统一操作台目标衔接，避免两个后台重复持有控制权或启动同一进程。
- 推理页范围已由用户重新选择确认：**上层任务模型推理 + 下层 SONIC 全身控制，两层分区显示**。此前误选“仅任务模型推理”已撤回。Robot Station 负责统一展示与编排；模型动作到 SONIC/G1 的语义、维度、坐标和频率适配仍需明确，不能默认已有通用 29 维动作通道。采集与推理分别管理任务，并统一运动控制权。
- **本轮先读参考控制台和现有代码、确认需求，不开始前端实现，不启动采集、推理或机器人运动。** 新界面可先在无设备情况下开发/展示，使用明确的未连接状态；不能用演示数据伪装真实就绪。

### 2026-10-16 XRoboToolkit 完整运行目录迁入项目（当前启动入口）

- 2026-10-16 15:00（Asia/Shanghai）真实图形窗口验证：已从现有 Ubuntu X11 图形会话 `DISPLAY=:1` 实际运行项目根 `run_xrobotoolkit.sh`，PC Service 与 Unity 客户端均来自项目运行目录。已取得 Unity 原始窗口截图（1500×800），场景与 UI 正常显示；窗口日志为 `Successfully connected to the service!` / `Waiting for device discovery...`。当前未连接 PICO，画面是头显/手部占位物体的初始场景，不能作为全身追踪、人体模型映射或 G1 重定向验收。截图与会话信息保存在 `outputs/xrobotoolkit/gui-preview-20261016-150004/`；服务和 Unity 窗口为本次预览保持打开，未启动机器人控制程序。此记录补充了此前只有无窗口测试、未验收实际 GUI 的状态。

- 原 `/opt/apps/roboticsservice/` 已完整复制到 **`/home/harry/workspace/sonic_deploy/external_dependencies/XRoboToolkit-PC-Service-runtime/`**，含 PC Service、Unity 3D、SDK 原生库、Qt、插件、QML、配置及资源。582 个原始文件逐一 SHA-256 校验一致，初始清单见运行目录 `.sonic-source-manifest.json`。系统安装保留作回退；当前项目入口与动态库解析不依赖原 `/opt` 目录。
- **首选项目入口是 `/home/harry/workspace/sonic_deploy/run_xrobotoolkit.sh`**。在 Ubuntu 图形桌面终端执行默认打开服务 + Unity 3D；`service` 仅确保后台服务运行，`status` 查看服务/Unity 进程和本地 gRPC 端口，`check` 检查运行文件和动态库。脚本从自身位置解析项目路径，可从其他工作目录调用。也已添加当前用户 Ubuntu 应用菜单 **SONIC XRoboToolkit 3D**，入口为 `~/.local/share/applications/sonic-xrobotoolkit.desktop`；菜单文件使用当前项目绝对路径，若以后移动项目须同步更新菜单文件。
- `gear_sonic/utils/teleop/xrobotoolkit_runtime.py` 是共享启动实现；PICO manager 的三个原 `/opt/.../runService.sh` 调用均已改用 `ensure_service()`。使用文件锁串行启动，复用已运行的 PC Service，并等待 `127.0.0.1:60061` 就绪后再初始化 SDK；从项目启动 Unity 后运行 PICO manager 不会重复拉起服务。原 `/opt` 服务若已经运行也会被复用，不会被自动重启或替换。
- 日志为 `outputs/xrobotoolkit/service.log`。无图形会话时默认 `3d` 会明确报错且不启动服务；显式 `service` 支持 Qt offscreen。关闭 Unity 后后台服务可继续供 PICO 使用。需要覆盖运行目录时可设置 `XROBOTOOLKIT_RUNTIME_DIR`。原始复制的 `run3D.sh` 等官方脚本保留原样，日常统一使用项目根入口。
- 二进制运行目录已加入 `.gitignore`，不要将这套约 368 MiB 的二进制与设备配置提交到 Git；Python SDK 1.1.0 的安装位置和 editable 映射保持原配置。
- 验证通过：项目入口可从 `/tmp` 调用；服务、SDK、UnityPlayer 的动态库均不引用原 `/opt`；后台服务实际启动且重复启动复用同一 PID；Python SDK 实际连接并查询追踪状态；PICO 脚本导入与 `--help` 正常。Unity 无窗口加载到引擎/程序集并成功连接服务，停在等待设备发现；`-quit` 未在 35 秒内正常退出，测试进程由超时机制终止。因此仅确认加载/连接，**真实图形窗口、PICO 实时追踪及姿态映射尚未验收**。测试服务也已停止，未启动机器人控制程序。
- 变更前文件备份：`.local-backups/xrobotoolkit-project-runtime-20261016-144005/`；验证日志：`.local-backups/xrobotoolkit-project-runtime-validation-20261016/`。

```bash
cd /home/harry/workspace/sonic_deploy
./run_xrobotoolkit.sh          # Ubuntu 图形桌面：PC Service + Unity 3D
./run_xrobotoolkit.sh service  # 仅后台服务；PICO manager 也会自动确保服务就绪
./run_xrobotoolkit.sh status
./run_xrobotoolkit.sh check
```

### 2026-10-16 用户确认：4070 双网卡、双网段直连方案

用户已确认采用以下网络拓扑：**4070 通过有线直接连接 G1，同时通过另一张网卡连接路由器；PICO 接入该路由器所在的局域网。** PC Service、Python SDK 和 SONIC 上位机程序运行在 4070，本机程序分别访问两侧网络。现有另一台工作站无需承担本方案的数据中转。

```text
PICO / XRoboToolkit App
        │ 路由器局域网（PICO 侧网段）
4070 的 Wi-Fi 或第二张有线网卡
        │
4070：PC Service → 本机 Python SDK → SONIC 上位机程序
        │
4070 的 G1 专用有线网卡：192.168.123.<未占用地址>
        │ 有线直连（机器人侧网段）
G1：192.168.123.164（用户提供，尚未实测）
```

| 配置项 | 已确认的方案与实施要求 |
| --- | --- |
| G1 侧地址 | G1 地址为用户提供的 `192.168.123.164`；4070 有线网卡使用该网段内未占用的静态地址。`192.168.123.100/24` 仅为候选示例，尚未选定或配置；实际配置前核对 G1 掩码及地址冲突，双方掩码匹配 |
| G1 侧网关 | 直连 G1 的网卡通常不配置默认网关；默认路由由连接路由器的网卡承担，避免影响管理连接与上网 |
| PICO 侧网络 | 4070 的另一张网卡和 PICO 接入同一路由器下可互通的局域网；网段不得与机器人侧重叠，并核对 VLAN、AP 客户端隔离和防火墙策略 |
| PICO 连接目标 | PICO 的 XRoboToolkit App 选择 **4070 在路由器局域网一侧的 IP**；确认连接状态后开启所需追踪和 `Send`。不把 G1 的 IP、有线网卡 IP 或 Tailscale 管理 IP 当作这一连接目标 |
| PC Service 与 SDK | 两者都在 4070；SDK 使用默认本机 gRPC 目标 `127.0.0.1:60061`。无需为了本方案将 SDK 服务开放到其他工作站；PC Service 的 PICO 设备连接与本机 SDK gRPC 是两段不同连接 |
| G1 通信接口 | SONIC / DDS 明确绑定连接 G1 的有线网卡，不能仅依赖自动选卡，避免选到 Wi-Fi、Tailscale 或 Docker 网桥 |
| 两网段关系 | 4070 本机程序处理 PICO 输入并生成 G1 指令；此拓扑不要求 PICO 直接访问 G1，也不需要在两网段间配置桥接、NAT 或 IP 转发 |
| 控制权 | 共享 G1 的运动控制端保持唯一；实施前确认现有工作站的控制进程与控制权状态，完成明确交接，避免两个工作站同时发送运动指令 |

**本会话的只读检查证据（2026-10-16）**：4070 的 Wi-Fi 接口 `wlx6c1ff78b48c1` 地址为 `10.4.161.222/22`，默认网关为 `10.4.163.254`；有线接口 `eno1` 为 `NO-CARRIER`，未配置机器人侧 IPv4。上述地址是检查时快照，不代表已经接入 PICO 所在网络，也不应作为后续固定配置。`.venv_teleop` 内 SDK `1.1.0` 的隔离导入、当前源码映射、唯一安装版本、SONIC 所需 15 个可调用接口及原生库依赖检查通过；PC Service 软件包 `roboticsservice 1.0.0.0` 已安装，按启动脚本库路径检查无缺失依赖，检查时未发现服务进程。

**验收顺序（待实施）**：

1. 现场接线并确认两侧 IP、掩码、路由和实际网卡名；先检查 4070 到 `192.168.123.164` 及 PICO 侧的网络可达性。
2. 在 4070 启动唯一的 PC Service，PICO 连接 4070 的路由器侧 IP；通过只读 SDK 检查确认追踪数据有效、时间戳持续更新。SONIC 默认 xrt 路径还需确认身体追踪数据就绪；SDK 可导入、`init()` 返回或数组有值均不等于真实追踪已就绪。
3. 将 SONIC / DDS 绑定 G1 有线网卡，先验证 G1 状态反馈；网络能 ping 通不等于 DDS 数据链路已建立。随后在明确控制权和操作边界后验证运动执行，并检查时延、抖动、指令过期与断线行为。

**当前阶段是网络方案已确认，现场接线、网卡配置、PICO 连接及真机链路验收仍待完成。** 本段网络方案确认时仅维护交接文档，未修改网络配置或启动硬件链路；后续 Docker 与仿真验证见下一节。后续部署网页应分别呈现“网络可达 → PC Service 就绪 → PICO 追踪有效 → G1 状态有效 → 控制执行就绪”，沿用项目共享 `ensure_service()` 的去重/就绪检查，避免另行叠加旧系统脚本启动服务。

通信实现参考：[PICO App 连接说明](https://github.com/XR-Robotics/XRoboToolkit-Unity-Client#feature-instructions)、[SDK 默认连接与配置](https://github.com/XR-Robotics/XRoboToolkit-PC-Service/blob/main/RoboticsService/PXREARobotSDK/PXREARobotSDK.cpp#L276-L299)。

### 2026-10-16 准备项复核与单局域网备选（尚未切换网络）

用户仍不在现场，提出也可以自建一个局域网，让 PICO、4070、G1 共同接入。此为可行备选，**不是已实施的网络配置，也未取代上文双网段方案的现场配置**。

- 单 LAN 推荐拓扑：PICO 通过 Wi-Fi 接路由器/AP；4070 和 G1 各用网线接同一路由器的 LAN 口或其下交换机。按用户给定的 G1 `192.168.123.164`，可将整套独立 LAN 规划为 `192.168.123.0/24`，路由器例如 `.1`，4070 有线例如 `.100`，PICO 由该网段 DHCP 分配；所有地址均须现场排除冲突，DHCP 池排除固定设备。路由器不能使用访客隔离/AP 客户端隔离，须允许 Wi-Fi 与有线 LAN 互通。
- 这个单 LAN 拓扑中，PICO 的 PC Service 地址填 **4070 的 LAN IP**，不是 G1 IP 或 Tailscale IP；机器人 DDS 仍明确绑定 4070 有线口 `eno1`。避免把 4070 的有线与 Wi-Fi 同时配置成同一子网的两条竞争路由。若仍采用“4070 网线直连 G1 + Wi-Fi 接路由器”，继续使用上文互不重叠的双网段，不要仅将两个接口地址改成同一网段。
- 实际当前状态：4070 仍在原 Wi-Fi `10.4.161.222/22`、默认网关 `10.4.163.254`；`eno1` 为 NO-CARRIER、无 IPv4 地址。PC Service/Unity 已运行，gRPC `127.0.0.1:60061` 就绪，PC Service TCP `63901` 正在监听外部接口；PICO 与实际 AP/防火墙互通仍未验收。未更改任何网络配置。
- PICO 硬件已确认（2026-10-16 用户回复）：**PICO 4，配有腿部追踪器**。PICO 4 在 SONIC 官方硬件清单内。现场仍需确认两只手柄和左右脚追踪器的配对、PICO 系统及 XRoboToolkit APK 版本、开发者模式，并完成 tracker/人体校准。设备型号与配件类别不再是待用户回答的问题；已缓存官方稳定版 `XRoboToolkit-PICO-1.1.1-SDK29.apk` 到 `installers/xrobotoolkit/`，大小 34,680,904 bytes，SHA-256 `6089e1ce175cf3e292cea5919c2b97711151186ca39c4a5569786a12fc167eb2` 与官方一致且 APK ZIP CRC 通过。包名 `com.xrobotoolkit.client`，版本 `1.1.1`，最低 Android API 29、目标 API 32；SDK29 是官方资产名称，不代表 targetSdkVersion 为 29。来源与元数据见同目录 `pico-apk-download-manifest.json`。头显当前 OS、已有 App、安装成功及实时追踪仍待设备验收；此次仅缓存，没有安装到头显或改动 Ubuntu 运行组件。
- 真实数据验收待完成：PICO 填 4070 LAN IP 后开启 Head、Controller、Full body 和 Send；除 Unity 显示连接，还应检查 SDK 身体数据可用且时间戳持续前进、关节方向/比例与人体姿态正确。此阶段 G1 不必参与。
- 控制验收待完成：真实 PICO → Python manager → Docker C++ → MuJoCo 的全身校准、姿态映射、模式切换与停止；退出仿真后再核对真机 G1 的关节/手部配置、固件及控制权，验证真实状态反馈与有线时延。现有离线闭环仅使用合成输入，不能代替这些验收。
- 故障测试待完成：PICO 暂停发送/掉线、时间戳冻结、manager 退出、PC Service 中断及网络断连/恢复。源码默认 xrt 使用 manager 内部的 `PicoReader`，其 `disconnected` 属性固定 False；另一个输入读取模块有超时标志，但不可直接当成当前 manager 已接入该机制。下游已有 planner 1 秒超时回 IDLE；已检索的姿态流延迟检测结果用于音频告警，不能将该阈值当作自动停机保证。须通过离线故障注入及后续现场验收确定各模式的最终行为，不要认定整条链路完全无保护或已经验收。
- 便捷性待完成：统一网络只读预检、图形仿真三进程的整体启动/停止编排尚未封装；当前可用已有手册分终端运行。tmux、独立采集/相机环境仍未补齐，属于一体采集流程，不阻塞首次 PICO → Unity 通信或现有最小手动仿真路径。

### 2026-10-16 Docker 启动与 SONIC 离线闭环已验证

用户最新要求：先在 4070 上验证 Docker / SONIC pipeline，并准备下次现场连接 PICO、4070 和 G1 后开始调试。当前分工为 **宿主机 PC Service + SDK + PICO/ZMQ 程序，Docker 内 C++ 控制 + TensorRT + Unitree DDS**，不是把宿主机虚拟环境整体搬入 Docker。

新增推荐入口：`gear_sonic_deploy/docker/sonic-runtime.sh`，支持 `status | start | build | check | shell | exec COMMAND... | stop`。默认持久容器为 `sonic-4070`，镜像 `g1-deploy-dev:latest`，采用 host 网络；`start` 仅让容器待命，不启动 PC Service、PICO 或机器人控制。它检查容器归属和挂载，复用现有容器，不强制删除其他容器。完整命令、现场步骤和验证边界见 [4070 Docker 运行手册](docs/sonic_4070_docker_validation.md)。

**本轮已实施**：

- 修复 `.venv_teleop` 中 `gear_sonic` 和 `unitree_sdk2py` 的旧 editable 路径，分别重新绑定 `/home/harry/workspace/sonic_deploy/gear_sonic`、`external_dependencies/unitree_sdk2_python`；使用 `--no-deps`，没有重建 venv 或更换其他依赖，SDK 保持 `1.1.0`。原元数据分别保存在 `.local-backups/gear-sonic-path-fix-20261016/` 和 `.local-backups/unitree-python-path-fix-20261016/`。
- 容器内使用已安装的 `/usr/src/googletest` 完成 CMake 配置，解决原配置会尝试联网下载 GoogleTest 的问题；启用 ROS 2 和 ZMQ，编译、链接实际 `g1_deploy_onnx_ref` 目标通过，运行时库检查无缺失。
- 为容器运行用户建立 UID/GID 对应的账户记录及 home，解决仅传数字 UID 时 Unitree SDK 的 `getpwuid error. uid:1000`。构建生成物仍归宿主机用户所有。
- 解码器、编码器、planner 的 ONNX 均已生成并加载 TensorRT 引擎；解码器/编码器 CUDA Graph 捕获通过，13 段参考动作成功读取。缓存保存在原模型目录的 `*.trt`，构建产物位于 `gear_sonic_deploy/target/release/` 与 `build/`，无需提交这些生成物。
- 移除 `gear_sonic/scripts/run_sim_loop.py` 入口处重复的 DDS 初始化，由 `BaseSimulator` 统一初始化；修复前虽可闭环运行，但会出现非致命 domain 初始化错误，修复后重新验证通过。

**离线验证证据**：

- Docker 内可识别 RTX 4070，镜像 ID 仍为 `sha256:34787d39ac2f99457952b513da5e20b98104260990bbe7a8ae3611fc70ed24e7`，本次未重建镜像。宿主机 G1 RobotModel 加载、PICO/仿真入口 `--help` 均通过。
- 宿主机合成 planner 指令（IDLE / 零速度）→ ZMQ → Docker C++ 实际推理 → loopback DDS → 宿主机无界面 MuJoCo → ZMQ 反馈，20 秒获得 **1000 帧、1000 个连续控制索引、29 个关节**，检查的反馈、动作和 token 数值均有限，无解码错误，正常 start/stop 通过。
- DDS 初始化修复后，重复闭环测试获得 **300 帧 / 300 个连续控制索引**，结果通过；仿真日志仅有 loopback 不支持多播的提示，不再出现重复 domain 初始化错误。
- 测试 DDS 均明确绑定 `lo`，ZMQ 使用 `15556/15557`；没有启动 PC Service、连接真实 PICO 或向物理 G1 发指令。合成 IDLE 输入不能当作真实人体姿态、行走稳定性或全链路断线保护的验收。
- 详细日志和 JSON 结果保存在 `.local-backups/docker-validation-20261016/logs/`；相关安装备份也保留，没有强制递归删除、提交或推送原有工作区内容。

**接续状态**：软件运行环境、实际控制程序、模型缓存及最小离线闭环已准备；现场仍需配置双网段，验证 PICO 身体追踪与校准、G1 DDS 状态、型号/关节/手部配置、控制权、初始化及真实移动/停止/断流行为。C++ 程序会请求释放原控制模式并执行初始化站立和手部动作，不能把启动该程序当成只读自检。

`tmux`、`.venv_data_collection`、独立 `.venv_sim`、`.venv_camera` 及官方一体采集 launcher 的 Docker 编排仍未完成。当前验证直接使用 `.venv_teleop` 跑宿主机仿真，绕开采集入口；这些缺项不阻塞上述最小调试链路，也不应被写成已安装。部署网页尚未实现。

### 2026-10-16 补充：Ubuntu XRoboToolkit 3D 客户端与 SONIC 仿真入口

用户指出现场调试还需要可视化检查人体姿态和机器人响应。已核对 [SONIC 官方 PICO 全身遥操作教程](https://nvlabs.github.io/GR00T-WholeBodyControl/tutorials/vr_wholebody_teleop.html#step-by-step-teleop-in-sim)：首次仿真推荐三终端运行 MuJoCo、C++ sim 控制和带 `--vis_vr3pt --vis_smpl` 的 PICO manager。本地原 `SONIC_SIM_TELEOP_RUNBOOK.md` 也记有该流程，但其中旧目录和安装状态只作历史参考。

- 功能代码已经存在：`gear_sonic/utils/teleop/vis/vr3pt_pose_visualizer.py`。PyVista 窗口显示 G1 参考网格、头/双腕三点及 SMPL 24 关节，用于坐标与校准检查；完整策略驱动后的模拟机器人关节响应在 MuJoCo 窗口检查。不能把参考姿态窗口等同于完整的 G1 全关节映射验收。
- 用户所指的 3D demo 是 **Ubuntu 的 XRoboToolkit Unity 3D 客户端**。当前从项目根 `run_xrobotoolkit.sh` 启动迁入项目的 PC Service 与 `SDKDemo/RobotUnityDemo/RobotLinuxDemo.x86_64`；系统旧菜单仍指向原 `/opt` 安装，项目菜单为 **SONIC XRoboToolkit 3D**。官方 README 将该客户端列为 3D 可视化演示及实时数据监控；本机程序集含 `Avatar`、`BodyTracking`、`BodyRoot` 等人体显示逻辑。Unity 已在无窗口模式加载并连接服务，但实际桌面画面、PICO 驱动模型和 G1 专用重定向仍未验收。SONIC PICO manager 现已使用同一服务启动实现进行去重/就绪检查。
- 2026-10-16 图形版安装包下载：已从 [XRoboToolkit 官方 v1.0.0 Release](https://github.com/XR-Robotics/XRoboToolkit-PC-Service/releases/tag/v1.0.0) 下载 Ubuntu 22.04 amd64 图形版至 `/home/harry/Downloads/XRoboToolkit_PC_Service_1.0.0_ubuntu_22.04_amd64.deb`（100,046,068 bytes），SHA-256 `61961067eb4b41f81ed7cae35f4690dbb0ddfefb329a12b24e0b90ebc46ada91` 与官方一致。包内版本和现有安装均为 `roboticsservice 1.0.0.0 amd64`；现有安装 `dpkg --verify roboticsservice` 无异常，服务程序、Unity 客户端和 UnityPlayer.so 的动态库检查均无缺失，因此未重复安装。以上为迁移前的系统安装检查记录；当前使用项目入口 `run_xrobotoolkit.sh` 和菜单 **SONIC XRoboToolkit 3D**，迁移后的实际启动验证见当前启动入口章节。
- Unity 3D 客户端单独解包（2026-10-16）：已从上述通过 SHA-256 校验的官方 Ubuntu 包提取完整客户端到 `/home/harry/Downloads/XRoboToolkit-Unity3D-Linux/`，含 `RobotLinuxDemo.x86_64`、`UnityPlayer.so` 和 `RobotLinuxDemo_Data/`。148 个官方文件均已逐一校验，与现有安装一致；来源与逐文件哈希保存在该目录 `download-manifest.json`。上述下载目录仍保留；当前工作副本和组合启动已迁入 `sonic_deploy`，使用项目根 `run_xrobotoolkit.sh`。下载当时未运行 GUI 或接入 PICO。
- 4070 已有 `pyvista 0.48.4`、`vtk 9.6.2`、`mujoco 3.10.0`。隔离导入通过，实际 EGL 离屏渲染通过：50 个 G1 网格 actor、24 个 SMPL 关节 actor、3 个 VR 标记，输出 1200×800 PNG。该检查没有真实 PICO 数据，不代表已经验证互动窗口和实时姿态映射。
- 普通 SSH 当前没有 `DISPLAY` 或 Wayland 显示连接；尚未在 4070 图形桌面启动并验收实时窗口。离屏测试结果和截图保存在 `.local-backups/docker-validation-20261016/visualization-check/`。
- 最新现场顺序应为 **Ubuntu 通过项目根 `run_xrobotoolkit.sh` 启动 Unity 3D 客户端 → PICO 连接 4070 路由器侧 IP、开启所需追踪/Send 并完成人体校准 → 检查三维姿态更新 → 使用共享服务入口进行 MuJoCo + C++ sim + PICO manager 联调 → 正常停止仿真 → G1 有线状态与受控真机调试**。当前就绪的是客户端安装文件、离线软件闭环和 SONIC 静态渲染能力；Unity/PICO 实时显示及 G1 映射仍待实际验证。Unity 客户端入口与功能参考：[官方 PC Service README](https://github.com/XR-Robotics/XRoboToolkit-PC-Service#sdk-and-demo)。

## 2. 当前实测状态（2026-10-15）

| 项目 | 本轮证据与状态 |
| --- | --- |
| GPU | `NVIDIA GeForce RTX 4070`，显存 12282 MiB；`nvidia-smi` 驱动 `580.178.04` |
| Docker | `docker` 命令可用；`docker ps -a` 为空，没有容器 |
| 已有镜像 | `g1-deploy-dev:latest` 存在；ID `sha256:34787d39ac2f99457952b513da5e20b98104260990bbe7a8ae3611fc70ed24e7` |
| `.venv_teleop/bin/python` | 存在并可运行 |
| 模块与 SDK | `gear_sonic`、`mujoco`、`zmq` 可被 `find_spec` 找到；XRoboToolkit SDK 已从旧 `1.0.2` 替换为官方 `1.1.0`，在 `.venv_teleop` 可实际导入。已从 `/tmp` 使用 `python -I` 验证迁移后源码映射、唯一版本及 SONIC 所需 15 个接口；未连接设备 |
| XRoboToolkit PC Service | 完整工作目录已迁入 `external_dependencies/XRoboToolkit-PC-Service-runtime/`；项目根 `run_xrobotoolkit.sh` 启动。实际服务/SDK 连接与重复启动复用已验证；测试进程已停止，PICO 实时链路尚未验证 |
| tmux | `command -v tmux` 未找到 |
| `.venv_data_collection` | 不存在 |
| `.venv_sim` | 不存在；即使 teleop 环境含 MuJoCo，也不满足官方 launcher 对该独立目录的检查 |
| `.venv_camera` | 不存在 |
| `gear_sonic_deploy/build` | 不存在，尚无本目录 C++ 编译产物证据 |
| 相机 / PICO / robot 端点 | 工作台现状显示未接通，未验证真实图像、设备反馈或录制 |
| 通用工作台 Web | `robot_station/apps` 的 `127.0.0.1:2947` 运行；同一 Web 进程持有 ZMQ `5580` |

旧文档 `SONIC_DOCKER_DEPLOYMENT_STATUS.md` 与 `SONIC_SIM_TELEOP_RUNBOOK.md` 写于 2026-07-26，包含旧 `/home/harry/sonic_deploy` 路径和当时的驱动/SDK 状态。**当前路径及本轮实测结果优先**，不要把旧文档的“已安装/可导入”直接当作本次状态。

本次只升级 XRoboToolkit Python SDK，并保留原 `.venv_teleop` 及其他运行依赖；没有构建镜像、创建容器、执行 `just build`、启动 PC Service/MuJoCo/PICO 或执行真机控制。

### XRoboToolkit：先安装依赖，运行时启动服务

用户已确认：**4070 上的 `sonic_deploy` 需要先准备 XRoboToolkit，标准 SONIC 遥操作启动流程包含它的启动/就绪检查**。按当前默认 `--input-source xrt` 路径区分两层，不能把两者混为一项：

- **Python SDK / 绑定 `xrobotoolkit_sdk`**：属于宿主机 SONIC 遥操作环境，现为官方 `1.1.0`，以 editable 模式安装在 `.venv_teleop`。源码位于迁移后的 `external_dependencies/XRoboToolkit-PC-Service-Pybind_X86_and_ARM64/`，提交 `8941e1dbbf4313fe83846f82984eaa8c992690bf`。包入口映射到该目录的 `src/xrobotoolkit_sdk/__init__.py`；本地编译扩展 `_core.abi3.so` 与配套原生库位于 venv 的 `site-packages/xrobotoolkit_sdk/`，这是正常的 editable 安装布局。它是 Python 模块，不是单独启动的服务。
- **XRoboToolkit PC Service**：当前工作副本位于项目内 `external_dependencies/XRoboToolkit-PC-Service-runtime/`，使用根目录 `run_xrobotoolkit.sh` 启动服务和 Unity 3D，或 `run_xrobotoolkit.sh service` 仅启动服务。系统 `/opt/apps/roboticsservice/` 保留作回退。运行流程仍需服务就绪、PICO 端连接并有新鲜追踪数据。
- **现有自动启动行为**：`gear_sonic/scripts/pico_manager_thread_server.py` 的 xrt 初始化及两个独立可视化入口均调用共享 `ensure_service()`，复用已运行服务或启动项目副本，并等本地 gRPC 就绪，再调用 `xrt.init()` 和等待身体追踪。未来部署网页也应复用这套服务管理，避免另行调用旧官方后台启动脚本。

因此部署网页应把 **SDK 可导入**列为安装/自检前置条件，把 **PC Service 运行 → PICO 连接及追踪数据就绪 → 遥操作程序就绪**列为运行阶段依赖。此处描述的是默认 xrt/PICO 路径；显式选择 `isaac-teleop` 时需按另一输入源检查，不套用相同 SDK 条件。SDK 安装已验证，但服务连接和真实追踪数据尚未验证。

SDK 官方源码归档、预编译 wheel 与校验说明保存在 **`installers/xrobotoolkit/`**，见 [installers/xrobotoolkit/README.md](installers/xrobotoolkit/README.md)。实际安装使用该官方源码归档解压后的本地目录，以 editable 模式构建，不是只安装缓存 wheel。

### 本次替换、验证与回滚

- 旧问题：`1.0.2` 的 editable finder 仍引用迁移前不存在的 `/home/harry/sonic_deploy/...`，因此旧安装虽有元数据却无法被模块查找找到。
- 已按用户要求从生效位置移除旧 SDK 源码、旧 `dist-info`、`.pth`、finder 与对应字节码。采用可回滚移出方式，没有强制递归删除环境；备份在 **`.local-backups/xrobotoolkit-upgrade-20261015-RO7yWd/`**，包含 `old-sdk-source/`、`site-packages/` 及修改前的安装脚本/文档。
- 新版源码沿用上述 `external_dependencies/..._X86_and_ARM64/` 位置，避免标准启动脚本分叉；`uv pip install --python .venv_teleop/bin/python --no-deps --editable <源码绝对路径>` 已成功构建和安装 `1.1.0`，没有更换其他运行包。
- 已通过隔离 Python 的真实导入、`direct_url.json` editable 路径核对、唯一版本检查、SONIC 所需 15 个可调用接口和未初始化状态下的只读 getter 形状检查。没有调用 `xrt.init()`，空追踪状态不是真实设备数据验证。
- 升级后在 `robot_station/apps` 再次运行后端回归测试，**19 项通过**。
- 新增 SDK 专用入口 **`bash install_scripts/install_xrobotoolkit_sdk.sh`**：只安装 SDK 并验证迁移后的映射，不重建 venv、不启动服务。完整 `install_pico.sh` 的 SDK 阶段改为调用此入口；其前面的全环境清理步骤仍然存在，单独维护 SDK 不要运行整个脚本。
- 若确需回滚：先把当前新版安装和源码另行备份，再恢复旧备份；不能直接覆盖后就认为恢复成功，旧版映射必须重新建立到 `/home/harry/workspace/sonic_deploy`。不得恢复旧目录硬编码。
- `external_dependencies/..._X86_and_ARM64/` 的旧文件删除/新文件增加属于此次有意 SDK 升级；不要用 Git 清理把它们恢复成旧版。`.local-backups/` 已忽略，不提交环境元数据。

## 3. 现有代码入口与实际职责

| 入口 | 作用与需保留的信息 |
| --- | --- |
| `gear_sonic_deploy/docker/run-ros2-dev.sh` | Docker 开发环境脚本；容器名/镜像名 `g1-deploy-dev`，使用 host 网络和 GPU。脚本是交互式 `docker run -it --rm ... bash`，不是现成的后台 Web 部署服务 |
| `gear_sonic_deploy/deploy.sh` | C++ 部署，支持 sim / real / 网卡或 IP；默认 real，运行时还涉及构建/部署确认 |
| `gear_sonic/scripts/launch_data_collection.py` | tmux 一体采集启动器，包含 C++ deploy、PICO、导出器与可选相机 viewer / 仿真。当前源码直接在宿主机目录执行 `deploy.sh`，**不会自动进入 Docker** |
| `gear_sonic/scripts/run_sim_loop.py` | MuJoCo 仿真入口；官方采集 launcher 使用 `.venv_sim`，并可启用图像发布 |
| `gear_sonic/scripts/pico_manager_thread_server.py` | PICO / ZMQ manager；图形可视化参数是 `--vis_smpl`，不是 `--vis_smple` |
| `gear_sonic/scripts/run_data_exporter.py` | 采集导出器，由官方 launcher 使用 `.venv_data_collection` 启动 |
| `gear_sonic/camera/composed_camera.py` | 相机服务实现；设备类型与设备 ID 按实际硬件确定 |
| `install_scripts/install_camera_server.sh` | 相机环境与可选 systemd 安装脚本，包含交互和删除旧环境的操作，不能不经审查直接包成一键启动 |
| `systemd/composed_camera_server.service` | 相机服务模板；默认 User/路径/设备 ID 为示例值，不能直接按当前机器可用配置处理 |
| `outputs/` | 原始 LeRobot 输出，仍在此目录，未迁移到网页项目 |

Docker 挂载关系由现有脚本确认：

```text
sonic_deploy/gear_sonic_deploy -> /workspace/g1_deploy
sonic_deploy/gear_sonic        -> /workspace/gear_sonic
容器工作目录                 -> /workspace/g1_deploy
```

旧手册中的三终端流程可作编排线索：PC Service / 仿真按需准备，容器内编译与部署，宿主机 PICO/ZMQ 与采集程序配合。实际实现前仍需核实每一步依赖、运行位置、完成条件与停止方式。

## 4. 执行端实施顺序（前端已完成，后台待接入）

统一前端现已位于 robot_station/apps，端口 2947；调用合同见 apps/contracts/console-v1.openapi.json。以下步骤的真实设备后台尚未实现，不把前端预演当作已接通。

1. **只读自检页**：主机/GPU、Docker daemon 与镜像、虚拟环境及关键模块（xrt 路径必须单独检查 `.venv_teleop` 内 `xrobotoolkit_sdk` 可导入）、PC Service 安装/运行状态、模型/构建产物、磁盘、网络端点、相机设备与 PICO 输入源。逐项显示未检测/通过/警告/阻塞、证据、时间和修复入口。
2. **Docker 阶段**：从“镜像已存在”到“容器就绪”、必要时编译，再到进程就绪；实现幂等复用、清晰日志、超时和失败重试。Web 请求提交后台任务，不长期阻塞 HTTP。
3. **相机阶段**：确定实际设备映射，提供头部/左右腕等可用视角的预览、帧时间、帧率和断流状态。现有 ZMQ 相机流需要浏览器可读的转发接口，网页不能直接把 ZMQ 地址当作视频 URL。
4. **机器人 / 遥操作阶段**：区分宿主机、容器和机器人端；按实际 sim / real 模式管理 PC Service、PICO、部署程序与导出器。用真实反馈或握手判定就绪，不能只检查进程存在或 TCP 端口。
5. **一键启动**：仅组合已验证的步骤，显示步骤依赖和当前进度；重复点击不会产生重复进程；失败后可定位/重试；停止时按依赖逆序处理本项目拥有的进程。
6. **接入通用工作台**：部署服务提供明确的状态、能力与受控动作接口，`robot_station/apps` 专注推理和数据采集任务。处理当前 apps 对 `5580` 的所有权，避免双后台重复控制。

最新接续优先级（2026-10-16）：用户暂不具备现场条件，当前已完成 `robot_station` 统一前端和接入合同；现场 PICO / G1 链路验证仍按 [4070 Docker 运行手册](docs/sonic_4070_docker_validation.md) 待设备接入后完成。前端开发可先进行，不将未验收硬件能力标记为真实就绪。

## 5. 已发现的实现注意项

- Docker 脚本含强制移除既有同名容器的操作；其交互式入口也不适合作为 Web 后台命令原样执行。部署服务需要明确容器所有权与复用策略。
- 环境安装脚本含强制递归删除旧 venv 的命令。用户的会话规则要求执行任何此类删除前披露准确命令、目标与替代方案，取得明确同意并发送双语 handoff 邮件；不要在自动启动流程中隐式调用。
- 当前 apps 适配器直接调用官方 launcher，并有部署提示自动确认逻辑；这不是已经验证的 Docker 阶段编排。未来重构须保留模式选择与操作者启动边界。
- `deploy.sh` 默认 real；仿真流程需要明确选择 sim，不能靠省略参数。
- 初次读取部署网页不应自动初始化机器人、执行动作或重启共享设备。把服务启动、连接、初始化、使能与运动执行作为不同状态。
- PC Service 与某些 MuJoCo/PICO 可视化需要显示会话，普通 SSH 下没有窗口不等于已成功运行；可探索 headless 的步骤需要单独验证。
- 当前参考站为 H1 机器人实现，SONIC/G1 的动作维度、协议和保护逻辑不同。复用样式与工作流，不直接复用 H1 的关节/高度命令。

## 6. 样式参考与职责划分

参考站 `192.168.10.46:9999` 使用深色侧栏、白色卡片、浅灰背景、蓝色主操作。自检页为“检查总览 + 放行项 + 运行准备”；传感器页为“主视角大画面 + 两个腕部小画面”。推理页的任务配置/运行状态布局主要供通用工作台参考。

截图与观察笔记保存在另一项目的 [docs/references/station-9999-20261015/README.md](../robot_station/docs/references/station-9999-20261015/README.md)。参考站 API 报告 `/workspace/robot_station` 运行目录，宿主机映射未核实；观察时相机回显关闭，没有触发设备启动或动作。

## 7. Git 与接续检查

本轮开始时分支 `main`，HEAD `4141c34`。原有改动如下，属于此前工作，保持原样：

```text
 M gear_sonic_deploy/cmake/FindTensorRT.cmake
 M gear_sonic_deploy/docker/Dockerfile.ros2
?? SONIC_DOCKER_DEPLOYMENT_STATUS.md
?? SONIC_SIM_TELEOP_RUNBOOK.md
?? installers/
```

可先执行以下只读检查：

```bash
cd /home/harry/workspace/sonic_deploy
git status --short
docker ps -a
docker image inspect g1-deploy-dev:latest --format '{{.Id}}'
command -v tmux
```

下一轮不要因为旧安装笔记存在就跳过环境复查，也不要通过清理目录/重建环境覆盖已有改动。每轮同步维护此文件的当前阶段、已验证证据、待办和与工作台的接口变化；不保存任何凭据。
