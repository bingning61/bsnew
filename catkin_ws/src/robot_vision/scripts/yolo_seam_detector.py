#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys

import cv2
import numpy as np
import rospy
from geometry_msgs.msg import Point
from sensor_msgs.msg import Image

class YoloSeamDetector(object):
    def __init__(self):
        self.image_topic = rospy.get_param("~image_topic", "/image_raw")
        self.center_topic = rospy.get_param("~center_topic", "/seam_center")
        self.result_topic = rospy.get_param("~result_topic", "/result_image")
        self.conf_threshold = float(rospy.get_param("~conf_threshold", 0.25))
        self.imgsz = int(rospy.get_param("~imgsz", 640))
        self.target_class_id = int(rospy.get_param("~target_class_id", -1))
        self.publish_result_image = self.get_bool_param("~publish_result_image", True)
        self.backend = str(rospy.get_param("~backend", "yolov5")).strip()
        self.model_path = rospy.get_param("~model_path", self.default_model_path())
        self.yolov5_repo_path = rospy.get_param("~yolov5_repo_path", self.default_yolov5_repo_path())
        self.yolo_repo_path = rospy.get_param("~yolo_repo_path", self.default_yolo_repo_path())
        self.iou_threshold = float(rospy.get_param("~iou_threshold", 0.45))
        self.device = rospy.get_param("~device", "cpu")
        self.verbose = self.get_bool_param("~verbose", False)

        self.device_obj = None
        self.stride = None
        self.imgsz_checked = self.imgsz
        self.letterbox = None
        self.non_max_suppression = None
        self.scale_coords = None
        self.torch = None
        self.np = None
        self.model = self.load_model()

        self.center_pub = rospy.Publisher(self.center_topic, Point, queue_size=1)
        self.result_pub = None
        if self.publish_result_image:
            self.result_pub = rospy.Publisher(self.result_topic, Image, queue_size=1)

        self.image_sub = rospy.Subscriber(self.image_topic, Image, self.image_callback, queue_size=1, buff_size=2 ** 24)
        rospy.loginfo(
            "YOLO seam detector started. backend=%s image_topic=%s center_topic=%s result_topic=%s model=%s",
            self.backend,
            self.image_topic,
            self.center_topic,
            self.result_topic,
            self.model_path,
        )

    def default_project_root(self):
        scripts_dir = os.path.dirname(os.path.abspath(__file__))
        return os.path.normpath(os.path.join(scripts_dir, "..", "..", "..", ".."))

    def default_model_path(self):
        return os.path.join(self.default_project_root(), "models", "seam_best.pt")

    def default_yolov5_repo_path(self):
        return os.path.join(self.default_project_root(), "yolov5")

    def default_yolo_repo_path(self):
        return os.path.join(self.default_project_root(), "yolo")

    def get_bool_param(self, key, default):
        value = rospy.get_param(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("1", "true", "yes", "on")

    def load_model(self):
        if self.backend == "yolov5":
            return self.load_yolov5_model()
        elif self.backend == "legacy_ultralytics":
            return self.load_legacy_ultralytics_model()
        else:
            rospy.logfatal("Unsupported detector backend: %s", self.backend)
            raise RuntimeError("Unsupported detector backend")

    def require_model_file(self):
        if not self.model_path:
            rospy.logfatal("~model_path is empty. Please set YOLO weight path.")
            raise RuntimeError("~model_path is empty")
        if not os.path.isfile(self.model_path):
            rospy.logfatal("model file does not exist: %s", self.model_path)
            raise RuntimeError("model file does not exist")

    def load_yolov5_model(self):
        self.require_model_file()

        if not self.yolov5_repo_path or not os.path.isdir(self.yolov5_repo_path):
            rospy.logfatal("YOLOv5 repo path does not exist: %s", self.yolov5_repo_path)
            raise RuntimeError("YOLOv5 repo path does not exist")

        if self.yolov5_repo_path not in sys.path:
            sys.path.insert(0, self.yolov5_repo_path)

        try:
            import numpy as np
            import torch
            try:
                from utils.augmentations import letterbox
            except ImportError:
                from utils.datasets import letterbox
            from models.experimental import attempt_load
            from utils.general import non_max_suppression, scale_coords, check_img_size
            from utils.torch_utils import select_device
        except Exception as exc:
            rospy.logfatal("Failed to import YOLOv5 modules from %s: %s", self.yolov5_repo_path, str(exc))
            raise RuntimeError("Failed to import YOLOv5 modules")

        try:
            self.device_obj = select_device(self.device)
            model = attempt_load(self.model_path, map_location=self.device_obj)
            model.eval()
            self.stride = int(model.stride.max())
            self.imgsz_checked = check_img_size(self.imgsz, s=self.stride)
        except Exception as exc:
            rospy.logfatal("Failed to load YOLOv5 model: %s", str(exc))
            raise RuntimeError("Failed to load YOLOv5 model")

        self.np = np
        self.torch = torch
        self.letterbox = letterbox
        self.non_max_suppression = non_max_suppression
        self.scale_coords = scale_coords

        rospy.loginfo(
            "Loaded YOLOv5 backend. repo=%s device=%s imgsz=%s stride=%s",
            self.yolov5_repo_path,
            self.device,
            self.imgsz_checked,
            self.stride,
        )
        return model

    def load_legacy_ultralytics_model(self):
        self.require_model_file()

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

    def ros_image_to_cv2(self, msg):
        encoding = msg.encoding.lower()
        if encoding in ("bgr8", "rgb8"):
            channels = 3
        elif encoding == "mono8":
            channels = 1
        else:
            raise ValueError("Unsupported image encoding: %s" % msg.encoding)

        valid_step = int(msg.width) * channels
        row_step = int(msg.step)
        if row_step < valid_step:
            raise ValueError("Image step is smaller than width * channels")

        if isinstance(msg.data, (bytes, bytearray)):
            raw = np.frombuffer(msg.data, dtype=np.uint8)
        else:
            raw = np.asarray(msg.data, dtype=np.uint8)

        required_size = int(msg.height) * row_step
        if raw.size < required_size:
            raise ValueError("Image data is shorter than height * step")

        image = raw[:required_size].reshape((int(msg.height), row_step))
        image = image[:, :valid_step]

        if channels == 3:
            image = image.reshape((int(msg.height), int(msg.width), 3)).copy()
            if encoding == "rgb8":
                image = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
            return image

        image = image.reshape((int(msg.height), int(msg.width))).copy()
        return cv2.cvtColor(image, cv2.COLOR_GRAY2BGR)

    def cv2_to_ros_image(self, cv_image, header=None, encoding="bgr8"):
        if encoding != "bgr8":
            raise ValueError("Unsupported output encoding: %s" % encoding)
        if cv_image.ndim != 3 or cv_image.shape[2] != 3:
            raise ValueError("bgr8 output requires a 3-channel image")

        image = np.ascontiguousarray(cv_image)
        msg = Image()
        if header is not None:
            msg.header = header
        else:
            msg.header.stamp = rospy.Time.now()
        msg.height = image.shape[0]
        msg.width = image.shape[1]
        msg.encoding = encoding
        msg.is_bigendian = 0
        msg.step = image.shape[1] * 3
        msg.data = image.tobytes()
        return msg

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

    def run_yolov5_inference(self, cv_image):
        img0 = cv_image
        img = self.letterbox(img0, self.imgsz_checked, stride=self.stride, auto=True)[0]
        img = img[:, :, ::-1].transpose(2, 0, 1)
        img = self.np.ascontiguousarray(img)
        img = self.torch.from_numpy(img).to(self.device_obj)
        img = img.float()
        img /= 255.0
        if img.ndimension() == 3:
            img = img.unsqueeze(0)

        with self.torch.no_grad():
            pred = self.model(img, augment=False)[0]

        classes = None if self.target_class_id < 0 else [self.target_class_id]
        pred = self.non_max_suppression(
            pred,
            conf_thres=self.conf_threshold,
            iou_thres=self.iou_threshold,
            classes=classes,
            agnostic=False,
        )

        det = pred[0]
        if det is not None and len(det):
            det[:, :4] = self.scale_coords(img.shape[2:], det[:, :4], img0.shape).round()
            best_det = det[det[:, 4].argmax()]
            xyxy = best_det[:4].tolist()
            best_box = (float(xyxy[0]), float(xyxy[1]), float(xyxy[2]), float(xyxy[3]))
            best_conf = float(best_det[4].item())
            best_cls = int(best_det[5].item())
            return best_box, best_conf, best_cls

        return None, 0.0, -1

    def run_legacy_ultralytics_inference(self, cv_image):
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
            return self.find_best_box(results[0].boxes)
        return None, 0.0, -1

    def image_callback(self, data):
        try:
            cv_image = self.ros_image_to_cv2(data)
        except ValueError as exc:
            rospy.logerr("ROS image conversion failed: %s", str(exc))
            return

        image_height, image_width = cv_image.shape[:2]
        best_box = None
        best_conf = 0.0
        best_cls = -1

        try:
            if self.backend == "yolov5":
                best_box, best_conf, best_cls = self.run_yolov5_inference(cv_image)
            elif self.backend == "legacy_ultralytics":
                best_box, best_conf, best_cls = self.run_legacy_ultralytics_inference(cv_image)
        except Exception as exc:
            rospy.logerr_throttle(1.0, "%s inference failed: %s", self.backend, str(exc))

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
            rospy.logwarn_throttle(5.0, "No valid seam detection. Published invalid center and controller should stop.")
            cv2.putText(debug_image, "NO DETECTION", (20, 40), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 2)

        if self.result_pub is not None:
            try:
                img_msg = self.cv2_to_ros_image(debug_image, data.header, "bgr8")
                self.result_pub.publish(img_msg)
            except ValueError as exc:
                rospy.logerr("ROS image publish conversion failed: %s", str(exc))


if __name__ == "__main__":
    rospy.init_node("yolo_seam_detector")
    YoloSeamDetector()
    rospy.spin()
