# Door_Adapter使用手册
------
## 1.1 简介
* 该代码主要目的是将**RMF**系统与[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)中的云设备（门）进行连接，从而实现**RMF**系统控制及获取云设备（门）状态。
## 1.2 使用方法
### 1.2.1 配置文件修改
* 配置文件格式为.yaml。
```
api:
  appId: "68518620319745" 
  appSecret: "8288EC12D8CFC60D"
  appCode: “00004V3”
door_subscriber:
  topic_name: "adapter_door_requests"
door_supervisor_heartbeat_publisher:
  topic_name: "door_supervisor_heartbeat"
door_publisher:
  topic_name: "door_states"
  door_state_publish_period: 1.0 # Seconds
door_requests_publisher:
  topic_name: "door_requests"
robot: 
    - {robotId: '000058062236',requester_id: 'tinyRobot/tinyRobot1',token: ''}
    - {robotId: '000058060279',requester_id: 'tinyRobot/tinyRobot2',token: ''}
    - {robotId: '000058069743',requester_id: 'door_panel_requester',token: ''}
doorinfo: 
    - {door_name: 'coe_door',states: 0,check: 0,error: 0,deviceUnique: '0000580620003',delay: 0,robotId: '',count: 0,token: ''}
    - {door_name: 'hardware_door',states: 0,check: 0,error: 0,deviceUnique: '0000580620001',delay: 0,robotId: '',count: 0,token: ''}
    - {door_name: 'main_door',states: 0,check: 0,error: 0,deviceUnique: '0000580620002',delay: 0,robotId: '',count: 0,token: ''}
```
* 使用时应修改**api**中的信息与[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)所提供的项目信息一致。
* 可通过修改**door_state_publish_period**的值改变门状态向RMF系统中更新的频率。
* **robot**项中将[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)中机器人的**robotId**与RMF系统中机器人名称建立映射即可（**token**在**DoorClientAPI.py**中会自动向云平台获取及更新，无需填写）。
* **doorinfo**项中将[旺龙智慧人机云平台](https://itlcloud.yun-r.com/login)中门的**deviceUnique**与RMF系统中门名称建立映射即可（其他项无需修改）。
### 1.2.2 DoorClientAPI.py文件修改
* 按照**DoorClientAPI.py**文件中注释说明修改即可。
### 1.2.3 在启动仿真世界中自动启动Door_Adapter
* 请注意：以下步骤一定要按顺序执行！！！
#### 1.2.3.1 修改文件停止门节点的发布
* 在**rmf_ws/rmf/src/rmf/rmf_simulation/rmf_building_sim_common/src**中找到文件**door_common.cpp**，将第85行修改为
 ```
      _initialized = false;
   ```
#### 1.2.3.2 编译文件
* 将**door_adapter**文件夹放置于**rmf_ws/rmf/src**中，在**rmf_ws/rmf/src**中使用以下命令进行编译。
```
    colcon build
```
* 请确认将所有文件都编译，包括**1.2.3.1**中所修改的文件。
#### 1.2.3.3 修改启动脚本
* 由于**door_adapter**与**door_supervior**职能冲突，需要在默认的启动脚本中覆盖。
* 在**rmf_ws/rmf/install/rmf_demos/share/rmf_demos**中找到文件**common.launch.xml**，并将
```   
  <!-- Door Supervisor -->
  <group>
    <node pkg="rmf_fleet_adapter" exec="door_supervisor">
      <param name="use_sim_time" value="$(var use_sim_time)"/>
    </node>
  </group>
```
* 修改为
```
  <node pkg="door_adapter" exec="door_adapter" args="--config_file '/home/hpr/rmf_ws/rmf/src/door_adapter/config.yaml'" output="both">
    <param name="use_sim_time" value="$(var use_sim_time)"/>
  </node>
```
* 请注意，修改内容中的'**/home/hpr/rmf_ws/rmf/src/door_adapter/config.yaml**'应修改为**1.2.1**中**config.yaml**的地址。
* 就此，在启动世界的时候就能运行**door_adapter**了。
## 1.3 Mock
### 1.3.1 设备需求
* mock设备采用**ESP32-S**。
### 1.3.2 代码修改
* **door_adapter**包使用方法与上述相同，修改方式也相同，但是注意**DoorClientAPI.py**中使用的url（以http://192.168.181.141/door_status为例，），地址应与**ESP32-S**向端口发送的ip一致（可通过Arduino端口监控器查看）。
* 使用前应修改.ino文件。.ino文件通过Arduino修改连接的wifi及密码。（只修改此项即可）
### 1.3.3 使用方法
* 打开一个世界，通电等待**ESP32-S**上电连接wifi，发布任务即可。
### 1.3.4 注意事项
* 使用Arduino烧录时需要将**ESP32-S**断电后再次上电！！！
* **ESP32-S**的IO4为门状态指示灯。
