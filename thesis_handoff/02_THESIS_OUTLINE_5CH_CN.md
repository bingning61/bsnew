# 五章论文提纲

本文档严格服务于以下五章结构：

1. 第一章 绪论
2. 第二章 视觉感知与目标位置表征方法
3. 第三章 运动控制与焊缝跟踪方法
4. 第四章 实机验证与仿真分析
5. 第五章 总结与展望

## 第一章 绪论

### 本章可以写什么

本章应说明焊缝跟踪机器人为什么值得研究，问题来自哪里，当前方法一般如何组织，以及本项目在当前工程基础上打算解决什么具体问题。建议把问题界定为“如何利用视觉识别结果构建可用于机器人运动控制的偏差量，并在 ROS1 系统中实现稳定闭环”，而不是“如何整合两个现成系统”。

本章还应完成论文目标、研究内容与技术路线的总览性说明。技术路线部分不需要深入到具体公式，但必须提前交代：视觉部分负责目标检测与位置表征，控制部分负责偏差构建与速度生成，系统实现部分负责 ROS1 闭环与底盘执行。

### 本章由哪些项目材料支撑

- `README.md`
- `catkin_ws/src/robot_vision/launch/seam_tracking.launch`
- `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`
- `catkin_ws/src/robot_vision/scripts/line_detector.py`
- `catkin_ws/src/base_control/script/base_control.py`
- `01_THESIS_CONTEXT_MASTER_CN.md`
- `08_METHODS_PRINCIPLES_MASTER_CN.md`

### 本章还需要补什么

- 国内外研究现状对应的正式文献
- 研究现状对比表
- 焊缝跟踪应用场景的实物照片或示意图

## 第二章 视觉感知与目标位置表征方法

### 本章可以写什么

本章必须围绕视觉展开，重点讨论三个问题：一是系统如何在图像中识别焊缝目标；二是系统如何从检测框中提取出控制真正需要的位置量；三是系统如何把目标位置与图像中心建立偏差关系。

建议本章按“输入图像 -> YOLO 检测 -> 最优检测框筛选 -> 检测框中心计算 -> 图像中心参考构造 -> 偏差量输出”的逻辑组织。论文叙述上应把 `yolo_seam_detector.py` 抽象为一种视觉目标感知与位置表征方法，而不是写成“把 YOLO 接进来用了”。核心表达应强调：检测框中心是控制接口的几何表征量，图像宽度是构造参考中心所需的辅助量，有效标志是控制安全逻辑所需的状态量。

### 本章由哪些项目材料支撑

- `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`
- `catkin_ws/src/robot_vision/launch/seam_tracking.launch`
- `catkin_ws/src/robot_vision/scripts/fake_camera.py`
- `catkin_ws/src/robot_vision/launch/robot_camera.launch`
- `catkin_ws/src/robot_vision/config/astrapro.yaml`
- `catkin_ws/src/robot_vision/config/csi72.yaml`
- `README.md` 中 `/seam_center` 的接口说明

### 本章还需要补什么

- 检测效果截图
- 检测框与中心点可视化示意图
- 若有训练数据或标签定义，需要补充类别说明
- 若要写识别性能，需要补充准确率、召回率、mAP 或至少测试样例统计

## 第三章 运动控制与焊缝跟踪方法

### 本章可以写什么

本章必须围绕运动控制展开，重点说明如何从视觉位置量构建偏差，以及如何根据偏差生成角速度和线速度。建议把 `line_detector.py` 的外部中心点模式写成“偏差驱动的速度控制方法”，把 `twist_calculate()` 写成“归一化偏差控制与速度协同调节策略”，并显式指出当前代码不是 PID，而是一种简单、直接、易于实现的比例式偏差调节方法。

本章还应说明闭环逻辑与安全逻辑。闭环逻辑是“图像变化引起检测中心变化，检测中心变化引起 `cmd_vel` 变化，`cmd_vel` 变化又反过来改变下一帧图像中的目标位置”。安全逻辑则包括无效检测时的零速度输出、外部中心消息超时后的看门狗停止、以及底盘接口文档中的下位机超时停机机制。

### 本章由哪些项目材料支撑

