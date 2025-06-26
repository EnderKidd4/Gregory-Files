#!/usr/bin/python3
# coding=utf8
import sys
sys.path.append('/home/pi/mse112-ws-student/MasterPi//')
import cv2
import time
import math
import signal
import Camera
import threading
import numpy as np
import yaml_handle
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Sonar as Sonar
import HiwonderSDK.Misc as Misc
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum
from HiwonderSDK.PID import PID
import pandas as pd


# initialization
chassis = mecanum.MecanumChassis()
AK = ArmIK()
pitch_pid = PID(P=0.28, I=0.16, D=0.18)

HWSONAR = Sonar.Sonar()
distance = 0 

range_rgb = {
    'red': (0, 0, 255),
    'blue': (255, 0, 0),
    'green': (0, 255, 0),
    'black': (0, 0, 0),
    'white': (255, 255, 255),
}
img_centerx = 320
# Variable for distance obstacle avoidance
distance_data = []
stopMotor = False
Threshold = 10  # Set threshold for obstacle distance


# line tracking
roi = [ # [ROI, weight]
        (240, 280,  0, 640, 0.1), 
        (340, 380,  0, 640, 0.3), 
        (430, 460,  0, 640, 0.6)
       ]

roi_h1 = roi[0][0]
roi_h2 = roi[1][0] - roi[0][0]
roi_h3 = roi[2][0] - roi[1][0]

roi_h_list = [roi_h1, roi_h2, roi_h3]
size = (640, 480)




# Line patrol
if sys.version_info.major == 2:
    print('Please run this program with python3!')
    sys.exit(0)

def servo_init():

    # TODO 1. set the PWM of the Servos appropriately to position arm for line-tracking, use Board.setPWMServoPulse() 
    # /.....enter code here...../


# Set the detection color
def setTargetColor(target_color):
    global __target_color

    print("COLOR", target_color)
    __target_color = target_color
    return (True, ())

lab_data = None

def load_config():
    global lab_data
    lab_data = yaml_handle.get_yaml_data(yaml_handle.lab_file_path)

# initial position
def initMove():
    servo_init()
    MotorStop()
    
line_centerx = -1
# Variable reset
def reset():
    global line_centerx
    global __target_color
    
    line_centerx = -1
    __target_color = ()
    
# app initialization call
def init():
    print("VisualPatrol Init")
    load_config()
    initMove()

__isRunning = False
# app starts playing method call
def start():
    reset()

    global __isRunning
    global stopMotor
    global forward
    global turn
    global obstacle
    obstacle = False
    turn = True
    forward = True
    stopMotor = True
    __isRunning = True

    print("Line tracker 1.1 Start")

# app stops playing method calls
def stop():
    global __isRunning
    __isRunning = False
    MotorStop()
    print("Line tracker 1.1 Stop")

# app exit gameplay call
def exit():
    global __isRunning
    __isRunning = False
    MotorStop()
    print("Line tracker 1.1 Exit")

def setBuzzer(timer):
    Board.setBuzzer(0)
    Board.setBuzzer(1)
    time.sleep(timer)
    Board.setBuzzer(0)

def MotorStop():
    Board.setMotor(1, 0) 
    Board.setMotor(2, 0)
    Board.setMotor(3, 0)
    Board.setMotor(4, 0)

def SetMotors(speed):
    Board.setMotor(1, speed[1]) 
    Board.setMotor(2, speed[2])
    Board.setMotor(3, speed[3])
    Board.setMotor(4, speed[4])


#Close before processing
def Stop(signum, frame):
    global __isRunning
    
    __isRunning = False
    print('Closing...')
    MotorStop()  # Turn off all motors

    
# Find the contour with the largest area
# The parameter is a list of contours to be compared
def getAreaMaxContour(contours):
    contour_area_temp = 0
    contour_area_max = 0
    area_max_contour = None

    for c in contours:  # Iterate over all contours
        contour_area_temp = math.fabs(cv2.contourArea(c))  # Calculate the contour area
        if contour_area_temp > contour_area_max:
            contour_area_max = contour_area_temp
            if contour_area_temp >= 5:  # Only when the area is greater than 300, the contour of the largest area is valid to filter out interference
                area_max_contour = c

    return area_max_contour, contour_area_max  # Return the largest contour



def move():
   
    global line_centerx
    global obstacle

    i = 0
    while True:

        if __isRunning:
            if line_centerx != -1 and not obstacle:
                
                num = (line_centerx - img_centerx)
                if abs(num) <= 5:  # The deviation is small and no processing is performed
                    pitch_pid.SetPoint = num
                else:
                    pitch_pid.SetPoint = 0
                pitch_pid.update(num) 
                tmp = pitch_pid.output    # Get PID output value
                tmp = 100 if tmp > 100 else tmp   
                tmp = -100 if tmp < -100 else tmp
                base_speed = Misc.map(tmp, -100, 100, -40, 40)  # Speed ​​mapping

                # TODO 2. Given the base_speed from pid controller, Set motor speeds for motor 1, 2, 3 and 4, use  Board.setMotor()
                SetMotors(base_speed)
                
            else:
                MotorStop()

                if obstacle:

                    time.sleep(0.01)
                    # Pick
                    print("Obstacle Avoidance Start\n")

                    print("The obstacle distance is :\n")


                    # TODO 3. Obstacle avoidance routine
                    # move left (11 cm)
                    SetMotors([-20, 20, -20, 20])
                    time.sleep(4)
                    MotorStop()
                    time.sleep(1.5)

                    # move forward (4 cm)
                    SetMotors([20, 20, 20, 20])
                    time.sleep(1.5)
                    MotorStop()
                    time.sleep(1.5)

                    # move right (11 cm)
                    SetMotors([20, -20, 20, -20])
                    time.sleep(4)
                    MotorStop()
                    
                    print("complete, now turning off motors\n")
                    chassis.set_velocity(0,0,0)  # Turn off all motors

                    obstacle = False
                    print("Obstacle Avoidance End\n")
                    time.sleep(1.5)

        else:
            time.sleep(0.01)
 
