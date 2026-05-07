# 代码驱动的毕业论文写作交接材料

## 1. 使用说明

本材料用于复制到新的 GPT 窗口，作为后续撰写本科毕业论文的代码事实交接资料。材料内容只依据当前 `bsnew/` 仓库内可以验证的代码、配置、README、报告、注释、权重文件清单和媒体文件清单整理，不应在论文写作中额外编造数据集、实验指标、硬件型号、传感器型号、训练过程或对比实验。

后续写论文时，应把本项目表述为围绕焊缝目标视觉感知、位置表征、中心偏差构建、速度控制输出和 ROS1 闭环执行形成的完整技术方案。不要把正文写成“两个系统拼接”或“模块简单融合”。如果某项内容仅由文档提及而代码中没有实现，应标注“文档提及，代码中未确认实现”；如果某项内容来自代码调用关系而非显式注释，应标注“基于代码调用关系的推断”。

后续任何 AI 写论文时，都应优先服从这份代码事实交接材料，而不是沿用旧阶段草稿中的过时技术路线。凡是与当前主链路不一致的旧说法，例如将系统写成 Stanley、MPC、滑模、UWB、多传感器融合、语义分割、三维定位或全局路径规划主导的方案，都应视为过时内容并主动纠正。

参考论文 `/home/bn/球罐检测机器人定位导航及控制技术研究_李杰.pdf` 已读取摘要、英文摘要和目录，仅读取其论文组织方式和正式学术表达习惯。该论文中的研究对象、机器人结构、Mask R-CNN、PID、滑模控制、UWB、卡尔曼滤波、路径规划、实验平台和现场测试等内容，不能作为当前项目已经实现的事实写入论文，除非当前仓库代码或用户后续材料能提供独立证据。

## 2. 项目总体定位

当前代码项目实际实现的是一个 ROS1/catkin 环境下的焊缝跟踪机器人软件链路：系统以相机或测试视频/图片发布的图像作为输入，通过 YOLOv5 推理得到焊缝目标检测框，提取检测框横向中心与图像宽度，并将其发布为控制器可消费的中心位置消息；随后控制逻辑以图像中心为参考，根据目标中心偏差生成 `geometry_msgs/Twist` 速度指令，最终可由底盘串口桥或 Gazebo 平面运动插件执行。依据：`README.md:5-16`、`README.md:46-73`、`catkin_ws/src/robot_vision/launch/seam_tracking.launch:42-83`、`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:284-325`、`catkin_ws/src/robot_vision/scripts/line_detector.py:82-99`、`catkin_ws/src/robot_vision/scripts/line_detector.py:165-202`。

为了避免后续论文写作继续受旧材料干扰，可将当前项目真实主链路统一概括为：

图像输入
→ YOLOv5 检测焊缝目标框
→ 提取检测框横向中心
→ 结合图像宽度构造位置表征
→ 与图像中心形成横向偏差
→ 控制节点输出 Twist 速度指令
→ 底盘接口或 Gazebo 执行
→ 无检测或超时时输出零速度

用户已确认实体机器人为冰达机器人 NanoOmni 麦克纳姆轮全向移动底盘。本地参考资料 `二代控制器BD_BASE_硬件资料及代码-Omni/` 已加入 `.gitignore`，不应提交到 Git；其中协议文件和 NanoOmni 控制板程序可支撑论文写“底盘执行层支持 `v_x`、`v_y`、`\omega_z` 三轴速度输入，并在控制板侧完成四轮目标转速分配、编码器测速和电机 PID 闭环”。代码层面可确认底盘桥 `base_control.py` 支持 `Twist.linear.x`、`Twist.linear.y` 和 `Twist.angular.z` 三轴速度接口，并且底盘协议文档明确包含 X 轴速度、Y 轴速度和 Z 轴角速度字段。底盘几何和执行层参数可先按本地控制板资料写入建模说明，包括轮距 0.168 m、轴距 0.145 m、轮径 0.064 m、减速比 21.3、编码器线数 11、控制周期 25 ms 和电机 PID 参数 0.2/0.2/0.25，但正文必须写成“根据控制板资料，本文建模暂按该参数取值”，不得写成实测尺寸。当前焊缝跟踪上层控制器仍采用前向速度加偏航角速度的基础跟踪方式，即输出 `linear.x` 和 `angular.z`，并将 `linear.y` 保持为 0；因此论文可以写“麦克纳姆轮全向底盘速度接口”和“底盘执行层轮速分配与电机闭环”，但不能写成上层焊缝跟踪控制已经利用 `v_y` 横向平移进行焊缝纠偏，也不能写成上层控制读取里程计闭环。依据：用户 2026-05-06 和 2026-05-07 确认、`catkin_ws/src/base_control/script/base_control.py:217-246`、`catkin_ws/src/base_control/README.md:43-48`、`catkin_ws/src/base_control/README.md:96-103`、`catkin_ws/src/robot_vision/scripts/line_detector.py:169-202`、`二代控制器BD_BASE_硬件资料及代码-Omni/底盘-ROS通讯协议.txt:32-37`、`二代控制器BD_BASE_硬件资料及代码-Omni/NanoOmni_407_211217.zip 内 NanoOmni_407/Src/app/Communication.c:262-280`、`二代控制器BD_BASE_硬件资料及代码-Omni/NanoOmni_407_211217.zip 内 NanoOmni_407/Src/app/Kinematics.c:87-101`、`二代控制器BD_BASE_硬件资料及代码-Omni/NanoOmni_407_211217.zip 内 NanoOmni_407/Src/app/Motor.c:74-139`。

代码中明确出现“seam tracking”“seam detector”“焊缝检测/跟踪”相关命名和说明，因此可以将论文任务定位为焊缝目标跟踪。代码没有明确说明具体工业生产场景、焊接工艺、焊缝材料、工件类型或实际部署工位，这些内容不能直接写成已完成事实。依据：`README.md:1-3`、`catkin_ws/src/robot_vision/launch/seam_tracking.launch:16-31`、`catkin_ws/src/nanoomni_description/worlds/seam_world_curve.world:74-178`。

在第一章写作中，研究背景与国内外研究现状的文献写法应明确区分。研究背景更侧重支撑课题意义和应用场景成立，可以采用概括式、总结式引用；国内外研究现状则应写成真正的文献综述，说明研究对象、采用方法、解决问题、特点和局限，而不是只堆技术名和编号。

允许在绪论中引用综述、学位论文或主论文对其他研究成果的总结、归纳和比较，但如果正文依据的是这篇主论文的总结性表述，编号应归属于这篇主论文本身，而不是它文内再引用的原始论文。写法上应诚实表达为“某综述指出”“某学位论文总结了”“某文献归纳认为”等，不得写成像已经逐篇查阅其全部引用链中的原始论文。

## 3. 代码证据总览

