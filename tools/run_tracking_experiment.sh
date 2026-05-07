#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/home/bn/bsnew"
ROS_SETUP="/opt/ros/melodic/setup.bash"
CATKIN_WS="${REPO_ROOT}/catkin_ws"
MODEL_PATH="${REPO_ROOT}/models/best_curve_bg_thin_real.pt"
YOLOV5_REPO="${REPO_ROOT}/yolov5"
WORLD_PATH="${CATKIN_WS}/src/nanoomni_description/worlds/seam_world_texture_half_width.world"
OUT_ROOT="${REPO_ROOT}/experiment_records"
STARTUP_WAIT="${STARTUP_WAIT:-12}"
SKIP_BUILD="${SKIP_BUILD:-0}"
SPAWN_X="${SPAWN_X:--2.9}"
SPAWN_Y="${SPAWN_Y:-0.0}"
SPAWN_YAW="${SPAWN_YAW:-0.35}"
CONF_THRESHOLD="${CONF_THRESHOLD:-0.1}"
TARGET_CLASS_ID="${TARGET_CLASS_ID:--1}"

EXPERIMENT_NAME="${1:-baseline}"
RECORD_SECONDS="${2:-30}"

Kp=""
Ki=""
dead_zone=""
integral_separation=""
i_max=""
v0=""
vmin=""
alpha=""
angular_threshold=""

usage() {
    cat <<'EOF'
Usage:
  bash tools/run_tracking_experiment.sh <baseline|opt_kp07|opt_kp08|slow_v016> [record_seconds]

Examples:
  cd /home/bn/bsnew
  bash tools/run_tracking_experiment.sh baseline 30
  bash tools/run_tracking_experiment.sh opt_kp07 30
  bash tools/run_tracking_experiment.sh opt_kp08 30
  bash tools/run_tracking_experiment.sh slow_v016 30

Environment:
  STARTUP_WAIT=12   seconds to wait after roslaunch before recording
  SKIP_BUILD=1      skip catkin_make
EOF
}

set_params() {
    case "$EXPERIMENT_NAME" in
        baseline)
            Kp="0.5"; Ki="0.02"; dead_zone="0.05"; integral_separation="0.30"
            i_max="0.3"; v0="0.2"; vmin="0.1"; alpha="0.5"; angular_threshold="0.2"
            ;;
        opt_kp07)
            Kp="0.7"; Ki="0.04"; dead_zone="0.04"; integral_separation="0.30"
            i_max="0.4"; v0="0.18"; vmin="0.08"; alpha="0.7"; angular_threshold="0.2"
            ;;
        opt_kp08)
            Kp="0.8"; Ki="0.04"; dead_zone="0.04"; integral_separation="0.30"
            i_max="0.4"; v0="0.18"; vmin="0.08"; alpha="0.7"; angular_threshold="0.2"
            ;;
        slow_v016)
            Kp="0.7"; Ki="0.04"; dead_zone="0.04"; integral_separation="0.30"
            i_max="0.4"; v0="0.16"; vmin="0.08"; alpha="0.7"; angular_threshold="0.2"
            ;;
        -h|--help|help)
            usage
            exit 0
            ;;
        *)
            echo "Unknown experiment: ${EXPERIMENT_NAME}" >&2
            usage >&2
            exit 2
            ;;
    esac
}

is_positive_int() {
    case "$1" in
        ''|*[!0-9]*) return 1 ;;
        *) [ "$1" -gt 0 ] ;;
    esac
}

check_inputs() {
    if [ ! -d "$REPO_ROOT" ]; then
        echo "Repository not found: ${REPO_ROOT}" >&2
        exit 1
    fi
    cd "$REPO_ROOT"

    if [ ! -f "$ROS_SETUP" ]; then
        echo "ROS Melodic setup not found: ${ROS_SETUP}" >&2
        echo "Run this script inside the Ubuntu 18.04 + ROS Melodic virtual machine." >&2
        exit 1
    fi
    if [ ! -f "$MODEL_PATH" ]; then
        echo "Model weight not found: ${MODEL_PATH}" >&2
        exit 1
    fi
    if [ ! -f "$WORLD_PATH" ]; then
        echo "Gazebo world not found: ${WORLD_PATH}" >&2
        exit 1
    fi
    if [ ! -d "$YOLOV5_REPO" ]; then
        echo "YOLOv5 repository not found: ${YOLOV5_REPO}" >&2
        exit 1
    fi
    if ! is_positive_int "$RECORD_SECONDS"; then
        echo "record_seconds must be a positive integer, got: ${RECORD_SECONDS}" >&2
        exit 2
    fi
    if ! is_positive_int "$STARTUP_WAIT"; then
        echo "STARTUP_WAIT must be a positive integer, got: ${STARTUP_WAIT}" >&2
        exit 2
    fi
}

