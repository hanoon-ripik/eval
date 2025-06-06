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
from PIL import Image
import math

# Add the external/gemini directory to the Python path
models_dir = "/Users/hanoon/Documents/eval/external/gemini"
if models_dir not in sys.path:
    sys.path.insert(0, models_dir)

from models import gemini_1_5_flash, gemini_1_5_pro, gemini_2_0_flash, gemini_2_5_pro_preview

# Configuration
MODEL_TO_USE = gemini_1_5_flash 
FOLDER_PATH = "/Users/hanoon/Documents/eval/ocr/data/digital_meter_readings/birla_copper/downloads"  # Change this to your folder path
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

# Pricing constants for Gemini models (per 1M tokens)
GEMINI_PRICING = {
    'gemini_1_5_flash': {'input': 0.075, 'output': 0.30},
    'gemini_1_5_pro': {'input': 1.25, 'output': 5.00},
    'gemini_2_0_flash': {'input': 0.10, 'output': 0.40},
    'gemini_2_5_pro_preview': {'input': 1.25, 'output': 10.00}
}

# System instruction for tonnage recognition
SYSTEM_INSTRUCTION = """You are a tonnage reading assistant. Your ONLY task is to extract tonnage values from digital meter images. You must ONLY return the tonnage number as a string float/int value without the 't' suffix and nothing else - no explanations, no formatting, no additional words, no styling, no markdown. Convert comma-separated values to decimal format (e.g., "15,720" becomes "15.72")."""

# Test prompt
TEST_PROMPT = """Look at this image and find the tonnage value. The tonnage is usually present as XXXXXXt (with 't' indicating tonnage) and is typically next to the text "Total". Extract ONLY the tonnage number without the 't' suffix and convert it to decimal format. For example, if you see "15,720t", return only "15.72" as a string. Remove trailing zeros after decimal point. Return only the string float/int value. If you cannot find a tonnage value clearly, return an empty string."""

def calculate_cost(model_name, input_tokens, output_tokens):
    """Calculate the cost of API call based on token usage"""
    if model_name not in GEMINI_PRICING:
        print(f"Warning: Unknown model {model_name}, using default pricing")
        model_name = 'gemini_1_5_flash'
    
    pricing = GEMINI_PRICING[model_name]
    input_cost = (input_tokens / 1_000_000) * pricing['input']
    output_cost = (output_tokens / 1_000_000) * pricing['output']
    total_cost = input_cost + output_cost
    
    return total_cost

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

def test_single_image(image_path, model_name='gemini_1_5_flash'):
    """Test tonnage recognition on a single image"""
    try:
        response = MODEL_TO_USE(
            system_instruction=SYSTEM_INSTRUCTION,
            prompt=TEST_PROMPT,
            image_path=image_path
        )
        
        # Get actual token counts from response usage metadata
        if hasattr(response, 'usage_metadata'):
            input_tokens = response.usage_metadata.prompt_token_count
            output_tokens = response.usage_metadata.candidates_token_count
            total_tokens = response.usage_metadata.total_token_count
        else:
            print("Warning: No usage metadata available from response")
            return None
        
        cost_usd = calculate_cost(model_name, input_tokens, output_tokens)
        
        # Clean the response and extract tonnage value
        clean_response = response.text.strip()
        
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
            "ocr_predicted": tonnage_value,
            "cost_usd": cost_usd,
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
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
    total_cost = 0.0
    total_input_tokens = 0
    total_output_tokens = 0
    
    # Process each image with progress bar
    for image_path in tqdm(image_files, desc="Extracting tonnage values from digital meters"):
        result = test_single_image(image_path)
        if result:
            all_results.append(result)
            result_count += 1
            total_cost += result['cost_usd']
            total_input_tokens += result['input_tokens']
            total_output_tokens += result['output_tokens']
            
            # Save updated results to JSON file after each image
            with open('tonnage_readings.json', 'w') as f:
                json.dump(all_results, f, indent=2)
    
    print(f"Saved {result_count} tonnage recognition results to tonnage_readings.json")
    print(f"Total cost: ${total_cost:.6f}")
    print(f"Average cost per image: ${total_cost/result_count:.6f}")
    print(f"Total input tokens: {total_input_tokens:,}")
    print(f"Total output tokens: {total_output_tokens:,}")
    print(f"Total tokens: {total_input_tokens + total_output_tokens:,}")

def test_all_models_on_folder():
    """Test all available models with tonnage recognition on the folder"""
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
        total_cost = 0.0
        total_input_tokens = 0
        total_output_tokens = 0
        
        for image_path in tqdm(image_files, desc=f"Tonnage recognition with {model_name}"):
            try:
                response = model_func(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=TEST_PROMPT,
                    image_path=image_path
                )
                
                # Get actual token counts from response usage metadata
                if hasattr(response, 'usage_metadata'):
                    input_tokens = response.usage_metadata.prompt_token_count
                    output_tokens = response.usage_metadata.candidates_token_count
                    total_tokens = response.usage_metadata.total_token_count
                else:
                    print(f"Warning: No usage metadata available for {os.path.basename(image_path)}")
                    continue
                
                cost_usd = calculate_cost(model_name, input_tokens, output_tokens)
                
                # Clean the response and convert tonnage value to decimal format
                clean_response = response.text.strip()
                tonnage_value = convert_tonnage_to_decimal(clean_response)
                
                # Return empty string if no valid tonnage found
                if not tonnage_value or tonnage_value.lower() in ['none', 'n/a', 'not found']:
                    tonnage_value = ""
                
                # Create result
                filename = os.path.basename(image_path)
                image_id = int(os.path.splitext(filename)[0])
                
                ocr_result = {
                    "id": image_id,
                    "ocr_predicted": tonnage_value,
                    "cost_usd": cost_usd,
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens,
                    "total_tokens": total_tokens
                }
                
                model_results.append(ocr_result)
                result_count += 1
                total_cost += cost_usd
                total_input_tokens += input_tokens
                total_output_tokens += output_tokens
                
                # Save updated results to JSON file named after the model
                with open(f'{model_name}_tonnage.json', 'w') as f:
                    json.dump(model_results, f, indent=2)
                
            except Exception as e:
                print(f"ERROR with {model_name} on {os.path.basename(image_path)}: {e}")
        
        print(f"Saved {result_count} results to {model_name}_tonnage.json")
        print(f"{model_name} - Total cost: ${total_cost:.6f}")
        print(f"{model_name} - Average cost per image: ${total_cost/result_count:.6f}")
        print(f"{model_name} - Total input tokens: {total_input_tokens:,}")
        print(f"{model_name} - Total output tokens: {total_output_tokens:,}")
        print(f"{model_name} - Total tokens: {total_input_tokens + total_output_tokens:,}")
        print()

if __name__ == "__main__":
    # Test single model on folder
    # test_folder_ocr()
    
    # Uncomment to test all models on folder
    test_all_models_on_folder()