| 证据类别 | 文件路径 | 主要内容 | 可支持的论文表述 | 可信等级 |
| --- | --- | --- | --- | --- |
| README | `README.md:1-73` | 项目定位、主运行链路、话题语义、中心点计算 | 系统以 `/image_raw` 为输入，经 YOLOv5 得到 `/seam_center`，再由控制逻辑输出 `/cmd_vel` | 文档提及，且代码已实现 |
| README | `README.md:75-231` | Ubuntu 18.04/ROS Melodic 构建、运行和调试命令 | 可写入论文附录或系统实现章节的运行流程 | 文档提及 |
| 源代码 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:13-53` | YOLO 检测节点参数、话题发布订阅、模型加载入口 | 视觉前端在 ROS 图像话题与检测模型之间建立适配 | 代码已实现 |
| 源代码 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:91-138` | YOLOv5 模型加载、`attempt_load`、`letterbox`、NMS、设备选择 | 系统通过本地 YOLOv5 代码进行推理准备 | 代码已实现 |
| 源代码 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:235-268` | 图像预处理、归一化、模型推理、NMS、最高置信度框选择 | 可描述为基于检测框的目标位置提取方法 | 代码已实现 |
| 源代码 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:284-331` | 图像回调、中心点发布、无检测处理、结果图绘制 | 可描述检测输出、调试可视化和无目标安全标志 | 代码已实现 |
| 源代码 | `catkin_ws/src/robot_vision/scripts/line_detector.py:39-60` | 外部中心点模式与旧 HSV 模式分支 | 可说明同一控制节点支持外部目标中心输入 | 代码已实现 |
| 源代码 | `catkin_ws/src/robot_vision/scripts/line_detector.py:82-99` | 有效标志检查、超时看门狗、零速度停止 | 可说明目标丢失或输入中断时的安全停止逻辑 | 代码已实现 |
| 源代码 | `catkin_ws/src/robot_vision/scripts/line_detector.py:101-135` | 旧 HSV 分割、形态学闭运算、扫描行求中心 | 可作为传统视觉备用路径说明 | 代码已实现 |
| 源代码 | `catkin_ws/src/robot_vision/scripts/line_detector.py:154-171` | 根据目标中心与参考中心生成线速度和角速度 | 可写入中心偏差控制方法 | 代码已实现 |
| Launch | `catkin_ws/src/robot_vision/launch/seam_tracking.launch:1-83` | 主运行入口：图像源、YOLO、控制节点、可选底盘桥 | 可作为系统总体方案和数据流依据 | 配置存在 |
| Launch | `catkin_ws/src/robot_vision/launch/gazebo_seam_tracking.launch:1-78` | Gazebo 环境、YOLO 和控制节点的仿真入口 | 可作为仿真支撑入口，需运行验证 | 配置存在 |
| 配置 | `catkin_ws/src/robot_vision/config/line_hsv.cfg:1-14` | HSV 阈值动态重配置参数 | 可说明旧视觉路径支持 HSV 参数调节 | 配置存在 |
| 配置 | `catkin_ws/src/robot_vision/config/astrapro.yaml:1-20`、`catkin_ws/src/robot_vision/config/csi72.yaml:1-20` | 相机内参文件 | 可说明仓库提供相机标定配置，但实际相机型号需确认 | 配置存在 |
| 源代码 | `catkin_ws/src/robot_vision/scripts/fake_camera.py:17-90` | 静态图像或视频循环发布 `/image_raw` | 可写入调试输入和视频测试流程 | 代码已实现 |
| 源代码 | `catkin_ws/src/base_control/script/base_control.py:145-166` | 串口打开、订阅 `cmd_vel` 或 Ackermann 指令 | 可说明底盘接口以 ROS 速度话题为输入 | 代码已实现 |
| 源代码 | `catkin_ws/src/base_control/script/base_control.py:217-246` | `cmd_vel` 打包为底盘串口速度协议 | 可说明速度命令执行接口 | 代码已实现 |
| 源代码 | `catkin_ws/src/base_control/script/base_control.py:428-477` | 里程计积分和 TF 发布 | 可说明底盘桥包含反馈发布，但主焊缝控制未消费 odom | 代码已实现 |
| README | `catkin_ws/src/base_control/README.md:7-37` | 串口通信协议、CRC、超时停机说明 | 可说明底盘协议文档中存在 1000 ms 无指令停机规则 | 文档提及，代码中未确认下位机行为 |
| 本地资料 | `二代控制器BD_BASE_硬件资料及代码-Omni/底盘-ROS通讯协议.txt:32-37` | 速度控制功能码 `0x01`，数据为 X/Y/Z 速度各乘 1000 | 可说明上位机到底盘控制板的三轴速度协议 | 本地资料确认，不提交 Git |
| 本地资料 | `二代控制器BD_BASE_硬件资料及代码-Omni/NanoOmni_407_211217.zip 内 NanoOmni_407/Inc/app/Config.h:8`、`:33-35`、`:60-70` | NanoOmni 控制周期、电机 PID、轮距、轴距、轮径、减速比、编码器和最大速度参数 | 可说明底盘执行层参数来源 | 本地资料确认，需实车一致性复核 |
| 本地资料 | `二代控制器BD_BASE_硬件资料及代码-Omni/NanoOmni_407_211217.zip 内 NanoOmni_407/Src/app/Communication.c:262-280` | 控制板解析 `0x01` 速度指令并调用运动学分配 | 可说明底盘控制板接收并解析三轴速度 | 本地资料确认 |
| 本地资料 | `二代控制器BD_BASE_硬件资料及代码-Omni/NanoOmni_407_211217.zip 内 NanoOmni_407/Src/app/Kinematics.c:87-133` | 三轴速度到四轮目标转速、四轮当前转速到车体速度的计算 | 可说明麦克纳姆轮轮速分配由底盘执行层完成 | 本地资料确认 |
| 本地资料 | `二代控制器BD_BASE_硬件资料及代码-Omni/NanoOmni_407_211217.zip 内 NanoOmni_407/Src/app/Motor.c:74-139`、`二代控制器BD_BASE_硬件资料及代码-Omni/NanoOmni_407_211217.zip 内 NanoOmni_407/Src/bsp/bsp_encoder.c:10-79`、`二代控制器BD_BASE_硬件资料及代码-Omni/NanoOmni_407_211217.zip 内 NanoOmni_407/Src/mainloop.c:387-405` | 编码器测速、电机 PID、PWM 执行和周期性控制循环 | 可说明底盘执行层存在电机速度闭环 | 本地资料确认，未做实车测试 |
| 源代码/URDF | `catkin_ws/src/nanoomni_description/urdf/nanoomni_description.gazebo.xacro:26-33` | Gazebo `cmd_vel` 平面运动插件 | 可说明仿真中可由 `cmd_vel` 驱动模型 | 代码已实现 |
| 源代码/URDF | `catkin_ws/src/nanoomni_description/urdf/nanoomni_description.gazebo.xacro:107-136` | Gazebo RGB 相机插件发布 `image_raw` | 可说明仿真视觉输入支撑 | 代码已实现 |
| 配置/World | `catkin_ws/src/nanoomni_description/worlds/seam_world_curve.world:74-178` | 曲线焊缝视觉模型 | 可说明仓库存在焊缝样式仿真场景文件 | 配置存在 |
| 配置/World | `catkin_ws/src/nanoomni_description/worlds/seam_world_texture.world:61-104` | 纹理表面和焊缝贴图片段 | 可说明仓库存在纹理化焊缝仿真支撑，但含绝对纹理路径 | 配置存在 |
| 源代码 | `yolov5/detect.py:35-43`、`yolov5/detect.py:183-220` | YOLOv5 离线推理和保存逻辑 | 可说明仓库包含离线检测工具，但不是 ROS 主入口 | 代码已实现 |
| 源代码 | `yolov5/train.py:434-467`、`yolov5/val.py:300-320` | YOLOv5 训练/验证参数入口 | 可说明存在训练与评估代码，但缺少当前项目数据集配置和结果 | 代码已实现 |
| 配置 | `yolov5/models/yolov5s.yaml:3-47` | YOLOv5s 官方模型结构配置 | 可介绍 YOLOv5 代码库包含典型结构配置，但不能断言当前权重一定使用该结构 | 配置存在 |
| 旧资料 | `thesis_handoff/*` | 旧论文交接材料、草稿、提示词、结构化事实 | 只能参考写作习惯；技术内容必须回到当前代码验证 | 旧资料 |
| 参考论文 | `/home/bn/球罐检测机器人定位导航及控制技术研究_李杰.pdf` | 摘要、英文摘要和目录体现博士论文的章节组织与学术表达方式 | 只能参考“背景—方法—实现—实验—总结”的写作组织，不能作为本项目技术事实依据 | 外部写作参考 |
| 报告 | `check_reports/yolov5主链路最小修正与运行说明报告.md:60-143` | 主链路、权重路径、中心点消息说明 | 可作为历史工程说明，但最终以源码和 README 为准 | 文档提及 |
| 实验结果 | `models/seam_best.pt`、`models/best_curve10s_img416.pt` 等 | 本地存在 `.pt` 权重文件 | 可说明仓库包含模型权重文件；当前环境缺少 `torch`，未能读取权重元数据 | 配置存在，权重内容未确认 |
| 媒体 | `原视频.mp4`、`识别视频.mp4`、`yolo/frames/*.png` | 参考视频与帧图像 | 可说明存在素材/展示文件；来源、用途和指标需用户确认 | 未确认 |

