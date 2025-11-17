import os
import cv2
import numpy as np

RESOURCES_DIR = "src/tracking/resources/"
DEFAULT_TRACKING_DIR = "src/tracking/outputs/" # path to tracking directory from root
OUTPUT_VIDEO_DIR = "output_videos/"
OUTPUT_IMAGES_DIR = "output_images/"

def findLastDirNumber(path: str, dirName: str) -> int:
    lastNumber = -1
    for item in os.listdir(path):
        if os.path.isdir(os.path.join(path, item)) and item.startswith(dirName):
            try:
                number = int(item[len(dirName):])
                if number > lastNumber:
                    lastNumber = number
            except ValueError:
                continue
    return lastNumber

def findLastFileNumber(path: str, filePrefix: str, fileSuffix: str) -> int:
    lastNumber = -1
    for item in os.listdir(path):
        if os.path.isfile(os.path.join(path, item)) and item.startswith(filePrefix) and item.endswith(fileSuffix):
            try:
                number = int(item[len(filePrefix):-len(fileSuffix)])
                if number > lastNumber:
                    lastNumber = number
            except ValueError:
                continue
    return lastNumber

def set_video_filename(path: str, filePrefix: str, fileSuffix: str) -> str:
    lastNumber = findLastFileNumber(path, filePrefix + '_', fileSuffix)
    newNumber = lastNumber + 1
    return f"{filePrefix}_{newNumber}{fileSuffix}"

def create_necessary_dirs(path: str) -> None:
    os.makedirs(path, exist_ok=True)
    os.makedirs(os.path.join(path, OUTPUT_VIDEO_DIR), exist_ok=True)
    os.makedirs(os.path.join(path, OUTPUT_IMAGES_DIR), exist_ok=True)


"""
balls = {
    ball_id: {
        'color': [], # RGB
        'positions': [],
        'hsv': [], # HSV
        'lower_hsv': [],
        'upper_hsv': [],
        'draw_color': [] # RGB color for drawing line
    }
    ...
}
or class
"""
class TrackBall:
    def __init__(self, backgroundColor: list = [0, 0, 0], ballColor: list = [255, 255, 255], output_video: str = "trajectory.mp4" ) -> None:
        self.backgroundColor = backgroundColor
        self.ballColor = np.uint8([[ballColor]]) # RGB -> BGR
        self.tracker = []
        self.frames = []
        self.path = os.getcwd() + "/" + DEFAULT_TRACKING_DIR
        create_necessary_dirs(self.path)
        self.outputDir = os.path.join(self.path + OUTPUT_IMAGES_DIR , "images_" + str(findLastDirNumber(self.path + OUTPUT_IMAGES_DIR, "images_") + 1))
        self.output_video = os.path.join(self.path + OUTPUT_VIDEO_DIR , set_video_filename(self.path + OUTPUT_VIDEO_DIR, output_video.split(".")[0], ".mp4"))

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
        height, width, _ = self.frames[0].shape
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(self.output_video, fourcc, 30, (width, height))

        hsv_color = cv2.cvtColor(self.ballColor, cv2.COLOR_BGR2HSV)[0][0]
        lower, upper = self._set_hue_range(hsv_color)
        positions = []
        canvas = np.zeros_like(self.frames[0])
        for frame in self.frames:
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            mask = cv2.inRange(hsv, lower, upper)
            # mask = cv2.medianBlur(mask, 5) # To test if needed
            self._add_center_ball(mask, positions)
            self._draw_image(out, canvas, positions)

        out.release()

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

    def _draw_image(self, out, canvas, positions):
        """
        Draw the trajectory of the ball on the canvas and write it to the output video.
        """
        if len(positions) == 0:
            out.write(canvas)
            return

        cv2.circle(canvas, (positions[-1][0], positions[-1][1]), 6, (0, 0, 255), -1)
        for j in range(1, len(positions)):
            cv2.line(canvas, positions[j - 1], positions[j], (0, 255, 0), 2)

        out.write(canvas)


if __name__ == "__main__":
    RESOURCE_PATH = os.path.join(os.getcwd(), RESOURCES_DIR)
    # np.set_printoptions(threshold=np.inf)
    experiment = TrackBall(ballColor=[63, 25, 37])
    experiment.convertVideoToImages(RESOURCE_PATH + "/first/big_blue.mp4", saveImages=True)
    experiment.trackBall()

