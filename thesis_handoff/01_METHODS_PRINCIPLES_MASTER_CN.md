# 方法与原理主文档

## 一、本项目最终系统的一句话技术定义

本项目构建的是一种基于单目图像目标检测、边界框中心位置表征与中心偏差控制的 ROS1 焊缝跟踪机器人系统，其核心任务是把视觉检测结果稳定地转换为 `cmd_vel` 运动控制量，并在目标失效时执行安全停机。

## 二、本项目面向的核心问题

从当前仓库的真实实现可以看出，本项目并不是在研究复杂的焊缝三维重建或高阶轨迹规划，而是在解决一个更适合本科毕业设计完成度与可解释性的关键问题：如何让移动机器人在 ROS1 环境下，依据相机图像中的焊缝目标位置，实现连续的方向修正与前进控制。

原有 `robot_vision/scripts/line_detector.py` 已经具备一套较简洁、稳定的中心偏差控制能力，但其传统输入来自颜色阈值分割后的“线中心”。当作业对象从规则彩色引导线转向焊缝目标时，单纯依赖 HSV 阈值的方式会受到表面纹理、亮度波动和背景干扰的影响。因此，当前项目的关键技术路线并不是重新发明一套控制器，而是把“目标检测结果”转换成“控制器可直接理解的位置偏差量”，从而建立面向焊缝跟踪任务的视觉到控制通道。

## 三、本项目采用的总体技术路线

当前代码对应的总体技术路线可以概括为：

1. 通过相机节点或假相机节点提供图像输入。
2. 使用 `yolo_seam_detector.py` 对图像进行目标检测，输出最优检测框。
3. 从检测框中提取横向中心坐标，将其压缩为控制所需的最小几何量。
4. 将目标中心与图像中心建立偏差关系。
5. 使用保留下来的 `line_detector.py` 控制律计算角速度与线速度。
6. 将 `cmd_vel` 交给 `base_control.py`，再由底盘串口协议执行运动。
7. 当视觉结果失效或中断时，触发零速度输出与底盘超时停机机制。

因此，本项目的论文表达重点不应放在“整合了 YOLO 和旧控制系统”，而应放在“提出了一种基于检测框中心位置表征和中心偏差控制的焊缝视觉跟踪方法，并在 ROS1 系统中实现了闭环落地”。

## 四、本项目的核心方法体系

### 4.1 基于 YOLO 检测的焊缝目标感知方法

该方法对应当前系统的感知前端，由 `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` 实现。它的作用不是直接输出轨迹，也不是输出分割曲线，而是从图像中识别焊缝目标所在区域，并给出一个可用于控制的检测框。

① 方法名称：基于 YOLO 检测的焊缝目标感知方法。

② 要解决的问题：在图像中稳定找出焊缝目标区域，使后续控制不再依赖传统 HSV 颜色阈值分割。

③ 输入：`sensor_msgs/Image` 图像消息、`model_path` 权重路径、`conf_threshold` 置信度阈值、`target_class_id` 类别筛选参数、`imgsz` 推理尺寸参数。

④ 输出：当前帧的最佳检测框，以及由该检测框进一步派生出的目标中心横坐标与有效标志。

⑤ 基本原理：节点在启动时读取 `~model_path` 并调用本地 `yolo/ultralytics` 中的 `YOLO` 类加载模型；在每一帧回调中调用 `model.predict()` 进行推理；如果存在多个候选框，则按照置信度从高到低选择最优框；若设置了 `target_class_id`，则先进行类别过滤，再在剩余候选中选取最高置信度框。

⑥ 关键逻辑关系或公式关系：

```text
best_box = argmax_conf(boxes)
best_box = argmax_conf(boxes where cls == target_class_id), if target_class_id >= 0
```

若当前帧无检测框，则感知结果记为无效。

⑦ 在当前项目中由哪些代码/节点/脚本实现：`robot_vision/scripts/yolo_seam_detector.py` 的 `load_model()`、`find_best_box()`、`image_callback()`；启动由 `robot_vision/launch/seam_tracking.launch` 完成；本地推理后端依赖 `yolo/ultralytics/` 目录。

