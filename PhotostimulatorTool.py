from PhotostimulatorController.CED1401 import *
from DebugLog.DebugLog import *

import tkinter as tk
from tkinter.messagebox import showerror, askretrycancel
import tkinter.ttk as ttk
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import (FigureCanvasTkAgg, NavigationToolbar2Tk)

import numpy as np
from glob import glob
import os
import pickle
from UserInterfaceApps.CalibrationWindow import *

import threading


class PhotostimulatorTool:
    REDBLUE_CONFIG_NAME = 'Red/Blue'
    REDGREENLASER_CONFIG_NAME = 'Red/Green/Laser'
    CALIBRATION_PATH = './.calibration_data/'

    def __init__(self, master, default_config='Red/Blue', disabled=False):
        self.__master = master

        self.__state = 'normal'
        if disabled:
            self.__state = 'disabled'

        frame = ttk.Frame(self.__master)
        frame.grid(row=0, column=0, padx=10, pady=10)
        self.highspeed = False


        # ================================== stimuli settings ==================================
        settings_separator = ttk.Separator(frame, orient='horizontal')
        settings_separator.grid(row=1, column=0, sticky='ew', pady=4)

        self.__settings_frame = ttk.Frame(frame)
        self.__settings_frame.grid(row=2, column=0, sticky='ew')

        # Configuration options
        config_label = ttk.Label(self.__settings_frame, text='Configuration Options')
        config_label.grid(row=0, column=0, sticky='w')

        self.__config_var = tk.StringVar(self.__settings_frame)
        self.__config_options = (PhotostimulatorTool.REDBLUE_CONFIG_NAME, PhotostimulatorTool.REDGREENLASER_CONFIG_NAME)
        config_optionmenu = ttk.OptionMenu(self.__settings_frame, self.__config_var, self.__config_options[0], *self.__config_options, command=self.config_option_changed)
        config_optionmenu.grid(row=1, column=0, sticky='w')
        config_optionmenu['state'] = self.__state

        # Red light settings
        red_labelframe = ttk.LabelFrame(self.__settings_frame, text='Red light settings')
        red_labelframe.grid(row=2, column=0, pady=10)

        # Waveform voltage (V)
        redvoltage_labelframe = ttk.LabelFrame(red_labelframe, text="Voltage (V)")
        redvoltage_labelframe.grid(row=0, column=0)

        self.__redvoltage_label = ttk.Label(redvoltage_labelframe)
        self.__redvoltage_label.grid(row=0, column=0)

        self.__redvoltage_var = tk.DoubleVar()

        redvoltage_spinbox = tk.Spinbox(redvoltage_labelframe, from_=0, to=5, increment=0.01, textvariable=self.__redvoltage_var)
        redvoltage_spinbox['state'] = self.__state
        redvoltage_spinbox.grid(row=1, column=0)

        # Termination threshold
        redthreshold_labelframe = ttk.LabelFrame(red_labelframe, text="Termination threshold")
        redthreshold_labelframe.grid(row=0, column=1)

        self.__redthreshold_label = ttk.Label(redthreshold_labelframe)
        self.__redthreshold_label.grid(row=0, column=0)

        self.__redthreshold_var = tk.DoubleVar()
        self.__redthreshold_var.set(0.9)

        redthreshold_spinbox = tk.Spinbox(redthreshold_labelframe, from_=0, to=1, increment=0.01, textvariable=self.__redthreshold_var)
        redthreshold_spinbox['state'] = self.__state
        redthreshold_spinbox.grid(row=1, column=0)

        # red/blue config: variables
        self.__bluewavetype_var = tk.StringVar()

        self.__bluelength_var = tk.DoubleVar()
        self.__bluelength_label = None

        self.__bluevoltage_var = tk.DoubleVar()
        self.__bluevoltage_label = None

        self.__bluefreq_var = tk.DoubleVar()
        self.__bluefreq_label = None

        self.__bluenum_var = tk.IntVar()
        self.__bluenum_label = None

        self.__redblue_settings = []

        # red/green/laser config: variables
        self.__greenlength_var = tk.DoubleVar()
        self.__greenlength_label = None

        self.__greenvoltage_var = tk.DoubleVar()
        self.__greenvoltage_label = None

        self.__laservoltage_var = tk.DoubleVar()
        self.__laservoltage_label = None

        self.__redgreenlaser_settings = []
        self.pulse_train_settings = []

        # Send signal
        launch_button = ttk.Button(frame, text="Launch", command=self.thread_launch)
        launch_button['state'] = self.__state
        launch_button.grid(row=3, column=0, pady=20)


        # Controller
        use_1401 = True
        while use_1401:
            if not disabled:
                try:
                    self.__controller = CED1401()
                    DebugLog.debugprint(self, 'Connected to 1401')
                    break

                except Exception as err:
                    # pop-up message on error
                    message = 'Failed to connect to 1401. Please make sure 1401 is on and retry.\nSelecting cancel will revert to Demo Mode'
                    use_1401 = askretrycancel(title='1401 Connection', message=message)
                          
            else:

                # disable GUI
                launch_button.state(['disabled'])
                use_1401 = False
                break
        if not use_1401:
            DebugLog.debugprint(self, 'No 1401 detected. Reverting to Demo Mode')
            self.__controller = PhotostimulatorController()
        

        if default_config == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
            self.__config_var.set(self.__config_options[1])
            self.config_option_changed()
        
        self.load_calibration()


        # ================================== waveform figure ==================================
        self.__canvas_frame = ttk.Frame(frame)
        self.__canvas_frame.grid(row=0, column=0, sticky='ew')

        self.__receive_redblue = {}
        self.__receive_redgreenlaser = {}

        # View signal
        # red/blue config
        self.__redblue_figure = Figure(dpi=100)
        plot_axes = self.__redblue_figure.add_subplot(111)
        plot_axes.spines['top'].set_color('none')
        plot_axes.spines['bottom'].set_color('none')
        plot_axes.spines['left'].set_color('none')
        plot_axes.spines['right'].set_color('none')
        plot_axes.tick_params(labelcolor='w', top=False, bottom=False, left=False, right=False)
        plot_axes.set_xlabel('Time (ms)')
        plot_axes.set_ylabel('Voltage (V)')
        plot_axes.set_title('Waveform Response')

        self.__redblue_plots = {}
        self.__redblue_plots['blue'] = self.__redblue_figure.add_subplot(211)
        self.__redblue_plots['red'] = self.__redblue_figure.add_subplot(212, sharex=self.__redblue_plots['blue'])

        self.__redblue_plots['blue_line'], = self.__redblue_plots['blue'].plot(np.zeros(1000),c='b')
        self.__redblue_plots['red_line'], = self.__redblue_plots['red'].plot(np.zeros(1000),c='r')
        self.__redblue_plots['latency_line'] = self.__redblue_plots['red'].axvline(np.nan)

        self.__redblue_plots['blue'].set_ylim(0,5)
        self.__redblue_plots['red'].set_ylim(0,5)
        
        self.__redblue_canvas = FigureCanvasTkAgg(self.__redblue_figure, master=self.__canvas_frame)
        self.__redblue_toolbar = NavigationToolbar2Tk(self.__redblue_canvas, self.__canvas_frame, pack_toolbar=False)

        self.redblue_timer = self.__redblue_canvas.new_timer(interval=100)
        self.redblue_timer.add_callback(self.update_redblue_plot,self.__redblue_plots)
        self.redblue_timer.start()

        # red/green/laser config
        self.__redgreenlaser_figure = Figure(dpi=100)
        plot_axes = self.__redgreenlaser_figure.add_subplot(111)
        plot_axes.spines['top'].set_color('none')
        plot_axes.spines['bottom'].set_color('none')
        plot_axes.spines['left'].set_color('none')
        plot_axes.spines['right'].set_color('none')
        plot_axes.tick_params(labelcolor='w', top=False, bottom=False, left=False, right=False)
        plot_axes.set_xlabel('Time (ms)')
        plot_axes.set_ylabel('Voltage (V)')
        plot_axes.set_title('Waveform Response')

        self.__redgreenlaser_plots = {}
        self.__redgreenlaser_plots['green'] = self.__redgreenlaser_figure.add_subplot(311)
        self.__redgreenlaser_plots['laser'] = self.__redgreenlaser_figure.add_subplot(312, sharex=self.__redgreenlaser_plots['green'])
        self.__redgreenlaser_plots['red'] = self.__redgreenlaser_figure.add_subplot(313, sharex=self.__redgreenlaser_plots['green'])

        self.__redgreenlaser_plots['green_line'], = self.__redgreenlaser_plots['green'].plot(np.zeros(1000),c='g')
        self.__redgreenlaser_plots['laser_line'], = self.__redgreenlaser_plots['laser'].plot(np.zeros(1000),c='m')
        self.__redgreenlaser_plots['red_line'], = self.__redgreenlaser_plots['red'].plot(np.zeros(1000),c='r')
        self.__redgreenlaser_plots['latency_line'] = self.__redgreenlaser_plots['red'].axvline(np.nan)

        self.__redgreenlaser_plots['green'].set_ylim(0,5)
        self.__redgreenlaser_plots['laser'].set_ylim(0,5)
        self.__redgreenlaser_plots['red'].set_ylim(0,5)

        self.__redgreenlaser_canvas = FigureCanvasTkAgg(self.__redgreenlaser_figure, master=self.__canvas_frame)
        self.__redgreenlaser_toolbar = NavigationToolbar2Tk(self.__redgreenlaser_canvas, self.__canvas_frame, pack_toolbar=False)

        self.redgreenlaser_timer = self.__redgreenlaser_canvas.new_timer(interval=100)
        self.redgreenlaser_timer.add_callback(self.update_redgreenlaser_plot,self.__redgreenlaser_plots)

        
        # open to default view
        self.show_redblue_settings()

        # set valid values, according to controller
        self.set_valid_lengths()
        self.set_valid_voltages()


    def update_redblue_plot(self,plot_dict):
        x = range(0, len(self.__controller.plot_top_data))
        plot_dict['blue_line'].set_data(x, self.__controller.plot_top_data)
        plot_dict['red_line'].set_data(x, self.__controller.plot_bot_data)
        plot_dict['latency_line'].set_xdata(self.__controller.latency)
        if self.__controller.ylim:
            plot_dict['blue'].set_ylim(0,self.__controller.ylim)
            plot_dict['blue'].set_xlim(0,self.__controller.xlim)
            self.__controller.reset_lim()
        
        self.__redblue_canvas.draw()

    def update_redgreenlaser_plot(self,plot_dict):
        x = range(0, len(self.__controller.plot_top_data))
        plot_dict['laser_line'].set_data(x,self.__controller.plot_mid_data)
        plot_dict['green_line'].set_data(x, self.__controller.plot_top_data)
        plot_dict['red_line'].set_data(x, self.__controller.plot_bot_data)
        plot_dict['latency_line'].set_xdata(self.__controller.latency)
        if self.__controller.ylim:
            plot_dict['laser'].set_ylim(0,self.__controller.ylim+0.1)
            plot_dict['green'].set_ylim(0,self.__controller.ylim+0.1)
            plot_dict['green'].set_xlim(0,self.__controller.xlim)
            self.__controller.reset_lim()
        
        self.__redgreenlaser_canvas.draw()

    def start_plotting(self):
        self.figure_timer.start()
    
    def stop_plotting(self):
        self.figure_timer.stop()

    def show_redblue_settings(self):
        if "to_mW" in dir(self):
            self.blue_mW_bottom = self.to_mW(0)
            self.blue_mW_top = self.to_mW(5)
        else:
            self.blue_mW_bottom = 0
            self.blue_mW_top = 0
        
        if not self.__redblue_settings:
            self.redgreenlaser_timer.stop()
            self.redblue_timer.start()
            # Figure
            self.__redblue_canvas.draw()
            self.__redblue_canvas.get_tk_widget().grid(row=0, column=0, sticky='new')
            self.__redblue_settings.append(self.__redblue_canvas.get_tk_widget())

            self.__redblue_toolbar.grid(row=1, column=0, sticky='w')
            self.__redblue_toolbar.update()
            self.__redblue_settings.append(self.__redblue_toolbar)

            # Blue light settings
            self.blue_labelframe = ttk.LabelFrame(self.__settings_frame, text='Blue light settings')
            self.blue_labelframe.grid(row=2, column=1, pady=10)
            self.__redblue_settings.append(self.blue_labelframe)

            # Waveform type
            bluewavetype_labelframe = ttk.LabelFrame(self.blue_labelframe, text="Waveform Type")
            bluewavetype_labelframe.grid(row=0, column=0)
            self.__redblue_settings.append(bluewavetype_labelframe)

            ramp_radiobutton = ttk.Radiobutton(bluewavetype_labelframe, text="Ramp", variable=self.__bluewavetype_var, value="Ramp", command=self.set_valid_lengths)
            ramp_radiobutton['state'] = self.__state
            ramp_radiobutton.grid(row=0, column=0)
            self.__redblue_settings.append(ramp_radiobutton)

            pulse_radiobutton = ttk.Radiobutton(bluewavetype_labelframe, text="Pulse", variable=self.__bluewavetype_var, value="Pulse", command=self.set_valid_lengths)
            pulse_radiobutton['state'] = self.__state
            pulse_radiobutton.grid(row=0, column=1)
            self.__redblue_settings.append(pulse_radiobutton)

            pulse_train_radiobutton = ttk.Radiobutton(bluewavetype_labelframe, text="Pulse Train", variable=self.__bluewavetype_var, value="Pulse Train", command=self.set_valid_lengths)
            pulse_train_radiobutton['state'] = self.__state
            pulse_train_radiobutton.grid(row=1, column=0)
            self.__redblue_settings.append(pulse_train_radiobutton)            

            self.__bluewavetype_var.set("Ramp")

            # Waveform length (ms)
            bluelength_labelframe = ttk.LabelFrame(self.blue_labelframe, text="Length (ms)")
            bluelength_labelframe.grid(row=0, column=1)
            self.__redblue_settings.append(bluelength_labelframe)

            self.__bluelength_label = ttk.Label(bluelength_labelframe)
            self.__bluelength_label.grid(row=0, column=0)
            self.__redblue_settings.append(self.__bluelength_label)

            bluelength_spinbox = tk.Spinbox(bluelength_labelframe, from_=10, to=30000, increment=1, textvariable=self.__bluelength_var)
            bluelength_spinbox['state'] = self.__state
            bluelength_spinbox.grid(row=1, column=0)
            self.__redblue_settings.append(bluelength_spinbox)

            # Waveform voltage (V)
            bluevoltage_labelframe = ttk.LabelFrame(self.blue_labelframe, text="Power (mW)")
            bluevoltage_labelframe.grid(row=0, column=2)
            self.__redblue_settings.append(bluevoltage_labelframe)

            self.__bluevoltage_label = ttk.Label(bluevoltage_labelframe)
            self.__bluevoltage_label.grid(row=0, column=0)
            self.__redblue_settings.append(self.__bluevoltage_label)

            bluevoltage_spinbox = tk.Spinbox(bluevoltage_labelframe, from_=self.blue_mW_bottom, to=self.blue_mW_top, increment=0.01, textvariable=self.__bluevoltage_var)
            
            #to_mW is the convserion based on calibration. It gets defined when the calibration is loaded in photostimulator tool 
            if "to_mW" in dir(self):
                bluevoltage_spinbox['state'] = 'normal'
            else:
                bluevoltage_spinbox['state'] = 'disabled'
            bluevoltage_spinbox.grid(row=1, column=0)
            self.__redblue_settings.append(bluevoltage_spinbox)

        else:
            self.redgreenlaser_timer.stop()
            self.redblue_timer.start()
            for item in self.__redblue_settings:
                item.grid()
    

    def remove_redblue_settings(self):
        for item in self.__redblue_settings:
            item.grid_remove()
    
    def remove_pulsetrain_settings(self):
        for item in self.pulse_train_settings:
            item.grid_remove()

    def show_redblue_pulsetrain(self):
        self.pulse_train_settings = []
        # PulseTrain Frequency
        bluefreq_labelframe = ttk.LabelFrame(self.blue_labelframe, text="Freq (Hz)")
        bluefreq_labelframe.grid(row=1, column=1)
        self.__redblue_settings.append(bluefreq_labelframe)
        self.pulse_train_settings.append(bluefreq_labelframe)

        self.__bluefreq_label = ttk.Label(bluefreq_labelframe)
        self.__bluefreq_label.grid(row=0, column=0)
        self.__redblue_settings.append(self.__bluefreq_label)
        self.pulse_train_settings.append(self.__bluefreq_label)

        bluefreq_spinbox = tk.Spinbox(bluefreq_labelframe, from_=0.1, to=20, increment=0.1, textvariable=self.__bluefreq_var)
        bluefreq_spinbox['state'] = self.__state
        bluefreq_spinbox.grid(row=1, column=0)
        self.__redblue_settings.append(bluefreq_spinbox)
        self.pulse_train_settings.append(bluefreq_spinbox)
        self.__bluefreq_label.config(text="valid range: 0.1 - 20")

        # PulseTrain Number of pulses
        bluenum_labelframe = ttk.LabelFrame(self.blue_labelframe, text="#Pulses")
        bluenum_labelframe.grid(row=1, column=2)
        self.__redblue_settings.append(bluenum_labelframe)
        self.pulse_train_settings.append(bluenum_labelframe)

        self.__bluenum_label = ttk.Label(bluenum_labelframe)
        self.__bluenum_label.grid(row=0, column=0)
        self.__redblue_settings.append(self.__bluenum_label)
        self.pulse_train_settings.append(self.__bluenum_label)

        bluenum_spinbox = tk.Spinbox(bluenum_labelframe, from_=1, to=100, increment=1, textvariable=self.__bluenum_var)
        bluenum_spinbox['state'] = self.__state
        bluenum_spinbox.grid(row=1, column=0)
        self.__redblue_settings.append(bluenum_spinbox)
        self.pulse_train_settings.append(bluenum_spinbox)
        self.__bluenum_label.config(text="valid range: 1 - 100")

    # display user parameters and figure for red/green/laser configuration
    def show_redgreenlaser_settings(self):
        if not self.__redgreenlaser_settings:
            self.redblue_timer.stop()
            self.redgreenlaser_timer.start()
            # Figure
            self.__redgreenlaser_canvas.draw()
            self.__redgreenlaser_canvas.get_tk_widget().grid(row=0, column=0, sticky='ew')
            self.__redgreenlaser_settings.append(self.__redgreenlaser_canvas.get_tk_widget())

            self.__redgreenlaser_toolbar.grid(row=1, column=0, sticky='w')
            self.__redgreenlaser_toolbar.update()
            self.__redgreenlaser_settings.append(self.__redgreenlaser_toolbar)

            # Green light settings
            green_labelframe = ttk.LabelFrame(self.__settings_frame, text='Green light settings')
            green_labelframe.grid(row=2, column=1, pady=10)
            self.__redgreenlaser_settings.append(green_labelframe)

            # Waveform length (ms)
            greenlength_labelframe = ttk.LabelFrame(green_labelframe, text="Length (ms)")
            greenlength_labelframe.grid(row=0, column=0)
            self.__redgreenlaser_settings.append(greenlength_labelframe)

            self.__greenlength_label = ttk.Label(greenlength_labelframe)
            self.__greenlength_label.grid(row=0, column=0)
            self.__redgreenlaser_settings.append(self.__greenlength_label)

            greenlength_spinbox = tk.Spinbox(greenlength_labelframe, from_=1000, to=20000, increment=1, textvariable=self.__greenlength_var)
            greenlength_spinbox['state'] = self.__state
            greenlength_spinbox.grid(row=1, column=0)
            self.__redgreenlaser_settings.append(greenlength_spinbox)

            # Waveform voltage (V)
            greenvoltage_labelframe = ttk.LabelFrame(green_labelframe, text="Voltage (V)")
            greenvoltage_labelframe.grid(row=0, column=1)
            self.__redgreenlaser_settings.append(greenvoltage_labelframe)

            self.__greenvoltage_label = ttk.Label(greenvoltage_labelframe)
            self.__greenvoltage_label.grid(row=0, column=0)
            self.__redgreenlaser_settings.append(self.__greenvoltage_label)

            greenvoltage_spinbox = tk.Spinbox(greenvoltage_labelframe, from_=0, to=5, increment=0.01, textvariable=self.__greenvoltage_var)
            greenvoltage_spinbox['state'] = self.__state
            greenvoltage_spinbox.grid(row=1, column=0)
            self.__redgreenlaser_settings.append(greenvoltage_spinbox)

            # LASER settings
            laser_labelframe = ttk.LabelFrame(self.__settings_frame, text='LASER settings')
            laser_labelframe.grid(row=2, column=2, pady=10)
            self.__redgreenlaser_settings.append(laser_labelframe)

            # Waveform voltage (V)
            laservoltage_labelframe = ttk.LabelFrame(laser_labelframe, text="Voltage (V)")
            laservoltage_labelframe.grid(row=0, column=0)
            self.__redgreenlaser_settings.append(laservoltage_labelframe)

            self.__laservoltage_label = ttk.Label(laservoltage_labelframe)
            self.__laservoltage_label.grid(row=0, column=0)
            self.__redgreenlaser_settings.append(self.__laservoltage_label)

            laservoltage_spinbox = tk.Spinbox(laservoltage_labelframe, from_=0, to=5, increment=0.01, textvariable=self.__laservoltage_var)
            laservoltage_spinbox['state'] = self.__state
            laservoltage_spinbox.grid(row=1, column=0)
            self.__redgreenlaser_settings.append(laservoltage_spinbox)

            # set valid values
            self.set_valid_lengths()
            self.set_valid_voltages()

        else:
            self.redblue_timer.stop()
            self.redgreenlaser_timer.start()
            for item in self.__redgreenlaser_settings:
                item.grid()

    def remove_redgreenlaser_settings(self):
        for item in self.__redgreenlaser_settings:
            item.grid_remove()

    def config_option_changed(self, *args):
        mode_option = self.__config_var.get()
        if mode_option == PhotostimulatorTool.REDBLUE_CONFIG_NAME:
            self.remove_redgreenlaser_settings()
            self.show_redblue_settings()
        elif mode_option == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
            self.remove_redblue_settings()
            self.show_redgreenlaser_settings()

    def get_launch_settings(self):
        settings = {}

        mode_option = self.__config_var.get()
        settings['mode'] = mode_option

        if mode_option == PhotostimulatorTool.REDBLUE_CONFIG_NAME:
            # red light settings
            settings['red_voltage'] = self.__redvoltage_var.get()
            settings['red_threshold'] = self.__redthreshold_var.get()

            # blue light settings
            settings['blue_wavetype'] = self.__bluewavetype_var.get()
            settings['blue_length'] = self.__bluelength_var.get()
            settings['blue_power'] = self.__bluevoltage_var.get()
            settings['blue_voltage'] = self.to_V(settings['blue_power'])
            a, b = self.calibration_params
            settings['calibration_slope'] = float(a)
            settings['calibration_intercept'] = float(b)
            settings['calibration_filename'] = self.last_cal

        elif mode_option == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
            # red light settings
            settings['red_voltage'] = self.__redvoltage_var.get()
            settings['red_threshold'] = self.__redthreshold_var.get()

            # green light settings
            settings['green_length'] = self.__greenlength_var.get()
            settings['green_voltage'] = self.__greenvoltage_var.get()

            # laser settings
            settings['laser_voltage'] = self.__laservoltage_var.get()

        return settings

    def get_current_configuration(self):
        return self.__config_var.get()

    def get_waveform_data(self):
        data = None

        mode_option = self.__config_var.get()

        if mode_option == PhotostimulatorTool.REDBLUE_CONFIG_NAME:
            data = self.__receive_redblue
        elif mode_option == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
            data = self.__receive_redgreenlaser

        return data

    # label valid waveform lengths, given by controller parameters
    def set_valid_lengths(self):
        mode_option = self.__config_var.get()


        if mode_option == PhotostimulatorTool.REDBLUE_CONFIG_NAME:
            self.remove_pulsetrain_settings()
            blue_wavetype = self.__bluewavetype_var.get()

            valid_low = 0
            valid_high = 0

            if blue_wavetype == "Ramp":
                valid_low, valid_high = self.__controller.get_valid_lengths("Ramp")
            elif blue_wavetype == "Pulse":
                valid_low, valid_high = self.__controller.get_valid_lengths("Pulse")
            elif blue_wavetype == "Pulse Train":
                self.show_redblue_pulsetrain()
                valid_low, valid_high = (1,1000)

            valid_text = "valid range: " + str(valid_low) + " - " + str(valid_high)

            self.__bluelength_label.config(text=valid_text)

        elif mode_option == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
            # TODO: get values from controller
            # red/green/laser configuration
            valid_text = "valid range: " + str(1000) + " - " + str(20000)

            self.__greenlength_label.config(text=valid_text)

    # label valid voltages, given by controller parameters
    def set_valid_voltages(self):
        valid_low = self.__controller.VALID_VOLTAGE_LOW
        valid_high = self.__controller.VALID_VOLTAGE_HIGH

        valid_text = "valid range: " + str(valid_low) + " - " + str(valid_high)
        blue_text = "valid range: {:.2f} - {:.2f}".format(self.blue_mW_bottom, self.blue_mW_top)

        mode_option = self.__config_var.get()

        if mode_option == PhotostimulatorTool.REDBLUE_CONFIG_NAME:
            self.__bluevoltage_label.config(text=blue_text)
            self.__redvoltage_label.config(text=valid_text)

        elif mode_option == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
            self.__greenvoltage_label.config(text=valid_text)
            self.__laservoltage_label.config(text=valid_text)

    # launch photostimuli
    def launch_waveform(self, plot=True, hsv_params = {}):
        mode_option = self.__config_var.get()

        if mode_option == PhotostimulatorTool.REDBLUE_CONFIG_NAME:
            blue_wavetype = self.__bluewavetype_var.get()
            blue_length = self.__bluelength_var.get()
            blue_mW = self.__bluevoltage_var.get()
            blue_voltage = self.to_V(blue_mW)
            blue_freq = self.__bluefreq_var.get()
            blue_num = self.__bluenum_var.get()

            red_threshold = self.__redthreshold_var.get()
            red_voltage = self.__redvoltage_var.get()


            message = "Launch Red/Blue: red voltage(V)=" + str(red_voltage) + " red threshold=" + str(red_threshold)
            message += " type=" + str(blue_wavetype) + " length(ms)=" + str(blue_length) + " blue voltage(V)=" + str(blue_voltage)
            DebugLog.debugprint(self, message)

            try:
                receive_blue = None
                receive_red = None
                if str(blue_wavetype) == "Ramp":
                    receive_blue, receive_red = self.__controller.ramp_redblue(float(blue_length), float(blue_voltage), float(red_threshold), float(red_voltage),hsv_params = hsv_params)
                elif str(blue_wavetype) == "Pulse":
                    receive_blue, receive_red = self.__controller.pulse_redblue(float(blue_length), float(blue_voltage), float(red_threshold), float(red_voltage), hsv_params = hsv_params)
                elif str(blue_wavetype) == "Pulse Train":
                    receive_blue, receive_red = self.__controller.pulsetrain_redblue(float(blue_length),float(blue_voltage),float(blue_freq),int(blue_num),float(red_threshold),float(red_voltage), hsv_params = hsv_params)

                self.__receive_redblue['blue'] = receive_blue
                self.__receive_redblue['red'] = receive_red

                # plot signals
                if plot:
                    self.draw_plot(mode_option, self.__receive_redblue)

            except Exception as err:
                # pop-up message on error
                message = 'Failed to launch waveform: ' + str(err)

                DebugLog.debugprint(self, message)

                showerror(title='Error', message=message)

        elif mode_option == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
            green_length = self.__greenlength_var.get()
            green_voltage = self.__greenvoltage_var.get()
            laser_voltage = self.__laservoltage_var.get()
            red_threshold = self.__redthreshold_var.get()
            red_voltage = self.__redvoltage_var.get()

            message = "Launch Red/Green/LASER: red voltage(V)=" + str(red_voltage) + " red threshold=" + str(red_threshold)
            message += " length(ms)=" + str(green_length) + " green voltage(V)=" + str(green_voltage) + " laser voltage(V)=" + str(laser_voltage)
            DebugLog.debugprint(self, message)

            try:
                # TODO: can't sample 3 channels at 1000 Hz accurately (1 Mhz not divisible by 3000 Hz)
                receive_green, receive_laser, receive_red = self.__controller.pulse_redgreenlaser(float(green_length), float(green_voltage), float(laser_voltage), float(red_threshold), float(red_voltage))

                self.__receive_redgreenlaser['green'] = receive_green
                self.__receive_redgreenlaser['laser'] = receive_laser
                self.__receive_redgreenlaser['red'] = receive_red

                # plot signals
                if plot:
                    self.draw_plot(mode_option, self.__receive_redgreenlaser)

            except Exception as err:
                # pop-up message on error
                message = 'Failed to launch waveform: ' + str(err)

                DebugLog.debugprint(self, message)

                showerror(title='Error', message=message)

    def thread_launch(self):
        thread = threading.Thread(target=self.launch_waveform,kwargs={'plot':False})
        thread.start()

    def draw_plot(self, config, data):
        if config == PhotostimulatorTool.REDBLUE_CONFIG_NAME:
            receive_blue = data['blue']
            receive_red = data['red']
            # TODO: would need to define x axis should controller's sampling rate not be 1000 Hz
            self.__redblue_plots['blue'].clear()
            self.__redblue_plots['red'].clear()
            self.__redblue_plots['blue'].plot(receive_blue, color='blue')
            self.__redblue_plots['red'].plot(receive_red, color='red')
            self.__redblue_plots['red'].axvline(analyze_latency(receive_red, threshold=float(self.__redthreshold_var.get())), linestyle='--', c='k')
            self.__redblue_plots['blue'].grid()
            self.__redblue_plots['red'].grid()

            # TODO: not thread-safe? UserInterface crashes when called
            self.__redblue_canvas.draw()

        elif config == PhotostimulatorTool.REDGREENLASER_CONFIG_NAME:
            receive_green = data['green']
            receive_laser = data['laser']
            receive_red = data['red']
            # TODO: would need to define x axis should controller's sampling rate not be 1000 Hz
            self.__redgreenlaser_plots['green'].clear()
            self.__redgreenlaser_plots['laser'].clear()
            self.__redgreenlaser_plots['red'].clear()
            self.__redgreenlaser_plots['green'].plot(receive_green, color='green')
            self.__redgreenlaser_plots['laser'].plot(receive_laser, color='purple')
            self.__redgreenlaser_plots['red'].plot(receive_red, color='red')
            self.__redgreenlaser_plots['red'].axvline(analyze_latency(receive_red, threshold=float(self.__redthreshold_var.get())), linestyle='--', c='k')
            self.__redgreenlaser_plots['green'].grid()
            self.__redgreenlaser_plots['laser'].grid()
            self.__redgreenlaser_plots['red'].grid()

            # TODO: not thread-safe? UserInterface crashes when called
            self.__redgreenlaser_canvas.draw()
    
    def set_DAC1(self,V):
        if 0 <= V < 5:
            self.__controller.set_DAC1(V)
            return True
        else:
            return False
    
    def load_calibration(self):
        path = PhotostimulatorTool.CALIBRATION_PATH
        calibrations = glob(path + '*.pickle')
        if calibrations:
            calibrations.sort(key=os.path.getctime)
            self.last_cal = calibrations[-1]
            with open(self.last_cal, 'rb') as handle:
                self.calibration_params = pickle.load(handle)
                print(self.last_cal)
                DebugLog.debugprint(self,"Loaded calibration, {}: Slope={}, Intercept={}".format(self.last_cal, self.calibration_params[0],self.calibration_params[1]))
                def to_mW(V):
                    return self.calibration_params[0]*V + self.calibration_params[1]
                self.to_mW = to_mW
                self.__controller.set_conversion(to_mW)
                def to_V(mW):
                    return (mW - self.calibration_params[1])/self.calibration_params[0]
                self.to_V = to_V
        else:
            showerror(title='Missing Calibration',message='Could not find calibration data. Opening Calibration Tool')
            calibration_window = CalibrationWindow(master = self.__master, photostimulator=self, calibration_path=path)
    
    def calibrate(self):
        calibration_window = CalibrationWindow(master = self.__master, photostimulator=self, calibration_path=PhotostimulatorTool.CALIBRATION_PATH)



def analyze_latency(array,threshold=0.9):
    red_data = BlueLightTerminator(threshold)
    for i in array:
        red_data.update(i)
        if red_data.terminate():
            break
    return red_data.return_latency()

if __name__ == '__main__':
    root = tk.Tk()
    root.title('Photostimulator Tool')
    root.geometry("720x800")
    window = PhotostimulatorTool(root)

    root.mainloop()
