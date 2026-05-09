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
        if "MPLCONFIGDIR" not in os.environ:
            cache_dir = os.path.join("/tmp", "bsnew_matplotlib_cache")
            os.makedirs(cache_dir, exist_ok=True)
            os.environ["MPLCONFIGDIR"] = cache_dir
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        return plt
    except Exception as exc:
        fail("matplotlib is required: {}".format(exc))


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


def read_rows(path):
    if not os.path.isfile(path):
        fail("CSV file does not exist: {}".format(path))
    with open(path, "r") as f:
        reader = csv.reader(f)
        rows = [row for row in reader if row]
    if not rows:
        fail("CSV file is empty: {}".format(path))
    return rows[0], rows[1:]


def to_float(value):
    try:
        return float(value)
    except Exception:
        return None


def normalize_time(value):
    if value is None:
        return None
    # rostopic echo -p usually writes ROS time in nanoseconds.
    if abs(value) > 1.0e6:
        return value / 1.0e9
    return value


def find_time_column(headers):
    idx = find_column(headers, ["wall_time"])
    if idx is not None:
        return idx, "wall"
    idx = find_column(headers, ["ros_time"])
    if idx is not None:
        return idx, "ros"
    idx = find_column(headers, ["time"])
    if idx is not None:
        return idx, "legacy"
    fail("no time column found in CSV headers: {}".format(headers))


def read_seam_center(path):
    headers, rows = read_rows(path)
    time_idx, time_mode = find_time_column(headers)
    x_idx = find_column(headers, ["x"])
    y_idx = find_column(headers, ["y"])
    z_idx = find_column(headers, ["z"])
    if x_idx is None or y_idx is None or z_idx is None:
        fail("seam CSV must contain x, y, z columns. headers={}".format(headers))

    data = []
    max_idx = max(time_idx, x_idx, y_idx, z_idx)
    for row in rows:
        if len(row) <= max_idx:
            continue
        t = to_float(row[time_idx])
        if time_mode == "legacy":
            t = normalize_time(t)
        x = to_float(row[x_idx])
        y = to_float(row[y_idx])
        z = to_float(row[z_idx])
        if t is None or x is None or y is None or z is None:
            continue
        image_center = y / 2.0 if y > 0.0 else None
        error_pixel = None
        error_norm = None
        if image_center is not None:
            error_pixel = x - image_center
            error_norm = (image_center - x) / image_center if image_center > 0.0 else None
        data.append({
            "time": t,
            "center_x": x,
            "image_width": y,
            "valid": 1.0 if z > 0.5 else 0.0,
            "image_center": image_center,
            "error_pixel": error_pixel,
            "error_norm": error_norm,
        })
    if not data:
        fail("no valid seam_center rows parsed from {}".format(path))
    return data


def read_cmd_vel(path):
    headers, rows = read_rows(path)
    time_idx, time_mode = find_time_column(headers)
    lx_idx = find_column(headers, ["linear.x"])
    az_idx = find_column(headers, ["angular.z"])
    if lx_idx is None or az_idx is None:
        fail("cmd CSV must contain linear.x and angular.z columns. headers={}".format(headers))

    data = []
    max_idx = max(time_idx, lx_idx, az_idx)
    for row in rows:
        if len(row) <= max_idx:
            continue
        t = to_float(row[time_idx])
        if time_mode == "legacy":
            t = normalize_time(t)
        lx = to_float(row[lx_idx])
        az = to_float(row[az_idx])
        if t is None or lx is None or az is None:
            continue
        data.append({"time": t, "linear_x": lx, "angular_z": az})
    if not data:
        fail("no valid cmd_vel rows parsed from {}".format(path))
    return data


def rel_time(data, t0):
    return [item["time"] - t0 for item in data]


def values(data, key, valid_only=False):
    out = []
    for item in data:
        if valid_only and item.get("valid", 1.0) <= 0.5:
            out.append(float("nan"))
        else:
            value = item.get(key)
            out.append(value if value is not None else float("nan"))
    return out


