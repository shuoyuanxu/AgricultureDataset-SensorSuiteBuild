#!/bin/bash

# Load the v4l2loopback module
sudo modprobe v4l2loopback

# Add the gst directory to PATH
export PATH=$PATH:/home/shuoyuan/catkin_ws/src/ricoh_theta_ros/deps/libuvc-theta-sample/gst

# Now launch the ROS nodes
roslaunch sensorsuite sensorsuite.launch


