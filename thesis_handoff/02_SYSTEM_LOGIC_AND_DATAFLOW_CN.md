# 系统逻辑与数据流说明

## 一、说明范围

本文件只依据当前仓库中的实际目录、`launch`、脚本、`package.xml`、`CMakeLists.txt` 和相关提交历史，说明系统的真实运行逻辑。对于仓库没有直接证据支撑的内容，本文件不会将其写成既成事实。

## 二、系统分层逻辑

从当前主运行入口 `catkin_ws/src/robot_vision/launch/seam_tracking.launch` 可以把系统分为四层：

1. 图像输入层：由真实相机或假相机提供 `image_raw`。
2. 视觉表征层：由 `yolo_seam_detector.py` 把目标检测结果压缩成控制可用的位置量。
3. 偏差控制层：由 `line_detector.py` 根据中心偏差生成 `cmd_vel`。
4. 执行接口层：由 `base_control.py` 把 `cmd_vel` 转换为底盘串口协议并驱动底盘。

在此基础上，还存在两类支撑层：

- 模型/仿真支撑层：`nanoomni_description`、`robot_simulation`
- 导航/雷达支撑层：`robot_navigation`、`lidar/*`

但这两类支撑层不属于当前 `seam_tracking.launch` 的主闭环链路。

## 三、当前主入口的真实结构

### 1. 主入口文件

当前仓库中与焊缝跟踪直接对应的主入口是：

- `catkin_ws/src/robot_vision/launch/seam_tracking.launch`

该文件是在 git 提交 `208353c Add seam tracking integration` 中新增的，说明它是当前项目中专门为焊缝跟踪主链路建立的统一启动入口。

### 2. 主入口的调度关系

`seam_tracking.launch` 的调度逻辑如下：

```text
if run_base_control == true:
    include base_control.launch

if use_fake_camera == true:
    start fake_camera.py
else:
    include robot_camera.launch

always:
    start yolo_seam_detector.py
    start line_detector.py in external-center mode
```

由此可以看出，当前系统从设计上同时支持两种使用方式：

- 不接底盘的纯感知/控制调试方式
- 接底盘的完整运动控制方式

## 四、节点与脚本关系

### 1. 主链路节点表

| 节点/脚本 | 所在位置 | 主要输入 | 主要输出 | 在系统中的作用 |
| --- | --- | --- | --- | --- |
| `uvc_camera_node` | `robot_camera.launch` 中调用外部 `uvc_camera` 包 | 物理相机设备 | `/image_raw`、`camera_info` | 真实图像采集 |
| `fake_camera.py` | `robot_vision/scripts/fake_camera.py` | 本地静态图片路径 | `/image_raw` | 无硬件时的图像源 |
| `yolo_seam_detector.py` | `robot_vision/scripts/yolo_seam_detector.py` | `/image_raw` | `/seam_center`、`/result_image` | 焊缝目标检测与位置表征 |
| `line_detector.py` | `robot_vision/scripts/line_detector.py` | `/seam_center` 或 `/image_raw` | `cmd_vel`、遗留调试图像话题 | 偏差控制与速度输出 |
| `base_control.py` | `base_control/script/base_control.py` | `cmd_vel` | 串口控制数据、`odom`、`battery`、可选 `imu`/`sonar` | 底盘通信接口 |

### 2. 主链路以外但需说明的模块

| 模块 | 所在位置 | 作用 | 是否属于当前主链路 |
| --- | --- | --- | --- |
| `line_follow.launch` | `robot_vision/launch/line_follow.launch` | 旧版 HSV 线跟踪启动入口 | 否，属于遗留入口 |
| `robot_camera.launch` | `robot_vision/launch/robot_camera.launch` | 真实相机启动与相机 TF | 是，作为图像源被主链路间接调用 |
| `base_startup.launch` | `base_control/launch/base_startup.launch` | 通用底盘启动，含雷达和相机 | 否，不是焊缝主入口 |
| `nanoomni_description` | `catkin_ws/src/nanoomni_description` | URDF/Gazebo/可视化支撑 | 否，属于支撑模块 |
| `robot_simulation` | `catkin_ws/src/robot_simulation` | Stage 地图与二维仿真 | 否，属于支撑模块 |

