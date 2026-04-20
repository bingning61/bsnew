# 毕业论文主上下文文档

## 1. 项目名称与一句话定义
本项目可以定义为：**一个基于 YOLO 焊缝目标检测与原 ROS1 偏差控制链路融合实现的焊缝跟踪机器人小车系统**。从当前仓库代码可见，它不是从零重新设计控制系统，而是在保留原有 ROS1 视觉跟线/运动控制后端的基础上，用 YOLO 检测结果替代原先 HSV 线中心提取输入，最终形成“图像输入 -> YOLO 检测 -> 中心偏差控制 -> `cmd_vel` -> 底盘运动”的完整链路。

## 2. 课题目标与要解决的问题
从根目录 `README.md`、`robot_vision` 包中的新旧脚本以及 `git` 提交历史可以确认，本课题要解决的核心问题是：如何在不大改原有稳定控制代码的前提下，把 YOLO 检测得到的焊缝目标位置接入原有 ROS1 小车控制链路，使小车能够依据焊缝在图像中的位置偏差进行转向和前进控制。

代码确认事实表明，本项目追求的是**最小改动集成**，而不是重新实现一套全新控制器。`README.md` 明确写出“YOLO 前端 + 原 ROS1 控制后端”的定位；`line_detector.py` 仍保留原有 `twist_calculate()` 控制律；`seam_tracking.launch` 则把 YOLO 检测节点和原控制节点串接起来。这说明本项目的任务重点是系统集成与工程落地，而不是单独研究某种全新控制算法。

## 3. 原有两个系统分别是什么

### 3.1 原有 ROS1 视觉控制系统
代码确认事实：`catkin_ws/src/robot_vision/scripts/line_detector.py` 是原有视觉跟线控制核心脚本；`catkin_ws/src/robot_vision/launch/line_follow.launch` 是原有启动入口；`catkin_ws/src/robot_vision/config/line_hsv.cfg` 和 `robot_vision/CMakeLists.txt` 中的 dynamic reconfigure 配置表明，这条旧链路主要基于 HSV 阈值分割提取图像中的线中心，然后由 `twist_calculate()` 生成 `cmd_vel` 控制指令。

从源码逻辑看，旧系统的处理过程是：订阅 `/image_raw`，把图像从 ROS 消息转成 OpenCV 图像，进行 HSV 颜色空间阈值分割，沿图像中部若干扫描行搜索非零像素点，取平均值得到中心位置 `center_point`，随后调用 `twist_calculate()` 生成 `Twist` 消息并发布到 `cmd_vel`。这套逻辑已经具备“图像中心偏差 -> 角速度/线速度”的闭环控制形态，因此非常适合作为焊缝跟踪系统中的后端控制器继续复用。

### 3.2 原有 YOLO 检测系统
代码确认事实：仓库根目录 `yolo/` 下存在一整套本地 Ultralytics 代码树，`yolo/pyproject.toml` 明确显示这是 `ultralytics` 项目源码；`yolo/README.md` 也是标准 Ultralytics YOLO 说明文档。`yolo/Detect.py`、`yolo/train.py`、`yolo/val.py` 说明该目录下还放有若干通用训练/推理模板脚本。

但必须强调一个真实性边界：当前仓库中真正与 ROS 融合运行直接相关的 YOLO 调用方式，不是 `yolo/Detect.py` 这种模板脚本，而是 `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`。该脚本直接 `from ultralytics import YOLO`，加载外部传入的 `model_path` 权重，并在 ROS 图像回调中执行 `self.model.predict()`。因此，在论文中写“项目运行时如何调用 YOLO”时，应优先引用 `yolo_seam_detector.py`，而不能把 `yolo/Detect.py` 之类占位模板误写成当前系统真实运行入口。

