import tkinter as tk
import tkinter.ttk as ttk


class ConnectionManagerWindow(tk.Toplevel):
    def __init__(self, fine_motors, coarse_motor, camera, master=None):
        super().__init__(master=master)
        self.title('Connection Manager')
        self.geometry("640x200")

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, padx=10, pady=10)

        columns = ('Device', 'Connected', 'Port')
        self.__tree = ttk.Treeview(frame, columns=columns, height=len(columns), selectmode='browse', show='headings')
        for column in columns:
            self.__tree.heading(column, text=column)
        self.__tree.grid(row=0, column=0)

        devices = []
        fine_motors_port = ''
        coarse_motors_port = ''
        if fine_motors is not None:
            fine_motors_port = fine_motors.my_interface._serial.name
        if coarse_motor is not None:
            coarse_motors_port = coarse_motor.my_interface._serial.name
        
        devices.append(('Fine motors', str(fine_motors is not None), fine_motors_port))
        devices.append(('Coarse motors', str(coarse_motor is not None), coarse_motors_port))
        devices.append(('Camera', str(camera is not None), ''))

        for device in devices:
            self.__tree.insert('', tk.END, values=device)

        configure_button = ttk.Button(frame, text='Configure Device...', command=self.configure_button_event)
        # TODO: implement
        configure_button['state'] = 'disabled'
        configure_button.grid(row=1, column=0, sticky='se')

    # TODO: implement
    def configure_button_event(self):
        selected_item = self.__tree.selection()
        if selected_item:
            item = self.__tree.item(selected_item)
            values = item['values']

            device = values[0]
            connected = values[1]
            port = values[2]