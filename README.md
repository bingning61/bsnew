# Seam-Tracking Robot (YOLO + Original ROS1 Controller)

## Project Purpose
This project merges:
- YOLO seam detection (perception front-end)
- Existing ROS1 line-following control pipeline (control back-end)

Final runtime flow:

`image -> YOLO bbox -> bbox center x -> original deviation controller -> cmd_vel -> chassis`

The original controller logic in `robot_vision/scripts/line_detector.py` is preserved.  
Only a thin adapter mode was added so it can consume YOLO center input.

## Module Structure
- ROS1 workspace: `catkin_ws/`
- ROS1 packages: `catkin_ws/src/`
- Perception + controller package: `catkin_ws/src/robot_vision/`
- Chassis/cmd_vel bridge: `catkin_ws/src/base_control/`
- YOLO codebase: `yolo/`

Primary integrated launch entry:
- `catkin_ws/src/robot_vision/launch/seam_tracking.launch`

## ROS Interfaces
- Camera input (default): `/image_raw` (`sensor_msgs/Image`)
- YOLO center output: `/seam_center` (`geometry_msgs/Point`)
  - `x`: bbox center x (pixel)
  - `y`: image width (pixel)
  - `z`: valid flag (`1.0` valid, `0.0` invalid)
- Control output: `cmd_vel` (`geometry_msgs/Twist`)
- Debug image: `/result_image` (`sensor_msgs/Image`)

## Required Runtime Parameters
- `model_path`: YOLO weight file path (`.pt`)  
  This must be provided when launching.
- YOLO node runtime: `python3 + ultralytics + torch + cv_bridge + rospy` must be available in the ROS runtime environment.

## Build (Ubuntu 18.04 ROS1 Catkin)
Generic template:
```bash
cd ~/bsnew/catkin_ws
source /opt/ros/<ros1_distro>/setup.bash
catkin_make
source devel/setup.bash
```

Example (`melodic`):
```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
catkin_make
source devel/setup.bash
```

## Run (Primary Integrated Path)
### 1) Real camera + full robot pipeline (includes base_control)
```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash
roslaunch robot_vision seam_tracking.launch \
  run_base_control:=true \
  model_path:=../yolo/runs/train/exp17/weights/best.pt
```

### 2) Perception/control debug without chassis (fake camera image)
```bash
cd ~/bsnew/catkin_ws
source /opt/ros/melodic/setup.bash
source devel/setup.bash
roslaunch robot_vision seam_tracking.launch \
  run_base_control:=false \
  use_fake_camera:=true \
  fake_image_path:=$(rospack find robot_vision)/data/bingda.png \
  model_path:=../yolo/runs/train/exp17/weights/best.pt
```

## Key Launch Args (`seam_tracking.launch`)
- `run_base_control` (default `false`): include chassis bridge
- `use_fake_camera` (default `false`): use static image publisher
- `model_path` (default empty): YOLO weight path
- `yolo_repo_path` (default `$(find robot_vision)/../../../../yolo`)
- `image_topic` (default `/image_raw`)
- `center_topic` (default `/seam_center`)
- `cmd_vel_topic` (default `cmd_vel`)
- `conf_threshold` (default `0.25`)
- `target_class_id` (default `-1`, means highest-confidence class)
- `external_center_timeout` (default `0.5`, seconds before safe stop)

## Safety Behavior
- If YOLO detection is invalid/missing, adapter publishes invalid center (`z=0`).
- Controller adapter mode immediately publishes zero `cmd_vel`.
- If center messages timeout, controller adapter mode also publishes zero `cmd_vel`.

## Architecture Notes
- Original `twist_calculate()` control law is unchanged.
- Original HSV path remains available (legacy `line_follow.launch`).
- New YOLO node is a front-end replacement for line-center extraction only.
