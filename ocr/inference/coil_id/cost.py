#!/usr/bin/env python3
"""
Test script for Gemini models with coil ID recognition functionality on folder of images
Specifically extracts coil ID values from steel coil images
"""

import os
import glob
import json
import sys
from pathlib import Path
from tqdm import tqdm
from PIL import Image
import math
import google.generativeai as genai

# Configure the API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

# Add the external/gemini directory to the Python path
models_dir = "/Users/hanoon/Documents/eval/external/gemini"
if models_dir not in sys.path:
    sys.path.insert(0, models_dir)

from models import gemini_1_5_flash, gemini_1_5_pro, gemini_2_0_flash, gemini_2_5_pro_preview

# Configuration
MODEL_TO_USE = gemini_2_0_flash 
FOLDER_PATH = "/Users/hanoon/Documents/eval/ocr/data/coil_id/downloads"  # Change this to your folder path
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

# Pricing constants for Gemini models (per 1M tokens)
GEMINI_PRICING = {
    'gemini_1_5_flash': {'input': 0.075, 'output': 0.30},
    'gemini_1_5_pro': {'input': 1.25, 'output': 5.00},
    'gemini_2_0_flash': {'input': 0.10, 'output': 0.40},
    'gemini_2_5_pro_preview': {'input': 1.25, 'output': 10.00}
}

# System instruction for coil ID recognition
SYSTEM_INSTRUCTION = """You are a steel coil ID recognition assistant. Your ONLY task is to extract coil identification numbers from images of steel coils. You must ONLY return the coil ID as a string and nothing else - no explanations, no formatting, no additional words, no styling, no markdown. The coil ID is typically an alphanumeric code printed, stamped, or tagged on the coil."""

# Test prompt
TEST_PROMPT = """Look at this image and find the coil identification number. The coil ID is typically printed, stamped, or tagged on the steel coil and may appear as an alphanumeric code. Extract ONLY the coil ID and return it exactly as it appears. Return only the coil ID string. If you cannot find a coil ID clearly, return an empty string."""

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

def clean_coil_id(coil_id_str):
    """Clean and normalize a coil ID string"""
    if not coil_id_str or coil_id_str == "":
        return ""
    
    try:
        # Strip any leading/trailing whitespace
        clean_id = coil_id_str.strip()
        
        # Remove any common prefixes/suffixes if necessary
        # Uncomment and modify if there are standard prefixes to remove
        # clean_id = clean_id.replace("COIL-", "")
        
        # Handle common OCR errors if needed
        # For example, replacing O with 0 or I with 1 if appropriate for your use case
        # clean_id = clean_id.replace("O", "0").replace("I", "1")
        
        # Remove any non-alphanumeric characters if required
        # import re
        # clean_id = re.sub(r'[^A-Za-z0-9]', '', clean_id)
        
        return clean_id
            
    except Exception:
        return coil_id_str  # Return original if cleaning fails

def test_single_image(image_path, model_name='gemini_2_0_flash'):
    """Test coil ID recognition on a single image"""
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
        
        # Clean the response and extract coil ID
        clean_response = response.text.strip()
        
        # Clean and normalize the coil ID
        coil_id = clean_coil_id(clean_response)
        
        # Return empty string if no valid coil ID found
        if not coil_id or coil_id.lower() in ['none', 'n/a', 'not found']:
            coil_id = ""
        
        # Create result
        filename = os.path.basename(image_path)
        try:
            # Try to convert the filename to an integer ID if possible
            image_id = int(os.path.splitext(filename)[0])
        except ValueError:
            # If not possible, use the filename without extension as ID
            image_id = os.path.splitext(filename)[0]
                
        ocr_result = {
            "id": image_id,
            "ocr_predicted": coil_id,
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
    """Test coil ID recognition on all images in the specified folder"""
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
    for image_path in tqdm(image_files, desc="Extracting coil IDs from steel coil images"):
        result = test_single_image(image_path)
        if result:
            all_results.append(result)
            result_count += 1
            total_cost += result['cost_usd']
            total_input_tokens += result['input_tokens']
            total_output_tokens += result['output_tokens']
            
            # Save updated results to JSON file after each image
            with open('coil_id_results.json', 'w') as f:
                json.dump(all_results, f, indent=2)
    
    print(f"Saved {result_count} coil ID recognition results to coil_id_results.json")
    print(f"Total cost: ${total_cost:.6f}")
    print(f"Average cost per image: ${total_cost/result_count:.6f}")
    print(f"Total input tokens: {total_input_tokens:,}")
    print(f"Total output tokens: {total_output_tokens:,}")
    print(f"Total tokens: {total_input_tokens + total_output_tokens:,}")

def test_all_models_on_folder():
    """Test all available models with coil ID recognition on the folder"""
    models = [
        # ("gemini_1_5_flash", gemini_1_5_flash),
        # ("gemini_1_5_pro", gemini_1_5_pro),
        ("gemini_2_0_flash", gemini_2_0_flash),
        # ("gemini_2_5_pro_preview", gemini_2_5_pro_preview),
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
        
        for image_path in tqdm(image_files, desc=f"Coil ID recognition with {model_name}"):
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
                
                # Clean the response and extract coil ID
                clean_response = response.text.strip()
                coil_id = clean_coil_id(clean_response)
                
                # Return empty string if no valid coil ID found
                if not coil_id or coil_id.lower() in ['none', 'n/a', 'not found']:
                    coil_id = ""
                
                # Create result
                filename = os.path.basename(image_path)
                try:
                    # Try to convert the filename to an integer ID if possible
                    image_id = int(os.path.splitext(filename)[0])
                except ValueError:
                    # If not possible, use the filename without extension as ID
                    image_id = os.path.splitext(filename)[0]
                
                ocr_result = {
                    "id": image_id,
                    "ocr_predicted": coil_id,
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
                with open(f'{model_name}_coil_id.json', 'w') as f:
                    json.dump(model_results, f, indent=2)
                
            except Exception as e:
                print(f"ERROR with {model_name} on {os.path.basename(image_path)}: {e}")
        
        print(f"Saved {result_count} results to {model_name}_coil_id.json")
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