## 4. 最终融合后的系统是什么
根据当前仓库状态，最终系统是一个以 `robot_vision/launch/seam_tracking.launch` 为主入口的 ROS1 焊缝跟踪系统。它支持两种输入场景：一种是实际相机输入，由 `robot_camera.launch` 启动 `uvc_camera` 节点发布 `/image_raw`；另一种是调试场景，由 `fake_camera.py` 按固定频率循环发布静态测试图像。无论使用哪一种图像来源，后续数据流都会进入新增的 `yolo_seam_detector.py`，由该节点输出焊缝检测框中心，再交给经过最小适配的原控制器 `line_detector.py` 计算 `cmd_vel`，最后可选地交给 `base_control.py` 发送到底盘。

从结构上说，这已经不是“两个彼此独立的代码仓”的拼接，而是一个有统一 launch 入口、统一数据流和统一运行说明的完整 ROS1/catkin 工程。根目录 `README.md` 和 `git` 历史中的提交 `208353c Add seam tracking integration` 进一步说明，这个融合状态不是推测，而是当前仓库已经落地的真实结果。

## 5. 当前系统整体架构
当前系统的主架构可以概括为：

```text
相机或假图像
-> /image_raw
-> yolo_seam_detector.py
-> /seam_center (geometry_msgs/Point)
-> line_detector.py（external center 模式）
-> cmd_vel (geometry_msgs/Twist)
-> base_control.py
-> 串口 /dev/move_base
-> 机器人底盘
```

同时，系统还保留一条旧的 HSV 视觉链路：

```text
/image_raw
-> line_detector.py（HSV 模式）
-> cmd_vel
```

因此，当前项目不是“把旧系统删掉后换成 YOLO”，而是“保留旧控制器与旧调试入口，同时增加一个新的 YOLO 感知前端，并让旧控制器支持外部中心输入模式”。这种结构对本科毕设尤其合适，因为它保留了原稳定代码，集成风险低，系统解释也清楚。

## 6. ROS1/catkin 工程结构说明
代码确认事实：仓库根目录为 `bsnew/`，ROS1 工作区根目录为 `bsnew/catkin_ws/`，主要源码包位于 `bsnew/catkin_ws/src/`。当前工作区中可见的 package 包括：

| package 名 | 路径 | 与焊缝跟踪主链路的关系 |
| --- | --- | --- |
| `robot_vision` | `catkin_ws/src/robot_vision` | 直接相关，包含视觉输入、旧控制器、新 YOLO 节点和主 launch |
| `base_control` | `catkin_ws/src/base_control` | 直接相关，负责 `cmd_vel` 到底盘串口协议的桥接 |
| `robot_navigation` | `catkin_ws/src/robot_navigation` | 辅助相关，偏向激光雷达、SLAM、导航，不是 `seam_tracking.launch` 的主链路 |
| `robot_simulation` | `catkin_ws/src/robot_simulation` | 辅助相关，用于 Stage 仿真，不是当前焊缝跟踪主入口 |
| `bingda_tutorials` | `catkin_ws/src/bingda_tutorials` | 教程/示例性质，与焊缝跟踪主链路无直接关系 |
| `nanoomni_description` | `catkin_ws/src/bingda_tutorials/nanoomni_description` | 机器人模型描述包，非焊缝跟踪主链路 |
| `rplidar_ros` | `catkin_ws/src/lidar/rplidar_ros` | 激光雷达驱动，辅助功能 |
| `nvilidar_ros` | `catkin_ws/src/lidar/nvilidar_ros` | 激光雷达驱动，辅助功能 |
| `sc_mini` | `catkin_ws/src/lidar/sc_mini` | 激光雷达驱动，辅助功能 |

其中，真正构成焊缝跟踪闭环的只有 `robot_vision` 与 `base_control`。其余 package 说明这个工作区原本就是一个更大的移动机器人教学/应用工程，而焊缝跟踪系统是在此基础上完成的一个融合式课题子系统。

## 7. 关键 package、节点、launch、config、脚本入口说明

