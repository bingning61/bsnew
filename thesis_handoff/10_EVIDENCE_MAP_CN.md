# 事实-证据映射文档

下表用于约束后续论文写作时的事实边界。凡是标记为“代码确认”的内容，可以较稳定地写入论文技术描述；标记为“结构推断”的内容，写入时应保持谨慎并最好加上“根据当前代码推断”；标记为“待人工确认”的内容，则不应被当作既定事实直接写入正文。

| 关键事实或关键结论 | 证据来源文件路径 | 归类 | 置信度 | 备注 |
| --- | --- | --- | --- | --- |
| 当前主集成入口是 `robot_vision/launch/seam_tracking.launch` | `catkin_ws/src/robot_vision/launch/seam_tracking.launch` | 代码确认 | 高 | launch 直接组织主链路 |
| 图像输入默认话题为 `/image_raw` | `catkin_ws/src/robot_vision/launch/seam_tracking.launch`、`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` | 代码确认 | 高 | launch 参数与脚本默认值一致 |
| YOLO 节点名称为 `yolo_seam_detector` | `catkin_ws/src/robot_vision/launch/seam_tracking.launch` | 代码确认 | 高 | 主链路显式启动 |
| YOLO 节点输出 `/seam_center`，消息类型为 `geometry_msgs/Point` | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` | 代码确认 | 高 | `Publisher(self.center_topic, Point)` |
| `Point.x` 存储目标中心横坐标，`Point.y` 存储图像宽度，`Point.z` 存储有效标志 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`、`README.md` | 代码确认 | 高 | 代码与 README 一致 |
| YOLO 节点采用最高置信度策略选择最优检测框 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` | 代码确认 | 高 | `find_best_box()` 的实现可直接证明 |
| 若设置 `target_class_id`，系统会按类别筛选检测框 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`、`catkin_ws/src/robot_vision/launch/seam_tracking.launch` | 代码确认 | 高 | 参数与代码逻辑一致 |
| 若无有效检测，YOLO 节点会发布无效中心并在调试图像标注 `NO DETECTION` | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` | 代码确认 | 高 | 代码显式实现 |
| 控制节点 `line_detector.py` 已支持外部中心点模式 | `catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | `use_external_center`、`external_center_topic`、`external_center_watchdog()` |
| 外部中心点模式下，控制节点继续调用原 `twist_calculate()` | `catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | `external_center_callback()` 直接调用 |
| 当前控制主反馈量是图像中心偏差，而不是 odom 误差 | `catkin_ws/src/robot_vision/scripts/line_detector.py`、`catkin_ws/src/base_control/script/base_control.py` | 结构推断 | 高 | seam 控制只消费 `/seam_center`，不读取 `odom` |
| 当前控制律不是 PID，而是简单比例式偏差调节与分段速度控制 | `catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | 代码中无积分/微分项 |
| 参考中心等价取值为图像宽度的一半 | `catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | `twist_calculate(image_width / 2.0, center_x)` |
| 当前角速度公式等价为 `ω=(x_ref-x_obj)/(2x_ref)` | `catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | 可由代码直接化简得到 |
| 当前线速度在小偏差时采用角速度耦合调节，在大偏差时降为 `0.1` | `catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | `linear.x` 赋值逻辑明确 |
| 无效检测或中心消息超时后，控制节点发布零速度 | `catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | `publish_stop()` 与看门狗逻辑 |
| 旧 HSV 视觉路径仍然保留 | `catkin_ws/src/robot_vision/launch/line_follow.launch`、`catkin_ws/src/robot_vision/scripts/line_detector.py` | 代码确认 | 高 | 旧 launch 仍可见 |
| `fake_camera.py` 可在无实机条件下模拟图像输入 | `catkin_ws/src/robot_vision/scripts/fake_camera.py`、`catkin_ws/src/robot_vision/launch/seam_tracking.launch` | 代码确认 | 高 | 直接发布 `/image_raw` |
| `robot_camera.launch` 通过 `uvc_camera` 获取真实图像，并按 `BASE_TYPE` 发布相机 TF | `catkin_ws/src/robot_vision/launch/robot_camera.launch` | 代码确认 | 高 | launch 细节明确 |
| `base_control.py` 订阅 `cmd_vel` 并把速度指令转成串口协议发送到底盘 | `catkin_ws/src/base_control/script/base_control.py` | 代码确认 | 高 | `cmdCB()` 实现明确 |
| `base_control.py` 通过 `/dev/move_base` 与底盘通信 | `catkin_ws/src/base_control/launch/base_control.launch`、`catkin_ws/src/base_control/script/base_control.py` | 代码确认 | 高 | launch 默认参数与脚本读取一致 |
| `base_control.py` 发布 `odom`、`battery`，并可选发布 `imu`、`sonar` | `catkin_ws/src/base_control/script/base_control.py` | 代码确认 | 高 | publisher 逻辑可直接证明 |
| 下位机在超过 1000ms 未收到新协议数据时会主动停机 | `catkin_ws/src/base_control/README.md` | 文档确认 | 中 | 来自 README 协议说明，未在代码中再次验证 |
| 当前主链路混用了 `python3` 和 `python` 风格节点 | `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py`、`catkin_ws/src/robot_vision/scripts/line_detector.py`、`catkin_ws/src/base_control/script/base_control.py` | 代码确认 | 高 | shebang 可直接证明 |
| `robot_vision` 是当前主焊缝跟踪 package | `catkin_ws/src/robot_vision/package.xml`、`catkin_ws/src/robot_vision/launch/seam_tracking.launch` | 代码确认 | 高 | 主 launch 和核心脚本均在该包内 |
| `base_control` 是当前底盘执行接口包 | `catkin_ws/src/base_control/package.xml`、`catkin_ws/src/base_control/script/base_control.py` | 代码确认 | 高 | `cmd_vel` 到串口链路明确 |
| `nanoomni_description` 属于模型和 Gazebo 支撑包 | `catkin_ws/src/nanoomni_description/package.xml`、`catkin_ws/src/nanoomni_description/README.md`、`catkin_ws/src/nanoomni_description/launch/*.launch` | 代码确认 | 高 | 包描述与 launch 内容一致 |
| `nanoomni_description` 的 Gazebo 插件同时具备 `cmd_vel`、`odom`、`image_raw` 接口 | `catkin_ws/src/nanoomni_description/urdf/nanoomni_description.gazebo.xacro` | 代码确认 | 高 | 插件定义清晰 |
| `robot_simulation` 是通用 Stage 仿真包，不是当前焊缝跟踪主入口 | `catkin_ws/src/robot_simulation/package.xml`、`README.md`、`launch/*.launch` | 结构推断 | 高 | 包内容集中在 Stage、地图、AMCL |
| `robot_navigation`、雷达驱动包属于通用移动机器人能力，不是当前焊缝跟踪主链路 | `catkin_ws/src/robot_navigation/package.xml`、`catkin_ws/src/lidar/*/package.xml`、相关 launch | 结构推断 | 高 | 当前 `seam_tracking.launch` 未引用这些包 |
| 仓库当前没有实际 `.pt` 权重文件 | 对仓库执行 `find /home/bn/bsnew -type f -name '*.pt'` 结果为空 | 代码确认 | 高 | 当前工作区搜索结果可直接证明 |
| README 与 YOLO 节点注释中的 `exp17/weights/best.pt` 只是历史示例路径 | `README.md`、`catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` | 结构推断 | 高 | 有路径示例，但仓库中无实际文件 |
| `yolo/train.py` 采用外部 Windows 路径数据集，说明训练数据未随仓库提供 | `yolo/train.py` | 代码确认 | 高 | 数据集路径写死为外部路径 |
| `yolo/frames/` 下存在大量帧图像，可作为辅助视觉材料 | `yolo/frames/` 目录 | 代码确认 | 高 | 当前目录统计为 353 张图像 |
| `原视频.mp4`、`识别视频.mp4` 只能视为参考媒体，不能直接推出实验结论 | 仓库根目录文件名 | 结构推断 | 中 | 文件存在，但内容和实验结论未被代码说明 |
| 当前仓库足以支撑论文方法与系统实现写作，但不足以单独支撑定量实验结论 | 全仓库综合分析 | 结构推断 | 高 | 缺少权重、实验表格、运行截图和硬件信息 |

## 使用说明

如果后续需要把这张表交给新的 GPT，建议同时提供 `12_ALL_IN_ONE_GPT_HANDOFF_CN.md`。前者负责把总体逻辑说清楚，后者负责限制新 GPT 的事实边界。
