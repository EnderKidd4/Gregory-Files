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
place_down_left = False
place_down_right = False
search_left = False
search_right = False
stop_threads = False
object_left = "none"
object_right = "none"
detected_object = "none"

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

    search_left = True

def init_detect_right():
    global search_right

    Board.setPWMServoPulse(5, 1500, 300)
    time.sleep(1)
    Board.setPWMServoPulse(3, 500, 500)
    time.sleep(0.5)
    Board.setPWMServoPulse(4, 2300, 500)
    time.sleep(0.5)
    Board.setPWMServoPulse(6, 500, 500)
    time.sleep(3)

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
    global pick_up, place_down_left, place_down_right, detected_object
    global search_left, search_right, start, stop_threads, object_left, object_right

    coordinate = {
        # TODO set coordinates appropriately depending on placement of object
        'place_left': (18, 0, 0),
        'place_right': (-18, 0, 0),
        'pick': (0, ik.l2 + ik.l4, ik.l1 - ik.l3)
    }

    init_move()

    while not stop_threads:
        while True:
            if pick_up:
                print("IN Pick-Up\n")
                Board.setPWMServoPulse(1, 2000, 500)  # Open claws
                time.sleep(1)

                # TODO set coordinates appropriately depending on placement of object
                AK.setPitchRangeMoving(coordinate['pick'], 90, -90, 90)
                time.sleep(3)
                Board.setPWMServoPulse(1, 1000, 500)  # Close paw
                time.sleep(0.5)
                pick_up = False  # turn off pick_up flag
                search_left = True
                init_detect_left()

            if search_left:
                object_left = detected_object
                print("Object_left: \n",object_left)
                print("In Search Left\n")
                if place_down_left:
                    print("IN PLACE DOWN LEFT\n")

                    # TODO Implement placing left mechanism, Hint see if "pick_up"

                else:
                    print("now going Right\n")
                    init_detect_right()


            if search_right:
                object_right = detected_object
                print("Object_right: \n",object_right)
                print("In Search Right\n")
                if place_down_right:
                    print("IN PLACE DOWN RIGHT\n")

                    # TODO Implement placing right mechanism, , Hint see if "pick_up"

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
    global start, place_down_left, place_down_right, stop_threads, object_left, object_right, detected_object

    # TODO explain working of this function
    target_object = "dog"
    while not stop_threads:
        if object_right == target_object:
            place_down_right = True
        elif object_left == target_object:
            place_down_left = True

signal.signal(signal.SIGINT, stop)

if __name__ == '__main__':
    main()