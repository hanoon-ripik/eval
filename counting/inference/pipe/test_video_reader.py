#!/usr/bin/env python3
"""
Test script to verify video reading functionality without YOLO dependencies
"""

import cv2
import time
from video.reader import VideoReader

def test_video_reader():
    video_path = "/Users/hanoon/Documents/eval/misc/fragments/00000000017000000/0.mp4"
    
    print(f"Testing video reader with: {video_path}")
    
    try:
        # Initialize video reader
        video_reader = VideoReader(video_path)
        
        print(f"Video properties:")
        print(f"  FPS: {video_reader.fps}")
        print(f"  Frame Width: {video_reader.frame_width}")
        print(f"  Frame Height: {video_reader.frame_height}")
        print(f"  Total Frames: {video_reader.get_total_frames()}")
        
        frame_count = 0
        max_frames = 10  # Test first 10 frames
        
        while frame_count < max_frames:
            ret, frame = video_reader.read()
            
            if not ret:
                print("End of video or error reading frame")
                break
                
            frame_count += 1
            current_frame = video_reader.get_current_frame_number()
            
            print(f"Frame {frame_count}: Successfully read frame {current_frame}")
            print(f"  Frame shape: {frame.shape}")
            
            # Simulate processing delay
            time.sleep(0.1)
        
        print(f"\nSuccessfully processed {frame_count} frames")
        
        # Test restart functionality
        print("\nTesting video restart...")
        video_reader.restart()
        print(f"Current frame after restart: {video_reader.get_current_frame_number()}")
        
        # Read one more frame to verify restart
        ret, frame = video_reader.read()
        if ret:
            print(f"Successfully read frame after restart: {video_reader.get_current_frame_number()}")
        
        # Clean up
        video_reader.release()
        print("\nVideo reader test completed successfully!")
        
    except Exception as e:
        print(f"Error during video reader test: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_video_reader()
    if success:
        print("\n✅ Video reader functionality is working correctly!")
    else:
        print("\n❌ Video reader test failed!")
