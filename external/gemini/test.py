#!/usr/bin/env python3
"""
Test script for Gemini models with OCR functionality on folder of images
"""

import os
import glob
from pathlib import Path
from models import gemini_2_5_pro_preview, gemini_2_5_flash_preview, gemini_2_0_flash

# Configuration
MODEL_TO_USE = gemini_2_0_flash 
FOLDER_PATH = "/Users/hanoon/Documents/eval/direct/clipped"  # Change this to your folder path
SUPPORTED_EXTENSIONS = ['.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp']

# System instruction for OCR tasks
SYSTEM_INSTRUCTION = """You are an expert OCR (Optical Character Recognition) assistant. Your task is to:
1. Carefully examine the provided image
2. Extract all visible text accurately, preserving formatting and structure
3. Identify different text elements (headers, body text, numbers, labels, etc.)
4. If the text is unclear or partially obscured, mention this in your response
5. Provide the extracted text in a clear, organized format"""

# Test prompt
TEST_PROMPT = "Please perform OCR on this image and extract all visible text. Organize the extracted text clearly and mention any areas where the text might be unclear or difficult to read."

def get_image_files(folder_path):
    """Get all image files from the specified folder"""
    image_files = []
    for ext in SUPPORTED_EXTENSIONS:
        pattern = os.path.join(folder_path, f"*{ext}")
        image_files.extend(glob.glob(pattern))
    return sorted(image_files)

def test_single_image(image_path):
    """Test OCR on a single image"""
    print(f"\n{'='*100}")
    print(f"📸 IMAGE: {os.path.basename(image_path)}")
    print(f"{'='*100}")
    
    try:
        response = MODEL_TO_USE(
            system_instruction=SYSTEM_INSTRUCTION,
            prompt=TEST_PROMPT,
            image_path=image_path
        )
        
        print("📝 OCR RESULTS:")
        print("-" * 80)
        print(response)
        print("-" * 80)
        print("✅ SUCCESS")
        
    except Exception as e:
        print(f"❌ ERROR: {e}")
    
    print(f"{'='*100}\n")

def test_folder_ocr():
    """Test OCR on all images in the specified folder"""
    print(f"🔍 Testing {MODEL_TO_USE.__name__} with OCR on folder: {FOLDER_PATH}")
    print(f"📁 Scanning for images with extensions: {', '.join(SUPPORTED_EXTENSIONS)}")
    
    # Get all image files
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"❌ No image files found in {FOLDER_PATH}")
        return
    
    print(f"📊 Found {len(image_files)} image(s) to process")
    print(f"🤖 Using model: {MODEL_TO_USE.__name__}")
    
    # Process each image
    for i, image_path in enumerate(image_files, 1):
        print(f"\n🔄 Processing image {i}/{len(image_files)}...")
        test_single_image(image_path)
    
    print(f"🎉 Completed OCR processing for {len(image_files)} images!")

def test_all_models_on_folder():
    """Test all available models with OCR on the folder"""
    models = [
        ("Gemini 2.5 Pro Preview", gemini_2_5_pro_preview),
        ("Gemini 2.5 Flash Preview", gemini_2_5_flash_preview),
        ("Gemini 2.0 Flash", gemini_2_0_flash)
    ]
    
    image_files = get_image_files(FOLDER_PATH)
    
    if not image_files:
        print(f"❌ No image files found in {FOLDER_PATH}")
        return
    
    print(f"📊 Found {len(image_files)} image(s) to process with {len(models)} models")
    
    for model_name, model_func in models:
        print(f"\n{'🚀'*50}")
        print(f"🤖 Testing {model_name}")
        print(f"{'🚀'*50}")
        
        for i, image_path in enumerate(image_files, 1):
            print(f"\n📸 Image {i}/{len(image_files)}: {os.path.basename(image_path)}")
            print("-" * 80)
            
            try:
                response = model_func(
                    system_instruction=SYSTEM_INSTRUCTION,
                    prompt=TEST_PROMPT,
                    image_path=image_path
                )
                
                print("📝 OCR Results:")
                print(response)
                print("✅ SUCCESS")
                
            except Exception as e:
                print(f"❌ Error with {model_name}: {e}")
            
            print("-" * 80)

if __name__ == "__main__":
    print("Gemini OCR Test Script")
    print("=" * 60)
    
    # Test single model on folder
    test_folder_ocr()
    
    # Uncomment to test all models on folder
    # test_all_models_on_folder()