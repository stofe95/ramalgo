import os
import threading
import queue
import time
from threading import Lock

from .LiveTracker import LiveTracker
import numpy as np

from JoystickController.JoystickController import MotorController
from UserInterfaceApps.VideoCameraController import VideoCameraController
from DebugLog.DebugLog import *

import cv2


class MouseTrackingController:
    TARGETPAW_IDX = 4
    ACCURACY_THRESHOLD = 0.7

    ERROR_THRESHOLD = 10
    VELOCITY = 50000

    def __init__(self, videocapture, fine_motors, centred_time, target):
        self.__live_tracker = LiveTracker()

        self.__videocapture = videocapture
        self.__frame_width, self.__frame_height = videocapture.get_frame_dims()

        self.__fine_motors = fine_motors
        self.__centred_time = centred_time

        self.__error_queue = queue.Queue()
        self.__tracking_data = []
        self.__centred_data = []
        self.__data_lock = Lock()
        self.__done = False
        self.__force_stop = False

        self.__x_target, self.__y_target = target

        self.initialize()

    # initialize the tracking object
    # exceptions: couldn't grab a valid frame within the limited retries
    def initialize(self):
        self.reset_data()

        retry = 5

        ret = None
        frame = None
        while retry > 0:
            ret, frame = self.__videocapture.get_frame()
            if ret:
                retry = 0
            else:
                retry -= 1

        if not ret:
            raise Exception('Unable to grab frame to initialize.')

        self.__live_tracker.initialize(frame)

    # clear data for next run
    def reset_data(self):
        if self.__error_queue:
            del self.__error_queue
            self.__error_queue = queue.Queue()

        if self.__tracking_data:
            self.__tracking_data.clear()

        if self.__centred_data:
            self.__centred_data.clear()

        self.__done = False
        self.__force_stop = False

    # get the latest tracking data
    def get_tracking_data(self):
        with self.__data_lock:
            return self.__tracking_data

    # detect when mouse paw is centred in frame
    def autodetect(self, fn=None):
        if self.__fine_motors:
            print(fn)
            tracking_video = cv2.VideoWriter(fn, cv2.VideoWriter_fourcc(*'DIVX'), 10, (self.__frame_width, self.__frame_height))
            follow_thread = threading.Thread(target=self.motor_follow, daemon=True)
            follow_thread.start()

            while not self.__force_stop:
                ret, frame = self.__videocapture.get_frame()
                if ret:
                    # Returns[[x position label1, y position label1, accuracy label1],[x position label2, y position label2, accuracy label2], ...for each labelled body part]
                    # target paw: xy[1]
                    # target paw x pos: xy[1][0]
                    # target paw y pos: xy[1][1]
                    # target paw accuracy: xy[1][2]
                    xy = self.__live_tracker.get_keypoints(frame)
                    

                    if xy[MouseTrackingController.TARGETPAW_IDX][2] > MouseTrackingController.ACCURACY_THRESHOLD:
                        x_pos = xy[MouseTrackingController.TARGETPAW_IDX][0]
                        y_pos = xy[MouseTrackingController.TARGETPAW_IDX][1]
                        x_error = x_pos - self.__x_target
                        y_error = y_pos - self.__y_target
                        self.__error_queue.put((x_error, y_error))
                        tracking_video.write(cv2.circle(frame,(int(x_pos),int(y_pos)), 8, (255, 0, 0), 2))

                        # check if paw is centred for the given time limit
                        self.__centred_data.append((time.time(), x_error, y_error))
                        start_time = self.__centred_data[0][0]
                        current_time = self.__centred_data[-1][0]
                        if current_time - start_time >= self.__centred_time:
                            print(np.array(self.__centred_data)[:,1:3])
                            # mouse paw is centred, break loop
                            if np.allclose([0], np.array(self.__centred_data)[:,1:3], atol=MouseTrackingController.ERROR_THRESHOLD): #Chaned: index just the errors rather than time as well
                                self.__force_stop = True

                            self.__centred_data.pop(0)
                    else:
                        self.__error_queue.put((1000,1000)) #1000, 10000 will tell motors to stop when paw not detected.
                        tracking_video.write(frame)
                            
            # stop motor follow thread
            tracking_video.release()
            self.__done = True
            follow_thread.join()
        
        else:
            self.__done = True

    # use fine motors to move the mouse paw into centre of frame
    def motor_follow(self):
        if self.__fine_motors:
            while not self.__done:
                # check if motor stalled (flag is cleared on read)
                x_stalled = self.is_motor_stalled(self.__fine_motors, MotorController.MOTOR_X_ID)
                y_stalled = self.is_motor_stalled(self.__fine_motors, MotorController.MOTOR_Y_ID)

                if x_stalled or y_stalled:
                    DebugLog.debugprint(self, 'Fine motor(s) stalled: X: ' + str(x_stalled) + ' Y: ' + str(y_stalled))

                # determine fine motor adjustments
                if not self.__error_queue.empty():
                    VX = self.__fine_motors.readRegisterField(self.__fine_motors.fields.VACTUAL[MotorController.MOTOR_X_ID])
                    VY = self.__fine_motors.readRegisterField(self.__fine_motors.fields.VACTUAL[MotorController.MOTOR_Y_ID])

                    # grab errors
                    x_error, y_error = self.__error_queue.get()
                    
                    if (x_error == 1000) & (y_error == 1000): #Use (1000, 1000) in the queue as a signal that a paw wasn't detected in the frame and to stop motor
                        self.__fine_motors.stop(MotorController.MOTOR_X_ID)
                        self.__fine_motors.stop(MotorController.MOTOR_Y_ID)
                        continue

                    # ensure x motors are stopped
                    if abs(x_error) < MouseTrackingController.ERROR_THRESHOLD:
                        if VX != 0:
                            self.__fine_motors.stop(MotorController.MOTOR_X_ID)
                    # move x motors
                    else:
                        value = int(MouseTrackingController.VELOCITY)
                        if x_error < 0:
                            self.__fine_motors.rotate_cw(MotorController.MOTOR_X_ID, value)
                        else:
                            self.__fine_motors.rotate_ccw(MotorController.MOTOR_X_ID, value)

                    # ensure y motors are stopped
                    if abs(y_error) < MouseTrackingController.ERROR_THRESHOLD:
                        if VY != 0:
                            self.__fine_motors.stop(MotorController.MOTOR_Y_ID)
                    # move y motors
                    else:
                        value = int(MouseTrackingController.VELOCITY)
                        if y_error > 0:
                            self.__fine_motors.rotate_ccw(MotorController.MOTOR_Y_ID, value)
                        else:
                            self.__fine_motors.rotate_cw(MotorController.MOTOR_Y_ID, value)

                    # log tracking data
                    with self.__data_lock:
                        self.__tracking_data.append((time.time(), x_error, VX, y_error, VY))

            # ensure x motors are stopped
            self.__fine_motors.stop(MotorController.MOTOR_X_ID)
            self.__fine_motors.stop(MotorController.MOTOR_Y_ID)

    # check if motor is stalled
    def is_motor_stalled(self, motors, motor_ID):
        return motors.readRegisterField(motors.fields.EVENT_STOP_SG[motor_ID])

    # force the autodetect thread to end
    def force_stop(self):
        self.__force_stop = True

    def __del__(self):
        self.__live_tracker.terminate()
