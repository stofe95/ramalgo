#!/usr/bin/env python3
import time
import PyTrinamic
from PyTrinamic.connections.ConnectionManager import ConnectionManager
from PyTrinamic.evalboards.TMC5072_eval import TMC5072_eval
from PyTrinamic.evalboards.TMC5130_eval import TMC5130_eval


# PyTrinamic.showInfo()

# TMC5072 = TMC5072_eval(myInterface)
# TMC5072.showChipInfo()


class Motors_TMC5072_eval(TMC5072_eval):
    VELOCITY_LOW = 100000 * 2

    # def __init__(self, my_interface):
    def __init__(self, num_motors, port_idx=0):
        # for multiple boards, specify index of port list to use
        # ex. for 2 connected boards at ['COM17', 'COM20'], port 0 = 'COM17' and port 1 = 'COM20'
        port = ""
        if port_idx > 0:
            port = "--port " + str(port_idx)

        self.connectionManager = ConnectionManager(port) #added
        self.my_interface = self.connectionManager.connect() #added
        super().__init__(self.my_interface)

        self.__num_motors = num_motors

        # TODO: modify to account for varying num_motors
        self.MOTOR_LEADING   = 0
        self.MOTOR_FOLLOWING = 1

        #self.VELOCITY     = 100000
        self.VELOCITY_high = 256000

        #self.ACCELERATION = 1000
        self.SG_VELOCITY  = 50000

        self.SG_THRESHOLD = int(4 * 1.5)

        self.direction = -1   # to the left

    def rest_registers(self):

        for DEFAULT_MOTOR in range(self.__num_motors):
            self.writeRegister(self.registers.A1[DEFAULT_MOTOR], 1000)
            self.writeRegister(self.registers.V1[DEFAULT_MOTOR], 50000)
            self.writeRegister(self.registers.D1[DEFAULT_MOTOR], 500)
            self.writeRegister(self.registers.DMAX[DEFAULT_MOTOR], 500)
            self.writeRegister(self.registers.VSTART[DEFAULT_MOTOR], 0)
            self.writeRegister(self.registers.VSTOP[DEFAULT_MOTOR], 10)
            self.writeRegister(self.registers.AMAX[DEFAULT_MOTOR], 1000)
            self.rotate(DEFAULT_MOTOR, 0)
            self.stop(DEFAULT_MOTOR)

            self.writeRegisterField(self.fields.XACTUAL[DEFAULT_MOTOR], 0)
            self.writeRegisterField(self.fields.VACTUAL[DEFAULT_MOTOR], 0)

            ## Configure motors for stallguard homing
            # Stall guard threshold
            self.writeRegisterField(self.fields.SGT[DEFAULT_MOTOR], self.SG_THRESHOLD)
            # Set stall guard minimum velocity
            self.writeRegisterField(self.fields.VCOOLTHRS[DEFAULT_MOTOR], self.SG_VELOCITY)
            # Enable Stall guard
            self.writeRegisterField(self.fields.SG_STOP[DEFAULT_MOTOR], 1)

            self.readRegisterField(self.fields.EVENT_STOP_SG[DEFAULT_MOTOR])

        ## Configure following motor for position ramping
        # TMC5072.writeRegister(TMC5072.registers.V1[MOTOR_FOLLOWING], 0)
        # TMC5072.writeRegister(TMC5072.registers.A1[MOTOR_FOLLOWING], 100)
        # TMC5072.writeRegister(TMC5072.registers.D1[MOTOR_FOLLOWING], 100)
        # TMC5072.writeRegister(TMC5072.registers.VSTART[MOTOR_FOLLOWING], 0)``
        # TMC5072.writeRegister(TMC5072.registers.VSTOP[MOTOR_FOLLOWING], 10)
        # TMC5072.writeRegister(TMC5072.registers.AMAX[MOTOR_FOLLOWING], ACCELERATION)
        # TMC5072.writeRegister(TMC5072.registers.DMAX[MOTOR_FOLLOWING], ACCELERATION)

    def rotate_cw(self, motor_ID, value):
        self.rotate(motor_ID, value)

    def rotate_ccw(self, motor_ID, value):
        self.rotate(motor_ID, -value)

    def read_stallguard(self):
        self.readRegisterField(self.fields.EVENT_STOP_SG[self.MOTOR_LEADING])
        self.readRegisterField(self.fields.EVENT_STOP_SG[self.MOTOR_FOLLOWING])

    # TODO: do not use (not tested)
    def center(self):

        print("Rotating right")
        # TMC5072.rotate(self.DEFAULT_MOTOR, 10*25600)
        self.rotate(self.MOTOR_LEADING, self.direction * Motors_TMC5072_eval.VELOCITY_LOW)
        self.rotate(self.MOTOR_FOLLOWING, self.direction * Motors_TMC5072_eval.VELOCITY_LOW)

        while(self.readRegisterField(self.fields.EVENT_STOP_SG[self.MOTOR_LEADING]) == 0 or self.readRegisterField(self.fields.EVENT_STOP_SG[self.MOTOR_FOLLOWING]) == 0):
            pass

        # stall_status = TMC5072.readRegisterField(TMC5072.fields.EVENT_STOP_SG[self.DEFAULT_MOTOR])
        # print(f'stall_status = {stall_status}')

        self.stop(self.MOTOR_LEADING)
        self.stop(self.MOTOR_FOLLOWING)

        time.sleep(1)

        #reset the current position as zero
        self.writeRegisterField(self.fields.XACTUAL[self.MOTOR_LEADING], 0)
        self.writeRegisterField(self.fields.XACTUAL[self.MOTOR_FOLLOWING], 0)

        MOTOR_LEADING_right_stop = self.readRegisterField(self.fields.XACTUAL[self.MOTOR_LEADING])
        print(f'MOTOR_LEADING right stop = {MOTOR_LEADING_right_stop}')

        MOTOR_FOLLOWING_right_stop = self.readRegisterField(self.fields.XACTUAL[self.MOTOR_FOLLOWING])
        print(f'MOTOR_FOLLOWING right stop = {MOTOR_FOLLOWING_right_stop}')


        center = 1650000
        print(f'center = {center}')

        self.moveTo(self.MOTOR_LEADING, center, self.direction * self.VELOCITY_high)
        self.moveTo(self.MOTOR_FOLLOWING, center, self.direction * self.VELOCITY_high)

        # Wait until position 0 is reached
        #while TMC5072.readRegister(TMC5072.registers.XACTUAL[DEFAULT_MOTOR]) != 0:
        while (self.getAxisParameter(self.APs.ActualPosition, self.MOTOR_LEADING) != center or self.getAxisParameter(self.APs.ActualPosition, self.MOTOR_FOLLOWING) != center):
            pass

        print("Reached Position center")

        time.sleep(1)

    def __delete__(self, instance):
        self.connectionManager.disconnect()