### 7.1 `robot_vision` 包
`robot_vision/package.xml` 显示其运行依赖包含 `rospy`、`sensor_msgs`、`geometry_msgs`、`dynamic_reconfigure`、`cv_bridge`、`opencv_apps`、`uvc_camera`。`robot_vision/CMakeLists.txt` 仅显式生成了 `config/line_hsv.cfg` 的 dynamic reconfigure 配置，没有自定义消息，也没有 C++ 可执行程序，说明其核心功能基本由 Python 脚本承担。

当前与论文最相关的 launch 和脚本如下：

| 文件 | 作用 |
| --- | --- |
| `launch/seam_tracking.launch` | 当前融合后的主入口 |
| `launch/line_follow.launch` | 原 HSV 视觉控制入口 |
| `launch/robot_camera.launch` | 实际相机输入入口 |
| `scripts/yolo_seam_detector.py` | 新增 YOLO 焊缝检测节点 |
| `scripts/line_detector.py` | 原控制脚本，现支持 external center 模式 |
| `scripts/fake_camera.py` | 静态图像调试输入节点 |
| `config/line_hsv.cfg` | 旧 HSV 链路的动态调参文件 |
| `config/astrapro.yaml` / `config/csi72.yaml` | 相机标定/信息文件 |

### 7.2 `base_control` 包
`base_control/package.xml` 表明它依赖 `rospy`、`tf`、`geometry_msgs`、`nav_msgs`、`sensor_msgs`、`ackermann_msgs` 等消息类型。核心脚本 `script/base_control.py` 负责订阅 `cmd_vel` 或 Ackermann 指令、生成串口协议数据帧、向底盘发送运动命令，同时周期性查询并发布里程计、电池和可选 IMU/超声波数据。

从 `launch/base_control.launch` 可见，该节点默认通过 `/dev/move_base` 与底盘连接，默认订阅主题名为 `cmd_vel`。因此，焊缝跟踪系统把 `cmd_vel` 接到 `base_control` 上之后，就完成了视觉控制到真实底盘执行层的连接。

### 7.3 其他 package 的定位
`robot_navigation`、`robot_simulation`、`lidar/*`、`bingda_tutorials`、`nanoomni_description` 等 package 在当前工作区中主要承担导航、雷达、仿真、教程和模型描述等角色。代码确认事实是：`seam_tracking.launch` 并没有直接 include 这些 package 的导航/仿真 launch，因此它们不应在论文中被误写为焊缝跟踪主链路的必需模块。

## 8. 图像输入 -> YOLO 检测 -> 检测框中心提取 -> 偏差计算 -> `cmd_vel` -> 底盘运动 的完整链路
当前仓库的完整链路已经可以直接从 launch 和脚本中读出来。首先，图像输入来源有两种：若 `use_fake_camera:=false`，`seam_tracking.launch` 会 include `robot_camera.launch`，启动 `uvc_camera` 节点向 `/image_raw` 发布实时图像；若 `use_fake_camera:=true`，则启动 `fake_camera.py`，从 `robot_vision/data/bingda.png` 读取一张静态图并以约 30Hz 重复发布到 `/image_raw`。

随后，`yolo_seam_detector.py` 订阅 `/image_raw`，将 ROS 图像转换为 OpenCV 格式，并调用 `self.model.predict()` 执行 YOLO 推理。它会从所有检测框中选择一个“最佳检测框”：若指定了 `target_class_id`，则只在该类别中选置信度最高者；若未指定，默认选全体检测中置信度最高者。得到最佳框后，脚本按照 `center_x = (x1 + x2) / 2` 计算检测框中心横坐标，并把 `geometry_msgs/Point` 的 `x` 字段写成中心横坐标、`y` 字段写成图像宽度、`z` 字段写成有效标志位，然后发布到 `/seam_center`。如果没有检测到框，则发布 `x=-1.0`、`y=image_width`、`z=0.0` 作为“无有效检测”的信号。

