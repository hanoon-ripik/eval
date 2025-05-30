from typing import Dict

from supervision.detection.core import Detections
from supervision.geometry.core import Point, Vector

class LineZone:
    """
    Count the number of objects that cross a line.
    """

    def __init__(self, start: Point, end: Point):
        """
        Initialize a LineCounter object.

        Attributes:
            start (Point): The starting point of the line.
            end (Point): The ending point of the line.

        """
        self.vector = Vector(start=start, end=end)
        self.tracker_state: Dict[str, bool] = {}
        self.in_count: int = 0
        self.out_count: int = 0
        # self.shift_in_count: int = 0
        # self.shift_out_count: int = 0
        # self.crossed_tracker_id = 0
        self.crossed_tracker_id = None
        self.out_crossed_tracker_id = None
        self.crossed = False
        self.reset_shift = False

    def trigger(self, detections: Detections, shift: str, script_start_shift: str):
        """
        Update the in_count and out_count for the detections that cross the line.

        Attributes:
            detections (Detections): The detections for which to update the counts.

        """
        for xyxy, _, confidence, class_id, tracker_id in detections:
            # handle detections with no tracker_id
            self.crossed = False

            if tracker_id is None:
                continue

            # we check if all four anchors of bbox are on the same side of vector
            x1, y1, x2, y2 = xyxy
            anchors = [
                Point(x=x1, y=y1),
                Point(x=x1, y=y2),
                Point(x=x2, y=y1),
                Point(x=x2, y=y2),
            ]
            triggers = [self.vector.is_in(point=anchor) for anchor in anchors]

            # detection is partially in and partially out
            if len(set(triggers)) == 2:
                continue

            tracker_state = triggers[0]
            # handle new detection
            if tracker_id not in self.tracker_state:
                self.tracker_state[tracker_id] = tracker_state
                continue

            # handle detection on the same side of the line
            if self.tracker_state.get(tracker_id) == tracker_state:
                if tracker_state:
                    self.crossed = True
                continue

            self.tracker_state[tracker_id] = tracker_state
            if tracker_state:
                self.crossed = True
                self.in_count += 1
                self.crossed_tracker_id = tracker_id
                if shift != script_start_shift:
                    self.reset_shift = True


                # self.in_count += 1
            else:
                self.out_count += 1
                self.out_crossed_tracker_id = tracker_id
                if shift != script_start_shift:
                    self.reset_shift = True
                # self.out_count += 1