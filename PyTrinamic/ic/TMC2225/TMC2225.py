'''
Created on 17.10.2019

@author: JM
'''

from PyTrinamic.ic.TMC2225.TMC2225_register import TMC2225_register
from PyTrinamic.ic.TMC2225.TMC2225_register_variant import TMC2225_register_variant
from PyTrinamic.ic.TMC2225.TMC2225_fields import TMC2225_fields
from PyTrinamic.helpers import TMC_helpers

class TMC2225():
    """
    Class for the TMC2225 IC
    """
    def __init__(self, channel):
        self.__channel  = channel

        self.registers  = TMC2225_register
        self.fields     = TMC2225_fields
        self.variants   = TMC2225_register_variant

        self.MOTORS     = 2

    def showChipInfo(self):
        print("TMC2225 chip info: The TMC2225 are ultra-silent motor driver ICs for two-phase stepper motors. Their pinning is compatible to a number of legacy drivers. Voltage supply: 4,75 - 36V")

    def writeRegister(self, registerAddress, value, channel):
        raise NotImplementedError

    def readRegister(self, registerAddress, channel):
        raise NotImplementedError

    def writeRegisterField(self, field, value):
        return self.writeRegister(field[0], TMC_helpers.field_set(self.readRegister(field[0], self.__channel), field[1], field[2], value), self.__channel)

    def readRegisterField(self, field):
        return TMC_helpers.field_get(self.readRegister(field[0], self.__channel), field[1], field[2])

    def moveBy(self, motor, distance, velocity):
        if not(0 <= motor < self.MOTORS):
            raise ValueError

        position = self.readRegister(self.registers.XACTUAL, self.__channel, signed=True)

        self.moveTo(motor, position + distance, velocity)

        return position + distance

    def get_pin_state(self):
        pass