接着，原控制脚本 `line_detector.py` 在 `seam_tracking.launch` 中以 `use_external_center:=true` 方式启动。此时它不再订阅 `/image_raw` 做 HSV 处理，而是订阅 `/seam_center`。当收到有效中心点时，控制器会把 `image_width / 2` 当作图像中心基准，把检测框中心 `center_x` 当作目标位置输入，并复用原来的 `twist_calculate()` 计算 `cmd_vel`。当收到无效检测或在给定超时时间内没有新的中心消息时，脚本立即发布零速度 `Twist`，实现安全停机。

如果 `run_base_control:=true`，`seam_tracking.launch` 还会 include `base_control.launch`。这样 `base_control.py` 就会订阅 `cmd_vel`，把线速度和角速度封装为底盘串口协议帧，通过 `/dev/move_base` 发送给底盘控制板，同时发布 `odom`、`battery` 等状态信息。至此，整个“视觉检测—偏差控制—运动执行”链路闭合。

## 9. 焊缝跟踪控制的核心原理
从当前代码看，本项目的控制思想不是复杂轨迹规划，而是典型的**图像中心偏差控制**。YOLO 的任务是把焊缝目标从图像中定位出来，并给出其检测框中心；控制器的任务是根据“焊缝中心相对于图像中心的偏差”调整小车转向和前进速度。

在数学表达上，YOLO 前端首先给出检测框坐标 `(x1, y1, x2, y2)`，然后计算：

```text
bbox_center_x = (x1 + x2) / 2
image_center_x = image_width / 2
```

从“偏差概念”看，可以把横向偏差理解为：

```text
error = bbox_center_x - image_center_x
```

但需要注意，原控制器的实际实现并没有显式写出上面这条 `error` 变量，而是沿用了旧代码中的归一化写法。`line_detector.py` 在调用 `twist_calculate()` 时，把 `width` 参数传入为 `image_width / 2`，随后在控制函数内部使用：

```text
ratio = center_x / (image_width / 2)
angular_z = ((image_width / 2 - center_x) / (image_width / 2)) / 2
```

如果 `ratio` 落在 `[0.95, 1.05]` 范围内，则认为目标接近图像中心，直接以 `0.2 m/s` 前进；否则根据归一化偏差计算角速度，并按角速度大小调整线速度。当角速度绝对值较小的时候，线速度设置为 `0.2 - angular_z / 2`；当偏差较大时，线速度降为 `0.1 m/s`。因此，本项目本质上是一个“基于视觉偏差的前视控制”系统，控制算法本身较简单，但工程实现清晰，适合本科毕业设计。

## 10. YOLO 检测在本项目中的作用
YOLO 在当前项目中的作用是**替代原 HSV 分割得到的线中心提取前端**。旧系统依赖颜色阈值与形态学处理来寻找线中心；新系统改为用深度学习目标检测器在图像中定位焊缝或目标区域，再用检测框中心作为控制输入。也就是说，YOLO 在这里承担的是“感知前端”和“目标中心定位器”的角色，而不是直接控制机器人。

代码确认事实表明，当前 ROS 集成层并没有使用 YOLO 的跟踪、多目标关联、分割掩膜等高级功能，只使用了检测框及其中心位置。因此，如果论文要描述 YOLO 的工程作用，应该写成“提供焊缝目标的稳定检测和中心位置”，而不应写成“系统进行了完整实例分割或多目标轨迹跟踪”，因为仓库里没有对应证据。

## 11. 原控制代码中保留了哪些内容
从 `git` 历史与当前源码对照可以确认，原控制系统被保留的主要内容包括：

1. `line_detector.py` 中原有的 `twist_calculate()` 控制律没有被重写。
2. 原有 HSV 视觉链路仍然存在，可通过 `line_follow.launch` 继续运行。
3. `cmd_vel` 作为运动控制输出主题没有被替换。
4. `base_control.py` 作为底盘接口和串口协议桥接节点没有被重构。
5. 原底盘协议、里程计、电池、IMU 等处理逻辑继续由 `base_control.py` 负责。

因此，更准确的说法不是“原控制代码完全原封不动”，而是“原控制核心与底盘执行链路被保留，输入源接线做了最小必要改动”。

