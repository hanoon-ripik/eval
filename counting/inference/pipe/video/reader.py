import cv2
from cv2.typing import MatLike
from typing import Optional, Tuple

class VideoReader:
    def __init__(self, video_path: str):        
        self.video_path: str = video_path
        self.camera: cv2.VideoCapture = cv2.VideoCapture(self.video_path)
        
        self.__fps: Optional[float] = None
        self.__frame_height: Optional[float] = None
        self.__frame_width: Optional[float] = None
        
        # Check if video was opened successfully
        if not self.camera.isOpened():
            raise ValueError(f"Error opening video file: {video_path}")
        
        print(f"Video loaded successfully: {video_path}")
        print(f"Total frames: {int(self.camera.get(cv2.CAP_PROP_FRAME_COUNT))}")
        print(f"FPS: {self.camera.get(cv2.CAP_PROP_FPS)}")

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

    def read(self) -> Tuple[bool, Optional[MatLike]]:
        """Read the next frame from the video"""
        if not self.camera.isOpened():
            return False, None
            
        ret, frame = self.camera.read()
        
        if not ret:
            # End of video, optionally restart from beginning
            print("End of video reached")
            return False, None
            
        return True, frame

    def isOpened(self) -> bool:
        return self.camera.isOpened()

    def release(self) -> None:
        """Release the video capture"""
        if self.camera.isOpened():
            self.camera.release()
        print('Video reader released.')

    def restart(self) -> None:
        """Restart video from the beginning"""
        self.camera.set(cv2.CAP_PROP_POS_FRAMES, 0)
        print("Video restarted from beginning")

    def get_current_frame_number(self) -> int:
        """Get current frame number"""
        return int(self.camera.get(cv2.CAP_PROP_POS_FRAMES))

    def get_total_frames(self) -> int:
        """Get total number of frames in the video"""
        return int(self.camera.get(cv2.CAP_PROP_FRAME_COUNT))
