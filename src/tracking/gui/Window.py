import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import cv2

from LiveTracking import LiveTracking

class Window():
    liveTracking = None
    size = (800, 600)
    videoSize = (720, 540)

    live = False
    def __init__(self):
        self.root = tk.Tk(screenName="Live Tracking")
        self.root.geometry(f"{self.size[0]}x{self.size[1]}")
        self.create_widgets()

    def create_widgets(self):
        # Frame principal
        main = tk.Frame(self.root)
        main.grid(row=0, column=0, sticky="nsew")

        # La fenêtre doit pouvoir s'étirer
        self.root.rowconfigure(0, weight=1)
        self.root.columnconfigure(0, weight=1)

        # 2 colonnes : gauche (vidéo) plus large, droite (options) plus étroite
        main.columnconfigure(0, weight=3)  # vidéo
        main.columnconfigure(1, weight=1)  # options
        main.rowconfigure(0, weight=1)

        # --- Gauche : vidéo ---

        left = ttk.Frame(main, padding=10)
        left.grid(row=0, column=0, sticky="nsew")

        self.labelVideo = ttk.Label(left, text="(video ici)")
        self.labelVideo.grid(row=0, column=0, sticky="nsew")

        left.rowconfigure(0, weight=1)
        left.columnconfigure(0, weight=1)

        # --- Droite : options ---
        right = ttk.Frame(main, padding=10)
        right.grid(row=0, column=1, sticky="nsew")

        ttk.Label(right, text="Options", font=("Arial", 14, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 10))

        ttk.Label(right, text="Ball Color").grid(row=1, column=0, sticky="w")

        ttk.Label(right, text="R").grid(row=2, column=0, sticky="w")
        self.inputR = ttk.Entry(right)
        self.inputR.grid(row=3, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(right, text="G").grid(row=4, column=0, sticky="w")
        self.inputG = ttk.Entry(right)
        self.inputG.grid(row=5, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(right, text="B").grid(row=6, column=0, sticky="w")
        self.inputB = ttk.Entry(right)
        self.inputB.grid(row=7, column=0, sticky="ew", pady=(0, 12))

        ttk.Button(right, text="Start Live", command=self.onStartLive).grid(row=8, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(right, text="Stop Live", command=self.onStopLive).grid(row=9, column=0, sticky="ew", pady=(0, 6))

        ttk.Button(right, text="Start Recording", command=self.onStartRecording).grid(row=10, column=0, sticky="ew", pady=(0, 6))
        ttk.Button(right, text="Stop Recording", command=self.onStopRecording).grid(row=11, column=0, sticky="ew", pady=(0, 6))

        # pour que les widgets de droite prennent toute la largeur
        right.columnconfigure(0, weight=1)

    def onStartLive(self):
        if self.live:
            return
        if self.liveTracking is None:
            self.setLiveTracking()
        self.liveTracking.openVideo()
        self.live = True
        self.updateImage()


    def updateImage(self):
        if not self.live or self.liveTracking is None:
            return
        frame = self.liveTracking.readFrame()
        if frame is None:
            return
        opencvImage = cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA)
        opencvImage = cv2.resize(opencvImage, self.videoSize)
        capturedImage = Image.fromarray(opencvImage)

        photoImage = ImageTk.PhotoImage(image=capturedImage)
        self.labelVideo.photoImage = photoImage
        self.labelVideo.configure(image=photoImage)
        self.root.after(15, self.updateImage)


    def onStopLive(self):
        self.live = False
        if self.liveTracking is not None:
            self.liveTracking.releaseVideo()


    def onStartRecording(self):
        pass
        self.liveTracking.startRecording()

    def onStopRecording(self):
        pass
        self.liveTracking.stopRecording()

    def mainloop(self):
        self.root.mainloop()

    def setLiveTracking(self):
        bgrValues = self.getBGRValues()
        if bgrValues is not None:
            self.liveTracking = LiveTracking(ballColor=bgrValues, videoSource=1, width=self.videoSize[0], height=self.videoSize[1])

    def getBGRValues(self) -> list:
        return [204, 114, 234]
        try:
            r = int(self.inputR.get())
            g = int(self.inputG.get())
            b = int(self.inputB.get())

            return [b, g, r]
        except ValueError:
            print("Invalid input for BGR values. Please enter integers.")
            return None
