"""
    The purpose of the class is only the be able to write the data from the TrackBall class into a file
    It writes the data in a csv format with the following columns: expID, temps, x, y, speed
    The expID is a unique identifier for each experiment, it is incremented by 1 for each new experiment.
    The temps is the frame number of the video, it is incremented by 1 for each new frame.
    The x and y are the coordinates of the ball in the frame.
    speedX and speedY are the speed of the ball in the x and y direction respectively, calculated from the PositionsAnalytics class.
"""

import os

from path import DEFAULT_TRACKING_DIR

FIRST_LINE = "expID;temps;x;y;speedX;speedY"

class DataWriter:
    finalFile = ""
    expID = 0

    def __init__(self, finalFile: str):
        # Chemin absolu → utilisé tel quel ; relatif → préfixé par DEFAULT_TRACKING_DIR
        if os.path.isabs(finalFile):
            self.finalFile = finalFile
        else:
            self.finalFile = DEFAULT_TRACKING_DIR + finalFile

    def appendData(self, data: list) -> None:
        self.expID = self._findLastExpID() + 1
        self._writeHeader()
        with open(self.finalFile, "a") as f:
            for entry in data:
                line = f"{self.expID}; {entry[0]}; {entry[1]}; {entry[2]}; {entry[3]}; {entry[4]}"
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


