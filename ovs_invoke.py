# coding=utf-8
import os
from time import sleep
import json
import urllib2
from time import ctime
import RPi.GPIO as GPIO
import time
from smbus import SMBus
import  sys  
import  tty, termios
import thread
#XRservo = SMBus(1)
import socket
import cv2
import numpy


def capture():
    cap=cv2.VideoCapture(0)
    i=0
    while(1):
        ret ,frame = cap.read()
        k=cv2.waitKey(1)&0XFF
        if k==ord('q'):
            break
        elif k==ord('s'):
            cv2.imwrite(str(i)+'.jpg',frame)
            i+=1
        cv2.imshow("capture", frame)

    cap.release()
    cv2.destroyAllWindows()


            
        
     

#######################################
#############信号引脚定义##############
#######################################
GPIO.setmode(GPIO.BCM)

########LED口定义#################
LED0 = 10
LED1 = 9
LED2 = 25

########电机驱动接口定义#################
ENA = 13	#//L298使能A
ENB = 20	#//L298使能B
IN1 = 19	#//电机接口1
IN2 = 16	#//电机接口2
IN3 = 21	#//电机接口3
IN4 = 26	#//电机接口4

########舵机接口定义#################

########超声波接口定义#################
ECHO = 4	#超声波接收脚位  
TRIG = 17	#超声波发射脚位

########红外传感器接口定义#################
IR_R = 18	#小车右侧巡线红外
IR_L = 27	#小车左侧巡线红外
IR_M = 22	#小车中间避障红外
IRF_R = 23	#小车跟随右侧红外
IRF_L = 24	#小车跟随左侧红外
global Cruising_Flag
Cruising_Flag = 0	#//当前循环模式
global Pre_Cruising_Flag
Pre_Cruising_Flag = 0 	#//预循环模式
buffer = ['00','00','00','00','00','00']

#######################################
#########管脚类型设置及初始化##########
#######################################
GPIO.setwarnings(False)

#########led初始化为000##########
GPIO.setup(LED0,GPIO.OUT,initial=GPIO.HIGH)
GPIO.setup(LED1,GPIO.OUT,initial=GPIO.HIGH)
GPIO.setup(LED2,GPIO.OUT,initial=GPIO.HIGH)

#########电机初始化为LOW##########
GPIO.setup(ENA,GPIO.OUT,initial=GPIO.LOW)
ENA_pwm=GPIO.PWM(ENA,1000) 
ENA_pwm.start(0) 
ENA_pwm.ChangeDutyCycle(100)
GPIO.setup(IN1,GPIO.OUT,initial=GPIO.LOW)
GPIO.setup(IN2,GPIO.OUT,initial=GPIO.LOW)
GPIO.setup(ENB,GPIO.OUT,initial=GPIO.LOW)
ENB_pwm=GPIO.PWM(ENB,1000) 
ENB_pwm.start(0) 
ENB_pwm.ChangeDutyCycle(100)
GPIO.setup(IN3,GPIO.OUT,initial=GPIO.LOW)
GPIO.setup(IN4,GPIO.OUT,initial=GPIO.LOW)