⑧ 为什么适合当前本科毕业设计：目标检测输出形式明确、接口简单、工程复用性高，不需要重新设计复杂的视觉测量模型；同时它可以把“焊缝是否被识别到”这一问题与后端控制逻辑解耦，便于论文中分章节展开。

⑨ 局限性：当前方法只选择单帧中“最佳”的一个检测框，没有时间序列滤波、轨迹关联和多目标判别机制；当前仓库缺少实际 `.pt` 权重文件，因此具体模型结构与类别语义仍需人工确认。

### 4.2 基于检测框中心的目标位置表征方法

当前系统并没有把完整检测框直接交给控制器，而是采用了一种更适合控制接口复用的位置压缩表达方式：把二维检测框压缩成“目标中心横坐标 + 图像宽度 + 有效标志”。这一步是整个论文表达中非常关键的方法抽象，因为它解释了视觉信息如何被转化为控制可以理解的量。

① 方法名称：基于检测框中心的目标位置表征方法。

② 要解决的问题：将复杂的视觉检测结果转化为轻量、稳定、可直接送入原有偏差控制器的几何量。

③ 输入：目标检测框坐标 `(x1, y1, x2, y2)` 与当前图像宽度 `W`。

④ 输出：`geometry_msgs/Point` 类型消息，其中 `Point.x` 表示目标中心横坐标，`Point.y` 表示图像宽度，`Point.z` 表示检测有效性。

⑤ 基本原理：系统只保留与横向偏差控制直接相关的横向中心信息，不保留检测框面积、纵向位置、长宽比等控制链路暂不需要的冗余量，从而将感知层输出压缩成一个“中心位置代理量”。

⑥ 关键逻辑关系或公式关系：

```text
bbox_center_x = (x1 + x2) / 2
bbox_center_y = (y1 + y2) / 2
message.x = bbox_center_x
message.y = image_width
message.z = 1.0 if detection_valid else 0.0
```

需要注意的是，当前控制器只实际使用 `bbox_center_x` 与 `image_width`，并不使用 `bbox_center_y`。

⑦ 在当前项目中由哪些代码/节点/脚本实现：`robot_vision/scripts/yolo_seam_detector.py` 的 `publish_center()` 与 `image_callback()`。

⑧ 为什么适合当前本科毕业设计：这种表征方式具有两个优点。第一，它使“感知层”和“控制层”之间的数据接口非常简洁，便于调试与论文阐述。第二，它最大限度复用了旧控制器只关心“中心偏差”的结构，降低了重构成本与回归风险。

⑨ 局限性：该方法忽略了焊缝形状、角度、长度和纵向延展信息，因此本质上是一种“单点中心代理”方法，而不是完整的焊缝几何建模方法。

### 4.3 基于图像中心参照的偏差构建方法

控制器并不直接关心检测框本身，而是关心“目标相对期望位置偏了多少”。当前系统采用图像中心作为参考位置，因此偏差的本质是“目标中心与图像中心的横向差值”。

① 方法名称：基于图像中心参照的偏差构建方法。

② 要解决的问题：建立从视觉位置量到控制误差量的映射，使控制器可以根据偏差生成方向修正。

③ 输入：图像宽度 `W`、目标中心横坐标 `bbox_center_x`。

④ 输出：横向像素偏差或等价的归一化偏差量。

⑤ 基本原理：系统假设理想跟踪状态下目标应处于图像中心附近，因此把图像中心 `W/2` 作为期望位置。当目标中心偏离图像中心时，偏差的符号和大小就反映了机器人需要向哪一侧修正。

⑥ 关键逻辑关系或公式关系：

从几何意义上，可以写为：

```text
image_center_x = W / 2
e_px = bbox_center_x - image_center_x
```

而当前控制器内部采用的等价控制偏差写法是：

```text
e_ctrl = image_center_x - bbox_center_x
```

二者只差一个符号。前者更适合论文中的位置偏差定义，后者更贴近当前控制律实现。

⑦ 在当前项目中由哪些代码/节点/脚本实现：`line_detector.py` 中 `external_center_callback()` 读取 `Point.y` 作为图像宽度，再以 `image_width / 2.0` 作为控制参考中心传入 `twist_calculate()`。

⑧ 为什么适合当前本科毕业设计：图像中心参照法直观、可解释性强，不需要额外标定焊缝空间坐标或建立复杂透视模型，适合在有限时间内完成一套可运行、可写作、可调试的跟踪系统。

