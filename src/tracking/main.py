import os
import argparse

from TrackBall import TrackBall
from DataWriter import DataWriter
from path import *
from gui import Window

def main(filePath: str = "", saveImages: bool = False, saveData: bool = False) -> None:
    RESOURCE_PATH = os.path.join(os.getcwd(), RESOURCES_DIR)
    experiment = TrackBall(ballColor=[15, 4, 127])
    experiment.convertVideoToImages(RESOURCE_PATH + filePath, saveImages=saveImages)
    experiment.trackBall()

    if not saveData:
        return
    dw = DataWriter("tracking_data.csv")
    dw.appendData(experiment.ballPositions)


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
    app = Window.Window()
    app.mainloop()

    # args = list(getArguments().values())
    # main(*args)
