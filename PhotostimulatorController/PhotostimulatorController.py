import numpy as np
import time


class PhotostimulatorController:
    # assume a sampling rate of 1000 Hz
    SAMPLING_RATE = 1000 # Hz

    # valid operating values
    VALID_VOLTAGE_LOW = 0
    VALID_VOLTAGE_HIGH = 5

    # blue light padding (2s, assuming 1000Hz sampling rate)
    BLUE_PAD_LENGTH = 2000

    def __init__(self):
        self.plot_top_data = np.full(1,np.nan)
        self.plot_mid_data = np.full(1,np.nan)
        self.plot_bot_data = np.full(1,np.nan)
        self.latency = np.nan
        self.ylim = False
        self.xlim = False

    def reset_lim(self):
        self.ylim = False

    # get valid waveform lengths in ms
    # valid lengths: 1s to 30s ramp
    # valid lengths: 10ms to 1000ms pulse
    def get_valid_lengths(self, wavetype):
        valid_low = 10
        valid_high = 30000

        if wavetype == "Ramp":
            valid_low = 1000
        elif wavetype == "Pulse":
            valid_high = 10000

        return valid_low, valid_high

    # validate args
    # exceptions: on validation
    def validate_ramp(self, blue_length, blue_voltage, red_voltage):
        if blue_voltage >= 0 and red_voltage > 0 and blue_length > 0:
            return True

        raise Exception('Invalid length and/or voltage. Must be > 0s and > 0V')

    def validate_pulse(self, blue_length, blue_voltage, red_voltage):
        if blue_voltage > 0 and red_voltage > 0 and blue_length > 0:
            return True

        raise Exception('Invalid length and/or voltage. Must be > 0s and > 0V')
    
    def set_conversion(self,func):
        self.to_mW = func
    
    def blue_to_mW(self,V):
        if "to_mW" in dir(self):
            return self.to_mW(V)
        else:
            raise Exception("Converion not available")

    # send/receive red and blue light waveforms, where blue light is a ramp
    # total length = length + 2(0.5 s)
    # red light will last 0.5 s before and after blue light is
    def ramp_redblue(self, blue_length, blue_voltage, blue_threshold, red_voltage, hsv_params={}):
        # validate args
        self.validate_ramp(blue_length, blue_voltage, red_voltage)

        # each element is 1 ms (i.e. sample at 1000 Hz)
        red = np.full(int(blue_length) + (PhotostimulatorController.BLUE_PAD_LENGTH * 2), red_voltage, dtype=np.float16)
        red[0] = 0
        red[-1] = 0

        blue = np.zeros(1, dtype=np.float16)
        blue = np.pad(blue, (0, int(blue_length)), 'linear_ramp', end_values=(0, blue_voltage))
        blue = np.pad(blue, (PhotostimulatorController.BLUE_PAD_LENGTH - 1, PhotostimulatorController.BLUE_PAD_LENGTH), 'constant')
        
        self.ylim = blue_voltage
        self.xlim = len(blue)
        self.plot_top_data = np.full(blue.shape[0],np.nan)
        self.plot_bot_data = np.full(red.shape[0],np.nan)
        step = 100
        for t in range(0,len(blue),step):
            self.plot_top_data[t:t+step] = blue[t:t+step]
            self.plot_bot_data[t:t+step] = red[t:t+step]
            time.sleep(0.1)

        return blue, red

    # send/receive red and blue light waveforms, where blue light is a pulse
    # total length = length + 2(0.5 s)
    # red light will last 0.5 s before and after blue light is on
    def pulse_redblue(self, blue_length, blue_voltage, blue_threshold, red_voltage, hsv_params = {}):
        # validate args
        self.validate_pulse(blue_length, blue_voltage, red_voltage)

        # each element is 1 ms (i.e. sample at 1000 Hz)
        red = np.full(int(blue_length) + (PhotostimulatorController.BLUE_PAD_LENGTH * 2), red_voltage, dtype=np.float16)
        red[0] = 0
        red[-1] = 0

        blue = np.full(int(blue_length), blue_voltage, dtype=np.float16)
        blue = np.pad(blue, (PhotostimulatorController.BLUE_PAD_LENGTH, PhotostimulatorController.BLUE_PAD_LENGTH), 'constant')

        time.sleep(blue.shape[0] / 1000.0)

        return blue, red

    def pulsetrain_redblue(self, length, voltage, freq, num, thresh, red, hasv_params={}):
        #Get period in ms
        period = int(1000*1/freq)
        blue = np.zeros(num*period,dtype=np.float16)
        for n in range(num):
            ind = int(n*period)
            blue[ind:ind + int(length)] = voltage
        blue = np.pad(blue, (PhotostimulatorController.BLUE_PAD_LENGTH, PhotostimulatorController.BLUE_PAD_LENGTH), 'constant')
        red = np.full(blue.size, red, dtype=np.float16)

        self.ylim = self.blue_to_mW(voltage)*1.2
        self.xlim = len(blue)
        self.plot_top_data = self.blue_to_mW(np.full(blue.shape[0],np.nan))
        self.plot_bot_data = np.full(red.shape[0],np.nan)
        step = 100
        for t in range(0,len(blue),step):
            self.plot_top_data[t:t+step] = self.blue_to_mW(blue[t:t+step])
            self.plot_bot_data[t:t+step] = red[t:t+step]
            time.sleep(0.1)

        return self.to_mW(blue), red

    def pulse_redgreenlaser(self, green_length, green_voltage, laser_voltage, red_threshold, red_voltage):
        # each element is 1 ms (i.e. sample at 1000 Hz)
        red = np.full(int(green_length) + (PhotostimulatorController.BLUE_PAD_LENGTH * 2), red_voltage, dtype=np.int16)
        red[0] = 0
        red[-1] = 0

        green = np.full(int(green_length), green_voltage, dtype=np.int16)
        green = np.pad(green, (PhotostimulatorController.BLUE_PAD_LENGTH, PhotostimulatorController.BLUE_PAD_LENGTH), 'constant')

        laser = np.full(int(green_length), laser_voltage, dtype=np.int16)
        laser = np.pad(laser, (PhotostimulatorController.BLUE_PAD_LENGTH, PhotostimulatorController.BLUE_PAD_LENGTH), 'constant')

        # data array contains both red and blue array, starting with red
        data = np.zeros(red.size + green.size + laser.size, dtype=np.int16)
        data[0::3] = red
        data[1::3] = green
        data[2::3] = laser

        self.ylim = green_voltage if green_voltage > laser_voltage else laser_voltage
        self.xlim = len(laser)
        self.plot_top_data = np.full(laser.shape[0],np.nan)
        self.plot_bot_data = np.full(red.shape[0],np.nan)
        self.plot_mid_data = np.full(red.shape[0],np.nan)

        step = 100
        for t in range(0,len(red),step):
            self.plot_top_data = laser[t:t+step]
            self.plot_bot_data = red[t:t+step]
            self.plot_mid_data = green[t:t+step]
            time.sleep(0.1)

        receive_red = red
        receive_green = green
        receive_laser = laser


        self.plot_top_data = receive_green
        self.plot_bot_data = receive_red
        self.plot_mid_data = laser

        return receive_green, receive_laser, receive_red
    
    def set_DAC1(self,V):
        pass

    def __del__(self):
        pass
