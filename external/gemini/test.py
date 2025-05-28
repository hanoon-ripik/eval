#!/usr/bin/env python3
"""
Test script for Gemini models with OCR functionality
"""

from models import gemini_2_5_pro_preview, gemini_2_5_flash_preview, gemini_2_0_flash

# Configuration
MODEL_TO_USE = gemini_2_0_flash 
IMAGE_PATH = "1740420075465_2501240027.png"

# System instruction for OCR tasks
SYSTEM_INSTRUCTION = """You are an expert OCR (Optical Character Recognition) assistant. Your task is to:
1. Carefully examine the provided image
2. Extract all visible text accurately, preserving formatting and structure
3. Identify different text elements (headers, body text, numbers, labels, etc.)
4. If the text is unclear or partially obscured, mention this in your response
5. Provide the extracted text in a clear, organized format"""

# Test prompt
TEST_PROMPT = "Please perform OCR on this image and extract all visible text. Organize the extracted text clearly and mention any areas where the text might be unclear or difficult to read."

def test_gemini_ocr():
    """Test the selected Gemini model with OCR functionality"""
    print(f"Testing {MODEL_TO_USE.__name__} with OCR...")
    print(f"Image: {IMAGE_PATH}")
    print("-" * 60)
    
    try:
        # Call the model with image
        response = MODEL_TO_USE(
            system_instruction=SYSTEM_INSTRUCTION,
            prompt=TEST_PROMPT,
            image_path=IMAGE_PATH
        )
        
        print("OCR Results:")
        print("=" * 60)
        print(response)
        print("=" * 60)
        
    except Exception as e:
        print(f"Error occurred: {e}")

def test_all_models():
    """Test all available models with OCR"""
    models = [
        ("Gemini 2.5 Pro Preview", gemini_2_5_pro_preview),
        ("Gemini 2.5 Flash Preview", gemini_2_5_flash_preview),
        ("Gemini 2.0 Flash", gemini_2_0_flash)
    ]
    
    for model_name, model_func in models:
        print(f"\n{'='*80}")
        print(f"Testing {model_name}")
        print(f"{'='*80}")
        
        try:
            response = model_func(
                system_instruction=SYSTEM_INSTRUCTION,
                prompt=TEST_PROMPT,
                image_path=IMAGE_PATH
            )
            
            print("OCR Results:")
            print("-" * 60)
            print(response)
            print("-" * 60)
            
        except Exception as e:
            print(f"Error with {model_name}: {e}")

if __name__ == "__main__":
    print("Gemini OCR Test Script")
    print("=" * 60)
    
    # Test single model
    test_gemini_ocr()
    
    # Test all
    # test_all_models()