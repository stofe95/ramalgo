import tkinter as tk
import tkinter.ttk as ttk
import numpy as np
import pickle
from datetime import datetime
import matplotlib.pyplot as plt
from glob import glob
import pandas as pd

class CalibrationWindow(tk.Toplevel):
    def __init__(self, master=None, photostimulator=None, calibration_path='./../.calibration_data/'):
        super().__init__(master=master)
        self.calibration_path = calibration_path
        self.photostimulator = photostimulator
        self.title("Blue Light Calibration")
        self.geometry("540x500")

        calibration_frame = ttk.Frame(self,height=540,width=500)
        calibration_frame.grid()

        
        table_frame = ttk.Frame(calibration_frame)
        table_frame.grid(rowspan=2,columnspan=4,sticky='n')
        self.tv1 = ttk.Treeview(table_frame,height=15,columns=('voltage', 'power'),show='headings')
        self.tv1.heading('voltage', text = 'Voltage (V)')
        self.tv1.heading('power', text = 'Power (mW)')
        self.tv1.grid()

        treescrolly = tk.Scrollbar(table_frame, orient="vertical", command=self.tv1.yview) # command means update the yaxis view of the widget
        treescrollx = tk.Scrollbar(table_frame, orient="horizontal", command=self.tv1.xview) # command means update the xaxis view of the widget
        self.tv1.configure(xscrollcommand=treescrollx.set, yscrollcommand=treescrolly.set) # assign the scrollbars to the Treeview Widget
        treescrollx.grid(row=1, column=0, columnspan=2,sticky='ews')
        treescrolly.grid(row=0,column=1,sticky='nse')

        # data
        self.calibration_data = {
            'Voltage': [],
            'Power' : []
        }

        voltage_frame = ttk.Frame(calibration_frame)
        voltage_frame.grid(row=6, column=0, pady=10, sticky='ne')

        voltage_label = ttk.Label(voltage_frame, text='Voltage (V)')
        voltage_label.grid(row=0, column=0, pady=10, sticky='ne')

        self.voltage_var = tk.DoubleVar()
        voltage_spinbox = tk.Spinbox(voltage_frame, from_=0, to=5, increment=0.01, textvariable=self.voltage_var)
        voltage_spinbox.grid(row=0,column=1,padx=1,pady = 10, sticky='ne')

        power_frame = ttk.Frame(calibration_frame)
        power_frame.grid(row=6, column = 3, pady = 10, sticky='nw')

        power_label = ttk.Label(power_frame, text='Power (mW)')
        power_label.grid(row=6, column=2, pady = 10, sticky='n')

        self.power_var = tk.DoubleVar()
        power_spinbox = tk.Spinbox(power_frame, from_=0, to=5, increment=0.01, textvariable=self.power_var)
        power_spinbox.grid(row=6,column=3,padx=1,pady = 10)

        set_V_button = tk.Button(calibration_frame, text='Set Blue Output',command = self.set_dac)
        set_V_button.grid(row=7,column=0, pady = 2)

        set_V_button = tk.Button(calibration_frame, text='Record Blue Power',command = self.get_power)
        set_V_button.grid(row=7,column=3, pady = 2)

        save_button = tk.Button(calibration_frame, text='Save Calibration Data',command=self.save)
        save_button.grid(row=8,column=2, pady = 10, sticky='n')
        
    def get_power(self):
        P = self.power_var.get()
        V = self.V
        self.calibration_data['Voltage'].append(V)
        self.calibration_data['Power'].append(P)
        self.add_data(V,P)
    
    def set_dac(self):
        self.V = self.voltage_var.get()
        if self.photostimulator:
            self.photostimulator.set_DAC1(self.V)
    
    def add_data(self, V, P):
        self.tv1.insert('',tk.END, values=(str(V),str(P)))
    
    def save(self):
        self.V = 0
        self.set_dac()
        a, b = np.polyfit(self.calibration_data['Voltage'], self.calibration_data['Power'],deg=1)
        fn = datetime.today().strftime('%Y-%m-%d_1')
        path = self.calibration_path
        num = 1
        while True:
            if glob(path + fn + '*'):
                num += 1
                ind = fn.index('_') + 1
                fn = fn[:ind] + str(num)
            else:
                break

        plt.scatter(self.calibration_data['Voltage'],self.calibration_data['Power'],c='b',edgecolors='k')
        x = np.linspace(0,self.calibration_data['Voltage'][-1],100)
        y = a*x + b
        plt.plot(x,y,c='k',linestyle='--')
        plt.xlabel('Voltage (V)')
        plt.ylabel('Power (mW)')
        plt.savefig(path + fn + '.png',facecolor='white',dpi=300)
        plt.close()
        out = pd.DataFrame(self.calibration_data)
        out.to_csv(path + fn + '.csv',index=False)
        with open(path + fn + '.pickle', 'wb') as handle:
            pickle.dump((a,b), handle, protocol=pickle.HIGHEST_PROTOCOL)
        self.photostimulator.load_calibration()
        self.photostimulator.show_redblue_settings()
        self.photostimulator.set_valid_voltages()
        self.destroy()


if __name__ == '__main__':
    root = tk.Tk()
    root.title('Calibration Window')
    root.geometry("540x500")
    window = CalibrationWindow(root)

    root.mainloop()