import tkinter as tk
from tkinter.messagebox import askyesno
import pandas as pd
import h5py
from PhotostimulatorTool import analyze_latency
import matplotlib.pyplot as plt
import numpy as np
import pathlib

def extract_latencies():
    filetypes = (
        ('HDF5 files', '*.hdf5'),
    )
    filenames = tk.filedialog.askopenfilenames(
        title = 'Select a data file',
        initialdir='./data_output',
        filetypes = filetypes
    )

    if not filenames:
        return
    
    check_latency = askyesno(title='', message='Do you want to manually validate?')

    for filename in filenames:
        data = {
            'Mouse': [],
            'Trial': [],
            'Datetime': [],
            'Waveform': [],
            'Green Voltage (V)': [],
            'Laser Voltage (V)': [],
            'Blue Voltage (V)': [],
            'Blue Power (mW)': [],
            'Stimulus Length (ms)': [],
            'Latency (ms)': [],
            'Good Trial': [],
            'Comments': [],
            'Video File': [],
            'Plot File': []
        }
        filepath = pathlib.Path(filename)
        parent = filepath.parents[0]
        plot_path = parent / (filepath.stem  + '_plots')
        if not((parent / plot_path).exists()):
            plot_path.mkdir()
        print(plot_path)
        data_file = h5py.File(filename,'r')
        for mouse,mouse_obj in data_file.items():
            for trial,trial_obj in mouse_obj.items():
                for name, trial_member in trial_obj.items():
                    if 'wave' in name:
                        mode = trial_member.attrs.get('mode',default=False)
                        mode = mode.decode('utf-8')
                        blue = trial_member[0]
                        red = trial_member[-1]
                        latency = analyze_latency(red) - 2000
                        data['Mouse'].append(mouse)
                        data['Trial'].append(trial_obj.attrs['num'])
                        data['Datetime'].append(trial_obj.attrs['timestamp'].decode('utf-8'))
                        data['Good Trial'].append(trial_obj.attrs.get('good_trial',default=1))
                        if mode == 'Red/Green/Laser':
                            data['Waveform'].append(np.nan)
                            data['Green Voltage (V)'].append(trial_member.attrs['green_voltage'])
                            data['Laser Voltage (V)'].append(trial_member.attrs['laser_voltage'])
                            data['Blue Voltage (V)'].append(np.nan)
                            data['Blue Power (mW)'].append(np.nan)
                            data['Stimulus Length (ms)'].append(np.nan)
                            this_plot_path = plot3(trial_member, latency, plot_path, parent, mouse, trial_obj.attrs['num'])
                        elif mode == 'Red/Blue':
                            data['Waveform'].append(trial_member.attrs['blue_wavetype'].decode('utf-8'))
                            data['Green Voltage (V)'].append(np.nan)
                            data['Laser Voltage (V)'].append(np.nan)
                            data['Blue Voltage (V)'].append(trial_member.attrs['blue_voltage'])
                            data['Blue Power (mW)'].append(trial_member.attrs['blue_power'])
                            data['Stimulus Length (ms)'].append(trial_member.attrs['blue_length'])
                            this_plot_path = plot2(trial_member, latency, plot_path, parent, mouse, trial_obj.attrs['num'])
                            if check_latency:
                                t = np.arange(0,len(red)) - 2000
                                title = '{m} Trial: {tr} Time: {t}'.format(m=mouse,tr=trial_obj.attrs['num'],t=trial_obj.attrs['timestamp'].decode('utf-8'))
                                a = latency_plot(t, latency, blue, red, title)
                                
                                if a.should_save:
                                    latency = a.Cline.position


                        #Check if comment exists as atribute, if it does, decode, if it doesn't just use ' '
                        comment = trial_obj.attrs.get('comment',default=None)
                        data['Plot File'].append('=HYPERLINK("{}","Plot Link")'.format(this_plot_path))
                        if comment:
                            comment = comment.decode('utf-8')
                        else:
                            comment = ' '
                        data['Comments'].append(comment)
                        data['Latency (ms)'].append(latency)
                    elif 'substage_frame_times' in name:
                        videopath = trial_member.attrs.get('path',default=None)
                        if videopath:
                            data['Video File'].append(format_hyperlink(videopath.decode('utf-8')))
                        else:
                            data['Video File'].append(' ')

        
        out_filename = filename.split('.')[0] + '_latencies.csv'
        out = pd.DataFrame(data)
        out.to_csv(out_filename,index=False)
def format_hyperlink(path):
    return '=HYPERLINK("{}","Video Link")'.format(path)

