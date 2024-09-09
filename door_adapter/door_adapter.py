import sys
import yaml
import argparse

import time
import threading
import rclpy
from door_adapter.DoorClientAPI import DoorClientAPI
from rclpy.node import Node
from rclpy.time import Time
from rmf_door_msgs.msg import DoorRequest, DoorState, DoorMode,SupervisorHeartbeat,DoorSessions,Session

## Before using this door_adapter, you need to modify door.common.cpp to avoid door node pub its' state firstly
## Remenber to colcon after that
## Then modify your common.launch.xml to ban door_supervisor and set to launch door_adapter
## The code is listed following:
## <!-- Door Adapter -->

## <node pkg="door_adapter" exec="door_adapter" args="--config_file '/opt/ros/galactic/share/rmf_door_adapter/config.yaml'" output="both">
##   <param name="use_sim_time" value="$(var use_sim_time)"/>
## </node>
## Do not forget to change the config.yaml adress

###############################################################################

class DoorAdapter(Node):
    def __init__(self,config_yaml):
        super().__init__('door_adapter')
        
        self.get_logger().info('Starting door adapter...')
        
        self.door_name = ''
        self.robotId = ''
        self.deviceUnique = ''
        ## Init check variable
        self.door_state_publish_period = config_yaml['door_publisher']['door_state_publish_period']
        ## Init the pub frequency
        door_pub = config_yaml['door_publisher']
        door_requests_pub = config_yaml['door_requests_publisher']
        door_sub = config_yaml['door_subscriber']
        door_supervisor_heartbeat_publisher_pub = config_yaml['door_supervisor_heartbeat_publisher']
        ## Init publisher and subscriber details
        self.taskdoor = lst = []
        ## Init a list to store doors' info which are in tasks
        self.doorinfo = config_yaml['doorinfo']
        ## Init a list to store all doors' info  including requested state(States),requester Id(robotId),
        ## check flag(check),check delay(delay) and the delay abaout get doors' current states (count) 
        self.robotinfo = config_yaml['robot']
        ## Init a list to store robots' info including requester_id and robotId
        self.api = DoorClientAPI()
        ## Init DoorClientAPI
        self.door_states_pub = self.create_publisher(
            DoorState, door_pub['topic_name'], 10)

        self.door_request_sub = self.create_subscription(
            DoorRequest, door_sub['topic_name'], self.door_request_cb, 10)

        self.periodic_timer = self.create_timer(
            self.door_state_publish_period, self.time_cb)
        
        self.door_supervisor_heartbeat_publisher_pub = self.create_publisher(
            SupervisorHeartbeat,door_supervisor_heartbeat_publisher_pub['topic_name'],10)
        
        self.door_requests_pub = self.create_publisher(
            DoorRequest, door_requests_pub['topic_name'], 10)
        ## Init publishers and a subscriber
        self.tokenupdate()
        self.tokencount = 259200
	## Get and store robot token information
	## Change token count to modify the cycle to update token

    def time_cb(self):
        k=len(self.doorinfo)-1
        ## All doors' state should be published
        self.count()
        ## Count time
        while k>=0:
        ## Traversal all doors
            if self.doorinfo[k].get('check') == 1 and self.doorinfo[k].get('count') < 0 and self.doorinfo[k].get('delay') < 0:
                ## Which means this door's state needs to be checked and it's time to check it
                self.door_mode = self.api.get_mode(self.doorinfo[k].get('robotId'),self.doorinfo[k].get("deviceUnique"),self.doorinfo[k].get("token"))
                ## Check states
                if self.door_mode == 2 and self.doorinfo[k].get('states') == 2:    
                    ## Successfully open                  
                    self.doorinfo[k]['count'] = 40
                    # Reset the check state timer
                    state_msg = DoorState()
                    state_msg.door_time = self.get_clock().now().to_msg()
                    state_msg.door_name = self.doorinfo[k].get('door_name')
                    state_msg.current_mode.value = self.door_mode
                    self.door_states_pub.publish(state_msg)
                    k=k-1
                    ## Publish door state
                elif self.door_mode != 2 and self.doorinfo[k].get('states') == 2:
                    ## Request successfully but door hasn't open
                    if not self.api.open_door(self.doorinfo[k].get('robotId'),self.doorinfo[k].get("deviceUnique"),self.doorinfo[k].get("token")):
                        ## Situation that effect time passed
                        ## Try to extend effect time
                        self.doorinfo[k]['error'] = 3
                        ## Set error count,it can change retry times by change the value
                    print("door error")
                    self.doorinfo[k]['delay'] = 3
                    ## Check again after 5 sec
                    self.doorinfo[k]['error'] += 1
                    ## Error counts
                    if self.doorinfo[k]['error'] >= 5:
                        ## Reach max retry times
                        print(self.doorinfo[k]['door_name']+' did not change states,it may be an error')
                        self.doorinfo[k]['error'] = 0
                        self.doorinfo[k]['check'] = 0
                        self.doorinfo[k]['states'] = 0
                        j = len(self.taskdoor)-1
                        while j >= 0:
                            if self.doorinfo[k]['door_name']== self.taskdoor[j]['door_name']:
                                break
                            j-=1
                        if j != -1:
                            del self.taskdoor[j]
                        ## Find the error door in task doors and remove it
                    k=k-1
            elif self.doorinfo[k].get('check') == 1 and self.doorinfo[k].get('delay') >= 0:
                ## During the delay of check states after post request to url
                    state_msg = DoorState()
                    state_msg.door_time = self.get_clock().now().to_msg()
                    state_msg.door_name = self.doorinfo[k].get('door_name')
                    state_msg.current_mode.value = 1
                    self.door_states_pub.publish(state_msg)
                    ## Publish the door_states
                    ## In order to run successfully in gazebo,defalut door mode value is 1 which means the door is moving in this situation
                    ## In reality this situation should be the url return the information that the door is moving
                    k=k-1
            else:
                ## This situation is for these doors that aren't in task
                    state_msg = DoorState()
                    state_msg.door_time = self.get_clock().now().to_msg()
                    state_msg.door_name = self.doorinfo[k].get('door_name')
                    state_msg.current_mode.value = self.doorinfo[k].get('states')
                    self.door_states_pub.publish(state_msg)
                    k=k-1
			## In reality during delay check door states should be 0!!!!!!!
    def door_request_cb(self, msg: DoorRequest):
        # when door node receive open request, the door adapter will send open command to API after checking
        # If door node receive close request, the door adapter will stop sending open command to API
        # check DoorRequest msg whether the door name of the request is same as the current door. If not, ignore the request 
        j = len(self.robotinfo)-1
        while j >= 0:
            if self.robotinfo[j]['requester_id'] == msg.requester_id:
                self.robotId=self.robotinfo[j]['robotId']
                break
            j-=1
        if j!=-1:
            m=len(self.taskdoor)-1
        ## Check whether the requester_Id is existed or not
            while m >= 0 :
                if self.taskdoor[m]['door_name'] == msg.door_name:
                    if msg.requested_mode.value != DoorMode.MODE_CLOSED:
                        self.get_logger().error('Request has existed. Ignoring...')
                    break
                m-=1
                ## Check whether this door has been in task or not
                ## If it's true,ignore the request 
            if m==-1 or msg.requested_mode.value == DoorMode.MODE_CLOSED:   
                i = len(self.doorinfo)-1
                while i >= 0:
                    if self.doorinfo[i]['door_name'] == msg.door_name:
                        self.deviceUnique=self.doorinfo[i]['deviceUnique']
                        self.door_name = msg.door_name
                        break
                    i-=1
                    ## Check whether the door is existed or not
                if i!=-1:
                    self.get_logger().info(f"Door mode [{msg.requested_mode.value}] requested by {msg.requester_id}")
                    if msg.requested_mode.value == DoorMode.MODE_OPEN:
                        # open door implementation
                        if not self.api.open_door(self.robotId,self.deviceUnique,self.robotinfo[j].get('token')):
                            self.get_logger().error('Failed to post open request. Ignoring...')
                        else:
                            self.door_requests_pub.publish(msg)
                            ## Pubulish door_requests to door node in order to run successfully in gazebo
                            ## In reality door node doesn't exist,this publisher is not neccessary
                            taskdoor_dict = {"door_name":'',"request_time": {"sec": 0,"nanosec": 0,"requester_id":''}} 
                            taskdoor_dict["door_name"] = self.door_name
                            taskdoor_dict["request_time"]["sec"] = msg.request_time.sec
                            taskdoor_dict["request_time"]["nanosec"] = msg.request_time.nanosec
                            taskdoor_dict["requester_id"] = msg.requester_id
                            ## Add infomation about request door into task door
                            self.doorinfo[i]['robotId'] = self.robotId
                            self.doorinfo[i]['states'] = 2
                            self.doorinfo[i]['check'] = 1
                            self.doorinfo[i]['count'] = 0
                            self.doorinfo[i]['delay'] = 5
                            self.doorinfo[i]['token'] = self.robotinfo[j].get('token')
                            ## Add infomation about request door into door_info
                            ## This implement to reduce the number of API called
                            ## It can change the check delay by change the value of delay
                            self.taskdoor.append(taskdoor_dict)
                            self.heartbeatopen()
                            ## Heartbeat is neccessary
                            print('Open Command to door received')
                    elif msg.requested_mode.value == DoorMode.MODE_CLOSED:
                        # close door implementation
                        self.get_logger().info('Close Command to door received')
                        if not self.api.close_door(self.robotId,self.deviceUnique,self.robotinfo[j].get('token')):
                            self.get_logger().error('Failed to post close request. Ignoring...')
                        else:
                            self.door_requests_pub.publish(msg)
                            ## Pubulish door_requests to door node in order to run successfully in gazebo
                            ## In reality door node doesn't exist,this publisher is not neccessary
                            self.doorinfo[i]['robotId'] = ''
                            self.doorinfo[i]['delay'] = 0
                            self.doorinfo[i]['states'] = 0
                            self.doorinfo[i]['check'] = 0
                            self.doorinfo[i]['count'] = 0
                            self.doorinfo[i]['token'] = ''
                            ## When door request is to close door and the door state is close
                            ## Will assume the door state is close until next door open request and has no need to check states 
                            ## Because the api can't be used when the open door task is finished
                            ## Reset the door in door_info
                            if m!=-1:
                                del self.taskdoor[m]
                            ## Remove door in taskdoor if it's in taskdoor
                            self.heartbeatclose(self.doorinfo[i]['door_name'])
                            ## Heartbeat is neccessary
                            print('Close Command to door received')
                    else:
                        self.get_logger().error('Invalid door mode requested. Ignoring...')
                else:
                    self.get_logger().error('No such door found. Ignoring...')
        else:
            self.get_logger().error('No such requester found. Ignoring...')
    
    def count(self):
        # Counter
        kl=len(self.doorinfo)-1
        ## Traversal all doors
        while kl>=0:
            if self.doorinfo[kl]['delay']>=0 and self.doorinfo[kl]['check']==1:
                ## During the delay after post request
                self.doorinfo[kl]['delay']-=1
            elif self.doorinfo[kl]['check']==1 and self.doorinfo[kl]['delay']<0:
                ## During the check state delay
                if self.doorinfo[kl]['count']>=0:
                    self.doorinfo[kl]['count']-=1
                else:
                    ## Reset Timer
                    self.doorinfo[kl]['count']=20
            kl=kl-1
        self.tokencount-=1
        if self.tokencount <= 0:
        ## Update token and reset timer
            self.tokenupdate()
            self.tokencount = 259200
    
    def heartbeatopen(self):
        # Info the sys that door adapter is online
        SupervisorHeartbeat_msg=SupervisorHeartbeat()
        k=len(self.taskdoor)-1
        ## Infomation should include all doors in task
        sessions=DoorSessions()
        i=0
        while k >=i:
            j = len(self.doorinfo)-1
            while j >= 0:
                if self.doorinfo[j]['door_name']== self.taskdoor[k]['door_name']:
                    break
                j-=1
            ## Find related infomation in door_info
            if j != -1:
                if self.doorinfo[j]['states']!=0:
                    session_msg = Session()
                    sessions.door_name = self.taskdoor[k]["door_name"]
                    session_msg.request_time.sec = self.taskdoor[k]['request_time']["sec"]
                    session_msg.request_time.nanosec =self.taskdoor[k]['request_time']["nanosec"]
                    session_msg.requester_id=self.taskdoor[k]['requester_id']
                    sessions.sessions.append(session_msg)
                    SupervisorHeartbeat_msg.all_sessions.append(sessions)
                    i+=1
        self.door_supervisor_heartbeat_publisher_pub.publish(SupervisorHeartbeat_msg)
        ## Publish when receive a door_adapter_request successfully

    def heartbeatclose(self,door_name):
        # info the sys that door adapter is online
        SupervisorHeartbeat_msg=SupervisorHeartbeat()
        k=len(self.taskdoor)-1
        ## Infomation should include all doors in task
        sessions=DoorSessions()
        i=0
        while k >=i:
            j = len(self.doorinfo)-1
            while j >= 0:
                if self.doorinfo[j]['door_name']== self.taskdoor[k]['door_name']:
                    break
                j-=1
            ## Find infomation in door_info
            if j != -1:
                if self.doorinfo[j]['states']!=0:
                    session_msg = Session()
                    sessions.door_name = self.taskdoor[k]["door_name"]
                    session_msg.request_time.sec = self.taskdoor[k]['request_time']["sec"]
                    session_msg.request_time.nanosec =self.taskdoor[k]['request_time']["nanosec"]
                    session_msg.requester_id=self.taskdoor[k]['requester_id']
                    sessions.sessions.append(session_msg)
                    SupervisorHeartbeat_msg.all_sessions.append(sessions)
                    i+=1
        sessions_msg = DoorSessions()
        sessions_msg.door_name = door_name
        session_msg = Session()
        SupervisorHeartbeat_msg.all_sessions.append(sessions_msg)
        ## Generate the special infomation about the door required to close
        self.door_supervisor_heartbeat_publisher_pub.publish(SupervisorHeartbeat_msg)
        ## Publish when receive a door_adapter_request successfully

    def tokenupdate(self):
        k = len(self.robotinfo)-1
        while k >= 0:
            self.robotinfo[k]['token'] = self.api.check_connection(self.robotinfo[k].get('robotId'))
            k-=1

###############################################################################

def main(argv=sys.argv):
    rclpy.init(args=argv)
    args_without_ros = rclpy.utilities.remove_ros_args(argv)
    parser = argparse.ArgumentParser(
        prog="door_adapter",
        description="Configure and spin up door adapter for door ")
    parser.add_argument("-c", "--config_file", type=str, required=True,
                        help="Path to the config.yaml file for this door adapter")
    args = parser.parse_args(args_without_ros[1:])
    config_path = args.config_file

    # Load config and nav graph yamls
    with open(config_path, "r") as f:
        config_yaml = yaml.safe_load(f)

    door_adapter = DoorAdapter(config_yaml)
    rclpy.spin(door_adapter)

    door_adapter.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main(sys.argv)
