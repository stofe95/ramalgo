from PhotostimulatorController.PhotostimulatorController import *
from DebugLog.DebugLog import *

import importlib.util
from time import perf_counter
import matplotlib.pyplot as plt

# CED1401 error-handling
class CED1401Exception:
    # terminate communications
    @staticmethod
    def Terminate(u14):
        u14.Close()

    # u14.GetError() -> error [code, text]
    @staticmethod
    def Open_Error(u14):
        error = u14.GetError()
        CED1401Exception.Terminate(u14)
        raise Exception('Failed to open the 1401: ', error)

    @staticmethod
    def Load_Error(u14):
        error = u14.GetError()
        CED1401Exception.Terminate(u14)
        raise Exception('Failed to load commands: ', error)

    @staticmethod
    def Clear_Error(u14):
        error = u14.GetError()
        raise Exception('Failed to clear: ', error)

    @staticmethod
    def To1401_Error(u14):
        error = u14.GetError()
        raise Exception('Failed to store waveform array: ', error)

    @staticmethod
    def ToHost_Error(u14):
        error = u14.GetError()
        raise Exception('Failed to read waveform array: ', error)

    @staticmethod
    def MEMDAC_Error(u14):
        error = u14.GetError()
        # kill command
        u14.Write('memdac,k;')
        raise Exception('Failed to launch waveform array: ', error)

    @staticmethod
    def ADCMEM_Error(u14):
        error = u14.GetError()
        # kill command
        u14.Write('adcmem,k;')
        raise Exception('Failed to sample ADC channels: ', error)

    @staticmethod
    def ReadInts_Error(u14):
        error = u14.GetError()
        raise Exception('Failed to read bytes: ', error)
    
    @staticmethod
    def Write_Error(u14):
        error = u14.GetError()
        raise Exception('Failed to Write command: ', error)

class BlueLightTerminator:
    WINDOW_SIZE = 1000
    CROSS_TIME = 20

    def __init__(self, threshold):
        self.__data = []
        self.__threshold = threshold
        self.__average = 0
        self.__cross_count = 0
        self.__current_index = 0
        self.__candidate = np.nan

        self.__terminate = False
        self.__terminated = False

    def terminate(self):
        self.__terminated = self.__terminate
        return self.__terminate

    def did_terminate(self):
        return self.__terminated

    def update(self, value):
        self.__average += value
        self.__data.append(value)

        # calculate if the last value dropped below threshold:
        # value < threshold * (average / window_size)
        if len(self.__data) == BlueLightTerminator.WINDOW_SIZE:
            if value < self.__threshold * self.__average / BlueLightTerminator.WINDOW_SIZE:
                if self.__cross_count == 0:
                    self.__candidate = self.__current_index
                # drop must last for cross_time to terminate light
                self.__cross_count += 1
                if self.__cross_count == BlueLightTerminator.CROSS_TIME:
                    self.__terminate = True
            else:
                self.__cross_count = 0
                self.__candidate = np.nan


            self.__average -= self.__data.pop(0)
        self.__current_index += 1
    
    def return_latency(self):
        return self.__candidate


