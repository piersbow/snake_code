from inputs import get_gamepad
import math, cmath
import threading
import numpy as np
from time import perf_counter


NUMBER_JOINTS = 7

# Movement propagation stuff
SMOOTHING_POINTS = 20
BUFFER_SPACES = 5
PROPAGATE_DISTANCE = 0.8

SPEED = 20

RIGHT_STICK_WEIGHTS = [0, 0, 0, 0.3, 0.5, 0.6, 0.7]


class XboxController(object):
    MAX_TRIG_VAL = math.pow(2, 8)
    MAX_JOY_VAL = math.pow(2, 15)

    def __init__(self):

        self.LeftJoystickY = 0
        self.LeftJoystickX = 0
        self.RightJoystickY = 0
        self.RightJoystickX = 0
        self.LeftTrigger = 0
        self.RightTrigger = 0
        self.LeftBumper = 0
        self.RightBumper = 0
        self.A = 0
        self.X = 0
        self.Y = 0
        self.B = 0
        self.LeftThumb = 0
        self.RightThumb = 0
        self.Back = 0
        self.Start = 0
        self.LeftDPad = 0
        self.RightDPad = 0
        self.UpDPad = 0
        self.DownDPad = 0

        self._monitor_thread = threading.Thread(target=self._monitor_controller, args=())
        self._monitor_thread.daemon = True
        self._monitor_thread.start()

    def _monitor_controller(self):
        while True:
            events = get_gamepad()
            for event in events:
                if event.code == 'ABS_Y':
                    self.LeftJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_X':
                    self.LeftJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_RY':
                    self.RightJoystickY = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_RX':
                    self.RightJoystickX = event.state / XboxController.MAX_JOY_VAL # normalize between -1 and 1
                elif event.code == 'ABS_Z':
                    self.LeftTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'ABS_RZ':
                    self.RightTrigger = event.state / XboxController.MAX_TRIG_VAL # normalize between 0 and 1
                elif event.code == 'BTN_TL':
                    self.LeftBumper = event.state
                elif event.code == 'BTN_TR':
                    self.RightBumper = event.state
                elif event.code == 'BTN_SOUTH':
                    self.A = event.state
                elif event.code == 'BTN_NORTH':
                    self.Y = event.state #previously switched with X
                elif event.code == 'BTN_WEST':
                    self.X = event.state #previously switched with Y
                elif event.code == 'BTN_EAST':
                    self.B = event.state
                elif event.code == 'BTN_THUMBL':
                    self.LeftThumb = event.state
                elif event.code == 'BTN_THUMBR':
                    self.RightThumb = event.state
                elif event.code == 'BTN_SELECT':
                    self.Back = event.state
                elif event.code == 'BTN_START':
                    self.Start = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY1':
                    self.LeftDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY2':
                    self.RightDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY3':
                    self.UpDPad = event.state
                elif event.code == 'BTN_TRIGGER_HAPPY4':
                    self.DownDPad = event.state


class JointPositions:
    def __init__(self):
        self.controller = XboxController()
        self.joints_raw_x = np.zeros((NUMBER_JOINTS * SMOOTHING_POINTS,))
        self.joints_raw_y = np.zeros((NUMBER_JOINTS * SMOOTHING_POINTS,))

        self.joints_theta = np.zeros((NUMBER_JOINTS,))
        self.joints_alpha = np.zeros((NUMBER_JOINTS,))

        self.distance_since_last_push = 0
        self.previous_time = perf_counter()

        self.velocity = 0

    def update_positions(self):
        x, y = self.controller.LeftJoystickX, self.controller.LeftJoystickY
        self.velocity = self.controller.RightTrigger

        right_x, right_y = self.controller.RightJoystickX, self.controller.RightJoystickY

        # is it time to shift?
        if self.distance_since_last_push > PROPAGATE_DISTANCE:
            # How many shifts?
            for i in range(0, math.floor(self.distance_since_last_push / PROPAGATE_DISTANCE)):
                # left shift joint values
                self.joints_raw_x[:-1] = self.joints_raw_x[1:]
                self.joints_raw_y[:-1] = self.joints_raw_y[1:]
            self.distance_since_last_push = self.distance_since_last_push % PROPAGATE_DISTANCE

        # make all front joint be current value
        self.joints_raw_x[-SMOOTHING_POINTS:] = x
        self.joints_raw_y[-SMOOTHING_POINTS:] = y

        for i in range(NUMBER_JOINTS):
            x = np.average(self.joints_raw_x[i * SMOOTHING_POINTS:((i + 1) * SMOOTHING_POINTS) - BUFFER_SPACES])
            y = np.average(self.joints_raw_y[i * SMOOTHING_POINTS:((i + 1) * SMOOTHING_POINTS) - BUFFER_SPACES])

            # add the change from the right stick
            x += RIGHT_STICK_WEIGHTS[i] * right_x
            y += RIGHT_STICK_WEIGHTS[i] * right_y


            # now that we have the joystick position for each joint, covert this into angles
            magnitude, theta = cmath.polar(complex(x, y))
            alpha = min(1.0, magnitude) * math.pi / 2

            self.joints_alpha[i] = alpha
            self.joints_theta[i] = theta

        self.distance_since_last_push += self.velocity * (perf_counter() - self.previous_time) * SPEED
        self.previous_time = perf_counter()

        return
