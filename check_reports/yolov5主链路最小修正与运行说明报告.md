# YOLOv5 主链路最小修正与运行说明报告

生成日期：2026-04-26

本轮目标是最小修正与运行说明固化。未重写控制器，未修改 `line_detector.py` 的控制公式，未删除旧 HSV、旧 `yolo/` 或 `yolov5/` 目录，未引入 ROS2、ament 或 colcon。

## 1. 修改文件清单

| 文件 | 修改内容 | 修改原因 | 是否影响控制主体 |
| --- | --- | --- | --- |
| `catkin_ws/src/robot_vision/launch/seam_tracking.launch` | 将 `model_path`、`yolov5_repo_path`、`yolo_repo_path` 默认值从 `/home/bn/bsnew/...` 改为基于 `$(find robot_vision)/../../../...` 的仓库内路径 | 避免写死当前机器绝对路径，使工程迁移到 `~/bsnew` 同类结构时仍可运行 | 否 |
| `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` | 增加 `default_project_root()`，将单独运行节点时的默认权重、YOLOv5、旧 YOLO 路径改为按脚本位置推导；启动日志补充 topic；无检测时增加节流 warning | 让 YOLO 节点默认路径更可迁移，并方便调试目标丢失 | 否 |
| `README.md` | 重写运行说明，明确当前主链路是 YOLOv5 + 原控制逻辑；给出构建、运行、调试命令；标注旧 HSV/旧 `yolo/` 为备用/历史方案 | 避免继续使用旧 `../yolo/runs/...` 示例路径，固化当前主入口 | 否 |
| `check_reports/yolov5主链路最小修正与运行说明报告.md` | 新增本报告 | 记录修改原因、运行方式和风险 | 否 |

## 2. 是否改动控制公式

没有改动 `line_detector.py`。

原控制主体仍为：

```text
robot_vision/scripts/line_detector.py
```

核心控制函数仍为：

```text
twist_calculate(width, center)
```

控制公式保持原样：

```text
if 0.95 < center / width < 1.05:
    linear.x = 0.2
else:
    angular.z = ((width - center) / width) / 2.0
    if abs(angular.z) < 0.2:
        linear.x = 0.2 - angular.z / 2.0
    else:
        linear.x = 0.1
```

其中在 YOLOv5 外部中心模式下：

```text
width  = image_width / 2.0
center = center_x
```

所以控制偏差方向是：

```text
image_width / 2.0 - center_x
```

如果论文中写成 `center_x - image_width / 2.0`，需要说明那是视觉几何偏差定义；控制代码内部实际用于角速度的是相反号。

## 3. 当前主链路

当前推荐主链路：

```text
/image_raw
-> robot_vision/scripts/yolo_seam_detector.py
-> /seam_center
-> robot_vision/scripts/line_detector.py
-> /cmd_vel
-> base_control 或 Gazebo 仿真执行
```

`seam_tracking.launch` 中：

| 模块 | 启动方式 |
| --- | --- |
| 图像输入 | `use_fake_camera:=true` 时启动 `fake_camera.py`；否则 include `robot_camera.launch` |
| YOLOv5 前端 | 启动 `yolo_seam_detector.py` |
| 原控制后端 | 启动 `line_detector.py`，并设置 `use_external_center=true` |
| 底盘桥 | `run_base_control:=true` 时 include `base_control.launch` |

旧 HSV 主视觉入口 `line_follow.launch` 不会被 `seam_tracking.launch` 启动。

`seam_tracking.launch` 里只有 `line_detector.py` 发布 `cmd_vel`；`base_control.py` 是订阅 `cmd_vel` 并转发到底盘，不是另一个 `cmd_vel` 发布者。

## 4. 权重路径

当前权重文件推荐放置位置：

```text
bsnew/models/seam_best.pt
```

当前 launch 默认路径：

```text
$(find robot_vision)/../../../models/seam_best.pt
```

按当前仓库结构展开后等价于：

```text
~/bsnew/models/seam_best.pt
```

YOLOv5 代码路径默认值：

```text
$(find robot_vision)/../../../yolov5
```

旧 `yolo/` 备用后端路径默认值：

```text
$(find robot_vision)/../../../yolo
```

## 5. `/seam_center` 字段含义

消息类型：

```text
geometry_msgs/Point
```

字段含义：

| 字段 | 含义 | 来源 |
| --- | --- | --- |
| `x` | `center_x`，YOLOv5 最优检测框中心横坐标 | `(x1 + x2) / 2.0` |
| `y` | `image_width`，输入图像宽度 | `cv_image.shape[:2]` |
| `z` | `valid_flag`，有效检测标志 | 有检测为 `1.0`，无检测为 `0.0` |

无目标时发布：

```text
x = -1.0
y = image_width
z = 0.0
```

`line_detector.py` 收到 `z <= 0.5` 或宽度无效时会发布零速度。

## 6. 回到 Ubuntu 18.04 ROS1 后的构建命令

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
```

不要从 `~/bsnew` 根目录运行 `catkin_make`。

## 7. 运行命令

### 7.1 假相机调试，不接底盘

先运行这一条，验证权重加载、YOLOv5 推理、`/seam_center` 和 `/cmd_vel`：

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash

roslaunch robot_vision seam_tracking.launch \
  use_fake_camera:=true \
  run_base_control:=false \
  device:=cpu
```