# micro4: 16-bit ADC and DACs, -5V to 4.9998V w 0.153 mV steps, 1Mhz ADC sampling rate
# port 0: red
# port 1: blue
class CED1401(PhotostimulatorController):
    # command syntax
    CMD_ADCMEM = 'adcmem'
    CMD_MEMDAC = 'memdac'
    CMD_DIGTIM = 'DIGTIM'
    CMD_CLEAR = 'clear'
    CMD_ARG_SEPARATOR = ','
    CMD_TERMINATOR = ';'

    # valid operating values
    VALID_VOLTAGE_LOW = 0
    VALID_VOLTAGE_HIGH = 4.9998

    # blue light padding (2s, assuming 1000Hz sampling rate)
    BLUE_PAD_LENGTH = 2000


    # exceptions: on CED1401 error
    def __init__(self):
        super().__init__()

        # import py1401 module
        spec = importlib.util.spec_from_file_location("py1401", "C:\\1401\\LangSup\\Python\\bin\\x64\\3.8\\py1401.pyd")
        py1401 = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(py1401)

        # make instance to talk to a 1401
        self.__u14 = py1401.Create()

        # establish connection
        if not self.__u14.Open():
            CED1401Exception.Open_Error(self.__u14)

        commands = [CED1401.CMD_ADCMEM, CED1401.CMD_MEMDAC, CED1401.CMD_CLEAR, CED1401.CMD_DIGTIM]
        commands = CED1401.CMD_ARG_SEPARATOR.join(commands)
        # returns [0,0] on success, [error,index] on failure
        if self.__u14.Load(commands, 'c:/1401')[0] != 0:
            CED1401Exception.Load_Error(self.__u14)

        controller_info = self.__u14.Info()
        if 'Micro1401-4' in controller_info:
            DebugLog.debugprint(self, 'Connected to: Micro1401-4 ')
            self.voltage_range = 5.0
        else:
            self.voltage_range = 10.0
            DebugLog.debugprint(self, 'Connected to: ' + controller_info[1] + ' adjusting output to 10V max range.')

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

    # valid voltages: 0V to 4.9998V
    # valid lengths: 1s to 30s ramp
    # exceptions: on validation
    def validate_ramp_redblue(self, blue_length, blue_voltage, red_voltage):
        if 0 < blue_voltage <= 4.9998 and 0 < red_voltage <= 4.9998 and 1000 <= blue_length <= 30000:
            return True

        raise Exception('Invalid length and/or voltage. Must be from 1s to 30s and 0V to 4.9998V')

    # valid voltages: 0V to 4.9998V
    # valid lengths: 10ms to 1000ms pulse
    # exceptions: on validation
    def validate_pulse_redblue(self, blue_length, blue_voltage, red_voltage):
        if 0 < blue_voltage <= 4.9998 and 0 < red_voltage <= 4.9998 and 10 <= blue_length <= 10000:
            return True

        raise Exception('Invalid length and/or voltage. Must be from 10ms to 1000ms and 0V to 4.9998V')
    
    def validate_pulsetrain_redblue(self, length, blue_voltage, red_voltage, freq, num):
        if 0 <= blue_voltage <= 5 and 0 <= red_voltage <= 5 and 1 <= length and 1 <= num <= 100 and 0.1 <= freq <= 10:
            period = int(1000/freq)
            if length > period:
                raise Exception('Invalid length. Pulse train length cannot exceed its period (1/freq = {})'.format(period))
            else:
                return True
        raise Exception('Invalid power. Must be within power limit')

    # valid voltages: 0V to 4.9998V
    # valid lengths: 1s to 20s pulse
    # exceptions: on validation
    def validate_pulse_redgreenlaser(self, green_length, green_voltage, laser_voltage, red_voltage):
        if 0 <= green_voltage <= 4.9998 and 0 <= laser_voltage <= 4.9998 and 0 < red_voltage <= 4.9998 and 1000 <= green_length <= 20000:
            return True

        raise Exception('Invalid length and/or voltage. Must be from 1s to 20s and 0V to 4.9998V')

    # convert the voltage to the 1401 linear mapping (e.g. -/+5.0V is represented by -/+2^15)
    def map_voltage_to_1401(self, voltage):
        return int(voltage / self.voltage_range * (2.0**15))

    # convert the data array from the 1401 linear mapping (e.g. -/+5.0V is represented by -/+2^15)
    def map_data_from_1401(self, arr):
        return arr / (2.0**15) * self.voltage_range

    # formulate waveform command 'adcmem' or 'memdac'
    # "[memdac,adcmem],[i,f],[byte],[byte address of start of data array],[num bytes in array(2*datapoints)],[channel list],[num times to cycle array],[clock source],[pre],[cnt];"
    def waveform_command(self, cmd, num_channels, start_adr, size_arr):
        kind = 'i'              # interrupt-mode
        byte = 2                # 2 = 16-bit data
        channels = '0'          # 0: red
        # TODO: can't sample 3 channels at 1000 Hz accurately (1 Mhz not divisible by 3000 Hz)
        if num_channels == 2:
            channels += ' 1'    # 1: blue
        elif num_channels == 3:
            channels += ' 1 2'  # 1: green, 2: laser
        rpt = 1                 # transmit 1 time (if rpt=0, essentially running inf)
        clock = 'c'             # 'c' = internal 1 Mhz clock
        # pre*cnt sets the clock divide down from source
        # memdac: transmit rate 1000 Hz: 1000 Hz = 1 Mhz / 10 / 100
        # adcmem: sample rate 2000 Hz (1000Hz per channel): 2000 Hz = 1 Mhz / 5 / 100
        pre = 10
        if cmd == CED1401.CMD_ADCMEM:
            pre = 5
        cnt = 100

        command = []
        command.append(cmd)
        command.append(kind)
        command.append(str(byte))
        command.append(str(start_adr))
        command.append(str(2 * size_arr))
        command.append(channels)
        command.append(str(rpt))
        command.append(clock)
        command.append(str(pre))
        command.append(str(cnt))

        return CED1401.CMD_ARG_SEPARATOR.join(command) + CED1401.CMD_TERMINATOR
    
    def digps_command(self,rate):
        return 'DIG,O,1'

    # formulate waveform command 'memdac'
    def cmd_memdac(self, num_channels, start_adr, size_arr):
        command = self.waveform_command(CED1401.CMD_MEMDAC, num_channels, start_adr, size_arr)
        self.highspeed=False
        if self.highspeed:
            command = command
        return command

    # formulate waveform command 'adcmem'
    def cmd_adcmem(self, num_channels, start_adr, size_arr):
        return self.waveform_command(CED1401.CMD_ADCMEM, num_channels, start_adr, size_arr)
    
    def cmd_trigger_hsv(self, FPS, length, memstart, memsize):
        #Clock rate will be 8 kHz to allow 4000 FPS video, where 1 clock tick would be on, one clock tick would be off
        preset1 = 5
        preset2 = 25
        clock_rate = 1000000 / (preset1 * preset2)
        repeats = int(FPS * length)
        period = int(clock_rate / FPS)
        onticks = int(period / 2)
        offticks = period - onticks
        cmd = "".join(
            "DIGTIM,SD,{},{};".format(memstart,memsize) +
            "DIGTIM,A,1,1,{};".format(onticks) + 
            "DIGTIM,A,1,0,{};".format(offticks) + 
            "DIGTIM,C,{},{},{};".format(preset1,preset2,repeats))
        return cmd
        
    # transmit and receive red and blue signals
    # exceptions: on validation, CED1401 errors
    # returns: blue, red received signals
    def execute(self, num_channels, data, blue_threshold, hsv_params = {}):
        # stop any 1401 activity
        if not self.__u14.Write('clear;'):
            CED1401Exception.Clear_Error(self.__u14)

        # check size of user memory, in bytes
        points = 2 * data.size
        info = self.__u14.Info()
        usermem_size = info[2]
        if points > usermem_size / 2:
            raise Exception('Waveform is too big. Limit(bytes) = %d, waveform(bytes) = %d', (usermem_size / 2, points))

        # waveform addr: 0
        # sampling addr: points

        # send waveform to memory
        if not self.__u14.To1401(data, 0):
            CED1401Exception.To1401_Error(self.__u14)

        # confirm waveform in memory
        read = np.zeros(data.size, dtype=np.int16)
        if not self.__u14.ToHost(read, 0):
            CED1401Exception.ToHost_Error(self.__u14)
        if not (read == data).all():
            raise Exception('Memory does not match written data. Memory = ' + str(read) + ' data = ' + str(data))

        # # execute waveform
        # if not self.__u14.Write(self.cmd_memdac(num_channels,0, data.size)):
        #     CED1401Exception.MEMDAC_Error(self.__u14)

        # TODO: can't sample 3 channels at 1000 Hz accurately (1 Mhz not divisible by 3000 Hz)
        # sample input channels
        read_size = data.size
        read_channels = num_channels
        if num_channels == 3:
            read_channels = 2
            read_size = int(data.size / 3 * 2)
        # if not self.__u14.Write(self.cmd_adcmem(read_channels, points, read_size)):
        #     CED1401Exception.ADCMEM_Error(self.__u14)

        if hsv_params:
            hsv_cmd = self.cmd_trigger_hsv(hsv_params['FPS'], hsv_params['length'], 2*points, 32)
        else:
            hsv_cmd = ""
        print(hsv_cmd)
        # execute waveform
        if not self.__u14.Write(
            'CLEAR;' + 
            self.cmd_memdac(num_channels,0, data.size) + 
            self.cmd_adcmem(read_channels, points, read_size) + 
            hsv_cmd):
            CED1401Exception.MEMDAC_Error(self.__u14)

        # determine when to terminate blue light
        blue_terminator = BlueLightTerminator(blue_threshold)
        prev = np.zeros(1, dtype=np.int16)

        n = 0
        idx = 0
        while n < points - 2:        
            print() 
            # "adcmem,p": returns byte address (relative to start) of next byte to be updated
            self.__u14.Write('adcmem,p;')
            # read response
            pos = self.__u14.ReadInts()
            if not pos:
                CED1401Exception.ReadInts_Error(self.__u14)
            n = pos[0]
            # next byte is ready
            if (n > idx) and ((n/2)%2 == 0): #pos will contain either red or blue interleaved sampled data. Only update blue terminator if the sampled data is red (the first leaf)
                idx = n
                self.__u14.ToHost(prev, points + idx - 4) # inx & n are the NEXT byte to be updated, but we don't know if they have been yet. Instead, include - 4 to read the previous byte to the next one (which we know will be updated)
                # calculate if termination condition was reached
                blue_terminator.update(prev[0])
                self.plot_bot_data[int(n/4)] = self.map_data_from_1401(prev[0])
            
            elif (n > idx) and ((n/2)%2 == 1):
                idx = n
                self.__u14.ToHost(prev, points + idx - 4)
                self.plot_top_data[int(n/4)] = self.blue_to_mW(self.map_data_from_1401(prev[0]))
                if num_channels == 3:
                    self.plot_mid_data[int(n/4)] = self.map_data_from_1401(prev[0])

            elif n == 0 and idx > 0:
                break

            # terminate blue light
            if not blue_terminator.did_terminate() and (blue_terminator.terminate() and n < points - 2):
                DebugLog.debugprint(self, "Withdrawal detected. Terminating stimulus...")

                # kill the remaining waveform, leave red light on for rest of duration
                self.__u14.Write('memdac,k;')
                self.__u14.Write('DAC,0,0;') # DAC,0 1,0 0
                self.__u14.Write('DAC,1,0;') # DAC,0 1,1 0
                self.__u14.Write('DAC,2,0;') # DAC,0 1,1 0              

        # ensure all lights are turned off
        self.__u14.Write('DAC,0,0;') # DAC,0 1,0 0

        # read sampled input
        read = np.zeros(read_size, dtype=np.int16)
        if not self.__u14.ToHost(read, points):
            CED1401Exception.ToHost_Error(self.__u14)

        # 1401 maps the maximum -/+ 5V from -/+ 2^15, scale voltages accordingly
        read = self.map_data_from_1401(read.astype('float16'))

        # TODO: can't sample 3 channels at 1000 Hz accurately (1 Mhz not divisible by 3000 Hz)
        # read array contains interleaved data, starting with red
        # red/blue: data = [red, blue, red, blue, ...]
        # red/green/laser: data = [red, green, laser, red, green, laser, ...]
        receive = []
        #for i in range(num_channels):
            #receive.append(read[i::num_channels])
        for i in range(read_channels):
            receive.append(read[i::read_channels])

        DebugLog.debugprint(self, "Waveform execution completed.")
        print(
            self.cmd_memdac(num_channels,0, data.size) + 
            self.cmd_adcmem(read_channels, points, read_size) + 
            hsv_cmd)

        return receive

     # send/receive red and blue light waveforms, where blue light is a ramp
    # length: ms, voltage: V
    # total length = length + 2(0.5 s)
    # red light will last 0.5 s before and after blue light is on
    # exceptions: on validation, CED1401 errors
    # returns: blue, red received signals
    def ramp_redblue(self, blue_length, blue_voltage, red_threshold, red_voltage, hsv_params={}):
        # validate args
        self.validate_ramp_redblue(blue_length, blue_voltage, red_voltage)
        bv = blue_voltage
        DebugLog.debugprint(self, "Validation completed.")

        # 1401 maps the maximum -/+ 5V from -/+ 2^15, scale voltages accordingly
        red_voltage = self.map_voltage_to_1401(red_voltage)
        blue_voltage = self.map_voltage_to_1401(blue_voltage)

        # each element is 1 ms (i.e. sample at 1000 Hz)
        red = np.full(int(blue_length) + (CED1401.BLUE_PAD_LENGTH * 2), red_voltage, dtype=np.int16)
        blue = np.zeros(1, dtype=np.int16)
        blue = np.pad(blue, (0, int(blue_length)), 'linear_ramp', end_values=(0, blue_voltage))
        blue = np.pad(blue, (CED1401.BLUE_PAD_LENGTH - 1, CED1401.BLUE_PAD_LENGTH), 'constant')

        # data array contains both red and blue array, starting with red
        data = np.zeros(red.size + blue.size, dtype=np.int16)
        data[0::2] = red
        data[1::2] = blue
        
        self.ylim = bv
        self.xlim = len(blue)
        self.plot_top_data = np.full(blue.shape[0],np.nan)
        self.plot_bot_data = np.full(red.shape[0],np.nan)

        DebugLog.debugprint(self, "Waveform data array completed.")

        receive = self.execute(2, data, red_threshold, hsv_params)
        receive_red = receive[0]
        receive_blue = receive[1]

        self.plot_top_data = receive_blue
        self.plot_bot_data = receive_red

        return receive_blue, receive_red

    # send/receive red and blue light waveforms, where blue light is a pulse
    # length: ms, voltage: V
    # total length = length + 2(0.5 s)
    # red light will last 0.5 s before and after blue light is on
    # exceptions: on validation, CED1401 errors
    # returns: blue, red received signals
    def pulse_redblue(self, blue_length, blue_voltage, red_threshold, red_voltage, hsv_params = {}):
        # validate args
        self.validate_pulse_redblue(blue_length, blue_voltage, red_voltage)
        bv = blue_voltage

        DebugLog.debugprint(self, "Validation completed.")

        # 1401 maps the maximum -/+ 5V from -/+ 2^15, scale voltages accordingly
        red_voltage = self.map_voltage_to_1401(red_voltage)
        blue_voltage = self.map_voltage_to_1401(blue_voltage)

        # each element is 1 ms (i.e. sample at 1000 Hz)
        red = np.full(int(blue_length) + (CED1401.BLUE_PAD_LENGTH * 2), red_voltage, dtype=np.int16)

        blue = np.full(int(blue_length), blue_voltage, dtype=np.int16)
        blue = np.pad(blue, (CED1401.BLUE_PAD_LENGTH, CED1401.BLUE_PAD_LENGTH), 'constant')

        # data array contains both red and blue array, starting with red
        data = np.zeros(red.size + blue.size, dtype=np.int16)
        data[0::2] = red
        data[1::2] = blue

        self.ylim = bv*1.2
        self.xlim = len(blue)
        self.plot_top_data = np.full(blue.shape[0],np.nan)
        self.plot_bot_data = np.full(red.shape[0],np.nan)

        DebugLog.debugprint(self, "Waveform data array completed.")

        receiv = self.execute(2, data, red_threshold, hsv_params)
        receive_red = receiv[0]
        receive_blue = receiv[1]

        self.plot_top_data = receive_blue
        self.plot_bot_data = receive_red

        return receive_blue, receive_red

    def pulsetrain_redblue(self, length, blue_voltage, freq, num, thresh, red_voltage, hsv_params = {}):

        # validate args
        self.validate_pulsetrain_redblue(length, blue_voltage, red_voltage, freq, num)
        bv = blue_voltage

        DebugLog.debugprint(self, "Validation completed.")

        # 1401 maps the maximum -/+ 5V from -/+ 2^15, scale voltages accordingly
        red_voltage = self.map_voltage_to_1401(red_voltage)
        blue_voltage = self.map_voltage_to_1401(blue_voltage)

        #Get period in ms
        period = int(1000*1/freq)
        blue = np.zeros(num*period,dtype=np.float16)
        for n in range(num):
            ind = int(n*period)
            blue[ind:ind + int(length)] = blue_voltage
        blue = np.pad(blue, (PhotostimulatorController.BLUE_PAD_LENGTH, PhotostimulatorController.BLUE_PAD_LENGTH), 'constant')
        red = np.full(blue.size, red_voltage, dtype=np.float16)

        # data array contains both red and blue array, starting with red
        data = np.zeros(red.size + blue.size, dtype=np.int16)
        data[0::2] = red
        data[1::2] = blue

        self.ylim = bv * 1.2
        self.xlim = len(blue)
        self.plot_top_data = np.full(blue.shape[0],np.nan)
        self.plot_bot_data = np.full(red.shape[0],np.nan)

        DebugLog.debugprint(self, "Waveform data array completed.")

        receiv = self.execute(2, data, thresh, hsv_params)
        receive_red = receiv[0]
        receive_blue = receiv[1]

        self.plot_top_data = receive_blue
        self.plot_bot_data = receive_red

        return receive_blue, receive_red

    # send/receive red, green and laser light waveforms, where green light and laser is a pulse
    # length: ms, voltage: V
    # total length = length + 2(0.5 s)
    # red light will last 0.5 s before and after green light and laser is on
    # exceptions: on validation, CED1401 errors
    # returns: green, laser, red received signals
    def pulse_redgreenlaser(self, green_length, green_voltage, laser_voltage, red_threshold, red_voltage):
        gv = green_voltage
        lv = laser_voltage
        # validate args
        self.validate_pulse_redgreenlaser(green_length, green_voltage, laser_voltage, red_voltage)

        DebugLog.debugprint(self, "Validation completed.")

        # 1401 maps the maximum -/+ 5V from -/+ 2^15, scale voltages accordingly
        red_voltage = self.map_voltage_to_1401(red_voltage)
        green_voltage = self.map_voltage_to_1401(green_voltage)
        laser_voltage = self.map_voltage_to_1401(laser_voltage)

        # each element is 1 ms (i.e. sample at 1000 Hz)
        red = np.full(int(green_length) + (CED1401.BLUE_PAD_LENGTH * 2), red_voltage, dtype=np.int16)

        green = np.full(int(green_length), green_voltage, dtype=np.int16)
        green = np.pad(green, (CED1401.BLUE_PAD_LENGTH, CED1401.BLUE_PAD_LENGTH), 'constant')

        laser = np.full(int(green_length), laser_voltage, dtype=np.int16)
        laser = np.pad(laser, (CED1401.BLUE_PAD_LENGTH, CED1401.BLUE_PAD_LENGTH), 'constant')

        # data array contains both red and blue array, starting with red
        data = np.zeros(red.size + green.size + laser.size, dtype=np.int16)
        data[0::3] = red
        data[1::3] = green
        data[2::3] = laser

        self.ylim = gv if gv > lv else lv
        self.xlim = len(laser)
        self.plot_top_data = np.full(laser.shape[0],np.nan)
        self.plot_bot_data = np.full(red.shape[0],np.nan)
        self.plot_mid_data = np.full(red.shape[0],np.nan)

        DebugLog.debugprint(self, "Waveform data array completed.")

        # TODO: can't sample 3 channels at 1000 Hz accurately (1 Mhz not divisible by 3000 Hz)
        receive = self.execute(3, data, red_threshold)
        receive_red = receive[0]
        receive_green = receive[1]
        receive_laser = laser


        self.plot_top_data = receive_green
        self.plot_bot_data = receive_red
        self.plot_mid_data = laser

        return receive_green, receive_laser, receive_red
    
    def set_DAC1(self,V):
        dac = 'DAC,1,{};'.format(self.map_voltage_to_1401(V))
        self.__u14.Write(dac) # DAC,chan,V;

    def __del__(self):
        #Close 1401 if it was initialized
        if hasattr(self,'__u14'):
            self.__u14.Close()

        super().__del__()