# 机器人小车实车部署与实验记录流程

本文档用于把当前 `bsnew` 项目部署到机器人小车，并记录焊缝跟踪实验曲线。项目主目标环境仍是 Ubuntu 18.04 + ROS Melodic + `catkin_make`；如果小车已经安装 ROS Noetic，可按本文的 Noetic 兼容步骤实车运行。不要把本项目改成 ROS2，也不要使用 `ament` 或 `colcon`。

当前主链路保持不变：

```text
/image_raw
-> robot_vision/scripts/yolo_seam_detector.py
-> /seam_center
-> robot_vision/scripts/line_detector.py
-> /cmd_vel
-> base_control / 底盘
```

## 1. 推荐工作方式

推荐使用 Windows 里的 Ubuntu 虚拟机作为开发和远程操作端，机器人小车作为运行端。

整体流程：

1. Windows 里的 Ubuntu 虚拟机设置桥接网络。
2. 确认虚拟机能 `ping` 通小车 IP。
3. 从虚拟机通过 SSH 登录小车。
4. 在小车上安装 ROS Noetic 依赖、Python 依赖和 YOLOv5 推理依赖。
5. 从虚拟机把 `bsnew` 项目复制到小车。
6. 在小车上进入 `~/bsnew/catkin_ws` 执行 `catkin_make`。
7. 先用假相机测试 YOLO、`/seam_center` 和 `/cmd_vel`，不要启用底盘。
8. 再用真实相机测试检测结果，仍然不要启用底盘。
9. 最后启用 `run_base_control:=true`，先架空轮子测试，再落地低速测试。
10. 用 `rosbag` 或 CSV 记录实验数据并绘制曲线。

## 2. 虚拟机 SSH 远程登录小车

虚拟机网络建议设置为：

```text
Bridged Adapter / 桥接模式
```

这样虚拟机和小车会像两台真实电脑一样处在同一个局域网内。

在小车上查看 IP：

```bash
hostname -I
ip addr
```

在虚拟机中测试网络：

```bash
ping 小车IP
```

能 `ping` 通后，从虚拟机登录小车：

```bash
ssh 用户名@小车IP
```

如果小车没有开启 SSH，需要先在小车本机执行：

```bash
sudo apt update
sudo apt install openssh-server
sudo systemctl enable ssh
sudo systemctl start ssh
sudo systemctl status ssh
```

如果第一次不知道小车 IP、Wi-Fi 没配好、SSH 没开，可能需要临时外接显示器、键盘和鼠标。配置好网络和 SSH 后，后续安装依赖、编译、运行都可以通过 SSH 完成。

## 3. 小车 ROS Noetic 依赖安装

以下命令在小车 SSH 终端中执行。Noetic 是 ROS1，不是 ROS2，所以仍然使用 `catkin_make` 和 `roslaunch`。

```bash
sudo apt update
sudo apt install ros-noetic-cv-bridge ros-noetic-image-transport ros-noetic-geometry-msgs ros-noetic-sensor-msgs ros-noetic-std-msgs
sudo apt install ros-noetic-camera-info-manager
sudo apt install ros-noetic-xacro ros-noetic-robot-state-publisher ros-noetic-joint-state-publisher
sudo apt install python3-opencv python3-numpy python3-yaml python3-serial python3-pip
```

相机节点优先尝试安装 `uvc_camera`：

```bash
sudo apt install ros-noetic-uvc-camera
```

如果提示找不到 `ros-noetic-uvc-camera`，先不要大改项目结构。可选处理：

1. 尝试安装 `usb_cam`：

   ```bash
   sudo apt install ros-noetic-usb-cam
   ```

2. 如果真实相机只能用 `usb_cam`，再做最小修改：新增或调整一个相机 launch，让它发布同名 `/image_raw`，不要改 YOLO、控制器和 `/cmd_vel` 链路。

常用检查：

```bash
rosversion -d
python3 --version
lsb_release -a
```

如果 `rosversion -d` 输出 `noetic`，后续 source 命令使用 `/opt/ros/noetic/setup.bash`。如果是在主目标虚拟机里复现论文工程，仍使用 `/opt/ros/melodic/setup.bash`。

## 4. YOLO 和 Python 依赖