def plot2(data_list, latency, savepath, latency_filepath, mouse, trial):
    fig, ax = plt.subplots(2,1, sharex=True)
    ax[0].plot(data_list[0], c='b')
    ax[1].plot(data_list[1], c='r')
    ax[1].axvline(latency + 2000, linestyle='--', c='k')
    ax[0].set_ylabel('Blue LED Voltage (V)')
    ax[1].set_ylabel('Red LED Voltage (V)')
    ax[1].set_xlabel('Time (ms)')
    path = savepath / (str(mouse) + str(trial) + '.png')
    plt.savefig(path, dpi=300, facecolor='white')
    plt.close()
    path = savepath.relative_to(latency_filepath) / (str(mouse) + str(trial) + '.png')
    rel_path = './' + str(path.as_posix())
    return rel_path

def plot3(data_list, latency, savepath, latency_filepath, mouse, trial):
    fig, ax = plt.subplots(3,1, sharex=True)
    ax[0].plot(data_list[0], c='g')
    ax[1].plot(data_list[1], c='gray')
    ax[2].plot(data_list[2], c='r')
    ax[2].axvline(latency + 2000, linestyle='--', c='k')
    ax[0].set_ylabel('Green LED Voltage (V)')
    ax[1].set_ylabel('IR Laser Voltage (V)')
    ax[2].set_ylabel('Red LED Voltage (V)')
    ax[2].set_xlabel('Time (ms)')
    path = savepath / (str(mouse) + str(trial) + '.png')
    plt.savefig(path, dpi=300, facecolor='white')
    plt.close()
    path = savepath.relative_to(latency_filepath) / (str(mouse) + str(trial) + '.png')
    rel_path = './' + str(path.as_posix())
    return rel_path


class latency_plot:
    def __init__(self, t, lat, blue, red, title):
        self.scroll_scaling = 0.6
        self.fig, self.ax = plt.subplots(2,1, sharex=True)
        self.ax[0].plot(t,blue,c='royalblue',linewidth=2)
        self.ax[1].plot(t,red,c='crimson')
        self.ax[1].set_xlabel('Latency (ms)')
        self.home_limits = self.ax[0].get_xlim()
        self.current_limits = self.home_limits
        self.fig.suptitle(title)
        sid = self.ax[0].get_figure().canvas.mpl_connect("key_press_event", self.next)
        self.ax[0].get_figure().canvas.mpl_connect("scroll_event", self.on_scroll)
        self.ax[0].get_figure().canvas.mpl_connect("motion_notify_event", self.on_move)
        self.Cline = click_line(self.ax[1], x=lat)
        manager = plt.get_current_fig_manager()
        manager.window.state('zoomed')
        plt.show()
    
    def next(self, event):
        if event.key == ' ':
            self.should_save = True
            plt.close()
        elif event.key == 'x':
            self.should_save = False
            plt.close()
    
    def on_scroll(self, event):
        print("Scrolled")
        increment = 1 - self.scroll_scaling if event.button == 'up' else 1 + self.scroll_scaling
        distance = self.current_limits[1] - self.current_limits[0]
        new_xmin = self.x_cursor - distance/2*increment
        new_xmax = self.x_cursor + distance/2*increment
        self.current_limits = (new_xmin, new_xmax)
        self.ax[0].set_xlim(new_xmin, new_xmax)
        self.ax[0].get_figure().canvas.draw_idle()
    
    def on_move(self, event):
        if event.inaxes:
            self.x_cursor = event.xdata
            self.y_cursor = event.ydata
            print(self.x_cursor, self.y_cursor)

class click_line():
    def __init__(self, ax, x = 0):
        self.line = ax.axvline(x, linestyle='--',c='k')
        self.canvas = ax.get_figure().canvas
        self.canvas.draw_idle()
        self.sid = self.canvas.mpl_connect("button_press_event", self.click)
        self.position = x
        if np.isnan(self.position):
            self.text = ax.text(0.05,0.05, 'N/A',weight='bold', fontsize='xx-large')
        else:
            self.text = ax.text(0.05,0.05,str(int(self.position)),weight='bold', fontsize='xx-large') #transform= ax.transAxes
        # print(ax.figure.canvas.mpl_connect("button_press_event", self.click))
    
    def click(self, event):
        print(event.xdata)
        self.position = event.xdata
        self.line.set_xdata(event.xdata)
        self.text.set_position((event.xdata,event.ydata))
        self.text.set_text(str(int(event.xdata)))
        self.canvas.draw_idle()

if __name__ == '__main__':
    extract_latencies()