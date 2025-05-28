# DIP Vision Local Video Modifications

## Changes Made

### 1. RTSPReader Modifications (`rtsp/reader.py`)
- Added detection for local video files vs RTSP streams
- Modified the camera loop to handle local video files:
  - For local files: loops video when it reaches the end
  - For RTSP: maintains original retry logic
  - Removed camera reconnection logging for local files

### 2. Main Application Changes (`main.py`)
- Removed S3/SQS import dependency
- Replaced `push_data_to_sqs()` with console output printing
- Added detailed formatted output showing:
  - Timestamp and camera information
  - Detected pipe data with IDs and diameters
  - Shift summary with pipe counts
- Removed queue_url dependency from initialization

### 3. Configuration Updates
- `cfg/camera-cfg/ccm1.yaml`: 
  - Changed `conn-string` from RTSP URL to `0.mp4`
  - Commented out `queue-url` field
- `cfg/camera-cfg/ccm6.yaml`:
  - Changed `conn-string` from RTSP URL to `0.mp4`
  - Commented out `queue-url` field

### 4. Video File Setup
- Copied existing video file to `0.mp4` in the DIP vision directory
- This video will be used as input instead of RTSP stream

## How to Use

### Running with Local Video
```bash
cd /Users/hanoon/Documents/eval/utils/counting/inference/dip-vision-ds-ds-dev-refactor
python main.py -c ccm1 --produce SQS
```

### Expected Output
The system will now:
1. Load the local video file `0.mp4` instead of connecting to RTSP
2. Process frames and detect pipes as before
3. Print detailed analysis results to console instead of pushing to S3/SQS
4. Loop the video continuously for continuous analysis

### Output Format
```
==================================================
DIP ANALYSIS OUTPUT
==================================================
Timestamp: 2025-05-28 10:30:45.123456
Camera ID: CCM1
Image ID: cam208_1740123456.789
Client ID: esldip-local
Material: dipcounter
Number of pipes detected: 2

Pipe Data:
  Pipe 1:
    ID: CCM1_12345_1740123456
    Diameter (mm): 150.5
  Pipe 2:
    ID: CCM1_12346_1740123456
    Diameter (mm): 200.2

Shift A Summary:
  Total pipes counted this shift: 15
  Out count: 0
==================================================
```

### Key Benefits
1. **No Cloud Dependencies**: System works completely offline
2. **Reproducible Testing**: Same video input for consistent testing
3. **Console Monitoring**: Real-time output visible in terminal
4. **Continuous Operation**: Video loops automatically
5. **Original Logic Preserved**: All counting and detection logic unchanged

### Files Modified
- `rtsp/reader.py` - Video input handling
- `main.py` - Output handling and S3 removal
- `cfg/camera-cfg/ccm1.yaml` - Configuration
- `cfg/camera-cfg/ccm6.yaml` - Configuration
- Added `0.mp4` - Local video file
- Added `test_local_video.py` - Test script

### Testing
Run the test script to verify components work:
```bash
python test_local_video.py
```

This will test:
- Configuration loading without queue-url
- RTSPReader with local video file
- Frame reading capability