小车如果没有独立 GPU，优先使用 CPU 推理：

```bash
device:=cpu
```

`torch` 和 `torchvision` 版本不要盲目安装最新版，必须匹配小车系统、Python 版本和 CPU/GPU 情况。先安装基础包：

```bash
python3 -m pip install --upgrade pip
python3 -m pip install numpy opencv-python pillow pyyaml tqdm matplotlib seaborn pandas requests scipy
```

再按小车环境安装 `torch` 和 `torchvision`。安装后检查：

```bash
python3 -c "import cv2; print(cv2.__version__)"
python3 -c "import torch; print(torch.__version__)"
python3 -c "import os, sys; sys.path.insert(0, os.path.expanduser('~/bsnew/yolov5')); from models.experimental import attempt_load; print('yolov5 import ok')"
ls -lh ~/bsnew/models/seam_best.pt
```

如果 `pip` 下载很慢，可以临时使用国内镜像源，但不要把镜像源写死进项目代码。

## 5. 从虚拟机复制项目到小车

推荐使用 `rsync`。在虚拟机终端执行，不是在小车终端执行：

```bash
rsync -av --exclude catkin_ws/build --exclude catkin_ws/devel --exclude catkin_ws/install --exclude .git ~/bsnew/ 用户名@小车IP:~/bsnew/
```

备选方式：

```bash
scp -r ~/bsnew 用户名@小车IP:~/
```

注意不要依赖虚拟机里的 `build/`、`devel/` 或 `install/` 编译产物。到小车后必须重新在小车系统上编译。

## 6. 小车上编译项目

ROS Noetic 小车：

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/noetic/setup.bash
catkin_make
source devel/setup.bash
```

主目标 Ubuntu 18.04 + ROS Melodic 虚拟机：

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
```

不要在 `~/bsnew` 仓库根目录运行 `catkin_make`，必须在 `~/bsnew/catkin_ws` 里运行。

## 7. 分阶段运行验证

每个新终端都先 source：

Noetic 小车：

```bash
source /opt/ros/noetic/setup.bash
source ~/bsnew/catkin_ws/devel/setup.bash
```

Melodic 虚拟机：

```bash
source /opt/ros/melodic/setup.bash
source ~/bsnew/catkin_ws/devel/setup.bash
```

### 阶段 1：假相机，不启用底盘

这一步只验证 YOLO 加载、`/seam_center` 和 `/cmd_vel`，不会驱动小车。

```bash
cd ~/bsnew/catkin_ws
roslaunch robot_vision seam_tracking.launch use_fake_camera:=true run_base_control:=false device:=cpu
```

也可以用视频循环测试：

```bash
cd ~/bsnew/catkin_ws
roslaunch robot_vision seam_tracking.launch use_fake_camera:=true run_base_control:=false device:=cpu video_path:=$HOME/bsnew/原视频.mp4
```

### 阶段 2：真实相机，不启用底盘

```bash
cd ~/bsnew/catkin_ws
roslaunch robot_vision seam_tracking.launch use_fake_camera:=false camera_device:=video0 run_base_control:=false device:=cpu
```

如果相机不是 `/dev/video0`，先检查：

```bash
ls /dev/video*
```

例如相机是 `/dev/video2`，则使用：

```bash
roslaunch robot_vision seam_tracking.launch use_fake_camera:=false camera_device:=video2 run_base_control:=false device:=cpu
```

### 阶段 3：真实相机 + 底盘，先架空轮子

第一次启用底盘时，小车必须架空轮子或离地，旁边要有人准备断电或急停。

```bash
cd ~/bsnew/catkin_ws
roslaunch robot_vision seam_tracking.launch use_fake_camera:=false camera_device:=video0 run_base_control:=true device:=cpu
```

当前 `base_control.launch` 默认串口为：

```text
/dev/move_base
```

如果小车实际是 `/dev/ttyUSB0`，需要确认系统是否已有 `/dev/move_base` 软链接或 udev 规则。也可以先检查：

```bash
ls -l /dev/move_base
ls /dev/ttyUSB*
```

### 阶段 4：落地低速测试并记录数据

