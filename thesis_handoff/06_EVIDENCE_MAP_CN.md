# 事实-证据映射文档

下表用于约束论文写作边界。凡是要进入正文的关键事实，尽量先在本表中找到对应证据；若只能落到“结构推断”或“待人工确认”，则在写作时必须显式说明。

| 编号 | 关键事实/关键结论 | 证据来源文件路径 | 性质 | 置信度 | 说明 |
| --- | --- | --- | --- | --- | --- |
| 1 | 当前焊缝跟踪主入口是 `robot_vision/launch/seam_tracking.launch` | `catkin_ws/src/robot_vision/launch/seam_tracking.launch` | 代码确认 | 高 | 文件在集成提交中新增 |
| 2 | 主入口可按参数决定是否接入底盘接口 | `catkin_ws/src/robot_vision/launch/seam_tracking.launch` | 代码确认 | 高 | `run_base_control` 参数直接控制是否 `include base_control.launch` |
| 3 | 系统支持假相机调试链路 | `catkin_ws/src/robot_vision/launch/seam_tracking.launch`、`catkin_ws/src/robot_vision/scripts/fake_camera.py` | 代码确认 | 高 | `use_fake_camera` 为真时启动 `fake_camera.py` |
| 4 | YOLO 节点订阅图像并发布中心点消息 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` | 代码确认 | 高 | 默认订阅 `/image_raw`，发布 `/seam_center` |
| 5 | 中心点消息类型为 `geometry_msgs/Point` | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`、`catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | 感知与控制均导入 `Point` |
| 6 | `Point.x` 表示目标中心横坐标，`Point.y` 表示图像宽度，`Point.z` 表示有效性 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` 的 `publish_center()` | 代码确认 | 高 | 代码直接赋值 |
| 7 | 检测框中心横坐标由 `(x1 + x2) / 2` 计算得到 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` 的 `image_callback()` | 代码确认 | 高 | 源码中直接计算 |
| 8 | 默认情况下 YOLO 节点选择最高置信度目标框 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` 的 `find_best_box()` | 代码确认 | 高 | 若 `target_class_id < 0`，按最高置信度选框 |
| 9 | 若指定 `target_class_id`，系统会先按类别过滤再选框 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` 的 `find_best_box()` | 代码确认 | 高 | 条件分支明确存在 |
| 10 | 当前控制器新增了外部中心点输入模式 | `catkin_ws/src/robot_vision/scripts/line_detector.py`、git diff `4879dfb..208353c` | 代码确认 | 高 | 新增 `use_external_center` 与相关回调 |
| 11 | 原 `twist_calculate()` 控制律在集成提交中未被重写 | git diff `4879dfb..208353c -- catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | diff 只新增外部中心点相关逻辑 |
| 12 | 控制器在目标居中时输出 `linear.x = 0.2` | `catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | `twist_calculate()` 直接赋值 |
| 13 | 控制器在非居中时依据归一化偏差计算 `angular.z` | `catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | `angular.z = ((width - center) / width) / 2.0` |
| 14 | 当前速度调节采用分段逻辑而非复杂控制器 | `catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | 只有阈值判断与简单比例关系 |
| 15 | 无效检测会触发零速度输出 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`、`catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | `valid=False` 时控制器执行 `publish_stop()` |
| 16 | 中心点超时也会触发零速度输出 | `catkin_ws/src/robot_vision/scripts/line_detector.py` 的 `external_center_watchdog()` | 代码确认 | 高 | 超时判断直接发布零速度 |
| 17 | 底盘接口层订阅 `cmd_vel` 并经串口发送速度控制帧 | `catkin_ws/src/base_control/script/base_control.py` 的 `cmdCB()` | 代码确认 | 高 | 代码中将 `linear.x`、`linear.y`、`angular.z` 打包发送 |
| 18 | 底盘接口层还会发布 `odom` 与 `battery` | `catkin_ws/src/base_control/script/base_control.py` 的 `timerOdomCB()`、`timerBatteryCB()` | 代码确认 | 高 | 代码中创建并发布对应 ROS 消息 |
| 19 | 底盘协议文档定义了超过 1000 ms 不接收新指令时主动停机 | `catkin_ws/src/base_control/README.md` | 代码确认 | 高 | README 明文说明 |
| 20 | 当前主链路仍保留旧版 HSV 路径 | `catkin_ws/src/robot_vision/launch/line_follow.launch`、`catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | 旧入口与 HSV 动态配置均仍在 |
| 21 | 真实相机链路依赖 `BASE_TYPE` 和 `CAMERA_TYPE` 环境变量 | `catkin_ws/src/robot_vision/launch/robot_camera.launch` | 代码确认 | 高 | `$(env BASE_TYPE)` 与 `$(env CAMERA_TYPE)` 直接出现在 launch 中 |
| 22 | 当前仓库没有实际 `.pt` 权重文件 | `find yolo -type f -name '*.pt'` 结果为空 | 代码确认 | 高 | 只能看到示例路径，看不到实际权重 |
| 23 | 根 README 与代码注释都提到过 `../yolo/runs/train/exp17/weights/best.pt` | `README.md`、`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` | 代码确认 | 高 | 说明曾存在示例权重路径，但当前仓库未附带文件 |
| 24 | `yolo/` 目录本质上是本地拷贝的 Ultralytics 代码库及其扩展 | `yolo/README.md`、`yolo/pyproject.toml`、`yolo/ultralytics/` | 代码确认 | 高 | 路径结构与包信息明确显示为 `ultralytics` |
| 25 | 训练脚本中的数据集路径不是当前仓库内路径 | `yolo/train.py` | 代码确认 | 高 | 使用外部 Windows 路径 `D:\\xiangmu\\dateset\\water-rain\\date.yaml` |
| 26 | 因缺少权重文件和数据集，无法从当前仓库确认实际部署模型结构 | `yolo/train.py`、`README.md`、`yolo/` 目录结构 | 结构推断 | 高 | 只能确定存在本地 YOLO 代码库，不能确定最终权重来源 |
| 27 | 当前系统采用的是“保留原控制器、替换前端位置来源”的兼容式方案 | git diff `4879dfb..208353c`、`README.md` | 结构推断 | 高 | diff 证据很强，但该结论本身是对工程策略的归纳 |
| 28 | 当前焊缝方法的核心不是分割曲线或三维重建，而是检测框中心代理 | `yolo_seam_detector.py`、`line_detector.py` | 结构推断 | 高 | 主链路只使用中心点，不使用更高阶几何量 |
| 29 | 当前主链路的实机闭环是视觉到底盘的反馈闭环 | `seam_tracking.launch`、`base_control.py`、`robot_camera.launch` | 结构推断 | 高 | 从节点关系可推断闭环存在，但缺少运行记录 |
| 30 | 假相机模式更适合功能验证，而非真实闭环实验 | `fake_camera.py`、`seam_tracking.launch` | 结构推断 | 高 | 输入图像静态不变，无法形成物理反馈 |
| 31 | `nanoomni_description` 属于模型与仿真支撑模块，不是当前焊缝主控制包 | `catkin_ws/src/nanoomni_description/package.xml`、`launch/`、`urdf/nanoomni_description.gazebo.xacro` | 结构推断 | 高 | 其内容明显偏向 URDF/Gazebo |
| 32 | `robot_simulation` 更偏向 Stage 雷达导航仿真而非焊缝视觉主链路 | `catkin_ws/src/robot_simulation/launch/*.launch`、`README.md` | 结构推断 | 高 | 其主内容是 `stage_ros`、地图与 AMCL |
| 33 | `robot_navigation` 与 `lidar/*` 是平台配套能力，不是焊缝论文主方法来源 | `catkin_ws/src/robot_navigation/launch/*.launch`、`catkin_ws/src/lidar/*` | 结构推断 | 高 | 代码内容集中在导航与雷达 |
| 34 | `nanoomni_description` 的 Gazebo 插件具备视觉仿真潜力 | `catkin_ws/src/nanoomni_description/urdf/nanoomni_description.gazebo.xacro` | 代码确认 | 高 | 同时存在 `cmd_vel` 插件和 `image_raw` 相机插件 |
| 35 | 仓库中存在 Python2 风格与 Python3 风格脚本并存的情况 | `robot_vision/scripts/*.py`、`base_control/script/base_control.py` | 代码确认 | 高 | `yolo_seam_detector.py` 为 `python3`，旧链路脚本为 `python`/`/usr/bin/python` |
| 36 | 混合解释器运行环境是否已经在原环境中配置完成，当前仓库无法直接确认 | 脚本 shebang、缺少环境脚本说明 | 待人工确认 | 中 | 必须由原运行环境验证 |
| 37 | 实际底盘型号不能仅凭 `nanoomni_description` 包名确定 | `robot_camera.launch`、`base_control.py`、`robot_navigation/param/*` | 待人工确认 | 中 | `BASE_TYPE` 支持多种平台 |
| 38 | 实际相机型号不能仅凭配置文件名确定 | `robot_vision/config/csi72.yaml`、`astrapro.yaml`、`robot_camera.launch` | 待人工确认 | 中 | 仓库只提供两个标定文件，不代表实际部署唯一值 |
| 39 | 视频 `原视频.mp4`、`识别视频.mp4` 不应被直接写成实验结论 | 仓库文件名本身不足以证明实验结果 | 结构推断 | 高 | 文件存在不等于可直接引用其结论 |
| 40 | 若要写实验性能结论，仍需实机数据和截图补证 | 仓库整体缺少实验数据目录 | 待人工确认 | 高 | 这是当前论文成稿的主要缺口 |

## 使用建议

1. 写“方法原理”前，优先查 1 至 18、27 至 30。
2. 写“系统实现”前，优先查 1 至 5、17 至 19、31 至 35。
3. 写“实验验证”前，必须先看 36 至 40，避免把缺失信息写成结果。
4. 若新的 GPT 想发挥性补充算法名、硬件型号或性能数字，应先对照本表；找不到证据的内容只能写成“待人工确认”。
