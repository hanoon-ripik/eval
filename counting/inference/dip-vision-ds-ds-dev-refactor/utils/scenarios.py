from typing import Tuple, Optional, Any
from utils.diameter_handler import DiameterHandler
from utils.logging import logger
import numpy as np

class PipeCounter:

    def __init__(self, cross_line: int, camera_id: str) -> None:
        
        self.cross_line : int = cross_line
        self.pipes_on_right : set = set()
        self.curr_pipe_on_line : int = -1
        self.curr_pipe_on_line_count : int = 0
        self.camera_id = camera_id
        
    def process(self, foc_tracker_id: int, box_corner_x1: int, box_corner_x2: int, mask: Any, frame: Any, dia_handler: DiameterHandler) -> Tuple[bool, Optional[str], Optional[int]]:

        if box_corner_x1 < self.cross_line and box_corner_x2 > self.cross_line and foc_tracker_id:
            if self.curr_pipe_on_line != foc_tracker_id:
                self.curr_pipe_on_line = foc_tracker_id
                self.curr_pipe_on_line_count = 0

            self.curr_pipe_on_line_count += 1

            mask[:, :int(frame.shape[1] * 0.5) - 1] = False
            mask[:, int(frame.shape[1] * 0.5) + 1:] = False
            mask_box = mask.astype(int)
            mask_box = mask_box[:, ~np.all(mask_box == 0, axis=0)]
            mask_box = mask_box[~np.any(mask_box == 0, axis=1)]
            pipe_dia_pixels = mask_box.shape[0] if mask_box.shape[0] else 0
            if dia_handler.handler_type == 'DICT':
                dia_handler.add(pipe_dia_pixels, foc_tracker_id)
                mediandia = dia_handler.px_to_mm(dia_handler.non_zero_median(), foc_tracker_id)
            else:
                dia_handler.add(pipe_dia_pixels)
                mediandia = dia_handler.px_to_mm(dia_handler.non_zero_median(), foc_tracker_id)

            if self.curr_pipe_on_line_count > 2 and self.curr_pipe_on_line in self.pipes_on_right:
                return True, self.curr_pipe_on_line, mediandia
            
        if box_corner_x1 > self.cross_line and box_corner_x2 > self.cross_line and foc_tracker_id:
            self.pipes_on_right.add(foc_tracker_id)

        return False, None, None