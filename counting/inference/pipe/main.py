import torch
from typing import List, Tuple, Dict
import argparse
from ultralytics import YOLO
import supervision as sv
import utils.supervision_mods as svm
import sys
import time
from datetime import datetime
import cv2

from video.reader import VideoReader

from utils.logging import logger
from utils.dip_utils import cam_to_ccm_mapping, get_ist_timestamp, get_shift, log_camera_down, log_camera_reconnected
from utils.scenarios import PipeCounter
from utils.diameter_handler import DiameterHandler
from data.config import read_cam_config

class DIP:

    def __init__(self, config: Dict, clientId: str, produce: str, video_path: str) -> None:
        
        # Temporarily patch torch.load to use weights_only=False for YOLO model loading
        import torch
        original_load = torch.load
        torch.load = lambda *args, **kwargs: original_load(*args, **kwargs, weights_only=False)
        
        try:
            self.model : YOLO = YOLO(config['ds-info']['pipe-model'])
        finally:
            # Restore original torch.load
            torch.load = original_load
        
        self.LINE_START : sv.Point = sv.Point(
            config['ds-info']['line-start'][0],
            config['ds-info']['line-start'][1]
        )
        self.LINE_END : sv.Point = sv.Point(
            config['ds-info']['line-end'][0],
            config['ds-info']['line-end'][1]
        )

        self.cross_point : int = config['ds-info']['line-start'][0]

        self.cap : VideoReader = VideoReader(video_path)
        self.camera_id : str = config['cam-id']

        self.clientId : str = clientId
        self.produce : str = produce

        self.last_analysis_timestamp : float = time.time()
        self.time_delta : float = config['analysis-time-delta']
        self.last_push_timestamp : float = time.time()
        self.push_delta : float = 2

        self.pipe_counter = PipeCounter(self.cross_point, self.camera_id)

        self.dia_handler : DiameterHandler = DiameterHandler(config['ds-info']['dia-handler'], config['ds-info']['ratios'], config['ds-info']['possible_dias'])
        self.this_shift_ids = set()

        self.cropping = config['ds-info']['cropping']

    def init_response(self) -> Dict:

        return {
            'imageId': None,
            'createdAt': get_ist_timestamp(),
            'cameraId': '',
            'originalImage': '',
            'annotatedImage': '',
            'pipeData': [],
            'clientId': self.clientId,
            'material': "dipcounter"
        }
    
    def process(self) -> None:
        logger.info("Starting analysis for camera: {}".format(self.camera_id))

        line_counter = svm.LineZone(start=self.LINE_START, end=self.LINE_END)
        line_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=2, text_scale=1)
        box_annotator = sv.BoxAnnotator(
            thickness=2
        )
        label_annotator = sv.LabelAnnotator()

        mask_annotator = sv.MaskAnnotator()

        script_start_time = get_ist_timestamp()
        script_start_shift = get_shift()

        response = self.init_response()

        while True:
            ret, frame = self.cap.read()
            if not ret:
                # End of video - restart or break
                print("End of video reached. Restarting from beginning...")
                self.cap.restart()
                time.sleep(1)
                continue

            if time.time() - self.last_analysis_timestamp < self.time_delta:
                continue
            self.last_analysis_timestamp = time.time()

            response['originalImage'] = frame

            frame = frame[self.cropping['y'][0]:self.cropping['y'][1], self.cropping['x'][0]:self.cropping['x'][1]]

            timestamp_curr = get_ist_timestamp()

            result = self.model.track(frame, persist=True, retina_masks=True, device='cpu')[0]
            shift = get_shift()

            line_annotator.custom_in_text = f"Shift {shift} in"
            line_annotator.custom_out_text = f"Shift {shift} out"

            detections = sv.Detections.from_ultralytics(result)

            if result.boxes.id is not None:
                detections.tracker_id = result.boxes.id.cpu().numpy().astype(int)

            labels = [
                f"{tracker_id} {self.model.model.names[class_id]} {confidence:0.2f}"
                for xyxy, mask, confidence, class_id, tracker_id, data
                in detections
            ]

            frame = mask_annotator.annotate(
                scene=frame,
                detections=detections
            )

            frame = box_annotator.annotate(
                scene=frame,
                detections=detections
            )

            frame = label_annotator.annotate(
                scene=frame,
                detections=detections,
                labels=labels
            )

            line_annotator.annotate(frame=frame, line_counter=line_counter)

            response['annotatedImage'] = frame

            if len(detections):
                mask = result.masks.cpu().numpy()
                masks = mask.data.astype(bool)

                for i in range(len(detections)):
                    mask_copy = masks[i].copy()

                    box_corner_x1 = int(detections.xyxy[i][0])
                    box_corner_x2 = int(detections.xyxy[i][2])
                    foc_tracker_id = detections[i].tracker_id[0] if detections[i].tracker_id is not None else None

                    ret, pipe_id, diaMM = self.pipe_counter.process(foc_tracker_id, box_corner_x1, box_corner_x2, mask_copy, frame, self.dia_handler)

                    if ret:
                        if pipe_id not in self.this_shift_ids:
                            line_counter.in_count+=1
                            response['pipeData'].append(
                                {
                                    'pipeId': f'{cam_to_ccm_mapping[self.camera_id]}_{pipe_id}_{get_ist_timestamp()}',
                                    'medianDiaMM': diaMM
                                }
                            )
                            self.this_shift_ids.add(pipe_id)

            else:
                self.dia_handler.clear()

            logger.info("Analysis done")

            if script_start_shift != shift:
                logger.info(f"changing shift from {script_start_shift} to {shift} at {datetime.fromtimestamp(get_ist_timestamp())}")
                script_start_shift = shift
                line_counter.in_count = 1
                line_counter.out_count = 0
                self.this_shift_ids = set()

            if time.time() - self.last_push_timestamp < self.push_delta:
                continue

            response['imageId'] = f'cam{self.camera_id}_{timestamp_curr}'
            response['createdAt'] = timestamp_curr
            response['cameraId'] = cam_to_ccm_mapping[self.camera_id]

            # Print the output instead of sending to SQS
            print("\n" + "="*50)
            print(f"ANALYSIS RESULT - Frame {self.cap.get_current_frame_number()}")
            print("="*50)
            print(f"Camera ID: {response['cameraId']}")
            print(f"Image ID: {response['imageId']}")
            print(f"Created At: {response['createdAt']}")
            print(f"Client ID: {response['clientId']}")
            print(f"Material: {response['material']}")
            print(f"Line Counter In: {line_counter.in_count}")
            print(f"Line Counter Out: {line_counter.out_count}")
            
            if response['pipeData']:
                print("Pipe Data:")
                for pipe in response['pipeData']:
                    print(f"  - Pipe ID: {pipe['pipeId']}")
                    print(f"    Median Diameter (MM): {pipe['medianDiaMM']}")
            else:
                print("No pipes detected in this frame")
            
            print("="*50)
            
            response = self.init_response()
            logger.info("Data processed and printed")
            self.last_push_timestamp = time.time()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runner script for DIP.')
    parser.add_argument('-c', '--config', type=str, help='Path to the config file for the camera. Exact path or path relative to \'cfg/camera-cfg\' folder.', required=True)
    parser.add_argument('--clientId', type=str, default='esldip-local', help='client id for sqs')
    parser.add_argument('--produce', type=str, default='debug', help='produce to debug or SQS')
    parser.add_argument('--video-path', type=str, default='/Users/hanoon/Documents/eval/misc/fragments/00000000017000000/0.mp4', help='Path to the video file to process')

    args = parser.parse_args()
    cfg_file = args.config

    # reading config file
    try:
        config = read_cam_config(cfg_file)
    except Exception as e:
        logger.error(f'Could not find config file {cfg_file}. Either give the exact path of the file, or the path relative to the \'cfg/camera-cfg\' directory.')
        sys.exit()

    print(f"Processing video: {args.video_path}")
    obj = DIP(config, args.clientId, args.produce, args.video_path)

    while True:
        try:
            obj.process()
        except Exception as e:
            logger.error(e)
        logger.info("restarting")

# python main.py -c ccm1 --produce SQS