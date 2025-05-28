import os
import base64
from google import genai
from google.genai import types

def gemini_2_5_pro_preview(system_instruction, prompt, image_path=None):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model = "gemini-2.5-pro-preview-05-06"

    parts = []
    if image_path:
        with open(image_path, "rb") as img_file:
            image_data = img_file.read()
        parts.append(
            types.Part.from_bytes(
                mime_type="image/jpeg",
                data=image_data
            )
        )
    parts.append(types.Part.from_text(prompt))

    contents = [
        types.Content(
            role="user",
            parts=parts
        )
    ]

    generate_content_config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="text/plain"
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config
    )
    return response.text.strip()

def gemini_2_5_flash_preview(system_instruction, prompt):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model = "gemini-2.5-flash-preview-05-20"

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(prompt)]
        )
    ]

    generate_content_config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="text/plain"
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config
    )
    return response.text.strip()

def gemini_2_0_flash(system_instruction, prompt):
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
    model = "gemini-2.0-flash"

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(prompt)]
        )
    ]

    generate_content_config = types.GenerateContentConfig(
        system_instruction=system_instruction,
        response_mime_type="text/plain"
    )

    response = client.models.generate_content(
        model=model,
        contents=contents,
        config=generate_content_config
    )
    return response.text.strip()