# Run child thread
th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

def line_tracking (img, __target_color):
    global line_centerx

    # Camera line tracking
    img_copy = img.copy()
    img_h, img_w = img.shape[:2]
    
    if not __isRunning or __target_color == ():
        return img
     
    frame_resize = cv2.resize(img_copy, size, interpolation=cv2.INTER_NEAREST)
    frame_gb = cv2.GaussianBlur(frame_resize, (3, 3), 3)         
    centroid_x_sum = 0
    weight_sum = 0
    center_ = []
    n = 0

    # Split the image into three parts: upper, middle and lower. This will make the processing faster and more accurate.
    for r in roi:
        roi_h = roi_h_list[n]
        n += 1       
        blobs = frame_gb[r[0]:r[1], r[2]:r[3]]
        frame_lab = cv2.cvtColor(blobs, cv2.COLOR_BGR2LAB)  # Convert the image to LAB space
        area_max = 0
        areaMaxContour = 0
        for i in lab_data:
            if i in __target_color:
                detect_color = i

                # TODO create frame mask using cv2.inRange () function to perform bitwise operations on the original image
                frame_mask = cv2.inRange(frame_lab, 
                (lab_data[i]['min'][0], lab_data[i]['min'][1],lab_data[i]['min'][2]),
                (lab_data[i]['max'][0], lab_data[i]['max'][1],lab_data[i]['max'][2]))

                eroded = cv2.erode(frame_mask, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3)))  #corrosion
                dilated = cv2.dilate(eroded, cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))) #Expansion

        cnts = cv2.findContours(dilated , cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_TC89_L1)[-2]# Find all contours
        cnt_large, area = getAreaMaxContour(cnts)# Find the contour with the largest area
        if cnt_large is not None:#If the contour is not empty
            rect = cv2.minAreaRect(cnt_large)#Minimum enclosing rectangle
            box = np.int0(cv2.boxPoints(rect))#The four vertices of the minimum enclosing rectangle
            for i in range(4):
                box[i, 1] = box[i, 1] + (n - 1)*roi_h + roi[0][0]
                box[i, 1] = int(Misc.map(box[i, 1], 0, size[1], 0, img_h))
            for i in range(4):                
                box[i, 0] = int(Misc.map(box[i, 0], 0, size[0], 0, img_w))

            cv2.drawContours(img, [box], -1, (0,0,255,255), 2)#Draw a rectangle consisting of four points
        
            #Get the diagonal points of the rectangle
            pt1_x, pt1_y = box[0, 0], box[0, 1]
            pt3_x, pt3_y = box[2, 0], box[2, 1]            
            center_x, center_y = (pt1_x + pt3_x) / 2, (pt1_y + pt3_y) / 2#Center point       
            cv2.circle(img, (int(center_x), int(center_y)), 5, (0,0,255), -1)# Draw the center point         
            center_.append([center_x, center_y])                        
            #Sum the top, middle and bottom center points according to different weights
            centroid_x_sum += center_x * r[4]
            weight_sum += r[4]
    if weight_sum != 0:
        #Find the final center point
        line_centerx = int(centroid_x_sum / weight_sum)
        cv2.circle(img, (line_centerx, int(center_y)), 10, (0,255,255), -1)# Draw the center point
    else:
        line_centerx = -1
    return img




def run(img, __target_color):
    global __isRunning
    global stopMotor
    global distance_data
    global obstacle
    global distance


    # Ultrasonic sensor measurements
    dist = HWSONAR.getDistance() / 10.0

    if __isRunning:
        
        distance_data.append(dist)

        if len(distance_data) > 5:
            distance_data.pop(0)

        distance = np.mean(distance_data)

        # TODO 4. Using measured distance value, write code to stop motors and change obstacle flag to true when obstacle is within certain threshold
        if distance <= threshold:
            MotorStop()
            obstacle = true
        

        time.sleep(0.03)

        img = line_tracking(img,__target_color)

        return img


    

    


if __name__ == '__main__':
    
    init()
    start()
    
    signal.signal(signal.SIGINT, Stop)
    cap = cv2.VideoCapture(-1)
    __target_color = ('green',)
    while __isRunning:
        ret, img = cap.read()
        if ret:
            frame = img.copy()
            Frame = run(frame, __target_color)  
            frame_resize = cv2.resize(Frame, (320, 240))
            cv2.imshow('frame', frame_resize)
            key = cv2.waitKey(1)
            if key == 27:
                break
        else:
            time.sleep(0.01)
    cv2.destroyAllWindows()