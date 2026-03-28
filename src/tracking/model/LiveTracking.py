import cv2
import os
import numpy as np

from path import DEFAULT_TRACKING_DIR
from stats.DataWriter import DataWriter
from stats.PositionsAnalytics import PositionsAnalytics
from utils import set_video_filename, create_necessary_dirs

class _BallDetector:
    """Détection HSV minimale — évite d'instancier TrackBall (qui crée des répertoires)."""

    def __init__(self, bgr_color: list, hue_range: int = 10):
        color_px = np.array([[bgr_color]], dtype=np.uint8)  # shape (1,1,3)
        hsv = cv2.cvtColor(color_px, cv2.COLOR_BGR2HSV)[0][0]
        h, s, v = int(hsv[0]), int(hsv[1]), int(hsv[2])
        r = hue_range * 5
        self.lower = np.array([max(0, h - r),   max(0,   s - r), max(0,   v - r)])
        self.upper = np.array([min(179, h + r),  min(255, s + r), min(255, v + r)])

    def find(self, frame: np.ndarray) -> tuple | None:
        """Retourne (cx, cy) du barycentre de la bille, ou None."""
        hsv  = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        mask = cv2.inRange(hsv, self.lower, self.upper)
        mask = cv2.medianBlur(mask, 5)
        M = cv2.moments(mask)
        if M["m00"] > 0:
            return (int(M["m10"] / M["m00"]), int(M["m01"] / M["m00"]))
        return None


