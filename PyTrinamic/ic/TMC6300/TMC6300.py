'''
Created on 17.04.2020

@author: JM
'''

import struct

from PyTrinamic.helpers import TMC_helpers

DATAGRAM_FORMAT = ">BI"
DATAGRAM_LENGTH = 5

class TMC6300():
    """
    Class for the TMC6300 IC
    """
    def __init__(self, connection, channel=0):
        self.__connection = connection
        self.__channel    = channel



        self.MOTORS       = 1

    def showChipInfo(self):
        print("TMC6300 chip info: Highly Efficient Low Voltage, Zero Standby Current Driver for 3-Phase BLDC/PMSM Motors up to 2A peak. Voltage supply: 2 - 11V")
        #print("VERSION:    " + hex(self.readRegister(self.TMC6300_register.IOIN_OUTPUT) >> 24))
     
    def writeRegister(self, registerAddress, value, channel=None):
        del channel
        datagram = struct.pack(DATAGRAM_FORMAT, registerAddress | 0x80, value)
        self.__connection.send_datagram(datagram, DATAGRAM_LENGTH)

    def readRegister(self, registerAddress, signed=False, channel=None):
        del channel
        datagram = struct.pack(DATAGRAM_FORMAT, registerAddress, 0)
        reply = self.__connection.send_datagram(datagram, DATAGRAM_LENGTH)

        values = struct.unpack(DATAGRAM_FORMAT, reply)
        value = values[1]

        return TMC_helpers.toSigned32(value) if signed else value

    def writeRegisterField(self, field, value):
        return self.writeRegister(field[0], TMC_helpers.field_set(self.readRegister(field[0], self.__channel), field[1], field[2], value), self.__channel)

    def readRegisterField(self, field):
        return TMC_helpers.field_get(self.readRegister(field[0], self.__channel), field[1], field[2])

    def get_pin_state(self):
        pass
