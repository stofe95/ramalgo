import tkinter as tk
import tkinter.ttk as ttk
from tkinter.messagebox import showerror, askyesno, showinfo
from tkinter import filedialog, simpledialog
import PIL.Image, PIL.ImageTk, PIL.ImageGrab
from subprocess import call

import numpy as np
import threading
import queue
import multiprocessing as mp
import time
import h5py
from datetime import datetime
import copy

from DebugLog.DebugLog import *
from PhotostimulatorTool import PhotostimulatorTool
from UserInterfaceApps.RunConfigurationWindow import RunConfigurationWindow
from UserInterfaceApps.RunFileWriter import RunFileWriter
from UserInterfaceApps.ChooseBuildDialog import ChooseBuildDialog
from UserInterfaceApps.ChooseBuildDialog import BuildProgressWindow
from UserInterfaceApps.ConnectionManagerWindow import ConnectionManagerWindow
from UserInterfaceApps.VideoCameraController import VideoCameraController, FrameManipulator
from UserInterfaceApps.JoystickControllerView import JoystickControllerView
from UserInterfaceApps.PositionControllerView import PositionControllerView
from UserInterfaceApps.MouseTrackingController import MouseTrackingController
from UserInterfaceApps.VideoPlayer import VideoPlayer
from UserInterfaceApps.HighSpeedVideoWindow import HighSpeedFilenameWindow
from Motors import Motors_TMC5072_eval, Motors_TMC5130_eval

from AnalysisTools import *