## 4. 整体技术路线

1. 输入与初始化：系统通过 ROS launch 参数确定图像源、模型权重路径、YOLOv5 代码路径、置信度阈值、NMS IoU 阈值、目标类别过滤参数、设备参数和是否启动底盘桥。主入口 `seam_tracking.launch` 的默认权重为 `$(find robot_vision)/../../../models/seam_best.pt`，YOLOv5 代码路径为 `$(find robot_vision)/../../../yolov5`。依据：`catkin_ws/src/robot_vision/launch/seam_tracking.launch:16-32`。

2. 数据读取或信息采集：图像输入可以来自真实相机，也可以来自假相机。真实相机路径调用 `uvc_camera_node`，默认分辨率为 640×480，话题为 `/image_raw`；假相机路径可读取单张图片或循环读取视频帧并发布同一图像话题。依据：`catkin_ws/src/robot_vision/launch/seam_tracking.launch:42-57`、`catkin_ws/src/robot_vision/launch/robot_camera.launch:15-39`、`catkin_ws/src/robot_vision/scripts/fake_camera.py:52-90`。

3. 预处理或状态构建：YOLO 检测节点把 ROS `sensor_msgs/Image` 转换为 OpenCV BGR 图像，并在 YOLOv5 后端中执行 letterbox 尺寸调整、BGR/RGB 通道顺序转换、维度转置、张量化、浮点化和 0-1 归一化。依据：`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:162-195`、`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:235-245`。

4. 核心算法处理：检测节点通过 `attempt_load()` 加载本地 `.pt` 权重，调用 YOLOv5 模型进行推理，再用 `non_max_suppression()` 过滤候选框，并使用 `scale_coords()` 把检测框坐标映射回原图尺寸。若设置 `target_class_id >= 0`，则按类别过滤；否则使用全部类别。代码选择置信度最高的检测框作为控制目标。依据：`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:91-138`、`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:246-266`。

5. 目标位置表征：当存在有效检测框时，系统计算 `center_x = (x1 + x2) / 2.0`，并把 `center_x`、`image_width` 和有效标志编码到 `geometry_msgs/Point` 中发布。`Point.x` 表示检测框横向中心，`Point.y` 表示图像宽度，`Point.z` 表示有效性。依据：`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:155-160`、`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:305-310`、`README.md:55-67`。

6. 决策与控制：控制节点在外部中心点模式下订阅 `/seam_center`。若消息有效，则以 `image_width / 2.0` 作为参考中心，将检测框中心作为目标中心，调用原有 `twist_calculate()` 生成 `Twist`。控制函数在目标接近图像中心时给定直行速度；偏差较小时同时调整角速度和线速度；偏差较大时降低线速度。依据：`catkin_ws/src/robot_vision/scripts/line_detector.py:82-90`、`catkin_ws/src/robot_vision/scripts/line_detector.py:154-171`。

7. 输出与执行：控制节点发布 `cmd_vel`。若启动 `run_base_control:=true`，底盘桥订阅同名速度话题，将 `linear.x`、`linear.y` 和 `angular.z` 放大 1000 后按协议打包，经串口发送到底盘。Gazebo 支撑路径中也存在订阅 `cmd_vel` 的平面运动插件。依据：`catkin_ws/src/robot_vision/launch/seam_tracking.launch:34-40`、`catkin_ws/src/base_control/script/base_control.py:217-246`、`catkin_ws/src/nanoomni_description/urdf/nanoomni_description.gazebo.xacro:26-33`。

8. 可视化、评估或反馈机制：视觉节点可发布 `/result_image`，在图像上绘制检测框、目标中心、图像中心线和置信度文字；旧 HSV 路径还可发布 `/mask_image`。仓库中存在 YOLOv5 `val.py` 评价逻辑和旧 `DrawLoss.py` 指标绘图脚本，但没有发现与当前焊缝权重对应的真实数值结果。依据：`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:311-331`、`catkin_ws/src/robot_vision/scripts/line_detector.py:143-150`、`yolov5/val.py:83-99`、`yolo/DrawLoss.py:15-81`。

## 5. 核心方法与原理

### 5.1 基于 ROS 图像话题的视觉输入方法

#### 代码依据

`catkin_ws/src/robot_vision/launch/seam_tracking.launch:42-57`；`catkin_ws/src/robot_vision/launch/robot_camera.launch:15-39`；`catkin_ws/src/robot_vision/scripts/fake_camera.py:17-90`。

#### 方法作用

该方法负责为后续视觉检测提供统一图像输入。无论输入来自真实 USB 相机、静态测试图像还是循环视频，后续节点均通过 `/image_raw` 消费图像，因此控制流程不依赖图像源实现细节。

