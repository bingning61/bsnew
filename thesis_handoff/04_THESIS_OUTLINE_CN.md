# 本科毕业论文提纲

## 一、提纲使用原则

本提纲不是通用模板，而是围绕当前仓库已经存在的真实工程链路组织出来的论文结构。写作时应坚持两个原则：

1. 以“方法、原理、逻辑、系统实现”为主线，而不是把正文写成“两个系统拼接说明”。
2. 所有能落到源码、节点、`launch`、话题和提交历史的内容，尽量写成明确论述；所有缺少证据的内容，都应标注待补。

## 二、摘要

### 本项目可以写什么

摘要应概括以下内容：

- 面向焊缝跟踪任务提出了什么方法；
- 方法的核心链条是什么；
- 在 ROS1 环境中实现了怎样的系统；
- 最终形成了怎样的闭环控制机制；
- 已完成哪些系统实现工作；
- 还有哪些实验部分需补充。

摘要的核心表达建议是：

本课题围绕焊缝目标视觉跟踪问题，提出了一种基于 YOLO 目标检测与中心偏差控制的移动机器人实现方法。该方法以相机图像为输入，利用目标检测结果提取焊缝目标检测框中心，以图像中心为参考构造横向偏差，并复用原有中心偏差控制器生成 `cmd_vel` 指令，最终在 ROS1 平台上实现感知到执行的闭环跟踪。

### 代码/配置/目录中哪些材料支撑这一部分

- `README.md`
- `robot_vision/launch/seam_tracking.launch`
- `robot_vision/scripts/yolo_seam_detector.py`
- `robot_vision/scripts/line_detector.py`
- `base_control/script/base_control.py`

### 哪些地方还需要后续补实验截图、数据或照片

- 实际检测准确率或示例结果
- 实机跟踪效果
- 安全停机验证

## 三、第一章 绪论

### 本项目可以写什么

第一章建议分为以下部分：

1. 焊缝自动跟踪与移动机器人视觉控制的应用背景；
2. 传统阈值法在复杂焊缝目标场景中的局限；
3. 目标检测在焊缝视觉感知中的价值；
4. 本课题面向的问题：如何把视觉检测结果稳定转化为移动机器人控制量；
5. 本文主要研究内容与章节安排。

在这一章中，不必把工程实现细节写太深，但必须明确论文的问题意识：不是研究抽象的“系统融合”，而是研究“焊缝目标位置到机器人控制量的构造方法”。

### 代码/配置/目录中哪些材料支撑这一章

- `AGENTS.md` 中对项目目标的约束说明
- `README.md` 中对最终链路的概括
- `robot_vision/scripts/line_detector.py` 中旧控制器的存在
- `robot_vision/scripts/yolo_seam_detector.py` 中新感知前端的存在

### 哪些地方还需要后续补实验截图、数据或照片

- 绪论通常需要文献综述，这部分仓库不提供
- 需要后续自行补充国内外研究现状与参考文献

## 四、第二章 相关技术与系统总体设计

### 本项目可以写什么

本章建议包括以下内容：

1. ROS1/catkin 工程组织方式；
2. 图像获取、目标检测、消息传输、底盘控制等关键技术基础；
3. 系统总体架构设计；
4. 各功能模块之间的接口关系；
5. 整体数据流与闭环流程。

可以把系统总体架构拆分为：

- 感知层：图像采集与目标检测
- 表征与控制层：中心点编码、偏差构造、速度控制
- 执行层：底盘通信接口
- 支撑层：模型描述、仿真与导航配套

### 代码/配置/目录中哪些材料支撑这一章

- `catkin_ws/src/robot_vision/package.xml`
- `catkin_ws/src/base_control/package.xml`
- `catkin_ws/src/nanoomni_description/package.xml`
- `catkin_ws/src/robot_simulation/package.xml`
- `catkin_ws/src/robot_vision/launch/seam_tracking.launch`
- `catkin_ws/src/base_control/launch/base_control.launch`
- `catkin_ws/src/nanoomni_description/launch/*.launch`
- `catkin_ws/src/robot_simulation/launch/*.launch`

### 哪些地方还需要后续补实验截图、数据或照片

- 系统总体框图建议后续人工绘制
- 节点关系图、话题关系图建议后续用 `rqt_graph` 截图补充

## 五、第三章 焊缝感知与位置表征方法

### 本项目可以写什么

本章是论文方法部分的重点之一，建议按以下结构写：

1. 焊缝目标感知需求分析；
2. 基于 YOLO 的目标检测方法；
3. 多候选框下的目标选取策略；
4. 检测框中心提取方法；
5. 基于 `geometry_msgs/Point` 的位置表征接口设计；
6. 图像中心参照下的偏差构造方法。

本章要强调：

- 当前项目并没有做复杂焊缝曲线拟合；
- 当前方法的关键是把检测框中心作为控制代理量；
- 当前方法用最小化的消息接口降低了控制链路改造量。

### 代码/配置/目录中哪些材料支撑这一章

- `robot_vision/scripts/yolo_seam_detector.py`
- `robot_vision/launch/seam_tracking.launch`
- `yolo/ultralytics/`
- `yolo/train.py`
- `yolo/Detect.py`
- `yolo/val.py`

