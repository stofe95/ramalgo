'''
Created on 18.04.2019

@author: LH
'''

class TMC5041_register:
    """
    Define all registers of the TMC5041.

    Each register is defined either as an integer or as a tuple of integers.
    Each integer represents a register address. Tuples of addresses are used to
    represent a register that exists multiple times for multiple motors.
    """
    GCONF          = 0x00
    GSTAT          = 0x01
    IFCNT          = 0x02
    TEST_SEL       = 0x03
    INPUT          = 0x04
    X_COMPARE      = 0x05
    PWMCONF_M1     = 0x10
    PWM_STATUS_M1  = 0x11
    PWMCONF_M2     = 0x18
    PWM_STATUS_M2  = 0x19
    RAMPMODE_M1    = 0x20
    XACTUAL_M1     = 0x21
    VACTUAL_M1     = 0x22
    VSTART_M1      = 0x23
    A1_M1          = 0x24
    V1_M1          = 0x25
    AMAX_M1        = 0x26
    VMAX_M1        = 0x27
    DMAX_M1        = 0x28
    D1_M1          = 0x2A
    VSTOP_M1       = 0x2B
    TZEROWAIT_M1   = 0x2C
    XTARGET_M1     = 0x2D
    RAMPMODE_M2    = 0x40
    XACTUAL_M2     = 0x41
    VACTUAL_M2     = 0x42
    VSTART_M2      = 0x43
    A1_M2          = 0x44
    V1_M2          = 0x45
    AMAX_M2        = 0x46
    VMAX_M2        = 0x47
    DMAX_M2        = 0x48
    D1_M2          = 0x4A
    VSTOP_M2       = 0x4B
    TZEROWAIT_M2   = 0x4C
    XTARGET_M2     = 0x4D
    IHOLD_IRUN_M1  = 0x30
    VCOOLTHRS_M1   = 0x31
    VHIGH_M1       = 0x32
    VDCMIN_M1      = 0x33
    SW_MODE_M1     = 0x34
    RAMP_STAT_M1   = 0x35
    XLATCH_M1      = 0x36
    IHOLD_IRUN_M2  = 0x50
    VCOOLTHRS_M2   = 0x51
    VHIGH_M2       = 0x52
    VDCMIN_M2      = 0x53
    SW_MODE_M2     = 0x54
    RAMP_STAT_M2   = 0x55
    XLATCH_M2      = 0x56
    MSLUT__        = 0x60
    MSLUTSEL       = 0x68
    MSLUTSTART     = 0x69
    MSCNT_M1       = 0x6A
    MSCURACT_M1    = 0x6B
    CHOPCONF_M1    = 0x6C
    COOLCONF_M1    = 0x6D
    DCCTRL_M1      = 0x6E
    DRV_STATUS_M1  = 0x6F
    MSCNT_M2       = 0x7A
    MSCURACT_M2    = 0x7B
    CHOPCONF_M2    = 0x7C
    COOLCONF_M2    = 0x7D
    DCCTRL_M2      = 0x7E
    DRV_STATUS_M2  = 0x7F