#### 基本原理

ROS1 中通过话题传递 `sensor_msgs/Image` 图像消息。主 launch 根据 `use_fake_camera` 选择真实相机或假相机。真实相机使用 `uvc_camera_node` 采集 640×480 图像；假相机使用 OpenCV 读取图片或视频帧，再通过 `cv_bridge` 转换为 ROS 图像消息。

#### 实现逻辑

真实相机路径根据 `camera_device`、`BASE_TYPE`、`CAMERA_TYPE` 等参数启动 `uvc_camera_node`。假相机路径读取 `~image_path` 或 `~video_path`，以 `~fps` 控制发布频率。视频读取到末尾后，代码将帧位置设回 0，实现循环播放。输出均为 `/image_raw`。

#### 可用于论文的表述

系统将视觉输入抽象为统一的 ROS 图像话题接口。实际运行时，可由相机节点直接发布实时图像，也可由测试节点读取本地图片或视频帧并周期性发布。该设计使感知算法与图像来源解耦，便于在无实车条件下进行链路调试，并为后续目标检测提供一致的数据入口。依据：`fake_camera.py` 中的 `pub_single_image()` 与 `pub_video()` 实现。

#### 不能写或待确认内容

不能写明实际相机型号、镜头参数、安装角度或工位布置；仓库只提供相机 launch 和两个相机内参配置文件，未说明实际采用哪一个硬件。

### 5.2 基于 YOLOv5 的目标检测推理方法

#### 代码依据

`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:74-138`；`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:235-266`；`yolov5/detect.py:35-43`；`yolov5/models/yolov5s.yaml:3-47`。

#### 方法作用

该方法负责从输入图像中得到焊缝目标候选框，并为后续中心点提取提供几何边界框。

#### 基本原理

代码调用本地 YOLOv5 工程中的 `attempt_load()` 加载 `.pt` 权重，通过 `letterbox` 调整输入尺寸，通过张量化和归一化构造模型输入。模型输出后使用非极大值抑制去除冗余候选框，再将坐标缩放回原始图像尺寸。代码中没有实现新的网络结构训练逻辑，而是复用 YOLOv5 推理工具链。

#### 实现逻辑

节点读取 `~model_path`、`~yolov5_repo_path`、`~conf_threshold`、`~iou_threshold`、`~target_class_id`、`~device` 等参数。若后端为 `yolov5`，将 YOLOv5 仓库加入 `sys.path`，导入 `attempt_load`、`letterbox`、`non_max_suppression`、`scale_coords` 和 `select_device`。每帧图像推理后，若有检测结果，则选择 `det[:, 4].argmax()` 对应的最高置信度框作为目标输出。

#### 可用于论文的表述

视觉感知部分采用基于检测框的目标检测方法。系统首先对输入图像进行尺寸调整、通道转换、张量化和归一化处理，然后调用本地 YOLOv5 模型进行前向推理。推理结果经过置信度阈值和非极大值抑制筛选后，保留置信度最高的候选框作为当前帧的焊缝目标区域，并将其坐标恢复到原图坐标系中，为后续位置表征提供依据。

#### 不能写或待确认内容

不能断言 `models/seam_best.pt` 的具体网络规模、训练轮数、训练数据集、类别名称、mAP、损失曲线或是否为 YOLOv5s。仓库存在 `yolov5s.yaml`，但当前环境缺少 `torch`，未能读取 `seam_best.pt` 元数据；因此权重结构和类别定义仍需用户确认。

### 5.3 检测框中心位置表征方法

#### 代码依据

`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:155-160`；`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:291-310`；`README.md:55-67`。

#### 方法作用

该方法把目标检测输出从完整边界框压缩为控制所需的最小几何量，即目标横向中心坐标、图像宽度和检测有效标志。

#### 基本原理

控制节点不需要完整图像或完整检测框，只需要知道目标在图像横向方向上相对中心的位置。因此系统使用检测框左右边界的均值表示目标中心横坐标，并用图像宽度构造参考中心。

#### 实现逻辑

当检测框为 `(x1, y1, x2, y2)` 时，代码计算 `center_x = (x1 + x2) / 2.0`。随后构造 `geometry_msgs/Point`：`x=center_x`，`y=image_width`，`z=1.0`。无检测时发布 `x=-1.0`，`y=image_width`，`z=0.0`。

#### 可用于论文的表述

为了将目标检测结果转化为可用于控制的几何量，系统没有直接使用完整边界框或图像特征，而是提取检测框的横向中心作为目标位置表征。该表征形式保留了控制所需的关键偏差信息，同时降低了感知输出与控制输入之间的接口复杂度。目标中心与图像宽度共同构成后续偏差计算的基础。

#### 不能写或待确认内容

不能写成系统进行了焊缝中心线拟合、骨架提取、语义分割、轨迹预测或三维重建；代码中只提取检测框中心点。

### 5.4 外部中心点输入下的中心偏差控制方法

#### 代码依据

`catkin_ws/src/robot_vision/scripts/line_detector.py:39-60`；`catkin_ws/src/robot_vision/scripts/line_detector.py:90-110`；`catkin_ws/src/robot_vision/scripts/line_detector.py:165-202`。

#### 方法作用

该方法将视觉目标横向位置转化为机器人速度控制指令。它保留了原控制函数，通过外部中心点输入替代旧 HSV 视觉中心输入。

#### 基本原理

控制参考为图像横向中心 `image_width / 2.0`，目标位置为检测框中心 `center_x`。代码中 `twist_calculate(ref_center, target_center)` 的第一个参数在外部模式下传入 `image_width / 2.0`，第二个参数传入 `center_x`。控制器内部使用归一化误差 `e = (ref_center - target_center) / ref_center`。当 `abs(e) < 0.05` 时，认为目标接近中心，给定前进速度；否则通过小增益 PI 形式计算角速度，其中 `Kp=0.5`、`Ki=0.02`，并带有 `abs(e)<0.30` 的条件积分、`i_max=0.3` 的积分限幅和异常时间间隔保护。

#### 实现逻辑

外部中心点回调读取 `Point.y` 作为图像宽度，读取 `Point.x` 作为目标中心。当 `Point.z > 0.5` 且宽度有效时，更新最后有效时间并调用 `twist_calculate(image_width / 2.0, center_x)`。控制函数初始化全零 `Twist`，明确将 `linear.y` 置为 0；在中心误差较小时设置 `linear.x=0.2`、`angular.z=0`；在偏差存在时设置 `angular.z=Kp*e+Ki*i_error`，并按 `abs(angular.z)<0.2` 分段将 `linear.x` 设置为 `0.2-abs(angular.z)/2.0` 或 `0.1`。检测无效、初始未收到有效中心或中心点超时时，代码发布零速度并清零积分状态。

#### 可用于论文的表述

