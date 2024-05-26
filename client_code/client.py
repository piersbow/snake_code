import socket
import numpy as np
import math, cmath
import subprocess
from json import dumps
from time import sleep

import joint_positions

server_ip = "10.42.0.1"

client_socket = socket.socket()  # instantiate
client_socket.connect((server_ip, 5000))  # connect to the server

# Module angle offsets e.g. modules not being straight
THETA_OFFSETS = np.array([0, np.pi, 0, np.pi, 0, np.pi, 0])

# Joint multipliers e.g. joint is backwards for some reason
THETA_MULTIPLIERS = np.array([1, 1, 1, 1, 1, 1, 1])
ALPHA_MULTIPLIERS = np.array([1, 1, 1, 1, 1, 1, 1])

SWAP_MOTORS = np.array([0, 0, 0, 0, 0, 0, 0])

HALF_MODULE_LENGTH = 0.07   # 7cm in meters
HALF_WHEEL_SPACING = 0.045        # 4.5cm in meters

NUM_DUMMY_WHEELS = 2


joints = joint_positions.JointPositions()

def get_servo_duty_cycles(alpha, theta):
    # angle_a and angle_b in radians
    complex_pos = cmath.rect(alpha / math.pi, theta) + 0.5 + 0.5j
    return complex_pos.real, complex_pos.imag


def send_data(data):
    client_socket.send(data)
    # wait for ack
    assert client_socket.recv(1024) == b'ack'

# Format to send data to snake
#
# [[data for the head],
#  [[servo a pos, servo b pos, wheel a speed, wheel b speed],
#   [servo a pos, servo b pos, wheel a speed, wheel b speed],
#   [servo a pos, servo b pos, wheel a speed, wheel b speed],
#   [servo a pos, servo b pos, wheel a speed, wheel b speed],
#   [servo a pos, servo b pos, wheel a speed, wheel b speed]]]


if __name__ == '__main__':

    background_video = subprocess.Popen(["C:\\Users\\Piers\\Documents\\snake_code\\venv\\Scripts\\python.exe", './video_feed.py'])
    try:
        while True:
            # get joint angles
            joints.update_positions()


            # adjust wheel speeds based on turning radius
            # find turning radius

            # horizontal component of the angle at each joint
            half_horizontal_angle = np.multiply(np.sin(joints.joints_alpha), np.cos(joints.joints_theta)) / 2

            radius = HALF_MODULE_LENGTH / np.tan(half_horizontal_angle)

            # get motor speeds
            left_speed = np.nan_to_num(np.divide((radius - HALF_WHEEL_SPACING), radius), nan=1) * joints.velocity
            right_speed = np.nan_to_num(np.divide((radius + HALF_WHEEL_SPACING), radius), nan=1) * joints.velocity

            # check if any speeds above 1, if so normalise
            max_speed = max(np.max(left_speed), np.max(right_speed))
            if max_speed > 1:
                left_speed = left_speed / max_speed
                right_speed = right_speed / max_speed


            # add "changes" to joints
            alpha = joints.joints_alpha * ALPHA_MULTIPLIERS
            theta = (joints.joints_theta + THETA_OFFSETS) * THETA_MULTIPLIERS

            wheel_left = np.zeros_like(alpha)
            wheel_right = np.zeros_like(alpha)

            for i in range(len(wheel_left)):
                if SWAP_MOTORS[i]:
                    wheel_left[i] = right_speed[i]
                    wheel_right[i] = left_speed[i]
                else:
                    wheel_left[i] = left_speed[i]
                    wheel_right[i] = right_speed[i]

            # prepare data for sending
            data = []

            # BUT there are also "dud" modules at the back with only wheels
            for i in range(NUM_DUMMY_WHEELS):
                speed = joints.velocity
                if speed > 1:
                    speed = joints.velocity / max_speed
                data.append((0.5, 0.5, speed, speed))

            # add data for "real" modules
            for i in range(len(alpha)):
                servo_a, servo_b = get_servo_duty_cycles(alpha[i], theta[i])
                data.append((servo_a, servo_b, wheel_left[i], wheel_right[i]))


            send_data(dumps(data).encode())

            sleep(0.01)
    except:
        background_video.kill()