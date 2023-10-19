'''
Created on 25.06.2019

@author: ED
'''
from PyTrinamic.helpers import TMC_helpers

class TMCM_1633():
    def __init__(self, connection):
        self.connection = connection

        self.GPs   = _GPs
        self.APs   = _APs
        self.ENUMs = _ENUMs

        self.motor = 0

    @staticmethod
    def getEdsFile():
        return __file__.replace("TMCM_1633.py", "TMCM_1633_Hw1.00_Fw2.10.eds")

    def showChipInfo(self):
        ("The TMCM-1633 is a highly integrated single axis BLDC servo controller module with several interface options. Voltage supply: 14,5 - 48V");

    " axis parameter access "
    def axisParameter(self, apType):
        return self.connection.axisParameter(apType, self.motor)

    def setAxisParameter(self, apType, value):
        self.connection.setAxisParameter(apType, self.motor, value)

    " global parameter access "
    def globalParameter(self, gpType):
        return self.connection.globalParameter(gpType, self.motor)

    def setGlobalParameter(self, gpType, value):
        self.connection.setGlobalParameter(gpType, self.motor, value)

    " standard functions "
    def moveToPosition(self, position):
        self.setAxisParameter(self.APs.TargetPosition, position)

    def targetPosition(self):
        return self.axisParameter(self.APs.TargetPosition)

    def actualPosition(self):
        return TMC_helpers.toSigned32(self.axisParameter(self.APs.ActualPosition))    

    def setActualPosition(self, position):
        return self.setAxisParameter(self.APs.ActualPosition, position)

    def rotate(self, velocity):
        self.setAxisParameter(self.APs.TargetVelocity, velocity)

    def actualVelocity(self):
        return TMC_helpers.toSigned32(self.axisParameter(self.APs.ActualVelocity))    

    def setTargetTorque(self, torque):
        self.setAxisParameter(self.APs.TargetTorque, torque)

    def targetTorque(self):
        return self.axisParameter(self.APs.TargetTorque)

    def actualTorque(self):
        return self.axisParameter(self.APs.ActualTorque)

    " helpful functions "

    def maxVelocity(self):
        return self.axisParameter(self.APs.MaxVelocity)

    def setMaxVelocity(self, maxVelocity):
        self.setAxisParameter(self.APs.MaxVelocity, maxVelocity)

    def maxTorque(self):
        return self.axisParameter(self.APs.MaxTorque)

    def setMaxTorque(self, maxTorque):
        self.setAxisParameter(self.APs.MaxTorque, maxTorque)

    def openLoopTorque(self):
        return self.axisParameter(self.APs.StartCurrent)

    def setOpenLoopTorque(self, torque):
        self.setAxisParameter(self.APs.StartCurrent, torque)

    def acceleration(self):
        return self.axisParameter(self.APs.Acceleration)

    def setAcceleration(self, acceleration):
        self.setAxisParameter(self.APs.Acceleration, acceleration)

    def targetReachedVelocity(self):
        return self.axisParameter(self.APs.TargetReachedVelocity)

    def setTargetReachedVelocity(self, velocity):
        self.setAxisParameter(self.APs.TargetReachedVelocity, velocity)

    def targetReachedDistance(self):
        return self.axisParameter(self.APs.TargetReachedDistance)

    def setTargetReachedDistance(self, distance):
        self.setAxisParameter(self.APs.TargetReachedDistance, distance)

    def motorHaltedVelocity(self):
        return self.axisParameter(self.APs.MotorHaltedVelocity)

    def setMotorHaltedVelocity(self, velocity):
        self.setAxisParameter(self.APs.MotorHaltedVelocity, velocity)

    def positionReached(self):
        return ((self.statusFlags() & self.ENUMs.FLAG_POSITION_END) != 0)

    def rampEnabled(self):
        return self.axisParameter(self.APs.EnableRamp)

    def setRampEnabled(self, enable):
        self.setAxisParameter(self.APs.EnableRamp, enable)

    def torquePParameter(self):
        return self.axisParameter(self.APs.TorqueP)

    def setTorquePParameter(self, pValue):
        self.setAxisParameter(self.APs.TorqueP, pValue)

    def torqueIParameter(self):
        return self.axisParameter(self.APs.TorqueI)

    def setTorqueIParameter(self, pValue):
        self.setAxisParameter(self.APs.TorqueI, pValue)

    def velocityPParameter(self):
        return self.axisParameter(self.APs.VelocityP)

    def setVelocityPParameter(self, pValue):
        self.setAxisParameter(self.APs.VelocityP, pValue)

    def velocityIParameter(self):
        return self.axisParameter(self.APs.VelocityI)

    def setVelocityIParameter(self, pValue):
        self.setAxisParameter(self.APs.VelocityI, pValue)

    def positionPParameter(self):
        return self.axisParameter(self.APs.PositionP)

    def setPositionPParameter(self, pValue):
        self.setAxisParameter(self.APs.PositionP, pValue)

    def motorPoles(self):
        return self.axisParameter(self.APs.MotorPoles)

    def setMotorPoles(self, poles):
        self.setAxisParameter(self.APs.MotorPoles, poles)

    def hallInvert(self):
        return self.axisParameter(self.APs.HallSensorInvert)

    def setHallInvert(self, invert):
        self.setAxisParameter(self.APs.HallSensorInvert, invert)

    def encoderInitMode(self):
        return self.axisParameter(self.APs.EncoderInitMode)

    def setEncoderInitMode(self, mode):
        self.setAxisParameter(self.APs.EncoderInitMode, mode)

    def encoderResolution(self):
        return self.axisParameter(self.APs.EncoderSteps)

    def setEncoderResolution(self, steps):
        self.setAxisParameter(self.APs.EncoderSteps, steps)

    def encoderDirection(self):
        return self.axisParameter(self.APs.EncoderDirection)

    def setEncoderDirection(self, direction):
        self.setAxisParameter(self.APs.EncoderDirection, direction)

    def commutationMode(self):
        return self.axisParameter(self.APs.CommutationMode)

    def setCommutationMode(self, mode):
        self.setAxisParameter(self.APs.CommutationMode, mode)

    def statusFlags(self):
        return self.axisParameter(self.APs.StatusFlags)

    def analogInput(self, x):
        return self.connection.analogInput(x)

    def digitalInput(self, x):
        return self.connection.digitalInput(x)

    def digitalOutput(self, x):
        return self.connection.digitalOutput(x)

    def setDigitalOutput(self, x):
        return self.connection.setDigitalOutput(x, 1)

    def clearDigitalOutput(self, x):
        return self.connection.setDigitalOutput(x, 0)

    def showMotorConfiguration(self):
        print("Motor configuration:")
        print("\tMotor poles: " + str(self.motorPoles()))
        print("\tMax torque:  " + str(self.maxTorque()) + " mA")

    def showHallConfiguration(self):
        print("Hall configuration:")
        print("\tHall invert: " + str(self.hallInvert()))

    def showEncoderConfiguration(self):
        print("Encoder configuration:")
        print("\tOpen loop torque:   " + str(self.openLoopTorque()) + " mA")
        print("\tEncoder resolution: " + str(self.encoderResolution()))
        print("\tEncoder direction:  " + str(self.encoderDirection()))
        print("\tEncoder init mode:  " + str(self.encoderInitMode()))

    def showMotionConfiguration(self):
        print("Motion configuration:")
        print("\tMax velocity: " + str(self.maxVelocity()))
        print("\tAcceleration: " + str(self.acceleration()))
        print("\tRamp enabled: " + ("disabled" if (self.rampEnabled()==0) else "enabled"))
        print("\tMotor halted velocity:   " + str(self.motorHaltedVelocity()))
        print("\tTarget reached velocity: " + str(self.targetReachedVelocity()))
        print("\tTarget reached distance: " + str(self.targetReachedDistance()))

    def showPIConfiguration(self):
        print("PI configuration:")
        print("\tTorque   P: " + str(self.torquePParameter()) + " I: " + str(self.torqueIParameter()))
        print("\tVelocity P: " + str(self.velocityPParameter()) + " I: " + str(self.velocityIParameter()))
        print("\tPosition P: " + str(self.positionPParameter()))

