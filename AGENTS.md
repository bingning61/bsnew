# Project instructions for Codex

## Project objective
This repository contains two existing systems that must be merged into one complete runnable undergraduate graduation project:

1. A YOLO-based vision detection system.
2. An existing ROS1 robot line-following / motion-control system.

The final target is:
A seam-tracking robot car system based on YOLO seam detection and the existing center-deviation control pipeline.

## Actual repository layout
Repository root: bsnew/
ROS1 workspace root: bsnew/catkin_ws/
ROS1 packages are under: bsnew/catkin_ws/src/
YOLO code is under: bsnew/yolo/
Reference media files:
- bsnew/原视频.mp4
- bsnew/识别视频.mp4

Do not modify the mp4 files unless explicitly asked.

## Runtime and build environment
This is a ROS1 project.
The final runtime environment is Ubuntu 18.04 in a virtual machine.
You must work according to ROS1/catkin conventions.

Strict requirements:
- do NOT convert anything to ROS2
- do NOT introduce ROS2 APIs
- do NOT introduce ament
- do NOT introduce colcon
- do NOT rewrite launch/config/build structure into ROS2 style

Treat this repository as a ROS1/catkin project.

## Repository inspection requirement
Before making edits, first locate the relevant ROS1 package(s) under bsnew/catkin_ws/src/.
Do not assume package.xml or CMakeLists.txt are at the repository root.

For each target ROS1 package, inspect:
- package.xml
- CMakeLists.txt
- launch/
- config/
- src/
- include/

Also inspect bsnew/yolo/ to understand how the YOLO code is currently organized and invoked.

## Workspace and path rules
Treat bsnew/catkin_ws/ as the catkin workspace root.
Do NOT run catkin_make from bsnew/.
Run catkin_make from bsnew/catkin_ws/.

Do not hardcode current-machine absolute paths.
Use ROS package-relative paths, launch arguments, config parameters, or repo-relative portable paths where possible.

Do NOT generate or depend on current-machine build artifacts.
Do NOT rely on build/, devel/, or install/ outputs from another Ubuntu version, another ROS version, or the current machine.
All modifications must remain source-level and portable back to Ubuntu 18.04 + ROS1 + catkin.

## Highest-priority constraint
The original control code is already relatively complete and stable.
Treat the original controller, cmd_vel pipeline, chassis interface, and motion logic as authoritative and stable.
Do NOT rewrite or heavily refactor the control code unless a small change is absolutely required for build or runtime correctness.

Preferred rule:
- keep the original controller unchanged if possible
- keep the original cmd_vel publishing path unchanged if possible
- keep original launch/topic names unchanged if possible
- if a controller change is unavoidable, make the smallest possible edit and document it clearly

## Preferred integration strategy
Use a compatibility-adapter strategy rather than a controller rewrite.

This means:
- YOLO becomes the new perception front-end
- the old HSV line-center extraction is replaced or bypassed
- a new adapter layer converts YOLO detection output into the same or very similar input expected by the original controller
- the existing controller continues to compute deviation and publish motion commands with minimal or zero logic changes

Preferred data flow:
camera image
-> YOLO seam detection
-> bounding box center extraction
-> adapter output compatible with old controller input
-> existing controller
-> cmd_vel
-> chassis / base control

## Implementation preference
Strongly prefer one of these two solutions:

Option A (most preferred):
- keep the original controller node almost unchanged
- add a small ROS1-compatible adapter node or helper module that publishes the center position and image width in the format expected by the old controller

Option B:
- if the old controller cannot be reused without a tiny patch, modify only the input source wiring while preserving the original control law and output behavior

Do NOT replace a stable controller with a brand-new controller unless reuse is truly impossible.

## Simplicity requirement
This is an undergraduate project with limited time and limited implementation ability.
Optimize for:
- minimal code changes
- low regression risk
- easy debugging
- end-to-end runnability
- thesis-friendly explanation
- practical completion

Do NOT optimize for:
- industrial-grade accuracy
- advanced architecture
- segmentation migration
- tracking-based redesign
- state-machine-heavy redesign
- calibration-heavy redesign
- novelty for novelty's sake

## Functional goal
The final system must:
- read image input
- detect the seam target with YOLO
- get the detection bounding-box center
- use that center as the replacement for the old line center
- compute deviation relative to image center
- publish cmd_vel through the existing control pipeline
- safely stop when no valid detection exists

## Control preservation rule
Preserve the original control behavior as much as possible.

Preferred formula if an adapter or minimal patch is needed:
- bbox_center_x = (x1 + x2) / 2
- image_center_x = image_width / 2
- error = bbox_center_x - image_center_x

If the old controller already implements deviation-based steering, reuse it instead of replacing it.

## Safety rule
If detection is invalid or missing:
- publish zero velocity, or
- trigger the existing safe stop behavior

Do not invent aggressive fallback motion.

## Required work sequence
1. Inspect the repository structure fully.
2. Read and understand:
   - relevant package.xml
   - relevant CMakeLists.txt
   - launch/
   - config/
   - src/
   - include/
   - bsnew/yolo/
3. Identify:
   - YOLO-related files
   - original controller files
   - launch/run files
   - dependencies/config files
4. Decide the minimum-change integration plan.
5. Implement the integration end-to-end.
6. Update the runnable ROS1/catkin entry point only if needed.
7. Validate the result as much as possible without depending on incompatible local build artifacts.
8. Fix integration errors found during validation.
9. Update README with exact ROS1/catkin run steps and architecture explanation.

## Required final deliverables
By the end of the task, provide:
1. working merged source code
2. exact files changed
3. why each file was changed
4. exact commands to build on Ubuntu 18.04 with catkin_make
5. exact roslaunch command(s) to run on Ubuntu 18.04
6. updated launch/run instructions
7. short explanation of the final architecture
8. short explanation of how much of the original controller was preserved
9. honest note about what still requires hardware testing

## Final reporting requirement
After modifications, explicitly report:
- which files were changed
- why each file was changed
- how to return to Ubuntu 18.04 and run:
  - cd ~/bsnew/catkin_ws
  - source /opt/ros/<ros1_distro>/setup.bash
  - catkin_make
  - source devel/setup.bash
  - roslaunch <package_name> <launch_file>.launch

## Review rule
Before finishing:
- review the diff
- remove dead code if it is clearly obsolete
- keep old files if removing them would create risk
- clearly mark the new primary entry path
## Additional package in this repository
There is an additional ROS1 package under:
bsnew/catkin_ws/src/nanoomni_description/

This package is a robot description / simulation-support package.
It may contain URDF/Xacro, RViz, Gazebo, meshes, robot model descriptions, and simulation launch files.

Rules:
- do not treat nanoomni_description as the primary seam-tracking control package unless the code clearly shows it is part of the main runtime path
- inspect it and document its role
- preserve it
- if it is only used for simulation/description, place it under system implementation / simulation support, not as the main control method
- do not refactor it unless the task explicitly requires simulation-related fixes