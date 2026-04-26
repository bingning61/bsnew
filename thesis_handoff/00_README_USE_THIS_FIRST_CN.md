# 本科毕业论文资料交接包使用说明

本目录用于把当前 `bsnew/` 仓库中的真实工程材料，重构为适合本科毕业论文写作与后续 AI 协作的“技术表达体系”。本资料包的主线不是“两个系统怎么拼接”，而是“焊缝目标如何被感知、如何被表征、如何转化为偏差、如何生成运动控制、如何在 ROS1 中形成闭环、如何组织成五章论文”。

## 一、先看哪几个文件

本轮交接包的**主文件集**是以下 15 个文件，请优先使用这些文件：

1. `00_README_USE_THIS_FIRST_CN.md`
2. `01_THESIS_CONTEXT_MASTER_CN.md`
3. `02_THESIS_OUTLINE_5CH_CN.md`
4. `03_CHAPTER_1_INTRO_CN.md`
5. `04_CHAPTER_2_VISION_CN.md`
6. `05_CHAPTER_3_MOTION_CONTROL_CN.md`
7. `06_CHAPTER_4_EXPERIMENTS_CN.md`
8. `07_CHAPTER_5_CONCLUSION_CN.md`
9. `08_METHODS_PRINCIPLES_MASTER_CN.md`
10. `09_SYSTEM_LOGIC_AND_DATAFLOW_CN.md`
11. `10_EVIDENCE_MAP_CN.md`
12. `11_NEW_CHAT_BOOTSTRAP_PROMPT_CN.md`
13. `12_ALL_IN_ONE_GPT_HANDOFF_CN.md`
14. `13_STRUCTURED_FACTS.json`
15. `14_MISSING_INFO_CHECKLIST_CN.md`

当前目录下如果还存在 `01_METHODS_PRINCIPLES_MASTER_CN.md`、`02_SYSTEM_LOGIC_AND_DATAFLOW_CN.md`、`03_THESIS_CONTEXT_MASTER_CN.md` 这类旧编号文件，请把它们视为历史遗留版本，不要优先发送给新的 GPT。

## 二、推荐发送顺序

如果你只发一个文件，优先发送：

- `12_ALL_IN_ONE_GPT_HANDOFF_CN.md`

如果你准备分三步发，建议顺序是：

1. `12_ALL_IN_ONE_GPT_HANDOFF_CN.md`
2. `08_METHODS_PRINCIPLES_MASTER_CN.md`
3. `10_EVIDENCE_MAP_CN.md`

如果你希望新的 GPT 稳定进入论文写作状态，建议顺序是：

1. `11_NEW_CHAT_BOOTSTRAP_PROMPT_CN.md`
2. `12_ALL_IN_ONE_GPT_HANDOFF_CN.md`
3. `01_THESIS_CONTEXT_MASTER_CN.md`
4. `08_METHODS_PRINCIPLES_MASTER_CN.md`
5. `09_SYSTEM_LOGIC_AND_DATAFLOW_CN.md`
6. `10_EVIDENCE_MAP_CN.md`
7. `02_THESIS_OUTLINE_5CH_CN.md`
8. `03_CHAPTER_1_INTRO_CN.md`
9. `04_CHAPTER_2_VISION_CN.md`
10. `05_CHAPTER_3_MOTION_CONTROL_CN.md`
11. `06_CHAPTER_4_EXPERIMENTS_CN.md`
12. `07_CHAPTER_5_CONCLUSION_CN.md`
13. `14_MISSING_INFO_CHECKLIST_CN.md`
14. `13_STRUCTURED_FACTS.json`

## 三、每个文件怎么用

| 文件名 | 用途 |
| --- | --- |
| `00_README_USE_THIS_FIRST_CN.md` | 使用说明、发送顺序、事实等级说明 |
| `01_THESIS_CONTEXT_MASTER_CN.md` | 高自包含主上下文，适合让新 GPT 快速理解项目 |
| `02_THESIS_OUTLINE_5CH_CN.md` | 严格对应五章结构的论文提纲 |
| `03_CHAPTER_1_INTRO_CN.md` | 绪论写作草稿与研究现状写法建议 |
| `04_CHAPTER_2_VISION_CN.md` | 第二章视觉感知与目标位置表征材料 |
| `05_CHAPTER_3_MOTION_CONTROL_CN.md` | 第三章运动控制与焊缝跟踪材料 |
| `06_CHAPTER_4_EXPERIMENTS_CN.md` | 第四章实机验证与仿真分析材料 |
| `07_CHAPTER_5_CONCLUSION_CN.md` | 第五章总结与展望材料 |
| `08_METHODS_PRINCIPLES_MASTER_CN.md` | 方法、原理、思路、逻辑主文档 |
| `09_SYSTEM_LOGIC_AND_DATAFLOW_CN.md` | 节点关系、话题关系、参数关系与完整数据流 |
| `10_EVIDENCE_MAP_CN.md` | 事实与证据映射，避免虚构 |
| `11_NEW_CHAT_BOOTSTRAP_PROMPT_CN.md` | 可直接复制到新对话框的启动提示词 |
| `12_ALL_IN_ONE_GPT_HANDOFF_CN.md` | 单文件总交接包，最适合一次性发送 |
| `13_STRUCTURED_FACTS.json` | 结构化事实库，适合程序读取或检索式引用 |
| `14_MISSING_INFO_CHECKLIST_CN.md` | 论文最终成稿前仍需补充的材料清单 |

