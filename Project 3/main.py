import time
import sys
import threading
import subprocess
import os
import signal

sys.path.append('/home/pi/mse112-ws-student/MasterPi/')
import yaml_handle
from ArmIK.Transform import *
from ArmIK.ArmMoveIK import *
import HiwonderSDK.Board as Board
import HiwonderSDK.mecanum as mecanum

chassis = mecanum.MecanumChassis()
start = True
pick_up = True
search_left = False
search_right = False
stop_threads = False
detected_object = "none"
target_object = "dog"

ik = IK('arm')
AK = ArmIK()

def stop(signum, frame):
    global stop_threads, start
    start = False
    stop_threads = True
    print('Stopping...')

def run_cpp_program():
    subprocess.run(["bash", "run_yolo.sh"])

# Initial position
def init_detect_left():
    global search_left

    Board.setPWMServoPulse(5, 1500, 300)
    time.sleep(1)
    Board.setPWMServoPulse(3, 500, 500)
    time.sleep(1)
    Board.setPWMServoPulse(4, 2300, 500)
    time.sleep(1)
    Board.setPWMServoPulse(6, 2500, 500)
    time.sleep(5)

    search_left = True

def init_detect_right():
    global search_right

    Board.setPWMServoPulse(5, 1500, 300)
    time.sleep(1)
    Board.setPWMServoPulse(3, 500, 500)
    time.sleep(1)
    Board.setPWMServoPulse(4, 2300, 500)
    time.sleep(1)
    Board.setPWMServoPulse(6, 500, 500)
    time.sleep(5)

    search_right = True

def init_move():
    Board.setPWMServoPulse(1, 2500, 300)
    time.sleep(1)
    Board.setPWMServoPulse(3, 900, 500)
    time.sleep(1)
    Board.setPWMServoPulse(4, 2200, 500)
    time.sleep(1)
    Board.setPWMServoPulse(5, 1950, 500)
    time.sleep(1)
    Board.setPWMServoPulse(6, 1500, 500)

def move():
    global pick_up, detected_object
    global search_left, search_right, start, stop_threads
    coordinate = {
        # TODO set coordinates appropriately depending on placement of object
        #using the coordinates from project 2 as a starting point:
        'place_left': (24, 15, 2),
        'place_right': (-24, 15, 2),
        'pick': (0, 18, 1)
    }

    init_move()

    while not stop_threads:
        while True:
            detected_object = "none"
            if pick_up:
                print("IN Pick-Up\n")
                Board.setPWMServoPulse(1, 2000, 500)  # Open claws
                time.sleep(1)

                # TODO set coordinates appropriately depending on placement of object
                #dont touch this code im using it as an example ty
                AK.setPitchRangeMoving(coordinate['pick'], 90, -90, 90)
                time.sleep(3)
                Board.setPWMServoPulse(1, 1000, 500)  # Close paw
                time.sleep(0.5)
                pick_up = False  # turn off pick_up flag
                search_left = True #begin searching left
                init_detect_left()

            if search_left:
                print("Object_left: \n",detected_object)
                print("In Search Left\n")
                if detected_object == target_object:
                    print("IN PLACE DOWN LEFT\n")

                    # TODO Implement placing left mechanism, Hint see if "pick_up"
                    #code based on if"pick_up", changed coordinate to place_left
                    #changed flags to true or false to begin search to the right
                    AK.setPitchRangeMoving(coordinate['place_left'], 90, -90, 90)
                    time.sleep(0.5)
                    Board.setPWMServoPulse(1, 2500, 500)  # open paw
                    time.sleep(0.5)
                    search_left = False  # turn off search_left flag
                    pick_up = True  #go back to pick up position
                    
                else:
                   
                    print("now going Right\n")
                    init_detect_right()


            if search_right:
                print("Object_right: \n",detected_object)
                print("In Search Right\n")
                if detected_object == target_object:
                    print("IN PLACE DOWN RIGHT\n")

                    # TODO Implement placing right mechanism, , Hint see if "pick_up"
                    #code based on if"pick_up", changed coordinate to place_right and detect right
                    #and search_right
                    AK.setPitchRangeMoving(coordinate['place_right'], 90, -90, 90)
                    time.sleep(0.5)
                    Board.setPWMServoPulse(1, 2500, 500)  # open paw
                    time.sleep(0.5)
                    search_right = False  # turn off searching flag
                    pick_up = True  #go back to pick up position

                else:
                   
                    print("now going Left\n")
                    init_detect_left()


def read_pipe():
    global detected_object, stop_threads
    while not stop_threads:
        with open(pipe_path, 'r') as pipe:
            detected_object = pipe.readline().strip()

th = threading.Thread(target=move)
th.setDaemon(True)
th.start()

cpp_thread = threading.Thread(target=run_cpp_program)
cpp_thread.start()

pipe_path = "/tmp/yolox_pipe"
if not os.path.exists(pipe_path):
    os.mkfifo(pipe_path)

pipe_thread = threading.Thread(target=read_pipe)
pipe_thread.setDaemon(True)
pipe_thread.start()

def main():
    print("Program start, looking for", target_object)

signal.signal(signal.SIGINT, stop)

if __name__ == '__main__':
    main()