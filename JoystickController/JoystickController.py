from DebugLog.DebugLog import *
from pygame.locals import *
from Motors import Motors_TMC5072_eval, Motors_TMC5130_eval

import time

class MotorController:
    MOTOR_X_ID = 0
    MOTOR_Y_ID = 1

    MOTOR_STEP_SIZE = int(200 * 256 / 5) #number of steps per rotation * motor number of microsteps per full step / axis lead (5mm)
    MOTOR_STEPS_PER_ROTATION = int(200 * 256)
    MOTOR_STEP_VELOCITY = 75000

class PS3GamePad:
    # joysticks
    LEFTJOY_X_AXIS = 0
    LEFTJOY_Y_AXIS = 1
    RIGHTJOY_X_AXIS = 2
    RIGHTJOY_Y_AXIS = 3

    # buttons
    DPAD_UP = 4
    DPAD_RIGHT = 5
    DPAD_DOWN = 6
    DPAD_LEFT = 7

    CIRCLE_BUTTON = 13
    CROSS_BUTTON = 14
    SQUARE_BUTTON = 15

class JoystickController:
    def __init__(self, fine_motors, coarse_motor, x, y, x_home, y_home, name="", cross_callback=None):
        # Private
        self.__name = name

        self.__fine_motors = fine_motors
        self.__fine_motors.rest_registers()
        self.__coarse_motor = coarse_motor
        self.__coarse_motor.rest_registers()

        self.__tohome = False
        self.__dpad_lr_pressed = False
        self.__dpad_ud_pressed = False

        # used for GUI (don't affect motors)
        self.__x_position = x
        self.__y_position = y
        self.__x_homeposition = x_home
        self.__y_homeposition = y_home

        # Public
        self.x_change = 0
        self.y_change = 0
        self.x_coarse_change = 0

        #Function that can be called when Cross button is pressed (intended for use with run_manual_callback)
        self.cross_callback = cross_callback

        if name:
            DebugLog.debugprint(self, "Controller connected: " + name)

    # position to display to GUI
    def get_position(self):
        return self.__x_position, self.__y_position

    # check if motor is stalled
    def is_motor_stalled(self, motors, motor_ID):
        return motors.readRegisterField(motors.fields.EVENT_STOP_SG[motor_ID])

    # check if motor's actual position is equal to target position
    def did_motor_reach_position(self, motors, motor_ID):
        return motors.getAxisParameter(motors.APs.ActualPosition, motor_ID) == motors.getAxisParameter(motors.APs.TargetPosition, motor_ID)

    # update position and motor motion on screen update
    def update_position(self, x, y):
        # update position to display to GUI
        self.__x_position = x
        self.__y_position = y

        # check if either motor is stalled
        x_stalled = self.is_motor_stalled(self.__fine_motors, MotorController.MOTOR_X_ID)
        y_stalled = self.is_motor_stalled(self.__fine_motors, MotorController.MOTOR_Y_ID)
        x_coarse_stalled = self.__coarse_motor.readRegisterField(self.__coarse_motor.fields.EVENT_STOP_SG)

        str_stalled = []

        if x_stalled:
            str_stalled.append("X")
        if y_stalled:
            str_stalled.append("Y")
        if x_coarse_stalled:
            str_stalled.append("X_c")

        if str_stalled:
            str_stalled = ", ".join(str_stalled)
            DebugLog.debugprint(self, "Motor " + str_stalled + " stalled. Wait 3 seconds...")
            time.sleep(3)
            DebugLog.debugprint(self, "Motor " + str_stalled + " stall cleared.")
        
        # TODO: GUI doesn't properly represent moving to home
        # motors are moving to home position
        if self.__tohome:
            if self.did_motor_reach_position(self.__fine_motors, MotorController.MOTOR_X_ID) and self.did_motor_reach_position(self.__fine_motors, MotorController.MOTOR_Y_ID):
                DebugLog.debugprint(self, "Reached home.")
                self.__tohome = False
                self.__fine_motors.stop(MotorController.MOTOR_X_ID)
                self.__fine_motors.stop(MotorController.MOTOR_Y_ID)
                self.x_change = 0
                self.y_change = 0

            elif self.did_motor_reach_position(self.__fine_motors, MotorController.MOTOR_X_ID):
                self.__fine_motors.stop(MotorController.MOTOR_X_ID)
                self.x_change = 0

            elif self.did_motor_reach_position(self.__fine_motors, MotorController.MOTOR_Y_ID):
                self.__fine_motors.stop(MotorController.MOTOR_Y_ID)
                self.y_change = 0
        
        # motors are stepping
        if self.__dpad_lr_pressed:
            while not self.did_motor_reach_position(self.__fine_motors, MotorController.MOTOR_X_ID):
                pass            
            self.__fine_motors.stop(MotorController.MOTOR_X_ID)
            self.__dpad_lr_pressed = False
            self.x_change = 0
            DebugLog.debugprint(self, "Stopped moving. Current position: " + str(self.__x_position) + " , " + str(self.__y_position))

        if self.__dpad_ud_pressed:
            while not self.did_motor_reach_position(self.__fine_motors, MotorController.MOTOR_Y_ID):
                pass            
            self.__fine_motors.stop(MotorController.MOTOR_Y_ID)
            self.__dpad_ud_pressed = False
            self.y_change = 0
            DebugLog.debugprint(self, "Stopped moving. Current position: " + str(self.__x_position) + " , " + str(self.__y_position))
        
    # force all motors to stop
    def force_stop(self):
        DebugLog.debugprint(self, "Force stop. Current position: " + str(self.__x_position) + " , " + str(self.__y_position))
        self.__fine_motors.stop(MotorController.MOTOR_X_ID)
        self.__fine_motors.stop(MotorController.MOTOR_Y_ID)
        self.__coarse_motor.stop(MotorController.MOTOR_X_ID)
        self.x_change = 0
        self.y_change = 0
        self.x_coarse_change = 0

    # move motors based on joystick inputs
    def joystick_event(self, event):
        DebugLog.debugprint(self, event)

        if event.value == 0:
            DebugLog.debugprint(self, "Stopped moving. Current position: " + str(self.__x_position) + " , " + str(self.__y_position))

        # left joystick: course axis motion control
        if event.axis == PS3GamePad.LEFTJOY_X_AXIS:
            DebugLog.debugprint(self, "Moving coarse left-right...")

            if event.value == 0:
                self.__coarse_motor.stop(MotorController.MOTOR_X_ID)

            else:
                value = int(Motors_TMC5130_eval.VELOCITY_LOW * abs(event.value))
                if event.value < 0:
                    self.__coarse_motor.rotate_ccw(MotorController.MOTOR_X_ID, value)
                elif event.value > 0:
                    self.__coarse_motor.rotate_cw(MotorController.MOTOR_X_ID, value)

            self.x_coarse_change = event.value * MotorController.MOTOR_STEP_SIZE

        # right joystick: fine-axis motion control
        elif event.axis == PS3GamePad.RIGHTJOY_X_AXIS:
            DebugLog.debugprint(self, "Moving left-right...")

            if event.value == 0:
                self.__fine_motors.stop(MotorController.MOTOR_X_ID)

            else:
                value = int(Motors_TMC5072_eval.VELOCITY_LOW * abs(event.value))
                if event.value < 0:
                    self.__fine_motors.rotate_ccw(MotorController.MOTOR_X_ID, value)
                elif event.value > 0:
                    self.__fine_motors.rotate_cw(MotorController.MOTOR_X_ID, value)

            self.x_change = event.value * MotorController.MOTOR_STEP_SIZE

        elif event.axis == PS3GamePad.RIGHTJOY_Y_AXIS:
            DebugLog.debugprint(self, "Moving up-down...")

            if event.value == 0:
                self.__fine_motors.stop(MotorController.MOTOR_Y_ID)

            else:
                value = int(Motors_TMC5072_eval.VELOCITY_LOW * abs(event.value))
                if event.value < 0:
                    self.__fine_motors.rotate_cw(MotorController.MOTOR_Y_ID, value)
                elif event.value > 0:
                    self.__fine_motors.rotate_ccw(MotorController.MOTOR_Y_ID, value)

            self.y_change = event.value * MotorController.MOTOR_STEP_SIZE

    # dpad: step motors
    # cross button: force motors to stop
    # circle button: move to home position
    def button_event(self, event):
        DebugLog.debugprint(self, event)

        # cross button: force stop
        if event.button == PS3GamePad.SQUARE_BUTTON:
            self.force_stop()

        elif event.button == PS3GamePad.CROSS_BUTTON:
            if callable(self.cross_callback):
                self.cross_callback()

        # circle button: home
        elif event.button == PS3GamePad.CIRCLE_BUTTON:
            DebugLog.debugprint(self, "Moving to home...")

            self.__tohome = True

            if self.__x_position < self.__x_homeposition:
                self.x_change = MotorController.MOTOR_STEP_SIZE

            elif self.__x_position > self.__x_homeposition:
                self.x_change = -MotorController.MOTOR_STEP_SIZE

            else:
                self.x_change = 0

            if self.__y_position < self.__y_homeposition:
                self.y_change = MotorController.MOTOR_STEP_SIZE

            elif self.__y_position > self.__y_homeposition:
                self.y_change = -MotorController.MOTOR_STEP_SIZE

            else:
                self.y_change = 0
            
            # home is defined as position of motors on startup
            self.__fine_motors.moveTo(MotorController.MOTOR_X_ID, 0, Motors_TMC5072_eval.VELOCITY_LOW)
            self.__fine_motors.moveTo(MotorController.MOTOR_Y_ID, 0, Motors_TMC5072_eval.VELOCITY_LOW)
            self.__coarse_motor.moveTo(MotorController.MOTOR_X_ID, 0, Motors_TMC5130_eval.VELOCITY_LOW)

        # dpad: step motion control
        elif event.button == PS3GamePad.DPAD_UP:
            DebugLog.debugprint(self, "Stepping up...")
            self.__dpad_ud_pressed = True
            self.__fine_motors.moveBy(MotorController.MOTOR_Y_ID, MotorController.MOTOR_STEP_SIZE, MotorController.MOTOR_STEP_VELOCITY)
            self.y_change = -MotorController.MOTOR_STEP_SIZE

        elif event.button == PS3GamePad.DPAD_RIGHT:
            DebugLog.debugprint(self, "Stepping right...")
            self.__dpad_lr_pressed = True
            self.__fine_motors.moveBy(MotorController.MOTOR_X_ID, MotorController.MOTOR_STEP_SIZE, MotorController.MOTOR_STEP_VELOCITY)
            self.x_change = MotorController.MOTOR_STEP_SIZE            

        elif event.button == PS3GamePad.DPAD_DOWN:
            DebugLog.debugprint(self, "Stepping down...")
            self.__dpad_ud_pressed = True
            self.__fine_motors.moveBy(MotorController.MOTOR_Y_ID, -MotorController.MOTOR_STEP_SIZE, MotorController.MOTOR_STEP_VELOCITY)
            self.y_change = MotorController.MOTOR_STEP_SIZE            

        elif event.button == PS3GamePad.DPAD_LEFT:
            DebugLog.debugprint(self, "Stepping left...")
            self.__dpad_lr_pressed = True
            self.__fine_motors.moveBy(MotorController.MOTOR_X_ID, -MotorController.MOTOR_STEP_SIZE, MotorController.MOTOR_STEP_VELOCITY)
            self.x_change = -MotorController.MOTOR_STEP_SIZE

    def __del__(self):
        if self.__name:
            DebugLog.debugprint(self, "Controller disconnected: " + self.__name)