class UserInterface():
    def __init__(self, master):
        self.__master = master
        self.__master.withdraw()

        # blocking dialog to select build type
        # TODO: currently no difference between builds
        build_dialog = ChooseBuildDialog(self.__master)
        self.__buildtype = build_dialog.get_build()

        DebugLog.debugprint(self, "Running in " + self.__buildtype + " mode...")

        # progress window
        build_progress = BuildProgressWindow(self.__master)

        self.__notebook = ttk.Notebook(self.__master)
        self.__notebook.pack(pady=10, expand=True)

        self.__frame = ttk.Frame(self.__notebook)
        self.__frame.pack(fill='both', expand=True)

        self.__notebook.add(self.__frame, text='Live Feed')

        os.chdir(os.path.dirname(os.path.realpath(__file__)))
        self.__currentdirectory = str(os.getcwd())
        DebugLog.debugprint(self, "Current directory: " + self.__currentdirectory)

        # progress: 10%
        build_progress.progress(10)

        # ================================== Filename/MouseInfo Label ==================================
        info_frame = ttk.Frame(self.__frame)
        info_frame.grid(row=0,column=1,sticky='nw')
        self.__info_label = tk.Label(info_frame, text="No Selected Data File")
        self.__info_label.grid(row=0,column=0)
        self.mouse_info = Mouse_Info(self.__info_label)

        # ================================== run variables ==================================
        self.__run_thread = None
        self.__run_queue = queue.Queue()
        self.__run_progress = RunProgressWindow(self.__master)
        self.__config_params = {}
        self.__mousetrackingcontroller = None

        # ================================== testing positions 1-12 ==================================
        position_frame = ttk.Frame(self.__frame)
        position_frame.grid(row=1, columnspan=2)
        
        # check connection to motors
        self.__fine_motors = None
        self.__coarse_motor = None

        try:
            # note: TMC5072 boards do not have unique identifiers that can be detected
            # fine motors must be connected to lower COM port to be correctly assigned
            self.__fine_motors = Motors_TMC5072_eval(2)
            self.__coarse_motor = Motors_TMC5130_eval(1)

        except Exception as err:
            # pop-up message on error
            message = 'Failed to connect to motor(s): ' + str(err)
            showerror(title='Error', message=message)

            DebugLog.debugprint(self, message)

        self.__positioncontrollerview = PositionControllerView(position_frame, self.__fine_motors, self.__coarse_motor, self.mouse_info,self.__config_params)

        # progress: 20%
        build_progress.progress(10)

        # ================================== live camera feed ==================================
        camera_frame = ttk.Frame(self.__frame)
        camera_frame.grid(row=2, column=0, sticky='nw')

        self.__camera_label = tk.Label(camera_frame)
        self.__camera_label.grid(row=0, column=0)

        self.__videocapture = None
        self.__frame_delay = 1.0 / VideoCameraController.FPS

        try:
            # exceptions: on connection error
            self.__videocapture = VideoCameraController()
            self.initialize_camera()

        except Exception as err:
            # pop-up message on error
            message = 'Failed to connect to camera: ' + str(err)
            showerror(title='Error', message=message)

            DebugLog.debugprint(self, message)

        finally:
            if not self.__videocapture:
                # format for an empty frame (normally, 640x480)
                self.__camera_label.config(padx=320, pady=240)

        # progress: 40%
        build_progress.progress(20)

        self.fine_motors_buttons_frame = ttk.Frame(camera_frame)
        self.fine_motors_buttons_frame.grid(row=1, column=0)

        # progress: 50%
        build_progress.progress(10)

        self.__joystickcontrollerview = None

        self.connect_joystick()

        # progress: 70%
        build_progress.progress(20)

        # ================================== waveform display ==================================
        self.__wavedisplay_frame = ttk.Frame(self.__frame)
        self.__wavedisplay_frame.grid(row=2, column=1, sticky='ne')

        self.__photostimulator = PhotostimulatorTool(self.__wavedisplay_frame)

        # progress: 90%
        build_progress.progress(20)


        # ================================== menu: file open/save ==================================
        menubar = tk.Menu(self.__master)
        self.__master.config(menu=menubar)

        file_menu = tk.Menu(menubar, tearoff=False)
        file_menu.add_command(label='Open...', command=self.menu_open)
        file_menu.add_separator()
        file_menu.add_command(label='Exit', command=self.on_closing)

        menubar.add_cascade(label='File', menu=file_menu)

        run_menu = tk.Menu(menubar, tearoff=False)
        run_menu.add_command(label='Run Configuration...', command=self.menu_runconfiguration)
        self.__runconfiguration_window = None
        run_menu.add_separator()
        # TODO: implement
        run_menu.add_command(label='Start Run', command=self.menu_startrun)

        menubar.add_cascade(label='Run', menu=run_menu)


        #================================== menu: utilities ==================================
        utilities_menu = tk.Menu(menubar, tearoff=False)
        utilities_menu.add_command(label='Connect joystick...', command=self.connect_joystick)
        if self.__fine_motors:
            utilities_menu.add_command(label='Reset fine motors...', command=self.__fine_motors.read_stallguard)
        utilities_menu.add_command(label='Calibrate blue power...', command=self.__photostimulator.calibrate)

        menubar.add_cascade(label='Utilities',menu=utilities_menu)

        analysis_menu = tk.Menu(menubar, tearoff=False)
        analysis_menu.add_command(label='Extract data to .csv...', command=extract_latencies)
        menubar.add_cascade(label='Analysis',menu=analysis_menu)

        help_menu = tk.Menu(menubar, tearoff=False)
        help_menu.add_command(label='Debug Log...', command=self.menu_debuglog)
        help_menu.add_command(label='Connection Manager...', command=self.menu_connectionmanager)
        self.__connectionmanager_window = None

        menubar.add_cascade(label='Help', menu=help_menu)

        # protocol on window close
        self.__master.protocol("WM_DELETE_WINDOW", self.on_closing)


        # progress: 100%
        build_progress.progress(10)
        build_progress.destroy()

        self.__master.deiconify()
        self.__done = False


    def initialize_camera(self):
        self.update_video_display()

    def update_video_display(self):
        frame = self.__videocapture.get_last_frame()
        frame = copy.deepcopy(frame) #WATCH OUT: MouseTracking can read from the same queue and manipulations to the frame here can affect tracking. Instead of locking, just creating a copy here so that the other process doesn't need to wait for a new frame if this one tried reading it first
        frame = FrameManipulator.draw_timestamp(frame, datetime.now())
        frame = FrameManipulator.draw_crosshair(frame, self.__videocapture.target)

        # frame must be RGB to display
        im = FrameManipulator.convert_BGR2RGB(frame)
        im = PIL.ImageTk.PhotoImage(image=PIL.Image.fromarray(im))
        self.__camera_label.config(image=im)
        self.__camera_label.image = im
        self.__master.update_idletasks()
        self.__camera_label.after(50, self.update_video_display)
        
    def update_infolabel(self):
        if not type(self.__config_params)== list:
            filename = self.__config_params['filename']
            mouse = str(self.__positioncontrollerview.get_current_position())
            trial = str(self.__config_params['trial'])
            self.__info_label.config(text='Filename: {filename} Number of trials for mouse {mouse}: {num}'.format(filename = filename, mouse = mouse, num=trial))

    # open the debug log
    def menu_debuglog(self):
        try:
            call("notepad " + DebugLog.FILENAME)

        except Exception as err:
            # pop-up message on error
            message = 'Failed to open Debug Log: ' + str(err)
            showerror(title='Error', message=message)

            DebugLog.debugprint(self, message)

    # open the run configuration window
    def menu_runconfiguration(self):
        if self.__runconfiguration_window:
            # save the last inputted configuration parameters
            if self.__runconfiguration_window.did_press_ok():
                self.__config_params = self.__runconfiguration_window.get_parameters()

            del self.__runconfiguration_window

        self.__runconfiguration_window = RunConfigurationWindow(self.__master, self.mouse_info)

        # open using the last inputted configuration parameters
        if self.__config_params:
            self.__runconfiguration_window.set_parameters(self.__config_params)
            #self.mouse_info.filename = self.__config_params['filename']
            #self.mouse_info.update_label()

    # execute run, as defined by parameters from the run configuration
    def menu_startrun(self):
        # get configuration parameters
        if self.__runconfiguration_window and self.__runconfiguration_window.did_press_ok():
            self.__config_params = self.__runconfiguration_window.get_parameters()

            selected_folder = self.__config_params['selectedfolder']
            filename = self.__config_params['filename']
            is_HDF5 = (self.__config_params['is_HDF5'] == 1)
            is_CSV = (self.__config_params['is_CSV'] == 1)
            trial_id = self.__config_params['trial']
            if 'hsv_fps' in self.__config_params.keys() and 'hsv_length' in self.__config_params.keys():
                hsv_params = {"FPS": self.__config_params['hsv_fps'], 'length': self.__config_params['hsv_length']}
            else:
                hsv_params = {}
            self.mouse_info.update_label()
            if self.mouse_info.trial:
                trial_id = self.mouse_info.trial + 1
            else:
                trial_id = 1

            # need to define a file type to proceed
            if not is_HDF5 and not is_CSV:
                message = 'Error: No file type(s) selected in configuration.\nGo to \'Run Configuration...\' to define parameters.'
                showerror(title='Error', message=message)

                DebugLog.debugprint(self, message)

                return

            # set mouse ID based on where the current position is
            mouse_id = self.__positioncontrollerview.get_current_position()

            # verify waveform settings and filename
            # if not (self.verify_waveform_settings() and self.validate_filename(selected_folder, filename, mouse_id, trial_id, is_HDF5, is_CSV)):
            #     return

            # verify waveform settings alone
            # if not (self.verify_waveform_settings()):
            #     return

            # lock joystick/button motor controls
            self.__joystickcontrollerview.lock_controls()

            # execute trial(s) in manual or automatic mode
            mode = self.__config_params['mode']
            if mode == 'Manual':
                start_delay = self.__config_params['startdelay']
                stop_delay = self.__config_params['stopdelay']

                self.__run_queue.join()

                # run progress window
                self.__run_progress.start()
                # TODO: only automatic mode should use queues
                # create threads for each trial, and add to the queue
                self.__run_queue.put(threading.Thread(target = self.run_manual_callback, args=[start_delay, stop_delay, is_HDF5, is_CSV, selected_folder, filename, mouse_id, trial_id, hsv_params]))
                # start recording video
                #self.__videocapture.start_video_recording()

                # start first trial
                thread = self.__run_queue.get()
                thread.start()

            elif mode == 'Automatic':
                trigger = self.__config_params['trigger']
                detection_limit = self.__config_params['detectionlimit']
                centred_time = self.__config_params['centredtime']
                row_select = self.__config_params['rowselect']
                mouse_start = self.__config_params['mousestart']
                mouse_stop = self.__config_params['mousestop']
                #mice_count = mouse_stop - mouse_start + 1

                self.__run_queue.join()

                # notify user how to pause/stop automated steps
                showinfo(title='Pausing automation steps', message='To pause at any point between steps, press Spacebar')
                self.__run_progress.allow_pausing()

                # initialize mouse tracking controller
                if trigger == 'autodetect':
                    try:
                        if not self.__mousetrackingcontroller:
                            self.__mousetrackingcontroller = MouseTrackingController(self.__videocapture, self.__fine_motors, centred_time, self.__videocapture.target)
                        else:
                            self.__mousetrackingcontroller.initialize()

                        message = 'DLCLive object initialized'
                        DebugLog.debugprint(self, message)

                    except Exception as err:
                        message = 'Failed to initialize mouse tracking: ' + str(err)
                        showerror(title='Error', message=message)

                        DebugLog.debugprint(self, message)

                        # close progress window
                        self.__run_progress.finished()

                        return

                # run progress window
                self.__run_progress.start()

                # create threads for each trial, and add to the queue
                for i in range(mouse_start, mouse_stop + 1):
                    mouse_id = row_select + str(i)
                    self.__run_queue.put(threading.Timer(0.0, self.run_automatic_callback, args=[trigger, detection_limit, is_HDF5, is_CSV, selected_folder, filename, mouse_id, trial_id]))

                # start first trial
                thread = self.__run_queue.get()
                thread.start()

        else:
            message = 'Error: Run configuration not defined.\nGo to \'Run Configuration...\' to define parameters.'
            showerror(title='Error', message=message)

            DebugLog.debugprint(self, message)

    # # show pop-up window to verify waveform settings to be used in the following trial(s)
    # # returns: True if 'Yes', False if 'No'
    # def verify_waveform_settings(self, num_trials=1):
    #     bluelightsettings, redlightsettings = self.__photostimulator.get_launch_settings()
    #     message = 'Preparing to run ' + str(num_trials) + ' trial(s) with the following waveform settings:\n\n'
    #     message += 'Blue light settings: Waveform Type: ' + str(bluelightsettings[0]) + ' Length (ms): ' + str(bluelightsettings[1]) + ' Voltage (V): ' + str(bluelightsettings[2]) + '\n'
    #     message += 'Red light settings: Voltage (V): ' + str(redlightsettings[0]) + '\n\n'
    #     message += 'Run with these settings?'

    #     return askyesno(title='Confirm waveform settings', message=message)

    # show pop-up window to verify waveform settings to be used in the following trial(s)
    # returns: True if 'Yes', False if 'No'
    def verify_waveform_settings(self, num_trials=1):
        message = ''
        lightsettings = self.__photostimulator.get_launch_settings()

        if lightsettings['mode'] == PhotostimulatorTool.REDBLUE_CONFIG_NAME:
            message = 'Preparing to run ' + str(num_trials) + ' trial(s) with the following waveform settings:\n\n'
            message += 'Red light settings: Voltage (V): ' + str(lightsettings['red_voltage']) + ' Termination Threshold: ' + str(lightsettings['red_threshold']) + '\n'
            message += 'Blue light settings: Waveform Type: ' + str(lightsettings['blue_wavetype'])
            message += ' Length (ms): ' + str(lightsettings['blue_length']) + ' Voltage (V): {:.2f}\n\n'.format(lightsettings['blue_voltage'])
            message += 'Run with these settings?'

            return askyesno(title='Confirm waveform settings', message=message)

        elif lightsettings['mode'] == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
            message = 'Preparing to run ' + str(num_trials) + ' trial(s) with the following waveform settings:\n\n'
            message += 'Red light settings: Voltage (V): ' + str(lightsettings['red_voltage']) + ' Termination Threshold: ' + str(lightsettings['red_threshold']) + '\n'
            message += 'Green light settings: Length (ms): ' + str(lightsettings['green_length']) + ' Voltage (V): ' + str(lightsettings['green_voltage']) + '\n'
            message += 'LASER settings: Voltage (V): ' + str(lightsettings['laser_voltage']) + '\n\n'
            message += 'Run with these settings?'

            return askyesno(title='Confirm waveform settings', message=message)

        return False

    # check if filename already exists, show pop-up if exists and asks to overwrite
    # returns: True if doesn't exist or 'Yes', False if 'No'
    def validate_filename(self, selected_folder, filename, mouse_id, trial_id, is_HDF5, is_CSV):
        file_exists = []

        if is_HDF5:
            filepath = selected_folder + '\\' + filename + RunFileWriter.HDF5_EXTENSION
            if os.path.exists(filepath):
                file_exists.append(filename + RunFileWriter.HDF5_EXTENSION)

        elif is_CSV:
            filenames = RunFileWriter.format_datafilename(filename, mouse_id, trial_id, RunFileWriter.AVI_EXTENSION)
            video_file = filenames['video_file']
            filepath = selected_folder + '\\' + video_file
            if os.path.exists(filepath):
                file_exists.append(video_file)

            filenames = RunFileWriter.format_datafilename(filename, mouse_id, trial_id, RunFileWriter.CSV_EXTENSION)
            csv_file = filenames['waveform_file']
            filepath = selected_folder + '\\' + csv_file
            if os.path.exists(filepath):
                file_exists.append(csv_file)

        if not file_exists:
            return True

        message = 'File(s) with the name \"' + filename + '\" already exists.\nOverwrite?'
        return askyesno(title='Found existing file(s)', message=message)

    # stop saving frames and write to .avi file
    # def stop_video_recording(self, selected_folder, filename, mouse_id, trial_id, write_to_file=True):
    #     self.__save_frame = False
    #     self.__videocapture.should_save_frame = False
    #     if write_to_file:
    #         video_path = selected_folder + '\\' + filename + '_videos'
    #         if not os.path.exists(video_path):
    #             os.mkdir(video_path)
    #         filenames = RunFileWriter.format_datafilename(filename, mouse_id, trial_id, RunFileWriter.AVI_EXTENSION)
    #         video_filename = filenames['video_file']
    #         filepath = video_path + '\\' + video_filename
    #         #self.__videocapture.write_to_file(filepath)
    #         self.save_queue.put(filepath)
    #         return filepath
    #     else:
    #         return None

    # execute one manual trial on a single mouse
    def run_manual_callback(self, start_delay, stop_delay, is_HDF5, is_CSV, selected_folder, filename, mouse_id, trial_id, hsv_params={}):
        message = 'Running: manual trial ' + str(trial_id)
        DebugLog.debugprint(self, message)

        trial_datetime = datetime.now()
        self.__videocapture.start_video_recording()
        time.sleep(start_delay)
        # launch waveform
        # TODO: adjust waveform lengths using start/stop delays?
        # TODO: drawing plots causes program crash, bypass for now
        self.__photostimulator.launch_waveform(plot=False,hsv_params = hsv_params)
        wave_settings = self.__photostimulator.get_launch_settings()

        wave_data = self.__photostimulator.get_waveform_data()
        wave_config = wave_settings['mode']


        time.sleep(stop_delay)
        # stop recording video
        videopath = self.__videocapture.stop_video_recording(selected_folder, filename, mouse_id, trial_id)

        self.__run_progress.finished()
        good_trial, comment = self.ask_good_trial()
        #self.__run_progress.saving()

        if hsv_params:
            hsv_window = HighSpeedFilenameWindow(selected_folder, filename, mouse_id, trial_id, master = self.__master)
            hsv_params['filename'] = hsv_window.get_filename()

        # save trial
        try:
            if is_HDF5:
                RunFileWriter.save_HDF5(
                    selected_folder,
                    filename,
                    mouse_id,
                    trial_id,
                    trial_datetime,
                    wave_settings,
                    wave_data,
                    substage_frame_times=self.__videocapture.get_frame_times(),
                    good_trial=good_trial,
                    comment=comment,
                    videopath=videopath,
                    hsv_params = hsv_params
                    )
            if is_CSV:
                RunFileWriter.save_csv(selected_folder, filename, mouse_id, trial_id, wave_config, wave_data)

        except Exception as err:
            # exceptions: waveform data is None
            # pop-up message on error
            message = 'Error: ' + str(err)
            showerror(title='Error', message=message)

            DebugLog.debugprint(self, message)


        self.mouse_info.update_label()

        # TODO: only automatic mode should use queues
        # execute next trial
        self.__run_queue.task_done()
        if not self.__run_queue.empty():
            self.__run_progress.running()

            next_thread = self.__run_queue.get()

            # start recording video
            #self.start_video_recording()
            self.__videocapture.start_video_recording()

            next_thread.start()

        else:
            # close progress window