### 7.2 真实相机调试，不接底盘

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash

export BASE_TYPE=NanoCar
export CAMERA_TYPE=csi72

roslaunch robot_vision seam_tracking.launch \
  use_fake_camera:=false \
  camera_device:=video0 \
  run_base_control:=false \
  device:=cpu
```

`BASE_TYPE` 和 `CAMERA_TYPE` 需要按实际硬件确认。

### 7.3 真实底盘运行

只在视觉和控制输出已经确认正常后运行：

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash

export BASE_TYPE=NanoCar
export CAMERA_TYPE=csi72

roslaunch robot_vision seam_tracking.launch \
  use_fake_camera:=false \
  camera_device:=video0 \
  run_base_control:=true \
  device:=cpu
```

首次实机测试应架空车轮或准备急停。

## 8. 调试命令

新开终端后先 source：

```bash
source /opt/ros/melodic/setup.bash
source ~/bsnew/catkin_ws/devel/setup.bash
```

查看 YOLOv5 输出：

```bash
rostopic echo /seam_center
```

判断方式：

```text
z: 1.0  表示检测有效
z: 0.0  表示当前无有效检测，控制器应停车
```

查看控制输出：

```bash
rostopic echo /cmd_vel
```

查看结果图像：

```bash
rqt_image_view /result_image
```

查看 topic 连接关系：

```bash
rostopic info /seam_center
rostopic info /cmd_vel
rqt_graph
```

验证目标丢失停车：

1. 启动主链路。
2. 让图像中没有焊缝目标，或临时遮挡目标。
3. 查看 `/seam_center.z` 是否变为 `0.0`。
4. 查看 `/cmd_vel` 是否变为全零。

## 9. 需要实机验证的内容

| 项目 | 为什么需要实机验证 |
| --- | --- |
| 摄像头设备名 `video0` | 不同机器可能是 `video0`、`video1` 等 |
| `BASE_TYPE`、`CAMERA_TYPE` | 相机 launch 使用环境变量选择底盘和相机配置 |
| YOLOv5 检测效果 | 权重是否适配实际焊缝、光照和相机角度只能实测确认 |
| `angular.z` 正负方向 | 控制公式未改，但相机安装方向和底盘坐标方向需要实车确认 |
| 串口 `/dev/move_base` | 底盘权限、设备名、波特率需要硬件确认 |
| 安全停止 | 无目标和输入超时停车必须在硬件上低速验证 |

## 10. Python3 / ROS Melodic 兼容风险

当前 YOLOv5 节点：

```text
robot_vision/scripts/yolo_seam_detector.py
```

使用 Python3 shebang：

```text
#!/usr/bin/env python3
```

风险点：

| 风险 | 说明 |
| --- | --- |
| ROS Melodic 默认 Python2 | Python3 节点必须能 import `rospy` |
| `cv_bridge` 兼容 | Python3 需要可用的 `cv_bridge` |
| `torch` 版本 | Ubuntu 18.04 / Python3.6 不适合安装过新的 PyTorch |
| `opencv-python` | 不建议用 pip 的 `opencv-python` 覆盖 ROS/OpenCV 环境，优先系统 `python3-opencv` |
| YOLOv5 v6.0 依赖 | 当前 `yolov5/` 是 v6.0，权重加载应使用匹配环境验证 |

运行前建议检查：

```bash
python3 -c "import rospy; print('rospy ok')"
python3 -c "from cv_bridge import CvBridge; print('cv_bridge ok')"
python3 -c "import cv2; print(cv2.__version__)"
python3 -c "import torch; print(torch.__version__)"
python3 -c "import os, sys; sys.path.insert(0, os.path.expanduser('~/bsnew/yolov5')); from models.experimental import attempt_load; print('yolov5 import ok')"
```

## 11. 本轮静态验证结果

已完成的轻量验证：

| 验证项 | 结果 |
| --- | --- |
| `yolo_seam_detector.py` Python3 语法编译 | 通过 |
| `seam_tracking.launch` XML 解析 | 通过 |
| `models/seam_best.pt` 是否存在 | 存在，约 14 MB |
| `yolov5/` 是否存在 | 存在，版本 `v6.0`，提交 `956be8e` |
| `line_detector.py` 是否被本轮修改 | 未修改 |
| 本机 ROS Melodic | 缺失，无法本机 roslaunch |
| 本机 torch | 缺失，无法本机加载权重 |

因此，本轮完成的是源码级和配置级检查。真实运行仍需回到 Ubuntu 18.04 + ROS Melodic 虚拟机验证。

## 12. 本轮结论

1. 已完成最小修正，主链路仍是 YOLOv5 视觉前端加原控制后端。
2. 旧 HSV、旧 `yolo/`、`yolov5/` 原仓库均未删除。
3. `line_detector.py` 控制主体和控制公式未改。
4. 当前推荐主入口是：

```bash
roslaunch robot_vision seam_tracking.launch
```

5. 最大剩余风险是 Ubuntu 18.04 + ROS Melodic 的 Python3、`rospy`、`cv_bridge`、`torch` 兼容性，以及实车方向和安全停车验证。
