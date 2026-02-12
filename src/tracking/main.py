import sys
import os

from TrackBall import TrackBall
from DataWriter import DataWriter
from path import *

def main(filePath: str = "", saveImages: bool = False):
    RESOURCE_PATH = os.path.join(os.getcwd(), RESOURCES_DIR)
    experiment = TrackBall(ballColor=[63, 25, 37])
    experiment.convertVideoToImages(RESOURCE_PATH + filePath, saveImages=saveImages)
    experiment.trackBall()
    dw = DataWriter("tracking_data.csv")
    dw.appendData(experiment.tracker)


def getArguments() -> tuple[str, bool]:
    """
    Get the video path and save images flag from command line arguments.
    Should be called as: python main.py (string)video_path (boolean)save_images
    """
    ret = (DEFAULT_PATH_VIDEO, False)
    if len(sys.argv) > 1:
        ret = (sys.argv[1], False)
    if len(sys.argv) > 2:
        ret = (sys.argv[1], sys.argv[2].lower() == 'true')
    return ret


if __name__ == "__main__":
    video_path, save_images = getArguments()
    main(video_path, save_images)
