#!/usr/bin/env python3
from __future__ import print_function

import argparse
import csv
import math
import os
import sys


def fail(message):
    print("ERROR: {}".format(message), file=sys.stderr)
    sys.exit(1)


def import_matplotlib():
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except Exception as exc:
        fail("matplotlib is required to plot curves: {}".format(exc))


def norm_name(name):
    return name.strip().lstrip("%").replace("field.", "").lower()


def find_column(headers, candidates):
    normalized = [norm_name(h) for h in headers]
    for candidate in candidates:
        candidate = candidate.lower()
        for idx, header in enumerate(normalized):
            if header == candidate or header.endswith("." + candidate):
                return idx
    for candidate in candidates:
        candidate = candidate.lower()
        for idx, header in enumerate(normalized):
            if candidate in header:
                return idx
    return None


def read_csv_rows(path):
    if not os.path.isfile(path):
        fail("CSV file does not exist: {}".format(path))
    with open(path, "r") as f:
        reader = csv.reader(f)
        rows = [row for row in reader if row]
    if not rows:
        return [], []
    return rows[0], rows[1:]


def to_float(value):
    try:
        return float(value)
    except Exception:
        return None


def normalize_time(value):
    if value is None:
        return None
    # rostopic echo -p commonly writes ROS time in nanoseconds.
    # Convert large integer-like timestamps to seconds for readable plots.
    if abs(value) > 1.0e6:
        return value / 1.0e9
    return value


def read_cmd_vel(path):
    headers, rows = read_csv_rows(path)
    if not headers:
        return []

    time_idx = find_column(headers, ["time"])
    lx_idx = find_column(headers, ["linear.x", "x"])
    ly_idx = find_column(headers, ["linear.y", "y"])
    az_idx = find_column(headers, ["angular.z", "z"])

    missing = []
    if time_idx is None:
        missing.append("%time")
    if lx_idx is None:
        missing.append("linear.x")
    if ly_idx is None:
        missing.append("linear.y")
    if az_idx is None:
        missing.append("angular.z")
    if missing:
        fail("cmd_vel CSV missing columns: {} in {}".format(", ".join(missing), headers))

    data = []
    for row in rows:
        if len(row) <= max(time_idx, lx_idx, ly_idx, az_idx):
            continue
        t = normalize_time(to_float(row[time_idx]))
        lx = to_float(row[lx_idx])
        ly = to_float(row[ly_idx])
        az = to_float(row[az_idx])
        if t is None or lx is None or ly is None or az is None:
            continue
        data.append({"time": t, "linear_x": lx, "linear_y": ly, "angular_z": az})
    return data


def read_seam_center(path):
    headers, rows = read_csv_rows(path)
    if not headers:
        return []

    time_idx = find_column(headers, ["time"])
    x_idx = find_column(headers, ["x"])
    y_idx = find_column(headers, ["y"])
    z_idx = find_column(headers, ["z"])

    missing = []
    if time_idx is None:
        missing.append("%time")
    if x_idx is None:
        missing.append("x")
    if y_idx is None:
        missing.append("y")
    if z_idx is None:
        missing.append("z")
    if missing:
        fail("seam_center CSV missing columns: {} in {}".format(", ".join(missing), headers))

    data = []
    for row in rows:
        if len(row) <= max(time_idx, x_idx, y_idx, z_idx):
            continue
        t = normalize_time(to_float(row[time_idx]))
        x = to_float(row[x_idx])
        y = to_float(row[y_idx])
        z = to_float(row[z_idx])
        if t is None or x is None or y is None or z is None:
            continue
        valid = z > 0.5 and y > 0.0
        error = None
        if valid:
            ref = y / 2.0
            if ref > 0.0:
                error = (ref - x) / ref
        data.append({"time": t, "center_x": x, "image_width": y, "valid": valid, "valid_value": z, "error": error})
    return data


def rel_times(data, t0):
    return [item["time"] - t0 for item in data]


def finite_values(values):
    return [v for v in values if v is not None and not math.isnan(v)]


def mean(values):
    values = finite_values(values)
    if not values:
        return None
    return sum(values) / float(len(values))


def min_or_none(values):
    values = finite_values(values)
    return min(values) if values else None


def max_or_none(values):
    values = finite_values(values)
    return max(values) if values else None


def fmt(value):
    if value is None:
        return "nan"
    if isinstance(value, str):
        return value
    if math.isnan(value):
        return "nan"
    return "{:.6f}".format(value)


def angular_sign_changes(values, threshold=0.01):
    last_sign = 0
    changes = 0
    for value in values:
        if value is None:
            continue
        if abs(value) <= threshold:
            continue
        sign = 1 if value > 0 else -1
        if last_sign != 0 and sign != last_sign:
            changes += 1
        last_sign = sign
    return changes


