# Gazebo 焊缝跟踪参数实验脚本

本目录提供一键 Gazebo 参数实验脚本，用于记录 `/cmd_vel` 和 `/seam_center`，生成论文曲线并输出统计结果。脚本面向 Ubuntu 18.04 + ROS Melodic 虚拟机。

## 一键运行

```bash
cd /home/bn/bsnew
bash tools/run_tracking_experiment.sh baseline 30
bash tools/run_tracking_experiment.sh opt_kp07 30
bash tools/run_tracking_experiment.sh opt_kp08 30
bash tools/run_tracking_experiment.sh slow_v016 30
```

第二个参数为记录时长，单位为秒，默认 30 秒。默认权重为：

```text
/home/bn/bsnew/models/best_curve_bg_thin_finetune.pt
```

默认 YOLOv5 路径为：

```text
/home/bn/bsnew/yolov5
```

如果不想每次运行前编译，可使用：

```bash
SKIP_BUILD=1 bash tools/run_tracking_experiment.sh opt_kp07 30
```

如果 Gazebo 和 YOLO 启动较慢，可延长等待时间：

```bash
STARTUP_WAIT=20 bash tools/run_tracking_experiment.sh opt_kp07 30
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
center_error_curve_clean.png
cmd_vel_curve_clean.png
valid_flag_curve_clean.png
summary.txt
roslaunch.log
```

## 图像含义

- `center_error_curve_clean.png`：目标中心归一化偏差曲线。检测无效时不计算误差，避免把 `center_x=-1` 画成异常大误差。
- `cmd_vel_curve_clean.png`：速度指令曲线，包括 `linear.x / vx`、`linear.y / vy` 和 `angular.z / wz`。
- `valid_flag_curve_clean.png`：检测有效标志曲线，1 表示检测有效，0 表示检测无效。

## 参数选择指标

重点查看 `summary.txt`：

- `mean_abs_error_valid`：有效检测阶段平均绝对误差，越小越好。
- `tail_mean_abs_error_valid`：有效误差最后 30% 的平均绝对值，用于观察后段残余偏差，越小越好。
- `max_abs_error_valid`：有效检测阶段最大绝对误差，不宜过大。
- `angular_z_max_abs`：最大角速度绝对值，不宜过大。
- `angular_sign_changes`：角速度正负切换次数，不宜过多，过多可能说明振荡。
- `linear_y_max_abs`：当前上层控制应接近 0，用于确认未启用横向速度纠偏。
- `stop_after_invalid`：检测无效后速度是否接近 0，理想情况为 `yes`；如果没有无效阶段则为 `no_invalid`。

最终参数不只看误差最小，还要看速度是否平稳、角速度是否频繁变号、检测无效后是否停止。

## 当前控制边界

当前焊缝跟踪上层控制仍为：

```text
u = [vx, 0, wz]^T
```

`linear.y` 保持为 0。脚本中的统计结果不能写成已经启用 `vy` 横向纠偏，也不能写成上层控制读取里程计闭环。
