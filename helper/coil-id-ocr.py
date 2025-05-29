import torch
from PIL import Image
from transformers import AutoProcessor, AutoModelForCausalLM

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
dtype = torch.float16 if torch.cuda.is_available() else torch.float32

model = AutoModelForCausalLM.from_pretrained(
    "microsoft/Florence-2-large",
    trust_remote_code=True,
    torch_dtype=dtype
).to(device)

processor = AutoProcessor.from_pretrained(
    "microsoft/Florence-2-large",
    trust_remote_code=True
)

prompt = "<OCR>"
image = Image.open("1740381605009_2501220054.png")

inputs = processor(text=prompt, images=image, return_tensors="pt").to(device, dtype)
generated_ids = model.generate(
    input_ids=inputs.input_ids,
    pixel_values=inputs.pixel_values,
    max_new_tokens=256
)

raw_output = processor.batch_decode(generated_ids, skip_special_tokens=True)[0]
ocr_text = processor.post_process_generation(
    raw_output,
    task=prompt,
    image_size=(image.width, image.height)
)

print(ocr_text)