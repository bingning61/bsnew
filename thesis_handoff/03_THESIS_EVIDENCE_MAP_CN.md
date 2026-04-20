# 事实-证据映射文档

## 1. 使用说明
本文件的目的是帮助新 GPT 区分三类内容：

1. 可以直接从仓库看到的**代码确认事实**。
2. 可以从当前结构或 `git` 历史做出的**较稳妥推断**。
3. 当前仓库无法确认、必须保留为**待人工确认**的内容。

## 2. 关键事实与证据

| 关键结论/关键事实 | 证据来源 | 具体脚本 / launch / package | 置信度 | 备注 |
| --- | --- | --- | --- | --- |
| 仓库最终目标是“YOLO 前端 + 原 ROS1 控制后端”的焊缝跟踪系统 | `README.md` | 根目录 `README.md` 第 1-13 行 | 高 | 代码确认 |
| 当前融合后的主入口是 `robot_vision/launch/seam_tracking.launch` | `README.md`、`seam_tracking.launch` | `README.md` 第 22-23 行；`seam_tracking.launch` 全文 | 高 | 代码确认 |
| 当前主数据流是 `image -> YOLO bbox -> bbox center -> controller -> cmd_vel -> chassis` | `README.md`、`seam_tracking.launch`、`yolo_seam_detector.py`、`line_detector.py` | `README.md` 第 8-13 行；对应源码调用链 | 高 | 代码确认 |
| YOLO 节点文件是 `catkin_ws/src/robot_vision/scripts/yolo_seam_detector.py` | `git` 历史、源码 | `git log` 显示该文件在 commit `208353c` 新增；源码全文 | 高 | 代码确认 |
| YOLO 节点订阅 `/image_raw`，发布 `/seam_center` 和 `/result_image` | `yolo_seam_detector.py` | 第 18-20、32-37 行 | 高 | 代码确认 |
| `/seam_center` 使用 `geometry_msgs/Point` 传输中心位置、图像宽度和有效标志 | `README.md`、`yolo_seam_detector.py` | `README.md` 第 25-32 行；`yolo_seam_detector.py` 第 70-75 行 | 高 | 代码确认 |
| YOLO 检测框中心计算公式为 `(x1 + x2) / 2` | `yolo_seam_detector.py` | 第 123-127 行 | 高 | 代码确认 |
| 默认不限定检测类别，而是选最高置信度检测框 | `yolo_seam_detector.py` | 第 21-23、77-93 行 | 高 | 代码确认 |
| 原控制节点仍然是 `line_detector.py` | `line_follow.launch`、`seam_tracking.launch` | `line_follow.launch` 第 12 行；`seam_tracking.launch` 第 62 行 | 高 | 代码确认 |
| 原控制器不是被重写，而是被加上了 external center 输入模式 | `git` 历史、`line_detector.py` | `git show 208353c -- line_detector.py`；当前第 39-57、82-99 行 | 高 | 代码确认 |
| 原 `twist_calculate()` 控制律仍被保留 | `line_detector.py` | 第 154-171 行 | 高 | 代码确认 |
| 控制器在无有效检测或超时情况下会发布零速度 | `line_detector.py` | 第 78-99 行 | 高 | 代码确认 |
| 旧 HSV 跟线链路仍保留，可通过 `line_follow.launch` 使用 | `line_follow.launch`、`line_detector.py`、`line_hsv.cfg` | `line_follow.launch` 全文；`line_detector.py` 第 101-153 行 | 高 | 代码确认 |
| `robot_vision` 通过 dynamic reconfigure 支持 HSV 参数调节 | `robot_vision/CMakeLists.txt`、`line_hsv.cfg` | `CMakeLists.txt` 第 88-92 行；`line_hsv.cfg` 全文 | 高 | 代码确认 |
| 图像真实输入默认来自 `uvc_camera`，调试时也可来自 `fake_camera.py` | `robot_camera.launch`、`fake_camera.py`、`seam_tracking.launch` | `robot_camera.launch` 全文；`fake_camera.py` 全文；`seam_tracking.launch` 第 33-46 行 | 高 | 代码确认 |
| `robot_camera.launch` 依赖环境变量 `BASE_TYPE` 和 `CAMERA_TYPE` | `robot_camera.launch` | 第 4-5 行 | 高 | 代码确认 |
| `base_control.py` 订阅 `cmd_vel` 并通过串口控制底盘 | `base_control.py` | 第 145-166、218-246 行 | 高 | 代码确认 |
| `base_control.py` 默认串口设备是 `/dev/move_base` | `base_control.launch`、`base_control.py` | `base_control.launch` 第 28、52 行；`base_control.py` 第 89 行 | 高 | 代码确认 |
| `base_control.py` 同时发布里程计和电池信息 | `base_control.py` | 第 166-167、428-496 行 | 高 | 代码确认 |
| 当前融合实现是“最小修改原控制器输入方式”，不是“新增独立适配节点” | `git` 历史、`line_detector.py`、`seam_tracking.launch` | commit `208353c` 变更内容；主 launch 直接把 `/seam_center` 接到 `line_detector.py` | 高 | 代码确认 |
| `README.md`、`seam_tracking.launch`、`yolo_seam_detector.py` 都是在同一融合提交中加入的 | `git` 历史 | commit `208353c Add seam tracking integration` | 高 | git 历史确认 |
| 当前工作区中还有导航、仿真、雷达、教程等 package，但不是焊缝跟踪主链路必需模块 | 目录结构、各 package 的 package.xml/launch | `robot_navigation`、`robot_simulation`、`lidar/*`、`bingda_tutorials` | 高 | 代码确认 |
| 根目录 `README.md` 示例使用了 `../yolo/runs/train/exp17/weights/best.pt` | `README.md` | 第 57-77 行 | 高 | 代码确认 |
| 当前仓库中并没有这个示例权重文件 | 本地文件存在性检查 | 未找到 `yolo/runs/train/exp17/weights/best.pt` | 高 | 代码确认 |
| `yolo/` 下存在 Ultralytics 源码树，但训练/推理模板脚本多为通用占位脚本 | `yolo/pyproject.toml`、`yolo/Detect.py`、`yolo/train.py`、`yolo/val.py` | `pyproject.toml` 第 26-81 行；模板脚本第 1-26 行 | 高 | 代码确认 |
| 当前仓库中没有直接可引用的检测精度、控制误差、实机实验结果 | 目录检查 | 未发现实验数据表、结果截图、性能统计文件 | 中 | 结构结论，但证据充分 |
| 当前项目大概率面向 ROS Melodic | `README.md`、项目背景 | `README.md` 使用 `/opt/ros/melodic/setup.bash` 示例；项目目标环境是 Ubuntu 18.04 | 中 | 合理推断 |
| 当前源码存在 Python2 风格节点与 Python3 风格节点混用 | 脚本 shebang 与语法 | `yolo_seam_detector.py` 使用 `python3`；`line_detector.py`、`fake_camera.py`、`base_control.py` 为 Python2 风格 | 高 | 代码确认 |
| 两个 mp4 文件只能确认“存在”，不能确认其具体实验内容和效果 | 文件存在性 | 仓库根目录 `原视频.mp4`、`识别视频.mp4` | 高 | 待人工确认其内容 |

