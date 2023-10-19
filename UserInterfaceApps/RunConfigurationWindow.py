import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog

import os


class RunConfigurationWindow(tk.Toplevel):
    def __init__(self, master=None, mouse_info_label = None):
        super().__init__(master=master)
        self.title('New Recording')
        self.geometry("540x500")

        settings_frame = ttk.Frame(self)
        settings_frame.grid(row=0, column=0, padx=10, pady=10)

        self.mouse_info_label = mouse_info_label

        # ================================== file settings ==================================
        filesettings_frame = ttk.Frame(settings_frame)
        filesettings_frame.grid(row=0, column=0)

        filesettings_label = ttk.Label(filesettings_frame, text='File Settings')
        filesettings_label.grid(row=0, column=0, sticky='nw')

        # save filepath
        self.__selectedfolder = ''

        selectfolder_label = ttk.Label(filesettings_frame, text='Selected Folder:')
        selectfolder_label.grid(row=1, column=0, pady=4)

        # assumes a 'data_output' folder exists in current directory
        self.__output_directory = str(os.getcwd()) + '\\' + 'data_output'
        self.__selectfolder_textbox = tk.Text(filesettings_frame, width=50, height=1)
        self.__selectfolder_textbox.insert('1.0', self.__output_directory)
        self.__selectfolder_textbox['state'] = 'disabled'
        self.__selectfolder_textbox.grid(row=1, column=1)

        selectfolder_button = ttk.Button(filesettings_frame, text='Browse...', command=self.browse_button_event)
        selectfolder_button.grid(row=2, columnspan=2, sticky='se')

        # save filename
        self.__filename = ''

        filename_label = ttk.Label(filesettings_frame, text='Filename:')
        filename_label.grid(row=3, column=0, pady=10, sticky='e')

        # TODO: validate filename
        self.__filename_textbox = tk.Text(filesettings_frame, width=50, height=1)
        self.__filename_textbox.insert('1.0', 'untitled')
        self.__filename_textbox.grid(row=3, column=1, pady=10)

        # trial number
        trial_label = ttk.Label(filesettings_frame, text='Trial Number:')
        trial_label.grid(row=4, column=0, pady=10, sticky='e')

        self.__trial_var = tk.IntVar()
        trial_spinbox = tk.Spinbox(filesettings_frame, from_=1, to=100, increment=1, width=4, textvariable=self.__trial_var)
        trial_spinbox.grid(row=4, column=1, sticky='w')

        # file types
        filetypes_label = ttk.Label(filesettings_frame, text='File Type(s):')
        filetypes_label.grid(row=5, column=0, sticky='e')

        self.__HDF5file_var = tk.IntVar()
        self.__HDF5file_var.set(1)
        # HDF5file_checkbox = ttk.Checkbutton(filesettings_frame, text='HDF5', variable=self.__HDF5file_var)
        # HDF5file_checkbox.grid(row=5, column=1, sticky='w')

        self.__CSVfile_var = tk.IntVar()
        CSVfile_checkbox = ttk.Checkbutton(filesettings_frame, text='CSV', variable=self.__CSVfile_var)
        CSVfile_checkbox.grid(row=6, column=1, sticky='w')

        # ================================== operating settings ==================================
        settings_separator = ttk.Separator(settings_frame, orient='horizontal')
        settings_separator.grid(row=1, column=0, sticky='ew', pady=4)

        self.__operatingsettings_frame = ttk.Frame(settings_frame)
        self.__operatingsettings_frame.grid(row=2, column=0, pady=4, sticky='ew')

        operatingsettings_label = ttk.Label(self.__operatingsettings_frame, text='Operating Settings')
        operatingsettings_label.grid(row=0, column=0, sticky='w')

        #high speed video
        self.__HSV_length_var = tk.DoubleVar()
        self.__HSV_fps_var = tk.IntVar()
        HSV_label = ttk.Label(self.__operatingsettings_frame, text='Trigger High Speed Cam:')
        HSV_label.grid(row=1, column=0, sticky='w')

        self.__useHSV_var = tk.IntVar()
        useHSV_checkbox = ttk.Checkbutton(self.__operatingsettings_frame, text='', variable=self.__useHSV_var,command=self.HSVsettings)
        useHSV_checkbox.grid(row=1, column=1,sticky='w')

        
        # operating mode
        mode_label = ttk.Label(self.__operatingsettings_frame, text='Operating Mode:')
        mode_label.grid(row=2, column=0, sticky='w')

        self.__mode_var = tk.StringVar(self.__operatingsettings_frame)
        self.__mode_options = ('Manual', 'Automatic')
        mode_optionmenu = ttk.OptionMenu(self.__operatingsettings_frame, self.__mode_var, self.__mode_options[0], *self.__mode_options, command=self.mode_option_changed)
        mode_optionmenu.grid(row=2, column=1, sticky='w')

        # manual mode: variables
        self.__startdelay_var = tk.IntVar()
        self.__stopdelay_var = tk.IntVar()

        self.__manual_settings = []
        self.show_manual_settings()

        # automatic mode: variables
        self.__stimulustrigger_var = tk.StringVar()

        self.__detectionlimit_var = tk.IntVar()
        self.__detectionlimit_var.set(30)

        self.__centredtime_var = tk.IntVar()
        self.__centredtime_var.set(10)

        self.__micecount_textbox = tk.Text(self.__operatingsettings_frame, width=3, height=1)
        self.__micecount_textbox.insert('1.0', '1')
        self.__micecount_textbox['state'] = 'disabled'

        self.__mousestart_var = tk.IntVar()
        self.__mousestop_var = tk.IntVar()

        self.__rowselect_var = tk.StringVar(self.__operatingsettings_frame)
        self.__rowselect_options = ('F', 'B')

        self.__automatic_settings = []
        self.HSVsettings_items = []

        # ok button
        self.__ok_button_pressed = False

        self.__ok_button = ttk.Button(settings_frame, text='OK', command=self.ok_button_event)
        self.__ok_button.grid(row=3, column=0, pady=16, sticky='se')

        # disable window resize
        self.resizable(False, False)
        # wait until visible before grabbing
        self.wait_visibility()
        # keep window focused
        self.grab_set()

    def did_press_ok(self):
        return self.__ok_button_pressed

    # get the last inputted configuration parameters
    def get_parameters(self):
        parameters = {}

        parameters['selectedfolder'] = self.__selectedfolder
        parameters['filename'] = self.__filename
        parameters['trial'] = self.__trial_var.get()
        parameters['is_HDF5'] = self.__HDF5file_var.get()
        parameters['is_CSV'] = self.__CSVfile_var.get()

        mode = self.__mode_var.get()
        parameters['mode'] = mode
        parameters['use_hsv'] = self.__useHSV_var.get()
        if parameters['use_hsv']:
            parameters['hsv_fps'] = self.__HSV_fps_var.get()
            parameters['hsv_length'] = self.__HSV_length_var.get()
        if mode == 'Manual':
            parameters['startdelay'] = self.__startdelay_var.get()
            parameters['stopdelay'] = self.__stopdelay_var.get()
        elif mode == 'Automatic':
            parameters['trigger'] = self.__stimulustrigger_var.get()
            parameters['detectionlimit'] = self.__detectionlimit_var.get()
            parameters['centredtime'] = self.__centredtime_var.get()
            parameters['rowselect'] = self.__rowselect_var.get()
            parameters['mousestart'] = self.__mousestart_var.get()
            parameters['mousestop'] = self.__mousestop_var.get()

        return parameters

    # insert the last inputted configuration parameters
    # exceptions: invalid parameter values
    def set_parameters(self, parameters):
        self.__selectedfolder = parameters['selectedfolder']
        self.__selectfolder_textbox['state'] = 'normal'
        self.__selectfolder_textbox.delete('1.0', tk.END)
        self.__selectfolder_textbox.insert('1.0', self.__selectedfolder)
        self.__selectfolder_textbox['state'] = 'disabled'

        self.__filename = parameters['filename']
        self.__filename_textbox.delete('1.0', tk.END)
        self.__filename_textbox.insert('1.0', self.__filename)

        self.__trial_var.set(parameters['trial'])

        self.__HDF5file_var.set(parameters['is_HDF5'])
        self.__CSVfile_var.set(parameters['is_CSV'])

        mode = parameters['mode']
        self.__mode_var.set(mode)
        self.mode_option_changed()
        self.__useHSV_var.set(parameters['use_hsv'])
        self.HSVsettings()
        if self.__useHSV_var.get():
            self.__HSV_fps_var.set(parameters['hsv_fps'])
            self.__HSV_length_var.set(parameters['hsv_length'])
        
        if mode == 'Manual':
            self.__startdelay_var.set(parameters['startdelay'])
            self.__stopdelay_var.set(parameters['stopdelay'])
        elif mode == 'Automatic':
            self.__stimulustrigger_var.set(parameters['trigger'])
            self.__detectionlimit_var.set(parameters['detectionlimit'])
            self.__centredtime_var.set(parameters['centredtime'])
            self.__rowselect_var.set(parameters['rowselect'])
            self.__mousestart_var.set(parameters['mousestart'])
            self.__mousestop_var.set(parameters['mousestop'])

    def show_manual_settings(self):
        if not self.__manual_settings:
            # start delay
            startdelay_label = ttk.Label(self.__operatingsettings_frame, text='Start Delay (s):')
            startdelay_label.grid(row=3, column=0, sticky='w')
            self.__manual_settings.append(startdelay_label)

            startdelay_spinbox = tk.Spinbox(self.__operatingsettings_frame, from_=0, to=5, increment=1, textvariable=self.__startdelay_var)
            startdelay_spinbox.grid(row=3, column=1, sticky='w')
            self.__manual_settings.append(startdelay_spinbox)

            # stop delay
            stopdelay_label = ttk.Label(self.__operatingsettings_frame, text='Stop Delay (s):')
            stopdelay_label.grid(row=4, column=0, sticky='w')
            self.__manual_settings.append(stopdelay_label)

            stopdelay_spinbox = tk.Spinbox(self.__operatingsettings_frame, from_=0, to=5, increment=1, textvariable=self.__stopdelay_var)
            stopdelay_spinbox.grid(row=4, column=1, sticky='w')
            self.__manual_settings.append(stopdelay_spinbox)

        else:
            for item in self.__manual_settings:
                item.grid()

    def remove_manual_settings(self):
        for item in self.__manual_settings:
            item.grid_remove()

    def show_automatic_settings(self):
        if not self.__automatic_settings:
            # automatic (paw tracking) or manual trigger
            stimulustrigger_label = ttk.Label(self.__operatingsettings_frame, text='Stimulus Trigger:')
            stimulustrigger_label.grid(row=3, column=0, sticky='w')
            self.__automatic_settings.append(stimulustrigger_label)

            manualtrigger_radiobutton = ttk.Radiobutton(self.__operatingsettings_frame, text="Manual", variable=self.__stimulustrigger_var, value="manual")
            manualtrigger_radiobutton.grid(row=3, column=1, sticky='w')
            self.__automatic_settings.append(manualtrigger_radiobutton)

            detectpawtrigger_radiobutton = ttk.Radiobutton(self.__operatingsettings_frame, text="Auto-detect paw", variable=self.__stimulustrigger_var, value="autodetect")
            detectpawtrigger_radiobutton.grid(row=4, column=1, sticky='w')
            self.__automatic_settings.append(detectpawtrigger_radiobutton)

            self.__stimulustrigger_var.set('manual')

            # detection time limit
            detectionlimit_label = ttk.Label(self.__operatingsettings_frame, text='Paw Detection Time Limit (s):')
            detectionlimit_label.grid(row=5, column=0, sticky='w')
            self.__automatic_settings.append(detectionlimit_label)

            detectionlimit_spinbox = tk.Spinbox(self.__operatingsettings_frame, from_=0, to=60, increment=1, textvariable=self.__detectionlimit_var)
            detectionlimit_spinbox.grid(row=5, column=1, sticky='w')
            self.__automatic_settings.append(detectionlimit_spinbox)

            # centred time
            centredtime_label = ttk.Label(self.__operatingsettings_frame, text='Paw Centred Time Frame (s):')
            centredtime_label.grid(row=6, column=0, sticky='w')
            self.__automatic_settings.append(centredtime_label)

            centredtime_spinbox = tk.Spinbox(self.__operatingsettings_frame, from_=0, to=30, increment=1, textvariable=self.__centredtime_var)
            centredtime_spinbox.grid(row=6, column=1, sticky='w')
            self.__automatic_settings.append(centredtime_spinbox)

            # row select
            rowselect_label = ttk.Label(self.__operatingsettings_frame, text='Row Select (F/B):')
            rowselect_label.grid(row=7, column=0, sticky='w')
            self.__automatic_settings.append(rowselect_label)

            rowselect_optionmenu = ttk.OptionMenu(self.__operatingsettings_frame, self.__rowselect_var, self.__rowselect_options[0], *self.__rowselect_options)
            rowselect_optionmenu.grid(row=7, column=1, sticky='w')
            self.__automatic_settings.append(rowselect_optionmenu)

            # number of mice
            micecount_label = ttk.Label(self.__operatingsettings_frame, text='Number of Mice:')
            micecount_label.grid(row=8, column=0, sticky='w')
            self.__automatic_settings.append(micecount_label)

            self.__micecount_textbox.grid(row=8, column=1, sticky='w')
            self.__automatic_settings.append(self.__micecount_textbox)

            # mouse start
            mousestart_label = ttk.Label(self.__operatingsettings_frame, text='Mouse Start:')
            mousestart_label.grid(row=9, column=0, sticky='w')
            self.__automatic_settings.append(mousestart_label)

            mousestart_spinbox = tk.Spinbox(self.__operatingsettings_frame, from_=1, to=12, increment=1, textvariable=self.__mousestart_var, command=self.mouse_startstop_changed)
            mousestart_spinbox.grid(row=9, column=1, sticky='w')
            self.__automatic_settings.append(mousestart_spinbox)

            # mouse stop
            mousestop_label = ttk.Label(self.__operatingsettings_frame, text='Mouse Stop:')
            mousestop_label.grid(row=10, column=0, sticky='w')
            self.__automatic_settings.append(mousestop_label)

            mousestop_spinbox = tk.Spinbox(self.__operatingsettings_frame, from_=1, to=12, increment=1, textvariable=self.__mousestop_var, command=self.mouse_startstop_changed)
            mousestop_spinbox.grid(row=10, column=1, sticky='w')
            self.__automatic_settings.append(mousestop_spinbox)

        else:
            for item in self.__automatic_settings:
                item.grid()

    def remove_automatic_settings(self):
        for item in self.__automatic_settings:
            item.grid_remove()

    def HSVsettings(self):
        if self.__useHSV_var.get():
            frame_rate_label = ttk.Label(self.__operatingsettings_frame, text='FPS:')
            frame_rate_label.grid(row=1,column=2,sticky='w')
            self.HSVsettings_items.append(frame_rate_label)
            frame_rate_spinbox = tk.Spinbox(self.__operatingsettings_frame, from_=100, to=4000, increment=1, width=4, textvariable=self.__HSV_fps_var)
            frame_rate_spinbox.grid(row=1,column=3,sticky='w')
            self.HSVsettings_items.append(frame_rate_spinbox)


            length_label = ttk.Label(self.__operatingsettings_frame, text='Length (s):')
            length_label.grid(row=1,column=4,sticky='w')
            self.HSVsettings_items.append(length_label)
            length_spinbox = tk.Spinbox(self.__operatingsettings_frame, from_=1, to=5, increment=1, width=4, textvariable=self.__HSV_length_var)
            length_spinbox.grid(row=1,column=5,sticky='w')
            self.HSVsettings_items.append(length_spinbox)
        else:
            for item in self.HSVsettings_items:
                item.grid_remove()


    # TODO: implement
    # TODO: if name exist, pop-up if want to overwrite
    def validate(self):
        pass

    def browse_button_event(self):
        filename = filedialog.askdirectory(initialdir=self.__output_directory)
        if filename:
            self.__selectfolder_textbox['state'] = 'normal'
            self.__selectfolder_textbox.delete('1.0', tk.END)
            self.__selectfolder_textbox.insert('1.0', filename)
            self.__selectfolder_textbox['state'] = 'disabled'

    def mode_option_changed(self, *args):
        mode_option = self.__mode_var.get()
        if mode_option == 'Manual':
            self.remove_automatic_settings()
            self.show_manual_settings()
        elif mode_option == 'Automatic':
            self.remove_manual_settings()
            self.show_automatic_settings()

    def mouse_startstop_changed(self):
        start = self.__mousestart_var.get()
        stop = self.__mousestop_var.get()

        # adjust if user sets lower stop position
        if stop < start:
            self.__mousestart_var.set(stop)
            start = self.__mousestart_var.get()

        count = stop - start + 1
        self.__micecount_textbox['state'] = 'normal'
        self.__micecount_textbox.delete('1.0', tk.END)
        self.__micecount_textbox.insert('1.0', str(count))
        self.__micecount_textbox['state'] = 'disabled'

    def ok_button_event(self):
        self.__ok_button_pressed = True

        # capture parameters before closing
        self.__selectedfolder = self.__selectfolder_textbox.get('1.0', tk.END).rstrip()
        self.__filename = self.__filename_textbox.get('1.0', tk.END).rstrip()
        if self.mouse_info_label:
            self.mouse_info_label.filename = self.__filename
            self.mouse_info_label.filepath = self.__selectedfolder
            self.mouse_info_label.update_label()

        self.grab_release()
        self.destroy()