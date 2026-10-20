# G1 独立关节 SDK 适配与现场标定

更新：2026-10-20（Asia/Shanghai）。**软件适配和离线检查已完成；本台G1的真实增益、支撑、运动与停止效果尚未标定。** 用户当天确认硬件是完整29自由度，腰部roll/pitch未锁定，已记录在4070的待标定配置中。没有执行真机运动。

## 官方依据与适用范围

依据4070已安装的官方 `unitree_sdk2_python` 源码，commit `4141c34280abb67c82e115342a8720f4a83d750d`：

- [G1 low-level 示例](https://github.com/unitreerobotics/unitree_sdk2_python/blob/4141c34280abb67c82e115342a8720f4a83d750d/example/g1/low_level/g1_low_level_example.py)：29个身体电机、官方索引、PR=0、mode_machine回填、2ms周期和示例Kp/Kd；明确标记23自由度和锁腰版本的无效关节。
- [HG LowCmd IDL](https://github.com/unitreerobotics/unitree_sdk2_python/blob/4141c34280abb67c82e115342a8720f4a83d750d/unitree_sdk2py/idl/unitree_hg/msg/dds_/_LowCmd_.py)：35个motor_cmd槽位。
- [CRC](https://github.com/unitreerobotics/unitree_sdk2_python/blob/4141c34280abb67c82e115342a8720f4a83d750d/unitree_sdk2py/utils/crc.py)：HG命令对齐布局1004字节、状态2092字节。
- [MotionSwitcher](https://github.com/unitreerobotics/unitree_sdk2_python/blob/4141c34280abb67c82e115342a8720f4a83d750d/unitree_sdk2py/comm/motion_switcher/motion_switcher_client.py)：CheckMode用于确认官方运动服务是否空闲。本适配器不自动调用ReleaseMode/SelectMode。

本适配器用于**可靠机械支撑下的单关节/姿态联调**，不承担自由站立平衡、行走、自动站立初始化或SONIC无缝接管。SDK消息的rad直接映射浏览器具名关节，没有擅自加入零位偏移、方向翻转或AB并联模式。不得通过编辑网页关节名称去兼容23自由度或锁腰硬件。

2026-10-20用户调整范围：SONIC运动程序启动时由其自身流程进入初始姿态，**暂不开发工作台手动姿态到SONIC的自动交接**，不将它列为当前交付缺项。独立关节调试和姿态库继续保留，预先应用工作台姿态不是SONIC启动前置步骤。控制源互斥仍须保持：结束手动控制并确认停止发布后才能使用SONIC运动，SONIC运行时禁止手动滑条并发下发。上述SONIC启动行为按用户说明记录，尚未实机验证；软件准备allow_motion:false不触发运动。详见 [handoff第0M节](../HANDOFF.md)。

## 已实现的控制路径

`网页命令 → ConsoleRuntime互斥 → RealManualControl私有租约/IPC → 独立console_real_worker → Unitree SDK2 rt/lowcmd`

- 使用HG `LowCmd_`，PR模式0，mode_machine必须与现场记录和持续LowState相符。仅前29个身体电机按官方索引启用，每帧新建消息并将29～34槽位、reserve清零禁用；tau前馈为0。调用官方CRC后发送。
- `initialize`通过本地标定门槛后只启动LowState/控制源预检，不创建LowCmd发布器。`claim`还需显式 `supported_operation_confirmed:true`，通过当前CRC/反馈/控制源检查后才创建发布器。从实际反馈姿态开始，1秒内逐步增加位置增益，不自动归零。
- LowState验证CRC、35槽位、29个具名反馈、递增tick（支持uint32回绕）、PR/mode_machine、数值/限位/电机故障状态/温度。当前保守要求motorstate=0；若某固件正常状态字非0，应先核实位定义并修改受审查适配层，不能直接忽略状态字。
- 检查唯一HG LowState发布者，绑定其DDS endpoint GUID；任何其他rt/lowcmd发布者或非空MotionSwitcher控制服务都阻止接管/继续输出。DDS发现依赖现场网络可见性，不等于全网不存在不可见控制器。
- 目标完整具名29维、rad、序号严格递增；按现场收窄限位、单次最大步幅、速度/加速度校验。五次轨迹连续保留当前命令位置、速度、加速度（C2），解析多项式极值验证整个过渡，不仅检查末端。轨迹可自动延长，超过边界或无法满足约束拒绝。
- 控制周期目标2ms，调度超过20ms触发退出；数值库在创建发布器前预热。Python/Linux调度不是硬实时保证，现场必须在实际GPU/采集负载下验证控制时序。
- 运行中检查目标跟踪误差、温度、IMU倾角、估算PD力矩和实测tau_est。**LowCmd没有独立的硬件力矩上限字段**；软件估算/反馈超限退出不能宣称为硬件限矩器，也不能替代硬件保护。
- 浏览器0.9秒心跳、3秒租约。正常释放/租约到期按已核定策略先kp=0进行阻尼，随后重复禁用命令约100ms并关闭发布器。此策略仅适用于机械支撑下的调试；释放后不保证维持初始姿态。
- 若反馈/CRC失效、模式/来源改变、出现竞争控制器或写入/调度故障，停止本适配器发布并退出，不向未知状态或其他控制器追加“停止指令”。**这不等于机器人已经物理停止**，硬件停止和机械支撑始终由现场保障。
- 独立进程自行检查心跳和本地授权，Web重启写入撤销状态；worker故障后不自动恢复运动。`run.sh`/systemd不会启动manual-real或自动接管。整机断电/主管被强杀时无法保证软件停止序列完成，必须依靠硬件侧停止方案。

## 本地标定文件与工具

正式文件位于 `apps/.runtime/console/real-control/commissioning.json`，普通本用户文件、0600权限，网页没有审批/写入接口。4070当前文件 `approved:false`，硬件版本已按用户确认记录；SDK增益仍为参考值，torque_limit_nm等现场必填项未伪造，输出保持关闭。

所有命令在4070的 `/home/harry/workspace/robot_station` 运行；使用SONIC teleop Python：

```sh
# 查看现场实时状态：只读，不创建LowCmd发布器
../sonic_deploy/.venv_teleop/bin/python apps/unitree_commission.py inspect

# 生成新参考模板，不覆盖现有文件、不启用运动
../sonic_deploy/.venv_teleop/bin/python apps/unitree_commission.py template --file /tmp/g1-commissioning-reference.json

# 检查填写后的参数格式/边界；软件通过不代表实机标定通过
../sonic_deploy/.venv_teleop/bin/python apps/unitree_commission.py validate

# 仅现场完成前置验证后执行：只读观测+终端人工确认，仍不会自动接管
../sonic_deploy/.venv_teleop/bin/python apps/unitree_commission.py approve

# 撤销授权；运行中的适配器会退出
../sonic_deploy/.venv_teleop/bin/python apps/unitree_commission.py revoke
```

首次现场核验必须由现场工程师在可靠支撑和独立物理停止保障下，确认各关节方向/索引、增益、限幅及停止方式，填写真实结果。本工具提供检查和记录，不做自动增益辨识、自动试动作或虚构“已通过”。不能为了让接口通过而把 `gains_validated/stop_tested` 等标志直接改成true。

软件对参数施加的应用上限（不是厂家硬件安全额定值）：Kp/Kd不高于本次官方G1示例参考，目标速度≤0.5rad/s、加速度≤2rad/s²、单次步幅≤0.5rad、跟踪误差≤0.5rad、温度阈值≤75°C。模板的0.2rad/s、0.5rad/s²、0.35rad步幅也只是待核定软件候选值。每个电机的力矩阈值必须现场填写。

本地approve要求只读反馈静止、模式一致、唯一LowState源、无其他LowCmd与空闲官方服务，并要求终端输入明确现场确认短语。授权绑定机器指纹、本次开机、DDS网卡/域、模型hash、SDK源文件hash、控制代码hash以及实际LowState来源，最长4小时。机器人/DDS来源重启、更换机器人、重启4070、更新代码/SDK或调整参数后需要重新核验。不能把授权文件复制给其他部署包使用。

## 网页与接口

“真机环境 → 全身控制”新增“真机适配与标定”面板，展示硬件确认、协议、29个索引、SDK参考增益/待标定参数与四项现场状态。可下载**未批准**的通用模板；没有网页批准按钮。

OpenAPI 1.5.0：`apps/contracts/console-v1.openapi.json`，34 paths / 43 schemas。

- `GET /api/v1/console/robot/commissioning`：已授权操作员只读查看状态与参考参数，排除本地审批绑定数据。
- 同接口 `?template=1` 返回通用未批准模板。
- 原普通命令 `/robot/commands`：real initialize/claim/apply_pose/release经本地门槛与互斥；claim必须owner=manual与supported_operation_confirmed=true；apply/release需私有lease_token。
- 原高频 `/robot/manual` **仅允许heartbeat/apply_pose**，不能绕过普通命令的版本和接管流程。
- 快照 `manual` 为实际模式控制状态；无有效授权时不开放真机运动capabilities。G1真电量仍来自独立BMS订阅，适配器不制造电量。

## 离线证据与未完成事项

证据：[unitree-adapter-20261020](references/unitree-adapter-20261020)。包含SDK原示例快照、100项后端检查、18项前端检查、8项实际SDK/控制IPC/物理仿真集成检查及生产门槛核验。SDK DDS测试严格使用lo/Domain232，控制进程IPC测试使用内存传输与临时目录，不向真实机器人域发布。

待现场完成：本台G1的真实LowState/BMS、逐轴映射/方向、实际增益/限幅/温度/停止效果标定、物理动作验收、极端负载时序及控制源互斥核验。SONIC自动交接已暂缓；自由站立/平衡不属于本独立适配器能力。上次检查有线口仍NO-CARRIER，未获得本台真实LowState或BMS；用户确认的机型不等于这些现场验证已完成。