⑨ 局限性：该偏差构造默认“期望焊缝位置等于图像中心”，没有显式处理相机安装偏移、视角透视误差和焊缝姿态变化，因此更适合作为工程上可行的本科方案，而不是高精度工业测量方案。

### 4.4 基于归一化中心偏差的焊缝跟踪控制方法

当前系统控制层最核心的部分仍然是 `line_detector.py` 中的 `twist_calculate()`。从 git 历史可见，在 `208353c Add seam tracking integration` 这次集成提交中，新增的是外部中心点输入能力，而不是重写控制律本身。因此，该控制方法可以被视为“原有中心偏差控制器在焊缝任务中的延续应用”。

① 方法名称：基于归一化中心偏差的焊缝跟踪控制方法。

② 要解决的问题：根据视觉偏差计算转向角速度与前进速度，使机器人在目标偏离时能纠偏，在目标居中时能直行。

③ 输入：图像中心横坐标 `image_center_x = W/2` 与目标中心横坐标 `bbox_center_x`。

④ 输出：`geometry_msgs/Twist` 中的 `linear.x` 与 `angular.z`，其中 `linear.y`、`linear.z`、`angular.x`、`angular.y` 被置零。

⑤ 基本原理：当目标中心落入设定居中范围时，机器人以固定前进速度直行；当目标偏离时，系统根据偏差构造角速度，并根据角速度大小调整线速度，形成“偏差越大，转向越明显，速度越保守”的控制趋势。

⑥ 关键逻辑关系或公式关系：

当前源码中的控制逻辑可整理为：

```text
if 0.95 < bbox_center_x / image_center_x < 1.05:
    linear.x = 0.2
    angular.z = 0
else:
    angular.z = ((image_center_x - bbox_center_x) / image_center_x) / 2
    if abs(angular.z) < 0.2:
        linear.x = 0.2 - angular.z / 2
    else:
        linear.x = 0.1
```

若代入 `image_center_x = W / 2`，则角速度项可化简为：

```text
angular.z = (W / 2 - bbox_center_x) / W
```

这说明当前控制器实质上采用了“以图像宽度归一化的中心偏差比例控制”。

⑦ 在当前项目中由哪些代码/节点/脚本实现：`robot_vision/scripts/line_detector.py` 的 `twist_calculate()`。

⑧ 为什么适合当前本科毕业设计：该方法结构非常清晰，不需要引入 PID、模型预测控制或状态估计等更复杂的理论，就能形成可运行的闭环控制；同时 git 历史表明该控制器主体被完整保留，论文中可以强调“在保留原稳定控制链路基础上完成焊缝任务迁移”。

⑨ 局限性：当前控制律属于经验式比例控制，未使用显式动力学模型，也没有积分项、微分项或自适应机制；此外，`linear.x = 0.2 - angular.z / 2` 使用了带符号的角速度，导致速度调节对左右偏差并非严格对称，这一点在论文中应被如实标注为当前实现特征，而不应包装成更高级的控制算法。

### 4.5 基于转向强度约束的速度协同调节方法

虽然线速度与角速度都由同一个控制器输出，但从论文写法上看，仍然有必要把“速度协同调节”单独抽象出来，因为它体现了当前系统如何在“跟踪准确性”和“前进效率”之间做工程化平衡。

① 方法名称：基于转向强度约束的速度协同调节方法。

② 要解决的问题：在保持焊缝跟踪能力的同时，避免目标偏差较大时仍以较高速度前进，从而降低跟踪失稳风险。

③ 输入：目标偏差对应的角速度 `angular.z`。

④ 输出：与当前转向需求相匹配的前进速度 `linear.x`。

⑤ 基本原理：系统采用分段调节思想。当目标基本居中时，以较高线速度直行；当偏差存在但仍处于可平滑修正范围内时，线速度随转向强度进行联动调整；当角速度超过阈值时，把线速度压到较低值，以优先保证姿态修正。

⑥ 关键逻辑关系或公式关系：

```text
straight zone:
    linear.x = 0.2

small-turn zone:
    if abs(angular.z) < 0.2:
        linear.x = 0.2 - angular.z / 2

large-turn zone:
    linear.x = 0.1
```