class _APs():
    TargetPosition                 = 0
    ActualPosition                 = 1
    TargetVelocity                 = 2
    ActualVelocity                 = 3
    MaxVelocity                    = 4
    MaxTorque                      = 6
    TargetReachedVelocity          = 7
    MotorHaltedVelocity            = 9
    TargetReachedDistance          = 10
    Acceleration                   = 11
    RampVelocity                   = 13
    ReinitBldcRegulation           = 31
    PIDRegulationLoopDelay         = 133
    CurrentRegulationLoopDelay     = 134
    EnableRamp                     = 146
    ActualTorque                   = 150
    SupplyVoltage                  = 151
    DriverTemperature              = 152
    TargetTorque                   = 155
    StatusFlags                    = 156
    CommutationMode                = 159
    ClearOnNull                    = 161
    ClearOnce                      = 163
    EncoderOffset                  = 165
    TorqueP                        = 172
    TorqueI                        = 173
    StartCurrent                   = 177
    MainLoopsPerSecond             = 180
    PwmLoopsPerSecond              = 181
    TorqueLoopsPerSecond           = 182
    VelocityLoopsPerSecond         = 183
    DebugValue0                    = 190
    DebugValue1                    = 191
    DebugValue2                    = 192
    DebugValue3                    = 193
    DebugValue4                    = 194
    DebugValue5                    = 195
    DebugValue6                    = 196
    DebugValue7                    = 197
    DebugValue8                    = 198
    DebugValue9                    = 199
    CurrentPIDError                = 200
    CurrentPIDErrorSum             = 201
    ActualHallAngle                = 210
    ActualEncoderAngle             = 211
    ActualControlledAngle          = 212
    PositionPIDError               = 226
    VelocityPIDError               = 228
    VelocityPIDErrorSum            = 229
    PositionP                      = 230
    VelocityP                      = 234
    VelocityI                      = 235
    InitVelocity                   = 241
    InitSineDelay                  = 244
    EncoderInitMode                = 249
    EncoderSteps                   = 250
    EncoderDirection               = 251
    HallInterpolation              = 252
    MotorPoles                     = 253
    HallSensorInvert               = 254
    DriverEnabled                  = 255

class _ENUMs():
    COMM_MODE_FOC_HALL              = 6
    COMM_MODE_FOC_ENCODER           = 7
    COMM_MODE_FOC_CONTROLLED        = 8

    ENCODER_INIT_MODE_0             = 0
    ENCODER_INIT_MODE_1             = 1
    ENCODER_INIT_MODE_2             = 2

    FLAG_POSITION_END               = 0x00004000

class _GPs():
    serialBaudRate                 = 65
    serialAddress                  = 66
    CANBitRate                     = 69
    CANsendID                      = 70
    CANreceiveID                   = 71
    telegramPauseTime              = 75
    serialHostAddress              = 76
    autoStartMode                  = 77
    applicationStatus              = 128
    programCounter                 = 130
    tickTimer                      = 132