在阶段 1 到 3 都正常后，再把小车放到地面进行低速测试。先观察 `/cmd_vel` 数值是否合理，确认检测无效时会输出零速度，再开始记录实验数据。

## 8. 运行前检查命令

查看 ROS 话题：

```bash
rostopic list
rostopic info /seam_center
rostopic info /cmd_vel
```

查看检测中心和速度输出：

```bash
rostopic echo /seam_center
rostopic echo /cmd_vel
```

查看频率：

```bash
rostopic hz /image_raw
rostopic hz /seam_center
```

查看相机和串口：

```bash
ls /dev/video*
ls /dev/ttyUSB*
ls -l /dev/move_base
```

查看串口权限：

```bash
groups
sudo usermod -aG dialout $USER
```

执行 `usermod` 后需要重新登录小车，权限才会生效。

查看结果图。如果是在小车本机有图形界面：

```bash
rqt_image_view /result_image
```

如果是纯 SSH，建议先用 `rostopic echo` 和 `rostopic hz` 判断链路；需要看图时再配置 X11 转发、远程桌面，或在同一 ROS 网络中的虚拟机上查看图像话题。

## 9. 实验曲线应该记录什么

建议记录以下量：

| 数据 | 含义 | 论文中可说明 |
| --- | --- | --- |
| `/seam_center.x` | YOLO 检测框中心横坐标 | 目标在图像横向方向的位置 |
| `/seam_center.y` | 图像宽度 | 用于计算图像中心 |
| `image_center = /seam_center.y / 2` | 图像中心横坐标 | 控制参考位置 |
| `error_pixel = /seam_center.x - image_center` | 像素误差 | 目标中心相对图像中心的偏差 |
| `error_norm = (image_center - /seam_center.x) / image_center` | 控制代码中的归一化误差 | `line_detector.py` 实际用于转向计算的误差方向 |
| `/seam_center.z` | 检测有效标志 | `1.0` 为有效检测，`0.0` 为无有效检测 |
| `/cmd_vel.linear.x` | 前进速度指令 | 上层跟踪控制输出的前向速度 |
| `/cmd_vel.angular.z` | 偏航角速度指令 | 上层跟踪控制输出的转向角速度 |
| `/odom` | 底盘反馈，若存在 | 可作为底盘执行反馈记录，但不能写成主控制已经读取 odom 闭环 |

当前上层控制输出为：

```text
u = [linear.x, 0, angular.z]
```

`linear.y` 应接近 0。论文中不要写成已经启用横向速度 `v_y` 纠偏，也不要写成上层焊缝跟踪控制读取里程计闭环。

## 10. 方式 A：rosbag 记录，推荐

先创建目录：

```bash
mkdir -p ~/bsnew/experiment_logs
```

如果有 `/odom`：

```bash
rosbag record -O ~/bsnew/experiment_logs/seam_test_001.bag /seam_center /cmd_vel /image_raw /result_image /odom
```

如果没有 `/odom`：

```bash
rosbag record -O ~/bsnew/experiment_logs/seam_test_001.bag /seam_center /cmd_vel /image_raw /result_image
```

如果 bag 文件太大，可以不记录图像，只记录曲线相关话题：

```bash
rosbag record -O ~/bsnew/experiment_logs/seam_test_001_small.bag /seam_center /cmd_vel /odom
```

没有 `/odom` 时：

```bash
rosbag record -O ~/bsnew/experiment_logs/seam_test_001_small.bag /seam_center /cmd_vel
```

## 11. 方式 B：CSV 文本记录

CSV 方式简单，适合快速画曲线。打开两个 SSH 终端分别执行：

终端 1：

```bash
mkdir -p ~/bsnew/experiment_logs
rostopic echo -p /seam_center > ~/bsnew/experiment_logs/seam_center.csv
```

终端 2：

```bash
mkdir -p ~/bsnew/experiment_logs
rostopic echo -p /cmd_vel > ~/bsnew/experiment_logs/cmd_vel.csv
```

实验结束后按 `Ctrl+C` 停止记录。

## 12. 绘制实验曲线

本仓库提供实车 CSV 曲线脚本：

