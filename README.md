# Robot_Station_RBM

Robot Station 是面向机器人操作、数据采集和推理工作流的工作台。本仓库保留现有项目历史，后续统一在 `main` 分支维护。

## 项目结构

- `frontend/`：操作界面与机器人可视化。
- `backend/`：HTTP API、任务协调与服务入口。
- `modules/`：ROS 2 通信、设备控制、自检、采集、回放、推理、标定及导航等模块。
- `ros_packages/`：控制、传感器和定位相关 ROS 2 包。
- `config/`：设备接口与坐标变换配置。
- `tests/`：现有自动化测试。
- `docs/`：架构与操作界面说明。

## 运行入口

项目基于 Linux、Python 3 和 ROS 2，当前启动脚本默认使用 ROS 2 Humble。使用前需安装后端依赖，并准备对应硬件的 SDK、ROS 工作空间与设备权限。

```bash
python3 -m pip install -r backend/requirements.txt
./run.sh
```

默认 Web 端口为 `9999`，控制端口为 `9998`；`run.sh` 中还包含 ROS 工作空间准备与构建逻辑。启动前请检查脚本和机器人配置，避免在未准备好的真机环境直接运行。

当前启动脚本默认设置 `ROS_DOMAIN_ID=99`、`ROS_LOCALHOST_ONLY=0`。跨机器使用时需要匹配 ROS 通信环境、消息定义和网络配置。当前设备自检及硬件驱动的进程管理仍以本机为目标，远程部署需要相应适配。

## 后续方向

持续完善推理与数据回放、数据采集、数据质检，以及工作站与机器人执行端之间的职责划分。以上为演进方向，不代表全部功能已完成。

架构说明见 [docs/architecture.md](docs/architecture.md)。
