# SONIC 控制器后端与有效反馈

更新：2026-10-20。网页入口为「SONIC 遥操作」，控制器运行在4070项目容器内。软件闭环已通过实际Docker/C++ TensorRT/MuJoCo隔离测试；PICO与G1的现场遥操作仍待验收。

## 使用流程

1. 选择仿真环境。点击「启动 SONIC 遥操作」或控制器卡片的「启动」；后台依次准备本项目Docker、XR PC Service、只读订阅、无窗口MuJoCo和固定参数的`g1_deploy_onnx_ref`。已运行的基础服务会复用。
2. 页面先显示启动、初始化，再显示「等待 PICO」。没有PICO时可以停在此处，不会伪造有效策略反馈。网页3D模型显示实际测量关节；无反馈时明确标注参考模型。
3. PICO4及腿部追踪器在现场完成全身标定，在连接配置确认标定后，后台只在身体追踪新鲜（≤500ms）时启动原SONIC PICO Manager。仍需原手柄操作开始控制/切换模式：A+X切换，A+B+X+Y开始/停止，具体以当前SONIC程序提示为准。网页启动不替代原手柄开始动作。
4. 点击「停止」先停止转发输入，发送原SONIC协议stop，确认容器内控制器退出，再关闭本次Manager与MuJoCo。Docker/XR保持待命，可另行点击各自停止。全局停止、工作台退出或网页后端丢失也会请求停止；重启不自动恢复运动。

「停止已确认」仅代表所托管进程退出与资源清理已确认，不能代替物理急停或证明机器人已机械静止。真机正常stop会走原C++退出/阻尼流程，其实际效果必须现场核验。若初始化期间无法处理stop，页面会显示退出未确认并阻止再次启动；真机不使用强制信号杀进程来伪装正常停止。

## 三层状态与反馈判据

| 状态 | 实际依据 |
| --- | --- |
| 进程运行 | immutable container ID内的固定可执行文件、UID、完整argv、专属session及PID/start ticks一致 |
| 初始化完成 | 控制器日志出现`Init Done`，并收到合法`robot_config`配置心跳 |
| 策略反馈有效 | `g1_debug`的`control_loop_type=cpp`；至少3个递增的非负整数`index`；29维测量关节及附带dq/action有限值；最后接受帧的单调时钟年龄≤500ms |

原生字段是`index`，HTTP对外映射为`control_index`。ZMQ模式`ros_timestamp=0`合法，不把它当冻结；重复、回退、无效帧不刷新有效期。配置心跳、打开端口或进程存在均不能证明策略正在执行。页面显示控制序号、接收频率、帧龄、进程/初始化状态与停止确认；3D优先使用`body_q_measured`，其顺序与已有MuJoCo具名映射一致，不能再次添加默认姿态偏移。接收频率不是机器人低层控制周期或实时性保证。

会话把校验反馈与精确进程归属组合使用；原生ZMQ数据本身没有加密身份凭据，不能宣称其经过密码学认证。

### 姿态视窗的实时计数

视窗左上角「绘制 FPS」统计浏览器实际完成绘制的频率；「姿态 Hz」统计浏览器应用新源时间戳测量的频率。同一快照反复应用不重复计数，机器人保持静止但源测量持续更新仍计数。至少两帧后形成频率；没有有效测量显示--，可见性/模式/来源变化会重新计量。

这两个数不代表MuJoCo步进、DDS接收或策略频率。网页目前仍每2秒取一次快照，所以可出现约30FPS绘制、约0.5Hz新姿态；本次增加计数器没有提高数据传输频率。提示文字说明各自口径。

## 输入代理与异常停止

原PICO Manager通过新增`--bind-host 127.0.0.1`发布到私有上游端口；托管worker独占配置中的回环输入端口，将新鲜追踪对应的原协议包转发给C++。HTTP不接受任意命令行、任意输入程序或合成PICO开关。

- PICO曾就绪后身体数据超过500ms或标定失效：立即阻断转发并请求正常stop。
- Manager退出，或首次数据超过30秒未到/已收到数据后超过1秒无包：请求stop。
- 开始指令后5秒仍无有效反馈，或曾有有效反馈后超过1秒无新帧/出现无效反馈：请求stop。500ms即取消页面「反馈有效」，1秒是停止判据。
- MuJoCo退出、控制器退出、网页后端PID身份丢失或显式停止：结束会话，不自动重新接管。
- 独立SDK手动控制、跨模式会话、重复启动、采集/准备占用和依赖服务停止均互斥。不会停止不属于本项目的外部控制器。

仿真强制`interface=lo`、Unitree DDS0；当前C++硬编码DDS0，其他域配置被明确拒绝。ROS相机Domain99保持独立。输入/反馈均要求不同的本机回环端口。仿真正常协议stop失败时仅允许核对身份后的pidfd SIGTERM；真机不采用该后备信号。

## 真机专项现场门槛

SONIC启动会释放原运动模式、进入默认站姿，并执行Dex3手部初始化动作。因此独立SDK关节标定不能替代SONIC专项验收。没有现场批准文件时，网页真机启动保持禁用，HTTP传`confirmed_real_start:true`也不能绕过。

现场人员使用4070本地工具（不会由网页自动批准）：

```sh
cd /home/harry/workspace/robot_station
/home/harry/workspace/sonic_deploy/.venv_teleop/bin/python apps/sonic_commission.py template
/home/harry/workspace/sonic_deploy/.venv_teleop/bin/python apps/sonic_commission.py inspect
# 实际核验并填写模板中的六项确认后，现场人员运行approve并输入程序要求的明确短语
/home/harry/workspace/sonic_deploy/.venv_teleop/bin/python apps/sonic_commission.py approve
```

批准最长4小时，绑定本机、本次开机、网卡/域、模型、SDK/控制代码/策略文件、唯一LowState来源与mode_machine，文件0600；还须网页单次明确确认。工具检查机械静止、唯一LowState、无竞争LowCmd及运动服务状态；不能用编辑布尔值替代现场确认。六项分别覆盖29维未锁腰、启动站姿、增益/限位、Dex3配置、正常停止和物理急停。该授权不得打包、提交或转移。当前没有创建有效SONIC真机授权、没有执行真机动作。

## API与日志

- `POST /api/v1/console/services/actions`：既有命令信封，`action=start|stop`、`payload.service_id=controller`。沿用授权、CSRF、expected_revision与Idempotency-Key；真机启动另需`confirmed_real_start:true`。start返回`state:accepted`，随后轮询状态，不能把接收成功当作启动完成。
- `GET /api/v1/console/controller?mode=sim|real`：会话状态与start/stop阻止原因。
- `GET /api/v1/console/controller/logs?mode=sim|real&component=...`：授权读取有界日志；component仅允许supervisor/controller/manager/simulator/preparation。
- 快照新增`sonic`，services.controller携带同一状态；运行任务占用与真实关节owner同时更新。

日志及状态位于`apps/.runtime/console/sonic-control`，每次运行单独UUID目录。停止未确认保留身份及日志，使用原停止入口可恢复核对与stop，不自动重新启动控制。OpenAPI **1.7.0，36 paths / 45 schemas**。依赖安装见[integrations/sonic](../integrations/sonic/README.md)；验证材料见[验收记录](references/sonic-controller-20261020/README.md)。