```bash
python3 tools/plot_experiment_curves.py --seam ~/bsnew/experiment_logs/seam_center.csv --cmd ~/bsnew/experiment_logs/cmd_vel.csv --out ~/bsnew/experiment_logs/plots
```

输出图片：

```text
seam_center_x_curve.png
seam_error_curve.png
valid_flag_curve.png
cmd_vel_linear_x_curve.png
cmd_vel_angular_z_curve.png
```

如果缺少绘图库：

```bash
python3 -m pip install matplotlib
```

脚本读取 `rostopic echo -p` 的 CSV，也兼容仓库已有 `tools/record_tracking_data.py` 生成的 `field.x`、`field.linear.x` 等列名格式。

## 13. 常见问题与解决方法

### SSH 连不上

检查小车和虚拟机是否在同一网络：

```bash
ping 小车IP
```

检查小车 SSH 服务：

```bash
sudo systemctl status ssh
sudo systemctl start ssh
```

确认用户名、密码和 IP 没写错。

### 虚拟机 ping 不通小车

把虚拟机网络改为桥接模式。确认 Windows、防火墙、校园网或路由器没有隔离设备。小车和虚拟机最好连接同一个 Wi-Fi 或同一个路由器。

### 小车没有网络

临时接屏幕键盘配置 Wi-Fi，或用网线直连路由器。网络恢复后再通过 SSH 操作。

### apt 安装包找不到

先执行：

```bash
sudo apt update
rosversion -d
```

确认 ROS 源和 ROS 版本一致。Noetic 用 `ros-noetic-...`，Melodic 用 `ros-melodic-...`。如果 `uvc_camera` 找不到，先尝试 `ros-noetic-usb-cam`，再做最小相机 launch 适配。

### ROS Noetic 和 Melodic 命令混用

Noetic 小车使用：

```bash
source /opt/ros/noetic/setup.bash
```

Melodic 虚拟机使用：

```bash
source /opt/ros/melodic/setup.bash
```

不要在同一个终端里混 source 两个 ROS 版本。

### catkin_make 找不到包

确认位置：

```bash
cd ~/bsnew/catkin_ws
ls src
catkin_make
```

不要在 `~/bsnew` 根目录编译。确认项目复制时没有漏掉 `catkin_ws/src/robot_vision`、`catkin_ws/src/base_control`。

### 没有 source setup.bash

如果 `roslaunch` 找不到包，重新执行：

```bash
source /opt/ros/noetic/setup.bash
source ~/bsnew/catkin_ws/devel/setup.bash
```

Melodic 环境把 `noetic` 换成 `melodic`。

### cv_bridge import error

安装：

```bash
sudo apt install ros-noetic-cv-bridge
```

然后重新打开终端并 source。Melodic 环境使用 `ros-melodic-cv-bridge`。

### torch import error

说明 `torch` 没装好或版本不匹配。先检查：

```bash
python3 --version
python3 -c "import torch; print(torch.__version__)"
```

按小车系统和 CPU/GPU 情况重新安装合适的 `torch`、`torchvision`。

### yolov5 import error

检查路径：

```bash
ls ~/bsnew/yolov5
python3 -c "import os, sys; sys.path.insert(0, os.path.expanduser('~/bsnew/yolov5')); from models.experimental import attempt_load; print('ok')"
```

如果失败，说明项目没有完整复制，或 YOLOv5 依赖缺失。

### 权重文件 seam_best.pt 找不到

检查：

```bash
ls -lh ~/bsnew/models/seam_best.pt
```

如果使用其他权重，通过 launch 参数覆盖：

```bash
roslaunch robot_vision seam_tracking.launch model_path:=$HOME/bsnew/models/你的权重.pt
```

不要随意改 launch 默认权重路径。

### 相机 /dev/video0 不存在

检查：

```bash
ls /dev/video*
```

把 `camera_device:=video0` 改成实际设备号，例如：

```bash
camera_device:=video2
```

### /image_raw 没有发布

检查相机节点是否启动：

```bash
rostopic list
rostopic hz /image_raw
```

先用假相机确认后端链路：

```bash
roslaunch robot_vision seam_tracking.launch use_fake_camera:=true run_base_control:=false device:=cpu
```

### /seam_center 一直 z=0

说明 YOLO 没检测到有效目标。检查：

