# Robot Station 应用目录

当前 G1 工作台的网页、HTTP API、设备适配和工作进程位于本目录，统一使用项目根目录的入口管理。

首次使用请读 [项目 README](../README.md)，其中包含下载、无需机器人预览、依赖准备和完整部署步骤。

## 日常运行

在项目根目录执行：

```bash
./run.sh
./run.sh status
./run.sh logs
./stop.sh
```

默认网页端口为 **9999**，现有部署地址为 `http://192.168.123.100:9999/`。根 `run.sh` 管理 systemd 用户服务及托管任务；启动网页不自动启用机器人运动。

本目录 `run.sh` 是直接前台运行 Web 的开发入口，默认同样使用 9999。它不经过常驻主管，不要与根入口同时使用；按 `Ctrl+C` 关闭。本目录 `stop.sh` 是保留的旧 PID 文件工具，不用于停止新的 systemd 服务。

## 代码与配置

- `static/`：原生 ES Modules 前端、Three.js、G1 模型与演示资源。
- `server.py`、`console_runtime.py`：HTTP 入口和统一状态/命令协调。
- `console_driver.py`、`station_supervisor.py`：设备/服务适配与常驻进程管理。
- `ros2_camera_bridge.py`：ROS 2 三路图像到 ZMQ 的桥接。
- `console_collection*`、`dataset_conversion.py`：采集和离线转换。
- `unitree_g1_*`、`console_real*`：Unitree SDK 适配及现场授权门槛。
- `contracts/`、`tests/`：接口规范和验证。
- `.runtime/`、`.venv_*/`：本机运行状态与隔离依赖，不纳入版本控制。

更多说明：[运行维护](../docs/station_operations.md)、[后端接入](../docs/data_collection_console.md)、[SDK 与现场标定](../docs/g1_sdk_adapter.md)、[最新交接](../HANDOFF.md)。
