from typing import List, Tuple, Dict
import argparse
import torch
import torch
try:
    from ultralytics.nn.tasks import SegmentationModel, DetectionModel, ClassificationModel
    torch.serialization.add_safe_globals([SegmentationModel, DetectionModel, ClassificationModel])
except ImportError:
    pass
from ultralytics import YOLO
import supervision as sv
import utils.supervision_mods as svm
import sys
import time
from datetime import datetime
import cv2
import json
from rtsp.reader import RTSPReader

from utils.logging import logger
from utils.dip_utils import cam_to_ccm_mapping, get_ist_timestamp, get_shift, log_camera_down, log_camera_reconnected
from utils.scenarios import PipeCounter
from utils.diameter_handler import DiameterHandler
from data.config import read_cam_config
# Removed S3 import
# from utils.s3util import push_data_to_sqs

class DIP:

    def __init__(self, config: Dict, clientId: str, produce: str) -> None:
        model_path = config['ds-info']['pipe-model']
        original_load = torch.load
        def load_with_weights_only_false(f, map_location=None, pickle_module=None, weights_only=None, **kwargs):
            return original_load(f, map_location=map_location, pickle_module=pickle_module, weights_only=False, **kwargs)
        torch.load = load_with_weights_only_false
        try:
            print(f"Loading custom pipe detection model: {model_path}")
            self.model : YOLO = YOLO(model_path)
            print("Custom pipe detection model loaded successfully!")
        except Exception as e:
            print(f"Failed to load custom model: {e}")
            print("Falling back to generic YOLO model...")
            self.model : YOLO = YOLO('yolov8n-seg.pt')
        finally:
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

        self.cap : RTSPReader = RTSPReader(config['conn-string'])
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
            'clientId': "esldip-local",
            'material': "dipcounter"
        }
    
    def process(self) -> None:
        logger.info("Starting analysis for camera: {}".format(self.camera_id))

        line_counter = svm.LineZone(start=self.LINE_START, end=self.LINE_END)
        line_annotator = sv.LineZoneAnnotator(thickness=2, text_thickness=2, text_scale=1)
        box_annotator = sv.BoxAnnotator(
            thickness=2
        )

        mask_annotator = sv.MaskAnnotator()

        script_start_time = get_ist_timestamp()
        script_start_shift = get_shift()

        response = self.init_response()

        while True:
            ret, frame = self.cap.read()
            if not ret:
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

            # Create labels with proper unpacking based on detection structure
            labels = []
            for i, detection in enumerate(detections):
                class_id = int(detection[3]) if len(detection) > 3 else 0
                confidence = float(detection[2]) if len(detection) > 2 else 0.0
                tracker_id = detections.tracker_id[i] if detections.tracker_id is not None and i < len(detections.tracker_id) else "N/A"
                class_name = self.model.model.names.get(class_id, "unknown")
                labels.append(f"{tracker_id} {class_name} {confidence:0.2f}")

            frame = mask_annotator.annotate(
                scene=frame,
                detections=detections
            )

            frame = box_annotator.annotate(
                scene=frame,
                detections=detections
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

            if self.produce == 'SQS':
                # Instead of pushing to S3/SQS, print the output
                print("\n" + "="*50)
                print("DIP ANALYSIS OUTPUT")
                print("="*50)
                print(f"Timestamp: {datetime.fromtimestamp(response['createdAt'])}")
                print(f"Camera ID: {response['cameraId']}")
                print(f"Image ID: {response['imageId']}")
                print(f"Client ID: {response['clientId']}")
                print(f"Material: {response['material']}")
                print(f"Number of pipes detected: {len(response['pipeData'])}")
                
                if response['pipeData']:
                    print("\nPipe Data:")
                    for i, pipe in enumerate(response['pipeData'], 1):
                        print(f"  Pipe {i}:")
                        print(f"    ID: {pipe['pipeId']}")
                        print(f"    Diameter (mm): {pipe['medianDiaMM']}")
                
                # Print summary statistics
                print(f"\nShift {shift} Summary:")
                print(f"  Total pipes counted this shift: {line_counter.in_count}")
                print(f"  Out count: {line_counter.out_count}")
                print("="*50 + "\n")
                
                response = self.init_response()
                logger.info("Data printed to console")
                self.last_push_timestamp = time.time()



if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Runner script for DIP.')
    parser.add_argument('-c', '--config', type=str, help='Path to the config file for the camera. Exact path or path relative to \'cfg/camera-cfg\' folder.', required=True)
    parser.add_argument('--clientId', type=str, default='esldip-local', help='client id for sqs')
    parser.add_argument('--produce', type=str, default='debug', help='produce to debug or SQS')

    args = parser.parse_args()
    cfg_file = args.config

    # reading config file
    try:
        config = read_cam_config(cfg_file)
    except Exception as e:
        logger.error(f'Could not find config file {cfg_file}. Either give the exact path of the file, or the path relative to the \'cfg/camera-cfg\' directory.')
        sys.exit()

    obj = DIP(config, args.clientId, args.produce)

    while True:
        try:
            obj.process()
        except Exception as e:
            logger.error(e)
        logger.info("restarting")

# python main.py -c ccm1 --produce SQS