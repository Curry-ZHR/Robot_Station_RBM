# SONIC 容器与 XRoboToolkit 启停

更新：2026-10-20。两个服务运行在4070，属于跨real/sim模式共享的基础服务。网页“整机管理 → 运行服务”提供实际启动和停止；机器人控制器另行管理。

## 网页操作

- **SONIC容器 → 停止**：核对项目标签、固定容器ID及容器内进程后，停止本项目待命容器，保留容器、镜像、模型及数据。控制器、构建或交互终端仍在容器中运行时拒绝停止。
- **XRoboToolkit → 停止**：同时关闭本项目的PC Service与Unity 3D客户端，核对进程用户、完整可执行路径、启动时间和Linux pidfd后发送SIGTERM，确认进程与gRPC退出。其他安装目录的服务不由本按钮停止。
- 请求进行中按钮显示“停止中…”，完成后快照显示“已停止”。失败或超时显示具体原因，不能把未确认退出标为停止成功。
- **重新启动**：SONIC按钮恢复待命容器；XRoboToolkit按钮显式启动PC Service，供PICO/SDK连接。Unity 3D可视化仍用已有桌面入口或下述`3d`命令单独打开。
- 采集任务、手动控制、准备任务，或仍运行的SONIC/遥操作/推理客户端会阻止停止。按钮悬停提示原因，后端在执行时再次检查；切换real/sim不绕过另一个模式的占用。

停止基础服务不等于机器人硬件急停。真实控制器运行期间应先按现场流程结束运动与控制，再停止依赖服务。工作台根目录`stop.sh`保持其既有的网页、只读和托管任务关闭职责，不以停止容器或XR服务代替机器人停止流程。

## XR扩展安装与命令行

扩展源码随Robot Station存放在`integrations/sonic/xrobotoolkit_runtime.py`，详见 [集成说明](../integrations/sonic/README.md)。从旧部署升级时：

```sh
bash scripts/install_xrobotoolkit_lifecycle.sh /home/harry/workspace/sonic_deploy
```

安装器备份原文件，拒绝覆盖不属于已核验基线的自定义改动。部署后可运行：

```sh
# 项目PC Service与Unity一并停止；不会删除安装文件
/home/harry/workspace/sonic_deploy/run_xrobotoolkit.sh stop

# 显式恢复后台PC Service
/home/harry/workspace/sonic_deploy/run_xrobotoolkit.sh service

# 在Ubuntu图形桌面中恢复PC Service及Unity 3D
/home/harry/workspace/sonic_deploy/run_xrobotoolkit.sh 3d

/home/harry/workspace/sonic_deploy/run_xrobotoolkit.sh status
```

停止标记保存在SONIC的`outputs/xrobotoolkit/service.stopped`。隐式`ensure_service()`遇到此标记会报告需要显式启动，防止刚停止就被SDK/PICO准备逻辑重新拉起；显式`service`或`3d`在共用生命周期文件锁内清除标记。进程未在期限内退出时不自动发送SIGKILL，标记保留，页面报告未确认退出。

## 接口合同

继续使用`POST /api/v1/console/services/actions`，无需新增URL。OpenAPI **1.6.0**，34 paths / 43 schemas：

```json
{
  "action": "stop",
  "mode": "real",
  "profile_id": "unitree-g1-29",
  "expected_revision": 123,
  "payload": {"service_id": "docker"}
}
```

XR服务使用`service_id:pc_service`。示例revision必须替换为最新快照值；写入沿用操作员授权、同源/CSRF和`Idempotency-Key`协议。不要在配置或日志中记录密钥/会话/CSRF。

只有确认资源退出才返回`state:stopped`。相同请求和幂等键重试返回原确认，不重复发送终止信号。409表示任务/控制器/资源归属冲突，503表示停止失败或未确认；失败后必须查看新的实际状态。

快照`services.docker`与`services.pc_service`补充`stop_allowed`、`stop_reason`及资源归属`owned`；XR补充`unity_running`。按钮以这些字段和能力列表门控，机器人反馈离线不妨碍停止闲置基础服务。工作台看护不自动重启这两项；重新准备或点击启动属于显式启动。
