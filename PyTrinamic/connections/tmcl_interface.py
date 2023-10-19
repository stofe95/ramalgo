'''
Created on 27.05.2019

@author: LH
'''

from PyTrinamic.TMCL import TMCL, TMCL_Request, TMCL_Command, TMCL_Reply

from PyTrinamic.helpers import TMC_helpers

class tmcl_interface():
    """
    This class is a base class for sending TMCL commands over a communication
    interface.

    Each instance of this class represents one TMCL host. The bus connection for
    the TMCL communication is represented by a subclass inheriting this base
    class. An application with multiple busses should therefore use subclasses
    for all types of busses (e.g. one USB TMCL interface and one serial TMCL
    interface) and create exactly one instance of one of those subclasses per
    bus.

    A subclass is required to override the following functions:
        _send(self, hostID, moduleID, data)
        _recv(self, hostID, moduleID)

    A subclass may use the boolean _debug attribute to toggle printing further
    debug output.

    A subclass may read the _HOST_ID and _MODULE_ID parameters.
    """

    def __init__(self, hostID=2, defaultModuleID=1, debug=False):
        """
        Parameters:
            hostID:
                Type: int, optional, default value: 2
                The ID of the TMCL host. This ID is the same for each module
                when communicating with multiple modules.
            defaultModuleID:
                Type: int, optional, default value: 1
                The default module ID to use when no ID is given to any of the
                tmcl_interface functions. When only communicating with one
                module a script can omit the moduleID for all TMCL interface
                calls by declaring this default value once at the start.
            debug:
                Type: bool, optional, default: False
                A switch for enabling debug mode. Can be changed with
                enableDebug(). In debug mode all sent and received TMCL packets
                get dumped to stdout. The boolean _debug attribute holds the
                current state of debug mode - subclasses may read it to print
                further debug output.
        """

        TMCL.validate_host_id(hostID)
        TMCL.validate_module_id(defaultModuleID)

        if not type(debug) == bool:
            raise TypeError

        self._HOST_ID    = hostID
        self._MODULE_ID  = defaultModuleID
        self._debug      = debug

    def _send(self, hostID, moduleID, data):
        """
        Send the bytearray [data] representing a TMCL command. The length of
        [data] is 9. The hostID and moduleID parameters may be used for extended
        addressing options available on the implemented communication interface.
        """
        raise NotImplementedError("The TMCL interface requires an implementation of the send() function")

    def _recv(self, hostID, moduleID):
        """
        Receive a TMCL reply and return it as a bytearray. The length of the
        returned byte array is 9. The hostID and moduleID parameters may be used
        for extended addressing options available on the implemented
        communication interface.
        """
        raise NotImplementedError("The TMCL interface requires an implementation of the receive() function")

    def enableDebug(self, enable):
        """
        Set the debug mode, which dumps all TMCL datagrams written and read.
        """
        if type(enable) != bool:
            raise TypeError("Expected boolean value")

        self._debug = enable

    def send_request(self, request, moduleID=None):
        """
        Send a TMCL_Request and read back a TMCL_Reply. This function blocks until
        the reply has been received.
        """

        if not moduleID:
            moduleID = self._MODULE_ID

        if self._debug:
            request.dump()

        self._send(self._HOST_ID, moduleID, request.toBuffer())
        reply = TMCL_Reply.from_buffer(self._recv(self._HOST_ID, moduleID))

        if self._debug:
            reply.dump()

        return reply

    def send(self, opcode, opType, motor, value, moduleID=None):
        """
        Send a TMCL datagram and read back a reply. This function blocks until
        the reply has been received.
        """

        if not(type(opcode) == type(opType) == type(motor) == type(value) == int):
            raise TypeError("Expected integer values")

        # If no module ID is given, use the default one
        if not moduleID:
            moduleID = self._MODULE_ID

        request = TMCL_Request(moduleID, opcode, opType, motor, value)

        if self._debug:
            request.dump()

        self._send(self._HOST_ID, moduleID, request.toBuffer())
        reply = TMCL_Reply.from_buffer(self._recv(self._HOST_ID, moduleID))

        if self._debug:
            reply.dump()

        return reply

    def sendBoot(self, moduleID=None):
        """
        Send the command for entering bootloader mode. This TMCL command does
        result in a reply.
        """
        # If no module ID is given, use the default one
        if not moduleID:
            moduleID = self._MODULE_ID

        request = TMCL_Request(moduleID, TMCL_Command.BOOT, 0x81, 0x92, 0xA3B4C5D6)

        if self._debug:
            request.dump()

        # Send the request
        self._send(self._HOST_ID, moduleID, request.toBuffer())

    def getVersionString(self, moduleID=None):
        """
        Request the ASCII version string.
        """
        reply = self.send(TMCL_Command.GET_FIRMWARE_VERSION, 0, 0, 0, moduleID)

        return reply.versionString()

    # General parameter access functions
    def parameter(self, pCommand, pType, pAxis, pValue, moduleID=None, signed=False):
        value = self.send(pCommand, pType, pAxis, pValue, moduleID).value
        return TMC_helpers.toSigned32(value) if signed else value

    def setParameter(self, pCommand, pType, pAxis, pValue, moduleID=None):
        return self.send(pCommand, pType, pAxis, pValue, moduleID)

    # Axis parameter access functions
    def axisParameter(self, commandType, axis, moduleID=None, signed=False):
        value = self.send(TMCL_Command.GAP, commandType, axis, 0, moduleID).value
        return TMC_helpers.toSigned32(value) if signed else value

    def setAxisParameter(self, commandType, axis, value, moduleID=None):
        return self.send(TMCL_Command.SAP, commandType, axis, value, moduleID)

    def storeAxisParameter(self, commandType, axis, moduleID=None):
        return self.send(TMCL_Command.STAP, commandType, axis, 0, moduleID)

    def setAndStoreAxisParameter(self, commandType, axis, value, moduleID=None):
        self.send(TMCL_Command.SAP, commandType, axis, value, moduleID)
        self.send(TMCL_Command.STAP, commandType, axis, 0, moduleID)

    # Global parameter access functions
    def globalParameter(self, commandType, bank, moduleID=None, signed=False):
        value = self.send(TMCL_Command.GGP, commandType, bank, 0, moduleID).value
        return TMC_helpers.toSigned32(value) if signed else value

    def setGlobalParameter(self, commandType, bank, value, moduleID=None):
        return self.send(TMCL_Command.SGP, commandType, bank, value, moduleID)

    def storeGlobalParameter(self, commandType, bank, moduleID=None):
        return self.send(TMCL_Command.STGP, commandType, bank, 0, moduleID)

    def setAndStoreGlobalParameter(self, commandType, bank, value, moduleID=None):
        self.send(TMCL_Command.SGP, commandType, bank, value, moduleID)
        self.send(TMCL_Command.STGP, commandType, bank, 0, moduleID)

    # Register access functions
    def writeMC(self, registerAddress, value, moduleID=None):
        return self.writeRegister(registerAddress, TMCL_Command.WRITE_MC, 0, value, moduleID)

    def readMC(self, registerAddress, moduleID=None, signed=False):
        return self.readRegister(registerAddress, TMCL_Command.READ_MC, 0, moduleID, signed)

    def writeDRV(self, registerAddress, value, moduleID=None):
        return self.writeRegister(registerAddress, TMCL_Command.WRITE_DRV, 1, value, moduleID)

    def readDRV(self, registerAddress, moduleID=None, signed=False):
        return self.readRegister(registerAddress, TMCL_Command.READ_DRV, 1, moduleID, signed)

    def readRegister(self, registerAddress, command, channel, moduleID=None, signed=False):
        value = self.send(command, registerAddress, channel, 0, moduleID).value
        return TMC_helpers.toSigned32(value) if signed else value

    def writeRegister(self, registerAddress, command, channel, value, moduleID=None):
        return self.send(command, registerAddress, channel, value, moduleID)

    # Motion control functions
    def rotate(self, motor, velocity, moduleID=None):
        return self.send(TMCL_Command.ROR, 0, motor, velocity, moduleID)

    def stop(self, motor, moduleID=None):
        return self.send(TMCL_Command.MST, 0, motor, 0, moduleID)

    def move(self, moveType, motor, position, moduleID=None):
        return self.send(TMCL_Command.MVP, moveType, motor, position, moduleID)

    def moveTo(self, motor, position, moduleID=None):
        """
        Use the TMCL MVP command to perform an absolute movement.

        Returns the value of the reply. Refer to the documentation of your
        specific module for details on what is returned.
        """
        return self.move(0, motor, position, moduleID).value

    def moveBy(self, motor, distance, moduleID=None):
        """
        Use the TMCL MVP command to perform a relative movement.

        Returns the value of the reply. Refer to the documentation of your
        specific module for details on what is returned.
        """
        return self.move(1, motor, distance, moduleID).value

    # IO pin functions
    def analogInput(self, x, moduleID=None):
        return self.send(TMCL_Command.GIO, x, 1, 0, moduleID).value

    def digitalInput(self, x, moduleID=None):
        return self.send(TMCL_Command.GIO, x, 0, 0, moduleID).value

    def digitalOutput(self, x, moduleID=None):
        return self.send(TMCL_Command.GIO, x, 2, 0, moduleID).value

    def setDigitalOutput(self, x, moduleID=None):
        self.send(TMCL_Command.SIO, x, 2, 1, moduleID).value

    def clearDigitalOutput(self, x, moduleID=None):
        self.send(TMCL_Command.SIO, x, 2, 0, moduleID).value

    " testing new interface usage (ED) => "
    # axis parameter access functions
    def axisParameterRaw(self, moduleID, axis, commandType):
        return self.send(TMCL_Command.GAP, commandType, axis, 0, moduleID).value

    def setAxisParameterRaw(self, moduleID, axis, commandType,  value):
        return self.send(TMCL_Command.SAP, commandType, axis, value, moduleID)

    # global parameter access functions
    def globalParameterRaw(self, moduleID, bank, commandType):
        return self.send(TMCL_Command.GGP, commandType, bank, 0, moduleID).value

    def setGlobalParameterRaw(self, moduleID, bank, commandType, value):
        return self.send(TMCL_Command.SGP, commandType, bank, value, moduleID)

    # IO pin functions
    def analogInputRaw(self, moduleID, x):
        return self.send(TMCL_Command.GIO, x, 1, 0, moduleID).value

    def digitalInputRaw(self, moduleID, x):
        return self.send(TMCL_Command.GIO, x, 0, 0, moduleID).value

    def digitalOutputRaw(self, moduleID, x):
        return self.send(TMCL_Command.GIO, x, 2, 0, moduleID).value

    def setDigitalOutputRaw(self, moduleID, x):
        self.send(TMCL_Command.SIO, x, 2, 1, moduleID).value

    def clearDigitalOutputRaw(self, moduleID, x):
        self.send(TMCL_Command.SIO, x, 2, 0, moduleID).value

    " <= testing new interface usage (ED) "