## 12. 新增/修改了哪些关键部分
这一部分不仅能从当前结构推断，还能从 `git` 历史直接确认。`git log` 显示，提交 `208353c` 的说明为 `Add seam tracking integration`，其变更包括：

1. 新增根目录 `README.md`，说明当前融合系统的目标、话题、命令和架构。
2. 新增 `catkin_ws/src/robot_vision/launch/seam_tracking.launch`，作为融合后的主启动入口。
3. 新增 `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`，作为新的 YOLO 前端 ROS 节点。
4. 修改 `catkin_ws/src/robot_vision/scripts/line_detector.py`，给原控制器增加 `use_external_center`、`external_center_topic`、`external_center_timeout`、`external_center_watchdog` 等逻辑，使其能够从外部话题接收中心位置并在无检测时停机。
5. 修改 `catkin_ws/src/robot_vision/package.xml`，增加 `geometry_msgs` 等依赖，以支持 `Point` 消息传输。

这说明当前仓库采用的融合方案更接近“最小修改原控制器输入方式”的策略，而不是新增一个独立的中间适配节点。若论文要描述集成方式，最好如实写成“在原控制器中增加外部中心输入模式”，而不是写成“新建了一个独立适配层节点”，因为后者与当前真实代码不符。

## 13. 项目运行环境与部署方式
代码确认事实与项目说明共同指出：最终目标环境是 Ubuntu 18.04 虚拟机上的 ROS1/catkin 工程。根目录 `README.md` 给出了通用构建模板：

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/<ros1_distro>/setup.bash
catkin_make
source devel/setup.bash
```

同时，`README.md` 又给出了 Ubuntu 18.04 常见的 `melodic` 示例：

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
```

但这里必须区分“代码确认事实”和“待人工确认”。代码确认事实是：README 确实使用了 `melodic` 示例。待人工确认的是：当前仓库的 launch/package 并没有硬编码 ROS 发行版名称，所以最终部署是否一定是 `melodic`，仍应由你的 Ubuntu 18.04 虚拟机环境最终确认。

对于运行命令，当前仓库中有两条最重要的主路径。第一条是调试路径，不带底盘，仅使用假图像输入：

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash
roslaunch robot_vision seam_tracking.launch \
  run_base_control:=false \
  use_fake_camera:=true \
  fake_image_path:=$(rospack find robot_vision)/data/bingda.png \
  model_path:=<你的YOLO权重文件路径>
```

第二条是真实相机与底盘的完整链路：

```bash
export BASE_TYPE=<实际底盘类型>
export CAMERA_TYPE=<astrapro或csi72等实际相机配置名>

cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash
roslaunch robot_vision seam_tracking.launch \
  run_base_control:=true \
  model_path:=<你的YOLO权重文件路径>