运动控制部分采用基于图像中心偏差的速度调节策略。系统以图像中心作为期望位置，以检测框中心作为当前目标位置，通过二者的横向差异构造控制误差。当目标接近期望中心时，机器人保持前向速度直行；当目标偏离中心时，系统通过小增益 PI 控制生成偏航角速度，并在角速度较大时降低前向速度，从而兼顾跟踪修正与运动稳定性。实体平台为麦克纳姆轮全向底盘，但当前焊缝跟踪控制输出为 `u=[v_x, 0, omega_z]`，没有启用横向速度 `v_y` 参与纠偏。

#### 不能写或待确认内容

不能将该控制律写成完整 PID、MPC、纯跟踪、卡尔曼滤波控制、闭环里程计反馈控制或基于横向平移的全向跟踪控制。主焊缝跟踪控制代码没有读取 `odom` 反馈；它只消费中心点消息并输出 `cmd_vel`。当前上层代码没有实现四轮麦克纳姆逆运动学，轮速分配应表述为底盘控制板或下位机执行层完成。现在本地 NanoOmni 控制板资料可以支撑“下位机侧完成轮速分配和电机闭环”，但不能支撑“上层焊缝跟踪控制已使用 `v_y` 或里程计反馈”。

### 5.5 目标丢失与输入超时安全停止方法

#### 代码依据

`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py:323-326`；`catkin_ws/src/robot_vision/scripts/line_detector.py:78-99`；`README.md:218-223`。

#### 方法作用

该方法用于在检测无效或视觉输入中断时避免继续运动。

#### 基本原理

系统使用有效标志和看门狗双重约束。检测节点在无目标时发布无效中心，控制节点收到无效标志时立即发布零速度；如果长时间没有收到有效中心点，定时器也会发布零速度。

#### 实现逻辑

检测失败时，`yolo_seam_detector.py` 调用 `publish_center(-1.0, image_width, False)`。控制节点在 `external_center_callback()` 中判断 `data.z > 0.5 and image_width > 0`，无效则调用 `publish_stop()`。定时器每 0.1 秒执行一次，如果距离最近有效中心点超过 `external_center_timeout`，同样发布零速度。

#### 可用于论文的表述

为提高系统运行安全性，控制链路对视觉结果有效性进行了显式约束。当检测模块未输出有效目标时，控制节点不再使用上一帧目标位置继续运动，而是发布零速度指令；当外部中心点消息超时，系统也进入停止状态。该机制可以降低目标丢失、遮挡或输入中断时的误运动风险。

#### 不能写或待确认内容

不能写成已经完成硬件急停测试或满足某种安全标准；仓库中没有实机安全测试记录。

### 5.6 旧 HSV 线中心提取方法

#### 代码依据

`catkin_ws/src/robot_vision/scripts/line_detector.py:101-135`；`catkin_ws/src/robot_vision/config/line_hsv.cfg:1-14`；`catkin_ws/src/robot_vision/launch/line_follow.launch:1-24`。

#### 方法作用

该方法是仓库保留的旧视觉路径，可作为备用方案或论文中的传统方法对照背景。当前主入口 `seam_tracking.launch` 不启动旧 HSV 视觉前端，而是把同一控制脚本置于外部中心点模式。

#### 基本原理

旧路径将 BGR 图像转换为 HSV 空间，通过上下限阈值得到二值掩膜，再进行形态学闭运算。随后在图像中部附近多条水平扫描线上寻找掩膜非零像素，使用其均值作为线中心。

#### 实现逻辑

代码用 `cv2.inRange()` 生成掩膜，用 9×9 核进行闭运算；在 `range(-60,100,20)` 的若干水平行上寻找非零像素，若像素数量大于 10，则取均值作为 `center_point`，再调用同一 `twist_calculate()` 产生速度。

#### 可用于论文的表述

仓库中保留了基于 HSV 阈值分割的传统线中心提取方法。该方法通过颜色空间阈值和局部扫描行求均值获得目标中心，具有实现简单、计算量低的特点。当前系统的主链路没有删除该路径，而是在新的检测框中心表征中继续复用其后端控制函数。

#### 不能写或待确认内容

不能把 HSV 路径写成当前主感知算法；当前 README 和 `seam_tracking.launch` 均指向 YOLOv5 主链路。

### 5.7 `cmd_vel` 到底盘串口协议的执行方法

#### 代码依据

`catkin_ws/src/base_control/launch/base_control.launch:24-45`；`catkin_ws/src/base_control/script/base_control.py:145-166`；`catkin_ws/src/base_control/script/base_control.py:217-246`；`catkin_ws/src/base_control/README.md:7-48`。

#### 方法作用

该方法负责把 ROS 标准速度指令转换为底盘可识别的串口协议数据，使上层视觉控制输出能够驱动实体底盘。

#### 基本原理

底盘桥订阅 `geometry_msgs/Twist`，读取 `linear.x`、`linear.y` 和 `angular.z` 三个速度分量，将其按 1000 倍缩放为整数并填入协议帧。协议帧以 `0x5a` 为帧头，包含帧长度、ID、功能码、速度数据、预留位和 CRC-8 校验。协议功能码 `0x01` 发送 X 轴速度、Y 轴速度和 Z 轴角速度；功能码 `0x11/0x12` 的说明中明确提到增加 Y 轴线速度是为了适应全向移动底盘需求。本地 NanoOmni 控制板资料进一步显示，控制板接收 `0x01` 速度帧后将 X/Y/Z 速度除以 1000 恢复为 `fLineX`、`fLineY` 和 `fAngleZ`，并调用底盘运动学函数计算四个电机目标转速。

#### 实现逻辑

`cmdCB()` 从 `Twist` 中取 `linear.x`、`linear.y`、`angular.z`，分别写入协议数据区的 X、Y、Z 速度字段，调用 `crc_byte()` 计算校验后通过 `self.serial.write(output)` 发送。底盘控制板程序中的 `vSetVelocityCommand()` 解析三轴速度，`vComputeMotorSpeed()` 按麦克纳姆轮关系计算四个电机目标转速。控制板主循环每 `MOTOR_CONTROL_PERIOD=25 ms` 读取四路编码器转速、进行电机 PID 计算并输出 PWM；电机 PID 参数来自控制板配置，$K_P=0.2$、$K_I=0.2$、$K_D=0.25$。底盘桥还发布 `odom`、`battery`，可选发布 IMU 和超声波数据，但主焊缝跟踪控制未消费 `odom`。

#### 可用于论文的表述

执行层采用 ROS 速度话题到串口协议的桥接方式。上层控制节点只需发布标准 `cmd_vel`，底盘接口节点负责将三轴速度分量编码为下位机通信帧并发送到底盘控制板，从而实现感知控制算法与底层硬件协议的分离。论文中可说明实体底盘为 NanoOmni 麦克纳姆轮全向移动平台，底盘接口支持 X/Y/Z 三自由度速度命令，底盘执行层完成四轮目标转速分配、编码器测速和电机速度闭环；但当前焊缝跟踪控制只使用 X 轴前向速度和 Z 轴角速度，Y 轴横向速度通道保留但未用于纠偏。

