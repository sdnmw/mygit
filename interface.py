# coding=utf-8
import os
from time import sleep
import json
import urllib2
from time import ctime
import RPi.GPIO as GPIO
import time
from smbus import SMBus
import sys
import tty, termios
import thread
# XRservo = SMBus(1)
from socket import *
import cv2
import numpy
import fcntl, struct

# socket.AF_INET用于服务器与服务器之间的网络通信
# socket.SOCK_STREAM代表基于TCP的流式socket通信


#######################################
#############信号引脚定义##############
#######################################
GPIO.setmode(GPIO.BCM)

########LED口定义#################
LED0 = 10
LED1 = 9
LED2 = 25

########电机驱动接口定义#################
ENA = 13  # //L298使能A
ENB = 20  # //L298使能B
IN1 = 19  # //电机接口1
IN2 = 16  # //电机接口2
IN3 = 21  # //电机接口3
IN4 = 26  # //电机接口4

########舵机接口定义#################

########超声波接口定义#################
ECHO = 4  # 超声波接收脚位  
TRIG = 17  # 超声波发射脚位

########红外传感器接口定义#################
IR_R = 18  # 小车右侧巡线红外
IR_L = 27  # 小车左侧巡线红外
IR_M = 22  # 小车中间避障红外
IRF_R = 23  # 小车跟随右侧红外
IRF_L = 24  # 小车跟随左侧红外
global Cruising_Flag
Cruising_Flag = 0  # //当前循环模式
global Pre_Cruising_Flag
Pre_Cruising_Flag = 0  # //预循环模式
buffer = ['00', '00', '00', '00', '00', '00']

#######################################
#########管脚类型设置及初始化##########
#######################################
GPIO.setwarnings(False)

