# Seam-Tracking Robot: YOLOv5 Vision + Original ROS1 Controller

This repository is a ROS1/catkin undergraduate seam-tracking robot project.

Current primary runtime chain:

```text
/image_raw
-> robot_vision/scripts/yolo_seam_detector.py
-> /seam_center
-> robot_vision/scripts/line_detector.py
-> /cmd_vel
-> optional base_control / simulation chassis
```

The current main vision front-end is YOLOv5. The original HSV line-following path is kept as a legacy/backup path, and the old `yolo/` directory is kept as historical experiment material. They are not the recommended main entry for the current system.

## Repository Layout

- ROS1 workspace: `catkin_ws/`
- ROS1 packages: `catkin_ws/src/`
- Main vision/control package: `catkin_ws/src/robot_vision/`
- Chassis bridge package: `catkin_ws/src/base_control/`
- Current YOLOv5 codebase: `yolov5/`
- Current model weight location: `models/seam_best.pt`
- Legacy YOLO/Ultralytics experiments: `yolo/`
- Robot description/simulation support: `catkin_ws/src/nanoomni_description/`

## Main Launch

Use this as the primary entry:

```text
catkin_ws/src/robot_vision/launch/seam_tracking.launch
```

It starts:

- fake camera or real `uvc_camera` image input
- YOLOv5 seam detector node
- original `line_detector.py` in external-center control mode
- optional `base_control` chassis bridge when `run_base_control:=true`

It does not start the old HSV visual front-end.

## ROS Interfaces

| Topic | Type | Meaning |
| --- | --- | --- |
| `/image_raw` | `sensor_msgs/Image` | Camera or fake-camera image input |
| `/seam_center` | `geometry_msgs/Point` | YOLOv5 detection result adapted for the original controller |
| `/result_image` | `sensor_msgs/Image` | Debug image with bbox, target center, and image center line |
| `/cmd_vel` | `geometry_msgs/Twist` | Control output for chassis or simulation |

`/seam_center` fields:

| Field | Meaning |
| --- | --- |
| `x` | `center_x`, the detection bbox center x coordinate |
| `y` | `image_width`, the input image width |
| `z` | `valid_flag`, `1.0` means valid detection, `0.0` means no valid detection |

The bbox center is computed as:

```text
center_x = (x1 + x2) / 2
```

The original controller uses:

```text
reference_x = image_width / 2
```

## Build On Ubuntu 18.04 + ROS Melodic

Run `catkin_make` from the catkin workspace, not from the repository root.

```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
```

## Runtime Dependencies

The YOLOv5 ROS adapter is a Python3 node. In the target ROS Melodic environment, Python3 must be able to import:

- `rospy`
- `cv_bridge`
- `cv2`
- `torch`
- YOLOv5 modules from `~/bsnew/yolov5`

Quick checks:

```bash
python3 -c "import cv2; print(cv2.__version__)"
python3 -c "import torch; print(torch.__version__)"
python3 -c "import os, sys; sys.path.insert(0, os.path.expanduser('~/bsnew/yolov5')); from models.experimental import attempt_load; print('yolov5 import ok')"
ls -lh ~/bsnew/models/seam_best.pt
```

## Run Without Chassis First

Use fake-camera mode first. This checks YOLOv5 loading, detection output, `/seam_center`, and `/cmd_vel` without moving hardware.

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

The launch file has the same default `model_path` and `yolov5_repo_path`, so the explicit arguments above are mainly for clarity.

## Run Continuous Video Test

After a single-image test works, use `video_path` to make `fake_camera.py` loop over a video file and publish frames to `/image_raw`.

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

When `video_path` is empty, fake-camera mode still publishes the single image from `fake_image_path`. The default video/image publish rate is `fps:=10`; override it if needed.

## Run With Real Camera, Still Without Chassis

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

Set `BASE_TYPE` and `CAMERA_TYPE` if your camera launch requires them:

```bash
export BASE_TYPE=NanoCar
export CAMERA_TYPE=csi72
```

## Run With Chassis

Only do this after fake-camera and real-camera detection are verified.

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

Keep the robot lifted or ready to stop during the first hardware test.

## Debug Commands

Open new terminals and source the workspace first:

```bash
source /opt/ros/melodic/setup.bash
source ~/bsnew/catkin_ws/devel/setup.bash
```

View YOLO-adapted center output:

```bash
rostopic echo /seam_center
```

View controller output:

```bash
rostopic echo /cmd_vel
```

View debug image:

```bash
rqt_image_view /result_image
```

Check publishers/subscribers:

```bash
rostopic info /seam_center
rostopic info /cmd_vel
rqt_graph
```

## Safety Behavior

- If YOLOv5 detects a valid seam target, `/seam_center.z` is `1.0`.
- If no valid target is detected, `/seam_center.z` is `0.0`.
- In external-center mode, `line_detector.py` publishes zero `Twist` when the center is invalid.
- It also publishes zero `Twist` if `/seam_center` times out.

## Legacy Paths

- `catkin_ws/src/robot_vision/launch/line_follow.launch`: legacy HSV line-following entry.
- `catkin_ws/src/robot_vision/config/line_hsv.cfg`: HSV threshold dynamic reconfigure support.
- `yolo/`: old Ultralytics/YOLO experiment code and frame materials.

These are preserved for reference and backup. The recommended main system is `seam_tracking.launch` with YOLOv5.
