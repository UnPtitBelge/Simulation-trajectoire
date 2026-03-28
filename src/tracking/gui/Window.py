import os
import tkinter as tk
from pathlib import Path
from tkinter import colorchooser, filedialog, ttk

import cv2
from model.LiveTracking import LiveTracking
from path import DEFAULT_TRACKING_DIR
from PIL import Image, ImageTk
from tkvideo import tkvideo

# Chemin absolu vers le CSV partagé avec le pipeline ML
_CSV_PATH = str(Path(__file__).resolve().parents[2] / "data" / "tracking_data.csv")


class Window:
    liveTracking = None
    size = (1280, 720)
    videoSize = (960, 540)

    live = False

    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Live Tracking")
        self.root.geometry(f"{self.size[0]}x{self.size[1]}")
        self.create_widgets()

    def create_widgets(self):
        # Onglets
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True)

        # Onglet Live Tracking
        self.tabLive = ttk.Frame(self.notebook)
        self.notebook.add(self.tabLive, text="Live Tracking")
        self._tabLive()

        # Onglet TrackBall
        self.tabTrackBall = ttk.Frame(self.notebook)
        self.notebook.add(self.tabTrackBall, text="TrackBall")
        self._tabTrackBall()

        self.notebook.select(1)

    def _tabLive(self):
        # Frame principal
        main = tk.Frame(self.tabLive)
        main.grid(row=0, column=0, sticky="nsew")

        main.columnconfigure(0, weight=0)  # vidéo
        main.columnconfigure(1, weight=0)  # options
        main.rowconfigure(0, weight=0)

        # --- Gauche : vidéo ---

        left = ttk.Frame(main, padding=10)
        left.grid(row=0, column=0, sticky="nsew")

        videoFrame = tk.Frame(
            left, width=self.videoSize[0], height=self.videoSize[1], bg="black"
        )
        videoFrame.grid(row=0, column=0)
        videoFrame.grid_propagate(False)  # empêche l’auto-resize

        self.labelVideo = tk.Label(videoFrame, bg="black")
        self.labelVideo.pack(fill="both", expand=True)
        self.labelVideo.configure(
            image=ImageTk.PhotoImage(Image.new("RGBA", self.videoSize, (0, 0, 0, 255)))
        )

        # --- Droite : options ---
        right = ttk.Frame(main, padding=10)
        right.grid(row=0, column=1, sticky="nsew")

        ttk.Label(right, text="Options", font=("Arial", 14, "bold")).grid(
            row=0, column=0, sticky="w", pady=(0, 10)
        )
        ttk.Label(right, text="Ball Color").grid(row=1, column=0, sticky="w")

        self.rgbButtons(right)
        self.colorPickerButtons(right)

        ttk.Button(right, text="Start Live", command=self.onStartLive).grid(
            row=8, column=0, sticky="ew", pady=(0, 6)
        )
        self.labelLive = tk.Label(right, text="OFF", fg="red")
        self.labelLive.grid(row=9, column=0, sticky="w")
        ttk.Button(right, text="Stop Live", command=self.onStopLive).grid(
            row=10, column=0, sticky="ew", pady=(0, 6)
        )

        ttk.Button(right, text="Start Recording", command=self.onStartRecording).grid(
            row=11, column=0, sticky="ew", pady=(0, 6)
        )
        self.labelRecord = tk.Label(right, text="OFF", fg="red")
        self.labelRecord.grid(row=12, column=0, sticky="w")
        ttk.Button(right, text="Stop Recording", command=self.onStopRecording).grid(
            row=13, column=0, sticky="ew", pady=(0, 6)
        )

        # pour que les widgets de droite prennent toute la largeur
        right.columnconfigure(0, weight=1)

    def rgbButtons(self, parent):
        rgbButtons = tk.Frame(parent)
        rgbButtons.grid(row=2, column=0, columnspan=2, sticky="ew")

        labelR = ttk.Label(rgbButtons, text="R")
        labelR.grid(row=0, column=0, sticky="e")
        self.inputR = ttk.Entry(rgbButtons, width=4)
        self.inputR.grid(row=0, column=1, sticky="w", pady=(0, 8))

        labelG = ttk.Label(rgbButtons, text="G")
        labelG.grid(row=0, column=2, sticky="e")
        self.inputG = ttk.Entry(rgbButtons, width=4)
        self.inputG.grid(row=0, column=3, sticky="w", pady=(0, 8))

        labelB = ttk.Label(rgbButtons, text="B")
        labelB.grid(row=0, column=4, sticky="e")
        self.inputB = ttk.Entry(rgbButtons, width=4)
        self.inputB.grid(row=0, column=5, sticky="w", pady=(0, 8))

    def colorPickerButtons(self, parent):
        cpButtons = tk.Frame(parent)
        cpButtons.grid(row=3, column=0, columnspan=2, sticky="ew")
        ttk.Button(cpButtons, text="Choose Color", command=self.onColorPicker).grid(
            row=0, column=0, sticky="ew", pady=(0, 8)
        )

        ttk.Button(cpButtons, text="✓", command=self.getBGRValues).grid(
            row=0, column=1, sticky="ew", pady=(0, 8)
        )

    def _tabTrackBall(self):
        main = tk.Frame(self.tabTrackBall)
        main.grid(row=0, column=0, sticky="nsew")

        main.columnconfigure(0, weight=0)  # vidéo
        main.columnconfigure(1, weight=0)  # options
        main.rowconfigure(0, weight=0)
        # --- LEFT video ---
        left = ttk.Frame(main, padding=10)
        left.grid(row=0, column=0, sticky="nsew")

        videoFrame = tk.Frame(
            left, width=self.videoSize[0], height=self.videoSize[1], bg="black"
        )
        videoFrame.grid(row=0, column=0)
        videoFrame.grid_propagate(False)  # empêche l’auto-resize

        videoPath = "/Users/ahew/Documents/ulb3/projet3/simulation/src/tracking/outputs/live_records/recording_5.mp4"
        self.labelVideoTrack = tk.Label(videoFrame, bg="black")
        self.labelVideoTrack.pack(fill="both", expand=True)
        self.labelVideoTrack.configure(
            image=ImageTk.PhotoImage(Image.new("RGBA", self.videoSize, (0, 0, 0, 255)))
        )  # random pixels

        # ---- RIGHT options ----
        row = 0
        right = ttk.Frame(self.tabTrackBall, padding=10)
        right.grid(row=0, column=1, sticky="nsew")

        ttk.Label(right, text="Options", font=("Arial", 14, "bold")).grid(
            row=row, column=0, sticky="w", pady=(0, 10)
        )
        row += 1
        ttk.Button(right, text="Choose File", command=self.onChooseFile).grid(
            row=row, column=0, sticky="w", pady=(0, 8)
        )
        row += 1
        self.labelFileTrack = tk.Label(right, text="No file selected", fg="red")

        ttk.Label(right, text="Condition initiale").grid(row=row, column=0, sticky="w")
        row += 1
        ttk.Label(right, text="Vitesse (unité?):").grid(
            row=row, column=0, sticky="w", pady=(0, 8)
        )
        self.inputInitialSpeed = ttk.Entry(right, width=10)
        self.inputInitialSpeed.grid(row=row, column=1, sticky="w", pady=(0, 8))
        row += 1
        ttk.Button(right, text="Track Ball", command=self.getBGRValues).grid(
            row=row, column=0, sticky="w", pady=(0, 8)
        )
        row += 1

        ttk.Button(right, text="▶", command=self.onPlayVideoTracked).grid(
            row=row, column=0, sticky="w", pady=(0, 8)
        )
        row += 1
        self.player = tkvideo("/", "void")

    def onStartLive(self):
        if self.live:
            return
        if self.liveTracking is None:
            self.setLiveTracking()
        self.liveTracking.openVideo()
        self.live = True
        self.labelLive.configure(text="ON", fg="green")
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
        self.root.after(4, self.updateImage)

    def onStopLive(self):
        self.live = False
        if self.liveTracking is not None:
            self.liveTracking.releaseVideo()
        self.labelLive.configure(text="OFF", fg="red")
        self.onStopRecording()  # Arrêter l'enregistrement si le live est arrêté

    def onStartRecording(self):
        self.liveTracking.startRecording()
        self.labelRecord.configure(text="ON", fg="green")

    def onStopRecording(self):
        if self.liveTracking is None:
            self.labelRecord.configure(text="OFF", fg="red")
            return
        ok, msg = self.liveTracking.stopRecording()
        color = "green" if ok else "orange"
        self.labelRecord.configure(
            text=f"Sauvegardé — {msg}" if ok else f"Erreur — {msg}", fg=color
        )
        self.root.after(4000, lambda: self.labelRecord.configure(text="OFF", fg="red"))

    def onColorPicker(self):
        color = colorchooser.askcolor(title="Choose Ball Color")
        if color[0] is not None:
            r, g, b = map(int, color[0])
            self.inputR.delete(0, tk.END)
            self.inputR.insert(0, str(r))
            self.inputG.delete(0, tk.END)
            self.inputG.insert(0, str(g))
            self.inputB.delete(0, tk.END)
            self.inputB.insert(0, str(b))

    def onChooseFile(self):
        filetypes = (("Vidéo", "*.mp4"), ("All files", "*.*"))
        path = os.path.join(os.getcwd(), DEFAULT_TRACKING_DIR)
        self.filenameVideoTrack = tk.filedialog.askopenfilename(
            title="Open a video file", initialdir=path, filetypes=filetypes
        )
        if self.filenameVideoTrack:
            print(f"Selected file: {self.filenameVideoTrack}")

    def onPlayVideoTracked(self):
        if not hasattr(self, "filenameVideoTrack") or not os.path.isfile(
            self.filenameVideoTrack
        ):
            print("No valid video file selected.")
            return
        if self.player.live:
            print("A video is already playing.")
            return
        self.player = tkvideo(
            self.filenameVideoTrack, self.labelVideoTrack, loop=0, size=self.videoSize
        )
        self.player.play()

    def mainloop(self):
        self.root.mainloop()

    def setLiveTracking(self):
        bgrValues = self.getBGRValues()
        if bgrValues is not None:
            self.liveTracking = LiveTracking(
                ballColor=bgrValues,
                videoSource=1,
                width=self.videoSize[0],
                height=self.videoSize[1],
                csv_path=_CSV_PATH,
            )

    def getBGRValues(self) -> list:
        try:
            r = int(self.inputR.get())
            g = int(self.inputG.get())
            b = int(self.inputB.get())

            return [b, g, r]
        except ValueError:
            print("Invalid input for BGR values. Please enter integers.")
        return [53, 92, 112]
