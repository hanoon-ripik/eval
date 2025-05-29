#!/usr/bin/env python3
"""
Test script for Gemini models with OCR functionality on folder of images
"""

import os
import glob
import json
from pathlib import Path
from tqdm import tqdm
from models import gemini_2_5_pro_preview, gemini_2_5_flash_preview, gemini_2_0_flash

# Configuration
MODEL_TO_USE = gemini_2_0_flash 
FOLDER_PATH = "/Users/hanoon/Documents/eval/direct/clipped"  # Change this to your folder path
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
    return sorted(image_files)

def test_single_image(image_path):
    """Test OCR on a single image"""
    try:
        response = MODEL_TO_USE(
            system_instruction=SYSTEM_INSTRUCTION,
            prompt=TEST_PROMPT,
            image_path=image_path
        )
        
        # Wrap the raw OCR text in JSON format
        ocr_result = {
            "data": os.path.basename(image_path),
            "ocr_predicted": response.strip()
        }
        
        print(json.dumps(ocr_result, indent=2))
        
    except Exception as e:
        print(f"ERROR processing {os.path.basename(image_path)}: {e}")

def test_folder_ocr():
    """Test OCR on all images in the specified folder"""
    # Get all image files
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    # Process each image with progress bar
    for image_path in tqdm(image_files, desc="Processing images"):
        test_single_image(image_path)

def test_all_models_on_folder():
    """Test all available models with OCR on the folder"""
    models = [
        ("Gemini 2.5 Pro Preview", gemini_2_5_pro_preview),
        ("Gemini 2.5 Flash Preview", gemini_2_5_flash_preview),
        ("Gemini 2.0 Flash", gemini_2_0_flash)
    ]
    
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"No image files found in {FOLDER_PATH}")
        return
    
    for model_name, model_func in models:
        for image_path in tqdm(image_files, desc=f"Processing with {model_name}"):
            try:
                response = model_func(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=TEST_PROMPT,
                    image_path=image_path
                )
                
                # Wrap the raw OCR text in JSON format
                ocr_result = {
                    "data": os.path.basename(image_path), 
                    "ocr_predicted": response.strip()
                }
                
                print(json.dumps(ocr_result, indent=2))
                
            except Exception as e:
                print(f"ERROR with {model_name} on {os.path.basename(image_path)}: {e}")

if __name__ == "__main__":
    # Test single model on folder
    test_folder_ocr()
    
    # Uncomment to test all models on folder
    # test_all_models_on_folder()