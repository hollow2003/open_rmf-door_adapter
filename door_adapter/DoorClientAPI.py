import requests
import json
import urllib3
import socket
import time
from rmf_door_msgs.msg import DoorRequest
import uuid
import hashlib
import binascii
from Crypto.Cipher import AES
import base64
from urllib import parse
## Every robotId has unique token!! 

class DoorClientAPI:
    def __init__(self):
        self.aes =Aes_ECB()
        ##Init encode and decode module
        count = 0
        self.connected = True
        self.headers = {'Content-Type': 'application/x-www-form-urlencoded'}
        while self.check_connection("000058069743") =='':        ##Input of self.check_connection() should be one of the enabled robotIds
            ##Using get token api to check connection
            if count >= 5:
                print("Unable to connect to door client API.")
                self.connected = False
                break
            else:
                print("Unable to connect to door client API. Attempting to reconnect...")
                count += 1
            time.sleep(1)

    def check_connection(self,robotId):
        # Get token and store
        self.connection_data = {"requestId":"Null","sign":"Null","robotId":"Null","projectId":"00005806","timestamp":"Null"}   ##Change the projectId if needed
        self.connection_data["requestId"]=getUUID()
        self.connection_data["timestamp"]=int(round(time.time() * 1000))
        self.connection_data["robotId"] =robotId
        self.connection_data["sign"]=md5value(str(self.connection_data.get("projectId"))+str(self.connection_data.get("requestId"))+str(self.connection_data.get("robotId"))+str(self.connection_data.get("timestamp"))+'8288EC12D8CFC60D') ##The last string should be your appSecret
        data='{"requestId":"'+self.connection_data.get("requestId")+'","sign":"'+self.connection_data.get("sign")+'","robotId":"'+self.connection_data.get("robotId")+'","projectId":"'+self.connection_data.get("projectId")+'","timestamp":"'+str(self.connection_data.get("timestamp"))+'"}'
        endata={"appId":"1527168518620319745","encryptType":"0","encryptScript":self.aes.AES_encrypt(data)}  ##Change the appId if needed
        payload=parse.urlencode(endata)   
        try:
            res = requests.request("POST","https://api.yun-r.com/api/cloud/base/developerLogin", headers=self.headers, data=payload)
            res.raise_for_status()
            temp=json.loads(res.text)
            self.result=json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
            print(self.result)
            if self.result.get('success')==True:
                self.token=self.result.get('data').get('token')
                return self.token
            else:
                return ''
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print(f"Connection Error: {e}")
            return ''
    
    ##储存设备信息至self.devices
    def get_DeviceInfo(self,robotId,token):
        # Get deviceinfo that this robot can control
        ## In this project every robot can control all doors 
        ## Because of this this function is none of use
        self.get_DeviceInfo_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","appCode":"00004V3"}  ##Change the apCode if needed
        self.get_DeviceInfo_data["requestId"]=getUUID()
        self.get_DeviceInfo_data["timestamp"]=int(round(time.time() * 1000))
        self.get_DeviceInfo_data["robotId"] =robotId
        data='{"requestId":"'+self.get_DeviceInfo_data.get("requestId")+'","robotId":"'+self.get_DeviceInfo_data.get("robotId")+'","timestamp":"'+str(self.get_DeviceInfo_data.get("timestamp"))+'","appCode":"'+self.get_DeviceInfo_data.get("appCode")+'"}'
        endata={"token":token,"appId": "1527168518620319745","encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}  ##Change the appId if needed
        payload=parse.urlencode(endata)
        try:
            res = requests.request("POST", "https://api.yun-r.com/api/cloud/base/getDeviceInfo", headers=self.headers, data=payload)
            res.raise_for_status()
            temp=json.loads(res.text)
            result=json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
            print(result)
            if(result.get('success')==True):
                self.devices = result.get('data')
                return True
            else:
                return False
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print(f"Connection Error: {e}")
            return False

    def open_door(self,robotId,deviceUnique,token):
        # Post open door request
        self.opendoor_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","deviceUnique":"Null","sign":"Null","appCode":"00004V3","timeout":"60","callBackUrl":"Null","openCtrl":"1"}  ##Change the apCode if needed
        ## Change the value of callBackUrl and timeout (which means effect time that door open) to suit your situation
        self.opendoor_data["requestId"]=getUUID()
        self.opendoor_data["timestamp"]=int(round(time.time() * 1000))
        self.opendoor_data["robotId"] =robotId
        self.opendoor_data["deviceUnique"]=deviceUnique
        self.opendoor_data["sign"]=json.dumps(md5value(str(self.opendoor_data.get("appCode"))+str(self.opendoor_data.get("callBackUrl"))+str(self.opendoor_data.get("deviceUnique"))+str(self.opendoor_data.get("openCtrl"))+str(self.opendoor_data.get("projectId"))+str(self.opendoor_data.get("requestId"))+str(self.opendoor_data.get("robotId"))+str(self.opendoor_data.get("timestamp"))+str(self.opendoor_data.get("timeout"))+'F6B86C8FA70AC4CB'))  ##The last string should be your appSecret
        data='{"requestId":"'+self.opendoor_data.get("requestId")+'","timestamp":"'+str(self.opendoor_data.get("timestamp"))+'","robotId":"'+self.opendoor_data.get("robotId")+'","deviceUnique":"'+self.opendoor_data.get("deviceUnique")+'","appCode":"'+self.opendoor_data.get("appCode")+'","timeout":"'+self.opendoor_data.get("timeout")+'","callBackUrl":"'+self.opendoor_data.get("callBackUrl")+'","openCtrl":"'+self.opendoor_data.get("openCtrl")+'"}'
        endata={"token":token,"appId": "1527168518620319745","encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}  ##Change the appId if needed
        payload=parse.urlencode(endata)
        try:
            response = requests.request("POST", "https://api.yun-r.com/api/cloud/entrance/netOpenDoor", headers=self.headers, data=payload)
            if response :
                while(1):
                    temp=json.loads(response.text)
                    result=json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
                    print(result)
                    if(result.get('success')==True):
                        if result.get('data').get('wait')=='0' and result.get('data').get('isOpen')=='true':
                            return True
                        elif(result.get('data').get('wait')!='0'):
                            print("Need to wait")
                            return False
                        else:
                            print("Can't open the door")
                            return False
                            break
                    else:
                        return False
            else:
                print("Invalid response received")
                return False
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("Connection Error. "+str(e))
            return False

    def close_door(self,robotId,deviceUnique,token):
        # Post close door request
        self.opendoor_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","deviceUnique":"Null","sign":"Null","appCode":"00004V3","timeout":"10","callBackUrl":"Null","openCtrl":"0"}  ##Change the apCode if needed
        ## Change the value of callBackUrl to suit your situation
        self.opendoor_data["requestId"]=getUUID()
        self.opendoor_data["timestamp"]=int(round(time.time() * 1000))
        self.opendoor_data["robotId"] =robotId
        self.opendoor_data["deviceUnique"]=deviceUnique
        self.opendoor_data["sign"]=md5value(str(self.opendoor_data.get("appCode"))+str(self.opendoor_data.get("callBackUrl"))+str(self.opendoor_data.get("deviceUnique"))+str(self.opendoor_data.get("openCtrl"))+str(self.opendoor_data.get("projectId"))+str(self.opendoor_data.get("requestId"))+str(self.opendoor_data.get("robotId"))+str(self.opendoor_data.get("timestamp"))+str(self.opendoor_data.get("timeout"))+'F6B86C8FA70AC4CB')  ##The last string should be your appSecret
        data='{"requestId":"'+self.opendoor_data.get("requestId")+'","timestamp":"'+str(self.opendoor_data.get("timestamp"))+'","robotId":"'+self.opendoor_data.get("robotId")+'","deviceUnique":"'+self.opendoor_data.get("deviceUnique")+'","appCode":"'+self.opendoor_data.get("appCode")+'","timeout":"'+self.opendoor_data.get("timeout")+'","callBackUrl":"'+self.opendoor_data.get("callBackUrl")+'","openCtrl":"'+self.opendoor_data.get("openCtrl")+'"}'
        endata={"token":token,"appId": "1527168518620319745","encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}  ##Change the appId if needed
        payload=parse.urlencode(endata)
        try:
            response = requests.request("POST", "https://api.yun-r.com/api/cloud/entrance/netOpenDoor", headers=self.headers, data=payload)
            if response :
                while(1):
                    temp=json.loads(response.text)
                    result=json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
                    print(result)
                    if(result.get('success')==True):
                        if(result.get('data').get('wait')=='0' and result.get('data').get('isOpen')=='false'):
                            return True
                        elif(result.get('data').get('wait')!='0'):
                            print("Need to wait")
                            time.sleep(0.1)
                            get_mode(robotId,Door_name)
                        elif(result.get('data').get('wait')!='0'):
                            print("Robot has no task about this door")
                            return True
                        else:
                            print("Can't close the door")
                            return False
                            break
                    else:
                        return False 
            else:
                print("Invalid response received")
                return False
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("Connection Error. "+str(e))
            return False

    def get_mode(self,robotId,deviceUnique,token):
        # Get door's current state
        self.getmode_data = {"requestId":"Null","timestamp":"Null","robotId":"Null","appCode":"00004V3","deviceUnique":"Null"}  ##Change the appCode if needed
        self.getmode_data["requestId"]=getUUID()
        self.getmode_data["timestamp"]=json.dumps(int(round(time.time() * 1000)))
        self.getmode_data["robotId"] =robotId
        self.getmode_data["deviceUnique"]=deviceUnique
        data='{"requestId":"'+self.getmode_data.get("requestId")+'","timestamp":"'+self.getmode_data.get("timestamp")+'","robotId":"'+self.getmode_data.get("robotId")+'","appCode":"'+self.getmode_data.get("appCode")+'","deviceUnique":"'+self.getmode_data.get("deviceUnique")+'"}'
        endata={"token":token,"appId": "1527168518620319745","encryptType": "0", "encryptScript": self.aes.AES_encrypt(data)}  ##Change the appId if needed
        payload=parse.urlencode(endata)
        try:
            response = requests.request("POST", "https://api.yun-r.com/api/cloud/base/getDeviceStatus", headers=self.headers, data=payload)
            if response:
                temp=json.loads(response.text)
                result=json.loads(self.aes.AES_decrypt(json.dumps(temp.get('encryptScript'))))
                print(result)
                if(result.get('success')==True):
                    while(1):
                        if result.get('data').get('wait') =='0':
                            state = result.get('data').get('doorStatus')
                            if state is None:
                                return 4
                            elif state == '0' or state =='1':## Close
                                return 0
                            elif state == '6' or state == '4' or state == '3':## Open
                                return 2
                            elif state == '-1':## Offline
                                return 3
                                #state 3 should return 1 when it comes to reality!!!
                        else:
                            print("Need to wait")
                else:
                    return 0
            else:
                return 4
        except (socket.gaierror, urllib3.exceptions.NewConnectionError, urllib3.exceptions.MaxRetryError, requests.exceptions.HTTPError ,requests.exceptions.ReadTimeout, requests.exceptions.ConnectionError) as e:
            print("Connection Error. "+str(e))
            return 4

def getUUID():
    # Generate UUid
    return "".join(str(uuid.uuid4()).split("-")).upper()
    
def md5value(s):
    # Calculate md5 value
    # Used in generate sign
    return hashlib.md5(s.encode(encoding='utf-8')).hexdigest()

class Aes_ECB(object):
    def __init__(self):
        self.key = '8288EC12D8CFC60D'
        ## The key value is consistent with APP Secret
        ## Change the value to suit your case
        self.MODE = AES.MODE_ECB
        self.BS = AES.block_size
        self.pad = lambda s: s + (self.BS - len(s) % self.BS) * chr(self.BS - len(s) % self.BS)
        self.unpad = lambda s: s[0:-ord(s[-1])]

    def add_to_16(value):
        while len(value) % 16 != 0:
            value += '\0'
        return str.encode(value)  
        ## Return bytes


    def AES_encrypt(self, text):
        aes = AES.new(Aes_ECB.add_to_16(self.key), self.MODE)  
        ## Init encode module
        encrypted_text = str(base64.encodebytes(aes.encrypt(Aes_ECB.add_to_16(self.pad(text)))), encoding='utf-8').replace('\n', '')     
        ## The 'replace' may be not neccessary
        ## In test it works with 'replace' 
        ## Encode and return bytes
        return encrypted_text

    def AES_decrypt(self, text):
        # Init decode module
        aes = AES.new(Aes_ECB.add_to_16(self.key), self.MODE)
        base64_decrypted = base64.decodebytes(text.encode(encoding='utf-8'))
        decrypted_text = self.unpad(aes.decrypt(base64_decrypted).decode('utf-8'))
        decrypted_code = decrypted_text.rstrip('\0')
        return decrypted_code