```

这里还需要补充一个很重要的事实边界：`README.md` 示例使用的是 `model_path:=../yolo/runs/train/exp17/weights/best.pt`，但当前仓库没有这个权重文件。因此，真正可运行时必须由你提供一个实际存在的 `.pt` 模型文件。

## 14. 当前项目已经完成了什么
从当前源码状态看，以下内容已经完成：

1. 已经有统一的融合启动入口 `seam_tracking.launch`。
2. 已经有可工作的 YOLO ROS 节点 `yolo_seam_detector.py`。
3. 已经对原控制器做了最小修改，使其能够接收外部中心输入而不是只依赖 HSV。
4. 已经保留旧版 HSV 跟线入口，便于对照和回退。
5. 已经提供了调试模式，可用 `fake_camera.py` 发布静态图像进行链路验证。
6. 已经保留并复用了 `base_control.py` 作为 `cmd_vel` 到底盘的桥接层。
7. 已经更新了根目录 `README.md`，给出了系统定位、主要话题和示例命令。

如果从“毕业设计已完成到什么程度”来表述，可以较稳妥地写成：**系统的源码级集成已经完成，主链路已经形成，具备继续开展实验与论文撰写的基础。**

## 15. 当前项目还缺什么、哪些需要人工实机验证
当前仓库中最明显的缺口不是系统结构，而是部署与实验材料。首先，YOLO 权重文件并未随仓库一同提供，所以当前无法仅靠仓库完成无条件复现。其次，仓库中没有提供实机实验数据、检测准确率、跟踪误差、速度统计、终端截图、`rostopic echo` 截图、`rviz` 截图等论文常用证据材料。再次，实际底盘型号、相机型号、`BASE_TYPE` 实际取值、`CAMERA_TYPE` 实际取值、串口映射方式、控制效果参数整定结果，也都没有在仓库中明确交代。

此外，当前项目还存在一个部署层面的待确认点：`yolo_seam_detector.py` 使用 `python3` 解释器，而 `line_detector.py`、`fake_camera.py`、`base_control.py` 等旧脚本仍是 Python2 风格写法。在 Ubuntu 18.04 + ROS1（尤其是 ROS Melodic）环境下，这意味着需要人工确认 Python3 版 `rospy`、`cv_bridge`、`ultralytics`、`torch` 是否都已经正确配置，否则实际部署时可能遇到混合 Python 运行环境问题。这个风险不是猜测，而是从脚本 shebang 和语法风格直接能看出来的源码事实。

## 16. 项目的优点、局限性与可改进方向
从本科毕业设计的角度看，当前方案的主要优点是工程结构清晰、改动量小、复用率高、容易解释。原控制器、`cmd_vel` 链路和底盘接口都被保留下来，使系统集成风险显著降低；YOLO 只负责把焊缝目标转换为中心点输入，前后端职责划分明确；还保留了旧的 HSV 路径，便于做方法对比或系统演进说明。这种“前端替换、后端复用”的模式非常适合本科毕设，因为它既体现了系统集成能力，又不会把项目复杂度推到难以完成的程度。

局限性同样很明显。当前实现只使用检测框中心，没有融合轨迹平滑、时序滤波、多帧跟踪或深度信息；仓库缺少权重文件和实验数据，导致论文中的性能指标部分无法直接由源码支撑；系统对实际相机与底盘部署环境有一定依赖，尤其是混合 Python 版本带来的运行环境配置问题，需要在 Ubuntu 18.04 实机上进一步确认。

如果写“可改进方向”，比较贴合当前项目实际的表述应该是：后续可以在不破坏现有架构的基础上，引入检测结果滤波、目标连续性判断、速度自适应调节、更多安全停机策略，以及更完整的实验量化评价体系；而不建议在论文里把“改进方向”写成完全更换为 ROS2、重构为复杂状态机或引入大规模工业级控制架构，因为这与当前项目目标不一致，也超出当前仓库证据范围。

## 17. 可以直接用于论文写作的材料摘要
如果你准备直接写论文，当前仓库最适合支撑以下几个部分：

1. **系统实现**：可以直接依据 `seam_tracking.launch`、`yolo_seam_detector.py`、`line_detector.py`、`base_control.py` 描述节点实现与接口关系。
2. **方法设计**：可以直接依据“检测框中心提取 + 图像中心偏差控制”写方法原理，并引用 `twist_calculate()` 的实际控制规则。
3. **系统集成**：可以直接依据 `git` 历史和主 launch 文件说明“新增了 YOLO 前端、保留了原控制后端、采用最小修改完成融合”。
4. **部署说明**：可以直接依据根目录 `README.md` 写 ROS1/catkin 的构建与运行流程，但要注明权重文件需要人工提供。
5. **实验说明的前半部分**：可以写实验平台、软件架构、运行步骤、待采集指标和待补实验内容，但不能凭空写出准确率、速度、误差等结果。

## 18. 对论文最关键问题的直接回答

### 18.1 这个项目最终是什么系统
当前仓库最终呈现的是一个“基于 YOLO 焊缝检测和原 ROS1 偏差控制链路的焊缝跟踪机器人小车系统”。

### 18.2 原来的两个系统分别是什么
原系统一是基于 `line_detector.py` 的 ROS1 HSV 视觉跟线/偏差控制系统；原系统二是以 `yolo/` 本地 Ultralytics 代码树为基础、在 `yolo_seam_detector.py` 中被 ROS 化调用的 YOLO 检测系统。

### 18.3 最终是怎么融合的
最终融合方式是：新增 `yolo_seam_detector.py` 和 `seam_tracking.launch`，并对原 `line_detector.py` 增加 external center 输入模式，使 YOLO 输出的中心位置能够直接进入原控制器。

### 18.4 融合后完整的数据流是什么
图像输入发布到 `/image_raw`，YOLO 节点检测目标并发布 `/seam_center`，原控制器订阅该中心消息后生成 `cmd_vel`，若启用底盘桥接则由 `base_control.py` 通过串口发送到机器人底盘。

### 18.5 YOLO 在这里承担什么功能
YOLO 承担的是焊缝目标检测与目标中心提取功能，它只提供控制所需的目标横向位置，不直接负责运动控制。

### 18.6 原控制系统保留了什么
保留了原有 `twist_calculate()` 控制律、`cmd_vel` 输出路径、`base_control.py` 底盘接口逻辑，以及旧的 HSV 入口 `line_follow.launch`。

### 18.7 为什么这种融合方案适合本科毕业设计
因为它改动小、风险低、结构清楚、便于调试和论文表述，能够在有限时间内完成一个可运行、可解释的集成系统。

### 18.8 当前方案的原理和方法是什么
核心方法是“检测框中心替代线中心”的视觉偏差控制：先由 YOLO 计算检测框中心，再将该中心与图像中心比较，最后由原控制器把偏差转成角速度和线速度。

### 18.9 这个系统完成了哪些内容
源码级融合已经完成，主 launch 入口已经建立，YOLO ROS 节点已经实现，原控制器已经支持外部中心输入，调试模式和完整运行说明也已经加入仓库。

### 18.10 这个系统的局限性是什么
权重文件未提供，实验数据和截图缺失，实际硬件参数未知，Ubuntu 18.04 + ROS1 的最终部署结果尚需人工验证，并且当前实现只使用检测框中心这一较简单的控制输入。

### 18.11 回到 Ubuntu 18.04 后如何 `catkin_make` 和 `roslaunch`
可以按下面模板执行：

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
roslaunch robot_vision seam_tracking.launch \
  run_base_control:=false \
  use_fake_camera:=true \
  fake_image_path:=$(rospack find robot_vision)/data/bingda.png \
  model_path:=<你的YOLO权重文件路径>
```

若要实机运行，再补充：

```bash
export BASE_TYPE=<实际底盘类型>
export CAMERA_TYPE=<实际相机配置名>
roslaunch robot_vision seam_tracking.launch \
  run_base_control:=true \
  model_path:=<你的YOLO权重文件路径>
```

### 18.12 新 GPT 如果只看这套文档，是否足够理解整个项目并继续帮你写论文
可以，前提是它严格依赖本资料包，不擅自虚构实验结果。对于“系统实现”“方法设计”“系统集成”“部署说明”这些章节，这套资料已经足够；对于“实验结果分析”“性能指标”“硬件参数表”等内容，仍需你后续人工补充。

## 19. 本次资料整理的验证边界说明
为了保持真实性，本次整理只做到以下级别：

1. 已完成目录、README、launch、config、脚本、package.xml、CMakeLists.txt、`git` 历史的核对。
2. 已确认当前机器上存在 `/opt/ros/jazzy`，未确认到 ROS1 运行环境，因此没有在本机会话中做 Ubuntu 18.04 + ROS1 的实机复现。
3. 已确认 README 示例权重路径在当前仓库中不存在，因此把模型权重文件列为待人工补充项。
4. 没有对两个 mp4 文件内容进行实验意义上的解读。
