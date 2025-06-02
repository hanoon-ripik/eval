#!/usr/bin/env python3
"""
Test script for Gemini models with coil ID recognition functionality on folder of images
Specifically extracts coil ID text written on coils in images
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

from models import gemini_1_5_pro, gemini_2_0_flash, gemini_2_5_pro_preview

# Configuration
MODEL_TO_USE = gemini_1_5_pro 
FOLDER_PATH = "/Users/hanoon/Documents/eval/ocr/data/coil_id/downloads"  # Change this to your folder path
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

# System instruction for coil ID recognition
SYSTEM_INSTRUCTION = """You are a coil ID recognition assistant. Your ONLY task is to read and extract the coil ID text that is written on coils in images. You must ONLY return the exact text/numbers written on the coil and nothing else - no explanations, no formatting, no additional words, no styling, no markdown. Just the coil ID text as it appears on the coil."""

# Test prompt
TEST_PROMPT = """Look at this image and find the coil ID text written on the coil. Extract ONLY the exact text/numbers that are written on the coil surface. Return ONLY that text with no other explanations, formatting, or additional words. If you cannot find any text written on the coil clearly, return an empty string."""

def get_image_files(folder_path):
    """Get all image files from the specified folder"""
    image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        pattern = os.path.join(folder_path, f"*{ext}")
        image_files.extend(glob.glob(pattern))
    return image_files

def test_single_image(image_path):
    """Test coil ID recognition on a single image"""
    try:
        response = MODEL_TO_USE(
            system_instruction=SYSTEM_INSTRUCTION,
            prompt=TEST_PROMPT,
            image_path=image_path
        )
        
        # Clean the response to get the coil ID text
        clean_response = response.strip()
        
        # Return empty string if no valid coil ID found
        if not clean_response or clean_response.lower() in ['none', 'n/a', 'not found', 'no text', 'unclear']:
            coil_id = ""
        else:
            coil_id = clean_response
        
        # Create result
        filename = os.path.basename(image_path)
        image_id = int(os.path.splitext(filename)[0])
                
        ocr_result = {
            "id": image_id,
            "ocr_predicted": coil_id
        }
        
        return ocr_result
        
    except Exception as e:
        print(f"ERROR processing {os.path.basename(image_path)}: {e}")
        return None

def test_folder_ocr():
    """Test coil ID recognition on all images in the specified folder"""
    # Get all image files
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    # Initialize empty JSON array
    all_results = []
    result_count = 0
    
    # Process each image with progress bar
    for image_path in tqdm(image_files, desc="Extracting coil ID text from images"):
        result = test_single_image(image_path)
        if result:
            all_results.append(result)
            result_count += 1
            
            # Save updated results to JSON file after each image
            with open('coil_id_results.json', 'w') as f:
                json.dump(all_results, f, indent=2)
    
    print(f"Saved {result_count} coil ID recognition results to coil_id_results.json")

def test_all_models_on_folder():
    """Test all available models with coil ID recognition on the folder"""
    models = [
        ("gemini_1_5_pro", gemini_1_5_pro),
        # ("gemini_2_0_flash", gemini_2_0_flash),
        # ("gemini_2_5_pro_preview", gemini_2_5_pro_preview)
    ]
    
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    for model_name, model_func in models:
        # Initialize empty JSON array for each model
        model_results = []
        result_count = 0
        
        for image_path in tqdm(image_files, desc=f"Coil ID recognition with {model_name}"):
            try:
                response = model_func(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=TEST_PROMPT,
                    image_path=image_path
                )
                
                # Clean the response to get the coil ID text
                clean_response = response.strip()
                
                # Return empty string if no valid coil ID found
                if not clean_response or clean_response.lower() in ['none', 'n/a', 'not found', 'no text', 'unclear']:
                    coil_id = ""
                else:
                    coil_id = clean_response
                
                # Create result
                filename = os.path.basename(image_path)
                image_id = int(os.path.splitext(filename)[0])
                
                ocr_result = {
                    "id": image_id,
                    "ocr_predicted": coil_id
                }
                
                model_results.append(ocr_result)
                result_count += 1
                
                # Save updated results to JSON file named after the model
                with open(f'{model_name}_coil_id.json', 'w') as f:
                    json.dump(model_results, f, indent=2)
                
            except Exception as e:
                print(f"ERROR with {model_name} on {os.path.basename(image_path)}: {e}")
        
        print(f"Saved {result_count} results to {model_name}_coil_id.json")

if __name__ == "__main__":
    # Test single model on folder
    # test_folder_ocr()
    
    # Uncomment to test all models on folder
    test_all_models_on_folder()
