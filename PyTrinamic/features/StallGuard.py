# Created on: 23.03.2020
# Author: LK

import argparse
import logging
import time

import PyTrinamic
from PyTrinamic.features.Feature import Feature

class StallGuard(Feature):

    def __init__(self, module, argList=None, logger=logging.getLogger(__name__)):
        super().__init__(module)

        self.__logger = logger

        parser = argparse.ArgumentParser(description='stallGuard calibration')
        parser.add_argument('-e', '--threshold-velocity', dest='threshold', action='store', nargs=1, type=int, default=[1],
                            help='Velocity threshold, above which stallGuard is enabled. Default: %(default)s.')
        args = parser.parse_known_args(argList)[0]

        self.__threshold = args.threshold[0]

    def calibrate_zero(self):
        self.__logger.info(f"StallGuard zero calibration for module {self._module}.")

        self._module.setAxisParameter(self._module.APs.smartEnergyStallVelocity, 0, 0)

        print("Now, do apply some load to the motor, at which you want it to stop automatically.")
        input("Press enter to continue ...")

        for i in range(3):
            self.__logger.info(f"Starting calibration in {3-i} seconds.")
            time.sleep(1.0)

        self.__logger.info(f"Calibrating SGT.")
        sgthresh = 0
        sgt = 0
        while((sgt == 0) and (sgthresh < 64)):
            self.__logger.info(f"SGT too low, increasing threshold to {sgthresh}.")
            self._module.setAxisParameter(self._module.APs.SG2Threshold, 0, sgthresh)
            sgthresh = sgthresh + 1
            time.sleep(0.2)
            sgt = self._module.getAxisParameter(self._module.APs.LoadValue, 0)
            self.__logger.info(f"SGT load: {sgt}")
        self._module.setAxisParameter(self._module.APs.SG2Threshold, 0, sgthresh - 1)
        print(f"Calibration done. Now release the load.")

        input("Press enter to continue ...")

        self._module.setAxisParameter(self._module.APs.smartEnergyStallVelocity, 0, self.__threshold)

    def calibrate_middle(self):
        self.__logger.info(f"StallGuard middle calibration for module {self._module}.")

        self._module.setAxisParameter(self._module.APs.smartEnergyStallVelocity, 0, 0)

        print("Now, do not apply any load to the motor. Let it run freely.")
        input("Press enter to continue ...")

        self.__logger.info(f"Calibrating SGT.")
        sgthresh = 0
        sgt = 0
        while((sgt < 450) and (sgthresh < 64)):
            self.__logger.info(f"SGT too low, increasing threshold to {sgthresh}.")
            self._module.setAxisParameter(self._module.APs.SG2Threshold, 0, sgthresh)
            sgthresh = sgthresh + 1
            time.sleep(0.1)
            sgt = self._module.getAxisParameter(self._module.APs.LoadValue, 0)
            self.__logger.info(f"SGT load: {sgt}")
        self._module.setAxisParameter(self._module.APs.SG2Threshold, 0, sgthresh - 1)
        print(f"Calibration done.")