'''
For Testing: Use keyboard input to move GUI cursor
'''
class KeyboardController:
    def __init__(self, x, y, x_home, y_home, name="Keyboard"):
        DebugLog.debugprint(self)
        # Private
        self.__name = name
        self.__tohome = False
        self.__x_position = x
        self.__y_position = y
        self.__x_homeposition = x_home
        self.__y_homeposition = y_home

        # Public
        self.x_change = 0
        self.y_change = 0

    def get_position(self):
        return self.__x_position, self.__y_position

    def update_position(self, x, y):
        self.__x_position = x
        self.__y_position = y

        if self.__tohome:
            if self.__x_position == self.__x_homeposition and self.__y_position == self.__y_homeposition:
                DebugLog.debugprint(self, "Reached home.")
                self.__tohome = False
                self.x_change = 0
                self.y_change = 0

            elif self.__x_position == self.__x_homeposition:
                self.x_change = 0

            elif self.__y_position == self.__y_homeposition:
                self.y_change = 0

    def force_stop(self):
        DebugLog.debugprint(self, "Force stop. Current position: " + str(self.__x_position) + " , " + str(self.__y_position))        
        self.x_change = 0
        self.y_change = 0

    # step in direction
    def arrowkeysdown_event(self, event):
        DebugLog.debugprint(self, event)

        if event.key == K_LEFT:
            DebugLog.debugprint(self, "Moving left...")
            self.x_change = -MotorController.MOTOR_STEP_SIZE

        elif event.key == K_RIGHT:
            DebugLog.debugprint(self, "Moving right...")
            self.x_change = MotorController.MOTOR_STEP_SIZE

        elif event.key == K_UP:
            DebugLog.debugprint(self, "Moving up...")
            self.y_change = -MotorController.MOTOR_STEP_SIZE

        elif event.key == K_DOWN:
            DebugLog.debugprint(self, "Moving down...")
            self.y_change = MotorController.MOTOR_STEP_SIZE

    def arrowkeysup_event(self, event):
        DebugLog.debugprint(self, event)

        if event.key == K_LEFT or event.key == K_RIGHT:
            DebugLog.debugprint(self, "Stopped moving. Current position: " + str(self.__x_position) + " , " + str(self.__y_position))
            self.x_change = 0

        elif event.key == K_DOWN or event.key == K_UP:
            DebugLog.debugprint(self, "Stopped moving. Current position: " + str(self.__x_position) + " , " + str(self.__y_position))
            self.y_change = 0

    # move to home position
    def spacekeydown_event(self, event):
        DebugLog.debugprint(self, event)
        DebugLog.debugprint(self, "Moving to home...")

        self.__tohome = True

        if self.__x_position < self.__x_homeposition:
            self.x_change = MotorController.MOTOR_STEP_SIZE

        elif self.__x_position > self.__x_homeposition:
            self.x_change = -MotorController.MOTOR_STEP_SIZE

        if self.__y_position < self.__y_homeposition:
            self.y_change = MotorController.MOTOR_STEP_SIZE

        elif self.__y_position > self.__y_homeposition:
            self.y_change = -MotorController.MOTOR_STEP_SIZE
        
    # force stop
    def xkeydown_event(self, event):
        DebugLog.debugprint(self, event)
        self.force_stop()