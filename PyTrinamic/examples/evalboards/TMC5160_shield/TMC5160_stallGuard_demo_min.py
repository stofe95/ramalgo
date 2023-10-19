#!/usr/bin/env python3
'''
Minimalistic demonstration of the stallGuard feature of the TMC5160.
To reset stall on all modules, restart then script.

Created on 20.03.2020

@author: LK
'''

################################################################################
# Configuration for all motors

CURRENT_MAX = 10
ACCELERATION = 1000
VELOCITY = 50000
THRESHOLD_SG = 3
THRESHOLD_VELOCITY = 1

################################################################################

import time

import PyTrinamic
from PyTrinamic.evalboards.TMC5160_shield import TMC5160_shield
from PyTrinamic.modules.TMC_EvalShield import TMC_EvalShield

PyTrinamic.showInfo()

from PyTrinamic.connections.ConnectionManager import ConnectionManager
connectionManager = ConnectionManager()
myInterface = connectionManager.connect()

shields = TMC_EvalShield(myInterface, TMC5160_shield).shields

# Initialize all attached shields
for shield in shields:
    print("Rotating motor.")
    shield.setAxisParameter(shield.APs.MaxCurrent, 0, CURRENT_MAX)
    shield.setAxisParameter(shield.APs.MaxAcceleration, 0, ACCELERATION)
    shield.rotate(0, VELOCITY)

    shield.setAxisParameter(shield.APs.SG2Threshold, 0, THRESHOLD_SG)
    shield.setAxisParameter(shield.APs.smartEnergyStallVelocity, 0, 0)
    time.sleep(1)
    shield.setAxisParameter(shield.APs.smartEnergyStallVelocity, 0, THRESHOLD_VELOCITY)

# Loop over all attached shields
while True:
    for shield in shields:
        print(f"Shield: {shield}, SGT: {shield.getAxisParameter(shield.APs.LoadValue, 0)}")
    time.sleep(0.1)

# Demo exit, stop all motors
logger.info("Stopping all motors.")
for shield in shields:
    logger.info(f"Stopping motors for shield {shield}.")
    shield.stop(0)

myInterface.close()
