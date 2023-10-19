import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import showerror
import pygame
import threading
import pywinusb.hid as hid
from msvcrt import kbhit

from JoystickController.JoystickController import JoystickController, PS3GamePad, MotorController
from DebugLog.DebugLog import *


class PS3GamePadRawDataHandler:
    NAME = 'PS3 GamePad'

    LEFTJOY_X = 'LeftJoyX'
    LEFTJOY_Y = 'LeftJoyY'
    RIGHTJOY_X = 'RightJoyX'
    RIGHTJOY_Y = 'RightJoyY'
    DPAD_UP = 'DpadUp'
    DPAD_RIGHT = 'DpadRight'
    DPAD_DOWN = 'DpadDown'
    DPAD_LEFT = 'DpadLeft'
    CIRCLE = 'Circle'
    CROSS = 'Cross'

    LEFTJOYX_IDX = 6
    LEFTJOYY_IDX = 7
    RIGHTJOYX_IDX = 8
    RIGHTJOYY_IDX = 9

    DUP_IDX = 14
    DRIGHT_IDX = 15
    DDOWN_IDX = 16
    DLEFT_IDX = 17
    CIRCLE_IDX = 23
    CROSS_IDX = 24

    def __init__(self):
        self.__events = {}
        self.__observers = []

    def bind_to(self, callback):
        self.__observers.append(callback)

    def process(self, data):
        '''
        Left joy: [1, 0, 0, 0, 0, 0, {0-255 l-r}, (0-255 u-d), 128, 128, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 238, 20, 0, 0, 0, 0, 2, 17, 119, 1, 29, 2, 0, 1, 240, 1, 132, 1, 244]
        Eight joy: [1, 0, 0, 0, 0, 0, 128, 128, {0-255 l-r}, (0-255 u-d), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 238, 20, 0, 0, 0, 0, 2, 17, 119, 1, 29, 2, 0, 1, 240, 1, 132, 1, 244]
        DUp: [1, 0, (16), 0, 0, 0, 128, 128, 128, 128, 0, 0, 0, 0, (255), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 238, 20, 0, 0, 0, 0, 2, 17, 119, 1, 29, 2, 0, 1, 240, 1, 132, 1, 244]
        DRight: [1, 0, (32), 0, 0, 0, 128, 128, 128, 128, 0, 0, 0, 0, 0, (255), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 238, 20, 0, 0, 0, 0, 2, 17, 119, 1, 29, 2, 0, 1, 240, 1, 132, 1, 244]
        DDown: [1, 0, (64), 0, 0, 0, 128, 128, 128, 128, 0, 0, 0, 0, 0, 0, (255), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 238, 20, 0, 0, 0, 0, 2, 17, 119, 1, 29, 2, 0, 1, 240, 1, 132, 1, 244]
        DLeft: [1, 0, (128), 0, 0, 0, 128, 128, 128, 128, 0, 0, 0, 0, 0, 0, 0, (255), 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 3, 238, 20, 0, 0, 0, 0, 2, 17, 119, 1, 29, 2, 0, 1, 240, 1, 132, 1, 244]
        Circle: [1, 0, (32), 0, 0, 0, 128, 128, 128, 128, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (255), 0, 0, 0, 0, 0, 3, 238, 20, 0, 0, 0, 0, 2, 17, 119, 1, 29, 2, 0, 1, 240, 1, 132, 1, 244]
        Cross: [1, 0, 0, (64), 0, 0, 128, 128, 128, 128, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, (255), 0, 0, 0, 0, 3, 238, 20, 0, 0, 0, 0, 2, 17, 119, 1, 29, 2, 0, 1, 240, 1, 132, 1, 244]
        '''

        self.__events.clear()
        if data[PS3GamePadRawDataHandler.LEFTJOYX_IDX] != 128:
            self.__events[PS3GamePadRawDataHandler.LEFTJOY_X] = (data[PS3GamePadRawDataHandler.LEFTJOYX_IDX] - 128) / 128
        if data[PS3GamePadRawDataHandler.LEFTJOYY_IDX] != 128:
            self.__events[PS3GamePadRawDataHandler.LEFTJOY_Y] = (data[PS3GamePadRawDataHandler.LEFTJOYY_IDX] - 128) / 128
        if data[PS3GamePadRawDataHandler.RIGHTJOYX_IDX] != 128:
            self.__events[PS3GamePadRawDataHandler.RIGHTJOY_X] = (data[PS3GamePadRawDataHandler.RIGHTJOYX_IDX] - 128) / 128
        if data[PS3GamePadRawDataHandler.RIGHTJOYY_IDX] != 128:
            self.__events[PS3GamePadRawDataHandler.RIGHTJOY_Y] = (data[PS3GamePadRawDataHandler.RIGHTJOYY_IDX] - 128) / 128
        if data[PS3GamePadRawDataHandler.DUP_IDX] == 255:
            self.__events[PS3GamePadRawDataHandler.DPAD_UP] = 1
        if data[PS3GamePadRawDataHandler.DRIGHT_IDX] == 255:
            self.__events[PS3GamePadRawDataHandler.DPAD_RIGHT] = 1
        if data[PS3GamePadRawDataHandler.DDOWN_IDX] == 255:
            self.__events[PS3GamePadRawDataHandler.DPAD_DOWN] = 1
        if data[PS3GamePadRawDataHandler.DLEFT_IDX] == 255:
            self.__events[PS3GamePadRawDataHandler.DPAD_LEFT] = 1
        if data[PS3GamePadRawDataHandler.CIRCLE_IDX] == 255:
            self.__events[PS3GamePadRawDataHandler.CIRCLE] = 1
        if data[PS3GamePadRawDataHandler.CROSS_IDX] == 255:
            self.__events[PS3GamePadRawDataHandler.CROSS] = 1

        for callback in self.__observers:
            callback(self.__events)