#            self.__run_progress.finished()

            # unlock joystick/button motor controls
            self.__joystickcontrollerview.unlock_controls()

        message = 'Finished: manual trial ' + str(trial_id)
        DebugLog.debugprint(self, message)

    def thread_manual_callback(self, stop_delay, is_HDF5, is_CSV, selected_folder, filename, mouse_id, trial_id):
        thread = threading.Thread(target=self.run_manual_callback,args=[stop_delay, is_HDF5, is_CSV, selected_folder, filename, mouse_id, trial_id])
        thread.start()

    def ask_good_trial(self):
        #Tkinter has a weird bug according to a stackoverflow post. Need to create a new window as a workaround, otherwise get
        #_tkinter.TclError: window ".!_querystring" was deleted before its visibility changed
        #when user hits ok for the askstring window
        tempWin = tk.Tk()
        tempWin.withdraw()

        good_trial = askyesno(title = 'Confirm', message = 'Mark as good trial?')
        if not good_trial:
            comment = simpledialog.askstring("Comment", "Add trial comment",parent=tempWin)
            if not comment:
                comment = ''
        else:
            comment=''
        tempWin.destroy()
        #HDF5 doesn't support saving an empty string, so just making it into ' ' if it's empty
        if len(comment) < 1:
            comment = ' '
        return good_trial, comment

    # check if user requested to terminate run on pause
    # return: True if termination requested
    def do_terminate_run(self, next_step_info):
        if self.__run_progress.did_request_pause():

            message = 'Run paused. Next step: ' + next_step_info + '. Continue?'
            if not askyesno(title='Paused', message=message):

                self.terminate_run(next_step_info)
                return True

        return False

    # terminate the run before completion
    def terminate_run(self, next_step_info):
        message = 'Run terminated at step: ' + next_step_info + '.'
        showinfo(title='Run terminated', message=message)

        DebugLog.debugprint(self, message)

        # empty queue
        self.__run_queue.task_done()
        while not self.__run_queue.empty():
            self.__run_queue.get()
            self.__run_queue.task_done()

        # close progress window
        self.__run_progress.finished()

        # unlock joystick/button motor controls
        self.__joystickcontrollerview.unlock_controls()

    # execute trial(s) on a given number of mice
    def run_automatic_callback(self, trigger, detection_limit, is_HDF5, is_CSV, selected_folder, filename, mouse_id, trial_id):
        message = 'Running: automatic trial ' + str(trial_id) + ' on mouse ' + mouse_id
        DebugLog.debugprint(self, message)

        # check between steps if pause requested
        if self.do_terminate_run('Move to position ' + mouse_id):
            return

        # move to position
        self.__run_progress.moving_to_position()

        self.__positioncontrollerview.move_to_position(mouse_id, block_until_stopped=True)

        # check between steps if pause requested
        if self.do_terminate_run('Detect and stimulate paw at position ' + mouse_id):
            return

        # manually or automatically trigger stimulus
        self.__run_progress.running()

        if trigger == 'manual':
            self.__joystickcontrollerview.unlock_controls()
            self.__joystickcontrollerview.set_input_to_joystick()
            showinfo(title='Manual stimulus trigger', message='Press OK to trigger stimulus. (Use joystick to adjust position, if needed)')
            self.__joystickcontrollerview.set_input_to_original()
            self.__joystickcontrollerview.lock_controls()

        elif trigger == 'autodetect':
            retry = True
            self.__mousetrackingcontroller.reset_data()

            while retry:
                tracking_video_fn = selected_folder + '\\' + filename + '_' + str(mouse_id) + '_trial' + str(trial_id) + '_tracking' + '.avi'
                autodetect_thread = threading.Thread(target = self.__mousetrackingcontroller.autodetect, kwargs={'fn':tracking_video_fn}, daemon=True)
                autodetect_thread.start()

                # block until paw is centred, or detection time limit reached
                autodetect_thread.join(detection_limit)

                if not autodetect_thread.is_alive():
                    retry = False

                else:
                    # stop autodetect thread
                    self.__mousetrackingcontroller.force_stop()
                    autodetect_thread.join()
                    self.__mousetrackingcontroller.reset_data()

                    # retry auto-detection
                    message = 'Failed to detect centred mouse paw within the detection time limit. Retry?'
                    if not askyesno(title='Detection time limit reached', message=message):
                        retry = False

                        # retry using manual trigger
                        message = 'Would you like to retry using a manual trigger? (Move to next mouse if select \'No\''
                        if askyesno(title='Switch to manual trigger', message=message):
                            self.__joystickcontrollerview.unlock_controls()
                            self.__joystickcontrollerview.set_input_to_joystick()
                            showinfo(title='Manual stimulus trigger', message='Press OK to trigger stimulus. (Use joystick to adjust position, if needed)')
                            self.__joystickcontrollerview.set_input_to_original()
                            self.__joystickcontrollerview.lock_controls()

                        # continue to next mouse or end if last mouse
                        else:
                            if not self.__run_queue.empty():
                                self.__run_queue.task_done()

                                self.__run_progress.running()

                                next_thread = self.__run_queue.get()
                                next_thread.start()

                            else:
                                # close progress window
                                self.__run_progress.finished()

                            message = 'Finished: automatic trial ' + str(trial_id) + ' on mouse ' + mouse_id
                            DebugLog.debugprint(self, message)
                            return

        trial_datetime = datetime.now()

        # start recording video
        #self.start_video_recording()
        self.__videocapture.start_video_recording()
        time.sleep(1) #TODO Add adjustable video recording length for automatic callback

        # launch waveform
        # TODO: drawing plots causes program crash, bypass for now
        self.__photostimulator.launch_waveform(plot=False)
        wave_settings = self.__photostimulator.get_launch_settings()
        wave_data = self.__photostimulator.get_waveform_data()
        wave_config = wave_settings['mode']

        # stop recording video
        #self.__videocapture.stop_video_recording(selected_folder, filename, mouse_id, trial_id)
        time.sleep(20) #TODO Along with previous point on video recording length
        videopath = self.__videocapture.stop_video_recording(selected_folder, filename, mouse_id, trial_id)

        # check between steps if pause requested
        if self.do_terminate_run('Saving data recorded at position ' + mouse_id):
            return

        self.__run_progress.saving()

        # save trial
        tracking_data = []
        if trigger == 'autodetect':
            tracking_data = self.__mousetrackingcontroller.get_tracking_data()
            if type(tracking_data) is list:
                tracking_data = np.asarray(tracking_data)
        try:
            if is_HDF5:
                #RunFileWriter.save_HDF5(selected_folder, filename, mouse_id, trial_id, trial_datetime, wave_settings, wave_data, tracking_data=tracking_data, substage_frame_times=self.__videocapture.get_last_frame_times())
                RunFileWriter.save_HDF5(
                    selected_folder,
                    filename,
                    mouse_id,
                    trial_id,
                    trial_datetime,
                    wave_settings,
                    wave_data,
                    substage_frame_times=self.__videocapture.get_frame_times(),
                    good_trial = 1, #Assuming good trial because it's auto
                    comment = 'Automatic Detection',
                    videopath = videopath
                    )
            if is_CSV:
                RunFileWriter.save_csv(selected_folder, filename, mouse_id, trial_id, wave_config, wave_data, tracking_data=tracking_data)

        except Exception as err:
            # exceptions: waveform data is None
            # pop-up message on error
            message = 'Error: ' + str(err)
            showerror(title='Error', message=message)

            DebugLog.debugprint(self, message)

        self.mouse_info.update_label()

        # execute next trial
        if not self.__run_queue.empty():
            # ask if want to continue to next mouse
            #if askyesno(title='Continue?', message='Do you want to continue to the next mouse?'):
            if True:
                self.__run_queue.task_done()

                self.__run_progress.running()

                next_thread = self.__run_queue.get()
                next_thread.start()

            # ask if want to repeat this trial
            elif askyesno(title='Repeat trial?', message='Do you want to repeat this trial? (Run will terminate if select \'No\''):
                # TODO: currently overwrites previous trials. Do we want to save retries as new files?
                self.run_automatic_callback(trigger, detection_limit, is_HDF5, is_CSV, selected_folder, filename, mouse_id, trial_id)

            # terminate run
            else:
                self.terminate_run('Start automatic trial on next mouse')

        else:
            self.__run_queue.task_done()

            # close progress window
            self.__run_progress.finished()

            # unlock joystick/button motor controls
            self.__joystickcontrollerview.unlock_controls()

        message = 'Finished: automatic trial ' + str(trial_id) + ' on mouse ' + mouse_id
        DebugLog.debugprint(self, message)

    # TODO: make tab closeable
    # TODO: show timestamps in video player
    # create new read-only tab
    # exceptions: invalid video and/or waveform files
    def open_newtab(self, video_file, waveform_data_file):
        # exception: no files given
        if not video_file or not waveform_data_file:
            raise Exception('No files given to open.')

        # TODO: mp4 not supported yet
        # exception: invalid file types
        if video_file.name.find(RunFileWriter.AVI_EXTENSION) == -1 or waveform_data_file.name.find(RunFileWriter.CSV_EXTENSION) == -1:
            raise Exception('Invalid file types given.')

        frame = ttk.Frame(self.__notebook)
        frame.pack(fill='both', expand=True)

        self.__notebook.add(frame, text='ReadOnly')

        # ================================== video file viewer ==================================
        camera_frame = ttk.Frame(frame)
        camera_frame.grid(row=0, column=0, sticky='nw')

        camera_label = tk.Label(camera_frame)
        camera_label.grid(row=0, column=0, columnspan=2)

        videoplayer = VideoPlayer(camera_label)

        play_button = ttk.Button(camera_frame, text='Play', command=videoplayer.play)
        play_button.grid(row=1, column=0, sticky='e')
        # TODO: implement
        pause_button = ttk.Button(camera_frame, text='Pause', command=videoplayer.pause, state='disabled')
        pause_button.grid(row=1, column=1, sticky='w')

        try:
            # note: need to close file for video player to establish its own connection
            name = video_file.name
            video_file.close()
            videoplayer.load(name)

        except Exception as err:
            # delete tab on error
            self.__notebook.forget(frame)
            raise Exception('Unable to read video file: ' + name + '. ' + str(err))

        # ================================== waveform data viewer ==================================
        wavedisplay_frame = ttk.Frame(frame)
        wavedisplay_frame.grid(row=0, column=1, sticky='ne')

        # TODO: adjust values on tool to reflect waveform metadata (how to store this?)
        photostimulator = PhotostimulatorTool(wavedisplay_frame, True)

        try:
            data = np.loadtxt(waveform_data_file.name, dtype=np.float16, delimiter=',', skiprows=1)
            # exception: invalid format
            receive_blue = np.empty(data.shape[0])
            receive_red = np.empty(data.shape[0])
            for i in range(data.shape[0]):
                receive_blue[i] = data[i][0]
                receive_red[i] = data[i][1]

            photostimulator.draw_plot(receive_blue, receive_red)

        except Exception as err:
            # delete tab on error
            self.__notebook.forget(frame)
            raise Exception('Unable to read waveform data file: ' + waveform_data_file.name + '. ' + str(err))

    # TODO: mp4 not supported yet
    # open a single trial in a new read-only tab
    def menu_open(self):
        filetypes = RunFileWriter.OPENFILEDIALOG_FILETYPES
        filenames = filedialog.askopenfiles(title='Open', initialdir=self.__currentdirectory, filetypes=filetypes)
        if filenames:
            try:
                # TODO: implement hdf5 viewer?
                if len(filenames) == 1 and filenames[0].name.find(RunFileWriter.HDF5_EXTENSION):
                    # open hdf5 as readonly
                    with h5py.File(filenames[0].name, 'r') as hdf5:
                        print(hdf5.name)
                        # each group represents one mouse
                        for mouse in hdf5.keys():
                            print(mouse)
                            # each dataset represents waveform or video data of one trial
                            for trial in hdf5[mouse]:
                                print('\t' + str(trial))
                                dataset = hdf5[mouse][trial]
                                print('\t' + str(dataset))

                elif len(filenames) == 2:
                    video_file = None
                    waveform_data_file = None
                    for file in filenames:
                        name = file.name
                        if name.find(RunFileWriter.CSV_EXTENSION) != -1:
                            waveform_data_file = file
                        elif name.find(RunFileWriter.AVI_EXTENSION) != -1:
                            video_file = file

                    if video_file is None or waveform_data_file is None:
                        raise Exception('Must select:\n(a) one HDF5 file, or\n(b) one .avi file and one .csv file.')

                    self.open_newtab(video_file, waveform_data_file)

                else:
                    raise Exception('Must select:\n(a) one HDF5 file, or\n(b) one .avi file and one .csv file.')

            except Exception as err:
                # exceptions: invalid video and/or waveform files
                # pop-up message on error
                message = 'Error: ' + str(err)
                showerror(title='Error', message=message)
                DebugLog.debugprint(self, message)

            finally:
                # close files
                for file in filenames:
                    file.close()

    # open the connection manager window
    def menu_connectionmanager(self):
        if self.__connectionmanager_window:
            del self.__connectionmanager_window
        self.__connectionmanager_window = ConnectionManagerWindow(self.__fine_motors, self.__coarse_motor, self.__videocapture, self.__master)
    
    def connect_joystick(self):
        try:
            # exceptions: on connection error
            self.__joystickcontrollerview = JoystickControllerView(self.fine_motors_buttons_frame, self.__fine_motors, self.__coarse_motor,cross_callback=self.menu_startrun)

        except Exception as err:
            # pop-up message on error
            message = 'Failed to connect to joystick controller: ' + str(err)
            showerror(title='Error', message=message)

            DebugLog.debugprint(self, message)

        finally:
            if not self.__joystickcontrollerview:
                self.__joystickcontrollerview = JoystickControllerView(self.fine_motors_buttons_frame, self.__fine_motors, self.__coarse_motor, True)

    def on_closing(self):
        if self.__videocapture:
            self.__videocapture.terminate()
            self.__videocapture.proc.kill()
        if self.__mousetrackingcontroller:
            del self.__mousetrackingcontroller

        # return to position F1
        self.__joystickcontrollerview.return_to_home()
        # block until reached position F1
        onclosewindow = OnClosingWindow(self.__master, self.__joystickcontrollerview.is_stopped)

        # disconnect video feed
        del self.__videocapture

        # disconnect motors
        del self.__fine_motors
        del self.__coarse_motor

        # disconnect joystick controller
        del self.__joystickcontrollerview

        self.__done = True
        self.__master.destroy()


class RunProgressWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master=master)
        self.title('Running...')
        self.geometry("220x80")

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, padx=10, pady=10)

        self.__loading_label = ttk.Label(frame, text='Running...')
        self.__loading_label.grid(row=0, column=0)

        self.__progressbar = ttk.Progressbar(frame, orient='horizontal', mode='indeterminate', length=200)
        self.__progressbar.grid(row=1, column=0)

        self.__pause_requested = False

        # disable close window
        self.protocol("WM_DELETE_WINDOW", ChooseBuildDialog.disable_event)
        # disable window resize
        self.resizable(False, False)
        # center window
        master.eval(f'tk::PlaceWindow {str(self)} center')
        # hide window
        self.withdraw()

    def start(self):
        self.running()
        # show window
        self.deiconify()
        
        # wait until visible before grabbing
        #When implementing the controller button press to start trial, got stuck here waiting
        #self.wait_visibility()

        # keep window focused
        self.grab_set()
        self.__progressbar.start()

    def allow_pausing(self):
        self.bind('<space>', self.paused_event)

    def paused_event(self, event):
        self.__pause_requested = True

    def did_request_pause(self):
        if self.__pause_requested:
            self.__pause_requested = False
            return True
        return False

    def moving_to_position(self):
        self.__loading_label.config(text='Moving to the next position...')

    def running(self):
        self.__loading_label.config(text='Running...')

    def saving(self):
        self.__loading_label.config(text='Saving...')

    def finished(self):
        self.__progressbar.stop()
        self.unbind_all('<space>')
        # release focus
        self.grab_release()
        # hide window
        self.withdraw()

        showinfo(title='Run Complete', message='Trial(s) completed.')

