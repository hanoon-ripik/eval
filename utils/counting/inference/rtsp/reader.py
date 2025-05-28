import threading
import cv2
from typing import Optional, Tuple, Any

class RTSPReader(threading.Thread):
    def __init__(self, cam_uri: str):
        self.cam_uri: str = cam_uri
        self.camera: cv2.VideoCapture = cv2.VideoCapture(self.cam_uri)

        self.__fps: Optional[float] = None
        self.__frame_height: Optional[float] = None
        self.__frame_width: Optional[float] = None

        self.frame: Optional[Any] = None
        self.super_killed: bool = False

        self.__new_frame_available: bool = False

        super().__init__()
        self.start()

    @property
    def fps(self) -> Optional[float]:
        self.__fps = self.camera.get(cv2.CAP_PROP_FPS) if self.isOpened() else None
        return self.__fps

    @property
    def frame_height(self) -> Optional[float]:
        self.__frame_height = self.camera.get(cv2.CAP_PROP_FRAME_HEIGHT) if self.isOpened() else None
        return self.__frame_height

    @property
    def frame_width(self) -> Optional[float]:
        self.__frame_width = self.camera.get(cv2.CAP_PROP_FRAME_WIDTH) if self.isOpened() else None
        return self.__frame_width

    def run(self) -> None:
        while not self.super_killed:
            if not self.camera.isOpened():
                break
            ret, frame = self.camera.read()
            if not ret:
                break
            self.frame = frame
            self.__new_frame_available = True

    def read(self) -> Tuple[bool, Optional[Any]]:
        if self.frame is None or not self.__new_frame_available:
            return False, None
        self.__new_frame_available = False
        return True, self.frame

    def isOpened(self) -> bool:
        return self.camera.isOpened()

    def release(self) -> None:
        self.super_killed = True
        self.camera.release()