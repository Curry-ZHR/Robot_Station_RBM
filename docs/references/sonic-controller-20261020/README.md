# 2026-10-20 SONIC控制器后端验收

软件范围：托管C++控制器启停、回环输入代理、真实反馈、日志、网页与故障停止。未连接物理G1或PICO，未生成有效SONIC真机授权，未执行真机动作。

- `backend-tests.log`：126项全部通过，无跳过；包括实际SDK/XR辅助扩展与ZMQ测量反馈校验。
- `frontend-tests.log`：20项全部通过。
- `closed-loop-result.json`：实际Docker/C++ TensorRT/无窗口MuJoCo + 合成IDLE输入，仅lo/DDS0和临时回环端口。正常停止、追踪断流、反馈冻结、父进程退出、Manager输入冻结、开始后无有效反馈，6例全部通过。每例均核对专属控制器退出与`Program exiting normally`，测试子进程随后清理。
- `api-integration-result.json`：隔离HTTP启动→初始化→等待PICO→停止；重复/跨模式/依赖服务停止拒绝，真机412门槛不能被HTTP布尔参数绕过。实际快照/控制器/命令响应通过OpenAPI1.7.0 schema验证。

有效反馈要求至少3个递增`index`、cpp标识、29维有限测量值和≤500ms接收帧龄。日志或配置心跳不能代替策略反馈。接收帧率不能证明真机低层实时性。真机默认站姿/Dex3动作、增益与正常停止仍须专项现场验收。

部署及网页复核在`deployment-verification.json`与截图记录；工作台部署前无任务、无录制、机器人离线，保留既有Docker/XR待命，Unity保持关闭。当前源码变更未另行commit/push。

正式页面通过浏览器实际点击一键仿真启动、读取日志、停止，显示“初始化完成/等待PICO”以及“进程退出已确认”。`live-waiting-pico.png`记录运行待命时的真实状态；`live-stopped.png`记录测试结束。均非preview合成页面。静态页面与后端均已部署，systemd主管已重启加载新版本；最终Docker/XR待命，控制器/Manager/MuJoCo已退出，Unity保持关闭。

2026-10-20姿态视窗新增实测频率标签：`viewer-performance.png`记录正式页面约30FPS绘制、约0.5Hz姿态更新。计数器与追加3项计量测试通过（前端合计23项）；只更新静态资源，未重启/启停原有仿真会话或调用机器人控制。
