#!/usr/bin/env python3
"""
Test script for Gemini models with tonnage recognition functionality on folder of images
Specifically extracts tonnage values from digital meter readings
"""

import os
import glob
import json
import sys
import time
from pathlib import Path
from tqdm import tqdm

# Add the external/gemini directory to the Python path
models_dir = "/Users/hanoon/Documents/eval/external/gemini"
if models_dir not in sys.path:
    sys.path.insert(0, models_dir)

from models import gemini_1_5_flash, gemini_1_5_pro, gemini_2_0_flash, gemini_2_5_pro_preview

# Configuration
MODEL_TO_USE = gemini_2_5_pro_preview 
FOLDER_PATH = "/Users/hanoon/Documents/eval/ocr/data/digital_meter_readings/birla_copper/downloads"  # Change this to your folder path
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

# System instruction for tonnage recognition
SYSTEM_INSTRUCTION = """You are a tonnage reading assistant. Your ONLY task is to extract tonnage values from digital meter images. You must ONLY return the tonnage number as a string float/int value without the 't' suffix and nothing else - no explanations, no formatting, no additional words, no styling, no markdown. Convert comma-separated values to decimal format (e.g., "15,720" becomes "15.72")."""

# Test prompt
TEST_PROMPT = """Look at this image and find the tonnage value. The tonnage is usually present as XXXXXXt (with 't' indicating tonnage) and is typically next to the text "Total". Extract ONLY the tonnage number without the 't' suffix and convert it to decimal format. For example, if you see "15,720t", return only "15.72" as a string. Remove trailing zeros after decimal point. Return only the string float/int value. If you cannot find a tonnage value clearly, return an empty string."""

def get_image_files(folder_path):
    """Get all image files from the specified folder"""
    image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        pattern = os.path.join(folder_path, f"*{ext}")
        image_files.extend(glob.glob(pattern))
    return image_files

def convert_tonnage_to_decimal(tonnage_str):
    """Convert comma-separated tonnage to decimal format (xx,xxx -> xx.xx)"""
    if not tonnage_str or tonnage_str == "":
        return ""
    
    try:
        # Remove any 't' suffix if present
        clean_tonnage = tonnage_str.lower().replace('t', '').strip()
        
        # Handle comma-separated format (e.g., "15,720" -> "15.72")
        if ',' in clean_tonnage:
            parts = clean_tonnage.split(',')
            if len(parts) == 2:
                # Convert xx,xxx to xx.xx format
                integer_part = parts[0]
                decimal_part = parts[1][:2]  # Take only first 2 digits after comma
                converted = f"{integer_part}.{decimal_part}"
                
                # Convert to float to remove trailing zeros, then back to string
                float_val = float(converted)
                if float_val == int(float_val):
                    return str(int(float_val))
                else:
                    return str(float_val).rstrip('0').rstrip('.')
        
        # If no comma, try to convert directly
        float_val = float(clean_tonnage)
        if float_val == int(float_val):
            return str(int(float_val))
        else:
            return str(float_val).rstrip('0').rstrip('.')
            
    except (ValueError, IndexError):
        return tonnage_str  # Return original if conversion fails

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
        
        # Convert tonnage value to decimal format
        tonnage_value = convert_tonnage_to_decimal(clean_response)
        
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
    start_time = time.time()
    print(f"Starting tonnage recognition processing at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
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
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nProcessing completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time taken: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"Average time per image: {total_time/len(image_files):.2f} seconds")
    print(f"Saved {result_count} tonnage recognition results to tonnage_readings.json")

def test_all_models_on_folder():
    """Test all available models with tonnage recognition on the folder"""
    start_time = time.time()
    print(f"Starting tonnage recognition processing at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    
    models = [
        ("gemini_2_5_pro_preview", gemini_2_5_pro_preview),
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
                
                # Clean the response and convert tonnage value to decimal format
                clean_response = response.strip()
                tonnage_value = convert_tonnage_to_decimal(clean_response)
                
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
        
        print(f"Saved {result_count} results to {model_name}_tonnage.json")
    
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\nProcessing completed at {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Total time taken: {total_time:.2f} seconds ({total_time/60:.2f} minutes)")
    print(f"Average time per image: {total_time/len(image_files):.2f} seconds")

if __name__ == "__main__":
    # Test single model on folder
    # test_folder_ocr()
    
    # Uncomment to test all models on folder
    test_all_models_on_folder()