class JoystickControllerView:
    # exceptions: on connection error
    def __init__(self, frame, fine_motors=None, coarse_motor=None, disable_joystick=False, cross_callback=None):
        self.__master = frame

        self.__fine_motors = fine_motors
        self.__coarse_motor = coarse_motor

        # connect to joystick controller
        self.__controller = None
        self.__joystick_device = None
        self.__joystickcontroller_thread = None
        self.__joystick_rawdatahandler = None
        self.__joystick_stopped = True

        if fine_motors and coarse_motor:
            name = None
            if not disable_joystick:
                # exceptions: on connection error
                name = self.connect_controller()
                self.__joystick_rawdatahandler = PS3GamePadRawDataHandler()
                self.__joystick_rawdatahandler.bind_to(self.joystickcontroller_event)
                self.__joystickcontroller_thread = threading.Thread(target=self.poll_joystickcontroller, daemon=True)

            self.__controller = JoystickController(self.__fine_motors, self.__coarse_motor, 0, 0, 0, 0, name,cross_callback=cross_callback)

        # set up UI buttons
        self.__left_icon = tk.PhotoImage(file=r".\assets\left_.png")
        self.__right_icon = tk.PhotoImage(file=r".\assets\right_.png")
        self.__up_icon = tk.PhotoImage(file=r".\assets\up_.png")
        self.__down_icon = tk.PhotoImage(file=r".\assets\down_.png")
        self.__fastup_icon = tk.PhotoImage(file=r".\assets\up.png")
        self.__fastleft_icon = tk.PhotoImage(file=r".\assets\left.png")
        self.__fastright_icon = tk.PhotoImage(file=r".\assets\right.png")
        self.__fastdown_icon = tk.PhotoImage(file=r".\assets\down.png")
        self.__home_icon = tk.PhotoImage(file=r".\assets\center.png")

        self.__buttons = []
        self.__up_button = ttk.Button(frame, image=self.__up_icon)
        self.__up_button.grid(row=1, column=2)
        self.__buttons.append(self.__up_button)
        self.__left_button = ttk.Button(frame, image=self.__left_icon)
        self.__left_button.grid(row=2, column=1)
        self.__buttons.append(self.__left_button)
        self.__right_button = ttk.Button(frame, image=self.__right_icon)
        self.__right_button.grid(row=2, column=3)
        self.__buttons.append(self.__right_button)
        self.__down_button = ttk.Button(frame, image=self.__down_icon)
        self.__down_button.grid(row=3, column=2)
        self.__buttons.append(self.__down_button)
        self.__fastup_button = ttk.Button(frame, image=self.__fastup_icon)
        self.__fastup_button.grid(row=0, column=2)
        self.__buttons.append(self.__fastup_button)
        self.__fastleft_button = ttk.Button(frame, image=self.__fastleft_icon)
        self.__fastleft_button.grid(row=2, column=0)
        self.__buttons.append(self.__fastleft_button)
        self.__fastright_button = ttk.Button(frame, image=self.__fastright_icon)
        self.__fastright_button.grid(row=2, column=4)
        self.__buttons.append(self.__fastright_button)
        self.__fastdown_button = ttk.Button(frame, image=self.__fastdown_icon)
        self.__fastdown_button.grid(row=4, column=2)
        self.__buttons.append(self.__fastdown_button)
        self.__home_button = ttk.Button(frame, image=self.__home_icon)
        self.__home_button.grid(row=2, column=2)
        self.__buttons.append(self.__home_button)
        self.__stop_button = ttk.Button(frame, text='Force Stop')
        self.__stop_button.grid(row=2, column=5, padx=20)
        self.__buttons.append(self.__stop_button)

        self.__lock_button = ttk.Button(frame, text='Lock', command=self.lock_button_event)
        self.__lock_button.grid(row=3, column=5, padx=20)

        input_label = ttk.Label(frame, text='Selected Input:')
        input_label.grid(row=2, column=6, padx=20)
        self.__input_option_var = tk.StringVar(frame)
        self.__input_options = ['Buttons']
        if self.__controller:
            self.__input_options.append('Joystick')
        input_optionmenu = ttk.OptionMenu(frame, self.__input_option_var, self.__input_options[0], *self.__input_options, command=self.input_option_changed)
        input_optionmenu.grid(row=2, column=7)

        self.__prev_input_option = self.__input_options[0]
        self.__lock_controls = False
        self.__lock_joystick_controls = True
        self.configure_buttons()

    # exceptions: on connection error
    def connect_controller(self):
        devices = hid.HidDeviceFilter().get_devices()
        device = None
        for i, dev in enumerate(devices):
            if dev.product_name == PS3GamePadRawDataHandler.NAME:
                device = dev

        if not device:
            raise Exception('Failed to identify a ' + PS3GamePadRawDataHandler.NAME + ' controller.')

        self.__joystick_device = device

        try:
            self.__joystick_device.open()
        except Exception as err:
            raise Exception('Failed to open connection to controller: ' + str(err))

        return PS3GamePadRawDataHandler.NAME

    def configure_buttons(self):
        if self.__controller:
            self.__up_button.bind("<ButtonPress>", self.up_button_event)
            self.__left_button.bind("<ButtonPress>", self.left_button_event)
            self.__right_button.bind("<ButtonPress>", self.right_button_event)
            self.__down_button.bind("<ButtonPress>", self.down_button_event)

            self.__fastup_button.bind("<ButtonPress>", self.fastup_button_event)
            self.__fastup_button.bind("<ButtonRelease>", self.fastupdown_buttonup_event)
            self.__fastleft_button.bind("<ButtonPress>", self.fastleft_button_event)
            self.__fastleft_button.bind("<ButtonRelease>", self.fastleftright_buttonup_event)
            self.__fastright_button.bind("<ButtonPress>", self.fastright_button_event)
            self.__fastright_button.bind("<ButtonRelease>", self.fastleftright_buttonup_event)
            self.__fastdown_button.bind("<ButtonPress>", self.fastdown_button_event)
            self.__fastdown_button.bind("<ButtonRelease>", self.fastupdown_buttonup_event)

            self.__stop_button.bind("<ButtonPress>", self.forcestop_button_event)
            self.__home_button.bind("<ButtonPress>", self.home_button_event)

    # check if motors are moving
    def is_stopped(self):
        if self.__fine_motors and self.__coarse_motor:
            return self.__fine_motors.getAxisParameter(self.__fine_motors.APs.ActualPosition,
                                                       MotorController.MOTOR_X_ID) == self.__fine_motors.getAxisParameter(
                self.__fine_motors.APs.TargetPosition, MotorController.MOTOR_X_ID) and self.__fine_motors.getAxisParameter(
                self.__fine_motors.APs.ActualPosition, MotorController.MOTOR_Y_ID) == self.__fine_motors.getAxisParameter(
                self.__fine_motors.APs.TargetPosition,
                MotorController.MOTOR_Y_ID) and self.__coarse_motor.readRegisterField(
                self.__coarse_motor.fields.POSITION_REACHED) == 1
        return True

    def return_to_home(self):
        if self.__fine_motors and self.__coarse_motor:
            event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.CIRCLE_BUTTON)
            self.__controller.button_event(event)

    def joystickcontroller_event(self, events):
        if not self.__lock_joystick_controls and events:
            for key in events.keys():
                value = events[key]

                if key == PS3GamePadRawDataHandler.LEFTJOY_X:
                    self.__joystick_stopped = False
                    event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.LEFTJOY_X_AXIS, value=value)
                    self.__controller.joystick_event(event)
                elif key == PS3GamePadRawDataHandler.LEFTJOY_Y:
                    self.__joystick_stopped = False
                    event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.LEFTJOY_Y_AXIS, value=value)
                    self.__controller.joystick_event(event)
                elif key == PS3GamePadRawDataHandler.RIGHTJOY_X:
                    self.__joystick_stopped = False
                    event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.RIGHTJOY_X_AXIS, value=value)
                    self.__controller.joystick_event(event)
                elif key == PS3GamePadRawDataHandler.RIGHTJOY_Y:
                    self.__joystick_stopped = False
                    event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.RIGHTJOY_Y_AXIS, value=value)
                    self.__controller.joystick_event(event)

                elif key == PS3GamePadRawDataHandler.DPAD_UP:
                    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.DPAD_UP)
                    self.__controller.button_event(event)
                elif key == PS3GamePadRawDataHandler.DPAD_RIGHT:
                    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.DPAD_RIGHT)
                    self.__controller.button_event(event)
                elif key == PS3GamePadRawDataHandler.DPAD_DOWN:
                    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.DPAD_DOWN)
                    self.__controller.button_event(event)
                elif key == PS3GamePadRawDataHandler.DPAD_LEFT:
                    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.DPAD_LEFT)
                    self.__controller.button_event(event)

                elif key == PS3GamePadRawDataHandler.CIRCLE:
                    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.CIRCLE_BUTTON)
                    self.__controller.button_event(event)
                elif key == PS3GamePadRawDataHandler.CROSS:
                    event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.CROSS_BUTTON)
                    self.__controller.button_event(event)

        # make sure motors are stopped when in joystick dead zones
        elif not self.__joystick_stopped:
            event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.LEFTJOY_X_AXIS, value=0)
            self.__controller.joystick_event(event)
            event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.LEFTJOY_Y_AXIS, value=0)
            self.__controller.joystick_event(event)
            event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.RIGHTJOY_X_AXIS, value=0)
            self.__controller.joystick_event(event)
            event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.RIGHTJOY_Y_AXIS, value=0)
            self.__controller.joystick_event(event)

            self.__joystick_stopped = True

    # continuously poll for joystick events
    def poll_joystickcontroller(self):
        try:
            # set custom raw data handler
            self.__joystick_device.set_raw_data_handler(self.__joystick_rawdatahandler.process)

            while not self.__lock_joystick_controls and not kbhit():
                if not self.__joystick_device.is_plugged():
                    raise Exception('Joystick controller was unplugged.')
                pass

        except Exception as err:
            # pop-up message on error
            message = 'Error polling joystick controller: ' + str(err)
            showerror(title='Error', message=message)

            DebugLog.debugprint(self, message)

    def up_button_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.DPAD_UP)
            self.__controller.button_event(event)

    def down_button_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.DPAD_DOWN)
            self.__controller.button_event(event)
        
    def left_button_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.DPAD_LEFT)
            self.__controller.button_event(event)
        
    def right_button_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.DPAD_RIGHT)
            self.__controller.button_event(event)

    def forcestop_button_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.CROSS_BUTTON)
            self.__controller.button_event(event)

    def home_button_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYBUTTONDOWN, button=PS3GamePad.CIRCLE_BUTTON)
            self.__controller.button_event(event)

    def fastup_button_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.RIGHTJOY_Y_AXIS, value=-0.5)
            self.__controller.joystick_event(event)
    
    def fastupdown_buttonup_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.RIGHTJOY_Y_AXIS, value=0)
            self.__controller.joystick_event(event)

    def fastdown_button_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.RIGHTJOY_Y_AXIS, value=0.5)
            self.__controller.joystick_event(event)

    def fastleft_button_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.RIGHTJOY_X_AXIS, value=-0.5)
            self.__controller.joystick_event(event)
    
    def fastleftright_buttonup_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.RIGHTJOY_X_AXIS, value=0)
            self.__controller.joystick_event(event)

    def fastright_button_event(self, event):
        if not self.__lock_controls and self.__lock_joystick_controls:
            event = pygame.event.Event(pygame.JOYAXISMOTION, axis=PS3GamePad.RIGHTJOY_X_AXIS, value=0.5)
            self.__controller.joystick_event(event)

    def disable_buttons(self):
        for button in self.__buttons:
            button['state'] = 'disabled'

    def enable_buttons(self):
        for button in self.__buttons:
            button['state'] = 'normal'

    def lock_controls(self):
        self.__lock_controls = True

        input_option = self.__input_option_var.get()
        if input_option == 'Buttons':
            self.disable_buttons()
        elif input_option == 'Joystick':
            self.__lock_joystick_controls = True
            if self.__joystickcontroller_thread:
                self.__joystickcontroller_thread.join()

    def unlock_controls(self):
        self.__lock_controls = False

        input_option = self.__input_option_var.get()
        if input_option == 'Buttons':
            if not self.__lock_controls:
                self.enable_buttons()
        elif input_option == 'Joystick':
            self.__lock_joystick_controls = False
            self.__joystickcontroller_thread = threading.Thread(target=self.poll_joystickcontroller, daemon=True)
            self.__joystickcontroller_thread.start()

    def set_input_to_joystick(self):
        input_option = self.__input_option_var.get()
        self.__prev_input_option = input_option

        if input_option == 'Buttons':
            if self.__controller:
                self.__input_option_var.set('Joystick')
                self.input_option_changed()

    def set_input_to_original(self):
        input_option = self.__input_option_var.get()
        if input_option != self.__prev_input_option:
            self.__input_option_var.set(self.__prev_input_option)
            self.input_option_changed()

    # switch between UI buttons and joystick to control motors
    def input_option_changed(self, *args):
        input_option = self.__input_option_var.get()
        if input_option == 'Buttons':
            self.__lock_joystick_controls = True
            if self.__joystickcontroller_thread:
                self.__joystickcontroller_thread.join()
            if not self.__lock_controls:
                self.enable_buttons()
        elif input_option == 'Joystick':
            self.__lock_joystick_controls = False
            self.disable_buttons()
            self.__joystickcontroller_thread = threading.Thread(target=self.poll_joystickcontroller, daemon=True)
            self.__joystickcontroller_thread.start()

    # block inputs to motors
    def lock_button_event(self):
        self.__lock_controls = not self.__lock_controls

        if self.__lock_controls:
            if self.__input_option_var.get() == 'Buttons':
                self.disable_buttons()
            self.__lock_button.config(text='Unlock')
        else:
            if self.__input_option_var.get() == 'Buttons':
                self.enable_buttons()
            self.__lock_button.config(text='Lock')

    def __del__(self):
        self.__joystick_device.close()
        del self.__controller
        pygame.quit()