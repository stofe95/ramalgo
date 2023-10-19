
'''
Log debug messages to a .txt file
Created on 07.11.2022
@author: Erica Austriaco
'''

import os
from datetime import datetime

class DebugLog:
    # set True to log debug messages to .txt file
    DEBUGPRINT = True
    FILENAME = 'debuglog.txt'

    @staticmethod
    def debugprint(instance, message=""):
        if DebugLog.DEBUGPRINT:
            datestr = "[" + datetime.now().strftime("%d/%m/%Y %H:%M:%S") + "] "

            text = []
            text.append(datestr)
            if instance:
                text.append(instance.__class__.__name__ + ": ")
            if message:
                text.append(str(message))

            fulltext = str(''.join(text))
            
            # print to console
            print(fulltext)

            # print to txt file
            mode = 'w'
            if os.path.isfile(DebugLog.FILENAME):
                mode = 'a'

            with open(DebugLog.FILENAME, mode) as f:
                f.write(fulltext + '\n')