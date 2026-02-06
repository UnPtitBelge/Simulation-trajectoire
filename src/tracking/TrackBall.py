import cv2
import numpy as np
import os
from scipy import interpolate as interp

from utils import *
from path import *

"""
Module for tracking a single colored ball in a video and creating an output video showing its trajectory.
"""

class TrackBall:
    def __init__(self, backgroundColor: list = [0, 0, 0], ballColor: list = [255, 255, 255], output_video: str = "trajectory.mp4" ):
        self.backgroundColor = backgroundColor
        self.ballColor = np.uint8([[ballColor]]) # RGB -> BGR
        self.tracker = []
        self.frames = []
        self.path = os.getcwd() + "/" + DEFAULT_TRACKING_DIR
        create_necessary_dirs(self.path, OUTPUT_IMAGES_DIR)
        create_necessary_dirs(self.path, OUTPUT_VIDEO_DIR)
        self.outputDir = os.path.join(
            self.path + OUTPUT_IMAGES_DIR,
            "images_" + str(findLastDirNumber(self.path + OUTPUT_IMAGES_DIR, "images_") + 1)
        )
        self.output_video_name = os.path.join(
            self.path + OUTPUT_VIDEO_DIR,
            set_video_filename(self.path + OUTPUT_VIDEO_DIR, output_video.split(".")[0], ".mp4")
        )

    def convertVideoToImages(self, path: str, saveImages: bool=True) -> bool:
        """
        Convert a video file into individual image frames and save them in the output directory.
        Args:
            path (str): The path to the video file.
        """

        video = cv2.VideoCapture(path)
        if not video.isOpened():
            return False
        if saveImages:
            os.makedirs(self.outputDir, exist_ok=True)

        frameIndex = 0
        while True:
            ret, frame = video.read()
            if not ret:
                break
            self.frames.append(frame)
            if saveImages:
                imagePath = os.path.join(self.outputDir, f"frame_{frameIndex:04d}.png")
                cv2.imwrite(imagePath, frame)
            frameIndex += 1

        video.release()
        return True


    def trackBall(self) -> None:
        """
        Track the ball in the video frames and create an output video showing the trajectory.
        """
        hsv_color = cv2.cvtColor(self.ballColor, cv2.COLOR_BGR2HSV)[0][0]
        lower, upper = self._set_hue_range(hsv_color)
        positions = []
        canvas = np.zeros_like(self.frames[0])
        for frame in self.frames:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, lower, upper)
            # mask = cv2.medianBlur(mask, 5) # To test if needed
            self._add_center_ball(mask, positions)

        positions = self._interpolate_positions(positions, smoothing=250)
        self._create_video(canvas, positions, fps=60)

    def _set_hue_range(self, hsv_color):
        """
        Set the hue range for color detection.
        """
        hue = hsv_color[0]
        lower = np.array([hue - 15, 50, 10])
        upper = np.array([hue + 15, 255, 255])
        return lower, upper

    def _add_center_ball(self, mask, positions):
        """
         Get the center of the ball from the mask and add it to the positions list.
        """
        M = cv2.moments(mask)
        if M["m00"] > 0:
            cx = int(M["m10"] / M["m00"])
            cy = int(M["m01"] / M["m00"])
            positions.append((cx, cy))

    def _create_video(self, canvas: np.array, positions: np.array, fps:int =30):
        """
        Draw the trajectory of the ball on the canvas.
        """
        height, width, _ = self.frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_video_name, fourcc, fps, (width, height))

        if len(positions) == 0:
            out.write(canvas)
            return
        green = (0, 255, 0)
        red = (0, 0, 255)
        trajectory = canvas.copy()
        for i in range(1, len(positions)):
            cv2.line(trajectory, positions[i-1], positions[i], green, 2)

            frame = trajectory.copy()
            x, y = positions[i]
            cv2.circle(frame, (x, y), 8, red, -1)

            out.write(frame)

        out.release()

    def _interpolate_positions(self, positions: np.array, smoothing: int = 0) -> np.array:
        """
        Interpolate the ball positions using spline interpolation.
        """
        positions = np.array(positions)
        x, y = positions[:,0], positions[:,1]

        tck, u = interp.splprep([x, y], s=smoothing)

        unew = np.linspace(0, 1, 240)
        x_new, y_new = interp.splev(unew, tck)

        return list(zip(np.array(x_new, dtype=int), np.array(y_new, dtype=int)))
