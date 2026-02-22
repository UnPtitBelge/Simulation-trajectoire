
class PositionsAnalytics:
    def __init__(self, ballPositions: list, width: int, height: int, fps: int, realWidth: float, realHeight: float):
        self.ballPositions = ballPositions
        self.width = width
        self.height = height
        self.fps = fps
        self.realWidth = realWidth
        self.realHeight = realHeight
        self.ballPosSpeed = []

    def calculateSpeed(self) -> list:
        scaleX = self.realWidth / self.width
        scaleY = self.realHeight / self.height

        speeds = []
        for i in range(1, len(self.ballPositions)):
            t1, p1 = self.ballPositions[i-1]
            t2, p2 = self.ballPositions[i]
            x1, y1 = p1
            x2, y2 = p2
            dx = (x2 - x1) * scaleX
            dy = (y2 - y1) * scaleY
            realDistance = (dx ** 2 + dy ** 2) ** 0.5
            timeElapsed = (t2 - t1) / self.fps
            speed = realDistance / timeElapsed if timeElapsed > 0 else 0
            speeds.append(speed)
            self.ballPosSpeed.append((t2, x2, y2, speed))
        # Insert the first position with same speed as the second position (approximation)
        self.ballPosSpeed.insert(0, (self.ballPositions[0][0], self.ballPositions[0][1][0], self.ballPositions[0][1][1], speeds[0] if speeds else 0))
        return speeds

    def setInitialSpeed(self, initialSpeed: float) -> None:
        if self.ballPosSpeed:
            self.ballPosSpeed[0] = (self.ballPosSpeed[0][0], self.ballPosSpeed[0][1], self.ballPosSpeed[0][2], initialSpeed)
        else:
            self.intialSpeed = initialSpeed

    @property
    def getBallPositionsWithSpeed(self):
        return self.ballPosSpeed

    @property
    def getBallPositions(self):
        return [(t, x, y) for t, x, y in self.ballPositions]