def stop_after_invalid(center_data, cmd_data, t0):
    invalid_times = []
    was_valid = False
    for item in center_data:
        if item["valid"]:
            was_valid = True
        elif was_valid:
            invalid_times.append(item["time"])
            break
    if not invalid_times:
        return "no_invalid"

    invalid_time = invalid_times[0]
    later_cmd = [item for item in cmd_data if item["time"] >= invalid_time]
    if not later_cmd:
        return "no_cmd_after_invalid"

    for item in later_cmd:
        if abs(item["linear_x"]) < 0.01 and abs(item["linear_y"]) < 0.01 and abs(item["angular_z"]) < 0.01:
            return "yes"
    return "no"


def plot_center_error(plt, center_data, t0, out_path):
    times = []
    errors = []
    for item in center_data:
        if item["valid"] and item["error"] is not None:
            times.append(item["time"] - t0)
            errors.append(item["error"])
    plt.figure(figsize=(16, 8))
    plt.plot(times, errors, label="normalized error")
    plt.xlabel("time / s")
    plt.ylabel("error")
    plt.title("Visual center error over time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_cmd_vel(plt, cmd_data, t0, out_path):
    times = rel_times(cmd_data, t0)
    linear_x = [item["linear_x"] for item in cmd_data]
    linear_y = [item["linear_y"] for item in cmd_data]
    angular_z = [item["angular_z"] for item in cmd_data]
    plt.figure(figsize=(16, 8))
    plt.plot(times, linear_x, label="linear.x / vx")
    plt.plot(times, linear_y, label="linear.y / vy")
    plt.plot(times, angular_z, label="angular.z / wz")
    plt.xlabel("time / s")
    plt.ylabel("velocity command")
    plt.title("Velocity command over time")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_valid_flag(plt, center_data, t0, out_path):
    times = rel_times(center_data, t0)
    valid = [1.0 if item["valid"] else 0.0 for item in center_data]
    plt.figure(figsize=(16, 6))
    plt.plot(times, valid, label="valid flag")
    plt.xlabel("time / s")
    plt.ylabel("valid")
    plt.title("Detection valid flag")
    plt.ylim(-0.05, 1.05)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def write_summary(path, name, center_data, cmd_data, t0):
    valid_errors = [abs(item["error"]) for item in center_data if item["valid"] and item["error"] is not None]
    valid_count = len(valid_errors)
    center_count = len(center_data)
    valid_ratio = (float(valid_count) / float(center_count)) if center_count else None

    tail_mean = None
    if len(valid_errors) >= 5:
        tail_count = max(5, int(math.ceil(len(valid_errors) * 0.30)))
        tail_mean = mean(valid_errors[-tail_count:])

    lx = [item["linear_x"] for item in cmd_data]
    ly = [item["linear_y"] for item in cmd_data]
    az = [item["angular_z"] for item in cmd_data]

    summary = [
        ("experiment_name", name),
        ("sample_count_center", center_count),
        ("sample_count_cmd_vel", len(cmd_data)),
        ("valid_ratio", valid_ratio),
        ("mean_abs_error_valid", mean(valid_errors)),
        ("tail_mean_abs_error_valid", tail_mean),
        ("max_abs_error_valid", max_or_none(valid_errors)),
        ("linear_x_min", min_or_none(lx)),
        ("linear_x_max", max_or_none(lx)),
        ("linear_x_mean", mean(lx)),
        ("linear_y_max_abs", max_or_none([abs(v) for v in ly])),
        ("angular_z_min", min_or_none(az)),
        ("angular_z_max", max_or_none(az)),
        ("angular_z_max_abs", max_or_none([abs(v) for v in az])),
        ("angular_sign_changes", angular_sign_changes(az)),
        ("stop_after_invalid", stop_after_invalid(center_data, cmd_data, t0)),
    ]

    with open(path, "w") as f:
        for key, value in summary:
            f.write("{}={}\n".format(key, fmt(value)))


def main():
    parser = argparse.ArgumentParser(description="Plot Gazebo seam tracking experiment curves.")
    parser.add_argument("--cmd-vel", required=True, help="CSV from rostopic echo -p /cmd_vel")
    parser.add_argument("--seam-center", required=True, help="CSV from rostopic echo -p /seam_center")
    parser.add_argument("--out-dir", required=True, help="Output directory")
    parser.add_argument("--name", required=True, help="Experiment name")
    args = parser.parse_args()

    cmd_data = read_cmd_vel(args.cmd_vel)
    center_data = read_seam_center(args.seam_center)
    if not cmd_data:
        fail("no valid cmd_vel samples parsed from {}".format(args.cmd_vel))
    if not center_data:
        fail("no valid seam_center samples parsed from {}".format(args.seam_center))

    os.makedirs(args.out_dir, exist_ok=True)
    t0 = min(cmd_data[0]["time"], center_data[0]["time"])
    plt = import_matplotlib()

    plot_center_error(plt, center_data, t0, os.path.join(args.out_dir, "center_error_curve_clean.png"))
    plot_cmd_vel(plt, cmd_data, t0, os.path.join(args.out_dir, "cmd_vel_curve_clean.png"))
    plot_valid_flag(plt, center_data, t0, os.path.join(args.out_dir, "valid_flag_curve_clean.png"))
    write_summary(os.path.join(args.out_dir, "summary.txt"), args.name, center_data, cmd_data, t0)


if __name__ == "__main__":
    main()
