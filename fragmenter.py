#!/usr/bin/env python3
"""
Video Fragmenter Script

This script fragments a video file into smaller segments based on a specified duration.
Example: A 1-hour video with 10-minute segments will create 6 fragments.
"""

import os
import subprocess
import sys
from pathlib import Path

# Configuration variables
FRAGMENT_MINUTES = 10  # Duration of each fragment in minutes
VIDEO_FILENAME = "00000000017000000.mp4"  # Input video file name

def get_video_duration(video_path):
    """Get the duration of a video file in seconds using ffprobe."""
    try:
        cmd = [
            'ffprobe', '-v', 'quiet', '-show_entries', 'format=duration',
            '-of', 'default=noprint_wrappers=1:nokey=1', video_path
        ]
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        return float(result.stdout.strip())
    except (subprocess.CalledProcessError, ValueError) as e:
        print(f"Error getting video duration: {e}")
        return None

def fragment_video(video_path, fragment_duration_minutes, output_dir="fragments"):
    """
    Fragment a video into smaller segments.
    
    Args:
        video_path (str): Path to the input video file
        fragment_duration_minutes (int): Duration of each fragment in minutes
        output_dir (str): Directory to save the fragments
    """
    # Check if input video exists
    if not os.path.exists(video_path):
        print(f"Error: Video file '{video_path}' not found!")
        return False
    
    # Get video duration
    total_duration = get_video_duration(video_path)
    if total_duration is None:
        return False
    
    # Convert fragment duration to seconds
    fragment_duration_seconds = fragment_duration_minutes * 60
    
    # Calculate number of fragments
    num_fragments = int(total_duration // fragment_duration_seconds)
    if total_duration % fragment_duration_seconds > 0:
        num_fragments += 1
    
    print(f"Video duration: {total_duration:.2f} seconds ({total_duration/60:.2f} minutes)")
    print(f"Fragment duration: {fragment_duration_minutes} minutes ({fragment_duration_seconds} seconds)")
    print(f"Number of fragments: {num_fragments}")
    
    # Get video file name without extension for folder structure
    video_name = Path(video_path).stem
    video_ext = Path(video_path).suffix
    
    # Create nested output directory: fragments/{file_name}/
    video_fragments_dir = os.path.join(output_dir, video_name)
    Path(video_fragments_dir).mkdir(parents=True, exist_ok=True)
    
    print(f"Saving fragments to: {video_fragments_dir}")
    
    # Fragment the video
    for i in range(num_fragments):
        start_time = i * fragment_duration_seconds
        output_filename = f"{i}{video_ext}"  # Named as 0.mp4, 1.mp4, 2.mp4, etc.
        output_path = os.path.join(video_fragments_dir, output_filename)
        
        # Build ffmpeg command
        cmd = [
            'ffmpeg', '-i', video_path,
            '-ss', str(start_time),
            '-t', str(fragment_duration_seconds),
            '-c', 'copy',  # Copy streams without re-encoding for speed
            '-avoid_negative_ts', 'make_zero',
            output_path
        ]
        
        print(f"Creating fragment {i}: {output_filename}")
        
        try:
            subprocess.run(cmd, check=True, capture_output=True)
            print(f"✓ Fragment {i} created successfully")
        except subprocess.CalledProcessError as e:
            print(f"✗ Error creating fragment {i}: {e}")
            return False
    
    print(f"\n✓ Video fragmentation completed! {num_fragments} fragments created in '{video_fragments_dir}' directory.")
    return True

def check_ffmpeg():
    """Check if ffmpeg is installed and available."""
    try:
        subprocess.run(['ffmpeg', '-version'], capture_output=True, check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False

def main():
    """Main function to run the video fragmenter."""
    print("Video Fragmenter")
    print("================")
    
    if not check_ffmpeg():
        print("Error: ffmpeg is not installed or not found in PATH.")
        print("Please install ffmpeg first:")
        print("  macOS: brew install ffmpeg")
        print("  Ubuntu/Debian: sudo apt install ffmpeg")
        print("  Windows: Download from https://ffmpeg.org/")
        return 1

    video_path = VIDEO_FILENAME
    fragment_minutes = FRAGMENT_MINUTES
    
    print(f"Input video: {video_path}")
    print(f"Fragment duration: {fragment_minutes} minutes")
    print()
    
    success = fragment_video(video_path, fragment_minutes)
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())
