# YOLOv5 Ubuntu 18.04 ROS1 部署说明

## 目标运行环境

- Ubuntu 18.04.6
- ROS1 Melodic
- Python 3.6.9
- torch 1.10.1+cu102
- torchvision 0.11.2+cu102
- OpenCV 和 ROS `cv_bridge` 已可用

## 当前默认检测后端

`robot_vision/scripts/yolo_seam_detector.py` 默认使用本地 YOLOv5 v6.0 后端：

- 默认后端：`yolov5`
- YOLOv5 仓库建议路径：`/home/bn/bsnew/yolov5`
- 权重建议路径：`/home/bn/bsnew/models/seam_best.pt`

系统不再默认使用 `/home/bn/bsnew/yolo` 下的魔改 Ultralytics 仓库，也不默认依赖 `timm`、`mmcv-full`、Gold-YOLO、dyhead、ConvNeXtV2、CARAFE 或新版 `ultralytics` pip 包。

旧 Ultralytics 路径只作为备用后端保留：

```bash
roslaunch robot_vision seam_tracking.launch detector_backend:=legacy_ultralytics
```

正常部署不要使用该备用后端。

## 获取 YOLOv5 v6.0

```bash
cd /home/bn/bsnew
git clone --branch v6.0 --depth 1 https://github.com/ultralytics/yolov5.git yolov5
```

不要使用 YOLOv5 main 分支，不要使用 `torch.hub` 从网络下载模型。

## Python 依赖建议

不要直接执行 YOLOv5 仓库的完整 `requirements.txt`，其中可能包含 `opencv-python`，容易干扰 ROS `cv_bridge` 使用的系统 OpenCV。

建议手动安装基础依赖：

```bash
python3 -m pip install --user \
  "numpy==1.19.5" \
  "Pillow==8.4.0" \
  "PyYAML==5.4.1" \
  "matplotlib==3.3.4" \
  "scipy==1.5.4" \
  "tqdm==4.64.1" \
  requests \
  "pandas==1.1.5" \
  "seaborn==0.11.2"
```

如果 `python3 import cv2` 失败，优先安装系统 OpenCV：

```bash
sudo apt install python3-opencv
```

不要优先使用 `pip install opencv-python`。

## 运行前检查

```bash
python3 -c "import cv2; print(cv2.__version__)"
python3 -c "import torch; print(torch.__version__)"
python3 -c "import torchvision; print(torchvision.__version__)"
python3 -c "import sys; sys.path.insert(0, '/home/bn/bsnew/yolov5'); from models.experimental import attempt_load; print('yolov5 import ok')"
find /home/bn/bsnew -iname "*.pt"
```

如果没有 `/home/bn/bsnew/models/seam_best.pt` 或其他可用 `.pt` 权重，不能启动真实检测。节点会明确报：

```text
model file does not exist
```

这种情况不应该再出现 `ultralytics`、`timm`、`mmcv`、ConvNeXtV2 或 CARAFE 相关错误。

## 编译

```bash
cd /home/bn/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
```

## 真实相机运行示例

```bash
export BASE_TYPE=NanoCar
export CAMERA_TYPE=csi72

cd /home/bn/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash

roslaunch robot_vision seam_tracking.launch \
  detector_backend:=yolov5 \
  yolov5_repo_path:=/home/bn/bsnew/yolov5 \
  model_path:=/home/bn/bsnew/models/seam_best.pt \
  device:=cpu \
  run_base_control:=false
```

如果需要指定摄像头设备，使用 `camera_device`：

```bash
roslaunch robot_vision seam_tracking.launch camera_device:=video0
```

`device` 参数现在用于检测后端，默认 `cpu`。如果后续确认 GPU 可用，可以传 `device:=0`。

## 假图片测试示例

```bash
roslaunch robot_vision seam_tracking.launch \
  detector_backend:=yolov5 \
  yolov5_repo_path:=/home/bn/bsnew/yolov5 \
  model_path:=/home/bn/bsnew/models/seam_best.pt \
  device:=cpu \
  use_fake_camera:=true \
  fake_image_path:=$(rospack find robot_vision)/data/bingda.png \
  run_base_control:=false
```

## ROS 接口语义

检测节点继续订阅图像话题，默认：

- `~image_topic`：`/image_raw`

检测节点继续发布：

- `~center_topic`：默认 `/seam_center`
- `~result_topic`：默认 `/result_image`

`/seam_center` 使用 `geometry_msgs/Point`，语义保持不变：

- `Point.x`：检测框中心 x 坐标
- `Point.y`：图像宽度 `image_width`
- `Point.z`：`1.0` 表示检测有效，`0.0` 表示无检测

无检测时发布：

```text
Point.x = -1.0
Point.y = image_width
Point.z = 0.0
```

## 最终链路

```text
ROS Image
-> cv_bridge 转 OpenCV BGR 图像
-> YOLOv5 v6.0 推理
-> 选择置信度最高的焊缝检测框
-> 计算检测框中心 x
-> 发布 /seam_center
-> 原 line_detector.py 外部中心点模式
-> 原 twist_calculate() 控制律
-> cmd_vel
-> 可选 base_control 底盘接口
```

原控制节点接口和 `/seam_center` 语义没有改变。`line_detector.py` 仍然负责根据中心偏差计算 `cmd_vel`，检测无效或超时时发布停止速度。

## 相关包角色

- `robot_vision`：主视觉检测、YOLO 焊缝检测入口、原始线跟随控制逻辑。
- `base_control`：可选底盘串口控制桥，由 `run_base_control:=true` 启动。
- `nanoomni_description`：机器人描述和仿真支持包，包含 URDF/Xacro、RViz、Gazebo、mesh 和仿真 launch，不是主焊缝跟踪控制方法。

## 硬件测试注意

源码层面的接口已经保持 ROS1/catkin 结构，但真实闭环仍需在 Ubuntu 18.04 + ROS Melodic 虚拟机和实际相机/底盘上验证：

- 相机 `/image_raw` 是否稳定发布。
- `seam_best.pt` 是否能正确检测焊缝。
- `/seam_center` 的中心偏差方向是否与车辆转向方向一致。
- `run_base_control:=true` 时底盘串口 `/dev/move_base` 是否可用。
- 实车速度和转向参数是否需要低速现场微调。
