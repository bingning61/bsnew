#!/usr/bin/env bash
set -euo pipefail

REPO_ROOT="/home/bn/bsnew"
ROS_SETUP="/opt/ros/melodic/setup.bash"
CATKIN_WS="${REPO_ROOT}/catkin_ws"
MODEL_PATH="${REPO_ROOT}/models/best_curve_bg_thin_real.pt"
YOLOV5_REPO="${REPO_ROOT}/yolov5"
WORLD_PATH="${CATKIN_WS}/src/nanoomni_description/worlds/seam_world_texture_half_width.world"
OUT_ROOT="${REPO_ROOT}/experiment_records"
STARTUP_WAIT="${STARTUP_WAIT:-25}"
CENTER_READY_TIMEOUT="${CENTER_READY_TIMEOUT:-15}"
SKIP_BUILD="${SKIP_BUILD:-0}"
RECORD_TIME_MODE="${RECORD_TIME_MODE:-sim}"
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
  bash tools/run_tracking_experiment.sh <baseline|opt_kp06|opt_kp065|slow_v016> [record_seconds]

Examples:
  cd /home/bn/bsnew
  bash tools/run_tracking_experiment.sh baseline 30
  bash tools/run_tracking_experiment.sh opt_kp06 30
  bash tools/run_tracking_experiment.sh opt_kp065 30
  bash tools/run_tracking_experiment.sh slow_v016 30

Environment:
  STARTUP_WAIT=25          seconds to wait after Gazebo and YOLO launch
  CENTER_READY_TIMEOUT=15  seconds to wait for the first valid /seam_center
  SKIP_BUILD=1             skip catkin_make
EOF
}

set_params() {
    case "$EXPERIMENT_NAME" in
        baseline)
            Kp="0.5"; Ki="0.02"; dead_zone="0.05"; integral_separation="0.30"
            i_max="0.3"; v0="0.2"; vmin="0.1"; alpha="0.5"; angular_threshold="0.2"
            ;;
        opt_kp06)
            Kp="0.6"; Ki="0.025"; dead_zone="0.045"; integral_separation="0.30"
            i_max="0.35"; v0="0.18"; vmin="0.08"; alpha="0.6"; angular_threshold="0.2"
            ;;
        opt_kp065)
            Kp="0.65"; Ki="0.03"; dead_zone="0.045"; integral_separation="0.30"
            i_max="0.35"; v0="0.17"; vmin="0.08"; alpha="0.65"; angular_threshold="0.2"
            ;;
        slow_v016)
            Kp="0.6"; Ki="0.025"; dead_zone="0.045"; integral_separation="0.30"
            i_max="0.35"; v0="0.16"; vmin="0.08"; alpha="0.6"; angular_threshold="0.2"
            ;;
        opt_kp07)
            echo "Warning: opt_kp07 is kept only as a compatibility alias; using the milder opt_kp065 parameters." >&2
            EXPERIMENT_NAME="opt_kp065"
            Kp="0.65"; Ki="0.03"; dead_zone="0.045"; integral_separation="0.30"
            i_max="0.35"; v0="0.17"; vmin="0.08"; alpha="0.65"; angular_threshold="0.2"
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

read_seam_center_valid() {
    local valid
    valid="$(timeout 3s rostopic echo -n 1 /seam_center 2>/dev/null | awk '
        $1 == "z:" {
            if (($2 + 0.0) > 0.5) {
                print "yes"
            } else {
                print "no"
            }
            exit
        }')"
    [ "$valid" = "yes" ]
}

wait_for_valid_center() {
    local wall_start wall_elapsed
    wall_start="$(date +%s)"
    while true; do
        if read_seam_center_valid; then
            return 0
        fi
        wall_elapsed=$(( $(date +%s) - wall_start ))
        if [ "$wall_elapsed" -ge "$CENTER_READY_TIMEOUT" ]; then
            return 1
        fi
        sleep 1
    done
}

is_positive_int() {
    case "$1" in
        ''|*[!0-9]*) return 1 ;;
        *) [ "$1" -gt 0 ] ;;
    esac
}

