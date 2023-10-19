
'''
Controller to move system to one of 12 x 2 pre-defined positions:

---------       -----------
 1B | 2B | ... | 11B | 12B |
---------       -----------
 1F | 2F | ... | 11F | 12F |
---------       -----------

Positions are grouped in 4s (30.5 cm total, 3.8 cm radius ea.), with 1.25 cm gaps between groups
Centres of furthest positions are 86.4 cm apart
Centres of front-back positions are 12 cm apart

Long actuator: 82 cm travel distance
short actuator: 22.3 cm travel distance


'''

import tkinter as tk
import tkinter.ttk as ttk

from JoystickController.JoystickController import MotorController
from DebugLog.DebugLog import *


class PositionControllerView():
    # distances, in mm
    FINE_ROTATION_DIST = 2      # 0.01 mm per step * 200 steps per rotation
    COARSE_ROTATION_DIST = 10   # 0.05 mm per step * 200 steps per rotation

    NEXT_POSITION_DIST = 76
    GAP_DIST = 12.5
    FRONTBACK_DIST = 80 #120
    COARSE_TOEND_DIST = 35      # 820 mm actuator length - (76 mm * 10 + 12.5 mm * 2)
    FINE_TOEND_DIST = 41        # (76 mm * 11 + 12.5 mm * 2) - 820 mm actuator length
    
    COARSE_STEPSIZE = int(MotorController.MOTOR_STEPS_PER_ROTATION * NEXT_POSITION_DIST / COARSE_ROTATION_DIST)
    COARSE_TOEND_STEPSIZE = int(MotorController.MOTOR_STEPS_PER_ROTATION * COARSE_TOEND_DIST / COARSE_ROTATION_DIST)
    FINE_TOEND_STEPSIZE = int(MotorController.MOTOR_STEPS_PER_ROTATION * FINE_TOEND_DIST / FINE_ROTATION_DIST)

    MAX_MICE_COUNT = 12

    CANVAS_RECT_WIDTH = 100
    CANVAS_RECT_HEIGHT = 40

    def __init__(self, frame, fine_motors=None, coarse_motor=None, mouse_info_label=None, config_params=None):
        self.__master = frame

        self.__fine_motors = fine_motors
        self.__coarse_motor = coarse_motor

        self.mouse_info_label = mouse_info_label
        self.config_params = config_params

        # set up UI buttons
        position_updown_frame = ttk.Frame(self.__master)
        position_updown_frame.grid(row=0, column=0)

        self.__up_icon = tk.PhotoImage(file=r".\assets\up_.png")
        position_up_button = ttk.Button(position_updown_frame, image=self.__up_icon, command=self.position_up_button_event)
        position_up_button.pack(side=tk.TOP)
        self.__down_icon = tk.PhotoImage(file=r".\assets\down_.png")
        position_down_button = ttk.Button(position_updown_frame, image=self.__down_icon, command=self.position_down_button_event)
        position_down_button.pack(side=tk.BOTTOM)

        self.__position_canvas = tk.Canvas(self.__master, width=1200, height=80)
        self.__position_canvas.grid(row=0, column=1)

        self.__position_rect_dict = {}

        for i in range(PositionControllerView.MAX_MICE_COUNT):
            width = PositionControllerView.CANVAS_RECT_WIDTH
            height = PositionControllerView.CANVAS_RECT_HEIGHT
            col_index = i * width

            key = 'B' + str(i + 1)
            self.__position_rect_dict[key] = self.__position_canvas.create_rectangle(col_index, 0, col_index + width, height, fill='white')
            key = 'F' + str(i + 1)
            self.__position_rect_dict[key] = self.__position_canvas.create_rectangle(col_index, height, col_index + width, 2 * height, fill='white')
            self.__position_canvas.create_text((col_index + 50, 20), text=str(i + 1))
            self.__position_canvas.create_text((col_index + 50, height + 20), text=str(i + 1))

        # assumes starting position at F1
        self.__current_position_key = 'F1'
        self.__position_canvas.itemconfig(self.__position_rect_dict[self.__current_position_key], fill='yellow')
        # detect click events
        self.__position_canvas.bind("<Button-1>", self.canvas_clicked_event)

        position_leftright_frame = ttk.Frame(self.__master)
        position_leftright_frame.grid(row=0, column=2)

        self.__left_icon = tk.PhotoImage(file=r".\assets\left_.png")
        position_left_button = ttk.Button(position_leftright_frame, image=self.__left_icon, command=self.position_left_button_event)
        position_left_button.pack(side=tk.LEFT)
        self.__right_icon = tk.PhotoImage(file=r".\assets\right_.png")
        position_right_button = ttk.Button(position_leftright_frame, image=self.__right_icon, command=self.position_right_button_event)
        position_right_button.pack(side=tk.RIGHT)

        self.__reached_end = False

    # get the current position
    def get_current_position(self):
        return self.__current_position_key

    # move to the given position
    # exceptions: invalid position name
    def move_to_position(self, position, block_until_stopped=False):
        moved_coarse_x = False
        moved_fine_x = False
        moved_fine_y = False
        # TODO: validate position name
        if position[0] == 'F' and self.__current_position_key[0] == 'B':
            # move to the front
            self.position_down_button_event()
            moved_fine_y = True

        elif position[0] == 'B' and self.__current_position_key[0] == 'F':
            # move to the back
            self.position_up_button_event()
            moved_fine_y = True

        move_to = int(position[1:])
        current = int(self.__current_position_key[1:])
        count = abs(move_to - current)
        # move left
        if move_to < current:
            moved_coarse_x, moved_fine_x = self.move_to_left(count)
        # move right
        elif move_to > current:
            moved_coarse_x, moved_fine_x = self.move_to_right(count)

        # block until position is reached
        if block_until_stopped:
            while not self.did_motors_stop(moved_coarse_x, moved_fine_x, moved_fine_y):
                pass

    def did_motors_stop(self, moved_coarse_x, moved_fine_x, moved_fine_y):
        result = True

        if self.__fine_motors and self.__coarse_motor:
            if moved_coarse_x:
                result = result and self.__coarse_motor.readRegisterField(self.__coarse_motor.fields.POSITION_REACHED) == 1
            if moved_fine_x:
                result = result and self.__fine_motors.getAxisParameter(self.__fine_motors.APs.ActualPosition, MotorController.MOTOR_X_ID) == self.__fine_motors.getAxisParameter(self.__fine_motors.APs.TargetPosition, MotorController.MOTOR_X_ID)
            if moved_fine_y:
                result = result and self.__fine_motors.getAxisParameter(self.__fine_motors.APs.ActualPosition, MotorController.MOTOR_Y_ID) == self.__fine_motors.getAxisParameter(self.__fine_motors.APs.TargetPosition, MotorController.MOTOR_Y_ID)

        return result

    # move system to the left
    # return: if coarse and/or fine motors are moving
    def move_to_left(self, count=1):
        moved_coarse_x = False
        moved_fine_x = False

        if int(self.__current_position_key[1:]) - (count - 1) > 1:
            if self.__fine_motors and self.__coarse_motor:
                stepsize = 0
                if int(self.__current_position_key[1:]) == 2 + (count - 1) and self.__reached_end:
                    self.__reached_end = False
                    # to get to position 1, reach end of long actuator (76 mm -> 41 mm) then use short actuator (41 mm -> 0 mm)
                    stepsize = -PositionControllerView.COARSE_TOEND_STEPSIZE - PositionControllerView.COARSE_STEPSIZE * (count - 1)

                    self.__fine_motors.moveBy(MotorController.MOTOR_X_ID, -PositionControllerView.FINE_TOEND_STEPSIZE, MotorController.MOTOR_STEP_VELOCITY)
                    moved_fine_x = True

                else:
                    stepsize = -PositionControllerView.COARSE_STEPSIZE * count
                    for i in range(count):
                        if int(self.__current_position_key[1:]) - i % 4 == 1:
                            stepsize -= int(MotorController.MOTOR_STEPS_PER_ROTATION * PositionControllerView.GAP_DIST / PositionControllerView.COARSE_ROTATION_DIST)

                self.__coarse_motor.moveBy(MotorController.MOTOR_X_ID, stepsize, MotorController.MOTOR_STEP_VELOCITY)
                moved_coarse_x = True

            # redraw canvas
            self.__position_canvas.itemconfig(self.__position_rect_dict[self.__current_position_key], fill='white')
            self.__current_position_key = self.__current_position_key[0] + str(int(self.__current_position_key[1:]) - count)
            self.__position_canvas.itemconfig(self.__position_rect_dict[self.__current_position_key], fill='yellow')

            if self.mouse_info_label:
                self.mouse_info_label.mouse_ID = self.__current_position_key
                self.mouse_info_label.read_hdf5_info()
                self.mouse_info_label.update_label()

            message = 'Moving to position ' + self.__current_position_key + '...'
            DebugLog.debugprint(self, message)

        return moved_coarse_x, moved_fine_x

    # move system to the right
    # return: if coarse and/or fine motors are moving
    def move_to_right(self, count=1):
        moved_coarse_x = False
        moved_fine_x = False

        if int(self.__current_position_key[1:]) + (count - 1) < PositionControllerView.MAX_MICE_COUNT:
            if self.__fine_motors and self.__coarse_motor:
                stepsize = 0
                if int(self.__current_position_key[1:]) == PositionControllerView.MAX_MICE_COUNT - 1 - (count - 1) and not self.__reached_end:
                    self.__reached_end = True
                    # to get to position 12, reach end of long actuator (785 mm -> 820 mm) then use short actuator (820 mm -> 861 mm)
                    stepsize = PositionControllerView.COARSE_TOEND_STEPSIZE + PositionControllerView.COARSE_STEPSIZE * (count - 1)

                    self.__fine_motors.moveBy(MotorController.MOTOR_X_ID, PositionControllerView.FINE_TOEND_STEPSIZE, MotorController.MOTOR_STEP_VELOCITY)
                    moved_fine_x = True

                else:
                    stepsize = PositionControllerView.COARSE_STEPSIZE * count
                    for i in range(count):
                        if int(self.__current_position_key[1:]) + i % 4 == 0:
                            stepsize += int(MotorController.MOTOR_STEPS_PER_ROTATION * PositionControllerView.GAP_DIST / PositionControllerView.COARSE_ROTATION_DIST)

                self.__coarse_motor.moveBy(MotorController.MOTOR_X_ID, stepsize, MotorController.MOTOR_STEP_VELOCITY)
                moved_coarse_x = True

            # redraw canvas
            self.__position_canvas.itemconfig(self.__position_rect_dict[self.__current_position_key], fill='white')
            self.__current_position_key = self.__current_position_key[0] + str(int(self.__current_position_key[1:]) + count)
            self.__position_canvas.itemconfig(self.__position_rect_dict[self.__current_position_key], fill='yellow')

            if self.mouse_info_label:
                self.mouse_info_label.mouse_ID = self.__current_position_key
                self.mouse_info_label.update_label()

            message = 'Moving to position ' + self.__current_position_key + '...'
            DebugLog.debugprint(self, message)

        return moved_coarse_x, moved_fine_x

    # move to the clicked position
    def canvas_clicked_event(self, event):
        # B: (:, 0:40), F: (:, 40:80)
        # 1: (0:100,:), 2: (100:200, :), ...
        position = ''
        if event.y >= 0 and event.y <= PositionControllerView.CANVAS_RECT_HEIGHT:
            position += 'B'
        elif event.y > PositionControllerView.CANVAS_RECT_HEIGHT and event.y <= PositionControllerView.CANVAS_RECT_HEIGHT * 2:
            position += 'F'
        for i in range(PositionControllerView.MAX_MICE_COUNT):
            if event.x > i * PositionControllerView.CANVAS_RECT_WIDTH and event.x <= (i + 1) * PositionControllerView.CANVAS_RECT_WIDTH:
                position += str(i + 1)
                break

        if position:
            self.move_to_position(position)

    # move system to the back
    def position_up_button_event(self):
        if self.__current_position_key[0] == 'F':
            if self.__fine_motors:
                stepsize = int(MotorController.MOTOR_STEPS_PER_ROTATION * PositionControllerView.FRONTBACK_DIST / PositionControllerView.FINE_ROTATION_DIST)
                self.__fine_motors.moveBy(MotorController.MOTOR_Y_ID, stepsize, MotorController.MOTOR_STEP_VELOCITY)

            self.__position_canvas.itemconfig(self.__position_rect_dict[self.__current_position_key], fill='white')
            self.__current_position_key = 'B' + self.__current_position_key[1:]
            self.__position_canvas.itemconfig(self.__position_rect_dict[self.__current_position_key], fill='yellow')

            message = 'Moving to position ' + self.__current_position_key + '...'
            DebugLog.debugprint(self, message)

    # move system to the front
    def position_down_button_event(self):
        if self.__current_position_key[0] == 'B':
            if self.__fine_motors:
                stepsize = -int(MotorController.MOTOR_STEPS_PER_ROTATION * PositionControllerView.FRONTBACK_DIST / PositionControllerView.FINE_ROTATION_DIST)
                self.__fine_motors.moveBy(MotorController.MOTOR_Y_ID, stepsize, MotorController.MOTOR_STEP_VELOCITY)

            self.__position_canvas.itemconfig(self.__position_rect_dict[self.__current_position_key], fill='white')
            self.__current_position_key = 'F' + self.__current_position_key[1:]
            self.__position_canvas.itemconfig(self.__position_rect_dict[self.__current_position_key], fill='yellow')

            message = 'Moving to position ' + self.__current_position_key + '...'
            DebugLog.debugprint(self, message)

    # move system to the left
    def position_left_button_event(self):
        self.move_to_left()

    # move system to the right
    def position_right_button_event(self):
        self.move_to_right()

    def update_mouse_info_label(self):
        self.mouse_info_label.config(text="MOUSE INFO")