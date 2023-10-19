import tkinter as tk
import tkinter.ttk as ttk


# TODO: define differences between builds
class ChooseBuildDialog(tk.Toplevel):
    BUILDS_LIST = ['Debug', 'Release']

    def __init__(self, master=None):
        super().__init__(master=master)
        self.title('Choose Build')
        self.geometry("240x100")

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, padx=10, pady=10)

        build_label = ttk.Label(frame, text="Build Type:")
        build_label.grid(row=0, column=0)

        self.__build_var = tk.StringVar()

        build_combobox = ttk.Combobox(frame, textvariable=self.__build_var)
        build_combobox['values'] = ChooseBuildDialog.BUILDS_LIST
        build_combobox.set(ChooseBuildDialog.BUILDS_LIST[0])
        build_combobox['state'] = 'readonly'
        build_combobox.grid(row=0, column=1)

        ok_button = ttk.Button(frame, text='OK', command=self.ok_button_event)
        ok_button.grid(row=1, columnspan=2, pady=20, sticky='se')

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
        # block until window is destroyed
        self.wait_window()

    @staticmethod
    def disable_event():
        pass

    def get_build(self):
        return self.__build_var.get()

    def ok_button_event(self):
        self.grab_release()
        self.destroy()


class BuildProgressWindow(tk.Toplevel):
    def __init__(self, master=None):
        super().__init__(master=master)
        self.title('Loading Build...')
        self.geometry("220x80")

        frame = ttk.Frame(self)
        frame.grid(row=0, column=0, padx=10, pady=10)

        loading_label = ttk.Label(frame, text='Loading...')
        loading_label.grid(row=0, column=0)

        self.__progressbar = ttk.Progressbar(frame, orient='horizontal', mode='determinate', length=200)
        self.__progressbar.grid(row=1, column=0)

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

    def progress(self, value):
        if self.__progressbar['value'] < 100:
            self.__progressbar['value'] += value
