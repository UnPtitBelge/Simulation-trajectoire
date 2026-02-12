"""
    The purpose of the class is only the be able to write the data from the TrackBall class into a file
"""

import os

from path import DEFAULT_TRACKING_DIR

FIRST_LINE = "expID; temps; x; y"

class DataWriter:
    finalFile = ""
    expID = 0

    def __init__(self, finaleFile: str):
        self.finalFile = DEFAULT_TRACKING_DIR + finaleFile

    def appendData(self, data: list) -> None:
        self.expID = self._findLastExpID() + 1
        self._writeHeader()
        with open(self.finalFile, "a") as f:
            for time, entry in enumerate(data):
                line = f"{self.expID}; {time}; {entry[0]}; {entry[1]}"
                f.write(line + "\n")


    def _findLastExpID(self) -> int:
        if not os.path.exists(self.finalFile):
            return 0
        with open(self.finalFile, "r") as f:
            lines = f.readlines()
            if len(lines) <= 1: # Only header exists
                return 0
            lastLine = lines[-1].strip()
            lastExpID = int(lastLine.split(";")[0])
            return lastExpID

    def _writeHeader(self) -> None:
        if not os.path.exists(self.finalFile):
            with open(self.finalFile, "w") as f:
                f.write(FIRST_LINE + "\n")
            return

        with open(self.finalFile, "r") as f:
            lines = f.readlines()
            if len(lines) == 0: # File is empty, write header
                with open(self.finalFile, "w") as fw:
                    fw.write(FIRST_LINE + "\n")


