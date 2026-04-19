#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright 2021 wechange tech.
# Developer: FuZhi Liu 
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import rospy
import cv2
from cv_bridge import CvBridge, CvBridgeError
from sensor_msgs.msg import Image
import numpy as np
from dynamic_reconfigure.server import Server
from robot_vision.cfg import line_hsvConfig
# from robot_vision.cfg

from geometry_msgs.msg import Twist, Point

class line_follow:
    def __init__(self):    
        #define topic publisher and subscriber
        self.bridge = CvBridge()
        self.mask_pub = rospy.Publisher("/mask_image", Image, queue_size=1)
        self.result_pub = rospy.Publisher("/result_image", Image, queue_size=1)
        self.pub_cmd = rospy.Publisher('cmd_vel', Twist, queue_size=5)
        self.srv = Server(line_hsvConfig, self.dynamic_reconfigure_callback)
        # get param from launch file 
        self.use_external_center = self.get_bool_param('~use_external_center', False)
        self.external_center_topic = rospy.get_param('~external_center_topic', '/seam_center')
        self.external_center_timeout = float(rospy.get_param('~external_center_timeout', 0.5))
        self.test_mode = self.get_bool_param('~test_mode', False)
        self.h_lower = int(rospy.get_param('~h_lower',110))
        self.s_lower = int(rospy.get_param('~s_lower',50))
        self.v_lower = int(rospy.get_param('~v_lower',50))

        self.h_upper = int(rospy.get_param('~h_upper',130))
        self.s_upper = int(rospy.get_param('~s_upper',255))
        self.v_upper = int(rospy.get_param('~v_upper',255))
        #line center point X Axis coordinate
        self.center_point = 0
        self.last_external_center_time = rospy.Time(0)

        if self.use_external_center:
            self.center_sub = rospy.Subscriber(self.external_center_topic, Point, self.external_center_callback, queue_size=1)
            self.center_watchdog = rospy.Timer(rospy.Duration(0.1), self.external_center_watchdog)
            rospy.loginfo("Line follow uses external center topic: %s", self.external_center_topic)
        else:
            self.image_sub = rospy.Subscriber("/image_raw", Image, self.callback)
            rospy.loginfo("Line follow uses HSV detector input from /image_raw")

    def get_bool_param(self, key, default):
        value = rospy.get_param(key, default)
        if isinstance(value, bool):
            return value
        return str(value).lower() in ("1", "true", "yes", "on")

    def dynamic_reconfigure_callback(self,config,level):
        # update config param
        self.h_lower = config.h_lower
        self.s_lower = config.s_lower
        self.v_lower = config.v_lower
        self.h_upper = config.h_upper
        self.s_upper = config.s_upper
        self.v_upper = config.v_upper
        return config

    def publish_stop(self):
        stop_twist = Twist()
        self.pub_cmd.publish(stop_twist)

    def external_center_callback(self, data):
        image_width = float(data.y)
        center_x = float(data.x)
        valid = data.z > 0.5 and image_width > 0
        if valid:
            self.last_external_center_time = rospy.Time.now()
            self.twist_calculate(image_width / 2.0, center_x)
        else:
            self.publish_stop()

    def external_center_watchdog(self, _event):
        if not self.use_external_center:
            return
        if self.last_external_center_time.to_sec() == 0:
            self.publish_stop()
            return
        if (rospy.Time.now() - self.last_external_center_time).to_sec() > self.external_center_timeout:
            self.publish_stop()

    def callback(self,data):
        # convert ROS topic to CV image formart
        try:
            cv_image = self.bridge.imgmsg_to_cv2(data, "bgr8")
        except CvBridgeError as e:
            print e
        # conver image color from RGB to HSV    
        hsv_image = cv2.cvtColor(cv_image,cv2.COLOR_RGB2HSV)
        #set color mask min amd max value
        line_lower = np.array([self.h_lower,self.s_lower,self.v_lower])
        line_upper = np.array([self.h_upper,self.s_upper,self.v_upper])
        # get mask from color
        mask = cv2.inRange(hsv_image,line_lower,line_upper)
        # close operation to fit some little hole
        kernel = np.ones((9,9),np.uint8)
        mask = cv2.morphologyEx(mask,cv2.MORPH_CLOSE,kernel)
        # if test mode,output the center point HSV value
        res = cv_image
        if self.test_mode:
            cv2.circle(res, (hsv_image.shape[1]/2,hsv_image.shape[0]/2), 5, (0,0,255), 1)
            cv2.line(res,(hsv_image.shape[1]/2-10, hsv_image.shape[0]/2), (hsv_image.shape[1]/2+10,hsv_image.shape[0]/2), (0,0,255), 1)
            cv2.line(res,(hsv_image.shape[1]/2, hsv_image.shape[0]/2-10), (hsv_image.shape[1]/2, hsv_image.shape[0]/2+10), (0,0,255), 1)
            rospy.loginfo("Point HSV Value is %s"%hsv_image[hsv_image.shape[0]/2,hsv_image.shape[1]/2])            
        else:
            # in normal mode,add mask to original image
            # res = cv2.bitwise_and(cv_image,cv_image,mask=mask)
            for i in range(-60,100,20):
                point = np.nonzero(mask[mask.shape[0]/2 + i])             
                if len(point[0]) > 10:
                    self.center_point = int(np.mean(point))
                    cv2.circle(res, (self.center_point,hsv_image.shape[0]/2+i), 5, (0,0,255), 5)
                    break
        if self.center_point:
            self.twist_calculate(hsv_image.shape[1]/2,self.center_point)
        self.center_point = 0


        # show CV image in debug mode(need display device)
        # cv2.imshow("Image window", res)
        # cv2.imshow("Mask window", mask)
        # cv2.waitKey(3)

        # convert CV image to ROS topic and pub 
        try:
            img_msg = self.bridge.cv2_to_imgmsg(res, encoding="bgr8")
            img_msg.header.stamp = rospy.Time.now()
            self.result_pub.publish(img_msg)
            img_msg = self.bridge.cv2_to_imgmsg(mask, encoding="passthrough")
            img_msg.header.stamp = rospy.Time.now()
            self.mask_pub.publish(img_msg)
            
        except CvBridgeError as e:
            print e
    def twist_calculate(self,width,center):
        center = float(center)
        self.twist = Twist()
        self.twist.linear.x = 0
        self.twist.linear.y = 0
        self.twist.linear.z = 0
        self.twist.angular.x = 0
        self.twist.angular.y = 0
        self.twist.angular.z = 0
        if center/width > 0.95 and center/width < 1.05:
            self.twist.linear.x = 0.2
        else:
            self.twist.angular.z = ((width - center) / width) / 2.0
            if abs(self.twist.angular.z) < 0.2:
                self.twist.linear.x = 0.2 - self.twist.angular.z/2.0
            else:
                self.twist.linear.x = 0.1
        self.pub_cmd.publish(self.twist)



if __name__ == '__main__':
    try:
        # init ROS node 
        rospy.init_node("line_follow")
        rospy.loginfo("Starting Line Follow node")
        line_follow()
        rospy.spin()
    except KeyboardInterrupt:
        print "Shutting down cv_bridge_test node."
        cv2.destroyAllWindows()
