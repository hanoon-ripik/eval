import os
import time
import google.generativeai as genai
from PIL import Image

# Configure the API key
genai.configure(api_key=os.environ.get("GEMINI_API_KEY"))

def upload_video_with_retry(video_path, max_retries=3):
    """Upload video with retry logic and wait for processing"""
    for attempt in range(max_retries):
        try:
            print(f"Uploading {os.path.basename(video_path)}... (attempt {attempt + 1})")
            video = genai.upload_file(video_path)
            
            # Wait for video to be processed
            while video.state.name == "PROCESSING":
                print("Processing video...")
                time.sleep(2)
                video = genai.get_file(video.name)
            
            if video.state.name == "ACTIVE":
                print(f"Video {os.path.basename(video_path)} ready for processing")
                return video
            else:
                print(f"Video {os.path.basename(video_path)} failed to process, state: {video.state.name}")
                
        except Exception as e:
            print(f"Upload attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:
                time.sleep(5 * (attempt + 1))  # Exponential backoff
    
    raise Exception(f"Failed to upload video after {max_retries} attempts")
def gemini_2_5_pro_preview(system_instruction, prompt, image_path=None, video_path=None):
    model = genai.GenerativeModel(
        model_name="gemini-2.5-pro-preview-05-06",
        system_instruction=system_instruction
    )
    
    content = [prompt]
    if image_path:
        image = Image.open(image_path)
        content = [prompt, image]
    elif video_path:
        video = upload_video_with_retry(video_path)
        content = [prompt, video]
    
    response = model.generate_content(content)
    return response.text.strip()

def gemini_2_5_flash_preview(system_instruction, prompt, image_path=None, video_path=None):
    model = genai.GenerativeModel(
        model_name="gemini-2.5-flash-preview-05-20",
        system_instruction=system_instruction
    )
    
    content = [prompt]
    if image_path:
        image = Image.open(image_path)
        content = [prompt, image]
    elif video_path:
        video = upload_video_with_retry(video_path)
        content = [prompt, video]
    
    response = model.generate_content(content)
    return response.text.strip()

def gemini_2_0_flash(system_instruction, prompt, image_path=None, video_path=None):
    model = genai.GenerativeModel(
        model_name="gemini-2.0-flash",
        system_instruction=system_instruction
    )
    
    content = [prompt]
    if image_path:
        image = Image.open(image_path)
        content = [prompt, image]
    elif video_path:
        video = upload_video_with_retry(video_path)
        content = [prompt, video]
    
    response = model.generate_content(content)
    return response.text.strip()

def gemini_1_5_flash(system_instruction, prompt, image_path=None, video_path=None):
    model = genai.GenerativeModel(
        model_name="gemini-1.5-flash",
        system_instruction=system_instruction
    )
    
    content = [prompt]
    if image_path:
        image = Image.open(image_path)
        content = [prompt, image]
    elif video_path:
        video = upload_video_with_retry(video_path)
        content = [prompt, video]
    
    response = model.generate_content(content)
    return response.text.strip()

def gemini_1_5_pro(system_instruction, prompt, image_path=None, video_path=None):
    model = genai.GenerativeModel(
        model_name="gemini-1.5-pro",
        system_instruction=system_instruction
    )
    
    content = [prompt]
    if image_path:
        image = Image.open(image_path)
        content = [prompt, image]
    elif video_path:
        video = upload_video_with_retry(video_path)
        content = [prompt, video]
    
    response = model.generate_content(content)
    return response.text.strip()