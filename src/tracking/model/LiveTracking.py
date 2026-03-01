import cv2
import os

from model.TrackBall import TrackBall
from path import DEFAULT_TRACKING_DIR
from utils import set_video_filename, create_necessary_dirs

class LiveTracking:
    recording = False
    fps = 30
    # BGR color of the ball to track
    def __init__(self, ballColor=[], videoSource=0, width=None, height=None):
        self.ballColor = ballColor
        self.videoSource = videoSource
        self.width = width
        self.height = height
        self.positions = []
        self.records = []

        self.tb = TrackBall(ballColor=[204, 114, 234])

    def openVideo(self) -> bool:
        self.cap = cv2.VideoCapture(self.videoSource)

        if self.width is not None and self.height is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)

        if not self.cap.isOpened():
            print("Error: Could not open video.")
            return False
        return True

    def readFrame(self):
        if self.cap is None or not self.cap.isOpened():
            print("Error: Video source is not opened.")
            return None
        ret, frame = self.cap.read()
        if not ret:
            print("Error: Could not read frame.")
            return None

        if self.recording and hasattr(self, 'out') and self.out is not None:
            # self.out.write(frame)
            self.records.append(frame.copy())

        frame = self.modifyFrame(frame)
        return frame

    def modifyFrame(self, frame):
        centre = self.tb.findBallFrame(frame)
        if centre is not None:
            self.positions.append(centre)

        self.positions = self.positions[-20:]  # trajectoire courte
        for i in range(1, len(self.positions)):
            cv2.line(frame, self.positions[i-1], self.positions[i], (0,255,0), 2)
        return frame

    def releaseVideo(self):
        if self.cap is not None and self.cap.isOpened():
            self.cap.release()
        try:
            cv2.destroyAllWindows()
        except cv2.error as e:
            print(f"Error closing windows: {e}")

    def startRecording(self):
        if self.recording:
            print("Already recording.")
            return
        if self.cap is None or not self.cap.isOpened():
            print("Error: Video source is not opened. Cannot start recording.")
            return

        ret, frame = self.cap.read()
        if not ret:
            print("Error: Cannot read frame to initialize recording.")
            return
        height, width = frame.shape[:2]

        create_necessary_dirs(DEFAULT_TRACKING_DIR, "live_records")
        basePath = DEFAULT_TRACKING_DIR + "live_records/"
        name = set_video_filename(DEFAULT_TRACKING_DIR + "live_records/", "recording", ".mp4")

        self.fourcc = cv2.VideoWriter_fourcc(*'avc1')
        self.out = cv2.VideoWriter(os.path.join(basePath, name), self.fourcc, self.fps, (width, height))

        if not self.out.isOpened():
            print("Error: VideoWriter failed to open.")
            return

        self.recording = True

    def stopRecording(self):
        self.recording = False
        for frame in self.records:
            self.out.write(frame)
        self.records = []
        if hasattr(self, 'out') and self.out is not None:
            self.out.release()
            self.out = None

if __name__ == '__main__':
    lv = LiveTracking(ballColor=[204, 114, 234], videoSource=0)
    lv.openVideo()
    for _ in range(100):
        frame = lv.readFrame()
        if frame is None:
            break
        cv2.imshow("Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    lv.releaseVideo()