从代码意义上看，该方法不是独立的新控制器，而是原控制律中的“速度约束层”。

⑦ 在当前项目中由哪些代码/节点/脚本实现：`robot_vision/scripts/line_detector.py` 的 `twist_calculate()`。

⑧ 为什么适合当前本科毕业设计：这种分段式速度协同调节容易说明、容易调试，也容易在论文中用曲线或流程图表示，既能体现控制思想，又不会让系统复杂度超出本科项目承受范围。

⑨ 局限性：当前仓库没有提供速度参数调节实验，因此无法从仓库事实中证明 `0.2` 与 `0.1` 是最优参数；论文中更适合把它表述为“当前工程实现采用的经验参数”，而不是“经过充分优化的最优控制参数”。

### 4.6 基于 ROS1 话题解耦的感知到控制闭环实现方法

从系统工程角度看，本项目真正完成的是一条可运行的 ROS1 视觉控制链路。它通过节点拆分、话题传输和 launch 调度，把视觉感知、偏差控制、底盘接口连接成一个清晰的层级结构。

① 方法名称：基于 ROS1 话题解耦的感知到控制闭环实现方法。

② 要解决的问题：让视觉检测、控制计算和底盘执行在 ROS1/catkin 架构下稳定协作，并保留调试与替换能力。

③ 输入：相机图像、检测中心消息、速度指令消息。

④ 输出：底盘运动、调试图像、底盘反馈话题。

⑤ 基本原理：系统通过 `seam_tracking.launch` 统一调度运行入口；通过 `/image_raw` 传递图像；通过 `/seam_center` 传递控制所需的位置表征量；通过 `cmd_vel` 传递速度指令；通过 `base_control.py` 完成到底盘串口协议的映射。这样，感知节点与控制节点之间只通过消息接口耦合，从而实现低侵入式复用。

⑥ 关键逻辑关系或公式关系：

```text
/image_raw -> yolo_seam_detector -> /seam_center -> line_detector -> cmd_vel -> base_control -> chassis
```

在调试模式下，还可以替换真实相机为 `fake_camera.py`：

```text
fake_camera -> /image_raw -> yolo_seam_detector -> /seam_center -> line_detector
```

⑦ 在当前项目中由哪些代码/节点/脚本实现：`robot_vision/launch/seam_tracking.launch`、`robot_vision/launch/robot_camera.launch`、`robot_vision/scripts/fake_camera.py`、`robot_vision/scripts/yolo_seam_detector.py`、`robot_vision/scripts/line_detector.py`、`base_control/launch/base_control.launch`、`base_control/script/base_control.py`。

⑧ 为什么适合当前本科毕业设计：ROS1 话题解耦方式非常适合做本科论文中的“总体架构设计”，因为每个节点的作用、输入输出和相互关系都能够被明确说明，而且改动边界清晰，便于回答“保留了哪些原代码、增加了哪些新模块”。

⑨ 局限性：当前主入口对实机运行仍依赖外部环境变量 `BASE_TYPE` 与 `CAMERA_TYPE`，而这些变量并未在 `seam_tracking.launch` 中直接暴露为参数；另外，YOLO 节点使用 Python3，旧控制链路使用 Python2 风格脚本，混合运行环境需要人工确认。

### 4.7 基于有效性标志与超时监测的异常安全处理方法

对于焊缝跟踪系统而言，识别失败时继续运动比停下更危险。因此，当前项目虽然没有构建复杂的故障诊断状态机，但已经实现了一套朴素而有效的安全处理逻辑。

① 方法名称：基于有效性标志与超时监测的异常安全处理方法。

② 要解决的问题：在检测无效、目标丢失或消息中断的情况下，防止机器人继续按旧指令盲目前进。

③ 输入：检测有效标志、外部中心点最近更新时间、底盘通讯超时规则。

④ 输出：零速度 `Twist` 消息，必要时由底盘侧触发被动停机。

⑤ 基本原理：YOLO 节点在无检测时输出 `Point.z = 0.0`；控制节点在收到无效标志时立刻发布零速度；控制节点还通过定时器监测外部中心点是否超时，超过 `external_center_timeout` 仍无有效中心点时继续发布零速度；底盘协议文档进一步规定，上位机超过 1000 ms 未发送协议内数据时，底盘会主动停止电机。

