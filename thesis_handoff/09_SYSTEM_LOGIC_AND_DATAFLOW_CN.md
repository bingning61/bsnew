# 系统逻辑与数据流文档

## 1. 总体说明

当前系统的主链路已经可以明确表示为：

```text
图像输入
-> YOLO 检测
-> 检测框中心提取
-> 图像中心偏差构建
-> cmd_vel 生成
-> 底盘执行
-> 新图像反馈
```

如果把 ROS1 节点和话题写全，则主数据流为：

```text
/image_raw
  -> yolo_seam_detector.py
  -> /seam_center (geometry_msgs/Point)
  -> line_detector.py
  -> cmd_vel (geometry_msgs/Twist)
  -> base_control.py
  -> /dev/move_base 底盘控制板
  -> 机器人运动
  -> 下一帧 /image_raw
```

该链路是当前仓库中最核心、最适合写论文的数据流。

## 2. 图像输入阶段

### 2.1 真实相机路径

当 `seam_tracking.launch` 中 `use_fake_camera:=false` 时，系统会包含 `robot_camera.launch`。该 launch 调用 `uvc_camera` 节点，从 `/dev/video0` 采集图像，并根据 `CAMERA_TYPE` 加载 `robot_vision/config/` 下的相机标定文件。若 `camera_tf:=true`，launch 还会依据 `BASE_TYPE` 发布从底盘到相机的静态 TF。

因此，真实相机路径的数据流可以写成：

`USB camera -> uvc_camera -> /image_raw`

### 2.2 假相机调试路径

当 `use_fake_camera:=true` 时，系统启动 `fake_camera.py`，该节点将指定图像文件反复发布到 `/image_raw`。当前默认测试图像为 `robot_vision/data/bingda.png`。这一调试路径不依赖真实相机和底盘，非常适合论文第四章中说明系统调试方法。

该路径可写成：

`bingda.png -> fake_camera.py -> /image_raw`

## 3. 视觉处理阶段

### 3.1 YOLO 节点的输入

`yolo_seam_detector.py` 订阅 `/image_raw`，利用 `cv_bridge` 将 ROS 图像转换为 OpenCV 图像，再调用本地 YOLO 模型进行推理。节点的关键输入参数包括：

- `image_topic`
- `center_topic`
- `result_topic`
- `model_path`
- `yolo_repo_path`
- `conf_threshold`
- `imgsz`
- `target_class_id`
- `device`

### 3.2 YOLO 节点的处理逻辑

该节点首先加载 YOLO 权重文件。若 `model_path` 为空或文件不存在，节点会报错并终止。推理完成后，节点从所有检测框中选出一个最优框。默认策略是在可用类别范围内选择置信度最高的框；若设置了 `target_class_id`，则只在指定类别内筛选。

### 3.3 YOLO 节点的输出

YOLO 节点输出两个结果：

1. `/seam_center`：类型为 `geometry_msgs/Point`
2. `/result_image`：类型为 `sensor_msgs/Image`

其中 `/seam_center` 是当前主链路最重要的中间量。它的含义为：

- `Point.x`：目标中心横坐标 `x_obj`
- `Point.y`：图像宽度 `W`
- `Point.z`：有效标志，`1.0` 表示有有效检测，`0.0` 表示无有效检测

可以看出，视觉节点已经把控制器真正需要的信息从原始检测框中抽象出来。

## 4. 位置表征到偏差计算阶段

### 4.1 控制节点的输入模式

`line_detector.py` 在 `seam_tracking.launch` 中以外部中心点模式启动，其关键参数包括：

- `use_external_center=true`
- `external_center_topic=/seam_center`
- `external_center_timeout=0.5`

这意味着当前控制节点不再订阅图像来做 HSV 阈值分割，而是直接订阅 `/seam_center`。

### 4.2 偏差构建过程

控制节点收到 `Point` 后，会先读取：

- `x_obj = Point.x`
- `W = Point.y`
- `v = Point.z`

若 `v` 有效且 `W>0`，则构造参考中心：

`x_ref = W / 2`

随后调用：

`twist_calculate(x_ref, x_obj)`

从而等价形成偏差：

`e = x_ref - x_obj`

可见，数据流在这一阶段从“视觉几何量”转变为“控制偏差量”。

## 5. 控制输出阶段

### 5.1 `twist_calculate()` 的作用

`twist_calculate()` 是当前主控制逻辑的核心函数。它把参考中心与目标中心之间的偏差，转换为 `geometry_msgs/Twist`。

### 5.2 控制量生成逻辑

该函数的输出逻辑如下：

- 若目标基本对准图像中心，则 `linear.x = 0.2`
- 否则计算 `angular.z = (x_ref - x_obj) / (2 x_ref)`
- 若 `|angular.z| < 0.2`，则 `linear.x = 0.2 - angular.z / 2`
- 若 `|angular.z| >= 0.2`，则 `linear.x = 0.1`

其余速度分量保持为零：

- `linear.y = 0`
- `linear.z = 0`
- `angular.x = 0`
- `angular.y = 0`

由此可知，控制节点输出的是一种以前进速度和偏航角速度为主的运动控制量。

### 5.3 安全停止逻辑

如果视觉节点输出无效目标，控制节点立即发布零速度。若超过 `external_center_timeout` 未收到新的有效中心消息，看门狗也会触发零速度。这里的数据流会直接切换为：

`/seam_center invalid or timeout -> line_detector.py -> zero cmd_vel`