```bash
rostopic echo /seam_center
rostopic hz /image_raw
ls -lh ~/bsnew/models/seam_best.pt
```

可临时降低置信度阈值观察：

```bash
roslaunch robot_vision seam_tracking.launch use_fake_camera:=false camera_device:=video0 run_base_control:=false device:=cpu conf_thres:=0.1 class_id:=-1
```

同时检查相机画面中焊缝是否清楚、光照是否过暗、权重是否适合当前场景。

### /cmd_vel 没输出

检查控制节点是否订阅 `/seam_center`：

```bash
rostopic info /seam_center
rostopic echo /cmd_vel
```

如果 `/seam_center.z` 一直是 0，控制器会安全停车，所以 `/cmd_vel` 可能为零。

### 底盘串口 /dev/ttyUSB0 权限不足

加入串口组：

```bash
sudo usermod -aG dialout $USER
```

重新登录后检查：

```bash
groups
```

当前底盘 launch 默认使用 `/dev/move_base`。如果小车没有这个设备，检查 udev 规则或软链接。

### 小车启动后不动

按顺序检查：

```bash
rostopic echo /cmd_vel
rostopic info /cmd_vel
ls -l /dev/move_base
ls /dev/ttyUSB*
```

如果 `/cmd_vel` 有数值但车不动，重点检查底盘串口、权限、底盘电源、急停开关和 base_control 日志。

### 小车运动方向反了

先不要大改控制器。确认相机安装方向、图像是否镜像、底盘坐标方向是否和协议一致。必要时只做最小参数或话题适配，并记录修改原因。

### 小车运动太快或不安全

先架空轮子测试。落地前可通过 launch 参数降低速度：

```bash
roslaunch robot_vision seam_tracking.launch use_fake_camera:=false camera_device:=video0 run_base_control:=true device:=cpu v0:=0.1 vmin:=0.05
```

### 远程运行时看不到图像界面

纯 SSH 不一定能打开 GUI。可先用：

```bash
rostopic echo /seam_center
rostopic hz /result_image
```

需要图像时，使用小车本机屏幕、远程桌面、X11 转发，或让同一 ROS 网络中的虚拟机订阅 `/result_image`。

### rosbag 文件太大

少记录图像话题，只记录曲线：

```bash
rosbag record -O ~/bsnew/experiment_logs/seam_test_001_small.bag /seam_center /cmd_vel
```

如果需要图像，只记录短时间片段。

### 记录曲线时间戳对不齐

`rostopic echo -p` 的两个 CSV 是两个终端分别启动，起始时间可能不同。画图脚本会把时间轴平移到共同起点附近；做精确分析时推荐使用 `rosbag`，或使用仓库已有 `tools/record_tracking_data.py` 同时记录 `/seam_center` 和 `/cmd_vel`。

## 14. 安全测试要求

1. 第一次启用 `run_base_control:=true` 时，小车必须架空轮子或离地。
2. 旁边要有人准备断电或急停。
3. 先用 `rostopic echo /cmd_vel` 验证速度指令合理，再落地。
4. `/seam_center.z=0` 或中心点超时时，控制器应输出零速度。
5. 不要在狭小空间直接全速测试。
6. 不要把测试线缆拖在轮子附近。
7. 实验记录前先做 10 到 20 秒短测试，确认不会异常运动。

## 15. 论文中可使用的曲线说明

可将实车实验曲线解释为：

- `seam_center_x_curve.png`：焊缝检测框中心横坐标随时间变化，反映视觉目标位置输出。
- `seam_error_curve.png`：目标中心相对图像中心的像素误差和控制归一化误差，反映跟踪偏差变化。
- `valid_flag_curve.png`：检测有效标志，反映 YOLO 检测连续性。
- `cmd_vel_linear_x_curve.png`：前进速度指令，反映控制器在直行和转向阶段的速度调节。
- `cmd_vel_angular_z_curve.png`：偏航角速度指令，反映控制器对横向偏差的转向修正。

注意：这些曲线能证明上层感知到控制指令链路是否连续有效。若记录了 `/odom`，可以作为底盘执行反馈材料，但当前主控制代码没有消费 `/odom`，论文中不能写成里程计闭环控制。