## 3. 容易被误写但当前无法确认的内容

| 内容 | 当前证据状态 | 置信度 | 建议写法 |
| --- | --- | --- | --- |
| 实际使用的 YOLO 权重文件名称 | README 只有示例路径，真实文件缺失 | 低 | 写成“需人工提供实际权重文件” |
| 焊缝类别名称与标签编号 | 代码只支持 `target_class_id`，未提供类别清单 | 低 | 写成“类别定义待人工确认” |
| 检测精度、召回率、mAP、FPS | 仓库无实验结果 | 低 | 不要编造，列为待补实验数据 |
| 底盘具体型号 | 有 `BASE_TYPE` 机制，但未看到实际取值 | 低 | 写成“底盘类型由部署环境决定，待人工确认” |
| 相机具体型号 | 有 `CAMERA_TYPE` 机制，但未看到实际取值 | 低 | 写成“相机型号待人工确认” |
| 最终 ROS1 发行版 | README 用 melodic 示例，但源码未硬编码 | 中 | 写成“README 以 melodic 为例，最终发行版待确认” |
| 两个 mp4 分别展示了什么实验现象 | 未做视频内容解析 | 低 | 只能写“仓库提供了参考视频素材” |

## 4. 写论文时的使用原则

1. 只要是节点名、话题名、launch 名、脚本名、参数名，尽量直接引用当前文件中的原名。
2. 只要涉及“系统已完成什么”，优先引用 `README.md`、`seam_tracking.launch`、`yolo_seam_detector.py`、`line_detector.py`、`base_control.py` 和 `git` 提交 `208353c`。
3. 只要涉及“性能如何”“实验结果怎样”“实机效果多好”，当前仓库都不能直接支撑，必须先由你后续补充材料。