## 四、事实等级如何理解

本资料包中的判断分为三类：

### 1. 代码确认事实

指能够直接从当前仓库源码、目录、`launch`、`package.xml`、`CMakeLists.txt`、脚本实现、配置文件中读出的内容。例如：

- 主运行入口为 `catkin_ws/src/robot_vision/launch/seam_tracking.launch`
- `yolo_seam_detector.py` 把检测结果编码为 `geometry_msgs/Point`
- `line_detector.py` 在外部中心点模式下继续调用 `twist_calculate()`
- `base_control.py` 订阅 `cmd_vel` 并把速度量打包为串口协议发送到底盘

### 2. 结构推断

指根据多个文件之间的关系、README 文字、launch 组织方式形成的较强推断，但仓库没有提供完整运行记录或实验报告。例如：

- 当前项目采用“检测框中心替代旧线中心”的兼容式感知到控制方案
- `nanoomni_description` 更适合归入模型与仿真支撑，而不是主焊缝跟踪控制包
- `robot_navigation`、雷达驱动包属于通用移动机器人能力，不是当前焊缝跟踪主链路

### 3. 待人工确认

指仓库无法给出最终答案，必须由项目持有人、实机环境或原始实验资料补充的信息。例如：

- 实际使用的是哪一套 `.pt` 权重文件
- 焊缝目标类别名称、类别编号与训练标签含义
- 实机底盘型号、相机型号、`BASE_TYPE`、`CAMERA_TYPE` 的真实取值
- 识别精度、跟踪成功率、实验截图、ROS 运行截图、硬件照片

## 五、当前可以稳定使用的核心结论

以下结论可作为论文表达的稳定基础：

1. 当前项目的主数据流已经明确为“图像输入 -> YOLO 检测 -> 检测框中心提取 -> 图像中心偏差构建 -> `cmd_vel` 输出 -> 底盘执行”。
2. `line_detector.py` 中原有的速度控制函数 `twist_calculate()` 仍然保留在当前主链路中，因此控制核心并未被整体重写。
3. 新的视觉前端脚本是 `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`，新的主入口是 `catkin_ws/src/robot_vision/launch/seam_tracking.launch`。
4. 当前系统使用 `geometry_msgs/Point` 传递最小视觉几何量：`x` 表示目标中心横坐标，`y` 表示图像宽度，`z` 表示检测有效标志。
5. 无有效检测或外部中心消息超时后，控制节点会主动发布零速度；底盘接口文档还给出了下位机超时停机机制。
6. `nanoomni_description` 与 `robot_simulation` 为第四章提供了模型与仿真分析素材，但它们没有直接出现在 `seam_tracking.launch` 的主运行链路中。

## 六、必须谨慎处理的不确定点

以下内容不能直接当作既定事实写入论文正文：

1. 仓库当前没有实际 `.pt` 权重文件，README 与脚本注释中的 `../yolo/runs/train/exp17/weights/best.pt` 只能视为历史示例路径。
2. `yolo/` 目录包含大量通用 Ultralytics 源码与示例，不能直接证明部署时采用了哪一种具体改进模型结构。
3. `yolo/train.py` 的数据集路径是外部 Windows 路径，不能作为当前仓库自带训练数据证据。
4. 当前主链路混用了 `python3` 的 YOLO 节点和 `python` 风格的控制/底盘节点，解释器与依赖共存情况需要回到 ROS1 环境后人工确认。
5. 项目是否完成了实机焊缝跟踪实验、实验效果如何、视频文件是否对应论文实验，仓库没有提供可直接引用的定量证据。
6. `nanoomni_description` 证明仓库存在 NanoOmni 相关模型与 Gazebo 插件，但不能据此直接认定实机平台就是 NanoOmni。

## 七、论文叙事边界

建议优先使用如下表述：

- 提出了一种基于目标检测中心表征的焊缝跟踪方法
- 建立了目标中心与图像中心之间的偏差构造关系
- 设计了基于归一化偏差的角速度与线速度协同调节策略
- 采用 ROS1 话题耦合方式实现感知到控制的闭环
- 在工程实现中复用了已有的 `cmd_vel` 底盘控制链路

不建议把论文主体写成：

- 把两个系统简单拼接
- 只是把 YOLO 接到了旧控制器上
- 只是调用已有代码

这些说法最多只能出现在工程实现背景中，不能成为第二章、第三章的方法主线。

## 八、给新 GPT 的一句话提示

把当前项目理解为“基于 YOLO 视觉感知、检测框中心位置表征与原有偏差控制律的 ROS1 焊缝跟踪机器人系统”，而不是“两个现成系统的简单整合说明”。