PIDS_TO_CLEAN=""
LAUNCH_PID=""
CMD_PID=""
CENTER_PID=""

cleanup() {
    set +e
    for pid in $PIDS_TO_CLEAN; do
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null
        fi
    done
    sleep 2
    for pid in $PIDS_TO_CLEAN; do
        if kill -0 "$pid" 2>/dev/null; then
            kill -9 "$pid" 2>/dev/null
        fi
    done
}

trap cleanup EXIT INT TERM

main() {
    set_params
    check_inputs

    TIMESTAMP="$(date +%Y%m%d_%H%M%S)"
    OUT_DIR="${OUT_ROOT}/${EXPERIMENT_NAME}_${TIMESTAMP}"
    mkdir -p "$OUT_DIR"

    cat > "${OUT_DIR}/params.txt" <<EOF
experiment_name=${EXPERIMENT_NAME}
record_seconds=${RECORD_SECONDS}
startup_wait=${STARTUP_WAIT}
model_path=${MODEL_PATH}
yolov5_repo_path=${YOLOV5_REPO}
world_name=${WORLD_PATH}
spawn_x=${SPAWN_X}
spawn_y=${SPAWN_Y}
spawn_yaw=${SPAWN_YAW}
conf_threshold=${CONF_THRESHOLD}
target_class_id=${TARGET_CLASS_ID}
control_mode=vx_plus_wz_linear_y_zero
Kp=${Kp}
Ki=${Ki}
dead_zone=${dead_zone}
integral_separation=${integral_separation}
i_max=${i_max}
v0=${v0}
vmin=${vmin}
alpha=${alpha}
angular_threshold=${angular_threshold}
external_center_timeout=0.5
EOF

    echo "Experiment: ${EXPERIMENT_NAME}"
    echo "Output dir: ${OUT_DIR}"

    # shellcheck source=/dev/null
    source "$ROS_SETUP"
    cd "$CATKIN_WS"

    if [ "$SKIP_BUILD" != "1" ]; then
        catkin_make
    else
        echo "SKIP_BUILD=1, skip catkin_make"
    fi

    if [ -f "${CATKIN_WS}/devel/setup.bash" ]; then
        # shellcheck source=/dev/null
        source "${CATKIN_WS}/devel/setup.bash"
    else
        echo "Warning: ${CATKIN_WS}/devel/setup.bash not found. Continuing after catkin_make attempt." >&2
    fi

    roslaunch robot_vision gazebo_seam_tracking.launch \
        world_name:="$WORLD_PATH" \
        spawn_x:="$SPAWN_X" \
        spawn_y:="$SPAWN_Y" \
        spawn_yaw:="$SPAWN_YAW" \
        model_path:="$MODEL_PATH" \
        yolov5_repo_path:="$YOLOV5_REPO" \
        device:=cpu \
        conf_threshold:="$CONF_THRESHOLD" \
        target_class_id:="$TARGET_CLASS_ID" \
        Kp:="$Kp" \
        Ki:="$Ki" \
        dead_zone:="$dead_zone" \
        integral_separation:="$integral_separation" \
        i_max:="$i_max" \
        v0:="$v0" \
        vmin:="$vmin" \
        alpha:="$alpha" \
        angular_threshold:="$angular_threshold" \
        > "${OUT_DIR}/roslaunch.log" 2>&1 &
    LAUNCH_PID=$!
    PIDS_TO_CLEAN="${PIDS_TO_CLEAN} ${LAUNCH_PID}"

    echo "roslaunch pid: ${LAUNCH_PID}"
    echo "Waiting ${STARTUP_WAIT}s for Gazebo, YOLO, and controller startup..."
    sleep "$STARTUP_WAIT"

    rostopic echo -p /cmd_vel > "${OUT_DIR}/cmd_vel.csv" &
    CMD_PID=$!
    PIDS_TO_CLEAN="${PIDS_TO_CLEAN} ${CMD_PID}"

    rostopic echo -p /seam_center > "${OUT_DIR}/seam_center.csv" &
    CENTER_PID=$!
    PIDS_TO_CLEAN="${PIDS_TO_CLEAN} ${CENTER_PID}"

    echo "Recording /cmd_vel and /seam_center for ${RECORD_SECONDS}s..."
    sleep "$RECORD_SECONDS"

    cleanup
    trap - EXIT INT TERM

    cd "$REPO_ROOT"
    python3 tools/plot_tracking_curves.py \
        --cmd-vel "${OUT_DIR}/cmd_vel.csv" \
        --seam-center "${OUT_DIR}/seam_center.csv" \
        --out-dir "$OUT_DIR" \
        --name "$EXPERIMENT_NAME"

    echo
    echo "Experiment finished."
    echo "Output dir: ${OUT_DIR}"
    echo "Summary:"
    sed -n '1,120p' "${OUT_DIR}/summary.txt"
}

main "$@"
