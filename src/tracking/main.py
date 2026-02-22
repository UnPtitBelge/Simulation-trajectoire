import os
import argparse

from model.TrackBall import TrackBall
from stats.DataWriter import DataWriter
from stats.PositionsAnalytics import PositionsAnalytics
from path import *
from gui import Window

def main(filePath: str = "", saveImages: bool = False, saveData: bool = False) -> None:
    RESOURCE_PATH = os.path.join(os.getcwd(), RESOURCES_DIR)
    experiment = TrackBall(ballColor=[127, 4, 15])
    experiment.convertVideoToImages(RESOURCE_PATH + filePath, saveImages=saveImages)
    experiment.trackBall()

    if not saveData:
        return
    pa = PositionsAnalytics(
        experiment.ballPositions,
        width=experiment.frames[0].shape[1],
        height=experiment.frames[0].shape[0],
        fps=30, # hypothesis, 30 frames per second uniformly.
        realWidth=90,
        realHeight=90
    )
    pa.calculateSpeed()
    pa.setInitialSpeed(6969) # Assuming the ball starts from rest, set initial speed to 0.

    dw = DataWriter("tracking_data.csv")
    dw.appendData(pa.getBallPositionsWithSpeed)


def getArguments() -> dict:
    """
    Get the video path and save images flag from command line arguments.
    Should be called as: python main.py --video_path <path_to_video> [--save_images] [--save_data]
    """
    parser = argparse.ArgumentParser(
        description="Track a colored ball in a video and save the trajectory data."
    )
    parser.add_argument(
        "--video_path", "-video_path",
        default="first/big_blue.mp4",
        type=str,
        help="The path to the video file to be processed. Should be relative to the resources directory."
    )
    parser.add_argument(
        "--save_images", "-save_images",
        action="store_true",
        default=False,
        help="Flag to indicate whether to save the individual image frames. Default is False."
    )
    parser.add_argument(
        "--save_data", "-save_data",
        action="store_true",
        default=False,
        help="Flag to indicate whether to save the tracking data into a file. Default is False."
    )
    return vars(parser.parse_args())


if __name__ == "__main__":
    # app = Window.Window()
    # app.mainloop()

    args = list(getArguments().values())
    main(*args)
