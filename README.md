# AgricultureDataset-SensorSuiteBuild
![image](https://github.com/shuoyuanxu/AgricultureDataset-SensorSuiteBuild/assets/21218812/1ee2e615-6324-438d-b9b5-473787312e21)


## GitHub setup

1. Create the token in Github webpage, activate the repo option
2. Install Git's Credential Helper (to avoid typing password repetitively) 

		sudo apt-get install libsecret-1-0 libsecret-1-dev
		cd /usr/share/doc/git/contrib/credential/libsecret
		sudo make
		git config --global credential.helper /usr/share/doc/git/contrib/credential/libsecret/git-credential-libsecret

4. Create a repo on Github webpage
5. prepare local repo:

		
		git init
		git add .
		git commit -m "InitialCommit"
		git remote add origin http://......
		git push -u origin main (--force)
		

Here they will ask for username and password, use token as your password instead of github password
#### Other useful commands
		1. Rename branch: git branch -m master main
		2. Switch branch: git checkout main
		3. Merge changes: git merge other-branch-name
		4. Fetch changes: git fetch origin
		5. Pull changes: git pull origin main


## 1. LIDAR driver installation (Ouster)
  #### 1) Install the official driver (to ros workspace)
  ```git clone --recurse-submodules https://github.com/ouster-lidar/ouster-ros.git```
  
  ```catkin_make -DCMAKE_BUILD_TYPE=Release```
  #### 2) Give your lidar a fixed IP
  a. go into settings, network cable setting, give IPv4 a manual address 
     e.g. 192.168.254.150 & Netmask 255.255.255.0 then disable IPv6
     
  b. check lidar ip to make sure its using IPv4 and static address:
  
   ```
   avahi-browse -lr _roger._tcp
   http http://169.254.217.248/api/v1/system/network/ipv4/override
   ```
     
  ##### null means its not static
  use
   ```
   echo \"192.168.254.101/24\" | http PUT http://169.254.217.248/api/v1/system/network/ipv4/override
   ```

  to force it to use a static one
  ##### for my lidar, it gives:
  HTTPConnectionPool(host='169.254.217.248', port=80): Max retries exceeded with url: /api/v1/system/network/ipv4/override (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7f5a7f332be0>: Failed to establish a new connection: [Errno 113] No route to host',))
     in IPv4 setting, give the pc a closer address, such as 169.254.217.150 then following echo... command should pass, change it back to 192.168.254.150 if necessary. During this, LIDAR and PC may need to be restarted multiple times.
  
  once finished, run 
  ``` http http://169.254.217.248/api/v1/system/network/ipv4/override ``` 
  to double check if IP is static, if the last line of the output shows 192.168.254.101/24, means setting succeed.

  not sure what it does: 
  ``` export LD_PRELOAD=/usr/lib/aarch64-linux-gnu/libGLdispatch.so.0:$LD_PRELOAD ```
 
  c. run the visulisation to validate the installation
   ```
   source devel/setup.bash
   roslaunch ouster_ros sensor.launch sensor_hostname:=192.168.254.101
   ```
  ##### RLException: Unable to contact my own server at
  ```
  nano ~/.bashrc
  source ~/.bashrc
  ```

  ##### When running across 2 PCs: Bond broken, exiting REQUIRED process [os_node-2] has died!
  The issue comes from time synchronisation, disable bond:   
  ```<arg name="no_bond" default="true"``` should solve the issue.


## 2. IMU driver installation (3dm-gx5-ahrs)
  ##### 1) Install the official driver (to ros workspace)
  a.
 ```
 git clone --recursive --branch ros https://github.com/LORD-MicroStrain/microstrain_inertial.git
 catkin_make
 ```
     
  b. remember to install the missing libraries
 ```
 sudo apt-get install ros-noetic-nmea-msgs
 sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
 sudo apt-get install libgeographic-dev)
 ```
     
  c. Change ros source if needed
 ```
 sudo sh -c 'echo "deb http://packages.ros.org/ros/ubuntu $(lsb_release -sc) main" > /etc/apt/sources.list.d/ros-latest.list'
 sudo apt-key adv --keyserver 'hkp://keyserver.ubuntu.com:80' --recv-key C1CF6E31E6BADE8868B172B4F42ED6FBAB17C654
 ```

  ##### 2) for my case, the imu driver requires a full clean of the ros workspace:
```
catkin init
catkin clean -y --workspace ~/catkin_ws
catkin_make
source ~/catkin_ws/devel/setup.bash
```

  ##### 3) Connect the imu and test the driver
  a. Change device permission: ```sudo chmod 666 /dev/ttyACM0```
  
  b. Run the testing script: ```roslaunch microstrain_inertial_driver microstrain.launch```


## 3. GNSS driver installation (F9P)
  ##### 1) Config the receiver using U-center
  a. View > Configuration View
  
  b. MSG (Messages), enable USB
  ```
  $GxGGA: Essential fix data which provides 3D location and accuracy data.
  $GxGLL: Geographic position, latitude/longitude, and time of position fix.
  $GxRMC: Recommended minimum specific GPS/Transit data, which includes
  ```

  c. CFG (configuration), Save current configuration, Send
  
  d. Receiver > Action > Save Config
  
  e. Double checking by going back to MSG
  

  ##### 2) Install Drivers:
  ```
  sudo apt-get install gpsd gpsd-clients
  sudo apt-get install ros-noetic-serial
  ```
  Change the gpsd config file: ```nano /etc/default/gpsd```
  ```
  START_DAEMON="true"
  GPSD_OPTIONS=""
  DEVICES="/dev/ttyACM0"
  USBAUTO="true"
  ```
  
  Then test the driver with gpsd
  ```
  sudo systemctl restart gpsd
  sudo service gpsd restart
  cgps
  ```
  
  Install nmea_navsat_driver 
  ```
  sudo apt-get install ros-noetic-nmea-navsat-driver
  ```

  ##### 3) Connect the GNSS receiver and test the driver
  a. Change device permission: 
  ```
  sudo chmod 666 /dev/ttyACM0
  sudo chmod a+rw /dev/ttyACM0
  ```
  b. Run the NMEA serial script: 
  ```
  rosrun nmea_navsat_driver nmea_serial_driver _port:=/dev/ttyACM0 _baud:=9600
  ```
  c. Run the Ros node:
  ```
  rosrun gpsd_client gpsd_client
  rostopic echo /fix
  ```


## 4. Theta V driver installation 
  ##### 1) Config the Camera
  Put the camera into live streaming mode
  ##### 2) Install Drivers:
  a. Camera driver
  ```
  git clone https://github.com/ricohapi/libuvc-theta.git
  sudo apt install libjpeg-dev
  cd libuvc-theta
  mkdir build
  cd build
  cmake ..
  make
  sudo make install
  cd ../..
  git clone https://github.com/ricohapi/libuvc-theta-sample.git
  cd libuvc-theta-sample/gst
  make
  $ ./gst_viewer
  ```
  b. Install dependencies
  #### libptp (use ptpcam --help to verify installation)
  ```
  sudo apt-get install libusb-dev libusb-0.1-4
  cd libptp2-1.2.0
  ./configure --with-libusbdir=/usr
  make
  sudo make install
  chmod +x /home/shuoyuan/catkin_ws/src/ricoh_theta_ros/deps/libptp/src/.libs/ptpcam
  sudo cp /home/shuoyuan/catkin_ws/src/ricoh_theta_ros/deps/libptp/src/.libs/ptpcam /usr/local/bin/
  export PATH=$PATH:/home/shuoyuan/catkin_ws/src/ricoh_theta_ros/deps/libptp/src/.libs
  sudo apt-get install ros-noetic-cv-camera
  ```

  #### Cannot find ricoh
  ```
  export PATH=$PATH:/home/shuoyuan/catkin_ws/src/ricoh_theta_ros/utils
  or
  sudo cp /home/shuoyuan/catkin_ws/src/ricoh_theta_ros/ricoh_theta_ros/utils/ricoh /usr/local/bin/ricoh
  sudo chmod +x /usr/local/bin/ricoh
  ```

  #### Error: Cannot identify device '/dev/video1'
  ![image](https://github.com/shuoyuanxu/AgricultureDataset-SensorSuiteBuild/assets/21218812/1f020893-c99f-41b6-89b8-061ce20b9431)

  #### [ERROR] [1712656572.447247469]: cv camera open failed: device_id0 cannot be opened
  The source code of the ricoh node is not giving enough time for gst_loopback to fully initilise (maybe a less powerfully computer wouldnt have the same issue). Adding a sleep time behind gst_loopback solves it.
  ![image](https://github.com/shuoyuanxu/AgricultureDataset-SensorSuiteBuild/assets/21218812/84a24942-88d7-4d2d-8170-9aff01ab2b14)

  c. Camera Ros Node (remember to replace the libptp in dependency to the newest version since the one included is for ARM processors)
  ```
  git -C src clone --recursive https://github.com/madjxatw/ricoh_theta_ros.git
  catkin_make
  ```

  #### Choppy and Laggy stream
  

  ##### 3) Connect the Camera and test the driver
  a. 
  ```
  source ~/devel/setup.bash
  sudo modprobe v4l2loopback
  export PATH=$PATH:/home/shuoyuan/catkin_ws/src/ricoh_theta_ros/deps/libuvc-theta-sample/gst
  rosrun ricoh_theta_ros start.sh
  rqt_image_view
  ```

  b. Use these settings to avoid lags and freezes
  ```
  if (strcmp(cmd_name, "gst_loopback") == 0)
    pipe_proc = "decodebin ! autovideoconvert ! "
      "video/x-raw,format=I420 ! identity drop-allocation=true !"
      "v4l2sink device=/dev/video0 qos=false sync=false";
  else
    pipe_proc = " decodebin ! glimagesink qos=false sync=false";

  ```

  c. resolution can be reduced as follows:
  ```
  pipe_proc = "decodebin ! videoconvert ! videoscale ! video/x-raw,width=1280,height=720,format=I420 ! x264enc tune=zerolatency ! rtph264pay ! udpsink host=example.com port=5000 qos=false sync=false";
  ```
  ```
pipe_proc = "decodebin ! videoconvert ! videoscale ! video/x-raw,width=1920,height=960,format=I420 ! identity tune=zerolatency ! "
    "v4l2sink device=/dev/video0 qos=false sync=false";
  ```
  
## 5. Launch script 
Before running the script, connect the lidar, 360 camera, and IMU to the NUC. Toggle the mode button (3rd side button from the top) to live video mode.	
  ##### 1) Source catkin workspace and master
  ```
  sudo nano .bashsrc
  uncomment last 2 lines 
      # >>> fishros initialize >>>
      source /opt/ros/noetic/setup.bash
      source /home/shuoyuan/catkin_driver_ws/devel/setup.bash
      source /home/shuoyuan/catkin_code_ws/devel/setup.bash
      # <<< fishros initialize <<<
      # export ROS_IP=192.168.1.150
      # export ROS_MASTER_URI=http://192.168.1.102:11311
  source .bashrc
  ```
  ##### 2) Launch sensors then recording (keep all sensors running, record when needed)
  ```
  rosrun sensorsuite sensorsuite.sh
  roslaunch sensorsuite recordstart.launch
  ```
  ##### 3) When IMU is not responding, try unplug then plugin the IMU or change the IMU USB ID here:
  ```
  /home/shuoyuan/catkin_driver_ws/src/microstrain_inertial/microstrain_inertial_driver/microstrain_inertial_driver_common/config/params.yml
  ```
  replacing ```ttyACM1 to ttyACM0``` or vice versa

## 6. Setting up SLAM algorithm
  ##### 1) LIO-SAM
  ```
  cd ~/catkin_ws/src
  git clone https://github.com/TixiaoShan/LIO-SAM.git
  cd ..
  catkin_make
  ```
  a) Change the following line to enable PCL compatibility:
  ```set(CMAKE_CXX_FLAGS "-std=c++11")``` to ```set(CMAKE_CXX_FLAGS "-std=c++14")```
  
  b) Modify line to avoid: imuPreintegration.cpp:214:100: error: conversion from ‘std::shared_ptr<gtsam::PreintegrationParams>’ to non-scalar type ‘boost::shared_ptr<gtsam::PreintegrationParams>’ requested'
  ```boost::shared_ptr<gtsam::PreintegrationParams> p = gtsam::PreintegrationParams::MakeSharedU(imuGravity);``` to ```std::shared_ptr<gtsam::PreintegrationParams> p = gtsam::PreintegrationParams::MakeSharedU(imuGravity);```
  
  c) Install related libs:
  ```
  sudo apt-get install ros-noetic-robot-localization
  ```
  
  d) Set the system to use sim time:
  ```rosparam set use_sim_time true```

  e) Try different "extrinsicRot" and extrinsicRPY in "params.yaml

  f) View point cloud
  ```pcl_viewer lio_sam_map.pcd```

  ##### 2) DSO
  a) Run
  ```
  roslaunch direct_lidar_odometry dlo.launch
  ```
  b) Save pcd 
  ```
  rosservice call /robot/dlo_map/save_pcd 0.2 "/home/shuoyuan/output"
  ```


## 7. Connecting to Antobot
  ##### 1) ssh into antobot
  ```
  antobot
  password
  ip 192.168.1.102
  ```
  
