#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import cv2
import rospy
from cv_bridge import CvBridge, CvBridgeError
from geometry_msgs.msg import Point
from sensor_msgs.msg import Image


class YoloSeamDetector(object):
    def __init__(self):
        self.bridge = CvBridge()

        self.image_topic = rospy.get_param("~image_topic", "/image_raw")
        self.center_topic = rospy.get_param("~center_topic", "/seam_center")
        self.result_topic = rospy.get_param("~result_topic", "/result_image")
        self.conf_threshold = float(rospy.get_param("~conf_threshold", 0.25))
        self.imgsz = int(rospy.get_param("~imgsz", 640))
        self.target_class_id = int(rospy.get_param("~target_class_id", -1))
        self.publish_result_image = self.get_bool_param("~publish_result_image", True)
        self.model_path = rospy.get_param("~model_path", "")
        self.yolo_repo_path = rospy.get_param("~yolo_repo_path", self.default_yolo_repo_path())
        self.device = rospy.get_param("~device", "")
        self.verbose = self.get_bool_param("~verbose", False)

        self.model = self.load_model()

        self.center_pub = rospy.Publisher(self.center_topic, Point, queue_size=1)
        self.result_pub = None
        if self.publish_result_image:
            self.result_pub = rospy.Publisher(self.result_topic, Image, queue_size=1)

        self.image_sub = rospy.Subscriber(self.image_topic, Image, self.image_callback, queue_size=1, buff_size=2 ** 24)
        rospy.loginfo("YOLO seam detector started. model=%s", self.model_path)

    def default_yolo_repo_path(self):
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.join(scripts_dir, "..", "..", "..", "..", "yolo"))

    def get_bool_param(self, key, default):
        value = rospy.get_param(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("1", "true", "yes", "on")

    def load_model(self):
        if not self.model_path:
            rospy.logfatal("~model_path is empty. Please set YOLO weight path.")
            raise RuntimeError("~model_path is empty")
        if not os.path.isfile(self.model_path):
            rospy.logfatal("YOLO model file does not exist: %s", self.model_path)
            raise RuntimeError("YOLO model file does not exist")

        if self.yolo_repo_path and os.path.isdir(os.path.join(self.yolo_repo_path, "ultralytics")):
            if self.yolo_repo_path not in sys.path:
                sys.path.insert(0, self.yolo_repo_path)

        try:
            from ultralytics import YOLO
        except Exception as exc:
            rospy.logfatal("Failed to import ultralytics: %s", str(exc))
            raise

        return YOLO(self.model_path)

    def publish_center(self, center_x, image_width, valid):
        msg = Point()
        msg.x = float(center_x)
        msg.y = float(image_width)
        msg.z = 1.0 if valid else 0.0
        self.center_pub.publish(msg)

    def find_best_box(self, boxes):
        best_box = None
        best_conf = -1.0
        best_cls = -1

        for box in boxes:
            conf = float(box.conf[0]) if box.conf is not None else 0.0
            cls_id = int(box.cls[0]) if box.cls is not None else -1
            if self.target_class_id >= 0 and cls_id != self.target_class_id:
                continue
            if conf > best_conf:
                xyxy = box.xyxy[0].tolist()
                best_box = (float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3]))
                best_conf = conf
                best_cls = cls_id

        return best_box, best_conf, best_cls

    def image_callback(self, data):
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as exc:
            rospy.logerr("CV bridge conversion failed: %s", str(exc))
            return

        image_height, image_width = cv_image.shape[:2]
        best_box = None
        best_conf = 0.0
        best_cls = -1

        try:
            predict_args = {
                "source": cv_image,
                "conf": self.conf_threshold,
                "imgsz": self.imgsz,
                "verbose": self.verbose,
            }
            if self.device:
                predict_args["device"] = self.device
            results = self.model.predict(**predict_args)
            if results and len(results) > 0 and results[0].boxes is not None and len(results[0].boxes) > 0:
                best_box, best_conf, best_cls = self.find_best_box(results[0].boxes)
        except Exception as exc:
            rospy.logerr_throttle(1.0, "YOLO inference failed: %s", str(exc))

        debug_image = cv_image.copy()
        if best_box is not None:
            x1, y1, x2, y2 = best_box
            center_x = (x1 + x2) / 2.0
            center_y = (y1 + y2) / 2.0
            self.publish_center(center_x, image_width, True)

            cv2.rectangle(debug_image, (int(x1), int(y1)), (int(x2), int(y2)), (0, 255, 0), 2)
            cv2.circle(debug_image, (int(center_x), int(center_y)), 5, (0, 0, 255), -1)
            cv2.line(debug_image, (int(image_width / 2), 0), (int(image_width / 2), image_height - 1), (255, 0, 0), 2)
            cv2.putText(
                debug_image,
                "cls:%d conf:%.2f" % (best_cls, best_conf),
                (int(x1), max(int(y1) - 10, 20)),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.6,
                (0, 255, 0),
                2,
            )
        else:
            self.publish_center(-1.0, image_width, False)
            cv2.putText(debug_image, "NO DETECTION", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        if self.result_pub is not None:
            try:
                img_msg = self.bridge.cv2_to_imgmsg(debug_image, encoding="bgr8")
                img_msg.header.stamp = rospy.Time.now()
                self.result_pub.publish(img_msg)
            except CvBridgeError as exc:
                rospy.logerr("CV bridge publish failed: %s", str(exc))


if __name__ == "__main__":
    rospy.init_node("yolo_seam_detector")
    YoloSeamDetector()
    rospy.spin()