- `catkin_ws/src/robot_vision/scripts/line_detector.py`
- `catkin_ws/src/robot_vision/config/line_hsv.cfg`
- `catkin_ws/src/base_control/script/base_control.py`
- `catkin_ws/src/base_control/README.md`
- `catkin_ws/src/base_control/launch/base_control.launch`
- `08_METHODS_PRINCIPLES_MASTER_CN.md`
- `09_SYSTEM_LOGIC_AND_DATAFLOW_CN.md`

### 本章还需要补什么

- `cmd_vel` 曲线或回显截图
- 偏差变化与速度变化的实测样例
- 实机跟踪过程中的转向现象描述
- 如需更严谨，可补充不同偏差下的线速度/角速度统计图

## 第四章 实机验证与仿真分析

### 本章可以写什么

本章标题保持“实机验证与仿真分析”，但正文应当实事求是地区分“当前仓库已经提供的验证支撑”与“仍待补充的实验材料”。现有仓库已经能支撑写系统实现路径、节点协同关系、启动方式、调试路径以及通用机器人模型/仿真资源；但不能直接证明已经完成了焊缝专用仿真和完整实机实验。

建议本章分成三个部分来写。第一部分写系统实现路径，说明 `seam_tracking.launch` 如何组织图像源、YOLO 节点、控制节点与可选底盘接口。第二部分写实机验证思路，说明应如何组织识别效果测试、偏差响应测试、无检测停止测试和整车跟踪测试。第三部分写仿真分析，明确指出仓库中存在 `nanoomni_description`、`robot_simulation` 等模型与仿真支撑资源，但这些资源当前主要面向通用移动机器人仿真，不是焊缝跟踪专用仿真场景。

### 本章由哪些项目材料支撑

- `catkin_ws/src/robot_vision/launch/seam_tracking.launch`
- `catkin_ws/src/robot_vision/scripts/fake_camera.py`
- `catkin_ws/src/robot_vision/data/bingda.png`
- `原视频.mp4`
- `识别视频.mp4`
- `yolo/frames/`
- `catkin_ws/src/nanoomni_description/README.md`
- `catkin_ws/src/nanoomni_description/launch/*.launch`
- `catkin_ws/src/nanoomni_description/urdf/*.xacro`
- `catkin_ws/src/robot_simulation/README.md`
- `catkin_ws/src/robot_simulation/launch/*.launch`

### 本章还需要补什么

- 实机运行照片
- 节点图或 `rqt_graph` 截图
- `rostopic echo /seam_center`、`/cmd_vel` 截图
- 识别结果截图
- 机器人跟踪过程截图
- 实验数据表
- 如果要把仿真写实，需补充焊缝场景、仿真相机画面与联调记录

## 第五章 总结与展望

### 本章可以写什么

本章应当总结项目已经完成的方法体系，而不是简单总结“代码完成了哪些文件修改”。建议从“视觉感知与位置表征”“偏差驱动控制”“ROS1 闭环实现”“实机与仿真支撑情况”四个方面回顾已完成工作，然后诚实说明当前方案的局限性，包括目标表征仍较粗、控制策略较简单、实验数据不足、仿真环境不专用等。

展望部分则可以从目标位置表征更精细化、控制策略更平滑化、实验评价更定量化、焊缝专用仿真场景补充、硬件参数标定完善等方向展开。

### 本章由哪些项目材料支撑

- `01_THESIS_CONTEXT_MASTER_CN.md`
- `08_METHODS_PRINCIPLES_MASTER_CN.md`
- `10_EVIDENCE_MAP_CN.md`
- `14_MISSING_INFO_CHECKLIST_CN.md`

### 本章还需要补什么

- 论文最终实验结论
- 论文最终图表编号
- 与答辩版本一致的总结口径

## 提纲使用建议

如果后续要把这份提纲交给新的 GPT，建议同时提供 `12_ALL_IN_ONE_GPT_HANDOFF_CN.md` 与 `10_EVIDENCE_MAP_CN.md`。前者负责给出整体逻辑，后者负责限制新 GPT 不要虚构节点、算法、硬件型号和实验结果。
