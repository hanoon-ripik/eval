#!/usr/bin/env python3
"""
Batch inference script for pipe counting
Runs main.py for all videos in a specified folder
"""

import os
import sys
import subprocess
import glob
from pathlib import Path

# Configuration parameters (set these at the top)
CONFIG = "ccm1"  # Camera configuration file
CLIENT_ID = "esldip-local"  # Client ID for SQS
PRODUCE = "debug"  # Produce to debug or SQS
FOLDER_PATH = "/Users/hanoon/Documents/eval/misc/fragments/00000000017000000"  # Folder containing videos

# Video file extensions to process
VIDEO_EXTENSIONS = [".mp4", ".avi", ".mov", ".mkv", ".flv", ".wmv", ".webm"]

def find_videos(folder_path):
    """Find all video files in the specified folder"""
    video_files = []
    
    if not os.path.exists(folder_path):
        print(f"❌ Error: Folder '{folder_path}' does not exist!")
        return []
    
    for ext in VIDEO_EXTENSIONS:
        pattern = os.path.join(folder_path, f"*{ext}")
        video_files.extend(glob.glob(pattern))
    
    # Sort the files for consistent processing order
    video_files.sort()
    
    return video_files

def run_main_for_video(video_path, config, client_id, produce):
    """Run main.py for a single video file"""
    try:
        cmd = [
            sys.executable, "main.py",
            "-c", config,
            "--clientId", client_id,
            "--produce", produce,
            "--video-path", video_path
        ]
        
        print(f"\n{'='*60}")
        print(f"🎬 Processing: {os.path.basename(video_path)}")
        print(f"📁 Full path: {video_path}")
        print(f"⚙️  Config: {config}")
        print(f"🔧 Command: {' '.join(cmd)}")
        print(f"{'='*60}")
        
        # Run the command and capture output
        result = subprocess.run(cmd, capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        if result.returncode == 0:
            print(f"✅ Successfully processed: {os.path.basename(video_path)}")
            if result.stdout:
                print("📤 Output:")
                print(result.stdout)
        else:
            print(f"❌ Error processing: {os.path.basename(video_path)}")
            if result.stderr:
                print("🚨 Error details:")
                print(result.stderr)
            if result.stdout:
                print("📤 Output:")
                print(result.stdout)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ Exception while processing {video_path}: {str(e)}")
        return False

def main():
    """Main function to process all videos in the folder"""
    print(f"🚀 Starting batch inference for pipe counting")
    print(f"📁 Folder: {FOLDER_PATH}")
    print(f"⚙️  Config: {CONFIG}")
    print(f"🆔 Client ID: {CLIENT_ID}")
    print(f"🔧 Produce: {PRODUCE}")
    
    # Find all video files
    video_files = find_videos(FOLDER_PATH)
    
    if not video_files:
        print(f"❌ No video files found in folder: {FOLDER_PATH}")
        print(f"📋 Looking for extensions: {', '.join(VIDEO_EXTENSIONS)}")
        return
    
    print(f"\n📊 Found {len(video_files)} video file(s) to process:")
    for i, video in enumerate(video_files, 1):
        print(f"   {i}. {os.path.basename(video)}")
    
    # Process each video
    successful = 0
    failed = 0
    
    for i, video_path in enumerate(video_files, 1):
        print(f"\n📹 Processing video {i}/{len(video_files)}")
        
        success = run_main_for_video(video_path, CONFIG, CLIENT_ID, PRODUCE)
        
        if success:
            successful += 1
        else:
            failed += 1
    
    # Final summary
    print(f"\n{'='*60}")
    print(f"📊 BATCH PROCESSING COMPLETE")
    print(f"{'='*60}")
    print(f"✅ Successfully processed: {successful} videos")
    print(f"❌ Failed to process: {failed} videos")
    print(f"📁 Total videos: {len(video_files)}")
    
    if failed > 0:
        print(f"⚠️  Please check the error messages above for failed videos")
    else:
        print(f"🎉 All videos processed successfully!")
    
    print(f"📄 Check output.json for combined results")

if __name__ == "__main__":
    main()
