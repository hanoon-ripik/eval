#!/usr/bin/env python3
"""
Test script for Gemini models with number plate recognition functionality on folder of images
Specifically extracts the LAST 4 digits of number plates
"""

import os
import glob
import json
import sys
from pathlib import Path
from tqdm import tqdm

# Add the external/gemini directory to the Python path
models_dir = "/Users/hanoon/Documents/eval/external/claude"
if models_dir not in sys.path:
    sys.path.insert(0, models_dir)

from models import claude_sonnet_4, claude_3_7_sonnet, claude_3_5_haiku, claude_3_5_sonnet

# Configuration
MODEL_TO_USE = claude_sonnet_4 
FOLDER_PATH = "/Users/hanoon/Documents/eval/ocr/data/number_plate_recognition/downloads"  # Change this to your folder path
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

# System instruction for number plate recognition
SYSTEM_INSTRUCTION = """You are a number plate recognition assistant. Your ONLY task is to extract the LAST 4 digits from number plates in images. You must ONLY return those 4 digits and nothing else - no explanations, no formatting, no additional words, no styling, no markdown. Just the last 4 digits of the number plate."""

# Test prompt
TEST_PROMPT = """Look at this image and find the number plate. Extract ONLY the last 4 digits from the number plate. Return ONLY those 4 digits with no other text, explanations, or formatting. If you cannot find a number plate or cannot read the last 4 digits clearly, return "XXXX"."""

def get_image_files(folder_path):
    """Get all image files from the specified folder"""
    image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        pattern = os.path.join(folder_path, f"*{ext}")
        image_files.extend(glob.glob(pattern))
    return image_files

def test_single_image(image_path):
    """Test number plate recognition on a single image"""
    try:
        response = MODEL_TO_USE(
            system_instruction=SYSTEM_INSTRUCTION,
            prompt=TEST_PROMPT,
            image_path=image_path
        )
        
        # Clean the response to ensure we only get 4 digits
        clean_response = response.strip()
        
        # Validate and extract exactly 4 digits
        if len(clean_response) == 4 and clean_response.isdigit():
            last_4_digits = clean_response
        elif len(clean_response) > 4:
            # If response is longer, try to extract last 4 digits
            digits_only = ''.join(filter(str.isdigit, clean_response))
            if len(digits_only) >= 4:
                last_4_digits = digits_only[-4:]
            else:
                last_4_digits = "XXXX"
        else:
            # If less than 4 characters or contains non-digits
            digits_only = ''.join(filter(str.isdigit, clean_response))
            if len(digits_only) == 4:
                last_4_digits = digits_only
            else:
                last_4_digits = "XXXX"
        
        # Wrap the number plate digits in JSON format
        filename = os.path.basename(image_path)
        image_id = int(os.path.splitext(filename)[0])
                
        ocr_result = {
            "id": image_id,
            "ocr_predicted": last_4_digits
        }
        
        return ocr_result
        
    except Exception as e:
        print(f"ERROR processing {os.path.basename(image_path)}: {e}")
        return None

def test_folder_ocr():
    """Test number plate recognition on all images in the specified folder"""
    # Get all image files
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    # Initialize empty JSON array
    all_results = []
    result_count = 0
    
    # Process each image with progress bar
    for image_path in tqdm(image_files, desc="Extracting last 4 digits from number plates"):
        result = test_single_image(image_path)
        if result:
            all_results.append(result)
            result_count += 1
            
            # Save updated results to JSON file after each image
            with open('number_plate_last_4_digits.json', 'w') as f:
                json.dump(all_results, f, indent=2)
    
    print(f"Saved {result_count} number plate recognition results to number_plate_last_4_digits.json")

def test_all_models_on_folder():
    """Test all available models with number plate recognition on the folder"""
    models = [
        ("claude_sonnet_4", claude_sonnet_4),
        ("claude_3_7_sonnet", claude_3_7_sonnet),
        ("claude_3_5_haiku", claude_3_5_haiku),
        ("claude_3_5_sonnet", claude_3_5_sonnet)
    ]
    
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    for model_name, model_func in models:
        # Initialize empty JSON array for each model
        model_results = []
        result_count = 0
        
        for image_path in tqdm(image_files, desc=f"Number plate recognition with {model_name}"):
            try:
                response = model_func(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=TEST_PROMPT,
                    image_path=image_path
                )
                
                # Clean the response to ensure we only get 4 digits
                clean_response = response.strip()
                
                # Validate and extract exactly 4 digits
                if len(clean_response) == 4 and clean_response.isdigit():
                    last_4_digits = clean_response
                elif len(clean_response) > 4:
                    # If response is longer, try to extract last 4 digits
                    digits_only = ''.join(filter(str.isdigit, clean_response))
                    if len(digits_only) >= 4:
                        last_4_digits = digits_only[-4:]
                    else:
                        last_4_digits = "XXXX"
                else:
                    # If less than 4 characters or contains non-digits
                    digits_only = ''.join(filter(str.isdigit, clean_response))
                    if len(digits_only) == 4:
                        last_4_digits = digits_only
                    else:
                        last_4_digits = "XXXX"
                
                # Wrap the number plate digits in JSON format without model field
                filename = os.path.basename(image_path)
                image_id = int(os.path.splitext(filename)[0])
                
                # Wrap the number plate digits in JSON format without model field
                ocr_result = {
                    "id": image_id,
                    "ocr_predicted": last_4_digits
                }
                
                model_results.append(ocr_result)
                result_count += 1
                
                # Save updated results to JSON file named after the model
                with open(f'{model_name}.json', 'w') as f:
                    json.dump(model_results, f, indent=2)
                
            except Exception as e:
                print(f"ERROR with {model_name} on {os.path.basename(image_path)}: {e}")
        
        print(f"Saved {result_count} results to {model_name}.json")

if __name__ == "__main__":
    # Test single model on folder
    # test_folder_ocr()
    
    # Uncomment to test all models on folder
    test_all_models_on_folder()