## 五、关键话题关系

### 1. 当前焊缝跟踪主链路中的核心话题

| 话题名 | 消息类型 | 生产者 | 消费者 | 作用 |
| --- | --- | --- | --- | --- |
| `/image_raw` | `sensor_msgs/Image` | `uvc_camera_node` 或 `fake_camera.py` | `yolo_seam_detector.py`，遗留 HSV 控制器 | 提供图像输入 |
| `/seam_center` | `geometry_msgs/Point` | `yolo_seam_detector.py` | `line_detector.py` | 传递目标中心位置表征 |
| `cmd_vel` | `geometry_msgs/Twist` | `line_detector.py` | `base_control.py` 或仿真插件 | 传递速度控制量 |
| `/result_image` | `sensor_msgs/Image` | `yolo_seam_detector.py` | 调试界面/图像工具 | 输出识别结果可视化 |
| `/mask_image` | `sensor_msgs/Image` | `line_detector.py` | 调试工具 | 遗留 HSV 路径调试图像，不是当前主链路必要话题 |

### 2. `/seam_center` 的特殊含义

当前系统没有单独定义自定义消息，而是复用了 `geometry_msgs/Point`。它在本项目中的语义不是空间三维点，而是一个轻量的控制接口：

```text
Point.x = bbox_center_x
Point.y = image_width
Point.z = valid_flag
```

这种话题设计直接体现了当前项目的数据流思想：视觉层不把完整框传给控制层，而是只传控制最需要的三个量。

## 六、图像输入到控制输出的全过程

### 1. 图像输入阶段

图像输入有两条分支。

第一条是实机分支。`seam_tracking.launch` 在 `use_fake_camera:=false` 时会 `include robot_camera.launch`。该 `launch` 内部调用 `uvc_camera_node`，默认相机分辨率为 `640x480`，帧率为 `30 fps`。它还会根据 `BASE_TYPE` 和 `CAMERA_TYPE` 环境变量决定相机标定文件与静态 TF。

第二条是假相机分支。`seam_tracking.launch` 在 `use_fake_camera:=true` 时会直接启动 `fake_camera.py`。该脚本读取一张本地图片，默认是 `robot_vision/data/bingda.png`，并以约 `30 Hz` 持续发布到 `/image_raw`。这条分支更适合做功能级调试和论文中的“软件验证流程”说明。

### 2. 视觉处理阶段

`yolo_seam_detector.py` 订阅 `/image_raw`，使用 `cv_bridge` 将 ROS 图像转换为 OpenCV 的 `bgr8` 图像，然后调用本地 `ultralytics.YOLO` 模型做推理。当前实现采取单帧单目标思路：

1. 获取当前帧全部候选框。
2. 若设定了 `target_class_id`，先按类别过滤。
3. 在剩余候选中选择最高置信度框。
4. 若存在候选，计算框中心；若不存在，则标记无效。

这一步的输出还不是控制量，而是控制前的“视觉几何代理量”。

### 3. 位置表征阶段

对最佳检测框，节点执行如下计算：

```text
bbox_center_x = (x1 + x2) / 2
bbox_center_y = (y1 + y2) / 2
```

然后把信息封装成：

```text
Point.x = bbox_center_x
Point.y = image_width
Point.z = 1.0
```

如果无有效检测，则输出：

```text
Point.x = -1.0
Point.y = image_width
Point.z = 0.0
```

这一步完成了“从视觉检测到控制接口”的关键转换。

### 4. 偏差计算阶段

`line_detector.py` 在外部中心点模式下不再订阅图像，而是订阅 `/seam_center`。在 `external_center_callback()` 中，它把 `Point.y` 解释为图像宽度 `W`，把 `Point.x` 解释为目标中心横坐标 `c_x`。随后它把 `W/2` 作为参考中心传给 `twist_calculate()`。

从论文意义上，可以把偏差写为：

```text
e_px = c_x - W/2
```

而当前控制器内部使用的等价控制表达是：

```text
e_ctrl = W/2 - c_x
```

