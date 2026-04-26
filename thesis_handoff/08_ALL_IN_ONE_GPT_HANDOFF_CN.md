# 单文件总交接包

## 一、项目定义

当前项目可论文化定义为：

**一种基于 YOLO 视觉目标感知、检测框中心位置表征与中心偏差控制的 ROS1 焊缝跟踪机器人系统。**

它的核心不是简单“把两个系统拼起来”，而是建立了这样一条技术链：

```text
图像输入 -> 焊缝目标检测 -> 检测框中心提取 -> 图像中心偏差构建 -> 速度控制输出 -> cmd_vel -> 底盘执行
```

## 二、核心问题

本项目所解决的核心问题是：

**如何将焊缝目标在图像中的视觉检测结果，稳定而低成本地转化为 ROS1 机器人可执行的运动控制量。**

从当前仓库真实代码看，原有系统已经存在一套较稳定的中心偏差控制链路，但其输入更接近传统阈值法提取的“线中心”。因此，当前项目的关键技术工作不在于重写底盘控制器，而在于把新的焊缝目标检测结果，转换成旧控制器仍能直接利用的位置偏差量。

## 三、项目要点速览

### 1. 代码确认的核心事实

- 主运行入口是 `catkin_ws/src/robot_vision/launch/seam_tracking.launch`
- 新视觉前端是 `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`
- 原控制节点仍是 `catkin_ws/src/robot_vision/scripts/line_detector.py`
- 底盘接口节点是 `catkin_ws/src/base_control/script/base_control.py`
- 控制主话题链是 `/image_raw -> /seam_center -> cmd_vel`
- YOLO 检测结果通过 `geometry_msgs/Point` 传给控制器
- 原 `twist_calculate()` 控制律在集成提交中被保留
- 无检测或超时会触发零速度输出

### 2. 需要谨慎表述的内容

- 仓库不包含实际 `.pt` 权重文件
- 无法从当前仓库确认最终部署模型结构与类别定义
- 无法确认实际底盘型号与相机型号
- 无法确认实机实验是否已经完成以及具体效果

## 四、方法体系

### 1. 焊缝目标感知方法

系统使用 `yolo_seam_detector.py` 对图像进行目标检测。其工作方式是：加载 `model_path` 指定的 YOLO 权重，对每一帧图像执行推理，并在候选框中选取最优目标框。若设置了 `target_class_id`，则先进行类别过滤；否则默认选择置信度最高的框。

这一步解决的是“焊缝目标在哪里”的问题。

### 2. 目标位置表征方法

系统并不把完整检测框直接交给控制器，而是采用轻量表征方式。对最佳检测框，计算：

```text
bbox_center_x = (x1 + x2) / 2
```

并将结果编码到：

```text
Point.x = bbox_center_x
Point.y = image_width
Point.z = valid_flag
```

这一步解决的是“如何把视觉结果变成控制器能读懂的量”的问题。

### 3. 偏差构建方法

控制层把图像中心当作期望位置，把目标中心当作实际位置。若图像宽度为 `W`，则图像中心为 `W/2`，论文中可定义偏差为：

```text
e_px = bbox_center_x - W/2
```

而当前控制代码内部采用的等价控制符号为：

```text
e_ctrl = W/2 - bbox_center_x
```

这一步解决的是“目标偏离了多少”的问题。

### 4. 跟踪控制方法

当前控制仍由 `line_detector.py` 中原有的 `twist_calculate()` 完成。控制逻辑分为三段：

```text
if target near center:
    linear.x = 0.2
    angular.z = 0
else:
    angular.z = (W/2 - bbox_center_x) / W
    if abs(angular.z) < 0.2:
        linear.x = 0.2 - angular.z / 2
    else:
        linear.x = 0.1
```

这说明当前方法本质上是一种基于图像宽度归一化偏差的经验式比例控制，而不是 PID 或其他高阶控制器。

### 5. 速度协同调节方法

当前系统并不是恒速前进，而是根据偏差大小调节线速度：

- 居中时快速直行；
- 偏差较小时边转边调速；
- 偏差较大时降低到保守速度。

这一步解决的是“在纠偏时如何兼顾稳定性和前进效率”的问题。

### 6. ROS1 闭环实现方法

系统通过 ROS1 节点与话题构成闭环：

```text
camera/fake_camera -> /image_raw
/image_raw -> yolo_seam_detector
yolo_seam_detector -> /seam_center
/seam_center -> line_detector
line_detector -> cmd_vel
cmd_vel -> base_control
base_control -> chassis
chassis motion -> new image
```

这一步解决的是“如何在 ROS1/catkin 架构下把方法落地”的问题。

### 7. 异常安全处理方法

安全逻辑有三层：

1. YOLO 无检测时发布无效中心点；
2. 控制节点收到无效中心点后发布零速度；
3. 外部中心点超时后控制节点继续发布零速度；
4. 底盘协议文档还定义了上位机 1000 ms 断联后主动停机。

这一步解决的是“识别失败时如何避免盲目前进”的问题。

## 五、原理与逻辑链条

当前项目最核心的原理，可以用如下逻辑表达：

1. 视觉层负责回答“目标在图像中的横向位置是多少”；
2. 表征层负责回答“如何把该位置转成统一的接口消息”；
3. 偏差层负责回答“目标相对期望中心偏离了多少”；
4. 控制层负责回答“偏差该转换成怎样的线速度与角速度”；
5. 执行层负责回答“如何把 `cmd_vel` 变成底盘实际运动”；
6. 安全层负责回答“目标失效时系统如何停下来”。

