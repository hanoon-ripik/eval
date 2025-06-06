#!/usr/bin/env python3
"""
Test script for Claude models via OpenRouter with OCR functionality on folder of images
"""

import os
import glob
import json
from pathlib import Path
from tqdm import tqdm
from models import claude_sonnet_4, claude_3_7_sonnet, claude_3_5_haiku, claude_3_5_sonnet

# Configuration
MODEL_TO_USE = claude_sonnet_4  # Change this to test different models
FOLDER_PATH = "/Users/hanoon/Documents/eval/helper/clipped"  # Change this to your folder path
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

# System instruction for OCR tasks
SYSTEM_INSTRUCTION = """You are an OCR assistant. You must ONLY return the extracted text from the image. Return NOTHING else - no explanations, no formatting, no additional words, no styling, no markdown. Just the raw text that you see in the image."""

# Test prompt
TEST_PROMPT = """Extract all visible text from this image using OCR. Return ONLY the raw text you see. Do not include any other words, explanations, or formatting. Just the text content."""

def get_image_files(folder_path):
    """Get all image files from the specified folder"""
    image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        pattern = os.path.join(folder_path, f"*{ext}")
        image_files.extend(glob.glob(pattern))
    return sorted(image_files[:10])  # Limit to 10 for testing

def test_single_image(image_path):
    """Test OCR on a single image"""
    try:
        response = MODEL_TO_USE(
            system_instruction=SYSTEM_INSTRUCTION,
            prompt=TEST_PROMPT,
            image_path=image_path
        )
        
        # Extract text from Claude response format
        if isinstance(response, dict) and 'choices' in response:
            ocr_text = response['choices'][0]['message']['content']
        else:
            ocr_text = str(response)
        
        # Wrap the raw OCR text in JSON format
        ocr_result = {
            "data": os.path.basename(image_path),
            "ocr_predicted": ocr_text.strip()
        }
        
        return ocr_result
        
    except Exception as e:
        print(f"ERROR processing {os.path.basename(image_path)}: {e}")
        return None

def test_folder_ocr():
    """Test OCR on all images in the specified folder"""
    # Get all image files
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    # Initialize empty JSON array
    all_results = []
    result_count = 0
    
    # Process each image with progress bar
    for image_path in tqdm(image_files, desc="Processing images"):
        result = test_single_image(image_path)
        if result:
            all_results.append(result)
            result_count += 1
            
            # Save updated results to JSON file after each image
            with open('result.json', 'w') as f:
                json.dump(all_results, f, indent=2)
    
    print(f"Saved {result_count} results to result.json")

def test_all_models_on_folder():
    """Test all available Claude models with OCR on the folder"""
    models = [
        ("Claude Sonnet 4", claude_sonnet_4),
        ("Claude 3.7 Sonnet", claude_3_7_sonnet),
        ("Claude 3.5 Haiku", claude_3_5_haiku),
        ("Claude 3.5 Sonnet", claude_3_5_sonnet),
    ]
    
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    # Initialize empty JSON array
    all_results = []
    result_count = 0
    
    for model_name, model_func in models:
        print(f"\nTesting {model_name}...")
        for image_path in tqdm(image_files, desc=f"Processing with {model_name}"):
            try:
                response = model_func(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=TEST_PROMPT,
                    image_path=image_path
                )
                
                # Extract text from Claude response format
                if isinstance(response, dict) and 'choices' in response:
                    ocr_text = response['choices'][0]['message']['content']
                else:
                    ocr_text = str(response)
                
                # Wrap the raw OCR text in JSON format
                ocr_result = {
                    "model": model_name,
                    "data": os.path.basename(image_path), 
                    "ocr_predicted": ocr_text.strip()
                }
                
                all_results.append(ocr_result)
                result_count += 1
                
                # Save updated results to JSON file after each image
                with open('result_all_models.json', 'w') as f:
                    json.dump(all_results, f, indent=2)
                
            except Exception as e:
                print(f"ERROR with {model_name} on {os.path.basename(image_path)}: {e}")
    
    print(f"Saved {result_count} results to result_all_models.json")

def test_simple_prompt():
    """Test a simple text prompt without images"""
    try:
        print("Testing simple text prompt...")
        response = MODEL_TO_USE(
            system_instruction="You are a helpful assistant.",
            prompt="What is 2+2?"
        )
        
        print("Response:")
        if isinstance(response, dict) and 'choices' in response:
            print(response['choices'][0]['message']['content'])
        else:
            print(response)
            
    except Exception as e:
        print(f"ERROR in simple test: {e}")

def test_single_image_with_path(image_path):
    """Test OCR on a specific image path"""
    if not os.path.exists(image_path):
        print(f"Image not found: {image_path}")
        return
    
    print(f"Testing OCR on: {os.path.basename(image_path)}")
    result = test_single_image(image_path)
    
    if result:
        print("OCR Result:")
        print(json.dumps(result, indent=2))
    else:
        print("Failed to process image")

if __name__ == "__main__":
    print("Claude Models Test Script")
    print("=" * 50)
    
    # Test simple prompt first
    test_simple_prompt()
    print("\n" + "=" * 50)
    
    # Test single model on folder
    # print("Testing OCR on image folder...")
    # test_folder_ocr()
    
    # Uncomment to test all models on folder
    # print("\nTesting all models on folder...")
    # test_all_models_on_folder()
    
    # Uncomment to test a single specific image
    # test_single_image_with_path("/path/to/your/image.png")
