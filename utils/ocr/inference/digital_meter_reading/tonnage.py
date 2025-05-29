#!/usr/bin/env python3
"""
Test script for Gemini models with tonnage recognition functionality on folder of images
Specifically extracts tonnage values from digital meter readings
"""

import os
import glob
import json
import sys
from pathlib import Path
from tqdm import tqdm

# Add the external/gemini directory to the Python path
models_dir = "/Users/hanoon/Documents/eval/external/gemini"
if models_dir not in sys.path:
    sys.path.insert(0, models_dir)

from models import gemini_1_5_flash, gemini_1_5_pro

# Configuration
MODEL_TO_USE = gemini_1_5_flash 
FOLDER_PATH = "/Users/hanoon/Documents/eval/utils/ocr/data/digital_meter_readings/birla_copper/downloads"  # Change this to your folder path
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

# System instruction for tonnage recognition
SYSTEM_INSTRUCTION = """You are a tonnage reading assistant. Your ONLY task is to extract tonnage values from digital meter images. You must ONLY return the tonnage number without the 't' suffix and nothing else - no explanations, no formatting, no additional words, no styling, no markdown. Just the tonnage value with commas if present."""

# Test prompt
TEST_PROMPT = """Look at this image and find the tonnage value. The tonnage is usually present as XXXXXXt (with 't' indicating tonnage) and is typically next to the text "Total". Extract ONLY the tonnage number without the 't' suffix. For example, if you see "15,360t", return only "15,360". If you cannot find a tonnage value clearly, return an empty string."""

def get_image_files(folder_path):
    """Get all image files from the specified folder"""
    image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        pattern = os.path.join(folder_path, f"*{ext}")
        image_files.extend(glob.glob(pattern))
    return image_files

def test_single_image(image_path):
    """Test tonnage recognition on a single image"""
    try:
        response = MODEL_TO_USE(
            system_instruction=SYSTEM_INSTRUCTION,
            prompt=TEST_PROMPT,
            image_path=image_path
        )
        
        # Clean the response and extract tonnage value
        clean_response = response.strip()
        
        # Extract tonnage value (remove 't' suffix if present)
        if clean_response.lower().endswith('t'):
            tonnage_value = clean_response[:-1]
        else:
            tonnage_value = clean_response
        
        # Return empty string if no valid tonnage found
        if not tonnage_value or tonnage_value.lower() in ['none', 'n/a', 'not found']:
            tonnage_value = ""
        
        # Create result
        filename = os.path.basename(image_path)
        image_id = int(os.path.splitext(filename)[0])
                
        ocr_result = {
            "id": image_id,
            "ocr_predicted": tonnage_value
        }
        
        return ocr_result
        
    except Exception as e:
        print(f"ERROR processing {os.path.basename(image_path)}: {e}")
        return None

def test_folder_ocr():
    """Test tonnage recognition on all images in the specified folder"""
    # Get all image files
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    # Initialize empty JSON array
    all_results = []
    result_count = 0
    
    # Process each image with progress bar
    for image_path in tqdm(image_files, desc="Extracting tonnage values from digital meters"):
        result = test_single_image(image_path)
        if result:
            all_results.append(result)
            result_count += 1
            
            # Save updated results to JSON file after each image
            with open('tonnage_readings.json', 'w') as f:
                json.dump(all_results, f, indent=2)
    
    print(f"Saved {result_count} tonnage recognition results to tonnage_readings.json")

def test_all_models_on_folder():
    """Test all available models with tonnage recognition on the folder"""
    models = [
        ("gemini_1_5_pro", gemini_1_5_pro),
    ]
    
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    for model_name, model_func in models:
        # Initialize empty JSON array for each model
        model_results = []
        result_count = 0
        
        for image_path in tqdm(image_files, desc=f"Tonnage recognition with {model_name}"):
            try:
                response = model_func(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=TEST_PROMPT,
                    image_path=image_path
                )
                
                # Clean the response and extract tonnage value
                clean_response = response.strip()
                
                # Extract tonnage value (remove 't' suffix if present)
                if clean_response.lower().endswith('t'):
                    tonnage_value = clean_response[:-1]
                else:
                    tonnage_value = clean_response
                
                # Return empty string if no valid tonnage found
                if not tonnage_value or tonnage_value.lower() in ['none', 'n/a', 'not found']:
                    tonnage_value = ""
                
                # Create result
                filename = os.path.basename(image_path)
                image_id = int(os.path.splitext(filename)[0])
                
                ocr_result = {
                    "id": image_id,
                    "ocr_predicted": tonnage_value
                }
                
                model_results.append(ocr_result)
                result_count += 1
                
                # Save updated results to JSON file named after the model
                with open(f'{model_name}_tonnage.json', 'w') as f:
                    json.dump(model_results, f, indent=2)
                
            except Exception as e:
                print(f"ERROR with {model_name} on {os.path.basename(image_path)}: {e}")
        
        print(f"Saved {result_count} results to {model_name}.json")

if __name__ == "__main__":
    # Test single model on folder
    # test_folder_ocr()
    
    # Uncomment to test all models on folder
    test_all_models_on_folder()