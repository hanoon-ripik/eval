#!/usr/bin/env python3
"""
Test script to verify the DIP vision system works with local video files
"""

import sys
import os

# Add the current directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_rtsp_reader():
    """Test the RTSPReader with local video file"""
    from rtsp.reader import RTSPReader
    import time
    
    print("Testing RTSPReader with local video file...")
    
    # Test with local video file
    reader = RTSPReader("0.mp4")
    
    # Give it some time to initialize
    time.sleep(2)
    
    # Try to read a few frames
    for i in range(5):
        ret, frame = reader.read()
        if ret and frame is not None:
            print(f"Frame {i+1}: Successfully read frame of shape {frame.shape}")
        else:
            print(f"Frame {i+1}: Failed to read frame")
        time.sleep(1)
    
    reader.release()
    print("RTSPReader test completed.")

def test_config_loading():
    """Test config loading without queue-url"""
    from data.config import read_cam_config
    
    print("Testing config loading...")
    
    try:
        config = read_cam_config("ccm1")
        print("Config loaded successfully:")
        print(f"  Camera ID: {config['cam-id']}")
        print(f"  Connection String: {config['conn-string']}")
        print(f"  Analysis Time Delta: {config['analysis-time-delta']}")
        print(f"  Queue URL present: {'queue-url' in config}")
        return config
    except Exception as e:
        print(f"Error loading config: {e}")
        return None

if __name__ == "__main__":
    print("DIP Vision Local Video Test")
    print("=" * 40)
    
    # Test config loading
    config = test_config_loading()
    print()
    
    # Test RTSPReader if config loaded successfully
    if config:
        test_rtsp_reader()
    
    print("\nTest completed!")
