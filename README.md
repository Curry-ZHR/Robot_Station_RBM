# Robot_Station_RBM

开发接续请先读 [HANDOFF.md](HANDOFF.md)，其中记录最新样式参考、`apps/` 当前状态及与 `sonic_deploy` 的分工。

Robot Station 是面向机器人操作、数据采集和推理工作流的工作台。本仓库保留现有项目历史，后续统一在 `main` 分支维护。

## 当前 G1 / SONIC 工作台入口

4070上的统一运行入口是根目录 `./run.sh`，关闭入口是 `./stop.sh`；已安装的 `robot-station.service` 随开机启动网页与只读服务。网页地址为 `http://192.168.123.100:9999/`。启动网页不自动使能机器人运动。

- 使用与部署：[运行说明](docs/station_operations.md)、[后端接口接入](docs/data_collection_console.md)。
- 计算分工：[HPC / 4090 / 4070 与 G1 执行侧](handoff_distribution.md)。
- 真机关节适配：[SDK与现场标定](docs/g1_sdk_adapter.md)，运动输出仍有本地现场门槛。
- 整机管理支持停止本项目待命SONIC容器，以及XRoboToolkit PC Service和Unity；采集/控制/准备期间阻止停止。XR扩展随仓库提供，首次安装或从旧版本升级时运行 `bash scripts/install_xrobotoolkit_lifecycle.sh /path/to/sonic_deploy`，见 [集成说明](integrations/sonic/README.md)。
- 当前任务模型推理和后台状态机执行仍按规划后置；`.deb` 安装包尚未制作，交付提醒见主handoff第0L节。

下文保留原平台的通用ROS背景；原根ROS启动器已迁为 `run_legacy_ros.sh`，不作为G1工作台默认入口。

## 项目结构

- `frontend/`：操作界面与机器人可视化。
- `backend/`：HTTP API、任务协调与服务入口。
- `modules/`：ROS 2 通信、设备控制、自检、采集、回放、推理、标定及导航等模块。
- `ros_packages/`：控制、传感器和定位相关 ROS 2 包。
- `config/`：设备接口与坐标变换配置。
- `tests/`：现有自动化测试。
- `docs/`：架构与操作界面说明。
- `apps/`：通用数据采集工作台，包含原 Data_platform 的网页、HTTP API、机器人适配器、测试及本地运行数据。

## 数据采集工作台

这套工作流统一维护两个同级目录：`robot_station/apps` 管理可视化界面和操作 API，`sonic_deploy` 管理 SONIC 机器人程序、模型、Python 环境与采集输出。原 `Data_platform` 已整体迁入 `apps/`，不保留机器人专属子目录，后续机器人通过适配器接入。

```bash
cd /home/harry/workspace/robot_station
./run.sh apps start
./run.sh apps status
```

默认仅启动 `127.0.0.1:2947` 的 Web 服务。Mac 使用 `ssh -N -L 12947:192.168.123.100:9999 harry@100.104.144.88` 转发后，打开 `http://127.0.0.1:12947/?view=collection`。

支持 `./run.sh apps stop`、`restart`、`foreground`、`logs`，也可在 `apps/` 内执行 `./run.sh` 前台运行界面；修改底层仓库位置时设置 `SONIC_REPO_ROOT`。Web 服务启动不会自动启动机器人。当前机器人程序由适配器调用 `sonic_deploy` 的官方启动器。

迁移结构、接口及启动方式见 [docs/data_collection_console.md](docs/data_collection_console.md)。

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
