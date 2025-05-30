import threading
import cv2
from cv2.typing import MatLike
from typing import Optional, Tuple
from utils.dip_utils import log_camera_down, log_camera_reconnected

class RTSPReader(threading.Thread):
    def __init__(self, cam_uri: str):        
        self.cam_uri : str = cam_uri

        self.camera : cv2.VideoCapture = cv2.VideoCapture(self.cam_uri)

        self.__fps : Optional[float] = None
        self.__frame_height : Optional[float] = None
        self.__frame_width : Optional[float] = None

        self.frame : Optional[MatLike] = None

        self.super_killed : bool = False

        super().__init__()
        self.start()
        
        # keeps track of whether last stored frame was read
        self.__new_frame_available : bool = False

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
            try:
                self.camera = cv2.VideoCapture(self.cam_uri)
                self.__camera_loop()
                log_camera_down()
            except Exception as _:
                pass

    def __camera_loop(self) -> None:
        print('Camera loop starting')
        log_camera_reconnected()
        while self.camera.isOpened():
            try:
                if self.super_killed:
                    break

                ret, self.frame = self.camera.read()

                if not ret:
                    break

                self.__new_frame_available = True

            except cv2.error as e:
                print(f"Error reading frame: {e}")
                break

        # avoid multiple connections
        self.camera.release()
        print('Feed dropped.')

    def read(self) -> Tuple[bool, Optional[MatLike]]:
        
        if self.frame is None:
            return False, self.frame

        if not self.__new_frame_available:
            return False, None

        self.__new_frame_available = False
        
        return True, self.frame

    def isOpened(self) -> bool:

        return self.camera.isOpened()

    def release(self) -> None:

        self.super_killed = True