## 6. 底盘执行阶段

### 6.1 `cmd_vel` 到底盘接口

当 `run_base_control:=true` 时，`seam_tracking.launch` 会包含 `base_control.launch`。此后，`base_control.py` 订阅 `cmd_vel`，读取 `linear.x`、`linear.y`、`angular.z`，将其按比例转换为整数数据并封装为串口协议，通过 `/dev/move_base` 发送到底盘控制板。

### 6.2 底盘反馈

`base_control.py` 在下发速度指令的同时，还会发布：

- `odom`
- `battery`
- 可选 `imu`
- 可选 `sonar_x`

这些反馈数据目前主要服务于底盘运行监测和通用机器人功能，并未直接进入焊缝跟踪控制律。

## 7. 节点关系

### 7.1 主链路节点

| 节点 | 作用 |
| --- | --- |
| `uvc_camera` 或 `fake_camera` | 产生 `/image_raw` |
| `yolo_seam_detector` | 消费图像并输出 `/seam_center`、`/result_image` |
| `linefollow` | 消费 `/seam_center` 并输出 `cmd_vel` |
| `base_control` | 消费 `cmd_vel` 并驱动底盘 |

### 7.2 支撑节点

| 节点或包 | 作用 |
| --- | --- |
| `image_transport republish` | 旧 HSV 路径下的调试图像转发 |
| `nanoomni_description` | URDF、Gazebo 传感器和模型支撑 |
| `robot_simulation` | Stage 通用移动平台仿真 |
| `robot_navigation` | 导航、定位、SLAM 支撑，不是焊缝跟踪主链路 |

## 8. 关键话题关系

### 8.1 当前焊缝跟踪主话题

| 话题名 | 类型 | 生产者 | 消费者 | 作用 |
| --- | --- | --- | --- | --- |
| `/image_raw` | `sensor_msgs/Image` | `uvc_camera` 或 `fake_camera` | `yolo_seam_detector` | 图像输入 |
| `/seam_center` | `geometry_msgs/Point` | `yolo_seam_detector` | `line_detector` | 目标中心与有效标志 |
| `/result_image` | `sensor_msgs/Image` | `yolo_seam_detector` | 调试显示 | 检测可视化 |
| `cmd_vel` | `geometry_msgs/Twist` | `line_detector` | `base_control` | 运动控制输出 |
| `odom` | `nav_msgs/Odometry` | `base_control` | 监测/其他模块 | 底盘反馈 |
| `battery` | `sensor_msgs/BatteryState` | `base_control` | 监测/其他模块 | 电池反馈 |

### 8.2 旧路径与辅助话题

| 话题名 | 说明 |
| --- | --- |
| `/mask_image` | 旧 HSV 路径下的阈值分割结果 |
| `/camera_info` | 相机标定信息 |
| `scan` | 激光雷达或仿真雷达话题，属于通用平台能力 |

## 9. 参数与 launch 的关系

当前主 launch 中最关键的参数关系如下：

- `use_fake_camera`：决定图像输入来自真实相机还是静态测试图像
- `run_base_control`：决定是否将 `cmd_vel` 接入真实底盘执行接口
- `model_path`：决定 YOLO 节点加载哪一套权重
- `center_topic`：决定视觉节点与控制节点之间的接口话题
- `cmd_vel_topic`：决定控制输出与底盘输入之间的接口话题
- `external_center_timeout`：决定视觉消息超时后的停止时间窗口

从系统逻辑上看，这些参数决定了主链路是“仅调试感知与控制”，还是“感知控制加底盘执行”的完整运行方式。

## 10. 系统闭环如何形成

当前系统的闭环形成机制可以表述为：

1. 机器人或测试图像提供当前视觉输入。
2. YOLO 节点根据当前图像计算目标中心位置。
3. 控制节点根据目标中心位置生成 `cmd_vel`。
4. 底盘执行 `cmd_vel` 后改变机器人位姿。
5. 机器人位姿变化又影响下一帧图像中的目标位置。
6. 新图像继续进入 YOLO 节点。

这里的关键在于：**闭环反馈量是目标在图像中的位置变化**。也就是说，系统通过视觉结果不断修正自身运动，使目标趋近图像中心。

## 11. 仿真/模型支撑数据流

虽然当前主 launch 未直接调用仿真包，但 `nanoomni_description` 在 Gazebo 中已经定义了兼容主链路的接口：

- 相机插件输出 `image_raw`
- 平面运动插件输入 `cmd_vel`
- 里程计插件输出 `odom`

这意味着从接口角度看，Gazebo 模型具备与主链路兼容的条件。与此同时，`robot_simulation` 基于 Stage 提供通用移动平台仿真环境，能够支撑地图与运动验证。然而，仓库中没有把这些仿真资源与焊缝跟踪主链路直接整合成专用 launch，因此第四章写作时应把它们定位为“仿真支撑能力”，而不是“已完成的焊缝跟踪仿真闭环”。

## 12. 当前数据流文档的结论

当前项目的数据流已经清晰地体现出一种“最小几何接口驱动的感知到控制闭环”结构。视觉节点把复杂检测结果压缩为目标中心横坐标、图像宽度和有效标志；控制节点再把这些量转化为偏差和 `cmd_vel`；底盘接口负责执行与反馈。由此，整个系统在 ROS1 中形成了一条从视觉感知到运动执行的清晰链路。这正是当前项目最适合被提升为本科毕业论文技术方案的根本原因。
