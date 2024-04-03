# AgricultureDataset-SensorSuiteBuild

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