class OnClosingWindow(tk.Toplevel):
    # timeout condition, in seconds
    TIMEOUT = 30.0

    def __init__(self, master=None, if_then_close_func=None):
        super().__init__(master=master)
        self.title('Resetting...')
        self.geometry("220x80")

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, padx=10, pady=10)

        loading_label = ttk.Label(frame, text='Resetting to position F1...')
        loading_label.grid(row=0, column=0)

        self.__progressbar = ttk.Progressbar(frame, orient='horizontal', mode='indeterminate', length=200)
        self.__progressbar.grid(row=1, column=0)

        self.__if_then_close_func = if_then_close_func

        # disable close window
        self.protocol("WM_DELETE_WINDOW", ChooseBuildDialog.disable_event)
        # disable window resize
        self.resizable(False, False)
        # center window
        master.eval(f'tk::PlaceWindow {str(self)} center')
        # wait until visible before grabbing
        self.wait_visibility()
        # keep window focused
        self.grab_set()

        # loop until close condition is satisfied
        self.__did_timeout = False
        threading.Thread(target=self.if_then_close_loop, daemon=True).start()

        # block until window is destroyed
        self.wait_window()

    # close when condition evaluates to true or timeout
    def if_then_close_loop(self):
        start = time.perf_counter()
        self.__progressbar.start()

        while not self.__if_then_close_func():
            # check timeout
            if time.perf_counter() - start > OnClosingWindow.TIMEOUT:
                self.__did_timeout = True
                break

        if self.__did_timeout:
            message = 'Error resetting to position F1. Use the joystick to reset to position F1 on next program startup and restart. Shutting down...'
            showerror(title='Error in shutdown sequence', message=message)
            DebugLog.debugprint(self, message)

        self.__progressbar.stop()
        # release focus
        self.grab_release()
        # destroy window
        self.destroy()

class Mouse_Info:
    def __init__(self,label):
        self.label = label
        self.mouse_ID = 'F1'
        self.trial = None
        self.trial_time = None
        self.filename = None
        self.filepath = None
    
    def update_label(self):
        if not(self.filename):
            label_text = "No file selected"
        else:
            self.read_hdf5_info()
            label_text = self.format_text()
        self.label.config(text=label_text)
    
    def format_text(self):
        return "Filename: {filename}, Last trial: {trial} at {trial_time}".format(filename = self.filename, trial = self.trial, trial_time = self.trial_time)
    
    def read_hdf5_info(self):
        self.trial, self.trial_time = RunFileWriter.get_hdf5_info(self.filepath,self.filename,self.mouse_ID)

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Pain behaviour testing tool')
    root.geometry("1600x1000")
    window = UserInterface(root)

    root.mainloop()
