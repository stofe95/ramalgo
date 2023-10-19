'''
Created on 29.05.2019

@author: LH
'''

import serial.tools.list_ports;

from PyTrinamic.connections.serial_tmcl_interface import serial_tmcl_interface

class usb_tmcl_interface(serial_tmcl_interface):
    """
    Opens a USB TMCL connection.

    This class is almost the same as the class for serial TMCL connections.
    The only difference are the functions for the connection manager, which
    filter the available serial connections to only include the serial over
    USB ones.
    """

    # USB Vendor and Product IDs
    __USB_IDS = [
        { # Landungsbrücke
            "VID": 0x2A3C,
            "PID": 0x0700
        },
        { # TMCM1460
            "VID": 0x16D0,
            "PID": 0x0461
        },
        { # Startrampe
            "VID": 0x16D0,
            "PID": 0x07E4
        },
        { # TMC_CDC_DEV
            "VID": 0x2A3C,
            "PID": 0x0200
        },
        { # TMCM1160, TMCM1161
            "VID": 0x2A3C,
            "PID": 0x0100
        },
        { # TMC_EvalShield
            "VID": 0x0483,
            "PID": 0x374B
        }
    ]

    def __init__(self, comPort, datarate=115200, hostID=2, moduleID=1, debug=False):
        super().__init__(comPort, datarate, hostID, moduleID, debug)

    def printInfo(self):
        print("Connection: type=usb_tmcl_interface com=" + self._serial.portstr + " baud=" + str(self._baudrate))

    @staticmethod
    def supportsTMCL():
        return True

    @staticmethod
    def list():
        """
            Return a list of available connection ports as a list of strings.

            This function is required for using this interface with the
            connection manager.
        """
        connected = []
        for element in sorted(serial.tools.list_ports.comports()):
            for entry in usb_tmcl_interface.__USB_IDS:
                if entry["VID"] == element.vid and entry["PID"] == element.pid:
                    connected.append(element.device)

        return connected
