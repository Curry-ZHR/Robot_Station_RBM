# 2026-10-20 Unitree G1 适配软件验收

软件检查去重合计126项：后端100、前端18、实际SDK/IPC/物理仿真新增集成8。

- backend-tests.log：100项，含原采集/转换/回放/访问控制与新协议/CRC/映射/限位/轨迹极值/C2/看护/本地标定门槛测试。
- frontend-tests.log：18项。
- sdk-and-control-tests.log：26项，其中18项与backend重复；新增8项为官方参考增益、实际HG IDL/独立CRC布局、实际LowState CRC、lo/Domain232 DDS收发及竞争发布者/来源绑定、manager无审批拒绝、真实进程IPC接管/心跳/目标/释放/重启撤销、MuJoCo物理步进与租约测试。IPC测试使用内存传输和临时目录，未连接机器人域。
- release-verification.json：生产文件保持approved=false、0600；完整29自由度未锁腰按用户确认记录；通用模板UNCONFIRMED/approved=false；real初始化/接管/下发HTTP412；网页审批路由不存在；未自启manual-real。
- real-commissioning-status.png：真实后端网页展示，非浏览器合成预演。
- sdk/g1_low_level_example.py：本地官方SDK示例快照，仅供审阅；本适配器不运行其中自动释放官方控制器、归零或摆动逻辑。

没有执行G1实际动作。增益、机械支撑、力矩边界、停止效果、实际控制时序和SONIC交接仍待现场验证；测试不等于完成实机标定。当前用户确认机型不能替代这些验证。
