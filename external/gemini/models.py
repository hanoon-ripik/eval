import os
import google.generativeai as genai
from PIL import Image

# Configure the API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def gemini_2_5_pro_preview(system_instruction, prompt, image_path=None):
    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro-preview-05-06",
        system_instruction=system_instruction
    )
    
    content = [prompt]
    if image_path:
        image = Image.open(image_path)
        content = [prompt, image]
    
    response = model.generate_content(content)
    return response.text.strip()

def gemini_2_5_flash_preview(system_instruction, prompt, image_path=None):
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-preview-05-20",
        system_instruction=system_instruction
    )
    
    content = [prompt]
    if image_path:
        image = Image.open(image_path)
        content = [prompt, image]
    
    response = model.generate_content(content)
    return response.text.strip()

def gemini_2_0_flash(system_instruction, prompt, image_path=None):
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_instruction
    )
    
    content = [prompt]
    if image_path:
        image = Image.open(image_path)
        content = [prompt, image]
    
    response = model.generate_content(content)
    return response.text.strip()

def gemini_1_5_flash(system_instruction, prompt, image_path=None):
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )
    
    content = [prompt]
    if image_path:
        image = Image.open(image_path)
        content = [prompt, image]
    
    response = model.generate_content(content)
    return response.text.strip()

def gemini_1_5_pro(system_instruction, prompt, image_path=None):
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=system_instruction
    )
    
    content = [prompt]
    if image_path:
        image = Image.open(image_path)
        content = [prompt, image]
    
    response = model.generate_content(content)
    return response.text.strip()