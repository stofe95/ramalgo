'''
Created on 30.03.2020

@author: JM
'''

from PyTrinamic.ic.TMC7300.TMC7300 import TMC7300

class TMC7300_eval(TMC7300):
    """
    This class represents a TMC7300 Evaluation board.

    Communication is done over the TMCL commands writeDRV and readDRV. An
    implementation without TMCL may still use this class if these two functions
    are provided properly. See __init__ for details on the function
    requirements.
    """
    
    def __init__(self, connection, moduleID=1):
        """
        Parameters:
            connection:
                Type: class
                A class that provides the neccessary functions for communicating
                with a TMC7300. The required functions are
                    connection.writeDRV(registerAddress, value, moduleID)
                    connection.readDRV(registerAddress, moduleID, signed)
                for writing/reading to registers of the TMC7300.
            moduleID:
                Type: int, optional, default value: 1
                The TMCL module ID of the TMC7300. This ID is used as a
                parameter for the writeDRV and readDRV functions.
        """
        TMC7300.__init__(self, moduleID)

        self.__connection = connection
        self._MODULE_ID = moduleID
        
        self.APs = _APs

    # Use the driver controller functions for register access
    def writeRegister(self, registerAddress, value, moduleID=None):
        # If the moduleID argument is omitted, use the stored module ID
        if not moduleID:
            moduleID = self._MODULE_ID

        return self.__connection.writeDRV(registerAddress, value, moduleID)

    def readRegister(self, registerAddress, moduleID=None, signed=False):
        # If the moduleID argument is omitted, use the stored module ID
        if not moduleID:
            moduleID = self._MODULE_ID

        return self.__connection.readDRV(registerAddress, moduleID, signed)

    # Axis parameter access
    def getAxisParameter(self, apType, axis):
        if not(0 <= axis < self.MOTORS):
            raise ValueError("Axis index out of range")

        return self.__connection.axisParameter(apType, axis)

    def setAxisParameter(self, apType, axis, value):
        if not(0 <= axis < self.MOTORS):
            raise ValueError("Axis index out of range")

        self.__connection.setAxisParameter(apType, axis, value)

    # Motion Control functions
    def rotate(self, motor, value):
        if not(0 <= motor < self.MOTORS):
            raise ValueError

        self.__connection.rotate(motor, value, moduleID=self._MODULE_ID)
    
    def stop(self, motor):
        self.__connection.stop(motor, moduleID=self._MODULE_ID)
    
    def ICStandby(self, motor, value):
        self.setAxisParameter(self.APs.ICStandby, motor, value)
        


class _APs():
    PWMDutyA                       = 0
    PWMDutyB                       = 1
    MaxCurrent                     = 6
    ICStandby                      = 7
    PWMTwoMotors                   = 8
    ChopperBlankTime               = 162
    PWMFrequency                   = 191
    PWMAutoscale                   = 192
    FreewheelingMode               = 204