class LiveTracking:
    recording = False

    def __init__(self, ballColor: list = [], videoSource: int = 0,
                 width: int | None = None, height: int | None = None,
                 csv_path: str | None = None,
                 real_width: float = 172, real_height: float = 100,
                 fps: int = 30,
                 roi_margin: int = 120,
                 n_trail_frames: int = 20):
        """
        ballColor      : couleur BGR de la bille
        videoSource    : index caméra (0 = webcam intégrée, 1 = externe)
        csv_path       : chemin absolu vers le CSV ML (None = pas de sauvegarde)
        real_width / real_height : dimensions réelles (mêmes unités que les données
                                   existantes, défaut = 172×100)
        fps            : fréquence d'acquisition (Hz) — [tracking].fps dans ml.toml
        roi_margin     : demi-largeur fenêtre ROI (px) — [tracking].roi_margin
        n_trail_frames : longueur de la trajectoire affichée — [tracking].n_trail_frames
        """
        self.ballColor      = ballColor
        self.videoSource    = videoSource
        self.width          = width
        self.height         = height
        self.fps            = fps
        self._roi_margin    = roi_margin
        self._n_trail       = n_trail_frames

        self._csv_path    = csv_path
        self._real_width  = real_width
        self._real_height = real_height

        self._detector = _BallDetector(ballColor if ballColor else [204, 114, 234])

        self.positions: list = []            # dernières 20 positions (affichage)
        self._last_center: tuple | None = None  # pour le suivi ROI

        # Enregistrement
        self._recording_positions: list = []  # (frame_n, (x, y))
        self._frame_count: int = 0

    # ── Caméra ────────────────────────────────────────────────────────────────

    def openVideo(self) -> bool:
        self.cap = cv2.VideoCapture(self.videoSource)
        if self.width is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH,  self.width)
        if self.height is not None:
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
        if not self.cap.isOpened():
            print("Erreur : impossible d'ouvrir la source vidéo.")
            return False
        return True

    def readFrame(self) -> np.ndarray | None:
        if not hasattr(self, 'cap') or not self.cap.isOpened():
            return None
        ret, frame = self.cap.read()
        if not ret:
            return None

        # Écriture directe — pas de buffer mémoire, pas de latence au stopRecording
        if self.recording and hasattr(self, '_out') and self._out is not None:
            self._out.write(frame)

        return self.modifyFrame(frame)

    def modifyFrame(self, frame: np.ndarray) -> np.ndarray:
        """Détecte la bille (ROI si position connue) et dessine la trajectoire."""
        centre = self._detect(frame)
        self._last_center = centre

        if centre is not None:
            self.positions.append(centre)
            if self.recording:
                self._recording_positions.append((self._frame_count, centre))

        if self.recording:
            self._frame_count += 1

        self.positions = self.positions[-self._n_trail:]
        for i in range(1, len(self.positions)):
            cv2.line(frame, self.positions[i - 1], self.positions[i], (0, 255, 0), 2)

        return frame

    def releaseVideo(self) -> None:
        if hasattr(self, 'cap') and self.cap.isOpened():
            self.cap.release()
        try:
            cv2.destroyAllWindows()
        except cv2.error:
            pass

    # ── Enregistrement ────────────────────────────────────────────────────────

    def startRecording(self) -> None:
        if self.recording:
            print("Enregistrement déjà en cours.")
            return
        if not hasattr(self, 'cap') or not self.cap.isOpened():
            print("Erreur : source vidéo non ouverte.")
            return

        ret, frame = self.cap.read()
        if not ret:
            print("Erreur : impossible de lire la première frame.")
            return
        h, w = frame.shape[:2]

        create_necessary_dirs(DEFAULT_TRACKING_DIR, "live_records")
        base = DEFAULT_TRACKING_DIR + "live_records/"
        name = set_video_filename(base, "recording", ".mp4")

        fourcc = cv2.VideoWriter.fourcc(*'avc1')
        self._out = cv2.VideoWriter(os.path.join(base, name), fourcc, self.fps, (w, h))
        if not self._out.isOpened():
            print("Erreur : VideoWriter n'a pas pu s'ouvrir.")
            return

        self._recording_positions = []
        self._frame_count = 0
        self.recording = True

    def stopRecording(self) -> tuple[bool, str]:
        """Arrête l'enregistrement et sauvegarde les données dans le CSV.

        Retourne (succès: bool, message: str).
        """
        self.recording = False
        if hasattr(self, '_out') and self._out is not None:
            self._out.release()
            self._out = None
        return self._process_and_save()

    # ── Interne ───────────────────────────────────────────────────────────────

    def _detect(self, frame: np.ndarray) -> tuple | None:
        """ROI si bille connue, frame entier sinon. Fallback sur frame entier si ROI échoue."""
        if self._last_center is not None:
            roi, (ox, oy) = self._get_roi(frame)
            c = self._detector.find(roi)
            if c is not None:
                return (c[0] + ox, c[1] + oy)
            # Bille sortie du ROI → recherche sur le frame complet
        return self._detector.find(frame)

    def _get_roi(self, frame: np.ndarray) -> tuple[np.ndarray, tuple[int, int]]:
        h, w = frame.shape[:2]
        cx, cy = self._last_center  # type: ignore[misc]
        m = self._roi_margin
        x1, y1 = max(0, cx - m), max(0, cy - m)
        x2, y2 = min(w, cx + m), min(h, cy + m)
        return frame[y1:y2, x1:x2], (x1, y1)

    def _process_and_save(self) -> tuple[bool, str]:
        """Calcule les vitesses et écrit dans le CSV de tracking."""
        positions = self._recording_positions
        self._recording_positions = []
        self._frame_count = 0

        if not self._csv_path:
            return False, "Aucun fichier CSV configuré"
        if len(positions) < 2:
            return False, f"Pas assez de données ({len(positions)} position(s) détectée(s))"

        try:
            w = self.width  or 960
            h = self.height or 540
            pa = PositionsAnalytics(
                ballPositions=positions,
                width=w, height=h,
                fps=self.fps,
                realWidth=self._real_width,
                realHeight=self._real_height,
            )
            pa.calculateSpeed()
            data = pa.getBallPositionsWithSpeed
            if not data:
                return False, "Aucune donnée de vitesse calculée"

            dw = DataWriter(self._csv_path)
            dw.appendData(data)
            return True, f"{len(data)} positions sauvegardées (expID {dw.expID})"
        except Exception as exc:
            return False, f"Erreur : {exc}"


if __name__ == '__main__':
    lt = LiveTracking(ballColor=[204, 114, 234], videoSource=0)
    lt.openVideo()
    for _ in range(300):
        frame = lt.readFrame()
        if frame is None:
            break
        cv2.imshow("Live Tracking", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    lt.releaseVideo()