#########led初始化为000##########
GPIO.setup(LED0, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(LED1, GPIO.OUT, initial=GPIO.HIGH)
GPIO.setup(LED2, GPIO.OUT, initial=GPIO.HIGH)

#########电机初始化为LOW##########
GPIO.setup(ENA, GPIO.OUT, initial=GPIO.LOW)
ENA_pwm = GPIO.PWM(ENA, 1000)
ENA_pwm.start(0)
ENA_pwm.ChangeDutyCycle(100)
GPIO.setup(IN1, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(IN2, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(ENB, GPIO.OUT, initial=GPIO.LOW)
ENB_pwm = GPIO.PWM(ENB, 1000)
ENB_pwm.start(0)
ENB_pwm.ChangeDutyCycle(100)
GPIO.setup(IN3, GPIO.OUT, initial=GPIO.LOW)
GPIO.setup(IN4, GPIO.OUT, initial=GPIO.LOW)

#########红外初始化为输入，并内部拉高#########
GPIO.setup(IR_R, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(IR_L, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(IR_M, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(IRF_R, GPIO.IN, pull_up_down=GPIO.PUD_UP)
GPIO.setup(IRF_L, GPIO.IN, pull_up_down=GPIO.PUD_UP)

##########超声波模块管脚类型设置#########
GPIO.setup(TRIG, GPIO.OUT, initial=GPIO.LOW)  # 超声波模块发射端管脚设置trig
GPIO.setup(ECHO, GPIO.IN, pull_up_down=GPIO.PUD_UP)  # 超声波模块接收端管脚设置echo


def ENA_Speed(EA_num):
    global left_speed
    left_speed = EA_num
    print 'EA_A改变啦 %d ' % EA_num
    ENA_pwm.ChangeDutyCycle(EA_num)


def ENB_Speed(EB_num):
    global right_speed
    right_speed = EB_num
    print 'EB_B改变啦 %d ' % EB_num
    ENB_pwm.ChangeDutyCycle(EB_num)


####################################################
##函数名称 Open_Light()
##函数功能 开大灯LED0
##入口参数 ：无
##出口参数 ：无
####################################################
def Open_Light():  # 开大灯LED0
    GPIO.output(LED0, False)  # 大灯正极接5V  负极接IO口
    time.sleep(1)


####################################################
##函数名称 Close_Light()
##函数功能 关大灯
##入口参数 ：无
##出口参数 ：无
####################################################
def Close_Light():  # 关大灯
    GPIO.output(LED0, True)  # 大灯正极接5V  负极接IO口
    time.sleep(1)


####################################################
##函数名称 init_light()
##函数功能 流水灯
##入口参数 ：无
##出口参数 ：无
####################################################
def init_light():  # 流水灯
    for i in range(1, 5):
        GPIO.output(LED0, False)  # 流水灯LED0
        GPIO.output(LED1, False)  # 流水灯LED1
        GPIO.output(LED2, False)  # 流水灯LED2
        time.sleep(0.5)
        GPIO.output(LED0, True)  # 流水灯LED0
        GPIO.output(LED1, False)  # 流水灯LED1
        GPIO.output(LED2, False)  # 流水灯LED2
        time.sleep(0.5)
        GPIO.output(LED0, False)  # 流水灯LED0
        GPIO.output(LED1, True)  # 流水灯LED1
        GPIO.output(LED2, False)  # 流水灯LED2
        time.sleep(0.5)
        GPIO.output(LED0, False)  # 流水灯LED0
        GPIO.output(LED1, False)  # 流水灯LED1
        GPIO.output(LED2, True)  # 流水灯LED2
        time.sleep(0.5)
        GPIO.output(LED0, False)  # 流水灯LED0
        GPIO.output(LED1, False)  # 流水灯LED1
        GPIO.output(LED2, False)  # 流水灯LED2
        time.sleep(0.5)
        GPIO.output(LED0, True)  # 流水灯LED0
        GPIO.output(LED1, True)  # 流水灯LED1
        GPIO.output(LED2, True)  # 流水灯LED2


##########机器人方向控制###########################
def Motor_Forward():
    print 'motor forward'
    GPIO.output(ENA, True)
    GPIO.output(ENB, True)
    GPIO.output(IN1, True)
    GPIO.output(IN2, False)
    GPIO.output(IN3, True)
    GPIO.output(IN4, False)
    GPIO.output(LED1, False)  # LED1亮
    GPIO.output(LED2, False)  # LED1亮


def Motor_Backward():
    print 'motor_backward'
    GPIO.output(ENA, True)
    GPIO.output(ENB, True)
    GPIO.output(IN1, False)
    GPIO.output(IN2, True)
    GPIO.output(IN3, False)
    GPIO.output(IN4, True)
    GPIO.output(LED1, True)  # LED1灭
    GPIO.output(LED2, False)  # LED2亮


def Motor_TurnLeft():
    print 'motor_turnleft'
    GPIO.output(ENA, True)
    GPIO.output(ENB, True)
    GPIO.output(IN1, True)
    GPIO.output(IN2, False)
    GPIO.output(IN3, False)
    GPIO.output(IN4, True)
    GPIO.output(LED1, False)  # LED1亮
    GPIO.output(LED2, True)  # LED2灭


def Motor_TurnRight():
    print 'motor_turnright'
    GPIO.output(ENA, True)
    GPIO.output(ENB, True)
    GPIO.output(IN1, False)
    GPIO.output(IN2, True)
    GPIO.output(IN3, True)
    GPIO.output(IN4, False)
    GPIO.output(LED1, False)  # LED1亮
    GPIO.output(LED2, True)  # LED2灭


def Motor_Stop():
    print 'motor_stop'
    GPIO.output(ENA, False)
    GPIO.output(ENB, False)
    GPIO.output(IN1, False)
    GPIO.output(IN2, False)
    GPIO.output(IN3, False)
    GPIO.output(IN4, False)
    GPIO.output(LED1, True)  # LED1灭
    GPIO.output(LED2, True)  # LED2亮


def camera():
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # 连接服务端
    address_server = ('10.0.0.1', 8010)
    sock.connect(address_server)

    # 从摄像头采集图像
    capture = cv2.VideoCapture(0)
    if capture != None:
        ret, frame = capture.read()
        encode_param = [int(cv2.IMWRITE_JPEG_QUALITY), 90]  # 设置编码参数

        while ret:
            # 首先对图片进行编码，因为socket不支持直接发送图片
            result, imgencode = cv2.imencode('.jpg', frame)
            data = numpy.array(imgencode)
            stringData = data.tostring()
            # 首先发送图片编码后的长度
            sock.send(str(len(stringData)).ljust(16))
            # 然后一个字节一个字节发送编码的内容
            # 如果是python对python那么可以一次性发送，如果发给c++的server则必须分开发因为编码里面有字符串结束标志位，c++会截断
            for i in range(0, len(stringData)):
                sock.send(stringData[i])
            ret, frame = capture.read()
            # cv2.imshow('CLIENT',frame)
            # if cv2.waitKey(10) == 27:
            #     break
            # 接收server发送的返回信息
            data_r = sock.recv(50)
            print (data_r)

        sock.close()
        cv2.destroyAllWindows()
    else:
        soc()
        


# get host_ip
def get_localip(ifname):
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    return socket.inet_ntoa(fcntl.ioctl(s.fileno(), 0x8915, struct.pack('256s', ifname[:15]))[20:24])


# parse json
def read(obj, key):
    collect = list()
    for k in obj:
        v = obj[k]
        if isinstance(v, dict):
            collect.extend(read(v, k))
        elif isinstance(v, list):
            if key == '':
                collect.extend(readList(v, k))
            else:
                collect.extend(readList(v, key + "." + k))
        else:
            if key == '':
                collect.append({k: v})
            else:
                collect.append({str(key) + "." + k: v})
    return collect


def readList(obj, key):
    collect = list()
    for index, item in enumerate(obj):
        for k in item:
            v = item[k]
            if isinstance(v, dict):
                collect.extend(read(v, key + "[" + str(index) + "]"))
            elif isinstance(v, list):
                collect.extend(readList(v, key + "[" + str(index) + "]"))
            else:
                collect.append({key + "[" + str(index) + "]" + "." + k: v})
    return collect

def soc():
    HOST = "10.0.0.3"
    PORT = 21567
    ADDR = (HOST, PORT)

    tcpCliSock = socket(AF_INET, SOCK_STREAM)
    tcpCliSock.connect(ADDR)

    while True:
        data = "picamera is shutdown please connect to 10.0.0.1"
        if not data:
            break

        tcpCliSock.send(data.encode("utf8"))
        break
        

    tcpCliSock.close()
url = 'http://10.0.0.1:8080/wm/staticflowpusher/list/all/json'
flow = urllib2.urlopen(url).read()
if __name__ == "__main__":
    while True:
        ip_port = ('10.0.0.1', 8888)
        sk = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, 0)
        sk.bind(ip_port)
        flow_new = urllib2.urlopen(url).read()
        if flow_new != flow:
            ojt = json.loads(flow_new)
            j = json.dumps(read(ojt, ''))
            print j[-14:-8]
            if j[-13:-8] == "group":
                print "car"
                while True:

                    data = sk.recv(1024)
                    print data
                    if data == 'w':  # wasd控制小车走动
                        print 'move forward'
                        Motor_Forward()
                    elif data == 's':
                        print 'move back'
                        Motor_Backward()
                    elif data == 'a':
                        Motor_TurnLeft()
                        print "turn left!"
                    elif data == 'd':
                        Motor_TurnRight()
                        print "turn right!"
                    elif data == 'p':
                        print "camera is invoked"
                        camera()
                    elif data == 'q':
                        Motor_Stop()
                        print "turn right!"
                    
                    # else:
                #	Motor_Stop()
                #	break  