def plot_line(plt, times, series, xlabel, ylabel, title, label, out_path):
    plt.figure(figsize=(12, 6))
    plt.plot(times, series, label=label)
    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def plot_error(plt, seam_data, t0, out_path):
    times = rel_time(seam_data, t0)
    error_pixel = values(seam_data, "error_pixel", valid_only=True)
    error_norm = values(seam_data, "error_norm", valid_only=True)
    plt.figure(figsize=(12, 6))
    plt.plot(times, error_pixel, label="pixel error: center_x - image_center")
    plt.plot(times, error_norm, label="normalized error used by controller")
    plt.xlabel("time / s")
    plt.ylabel("error")
    plt.title("Seam center error")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()
    plt.savefig(out_path, dpi=150)
    plt.close()


def write_summary(path, seam_data, cmd_data):
    valid = [item for item in seam_data if item["valid"] > 0.5 and item["error_pixel"] is not None]
    abs_pixel = [abs(item["error_pixel"]) for item in valid]
    abs_norm = [abs(item["error_norm"]) for item in valid if item["error_norm"] is not None]

    def mean(seq):
        return sum(seq) / float(len(seq)) if seq else float("nan")

    def max_or_nan(seq):
        return max(seq) if seq else float("nan")

    lines = [
        ("sample_count_seam_center", len(seam_data)),
        ("sample_count_cmd_vel", len(cmd_data)),
        ("valid_count", len(valid)),
        ("valid_ratio", float(len(valid)) / float(len(seam_data)) if seam_data else float("nan")),
        ("mean_abs_error_pixel", mean(abs_pixel)),
        ("max_abs_error_pixel", max_or_nan(abs_pixel)),
        ("mean_abs_error_norm", mean(abs_norm)),
        ("max_abs_error_norm", max_or_nan(abs_norm)),
    ]

    with open(path, "w") as f:
        for key, value in lines:
            if isinstance(value, float) and math.isnan(value):
                f.write("{}=nan\n".format(key))
            else:
                f.write("{}={}\n".format(key, value))


def main():
    parser = argparse.ArgumentParser(description="Plot real-robot seam tracking curves from rostopic echo -p CSV files.")
    parser.add_argument("--seam", required=True, help="CSV saved by: rostopic echo -p /seam_center")
    parser.add_argument("--cmd", required=True, help="CSV saved by: rostopic echo -p /cmd_vel")
    parser.add_argument("--out", required=True, help="Output directory for PNG curves")
    args = parser.parse_args()

    seam_data = read_seam_center(os.path.expanduser(args.seam))
    cmd_data = read_cmd_vel(os.path.expanduser(args.cmd))
    out_dir = os.path.expanduser(args.out)
    os.makedirs(out_dir, exist_ok=True)

    t0 = min(seam_data[0]["time"], cmd_data[0]["time"])
    plt = import_matplotlib()

    plot_line(
        plt,
        rel_time(seam_data, t0),
        values(seam_data, "center_x"),
        "time / s",
        "center x / pixel",
        "YOLO detection box center x",
        "/seam_center.x",
        os.path.join(out_dir, "seam_center_x_curve.png"),
    )
    plot_error(plt, seam_data, t0, os.path.join(out_dir, "seam_error_curve.png"))
    plot_line(
        plt,
        rel_time(seam_data, t0),
        values(seam_data, "valid"),
        "time / s",
        "valid flag",
        "YOLO detection valid flag",
        "/seam_center.z",
        os.path.join(out_dir, "valid_flag_curve.png"),
    )
    plot_line(
        plt,
        rel_time(cmd_data, t0),
        values(cmd_data, "linear_x"),
        "time / s",
        "linear.x",
        "Forward velocity command",
        "/cmd_vel.linear.x",
        os.path.join(out_dir, "cmd_vel_linear_x_curve.png"),
    )
    plot_line(
        plt,
        rel_time(cmd_data, t0),
        values(cmd_data, "angular_z"),
        "time / s",
        "angular.z",
        "Yaw velocity command",
        "/cmd_vel.angular.z",
        os.path.join(out_dir, "cmd_vel_angular_z_curve.png"),
    )
    write_summary(os.path.join(out_dir, "summary.txt"), seam_data, cmd_data)
    print("Saved curves to {}".format(out_dir))


if __name__ == "__main__":
    main()
