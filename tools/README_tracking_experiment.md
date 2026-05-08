# Gazebo 焊缝跟踪实验脚本说明

本目录提供 Gazebo 焊缝跟踪实验脚本，用于在 Ubuntu 18.04 + ROS Melodic 虚拟机中自动记录 `/cmd_vel`、`/seam_center` 和 `/clock`，生成中心偏差、速度指令、检测有效标志曲线，并输出统计结果。

当前提供两个实验脚本：

```bash
tools/run_tracking_experiment.sh
tools/run_tracking_experiment_mid_straight.sh
```

其中 `run_tracking_experiment.sh` 保留旧半宽纹理场景；`run_tracking_experiment_mid_straight.sh` 使用中段直线场景。两者的参数分组和输出格式保持一致。

旧脚本默认场景为：

```text
world_name=/home/bn/bsnew/catkin_ws/src/nanoomni_description/worlds/seam_world_texture_half_width.world
```

mid-straight 脚本默认场景为：

```text
world_name=/home/bn/bsnew/catkin_ws/src/nanoomni_description/worlds/seam_world_texture_half_width_mid_straight.world
```

两者默认权重和运行设置为：

```text
model_path=/home/bn/bsnew/models/best_curve_bg_thin_real.pt
yolov5_repo_path=/home/bn/bsnew/yolov5
spawn_x=-2.9
spawn_y=0.0
spawn_yaw=0.35
conf_threshold=0.1
target_class_id=-1
device=cpu
publish_result_image=true
```

脚本采用“两段启动”方式：先启动 Gazebo 和 YOLO，等待系统稳定并检查 `/seam_center`，再启动记录器和控制器。这样可以尽量减少启动阶段数据对实验曲线的影响。

## 方案 A：参数对比实验

方案 A 用于在相同前向速度约束下比较控制参数影响。四组实验统一采用：

```text
v0=0.30
vmin=0.15
record_seconds=240
```

四组差异主要体现在 `Kp`、`Ki`、`dead_zone`、`integral_separation`、`i_max`、`alpha` 和 `angular_threshold`，不把前向速度差异作为影响因素。

```bash
cd /home/bn/bsnew
SKIP_BUILD=1 bash tools/run_tracking_experiment_mid_straight.sh baseline 240
SKIP_BUILD=1 bash tools/run_tracking_experiment_mid_straight.sh opt_kp06 240
SKIP_BUILD=1 bash tools/run_tracking_experiment_mid_straight.sh opt_kp065 240
SKIP_BUILD=1 bash tools/run_tracking_experiment_mid_straight.sh slow_v016 240
```

旧脚本也支持同一套参数，建议在虚拟机里分开逐条运行：

```bash
cd /home/bn/bsnew
SKIP_BUILD=1 bash tools/run_tracking_experiment.sh baseline 240
```

```bash
cd /home/bn/bsnew
SKIP_BUILD=1 bash tools/run_tracking_experiment.sh opt_kp06 240
```

```bash
cd /home/bn/bsnew
SKIP_BUILD=1 bash tools/run_tracking_experiment.sh opt_kp065 240
```

```bash
cd /home/bn/bsnew
SKIP_BUILD=1 bash tools/run_tracking_experiment.sh slow_v016 240
```

参数设置如下：

```text
baseline:  Kp=0.50, Ki=0.020, dead_zone=0.050, integral_separation=0.30, i_max=0.30, alpha=0.50, angular_threshold=0.20
opt_kp06:  Kp=0.60, Ki=0.025, dead_zone=0.045, integral_separation=0.30, i_max=0.35, alpha=0.60, angular_threshold=0.20
opt_kp065: Kp=0.65, Ki=0.030, dead_zone=0.045, integral_separation=0.30, i_max=0.35, alpha=0.65, angular_threshold=0.20
slow_v016: Kp=0.60, Ki=0.025, dead_zone=0.045, integral_separation=0.30, i_max=0.35, alpha=0.60, angular_threshold=0.20
```