#### 不能写或待确认内容

不能写成底盘硬件已经在本次环境中验证运行；当前环境没有执行实车测试。下位机 1000 ms 无指令主动停机来自 README 协议说明，属于文档提及。不能写上层 ROS 代码已经完成麦克纳姆四轮轮速逆解、横向平移纠偏或全向轨迹跟踪；当前可确认的是三轴速度接口存在，底盘控制板资料中存在四轮轮速分配和电机闭环。

### 5.8 Gazebo 与机器人模型仿真支撑方法

#### 代码依据

`catkin_ws/src/nanoomni_description/package.xml:1-20`；`catkin_ws/src/nanoomni_description/urdf/nanoomni_description.urdf.xacro:139-201`；`catkin_ws/src/nanoomni_description/urdf/nanoomni_description.gazebo.xacro:26-33`；`catkin_ws/src/nanoomni_description/urdf/nanoomni_description.gazebo.xacro:107-136`；`catkin_ws/src/robot_vision/launch/gazebo_seam_tracking.launch:1-78`。

#### 方法作用

该方法为系统提供机器人模型、Gazebo 运动执行、相机图像输出和焊缝场景支撑。它不是当前实物主运行路径，但可作为论文系统实现或仿真分析的依据。

#### 基本原理

URDF/Xacro 描述机器人车体、轮、相机、雷达和 IMU 链接。Gazebo 插件提供平面运动、IMU、雷达和相机数据，其中 RGB 相机插件发布 `image_raw`，平面运动插件接收 `cmd_vel`。

#### 实现逻辑

`gazebo_seam_tracking.launch` 可启动 Gazebo world、加载机器人描述并生成模型，同时启动 YOLO 检测节点和外部中心点控制节点。`nanoomni_description` 下还存在曲线焊缝和纹理焊缝 world 文件。

#### 可用于论文的表述

仓库提供了面向仿真验证的机器人描述与 Gazebo 支撑环境。模型文件定义了移动底盘、相机、雷达和 IMU 等传感器链接，Gazebo 插件能够输出与实机链路一致的图像话题并接收 `cmd_vel` 速度指令，因此具备进行感知控制闭环仿真联调的基础。

#### 不能写或待确认内容

不能写成已经完成 Gazebo 仿真实验并得到定量结果。`seam_world_texture.world` 中存在 `file:///home/bn/...` 绝对纹理路径，跨机器运行前需要确认路径可用。

### 5.9 训练、评估和可视化工具的存在边界

#### 代码依据

`yolov5/train.py:434-467`；`yolov5/val.py:83-99`；`yolov5/val.py:236-297`；`yolo/DrawLoss.py:15-81`；`yolo/FPS.py:54-72`；`yolo/HeatPhoto.py:153-169`。

#### 方法作用

这些文件说明仓库中存在训练、验证、指标绘图、模型延迟测试和热力图可视化工具。但它们不等于当前项目已经完成对应实验。

#### 基本原理

YOLOv5 `train.py` 支持通过数据集 YAML、权重、图像尺寸、batch、epoch 等参数训练模型；`val.py` 支持 Precision、Recall、mAP@0.5、mAP@0.5:0.95 等指标计算；旧 `DrawLoss.py` 读取 `results.csv` 绘制训练损失曲线；`FPS.py` 通过多次推理统计延迟和 FPS。

#### 实现逻辑

当前仓库没有发现焊缝专用 `data.yaml`、训练 `results.csv`、验证输出目录或可读取的数值日志。`yolo/train.py` 使用 Windows 路径 `D:\xiangmu\dateset\water-rain\date.yaml`，不适合作为 Ubuntu ROS 主运行入口。`yolo/metrics_row_plot.png` 存在，但缺少对应源 CSV，不能提取论文指标。

#### 可用于论文的表述

仓库包含 YOLOv5 官方训练和验证代码，以及若干旧的模型性能与可视化脚本，可为后续补充训练实验、检测评估和可视化分析提供工具基础。当前可确认的是工具存在，而不是实验已经完成。

#### 不能写或待确认内容

不能编造 mAP、准确率、召回率、FPS、损失值、消融实验或对比实验；也不能把旧脚本中的 `YOLOv11`、`Gold-YOLO`、`EMSD-YOLO` 等标签写成当前系统实际采用的方法。

## 5.10 需要主动避免沿用的旧方向

后续 AI 在论文写作中应主动避免把以下内容继续写成“当前方案可能采用、可作为当前正文延伸、后续章节可按此展开”的口气：

- Stanley 控制；
- MPC 控制；
- 滑模控制；
- UWB；
- 多传感器融合定位；
- 卡尔曼滤波；
- Mask R-CNN 作为本文已实现方法；
- DeepLabv3+ 作为本文已实现方法；
- 三维点云定位作为本文已实现方法；
- 焊缝语义分割、中心线拟合、骨架提取作为本文已实现方法；
- 全局路径规划；
- Frenet 轨迹规划作为本文已实现方法；
- PID 对比实验；
- 工业现场测试已完成；
- 完整实机闭环定量实验已完成；
- 上层 ROS 焊缝跟踪代码已实现四轮麦克纳姆逆运动学；
- 上层控制已启用 `linear.y` 横向纠偏；
- 上层焊缝跟踪控制读取 `odom`、IMU 或编码器反馈形成闭环。

这些内容若仅出现在“禁止写入”边界说明中可以保留，但不应再在任何提示词、交接材料或写作说明中以“可以继续往这个方向写”的口气出现。

## 6. 系统实现逻辑

从实现结构看，当前仓库可以分为六个功能层。

1. 图像输入层：由真实相机 launch 或假相机脚本产生 `/image_raw`。这一层只负责提供图像，不承担检测或控制决策。依据：`robot_camera.launch`、`fake_camera.py`。

2. 视觉检测层：由 YOLO 检测节点接收图像、加载权重、完成推理、筛选检测框并发布结果图。该层输出的是目标位置而不是速度。依据：`yolo_seam_detector.py`。

3. 位置表征与接口层：将检测框压缩为 `center_x + image_width + valid_flag`，通过 `geometry_msgs/Point` 发送给控制层。该层是感知输出进入控制逻辑的关键接口。依据：`yolo_seam_detector.py:155-160`、`README.md:55-67`。

4. 偏差控制层：控制节点在外部中心点模式下不再进行 HSV 图像提取，而是直接使用 `/seam_center` 构造中心偏差并输出 `cmd_vel`。旧 HSV 逻辑仍保留在同一脚本中作为备用路径。依据：`line_detector.py:39-60`、`line_detector.py:82-99`、`line_detector.py:154-171`。

5. 执行接口层：实机路径由 `base_control.py` 把 `cmd_vel` 编码成串口协议；仿真路径可由 Gazebo 插件消费 `cmd_vel` 并产生机器人运动。依据：`base_control.py:217-246`、`nanoomni_description.gazebo.xacro:26-33`。

