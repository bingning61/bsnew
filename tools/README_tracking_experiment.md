# Gazebo 焊缝跟踪参数实验脚本

本目录提供一键 Gazebo 参数实验脚本，用于记录 `/cmd_vel` 和 `/seam_center`，生成论文曲线并输出统计结果。脚本面向 Ubuntu 18.04 + ROS Melodic 虚拟机。

## 一键运行

```bash
cd /home/bn/bsnew
bash tools/run_tracking_experiment.sh baseline 30
bash tools/run_tracking_experiment.sh opt_kp06 30
bash tools/run_tracking_experiment.sh opt_kp065 30
bash tools/run_tracking_experiment.sh slow_v016 30
```

第二个参数为记录时长，单位为秒，默认 30 秒。脚本默认复现半宽纹理焊缝场景，默认权重为：

```text
/home/bn/bsnew/models/best_curve_bg_thin_real.pt
```

默认 Gazebo world 为：

```text
/home/bn/bsnew/catkin_ws/src/nanoomni_description/worlds/seam_world_texture_half_width.world
```

默认初始位姿和检测参数为：

```text
spawn_x=-2.9
spawn_y=0.0
spawn_yaw=0.35
conf_threshold=0.1
target_class_id=-1
device=cpu
```

默认 YOLOv5 路径为：

```text
/home/bn/bsnew/yolov5
```

如果不想每次运行前编译，可使用：

```bash
SKIP_BUILD=1 bash tools/run_tracking_experiment.sh opt_kp06 30
```

如果 Gazebo 和 YOLO 启动较慢，可延长等待时间：

```bash
STARTUP_WAIT=25 bash tools/run_tracking_experiment.sh opt_kp06 30
```

如果虚拟机里话题启动较慢，想多给一点“检测先准备好”的时间，可设置：

```bash
CENTER_READY_TIMEOUT=20 bash tools/run_tracking_experiment.sh baseline 30
```

脚本默认按真实时间记录 30 秒，并按 `wall_time` 绘图。这样即使虚拟机中 Gazebo 仿真时间推进较慢，图片横坐标也会显示真实记录时长。若需要诊断仿真时间，可查看 `summary.txt` 中的 `clock_ros_duration` 和 `sim_realtime_factor_est`。

如无特殊诊断需求，不建议改成 ROS 仿真时间作为记录基准；在虚拟机中仿真时间可能明显慢于真实时间，容易再次出现“运行了 30 秒但图上只有几秒”的现象。

如需临时覆盖初始位姿或检测参数，可使用环境变量，例如：

```bash
SPAWN_X=-2.9 SPAWN_YAW=0.35 CONF_THRESHOLD=0.1 bash tools/run_tracking_experiment.sh baseline 30
```

如需在不修改控制源码的前提下临时提高前向速度，可覆盖 `v0` 和 `vmin`，例如：

```bash
V0=0.30 VMIN=0.15 STARTUP_WAIT=25 CENTER_READY_TIMEOUT=20 SKIP_BUILD=1 \
bash tools/run_tracking_experiment.sh baseline 60
```

## 输出目录

每次运行会生成：

```text
experiment_records/<实验名>_<时间戳>/
```

目录中包含：

```text
params.txt
cmd_vel.csv
seam_center.csv
clock.csv
center_error_curve_clean.png
cmd_vel_curve_clean.png
valid_flag_curve_clean.png
summary.txt
roslaunch.log
recorder.log
```

脚本当前采用“两段启动”方式：先启动 Gazebo 和 YOLO，等待场景稳定后检查 `/seam_center` 是否出现有效检测；随后启动记录器，再启动控制器。这样可以尽量避免等待阶段车辆已经转丢目标，也能记录控制器启动后的完整速度响应。

## 图像含义

- `center_error_curve_clean.png`：目标中心归一化偏差曲线。检测无效时不计算误差，避免把 `center_x=-1` 画成异常大误差。
- `cmd_vel_curve_clean.png`：速度指令曲线，包括 `linear.x / vx`、`linear.y / vy` 和 `angular.z / wz`。
- `valid_flag_curve_clean.png`：检测有效标志曲线，1 表示检测有效，0 表示检测无效。

默认三张图使用 `wall_time` 作为横坐标。如果横坐标仍明显短于 30 秒，应优先查看 `recorder.log` 是否有异常退出。

## 参数选择指标

重点查看 `summary.txt`：

- `mean_abs_error_valid`：有效检测阶段平均绝对误差，越小越好。
- `tail_mean_abs_error_valid`：有效误差最后 30% 的平均绝对值，用于观察后段残余偏差，越小越好。
- `max_abs_error_valid`：有效检测阶段最大绝对误差，不宜过大。
- `angular_z_max_abs`：最大角速度绝对值，不宜过大。
- `angular_sign_changes`：角速度正负切换次数，不宜过多，过多可能说明振荡。
- `linear_y_max_abs`：当前上层控制应接近 0，用于确认未启用横向速度纠偏。
- `stop_after_invalid`：检测无效后速度是否接近 0，理想情况为 `yes`；如果没有无效阶段则为 `no_invalid`。
- `duration_center_axis`、`duration_cmd_vel_axis`：当前绘图时间轴下的数据持续时间，默认应接近 30 秒。
- `clock_ros_duration`：Gazebo 仿真时间实际推进量。
- `sim_realtime_factor_est`：仿真时间与真实时间的比值，明显小于 1 表示虚拟机仿真较慢。

最终参数不只看误差最小，还要看速度是否平稳、角速度是否频繁变号、检测无效后是否停止。

建议优先比较这四组温和参数：

- `baseline`：原始基准参数。
- `opt_kp06`：小幅提高角速度响应，整体仍偏稳。
- `opt_kp065`：在 `opt_kp06` 基础上略增强修正能力，但避免过激转向。
- `slow_v016`：降低前向速度，观察残余偏差是否进一步收敛。

## 当前控制边界

当前焊缝跟踪上层控制仍为：

```text
u = [vx, 0, wz]^T
```

`linear.y` 保持为 0。脚本中的统计结果不能写成已经启用 `vy` 横向纠偏，也不能写成上层控制读取里程计闭环。
