# 数据采集工作台

现位于 `robot_station/apps/`，原 Data_platform 的全部文件已迁入此目录，不保留 `sonic` 子目录。界面与操作 API 统一在这里维护，当前底层机器人程序和数据使用同级 `sonic_deploy`。在 Robot Station 根目录使用 `./run.sh apps start` 启动，`./run.sh apps stop` 停止，`./run.sh apps status` 查看状态。

本次采集页新增场景配置、真实/演示记录区分、分页记录、人工 A/B/F 评级和多路视频回看，接口说明见 `../docs/data_collection_console.md`。当前 `sonic_adapter.py` 是机器人专属适配层，后续其他机器人可接入同一套网页和记录接口。

统一的本机数据采集控制台，当前通过适配器连接 `sonic_deploy`，提供：

- Sonic 采集栈启动、停止和 tmux 进程状态
- 通过 ZMQ `5580` 控制片段开始、保存和丢弃
- 14 DoF 关节、温度、开发机资源和三视角视频监控
- 数据质量筛选：采样频率、丢帧、同步偏差、关节异常和动作突变
- LeRobot v2.1 数据管理、质量评分、来源追溯与 Sonic 数据清洗
- 设备与数据告警、近七日趋势和汇报摘要导出
- 相机、PICO/SMPL、机器人状态和控制端点诊断
- 真机启动、停止和丢弃操作二次确认

未接入机器人遥测和相机流时，实时监控页会显示明确标注的演示数据；开发机资源和输出目录统计始终读取真实数据。

## 启动

```bash
cd /home/harry/workspace/robot_station/apps
./run.sh
```

服务默认只监听 `127.0.0.1:2947`：

```text
http://localhost:2947
```

停止通过后台方式启动的服务：

```bash
cd /home/harry/workspace/robot_station/apps
./stop.sh
```

从 Mac 访问开发机上的本机端口：

```bash
ssh -N -L 12947:127.0.0.1:2947 harry@100.104.144.88
```

然后在 Mac 浏览器打开 `http://127.0.0.1:12947`。

## Sonic 前置项

平台会在“系统诊断”页检查依赖。当前 Sonic 标准采集栈要求：

```bash
sudo apt install tmux
cd /home/harry/workspace/sonic_deploy
bash install_scripts/install_data_collection.sh
```

服务启动不会自动连接或驱动机器人。只有在页面确认启动后，后端才调用 Sonic 官方 `launch_data_collection.py`。

## 配置

```bash
DATA_PLATFORM_HOST=127.0.0.1
DATA_PLATFORM_PORT=2947
SONIC_REPO_ROOT=/home/harry/workspace/sonic_deploy
```