6. 支撑层：`nanoomni_description` 提供 URDF、Gazebo、纹理和 world；`robot_navigation`、`lidar`、`robot_simulation`、`bingda_tutorials` 等包主要提供导航、雷达、Stage 仿真和教程功能。它们不属于当前 `seam_tracking.launch` 的主焊缝跟踪闭环。依据：`robot_navigation/package.xml:59-71`、`robot_simulation/package.xml:53-58`、`bingda_tutorials/CMakeLists.txt:52-78`、`lidar/*/package.xml`。

基于代码调用关系的推断：当前焊缝跟踪主控制闭环不依赖 `robot_navigation` 的 `move_base`、AMCL、SLAM 或激光雷达路径；这些功能在仓库中存在，但没有被 `seam_tracking.launch` 引入。

## 7. 运行流程与关键命令

### 环境依赖

README 明确面向 Ubuntu 18.04 + ROS Melodic 构建，YOLOv5 ROS 适配节点使用 Python3，需要 `rospy`、`cv_bridge`、`cv2`、`torch` 和本地 YOLOv5 模块。依据：`README.md:75-103`、`catkin_ws/src/robot_vision/YOLOV5_UBUNTU18_DEPLOY.md:3-20`。

### 构建命令

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
```

依据：`README.md:75-84`。

### 主运行入口

主入口为：

```bash
roslaunch robot_vision seam_tracking.launch
```

依据：`README.md:29-44`、`catkin_ws/src/robot_vision/launch/seam_tracking.launch:1-83`。

### 假相机调试，不启动底盘

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash

roslaunch robot_vision seam_tracking.launch \
  use_fake_camera:=true \
  run_base_control:=false \
  model_path:=$(rospack find robot_vision)/../../../models/seam_best.pt \
  yolov5_repo_path:=$(rospack find robot_vision)/../../../yolov5 \
  device:=cpu
```

依据：`README.md:105-122`。

### 视频循环测试

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash

roslaunch robot_vision seam_tracking.launch \
  use_fake_camera:=true \
  run_base_control:=false \
  device:=cpu \
  conf_thres:=0.1 \
  class_id:=-1 \
  video_path:=$HOME/bsnew/原视频.mp4
```

依据：`README.md:124-142`。

### 真实相机运行，不启动底盘

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash

roslaunch robot_vision seam_tracking.launch \
  use_fake_camera:=false \
  camera_device:=video0 \
  run_base_control:=false \
  device:=cpu
```

如相机 launch 依赖环境变量，可设置：

```bash
export BASE_TYPE=NanoCar
export CAMERA_TYPE=csi72
```

依据：`README.md:144-163`。

### 启动底盘桥

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash

roslaunch robot_vision seam_tracking.launch \
  use_fake_camera:=false \
  camera_device:=video0 \
  run_base_control:=true \
  device:=cpu
```

依据：`README.md:165-181`。是否能实车运行仍需硬件验证。

### Gazebo 支撑入口

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash
roslaunch robot_vision gazebo_seam_tracking.launch
```

依据：`catkin_ws/src/robot_vision/launch/gazebo_seam_tracking.launch:1-78`。README 没有把该命令列为主入口，写论文时应表述为仿真支撑入口，而不是已验证主实验结果。

### 调试命令

```bash
source /opt/ros/melodic/setup.bash
source ~/bsnew/catkin_ws/devel/setup.bash
rostopic echo /seam_center
rostopic echo /cmd_vel
rqt_image_view /result_image
rostopic info /seam_center
rostopic info /cmd_vel
rqt_graph
```

依据：`README.md:183-216`。

### 训练、推理、评估命令边界

仓库包含 `yolov5/train.py`、`yolov5/detect.py`、`yolov5/val.py`，但未发现当前焊缝数据集 `data.yaml`、训练日志或 README 中的项目训练命令。因此论文中只能写“代码中存在 YOLOv5 训练、离线推理和验证工具”，不能写成当前项目已经完成训练和定量评估。

## 8. 实验、结果与评价指标

仓库中未发现可直接用于论文的完整实验结果表、检测精度数值、跟踪误差曲线、实机运行日志或消融实验记录。

可确认的实验或验证相关材料如下：

| 材料 | 仓库证据 | 可写内容 | 不能写内容 |
| --- | --- | --- | --- |
| 本地权重文件 | `models/seam_best.pt` 等 4 个 `.pt` 文件，约 14 MB | 仓库包含可供推理加载的模型权重文件 | 不能写权重训练来源、类别名、mAP 或模型结构 |
| 视频文件 | `原视频.mp4`、`识别视频.mp4` | 仓库存在参考原视频和识别视频 | 不能写视频来源、测试指标、帧率和检测成功率 |
| 帧图像 | `yolo/frames/` 下 353 张 `frame_*.png` | 仓库存在一组帧素材 | 不能写这些帧用于训练、验证或测试，除非用户确认 |
| 评估代码 | `yolov5/val.py:83-99`、`yolov5/val.py:236-297` | 存在 Precision、Recall、mAP 等评价逻辑 | 不能编造评价数值 |
| 绘图脚本 | `yolo/DrawLoss.py:15-81` | 存在读取 `results.csv` 绘图的脚本 | 未发现源 `results.csv`，不能写曲线结论 |
| 性能脚本 | `yolo/FPS.py:54-72` | 存在延迟/FPS 测试逻辑 | 未发现运行日志，不能写速度数值 |
| 静态检查报告 | `check_reports/yolov5主链路最小修正与运行说明报告.md:306-319` | 文档记录曾做源码级和配置级检查 | 不能替代 Ubuntu 18.04 + ROS Melodic 的实际运行验证 |

当前环境验证情况：尝试读取 `models/seam_best.pt` 元数据时，本机缺少 `torch`，因此未能确认权重内的类别名称、模型结构和训练信息。静态 XML 解析检查显示 `robot_vision`、`base_control`、`nanoomni_description` 的主要 launch 文件可被 Python XML 解析器解析，但这不等价于 ROS Melodic 运行成功。

## 9. 适合写入毕业论文的章节建议

章节建议可借鉴参考论文中“绪论、相关方法、系统方法、控制实现、实验验证、总结展望”的组织逻辑，但必须按当前代码能力重新裁剪。当前仓库不能支撑独立撰写机器人机构设计、三维空间定位、全局路径规划或现场工业测试等章节；这些内容只属于参考论文的研究范围，不属于本项目已确认实现。

### 第一章 绪论

可写内容：焊缝跟踪机器人任务背景、视觉感知到运动控制的总体问题、本文围绕图像目标检测、位置表征、偏差控制和 ROS1 闭环实现展开。应避免把项目表述为简单拼接。

代码依据：`README.md:1-16`、`README.md:46-73`、`seam_tracking.launch:1-83`。

需要补充的非代码材料：正式参考文献、应用场景介绍、研究意义、国内外研究现状。

### 第二章 相关技术与理论基础