class Motors_TMC5130_eval(TMC5130_eval):
    VELOCITY_LOW = 100000

    # def __init__(self, my_interface):
    def __init__(self, port_idx=0):
        # for multiple boards, specify index of port list to use
        # ex. for 2 connected boards at ['COM17', 'COM20'], port 0 = 'COM17' and port 1 = 'COM20'
        port = ""
        if port_idx > 0:
            port = "--port " + str(port_idx)

        self.connectionManager = ConnectionManager(port) #added
        self.my_interface = self.connectionManager.connect() #added
        super().__init__(self.my_interface)

        self.SG_VELOCITY  = 50000

        self.SG_THRESHOLD = int(4 * 1.5)

    def rest_registers(self):

        self.writeRegister(self.registers.A1, 1000)
        self.writeRegister(self.registers.V1, 50000)
        self.writeRegister(self.registers.D1, 500)
        self.writeRegister(self.registers.DMAX, 500)
        self.writeRegister(self.registers.VSTART, 0)
        self.writeRegister(self.registers.VSTOP, 10)
        self.writeRegister(self.registers.AMAX, 1000)
        self.rotate(0, 0)
        self.stop(0)

        self.writeRegisterField(self.fields.XACTUAL, 0)
        self.writeRegisterField(self.fields.VACTUAL, 0)

        ## Configure motors for stallguard homing
        # Stall guard threshold
        self.writeRegisterField(self.fields.SGT, self.SG_THRESHOLD)
        # Set stall guard minimum velocity
        #self.writeRegisterField(self.fields.VCOOLTHRS, self.SG_VELOCITY)
        # Enable Stall guard
        self.writeRegisterField(self.fields.SG_STOP, 1)

        self.readRegisterField(self.fields.EVENT_STOP_SG)

        ## Configure following motor for position ramping
        # TMC5072.writeRegister(TMC5072.registers.V1[MOTOR_FOLLOWING], 0)
        # TMC5072.writeRegister(TMC5072.registers.A1[MOTOR_FOLLOWING], 100)
        # TMC5072.writeRegister(TMC5072.registers.D1[MOTOR_FOLLOWING], 100)
        # TMC5072.writeRegister(TMC5072.registers.VSTART[MOTOR_FOLLOWING], 0)``
        # TMC5072.writeRegister(TMC5072.registers.VSTOP[MOTOR_FOLLOWING], 10)
        # TMC5072.writeRegister(TMC5072.registers.AMAX[MOTOR_FOLLOWING], ACCELERATION)
        # TMC5072.writeRegister(TMC5072.registers.DMAX[MOTOR_FOLLOWING], ACCELERATION)

    def rotate_cw(self, motor_ID, value):
        self.rotate(motor_ID, value)

    def rotate_ccw(self, motor_ID, value):
        self.rotate(motor_ID, -value)

    def __delete__(self, instance):
        self.connectionManager.disconnect()