说明：`slow_v016` 保留旧实验名，但在方案 A 中同样使用 `v0=0.30`、`vmin=0.15`。论文中可说明为“为排除前向速度差异影响，参数对比实验统一采用相同速度约束”。

## 方案 B：速度影响实验

方案 B 用于固定较优控制参数，只比较不同前向速度约束对跟踪误差、速度平稳性和检测稳定性的影响。三组均采用：

```text
Kp=0.65
Ki=0.03
dead_zone=0.045
integral_separation=0.30
i_max=0.35
alpha=0.65
angular_threshold=0.2
```

速度与记录时间按方案 A 的 240 秒基准换算：

```text
speed_low:  v0=0.20, vmin=0.10, record_seconds=360
speed_mid:  v0=0.25, vmin=0.12, record_seconds=288
speed_high: v0=0.30, vmin=0.15, record_seconds=240
```

运行命令：

```bash
cd /home/bn/bsnew
SKIP_BUILD=1 bash tools/run_tracking_experiment_mid_straight.sh speed_low
SKIP_BUILD=1 bash tools/run_tracking_experiment_mid_straight.sh speed_mid
SKIP_BUILD=1 bash tools/run_tracking_experiment_mid_straight.sh speed_high
```

旧脚本同样支持方案 B，也建议分开逐条运行：

```bash
cd /home/bn/bsnew
SKIP_BUILD=1 bash tools/run_tracking_experiment.sh speed_low
```

```bash
cd /home/bn/bsnew
SKIP_BUILD=1 bash tools/run_tracking_experiment.sh speed_mid
```

```bash
cd /home/bn/bsnew
SKIP_BUILD=1 bash tools/run_tracking_experiment.sh speed_high
```

如果需要临时指定记录时长，也可以在实验名后添加秒数，例如：

```bash
SKIP_BUILD=1 bash tools/run_tracking_experiment_mid_straight.sh speed_mid 300
```

## 查看 YOLO 识别画面

脚本默认保持 `publish_result_image=true`，因此运行过程中可以另开终端查看 YOLO 结果图。脚本不会自动打开 GUI。

```bash
source /opt/ros/melodic/setup.bash
cd /home/bn/bsnew/catkin_ws
source devel/setup.bash
rqt_image_view /result_image
```

如果虚拟机性能不足，可临时关闭结果图发布：

```bash
PUBLISH_RESULT_IMAGE=false SKIP_BUILD=1 bash tools/run_tracking_experiment_mid_straight.sh baseline 240
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

`params.txt` 会记录实验名、实验类型、记录时间、控制参数、速度参数、场景路径、权重路径和 `publish_result_image` 设置。方案 A 的 `experiment_type` 为 `parameter_compare`，方案 B 的 `experiment_type` 为 `speed_compare`。

## 结果判断

重点查看 `summary.txt`：

- `mean_abs_error_valid`：有效检测阶段平均绝对误差，越小越好。
- `tail_mean_abs_error_valid`：有效误差最后 30% 的平均绝对值，用于观察后段残余偏差，越小越好。
- `max_abs_error_valid`：有效检测阶段最大绝对误差，不宜过大。
- `angular_z_max_abs`：最大角速度绝对值，不宜过大。
- `angular_sign_changes`：角速度正负切换次数，不宜过多，过多可能说明振荡。
- `linear_y_max_abs`：当前上层控制应接近 0，用于确认未启用横向速度纠偏。
- `stop_after_invalid`：检测无效后速度是否接近 0，理想情况为 `yes`；如果没有无效阶段则为 `no_invalid`。
- `clock_ros_duration`：Gazebo 仿真时间实际推进量。
- `sim_realtime_factor_est`：仿真时间与真实时间的比值，明显小于 1 表示虚拟机仿真较慢。

最终参数不只看误差最小，还要综合观察角速度是否平稳、检测是否连续有效、末段误差是否收敛以及目标丢失后是否停止。

## 当前控制边界

当前焊缝跟踪上层控制仍为：

```text
u = [vx, 0, wz]^T
```

`linear.y` 保持为 0。实验曲线和统计结果不能写成已经启用 `vy` 横向纠偏，也不能写成上层控制读取里程计闭环。