#########红外初始化为输入，并内部拉高#########
GPIO.setup(IR_R,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(IR_L,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(IR_M,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(IRF_R,GPIO.IN,pull_up_down=GPIO.PUD_UP)
GPIO.setup(IRF_L,GPIO.IN,pull_up_down=GPIO.PUD_UP)



##########超声波模块管脚类型设置#########
GPIO.setup(TRIG,GPIO.OUT,initial=GPIO.LOW)#超声波模块发射端管脚设置trig
GPIO.setup(ECHO,GPIO.IN,pull_up_down=GPIO.PUD_UP)#超声波模块接收端管脚设置echo


def ENA_Speed(EA_num):
	global left_speed
	left_speed=EA_num
	print 'EA_A改变啦 %d '%EA_num
	ENA_pwm.ChangeDutyCycle(EA_num)

def ENB_Speed(EB_num):
	global right_speed
	right_speed=EB_num
	print 'EB_B改变啦 %d '%EB_num
	ENB_pwm.ChangeDutyCycle(EB_num)
####################################################
##函数名称 Open_Light()
##函数功能 开大灯LED0
##入口参数 ：无
##出口参数 ：无
####################################################
def	Open_Light():#开大灯LED0
	GPIO.output(LED0,False)#大灯正极接5V  负极接IO口
	time.sleep(1)

####################################################
##函数名称 Close_Light()
##函数功能 关大灯
##入口参数 ：无
##出口参数 ：无
####################################################
def	Close_Light():#关大灯
	GPIO.output(LED0,True)#大灯正极接5V  负极接IO口
	time.sleep(1)
	
####################################################
##函数名称 init_light()
##函数功能 流水灯
##入口参数 ：无
##出口参数 ：无
####################################################
def	init_light():#流水灯
	for i in range(1, 5):
		GPIO.output(LED0,False)#流水灯LED0
		GPIO.output(LED1,False)#流水灯LED1
		GPIO.output(LED2,False)#流水灯LED2
		time.sleep(0.5)
		GPIO.output(LED0,True)#流水灯LED0
		GPIO.output(LED1,False)#流水灯LED1
		GPIO.output(LED2,False)#流水灯LED2
		time.sleep(0.5)
		GPIO.output(LED0,False)#流水灯LED0
		GPIO.output(LED1,True)#流水灯LED1
		GPIO.output(LED2,False)#流水灯LED2
		time.sleep(0.5)
		GPIO.output(LED0,False)#流水灯LED0
		GPIO.output(LED1,False)#流水灯LED1
		GPIO.output(LED2,True)#流水灯LED2
		time.sleep(0.5)
		GPIO.output(LED0,False)#流水灯LED0
		GPIO.output(LED1,False)#流水灯LED1
		GPIO.output(LED2,False)#流水灯LED2
		time.sleep(0.5)
		GPIO.output(LED0,True)#流水灯LED0
		GPIO.output(LED1,True)#流水灯LED1
		GPIO.output(LED2,True)#流水灯LED2
##########机器人方向控制###########################
def Motor_Forward():
	print 'motor forward'
	GPIO.output(ENA,True)
	GPIO.output(ENB,True)
	GPIO.output(IN1,True)
	GPIO.output(IN2,False)
	GPIO.output(IN3,True)
	GPIO.output(IN4,False)
	GPIO.output(LED1,False)#LED1亮
	GPIO.output(LED2,False)#LED1亮
	
def Motor_Backward():
	print 'motor_backward'
	GPIO.output(ENA,True)
	GPIO.output(ENB,True)
	GPIO.output(IN1,False)
	GPIO.output(IN2,True)
	GPIO.output(IN3,False)
	GPIO.output(IN4,True)
	GPIO.output(LED1,True)#LED1灭
	GPIO.output(LED2,False)#LED2亮
	
def Motor_TurnLeft():
	print 'motor_turnleft'
	GPIO.output(ENA,True)
	GPIO.output(ENB,True)
	GPIO.output(IN1,True)
	GPIO.output(IN2,False)
	GPIO.output(IN3,False)
	GPIO.output(IN4,True)
	GPIO.output(LED1,False)#LED1亮
	GPIO.output(LED2,True) #LED2灭
def Motor_TurnRight():
	print 'motor_turnright'
	GPIO.output(ENA,True)
	GPIO.output(ENB,True)
	GPIO.output(IN1,False)
	GPIO.output(IN2,True)
	GPIO.output(IN3,True)
	GPIO.output(IN4,False)
	GPIO.output(LED1,False)#LED1亮
	GPIO.output(LED2,True) #LED2灭
def Motor_Stop():
	print 'motor_stop'
	GPIO.output(ENA,False)
	GPIO.output(ENB,False)
	GPIO.output(IN1,False)
	GPIO.output(IN2,False)
	GPIO.output(IN3,False)
	GPIO.output(IN4,False)
	GPIO.output(LED1,True)#LED1灭
	GPIO.output(LED2,True)#LED2亮

     
                       

while True:
    j=1
    for j in range(10):
        s = os.popen(" ovs-ofctl dump-flows br0")
        try:
            s = s.read().split('\n')[j].split(',')[-1].split(' ')[-1].split(':')[-1].split('=')[1]
          
            
            if s == "picamera":
               capture()
            elif s == "car_move":
                while True:
                    print "car is going to move"
                    fd = sys.stdin.fileno()
                    old_settings = termios.tcgetattr(fd)
                    # old_settings[3]= old_settings[3] & ~termios.ICANON & ~termios.ECHO
                    try:
                        tty.setraw(fd)
                        ch = sys.stdin.read(1)
                    finally:
                        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                    # print 'error'
                    if ch == 'w':  # wasd控制小车走动
                        Motor_Forward()
                        ENA_Speed(EA_num)
                        ENA_Speed(EA_num)
                        ENA_Speed(EA_num)
                        ENA_Speed(EA_num)
                        ENA_Speed(EA_num)
                    elif ch == 's':
                        
                        Motor_Backward()
                    elif ch == 'a':
                        Motor_TurnLeft()
                        
                    elif ch == 'd':
                        Motor_TurnRight()
			
                    else:
                        Motor_Stop()
                        break

            
                    
                    
                
                    
        except Exception as e:
            pass
    
