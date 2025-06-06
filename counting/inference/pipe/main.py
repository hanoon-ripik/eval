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
import json
import os
import numpy as np

import cv2

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

        self.cap : cv2.VideoCapture = cv2.VideoCapture(video_path)
        self.camera_id : str = config['cam-id']
        self.video_path : str = video_path

        self.clientId : str = clientId
        self.produce : str = produce

        self.last_analysis_timestamp : float = time.time()
        self.time_delta : float = 0 # 6 FPS inference rate (0.167 seconds)
        self.last_push_timestamp : float = time.time()
        self.push_delta : float = 2

        self.pipe_counter = PipeCounter(self.cross_point, self.camera_id)

        self.dia_handler : DiameterHandler = DiameterHandler(config['ds-info']['dia-handler'], config['ds-info']['ratios'], config['ds-info']['possible_dias'])
        self.this_shift_ids = set()

        # Initialize JSON tracking for unique YOLO IDs
        self.output_json_path = "output_2.json"
        self.saved_yolo_ids = set()
        self.pipe_detections = []  # Store pipe info for final JSON
        self.load_existing_json()

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
    
    def load_existing_json(self):
        """Load existing JSON file and populate saved_yolo_ids set"""
        if os.path.exists(self.output_json_path):
            try:
                with open(self.output_json_path, 'r') as f:
                    data = json.load(f)
                
                # Handle both old format (single object) and new format (array)
                if isinstance(data, dict):
                    # Old format - single object
                    if 'pipe_info' in data:
                        for pipe in data['pipe_info']:
                            if 'yolo_id' in pipe:
                                self.saved_yolo_ids.add(pipe['yolo_id'])
                elif isinstance(data, list):
                    # New format - array of objects
                    video_filename = os.path.basename(self.video_path)
                    # Find entry for current video+camera combination
                    for entry in data:
                        if entry.get("video") == video_filename and entry.get("camera") == self.camera_id:
                            if 'pipe_info' in entry:
                                for pipe in entry['pipe_info']:
                                    if 'yolo_id' in pipe:
                                        self.saved_yolo_ids.add(pipe['yolo_id'])
                            break
                
                print(f"Loaded existing JSON with {len(self.saved_yolo_ids)} unique YOLO IDs for this video+camera")
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading existing JSON: {e}. Starting with empty file.")
                self.saved_yolo_ids = set()
        else:
            print("No existing output.json found. Starting fresh.")

    def save_pipe_detection_to_json(self, yolo_id: int, video_time: str, frame_number: int, confidence: float):
        """Add pipe detection with YOLO ID to internal list"""
        # Only save if YOLO ID hasn't been saved before
        if yolo_id not in self.saved_yolo_ids:
            # Create new pipe info record
            pipe_info = {
                "yolo_id": yolo_id,
                "confidence": float(confidence)
            }
            
            # Add to our internal list
            self.pipe_detections.append(pipe_info)
            
            # Add to our tracking set
            self.saved_yolo_ids.add(yolo_id)
            
            print(f"💾 Added YOLO ID {yolo_id} to pipe detections")
            return True
        return False

    def save_final_json(self):
        """Save final JSON with new format: video, camera, total_pipes, pipe_info"""
        import os
        video_filename = os.path.basename(self.video_path)
        
        # Create new entry for this video+camera combination
        new_entry = {
            "video": video_filename,
            "camera": self.camera_id,
            "total_pipes": len(self.pipe_detections),
            "pipe_info": self.pipe_detections
        }
        
        # Load existing data if file exists
        if os.path.exists(self.output_json_path):
            try:
                with open(self.output_json_path, 'r') as f:
                    existing_data = json.load(f)
                
                # If existing data is a single object (old format), convert to list
                if isinstance(existing_data, dict):
                    existing_data = [existing_data]
                elif not isinstance(existing_data, list):
                    existing_data = []
                    
            except (json.JSONDecodeError, KeyError) as e:
                print(f"Error loading existing JSON: {e}. Starting with new data.")
                existing_data = []
        else:
            existing_data = []
        
        # Check if entry for this video+camera combination already exists
        updated = False
        for i, entry in enumerate(existing_data):
            if entry.get("video") == video_filename and entry.get("camera") == self.camera_id:
                # Update existing entry
                existing_data[i] = new_entry
                updated = True
                print(f"📄 Updated existing entry for {video_filename} + Camera {self.camera_id}")
                break
        
        # If no existing entry found, add new one
        if not updated:
            existing_data.append(new_entry)
            print(f"📄 Added new entry for {video_filename} + Camera {self.camera_id}")
        
        # Save updated data
        with open(self.output_json_path, 'w') as f:
            json.dump(existing_data, f, indent=2)
        
        print(f"📄 Final JSON saved to {self.output_json_path}")
        print(f"   Video: {video_filename}")
        print(f"   Camera: {self.camera_id}")
        print(f"   Total unique pipes detected: {len(self.pipe_detections)}")
        print(f"   Total entries in JSON: {len(existing_data)}")
    
    def process(self) -> None:
        logger.info("Starting analysis for camera: {}".format(self.camera_id))

        line_counter = svm.LineZone(start=self.LINE_START, end=self.LINE_END)
        line_annotator = sv.LineZoneAnnotator(thickness=2)
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
                # End of video - exit cleanly
                print("End of video reached. Exiting...")
                break

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
            else:
                pass  # No tracker IDs available yet

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

            # Only print when pipes are detected
            if len(detections) > 0:
                # Calculate video timestamp based on frame number and FPS
                current_frame = int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))
                video_fps = self.cap.get(cv2.CAP_PROP_FPS)  # Get video FPS using cv2 property
                video_timestamp_seconds = current_frame / video_fps
                
                # Format as MM:SS.mmm
                minutes = int(video_timestamp_seconds // 60)
                seconds = video_timestamp_seconds % 60
                video_time_formatted = f"{minutes:02d}:{seconds:06.3f}"
                
                print(f"\n🔍 PIPE DETECTED - Video Time: {video_time_formatted} - Frame {current_frame}")
                print(f"   Detections: {len(detections)} pipe(s)")
                for i in range(len(detections)):
                    if hasattr(detections, 'tracker_id') and detections.tracker_id is not None and i < len(detections.tracker_id):
                        tracker_id = detections.tracker_id[i]
                    else:
                        tracker_id = "N/A"
                    
                    if hasattr(detections, 'confidence') and detections.confidence is not None and i < len(detections.confidence):
                        confidence = detections.confidence[i]
                    else:
                        confidence = "N/A"
                    
                    print(f"   Pipe {i+1}: YOLO ID={tracker_id}, Confidence={confidence:.2f}" if isinstance(confidence, (int, float)) else f"   Pipe {i+1}: YOLO ID={tracker_id}, Confidence={confidence}")
                    
                    # Save pipe detection to JSON if we have valid tracker_id and confidence
                    if tracker_id != "N/A" and confidence != "N/A" and isinstance(tracker_id, (int, float, np.int64, np.float32)) and isinstance(confidence, (int, float, np.int64, np.float32)):
                        self.save_pipe_detection_to_json(int(tracker_id), video_time_formatted, current_frame, float(confidence))
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

            # Only print analysis results when pipes are detected
            if response['pipeData']:
                print("\n" + "="*50)
                print(f"ANALYSIS RESULT - Frame {int(self.cap.get(cv2.CAP_PROP_POS_FRAMES))}")
                print("="*50)
                print(f"Camera ID: {response['cameraId']}")
                print(f"Image ID: {response['imageId']}")
                print(f"Created At: {response['createdAt']}")
                print(f"Client ID: {response['clientId']}")
                print(f"Material: {response['material']}")
                print(f"Line Counter In: {line_counter.in_count}")
                print(f"Line Counter Out: {line_counter.out_count}")
                
                print("Pipe Data:")
                for pipe in response['pipeData']:
                    print(f"  - Pipe ID: {pipe['pipeId']}")
                    print(f"    Median Diameter (MM): {pipe['medianDiaMM']}")
                
                print("="*50)
                logger.info("Data processed and printed")
            
            response = self.init_response()
            self.last_push_timestamp = time.time()

        # Save final JSON at the end of processing
        self.save_final_json()



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

    try:
        obj.process()
    except Exception as e:
        logger.error(e)
    
    print("Video processing completed.")

# python main.py -c ccm1 --produce SQS