⑥ 关键逻辑关系或公式关系：

```text
if detection_invalid:
    publish zero Twist

if time_since_last_valid_center > external_center_timeout:
    publish zero Twist

if no new chassis command for > 1000 ms:
    chassis stops itself
```

⑦ 在当前项目中由哪些代码/节点/脚本实现：`yolo_seam_detector.py` 的 `publish_center(..., valid=False)`；`line_detector.py` 的 `publish_stop()`、`external_center_callback()`、`external_center_watchdog()`；`base_control/README.md` 中关于 1000 ms 断联停机的底盘协议说明。

⑧ 为什么适合当前本科毕业设计：该方法虽然简单，但安全逻辑清晰、实现成本低、可解释性强，非常适合写成论文中的“异常处理与安全机制”一节。

⑨ 局限性：当前安全策略以“停机”为主，没有更细分的故障级别、缓停曲线或再定位策略；因此适合毕业设计级系统，但不宜包装为复杂的容错控制框架。

### 4.8 基于 URDF/Gazebo/Stage 的模型与仿真支撑方法

当前仓库并不只有主运行链路，还保留了模型、Gazebo 和 Stage 相关包。它们虽然不是当前 `seam_tracking.launch` 的主执行通路，但对于论文写作中的“系统实现支撑环境”与“仿真基础”仍有价值。

① 方法名称：基于 URDF/Gazebo/Stage 的模型与仿真支撑方法。

② 要解决的问题：为机器人系统提供模型描述、可视化和潜在仿真运行环境，以支撑总体架构说明与后续验证扩展。

③ 输入：URDF/Xacro 机器人描述、Gazebo 插件、Stage 地图与世界文件、`cmd_vel` 等标准 ROS 接口。

④ 输出：机器人模型显示、Gazebo 中的运动与相机话题、Stage 中的二维导航仿真环境。

⑤ 基本原理：`nanoomni_description` 通过 URDF/Xacro 描述机器人结构，并在 Gazebo 插件中定义 `cmd_vel`、`odom`、`image_raw`、`scan` 等接口；`robot_simulation` 使用 Stage 地图与世界文件实现二维导航仿真；`robot_navigation` 和 `lidar/*` 提供雷达与导航配套能力。

⑥ 关键逻辑关系或公式关系：

```text
nanoomni_description:
    cmd_vel -> gazebo_ros_planar_move -> simulated motion
    gazebo camera plugin -> image_raw

robot_simulation:
    stage world + map + amcl
```

⑦ 在当前项目中由哪些代码/节点/脚本实现：`catkin_ws/src/nanoomni_description/urdf/nanoomni_description.gazebo.xacro`、`catkin_ws/src/nanoomni_description/launch/*.launch`、`catkin_ws/src/robot_simulation/launch/*.launch`、`catkin_ws/src/robot_navigation/launch/*.launch`。

⑧ 为什么适合当前本科毕业设计：这些支撑材料有助于在论文中补充“系统总体实现环境”和“后续仿真扩展能力”，尤其是 `nanoomni_description` 中已经存在相机话题与 `cmd_vel` 插件，说明系统具有向视觉仿真扩展的基础。

⑨ 局限性：当前主入口 `seam_tracking.launch` 并未直接调用这些仿真包；`robot_simulation` 更偏向雷达导航而非焊缝视觉任务；因此它们应被写成支撑模块，而不能拔高为当前论文的主方法。

## 五、为什么这条方法路线适合本科毕业设计

从当前仓库与提交历史看，项目采用的是一种非常典型、也非常适合本科毕业设计完成的技术路线：不推翻原稳定控制链路，而是把问题集中到“视觉结果如何映射成控制器所需的位置偏差量”上。这样做有四个明显优点。

第一，方法链条短。图像经过检测后，只需提取检测框中心并构造相对图像中心的偏差，即可进入控制器，不需要增加大规模中间层。

第二，逻辑闭合清楚。感知、表征、偏差、控制、执行和安全停机之间存在完整而可解释的因果关系，适合写成论文的方法章节。

第三，保留了原稳定控制器。git diff 清楚表明 `line_detector.py` 的 `twist_calculate()` 没有被重写，新增内容只是外部中心点输入与超时停机逻辑，这使得系统具有较低的回归风险。