这条逻辑链条完整、闭合、可解释，是当前项目最适合写成论文的方法主线。

## 六、系统数据流

### 1. 图像输入

图像有两种来源：

- 实机路径：`robot_camera.launch` 中的 `uvc_camera_node`
- 调试路径：`fake_camera.py`

二者都向 `/image_raw` 提供图像。

### 2. 视觉处理

`yolo_seam_detector.py` 订阅 `/image_raw`，完成推理并输出：

- `/seam_center`
- `/result_image`

### 3. 位置到偏差

`line_detector.py` 在外部中心点模式下订阅 `/seam_center`，读取：

- `Point.x` 作为目标中心
- `Point.y` 作为图像宽度
- `Point.z` 作为有效标志

### 4. 控制到执行

控制节点输出 `cmd_vel`，由 `base_control.py` 接收并编码为串口协议下发到底盘。

### 5. 反馈闭环

底盘运动改变焊缝目标在图像中的位置，新的图像再次进入检测节点，闭环由此形成。

## 七、关键工程结构

### 1. 工作区与主包

- 工作区根目录：`catkin_ws/`
- 主视觉与控制包：`catkin_ws/src/robot_vision/`
- 底盘接口包：`catkin_ws/src/base_control/`
- 模型与仿真支撑包：`catkin_ws/src/nanoomni_description/`
- Stage 仿真支撑包：`catkin_ws/src/robot_simulation/`
- YOLO 代码库：`yolo/`

### 2. 关键文件

- `catkin_ws/src/robot_vision/launch/seam_tracking.launch`
- `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`
- `catkin_ws/src/robot_vision/scripts/line_detector.py`
- `catkin_ws/src/robot_vision/launch/robot_camera.launch`
- `catkin_ws/src/robot_vision/scripts/fake_camera.py`
- `catkin_ws/src/base_control/launch/base_control.launch`
- `catkin_ws/src/base_control/script/base_control.py`
- `catkin_ws/src/nanoomni_description/urdf/nanoomni_description.gazebo.xacro`

### 3. 已保留的原控制部分

根据 git 提交 `208353c Add seam tracking integration` 的 diff 可以确认：

- 保留了 `line_detector.py` 中的 `twist_calculate()` 控制律
- 保留了旧版 HSV 路径 `line_follow.launch`
- 新增的是外部中心点输入模式与焊缝主入口

因此，当前系统属于“原控制器保留、感知前端更新、接口层适配”的方案。

## 八、已完成内容

当前仓库已经完成的内容包括：

1. 焊缝主入口 `seam_tracking.launch`
2. YOLO 检测节点 `yolo_seam_detector.py`
3. 控制器外部中心点适配
4. 主话题链 `/image_raw -> /seam_center -> cmd_vel`
5. 假相机调试路径
6. 底盘接口贯通
7. 无检测与超时停机逻辑
8. README 中的构建与启动模板

## 九、局限性

当前仓库层面存在以下限制：

1. 没有实际 `.pt` 权重文件；
2. 无法确认最终部署模型结构与类别标签；
3. 训练脚本使用外部数据集路径，训练材料不完整；
4. 缺少实验数据、截图、照片和量化指标；
5. 主链路运行依赖 `BASE_TYPE`、`CAMERA_TYPE` 等环境变量；
6. 存在 Python2 与 Python3 脚本并存的运行环境问题；
7. 仿真支撑存在，但未看到焊缝主链路的一键联通仿真入口。

## 十、待补充信息

如果后续要把论文写完整，至少还需要补充：

- 实际权重文件路径和类别定义
- 实机底盘型号
- 相机型号及其实际 `CAMERA_TYPE`
- 串口设备信息
- 实验截图与数据
- `/result_image` 识别效果图
- 跟踪成功案例与失败案例
- 停机验证记录
- 运行环境说明

## 十一、回到原环境的构建与运行

### 1. 构建

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
```

### 2. 推荐调试运行

```bash
roslaunch robot_vision seam_tracking.launch \
  run_base_control:=false \
  use_fake_camera:=true \
  fake_image_path:=$(rospack find robot_vision)/data/bingda.png \
  model_path:=<YOLO_WEIGHT_PATH>
```

### 3. 实机运行的源码级要求

根据当前源码，实机运行前还需要人工确认：

```bash
export BASE_TYPE=<待确认>
export CAMERA_TYPE=<待确认>
```

之后再运行：

```bash
roslaunch robot_vision seam_tracking.launch \
  run_base_control:=true \
  model_path:=<YOLO_WEIGHT_PATH>
```

说明：

- `<YOLO_WEIGHT_PATH>` 必须替换为实际存在的权重文件路径；
- README 与代码注释出现过 `../yolo/runs/train/exp17/weights/best.pt`，但该文件不在当前仓库中，只能视为历史示例路径。

## 十二、给新 GPT 的使用建议

如果你是新的 GPT，请优先按以下顺序理解项目：

1. 先把项目理解为“基于检测框中心表征和中心偏差控制的焊缝跟踪系统”；
2. 再理解它的工程实现是“在保留原控制器的前提下新增 YOLO 感知前端”；
3. 写作时优先展开“方法、原理、逻辑、系统闭环”；
4. 对于仓库没有给出的内容，一律写成“待人工确认”，不要自行补造实验结论。
