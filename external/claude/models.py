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
    """Make a request to OpenRouter API for Claude models"""
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
        return result
        
    except requests.exceptions.RequestException as e:
        print(f"Request failed: {e}")
        if hasattr(e, 'response') and e.response is not None:
            print(f"Response: {e.response.text}")
        raise

def claude_sonnet_4(system_instruction, prompt, image_path=None, video_path=None):
    """Anthropic Claude Sonnet 4 model via OpenRouter"""
    if video_path:
        print("Warning: Video processing not supported for Claude models")
    
    return make_openrouter_request("anthropic/claude-sonnet-4", system_instruction, prompt, image_path)

def claude_3_7_sonnet(system_instruction, prompt, image_path=None, video_path=None):
    """Anthropic Claude 3.7 Sonnet model via OpenRouter"""
    if video_path:
        print("Warning: Video processing not supported for Claude models")
    
    return make_openrouter_request("anthropic/claude-3.7-sonnet", system_instruction, prompt, image_path)

def claude_3_5_haiku(system_instruction, prompt, image_path=None, video_path=None):
    """Anthropic Claude 3.5 Haiku model via OpenRouter"""
    if video_path:
        print("Warning: Video processing not supported for Claude models")
    
    return make_openrouter_request("anthropic/claude-3.5-haiku", system_instruction, prompt, image_path)

def claude_3_5_sonnet(system_instruction, prompt, image_path=None, video_path=None):
    """Anthropic Claude 3.5 Sonnet model via OpenRouter"""
    if video_path:
        print("Warning: Video processing not supported for Claude models")
    
    return make_openrouter_request("anthropic/claude-3.5-sonnet", system_instruction, prompt, image_path)