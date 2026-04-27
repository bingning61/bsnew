#!/usr/bin/env python
from __future__ import print_function

import rospy
import cv2
import os
import sys
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image

try:
    unicode
except NameError:
    unicode = str


class fake_camera:
    def __init__(self):
        self.image_path = self.normalize_path(rospy.get_param('~image_path', 'bingda.png'))
        self.video_path = self.normalize_path(rospy.get_param('~video_path', ''))
        self.fps = self.normalize_fps(rospy.get_param('~fps', 10.0))
        self.image_pub = rospy.Publisher("/image_raw", Image, queue_size=3)
        self.bridge = CvBridge() 
        self.pub_image()

    def normalize_path(self, path):
        path = os.path.expanduser(os.path.expandvars(path))
        if sys.version_info[0] < 3 and isinstance(path, unicode):
            path = path.encode('utf-8')
        return path

    def normalize_fps(self, fps):
        try:
            fps = float(fps)
        except (TypeError, ValueError):
            rospy.logwarn("Invalid fake camera fps '%s', use 10.0", str(fps))
            fps = 10.0
        if fps <= 0.0:
            rospy.logwarn("Fake camera fps must be positive, use 10.0")
            fps = 10.0
        return fps

    def publish_frame(self, cv_image):
        try:
            img_msg = self.bridge.cv2_to_imgmsg(cv_image, "bgr8")
        except CvBridgeError as exc:
            rospy.logerr("Fake camera image conversion failed: %s", str(exc))
            return
        img_msg.header.stamp = rospy.Time.now()
        self.image_pub.publish(img_msg)

    def pub_single_image(self):
        rate = rospy.Rate(self.fps)
        cv_image = cv2.imread(self.image_path, 1)
        if cv_image is None:
            rospy.logerr("Fake camera image read failed: %s", self.image_path)
            return

        rospy.loginfo("Start Publish Fake Camera Image: %s at %.2f fps", self.image_path, self.fps)
        while not rospy.is_shutdown():
            self.publish_frame(cv_image)
            rate.sleep()

    def pub_video(self):
        cap = cv2.VideoCapture(self.video_path)
        if not cap.isOpened():
            rospy.logerr("Fake camera video open failed: %s", self.video_path)
            return

        rate = rospy.Rate(self.fps)
        rospy.loginfo("Start Publish Fake Camera Video: %s at %.2f fps", self.video_path, self.fps)
        while not rospy.is_shutdown():
            ok, frame = cap.read()
            if not ok or frame is None:
                cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
                ok, frame = cap.read()
                if not ok or frame is None:
                    rospy.logerr("Fake camera video read failed after rewind: %s", self.video_path)
                    break

            self.publish_frame(frame)
            rate.sleep()

        cap.release()

    def pub_image(self):
        if self.video_path:
            self.pub_video()
        else:
            self.pub_single_image()

if __name__ == '__main__':
    try:
        rospy.init_node("fake_camera", anonymous=False)
        fake_camera()
    except rospy.ROSInternalException:
        pass