这意味着目标位于图像中心左侧和右侧时，控制器能够根据符号产生相反方向的角速度。

### 5. 控制输出阶段

`twist_calculate()` 的输出逻辑可以分三段理解。

第一段是居中直行。若目标中心进入居中窗口，则：

```text
linear.x = 0.2
angular.z = 0
```

第二段是中等偏差修正。若目标不在居中窗口内，则先计算角速度：

```text
angular.z = (W/2 - c_x) / W
```

然后，当 `|angular.z| < 0.2` 时，线速度按角速度联动调节：

```text
linear.x = 0.2 - angular.z / 2
```

第三段是大偏差保守前进。当 `|angular.z| >= 0.2` 时：

```text
linear.x = 0.1
```

由此可见，当前控制器采用的是一种分段式、经验式的偏差到速度映射方法，而不是复杂的高阶控制器。

### 6. 底盘执行阶段

`base_control.py` 订阅 `cmd_vel`。在 `cmdCB()` 中，它读取：

- `linear.x`
- `linear.y`
- `angular.z`

然后将其乘以 `1000` 并按串口协议封装为速度控制帧，通过串口发送给下位机底盘。由于 `line_detector.py` 只设置了 `linear.x` 和 `angular.z`，并把 `linear.y` 固定为零，因此当前焊缝跟踪链路使用的是“前进 + 转向”控制方式，而不是横向平移控制。

底盘接口层同时会周期性查询和发布：

- `odom`
- `battery`
- 可选 `imu`
- 可选 `sonar`

这些反馈不是当前焊缝主方法的一部分，但属于完整机器人系统的执行接口支撑。

## 七、系统闭环如何形成

### 1. 实机闭环

当前系统的实机闭环逻辑是：

```text
相机看到焊缝 ->
YOLO 给出焊缝目标位置 ->
控制器根据目标偏差生成 cmd_vel ->
底盘执行运动 ->
机器人姿态变化导致下一帧图像中焊缝位置改变 ->
进入下一轮检测与控制
```

因此，这是一个标准的“视觉感知驱动运动，运动结果再反馈到视觉”的闭环系统。

### 2. 假相机调试链路

在 `use_fake_camera:=true` 时，系统虽然仍可运行感知与控制节点，但输入图像是静态图片，因此此时形成的不是严格意义上的物理闭环，而是“软件功能验证链路”。这一点在论文中应如实写明，不应把静态图片调试包装成完整跟踪实验。

### 3. 仿真支撑链路

`nanoomni_description` 的 Gazebo 配置中存在：

- `cmd_vel` 驱动插件
- 相机 `image_raw` 话题插件
- `scan`、`imu` 等仿真插件

因此，从结构上看，它具备构造“视觉感知 + 仿真运动”闭环的基础。另一方面，`robot_simulation` 更偏向 Stage 的二维地图导航与雷达定位，并不直接提供焊缝视觉场景。因此，在当前论文叙事中，更合理的写法是：

- `nanoomni_description`：视觉闭环仿真的潜在支撑模块
- `robot_simulation`：通用导航仿真支撑模块

而不是把它们写成当前焊缝主链路的一部分。

## 八、关键 launch 与参数关系

### 1. `seam_tracking.launch` 关键参数

| 参数名 | 默认值 | 作用 |
| --- | --- | --- |
| `run_base_control` | `false` | 是否接入底盘控制桥接 |
| `use_fake_camera` | `false` | 是否使用假相机 |
| `model_path` | 空字符串 | YOLO 权重路径，必须人工提供 |
| `yolo_repo_path` | `$(find robot_vision)/../../../../yolo` | 本地 YOLO 代码库路径 |
| `image_topic` | `/image_raw` | 图像输入话题 |
| `center_topic` | `/seam_center` | 中心点输出话题 |
| `result_topic` | `/result_image` | 调试图像输出话题 |
| `conf_threshold` | `0.25` | 检测置信度阈值 |
| `imgsz` | `640` | YOLO 推理尺寸 |
| `target_class_id` | `-1` | 默认按最高置信度选择，不限定类别 |
| `external_center_timeout` | `0.5` | 外部中心点超时阈值 |

