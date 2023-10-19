import tkinter as tk
import tkinter.ttk as ttk
from tkinter import filedialog
import pyperclip

import os

class HighSpeedFilenameWindow(tk.Toplevel):
    def __init__(self, path, filename, mouse_id, trial_id, master=None):
        super().__init__(master=master)
        self.title('High Speed Filename')
        self.geometry("425x100")
        self.HSV_filename = filename + '_mouse' + str(mouse_id) + '_trial' + str(trial_id) + '_highspeed'
        if not os.path.exists(path + '\\' + filename + '_highspeed_videos'):
            os.mkdir(path + '\\' + filename + '_highspeed_videos')
        
        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, padx=10, pady=10)
        
        label = tk.Label(frame, text='Copied to clipboard (can\'t edit):')
        label.grid(row=0,column=0,sticky='w')

        textbox = tk.Text(frame, width=50, height=1)
        textbox.insert('1.0', self.HSV_filename)
        textbox.grid(row=1, column=0)
        pyperclip.copy(self.HSV_filename)

        ok_button = ttk.Button(frame, text='OK', command=self.ok_button_event)
        ok_button.grid(row=2, column=0, pady=16)
    
    def get_filename(self):
        return self.HSV_filename
    
    def ok_button_event(self):
        self.grab_release()
        self.destroy()