### 哪些地方还需要后续补实验截图、数据或照片

- 识别结果截图
- 不同场景下的检测样例
- 类别定义与训练数据说明
- 检测性能指标

## 六、第四章 焊缝跟踪控制方法

### 本项目可以写什么

本章是另一处重点，应围绕原控制器的复用与偏差到速度的映射展开。建议包括：

1. 控制目标与控制输入输出定义；
2. 图像中心偏差的控制意义；
3. 原有 `twist_calculate()` 控制律分析；
4. 角速度生成方法；
5. 线速度协同调节方法；
6. 异常情况下的安全停机机制；
7. 控制器复用策略及其合理性。

写作时要明确指出：本项目的创新重点不在新控制器设计，而在于焊缝视觉位置量到既有偏差控制器输入的转换。

### 代码/配置/目录中哪些材料支撑这一章

- `robot_vision/scripts/line_detector.py`
- git 提交 `208353c Add seam tracking integration` 对 `line_detector.py` 的 diff
- `base_control/script/base_control.py`
- `base_control/README.md`

### 哪些地方还需要后续补实验截图、数据或照片

- 偏差与速度关系曲线图
- 控制参数调节过程说明
- 实机纠偏视频或轨迹截图

## 七、第五章 系统实现与实验验证

### 本项目可以写什么

本章应把工程实现和实验设计结合起来，建议分为：

1. ROS1 工程实现与节点部署；
2. 主运行入口与启动流程；
3. 假相机功能验证方案；
4. 实机闭环跟踪验证方案；
5. 异常停机验证方案；
6. 结果分析与局限性讨论。

实验设计建议采用三类：

1. 软件功能验证：使用 `fake_camera.py` 和 `bingda.png` 验证图像输入、检测输出与控制链路是否贯通。
2. 视觉检测验证：记录 `/result_image`，展示检测框、中心点与图像中心线是否正确。
3. 实机跟踪验证：在实际底盘上运行主链路，观察机器人是否能够依据视觉偏差完成姿态修正与前进控制。

如果后续条件允许，还可以补做：

4. 无检测停机验证；
5. 超时停机验证；
6. 不同场景光照下的鲁棒性对比。

### 代码/配置/目录中哪些材料支撑这一章

- `robot_vision/launch/seam_tracking.launch`
- `robot_vision/scripts/fake_camera.py`
- `robot_vision/data/bingda.png`
- `robot_vision/scripts/yolo_seam_detector.py`
- `robot_vision/scripts/line_detector.py`
- `base_control/launch/base_control.launch`
- `base_control/script/base_control.py`
- `nanoomni_description/urdf/nanoomni_description.gazebo.xacro`

### 哪些地方还需要后续补实验截图、数据或照片

- `roslaunch` 启动终端截图
- `rqt_graph` 或话题关系图截图
- `/result_image` 识别效果截图
- 实机运行照片
- 小车跟踪视频截图
- 停机验证截图或日志
- 如果使用仿真，还需补 Gazebo 或 RViz 截图

## 八、第六章 总结与展望

### 本项目可以写什么

本章可以总结为：

1. 完成了基于 YOLO 与中心偏差控制的焊缝跟踪系统设计与实现；
2. 构建了从图像输入到 `cmd_vel` 输出的 ROS1 闭环链路；
3. 保留了原有控制器，仅对输入接口进行了兼容式扩展；
4. 当前系统仍存在实验数据、模型权重和环境说明不完整的问题；
5. 后续可向更丰富的位置表征、更稳健的控制策略和更完整的仿真验证扩展。

### 代码/配置/目录中哪些材料支撑这一章

- 全部主链路文件
- git 集成提交记录
- `06_EVIDENCE_MAP_CN.md`
- `10_MISSING_INFO_CHECKLIST_CN.md`

### 哪些地方还需要后续补实验截图、数据或照片

- 总结章节通常不需要额外截图，但需要有完整实验结论作支撑

## 九、附加建议：章节材料调用顺序

若后续要让新的 GPT 分章写作，建议按以下顺序投喂材料：

1. 写第二章前：发 `03_THESIS_CONTEXT_MASTER_CN.md` + `02_SYSTEM_LOGIC_AND_DATAFLOW_CN.md`
2. 写第三章前：发 `01_METHODS_PRINCIPLES_MASTER_CN.md` 中 4.1 至 4.3
3. 写第四章前：发 `01_METHODS_PRINCIPLES_MASTER_CN.md` 中 4.4 至 4.7
4. 写第五章前：发 `02_SYSTEM_LOGIC_AND_DATAFLOW_CN.md` + `10_MISSING_INFO_CHECKLIST_CN.md`
5. 写全文终稿前：发 `06_EVIDENCE_MAP_CN.md` 做事实核对

## 十、本提纲的边界

本提纲已经尽量贴合当前真实项目，但以下部分仍需人工补足：

1. 文献综述与相关研究现状；
2. 实机实验结果与性能数据；
3. 实验截图、照片、图表；
4. 实际权重文件与训练数据说明；
5. 最终论文题目、摘要字数、学校格式要求。
