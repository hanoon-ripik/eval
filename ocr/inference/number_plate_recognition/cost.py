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
from PIL import Image

# Add the external/gemini directory to the Python path
models_dir = "/Users/hanoon/Documents/eval/external/gemini"
if models_dir not in sys.path:
    sys.path.insert(0, models_dir)

from models import gemini_2_0_flash, gemini_1_5_pro

# Configuration
MODEL_TO_USE = gemini_2_0_flash 
FOLDER_PATH = "/Users/hanoon/Documents/eval/ocr/data/number_plate_recognition/downloads"  # Change this to your folder path
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

# Gemini API Pricing (per 1M tokens) - as of June 2025
GEMINI_PRICING = {
    "gemini_2_0_flash": {
        "input": 0.10,  # $0.075 per 1M input tokens
        "output": 0.40   # $0.30 per 1M output tokens
    },
    "gemini_1_5_pro": {
        "input": 1.25,   # $1.25 per 1M input tokens  
        "output": 5.00   # $5.00 per 1M output tokens
    }
}

def estimate_image_tokens(image_path):
    """
    Estimate tokens for an image based on resolution.
    Gemini uses approximately 258 tokens per 512x512 tile.
    """
    try:
        with Image.open(image_path) as img:
            width, height = img.size
            # Calculate number of 512x512 tiles needed
            tiles_width = (width + 511) // 512
            tiles_height = (height + 511) // 512
            total_tiles = tiles_width * tiles_height
            return total_tiles * 258
    except Exception:
        # Default estimate if image can't be opened
        return 258  # Assume 1 tile

def estimate_text_tokens(text):
    """
    Rough estimate: 1 token ≈ 4 characters for English text
    """
    return len(text) // 4

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

def test_single_image(image_path, model_name="gemini_2_0_flash"):
    """Test number plate recognition on a single image and calculate cost"""
    try:
        # Calculate input tokens
        image_tokens = estimate_image_tokens(image_path)
        system_tokens = estimate_text_tokens(SYSTEM_INSTRUCTION)
        prompt_tokens = estimate_text_tokens(TEST_PROMPT)
        input_tokens = image_tokens + system_tokens + prompt_tokens
        
        response = MODEL_TO_USE(
            system_instruction=SYSTEM_INSTRUCTION,
            prompt=TEST_PROMPT,
            image_path=image_path
        )
        
        # Calculate output tokens
        output_tokens = estimate_text_tokens(response)
        
        # Calculate cost
        pricing = GEMINI_PRICING.get(model_name, GEMINI_PRICING["gemini_2_0_flash"])
        input_cost = (input_tokens / 1_000_000) * pricing["input"]
        output_cost = (output_tokens / 1_000_000) * pricing["output"]
        total_cost = input_cost + output_cost
        
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
            "ocr_predicted": last_4_digits,
            "cost_usd": round(total_cost, 6),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens
        }
        
        return ocr_result, total_cost
        
    except Exception as e:
        print(f"ERROR processing {os.path.basename(image_path)}: {e}")
        return None, 0.0

def test_folder_ocr():
    """Test number plate recognition on all images in the specified folder"""
    print(f"Starting number plate recognition cost analysis...")
    
    # Get all image files
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    # Initialize tracking variables
    all_results = []
    result_count = 0
    total_cost = 0.0
    
    # Process each image with progress bar
    for image_path in tqdm(image_files, desc="Extracting last 4 digits from number plates"):
        result, cost = test_single_image(image_path, "gemini_2_0_flash")
        if result:
            all_results.append(result)
            result_count += 1
            total_cost += cost
            
            # Save updated results to JSON file after each image
            with open('number_plate_last_4_digits.json', 'w') as f:
                json.dump(all_results, f, indent=2)
    
    # Calculate and display cost statistics
    avg_cost_per_image = total_cost / result_count if result_count > 0 else 0
    print(f"\nCost Analysis:")
    print(f"Total images processed: {result_count}")
    print(f"Total cost: ${total_cost:.6f}")
    print(f"Average cost per image: ${avg_cost_per_image:.6f}")
    print(f"Saved {result_count} number plate recognition results to number_plate_last_4_digits.json")

def test_all_models_on_folder():
    """Test all available models with number plate recognition on the folder and calculate costs"""
    print(f"Starting number plate recognition cost analysis for multiple models...")
    
    models = [
        ("gemini_2_0_flash", gemini_2_0_flash),
    ]
    
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    total_cost_all_models = 0.0
    
    for model_name, model_func in models:
        # Initialize tracking variables for each model
        model_results = []
        result_count = 0
        model_total_cost = 0.0
        
        print(f"\nProcessing with {model_name}...")
        
        for image_path in tqdm(image_files, desc=f"Number plate recognition with {model_name}"):
            try:
                # Calculate input tokens
                image_tokens = estimate_image_tokens(image_path)
                system_tokens = estimate_text_tokens(SYSTEM_INSTRUCTION)
                prompt_tokens = estimate_text_tokens(TEST_PROMPT)
                input_tokens = image_tokens + system_tokens + prompt_tokens
                
                response = model_func(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=TEST_PROMPT,
                    image_path=image_path
                )
                
                # Calculate output tokens and cost
                output_tokens = estimate_text_tokens(response)
                pricing = GEMINI_PRICING.get(model_name, GEMINI_PRICING["gemini_2_0_flash"])
                input_cost = (input_tokens / 1_000_000) * pricing["input"]
                output_cost = (output_tokens / 1_000_000) * pricing["output"]
                total_cost = input_cost + output_cost
                
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
                
                # Wrap the number plate digits in JSON format with cost information
                filename = os.path.basename(image_path)
                image_id = int(os.path.splitext(filename)[0])
                
                ocr_result = {
                    "id": image_id,
                    "ocr_predicted": last_4_digits,
                    "cost_usd": round(total_cost, 6),
                    "input_tokens": input_tokens,
                    "output_tokens": output_tokens
                }
                
                model_results.append(ocr_result)
                result_count += 1
                model_total_cost += total_cost
                
                # Save updated results to JSON file named after the model
                with open(f'{model_name}.json', 'w') as f:
                    json.dump(model_results, f, indent=2)
                
            except Exception as e:
                print(f"ERROR with {model_name} on {os.path.basename(image_path)}: {e}")
        
        # Calculate and display cost statistics for this model
        avg_cost_per_image = model_total_cost / result_count if result_count > 0 else 0
        total_cost_all_models += model_total_cost
        
        print(f"\nCost Analysis for {model_name}:")
        print(f"Images processed: {result_count}")
        print(f"Total cost: ${model_total_cost:.6f}")
        print(f"Average cost per image: ${avg_cost_per_image:.6f}")
        print(f"Saved {result_count} results to {model_name}.json")
    
    # Display overall cost summary
    print(f"\n" + "="*50)
    print(f"OVERALL COST SUMMARY:")
    print(f"Total cost across all models: ${total_cost_all_models:.6f}")
    print(f"Total images processed: {len(image_files) * len(models)}")
    print(f"="*50)

if __name__ == "__main__":
    # Test single model on folder
    # test_folder_ocr()
    
    # Uncomment to test all models on folder
    test_all_models_on_folder()