### 2. 实机运行的隐含环境依赖

当前源码显示，实机路径还依赖以下环境变量：

- `BASE_TYPE`
- `CAMERA_TYPE`

其中：

- `robot_camera.launch` 使用 `$(env BASE_TYPE)` 与 `$(env CAMERA_TYPE)` 决定相机翻转和标定文件
- `base_control.py` 读取 `BASE_TYPE` 决定日志输出、部分底盘类型分支和 TF 处理

因此，论文中的运行说明必须明确指出：当前主入口虽然是 `seam_tracking.launch`，但回到原环境运行时仍需人工确认这些环境变量的实际取值。

## 九、异常处理与安全逻辑链

当前系统的安全逻辑具有三层。

第一层是感知层无效标志。YOLO 节点无检测时发布 `Point.z = 0.0`。

第二层是控制层零速度输出。`line_detector.py` 收到无效标志时立即调用 `publish_stop()`，发布全零 `Twist`；如果有效中心点长时间未更新，定时器也会重复发布零速度。

第三层是底盘侧通讯超时保护。`base_control/README.md` 说明，当上位机超过 `1000 ms` 未发送新的协议内数据时，底盘会主动停止电机运动。

因此，当前系统的安全逻辑并不是复杂容错控制，而是“感知无效即停、消息超时即停、通讯断联仍停”的层级式保守策略。

## 十、哪些原控制代码被保留

根据 git 提交 `208353c Add seam tracking integration` 的 diff，可以确认以下事实：

1. `line_detector.py` 中新增的是 `use_external_center`、`external_center_topic`、`external_center_timeout`、`publish_stop()`、`external_center_callback()`、`external_center_watchdog()` 等外部中心点适配逻辑。
2. `twist_calculate()` 控制律主体没有在该集成提交中被重写。
3. 旧版 `line_follow.launch` 仍然保留，说明 HSV 线中心提取路径没有被删除。

这说明当前项目在系统逻辑上采用的是“保留原控制器、替换前端位置来源”的策略。

## 十一、哪些内容是新增或新建立的

从当前仓库和提交历史可以确认，以下内容属于焊缝跟踪主链路新增或新建立的部分：

1. `robot_vision/scripts/yolo_seam_detector.py`
2. `robot_vision/launch/seam_tracking.launch`
3. `robot_vision/package.xml` 中对 `geometry_msgs` 与 `dynamic_reconfigure` 运行依赖的补充
4. `line_detector.py` 中的外部中心点输入适配与安全停机逻辑
5. 根目录 `README.md` 中的焊缝跟踪运行说明

## 十二、支撑模块角色定位

### 1. `nanoomni_description`

该包提供：

- URDF/Xacro 机器人模型
- RViz 显示
- Gazebo 场景
- `cmd_vel`、`image_raw`、`scan` 等 Gazebo 插件接口

因此它应被定位为“模型与仿真支撑模块”，而不是“当前主控制方法所在包”。

### 2. `robot_simulation`

该包提供：

- Stage 地图与世界文件
- `simulation_one_robot.launch`
- `simulation_one_robot_with_map.launch`
- AMCL 配套定位

它更适合被描述为“二维导航/地图仿真支撑包”，与当前焊缝视觉主链路不是同一层次。

### 3. `robot_navigation` 与 `lidar/*`

这些包用于雷达、导航和地图定位，不应被写成当前焊缝跟踪论文的核心方法来源。它们最多作为完整机器人平台的配套能力出现。

## 十三、论文写作时应如何使用本文件

本文件最适合支撑以下内容：

1. “系统总体流程图”与“节点关系图”的绘制
2. “系统实现”章节中对节点功能、话题关系和 launch 组织方式的说明
3. “感知到控制闭环”部分的逻辑描述
4. “异常处理与安全停机”部分的机制说明

如果要写“方法章节”，还需要同时查看 `01_METHODS_PRINCIPLES_MASTER_CN.md`；如果要避免把推断写成事实，则需配合 `06_EVIDENCE_MAP_CN.md` 使用。