第四，论文表达空间充足。虽然工程实现较简洁，但完全可以被提升为“目标感知方法、位置表征方法、偏差构建方法、跟踪控制方法、速度协同调节方法、ROS1 闭环实现方法、安全处理方法”这样一整套技术体系。

## 六、本项目的总体局限性

从论文写作角度，以下局限性需要如实说明，而不是回避：

1. 当前仓库不包含实际部署权重文件，无法从源码直接证明具体模型精度与类别定义。
2. 训练脚本与验证脚本仍含占位路径或外部路径，说明训练过程材料并不完整。
3. 当前控制器本质上是经验式比例控制，不能写成 PID、Stanley、滑模或模型预测控制。
4. 位置表征只使用了检测框中心横坐标，没有建立更高阶几何模型。
5. 仿真与模型包存在，但没有看到“焊缝视觉场景 + seam_tracking 主链路”一键联通的直接证据。
6. 混合 Python2/Python3 的 ROS 运行环境需要人工确认。

## 七、项目关键问题直答

### 1. 这个项目最终是什么系统？

它是一个基于 YOLO 目标检测与中心偏差控制的 ROS1 焊缝跟踪机器人系统。

### 2. 这个系统的研究目标是什么？

研究目标是在不重写原稳定控制链路的前提下，实现从焊缝视觉检测到机器人运动控制的闭环跟踪。

### 3. 这个系统采用了哪些具体方法？

采用了焊缝目标感知、目标位置表征、偏差构建、偏差控制、速度协同调节、ROS1 闭环实现、安全停机和模型仿真支撑等方法。

### 4. 每个方法的原理是什么？

核心原理是先用 YOLO 找到焊缝目标区域，再用检测框中心作为横向位置代理量，把它与图像中心建立偏差关系，并将偏差映射为 `cmd_vel` 中的线速度与角速度。

### 5. 系统完整逻辑链条是什么？

`/image_raw -> yolo_seam_detector -> /seam_center -> line_detector -> cmd_vel -> base_control -> chassis -> new image`

### 6. YOLO 在这里承担什么功能？

YOLO 是视觉感知前端，负责识别焊缝目标并输出最优检测框。

### 7. 控制器在这里承担什么功能？

控制器负责根据目标中心与图像中心的偏差，计算机器人前进速度和转向角速度。

### 8. 视觉信息是如何转换成运动控制量的？

系统先计算检测框中心横坐标，再与图像中心横坐标比较形成偏差，最后通过 `twist_calculate()` 输出 `linear.x` 和 `angular.z`。

### 9. 系统闭环是如何形成的？

机器人执行 `cmd_vel` 后会改变视野中的目标位置，新的图像再次进入感知节点，从而形成视觉到运动的反馈闭环。

### 10. 为什么这种方法路线适合本科毕业设计？

因为它改动小、逻辑清晰、风险低、容易调试，也容易写成完整的方法章节。

### 11. 这个项目已经完成了哪些工作？

已经完成 YOLO 节点、外部中心点适配、主 launch 入口、假相机调试链路、原控制器复用和底盘接口贯通。

### 12. 这个项目还有哪些不足与局限？

缺少权重文件、训练数据说明、实验数据、实机截图和完整环境说明，控制方法也较为基础。

### 13. 回到原运行环境后如何 `catkin_make` 与 `roslaunch`？

构建方式仍然是标准 ROS1/catkin：

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
```

调试运行优先建议使用假相机链路：

```bash
roslaunch robot_vision seam_tracking.launch \
  run_base_control:=false \
  use_fake_camera:=true \
  fake_image_path:=$(rospack find robot_vision)/data/bingda.png \
  model_path:=<YOLO_WEIGHT_PATH>
```

实机运行前还需人工确认 `BASE_TYPE`、`CAMERA_TYPE`、串口设备与实际权重路径。

### 14. 新 GPT 只看这些文档，是否足够继续帮我写论文？

足够。若只看一份文件，优先看 `08_ALL_IN_ONE_GPT_HANDOFF_CN.md`；若要稳妥写方法章节，再补看本文件与 `02_SYSTEM_LOGIC_AND_DATAFLOW_CN.md`。
