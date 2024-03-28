# AgricultureDataset-SensorSuiteBuild

1. ## LIDAR driver installation (Ouster)
  1) Install the official driver (to ur ros directory)
     git clone --recurse-submodules https://github.com/ouster-lidar/ouster-ros.git
     catkin_make -DCMAKE_BUILD_TYPE=Release  
  2) Give your lidar a fixed IP
     ### a. go into settings, network cable setting, give IPv4 a manual address e.g. 192.168.254.150 & Netmask 255.255.255.0 then disable IPv6
     ### b. check lidar ip to make sure its using IPv4 and static address:
     avahi-browse -lr _roger._tcp
     http http://169.254.217.248/api/v1/system/network/ipv4/override
     ## null means its not static
     use
     echo \"192.168.254.101/24\" | http PUT http://169.254.217.248/api/v1/system/network/ipv4/override
     to force it to use a static one
     ## for my lidar, it gives:
     HTTPConnectionPool(host='169.254.217.248', port=80): Max retries exceeded with url: /api/v1/system/network/ipv4/override (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x7f5a7f332be0>: Failed to establish a new connection: [Errno 113] No route to host',))
     in IPv4 setting, give the pc a closer address, such as 169.254.217.150 then following echo... command should pass, change it back to 192.168.254.150 if necessary. During this, LIDAR and PC may need to be restarted multiple times.
     once finished, run http http://169.254.217.248/api/v1/system/network/ipv4/override to double check if IP is static, if the last line of the output shows 192.168.254.101/24, means setting succeed.

     ### c. run the visulisation to validate the installation
     source devel/setup.bash
      
