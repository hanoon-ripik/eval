#!/usr/bin/env python3
"""
Pipe counting script using Gemini models for video processing
Processes video files and counts the number of pipes visible in each video
"""

import os
import glob
import json
import sys
import time
import re
from pathlib import Path
from tqdm import tqdm

# Add the external/gemini directory to the Python path
models_dir = "/Users/hanoon/Documents/eval/external/gemini"
if models_dir not in sys.path:
    sys.path.insert(0, models_dir)

from models import gemini_1_5_flash, gemini_1_5_pro, gemini_2_0_flash, gemini_2_5_pro_preview

# Configuration
MODEL_TO_USE = gemini_2_0_flash  # Using a model that supports video well
FOLDER_PATH = "/Users/hanoon/Documents/eval/misc/fragments/00000000017000000"  # Video folder path
SUPPORTED_EXTENSIONS = ['.mp4', '.mov', '.avi', '.mkv', '.webm']

# System instruction for pipe counting
SYSTEM_INSTRUCTION = """You are a pipe counting assistant. Your ONLY task is to count the number of pipes visible in video content. You must ONLY return the count as a plain integer number and nothing else - no explanations, no formatting, no additional words, no styling, no markdown. Count all visible pipes in the video, including partial pipes that are clearly identifiable as pipes."""

# Test prompt for pipe counting
TEST_PROMPT = """Watch this video carefully and count the total number of pipes visible throughout the video. Count all pipes that are clearly visible, including partial pipes. Return ONLY the count as a plain integer number (e.g., "5" or "12"). If you cannot see any pipes clearly, return "0"."""

def get_video_files(folder_path):
    """Get all video files from the specified folder"""
    video_files = []
    for ext in SUPPORTED_EXTENSIONS:
        pattern = os.path.join(folder_path, f"*{ext}")
        video_files.extend(glob.glob(pattern))
    return sorted(video_files)  # Sort for consistent processing order

def clean_count_response(response):
    """Clean the response and extract count value"""
    if not response or response == "":
        return 0
    
    try:
        # Remove any non-numeric characters and extract the number
        clean_response = response.strip()
        
        # Try to extract just the number from the response
        import re
        numbers = re.findall(r'\b\d+\b', clean_response)
        
        if numbers:
            return int(numbers[0])  # Take the first number found
        else:
            return 0
            
    except (ValueError, IndexError):
        return 0  # Return 0 if conversion fails

def test_single_video(video_path, model_func=None):
    """Test pipe counting on a single video"""
    if model_func is None:
        model_func = MODEL_TO_USE
        
    try:
        # Add delay to avoid rate limiting
        time.sleep(2)
        
        response = model_func(
            system_instruction=SYSTEM_INSTRUCTION,
            prompt=TEST_PROMPT,
            video_path=video_path
        )
        
        # Clean the response and extract count value
        pipe_count = clean_count_response(response)
        
        # Create result
        filename = os.path.basename(video_path)
        
        result = {
            "video": filename,
            "count": pipe_count
        }
        
        return result
        
    except Exception as e:
        print(f"ERROR processing {os.path.basename(video_path)}: {e}")
        # Add longer delay on error
        time.sleep(5)
        # Return 0 count for failed videos
        filename = os.path.basename(video_path)
        return {
            "video": filename,
            "count": 0
        }

def test_folder_pipe_counting():
    """Test pipe counting on all videos in the specified folder"""
    # Get all video files
    video_files = get_video_files(FOLDER_PATH)
    
    if not video_files:
        print(f"No video files found in {FOLDER_PATH}")
        return
    
    print(f"Found {len(video_files)} video files to process")
    
    # Initialize empty JSON array
    all_results = []
    result_count = 0
    
    # Process each video with progress bar
    for video_path in tqdm(video_files, desc="Counting pipes in videos"):
        result = test_single_video(video_path)
        if result:
            all_results.append(result)
            result_count += 1
            
            # Save updated results to JSON file after each video
            with open('pipe_counts.json', 'w') as f:
                json.dump(all_results, f, indent=2)
    
    print(f"Saved {result_count} pipe counting results to pipe_counts.json")

def test_all_models_on_folder():
    """Test all available models with pipe counting on the folder"""
    models = [
        ("gemini_2_0_flash", gemini_2_0_flash),
        ("gemini_1_5_flash", gemini_1_5_flash),
        ("gemini_1_5_pro", gemini_1_5_pro),
        ("gemini_2_5_pro_preview", gemini_2_5_pro_preview),
    ]
    
    video_files = get_video_files(FOLDER_PATH)
    
    if not video_files:
        print(f"No video files found in {FOLDER_PATH}")
        return
    
    print(f"Found {len(video_files)} video files to process")
    
    for model_name, model_func in models:
        print(f"\nTesting {model_name}...")
        
        # Initialize empty JSON array for each model
        model_results = []
        result_count = 0
        
        for video_path in tqdm(video_files, desc=f"Pipe counting with {model_name}"):
            try:
                # Add delay to avoid rate limiting
                time.sleep(2)
                
                response = model_func(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=TEST_PROMPT,
                    video_path=video_path
                )
                
                # Clean the response and extract count value
                pipe_count = clean_count_response(response)
                
                # Create result
                filename = os.path.basename(video_path)
                
                result = {
                    "video": filename,
                    "count": pipe_count
                }
                
                model_results.append(result)
                result_count += 1
                
                # Save updated results to JSON file named after the model
                with open(f'{model_name}_pipe_counts.json', 'w') as f:
                    json.dump(model_results, f, indent=2)
                
            except Exception as e:
                print(f"ERROR with {model_name} on {os.path.basename(video_path)}: {e}")
                # Add longer delay on error
                time.sleep(5)
                # Add failed result with 0 count
                filename = os.path.basename(video_path)
                failed_result = {
                    "video": filename,
                    "count": 0
                }
                model_results.append(failed_result)
        
        print(f"Saved {result_count} results to {model_name}_pipe_counts.json")

def test_sample_videos():
    """Test pipe counting on just a few sample videos for quick testing"""
    video_files = get_video_files(FOLDER_PATH)
    
    if not video_files:
        print(f"No video files found in {FOLDER_PATH}")
        return
    
    # Take only first 5 videos for quick testing
    sample_videos = video_files[:5]
    print(f"Testing on {len(sample_videos)} sample videos...")
    
    # Initialize empty JSON array
    sample_results = []
    
    # Process sample videos with progress bar
    for video_path in tqdm(sample_videos, desc="Counting pipes in sample videos"):
        result = test_single_video(video_path)
        if result:
            sample_results.append(result)
            print(f"Video: {result['video']}, Pipe Count: {result['count']}")
        
        # Add delay between videos
        time.sleep(1)
    
    # Save sample results
    with open('sample_pipe_counts.json', 'w') as f:
        json.dump(sample_results, f, indent=2)
    
    print(f"Saved {len(sample_results)} sample results to sample_pipe_counts.json")

if __name__ == "__main__":
    # Test just a few sample videos for quick testing (recommended first)
    test_sample_videos()
    
    # Uncomment to test single model on all videos in folder
    # test_folder_pipe_counting()
    
    # Uncomment to test all models on folder (this will take much longer)
    # test_all_models_on_folder()