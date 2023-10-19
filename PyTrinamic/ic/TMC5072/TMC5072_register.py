'''
Created on 20.09.2019

@author: JM
'''

class TMC5072_register:
    """
    Define all registers of the TMC5072.

    Each register is defined either as an integer or as a tuple of integers.
    Each integer represents a register address. Tuples of addresses are used to
    represent a register that exists multiple times for multiple motors.
    """
    GCONF           = 0x00
    GSTAT           = 0x01
    IFCNT           = 0x02
    SLAVECONF       = 0x03
    INPUT___OUTPUT  = 0x04
    X_COMPARE       = 0x05
    PWMCONF_M1      = 0x10
    PWM_STATUS_M1   = 0x11
    PWMCONF_M2      = 0x18
    PWM_STATUS_M2   = 0x19
    
    #================================
    RAMPMODE       = ( 0x20, 0x40)
    XACTUAL        = ( 0x21, 0x41)
    VACTUAL        = ( 0x22, 0x42)
    VSTART         = ( 0x23, 0x43)
    A1             = ( 0x24, 0x44) # ATM , no motor validation possible
    V1             = ( 0x25, 0x45)
    AMAX           = ( 0x26, 0x46)
    VMAX           = ( 0x27, 0x47)
    DMAX           = ( 0x28, 0x48)
    D1             = ( 0x2A, 0x4A)
    VSTOP          = ( 0x2B, 0x4B)
    TZEROWAIT      = ( 0x2C, 0x4C)
    XTARGET        = ( 0x2D, 0x4D)
    #=================================


    IHOLD_IRUN      = [0x30, 0x50]
    VCOOLTHRS       = [0x31, 0x51]
    VHIGH           = [0x32, 0x52]
    VDCMIN          = [0x33, 0x53]
    SW_MODE         = [0x34, 0x54]
    RAMP_STAT       = [0x35, 0x55]
    XLATCH          = [0x36, 0x56]

    ENCMODE         = [0x38, 0x58]
    X_ENC           = [0x39, 0x59]
    ENC_CONST       = [0x3A, 0x5A]
    ENC_STATUS      = [0x3B, 0x5B]
    ENC_LATCH       = [0x3C, 0x5C]
    
    MSLUT__         = 0x60
    MSLUTSEL        = 0x68
    MSLUTSTART      = 0x69

    MSCNT           = [0x6A, 0x7A]
    MSCURACT        = [0x6B, 0x7B]
    CHOPCONF        = [0x6C, 0x7C]
    COOLCONF        = [0x6D, 0x7D]
    DCCTRL          = [0x6E, 0x7E]
    DRV_STATUS      = [0x6F, 0x7F]

