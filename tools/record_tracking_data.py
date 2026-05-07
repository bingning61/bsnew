#!/usr/bin/env python3
from __future__ import print_function

import argparse
import csv
import os
import sys
import time

import rospy
from geometry_msgs.msg import Point, Twist
from rosgraph_msgs.msg import Clock


class TrackingRecorder(object):
    def __init__(self, args):
        self.args = args
        self.start_wall = time.time()
        self.last_clock = None
        self.cmd_count = 0
        self.center_count = 0
        self.clock_count = 0

        if not os.path.isdir(args.out_dir):
            os.makedirs(args.out_dir)

        self.cmd_file = open(os.path.join(args.out_dir, "cmd_vel.csv"), "w")
        self.center_file = open(os.path.join(args.out_dir, "seam_center.csv"), "w")
        self.clock_file = open(os.path.join(args.out_dir, "clock.csv"), "w")

        self.cmd_writer = csv.writer(self.cmd_file)
        self.center_writer = csv.writer(self.center_file)
        self.clock_writer = csv.writer(self.clock_file)

        self.cmd_writer.writerow([
            "wall_time",
            "ros_time",
            "field.linear.x",
            "field.linear.y",
            "field.linear.z",
            "field.angular.x",
            "field.angular.y",
            "field.angular.z",
        ])
        self.center_writer.writerow(["wall_time", "ros_time", "field.x", "field.y", "field.z"])
        self.clock_writer.writerow(["wall_time", "ros_time"])

        rospy.Subscriber(args.cmd_topic, Twist, self.cmd_callback, queue_size=200)
        rospy.Subscriber(args.center_topic, Point, self.center_callback, queue_size=200)
        rospy.Subscriber(args.clock_topic, Clock, self.clock_callback, queue_size=200)

    def wall_time(self):
        return time.time() - self.start_wall

    def ros_time(self):
        if self.last_clock is not None:
            return self.last_clock
        now = rospy.Time.now()
        if now is not None:
            return now.to_sec()
        return 0.0

    def flush_periodically(self, count):
        if count % 10 == 0:
            self.cmd_file.flush()
            self.center_file.flush()
            self.clock_file.flush()

    def cmd_callback(self, msg):
        self.cmd_count += 1
        self.cmd_writer.writerow([
            "{:.6f}".format(self.wall_time()),
            "{:.9f}".format(self.ros_time()),
            "{:.9f}".format(msg.linear.x),
            "{:.9f}".format(msg.linear.y),
            "{:.9f}".format(msg.linear.z),
            "{:.9f}".format(msg.angular.x),
            "{:.9f}".format(msg.angular.y),
            "{:.9f}".format(msg.angular.z),
        ])
        self.flush_periodically(self.cmd_count)

    def center_callback(self, msg):
        self.center_count += 1
        self.center_writer.writerow([
            "{:.6f}".format(self.wall_time()),
            "{:.9f}".format(self.ros_time()),
            "{:.9f}".format(msg.x),
            "{:.9f}".format(msg.y),
            "{:.9f}".format(msg.z),
        ])
        self.flush_periodically(self.center_count)

    def clock_callback(self, msg):
        self.clock_count += 1
        self.last_clock = msg.clock.to_sec()
        if self.args.record_clock:
            self.clock_writer.writerow([
                "{:.6f}".format(self.wall_time()),
                "{:.9f}".format(self.last_clock),
            ])
            self.flush_periodically(self.clock_count)

    def close(self):
        self.cmd_file.flush()
        self.center_file.flush()
        self.clock_file.flush()
        self.cmd_file.close()
        self.center_file.close()
        self.clock_file.close()


def main():
    parser = argparse.ArgumentParser(description="Record seam tracking topics with wall-time and ROS-time columns.")
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--duration-wall", type=float, default=30.0)
    parser.add_argument("--cmd-topic", default="/cmd_vel")
    parser.add_argument("--center-topic", default="/seam_center")
    parser.add_argument("--clock-topic", default="/clock")
    parser.add_argument("--record-clock", action="store_true")
    args = parser.parse_args()

    if args.duration_wall <= 0:
        print("ERROR: --duration-wall must be positive", file=sys.stderr)
        return 2

    rospy.init_node("tracking_experiment_recorder", anonymous=True)
    recorder = TrackingRecorder(args)
    rospy.loginfo(
        "Tracking recorder started. duration_wall=%.3fs cmd_topic=%s center_topic=%s out_dir=%s",
        args.duration_wall,
        args.cmd_topic,
        args.center_topic,
        args.out_dir,
    )

    end_wall = time.time() + args.duration_wall
    try:
        while not rospy.is_shutdown() and time.time() < end_wall:
            time.sleep(0.05)
    finally:
        recorder.close()
        rospy.loginfo(
            "Tracking recorder finished. cmd_count=%d center_count=%d clock_count=%d",
            recorder.cmd_count,
            recorder.center_count,
            recorder.clock_count,
        )
    return 0


if __name__ == "__main__":
    sys.exit(main())