read_clock_seconds() {
    local line secs nsecs
    line="$(timeout 3s rostopic echo -n 1 /clock 2>/dev/null | awk '
        $1 == "secs:" {secs=$2}
        $1 == "nsecs:" {nsecs=$2}
        secs != "" && nsecs != "" {
            printf "%s.%09d\n", secs, nsecs
            exit
        }')"
    if [ -n "$line" ]; then
        printf "%s\n" "$line"
        return 0
    fi
    return 1
}

wait_sim_seconds() {
    local duration start now elapsed wall_start wall_elapsed
    start="$(read_clock_seconds)" || return 1
    wall_start="$(date +%s)"
    while true; do
        now="$(read_clock_seconds)" || return 1
        elapsed="$(awk -v now="$now" -v start="$start" 'BEGIN { printf "%.3f", now - start }')"
        if awk -v elapsed="$elapsed" -v duration="$duration" 'BEGIN { exit !(elapsed >= duration) }'; then
            break
        fi
        wall_elapsed=$(( $(date +%s) - wall_start ))
        if [ "$wall_elapsed" -gt $((duration * 3 + 30)) ]; then
            echo "Sim time did not advance enough; falling back to wall-time recording." >&2
            return 1
        fi
        sleep 0.5
    done
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
    if ! is_positive_int "$CENTER_READY_TIMEOUT"; then
        echo "CENTER_READY_TIMEOUT must be a positive integer, got: ${CENTER_READY_TIMEOUT}" >&2
        exit 2
    fi
}

PIDS_TO_CLEAN=""
LAUNCH_PID=""
CONTROLLER_PID=""
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
center_ready_timeout=${CENTER_READY_TIMEOUT}
record_time_mode=${RECORD_TIME_MODE}
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
        start_controller:=false \
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
    echo "Waiting ${STARTUP_WAIT}s for Gazebo and YOLO startup. Controller is not started yet."
    sleep "$STARTUP_WAIT"

    echo "Checking whether /seam_center is valid before starting the controller..."
    if wait_for_valid_center; then
        echo "Valid /seam_center detected. Start recording and then start controller."
    else
        echo "Warning: no valid /seam_center detected within ${CENTER_READY_TIMEOUT}s." >&2
        echo "The experiment will continue for diagnosis, but curves may show invalid detection only." >&2
    fi

    rostopic echo -p /cmd_vel > "${OUT_DIR}/cmd_vel.csv" &
    CMD_PID=$!
    PIDS_TO_CLEAN="${PIDS_TO_CLEAN} ${CMD_PID}"

    rostopic echo -p /seam_center > "${OUT_DIR}/seam_center.csv" &
    CENTER_PID=$!
    PIDS_TO_CLEAN="${PIDS_TO_CLEAN} ${CENTER_PID}"

    roslaunch robot_vision gazebo_seam_tracking.launch \
        start_gazebo:=false \
        start_yolo:=false \
        start_controller:=true \
        center_topic:=/seam_center \
        cmd_vel_topic:=/cmd_vel \
        Kp:="$Kp" \
        Ki:="$Ki" \
        dead_zone:="$dead_zone" \
        integral_separation:="$integral_separation" \
        i_max:="$i_max" \
        v0:="$v0" \
        vmin:="$vmin" \
        alpha:="$alpha" \
        angular_threshold:="$angular_threshold" \
        >> "${OUT_DIR}/roslaunch.log" 2>&1 &
    CONTROLLER_PID=$!
    PIDS_TO_CLEAN="${PIDS_TO_CLEAN} ${CONTROLLER_PID}"

    echo "controller roslaunch pid: ${CONTROLLER_PID}"
    echo "Recording /cmd_vel and /seam_center for ${RECORD_SECONDS}s (${RECORD_TIME_MODE} time)..."
    if [ "$RECORD_TIME_MODE" = "sim" ]; then
        wait_sim_seconds "$RECORD_SECONDS" || sleep "$RECORD_SECONDS"
    else
        sleep "$RECORD_SECONDS"
    fi

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