可写内容：ROS1/catkin 话题通信、`sensor_msgs/Image`、`geometry_msgs/Point`、`geometry_msgs/Twist`、YOLOv5 检测流程、非极大值抑制、图像中心偏差控制的基本概念。

代码依据：`robot_vision/package.xml:51-61`、`yolo_seam_detector.py:91-138`、`yolo_seam_detector.py:235-266`、`line_detector.py:154-171`。

需要补充的非代码材料：YOLO 原理和 NMS 原理的正式文献引用。注意不要引用文献内容替代当前代码实现。

### 第三章 焊缝目标感知与位置表征方法

可写内容：图像输入、YOLO 推理、候选框筛选、最高置信度目标选择、检测框中心提取、`/seam_center` 消息构造、结果图可视化。

代码依据：`fake_camera.py:17-90`、`robot_camera.launch:15-39`、`yolo_seam_detector.py:155-160`、`yolo_seam_detector.py:284-331`。

需要补充的非代码材料：权重类别定义、数据集来源、训练方式、检测效果截图。

### 第四章 运动控制与系统实现

可写内容：外部中心点模式、参考中心构建、速度控制公式、目标丢失停车、`cmd_vel` 输出、底盘串口桥、Gazebo 仿真支撑、ROS 节点协同。

代码依据：`line_detector.py:39-60`、`line_detector.py:78-99`、`line_detector.py:154-171`、`base_control.py:217-246`、`nanoomni_description.gazebo.xacro:26-33`、`nanoomni_description.gazebo.xacro:107-136`。

需要补充的非代码材料：真实硬件型号、相机安装方式、`BASE_TYPE`、`CAMERA_TYPE`、串口设备实际情况、运行截图。

### 第五章 实验验证、结果分析与总结展望

可写内容：目前只能写实验设计、验证流程和应采集指标，不能写已完成的定量结果。可说明用假相机验证链路、用真实相机验证检测输出、用底盘桥验证 `cmd_vel` 执行、用无检测场景验证停车。总结部分可以概括当前系统已经形成从图像输入、目标检测、中心表征、偏差控制到速度输出的 ROS1 链路；展望部分可包括补充数据集训练、实机参数调优、增加稳定性评估和更完整的仿真验证。

代码依据：`README.md:105-216`、`yolov5/val.py:83-99`、`yolo/FPS.py:54-72`。

需要补充的非代码材料：检测精度、跟踪效果、速度响应、安全停止、实机视频、截图、表格数据和最终实验结论。

## 10. 可直接给新 GPT 的论文写作提示词

请基于我提供的《代码驱动的毕业论文写作交接材料》协助撰写中文本科毕业论文。你必须严格以交接材料中的代码、配置、README、报告、注释和仓库文件证据为依据，不得编造代码中不存在的数据集、硬件型号、传感器、训练过程、实验指标、对比实验、模型结构或运行结果。写作风格应为正式、客观、严谨的中文毕业论文表达，避免口语化，避免夸大创新性。外部参考论文只能用于借鉴章节组织和学术表达习惯，不得把参考论文中的机器人结构、算法、实验或应用场景写成本项目事实。

论文主线不要写成“两个系统融合”“两个模块拼接”，而要写成一个完整的技术方案：图像输入、YOLO 目标检测、检测框中心位置表征、目标中心与图像中心偏差构建、速度控制输出、ROS1 话题通信、底盘或仿真执行、安全停止与验证流程。正文中不要堆砌过多代码文件名、函数名、节点名，只有在需要证据时才引用具体名称。

请按章节逐步生成论文，每次先说明本章可以基于哪些证据写，哪些内容需要用户补充。遇到证据不足时，必须明确标注“需要用户补充”，不要用“可能”“应该”“看起来像”来补全事实。训练数据集、权重类别、实机平台、相机型号、实验指标、运行截图和测试结论如未由用户补充，不得写成既定事实。

## 11. 明确不能写的内容

1. 不能写项目已经完成 YOLO 训练并获得具体 mAP、Precision、Recall、FPS 或损失数值；仓库没有对应结果文件。
2. 不能写 `models/seam_best.pt` 的训练数据集、类别名称、训练轮次、网络规模或模型结构；当前环境未能读取权重元数据，仓库也没有对应说明。
3. 不能写当前系统采用完整 PID、MPC、卡尔曼滤波、轨迹规划、SLAM、AMCL 或 `move_base` 完成焊缝跟踪；主链路控制只使用中心偏差、小增益 PI 角速度调节和 `cmd_vel`。
4. 不能写系统实现了焊缝语义分割、中心线拟合、骨架提取、三维重建或焊缝宽度测量；代码只使用检测框中心。
5. 不能写雷达、IMU、里程计参与焊缝跟踪闭环控制；这些功能在仓库中存在，但主 seam-tracking 控制逻辑没有消费它们。
6. 不能写 `nanoomni_description` 是主控制包；它是描述和仿真支撑包。
7. 不能写 `yolo/` 旧 Ultralytics 目录是当前主运行入口；README 明确当前主视觉前端是 YOLOv5，旧目录为历史实验材料。
8. 不能把 `yolo/DrawLoss.py` 中的 `YOLOv11`、`Gold-YOLO`、`YOLOv10`、`YOLOv8`、`EMSD-YOLO` 标签写成当前项目已验证对比实验。
9. 用户已确认实体机器人为麦克纳姆轮全向移动底盘，但不能写未提供证据的具体商品型号、相机型号、安装位置、工位环境、焊缝材料或真实部署平台。
10. 不能写已经完成实机安全停止测试、实机闭环跟踪测试或 Gazebo 定量仿真实验；仓库只提供运行入口和支撑文件。
11. 不能把参考视频 `原视频.mp4`、`识别视频.mp4` 的来源、用途或指标写成已确认事实；仓库只证明文件存在。
12. 不能直接引用旧 `thesis_handoff/` 的技术结论作为当前事实；旧资料仅作为写作风格参考。
13. 不能把参考论文中的 Mask R-CNN、PID 控制、滑模控制、UWB 定位、卡尔曼滤波、多传感器融合、欧拉回路路径规划、圆柱罐实验平台或工业球罐现场测试写成当前项目代码已经实现的内容。

## 12. 待用户确认的问题

1. `models/seam_best.pt` 的训练数据集来源、类别名称、类别编号和是否为单类别检测。
2. 正式论文中使用的实际硬件平台细节：麦克纳姆轮全向底盘的具体型号、相机型号、安装位置、供电和串口设备映射。
3. 运行时 `BASE_TYPE`、`CAMERA_TYPE`、`target_class_id`、`conf_thres` 等参数的真实取值。
4. 是否已有可作为论文证据的实机运行截图、`/seam_center` 回显、`/cmd_vel` 回显、`/result_image` 截图和跟踪视频。
5. 是否需要把 Gazebo seam world 作为正式仿真实验；如果需要，需要补充仿真运行截图、话题记录和结果分析。
6. 是否有真实检测或跟踪评价数据；若没有，论文实验章节只能写验证流程和待补指标，不能写数值结论。
