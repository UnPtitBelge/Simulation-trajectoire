import argparse
import os

from gui import Window
from model.TrackBall import TrackBall
from path import *
from stats.DataWriter import DataWriter
from stats.PositionsAnalytics import PositionsAnalytics


def main(filePath: str = "", saveData: bool = False) -> None:
    RESOURCE_PATH = os.path.join(os.getcwd(), RESOURCES_DIR)

    experiment = TrackBall(ballColor=[144, 92, 254])
    experiment.convertVideoToImages(RESOURCE_PATH + filePath)
    experiment.trackBall()

    if not saveData:
        return
    pa = PositionsAnalytics(
        experiment.ballPositions,
        width=experiment.frames[0].shape[1],
        height=experiment.frames[0].shape[0],
        fps=30,  # hypothesis, 30 frames per second uniformly.
        realWidth=172,
        realHeight=100,
    )
    pa.calculateSpeed()
    # pa.setInitialSpeed() # Assuming the ball starts from rest, set initial speed to 0.

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
        "--video_path",
        "-video_path",
        default="first/big_blue.mp4",
        type=str,
        help="The path to the video file to be processed. Should be relative to the resources directory.",
    )
    parser.add_argument(
        "--save_data",
        "-save_data",
        action="store_true",
        default=False,
        help="Flag to indicate whether to save the tracking data into a file. Default is False.",
    )
    return vars(parser.parse_args())


if __name__ == "__main__":
    app = Window.Window()
    app.mainloop()

    # args = list(getArguments().values())
    # main(*args)
