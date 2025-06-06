import os
import json
import requests
import base64
from PIL import Image
import io
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

def encode_image_to_base64(image_path):
    """Convert image to base64 string for API"""
    with Image.open(image_path) as img:
        # Convert to RGB if necessary
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Save to bytes
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG")
        img_bytes = buffered.getvalue()
        
        # Encode to base64
        return base64.b64encode(img_bytes).decode('utf-8')

def make_openrouter_request(model_name, system_instruction, prompt, image_path=None):
    """Make a request to OpenRouter API"""
    headers = {
        "Authorization": f"Bearer {os.environ.get('OPENROUTER_API_KEY')}",
        "Content-Type": "application/json",
    }
    
    messages = []
    
    # Add system message if provided
    if system_instruction:
        messages.append({
            "role": "system",
            "content": system_instruction
        })
    
    # Prepare user message content
    content = [{"type": "text", "text": prompt}]
    
    # Add image if provided
    if image_path:
        base64_image = encode_image_to_base64(image_path)
        content.append({
            "type": "image_url",
            "image_url": {
                "url": f"data:image/jpeg;base64,{base64_image}"
            }
        })
    
    messages.append({
        "role": "user",
        "content": content
    })
    
    data = {
        "model": model_name,
        "messages": messages
    }
    
    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(data)
        )
        response.raise_for_status()
        result = response.json()
        
        # Print usage information if available
        if 'usage' in result:
            print("Usage:", result['usage'])
        
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise

def o4_mini(system_instruction, prompt, image_path=None, video_path=None):
    """OpenAI O4 Mini model via OpenRouter"""
    if video_path:
        print("Warning: Video processing not supported for OpenAI models")
    
    return make_openrouter_request("openai/o4-mini", system_instruction, prompt, image_path)

def gpt_4_1(system_instruction, prompt, image_path=None, video_path=None):
    """OpenAI GPT-4.1 model via OpenRouter"""
    if video_path:
        print("Warning: Video processing not supported for OpenAI models")
    
    return make_openrouter_request("openai/gpt-4.1", system_instruction, prompt, image_path)

def gpt_4_1_mini(system_instruction, prompt, image_path=None, video_path=None):
    """OpenAI GPT-4.1 Mini model via OpenRouter"""
    if video_path:
        print("Warning: Video processing not supported for OpenAI models")
    
    return make_openrouter_request("openai/gpt-4.1-mini", system_instruction, prompt, image_path)

def gpt_4o(system_instruction, prompt, image_path=None, video_path=None):
    """OpenAI ChatGPT-4o Latest model via OpenRouter"""
    if video_path:
        print("Warning: Video processing not supported for OpenAI models")
    
    return make_openrouter_request("openai/chatgpt-4o-latest", system_instruction, prompt, image_path)
