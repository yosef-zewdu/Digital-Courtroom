import os
import fitz  # PyMuPDF
import base64
import tempfile
import shutil
from pathlib import Path
from typing import List, Dict, Optional
from huggingface_hub import InferenceClient
from langchain_core.tools import tool
from dotenv import load_dotenv

load_dotenv()

# Global registry for vision temp dirs
_active_vision_dirs = []

@tool
def extract_images_from_pdf(pdf_path: str) -> str:
    """
    Extracts all images from a PDF file to a temporary directory.
    Returns a comma-separated list of image paths.
    """
    if not os.path.exists(pdf_path):
        return f"Error: PDF not found at {pdf_path}"
    
    # Use a temporary directory
    temp_dir = tempfile.TemporaryDirectory(prefix="auditor_vision_")
    _active_vision_dirs.append(temp_dir)
    output_path = Path(temp_dir.name)
    
    doc = fitz.open(pdf_path)
    extracted_images = []
    
    for page_index in range(len(doc)):
        page = doc[page_index]
        image_list = page.get_images(full=True)
        
        for img_index, img in enumerate(image_list):
            xref = img[0]
            base_image = doc.extract_image(xref)
            image_bytes = base_image["image"]
            image_ext = base_image["ext"]
            
            image_filename = f"page_{page_index+1}_img_{img_index+1}.{image_ext}"
            image_full_path = output_path / image_filename
            
            with open(image_full_path, "wb") as f:
                f.write(image_bytes)
            
            extracted_images.append(str(image_full_path))
            
    doc.close()
    
    if not extracted_images:
        return "No images found in the PDF."
    
    return ",".join(extracted_images)

@tool
def analyze_image_with_vision(image_path: str, prompt: str) -> str:
    """
    Analyzes an image using Qwen2.5-VL via Hugging Face Inference API.
    Use this to inspect architectural diagrams or visual evidence.
    """
    if not os.path.exists(image_path):
        return f"Error: Image not found at {image_path}"
    
    hf_token = os.getenv("HF_TOKEN")
    if not hf_token:
        return "Error: HUGGING_FACE_KEY not found in .env"
    
    try:
        # Encode image to base64
        with open(image_path, "rb") as image_file:
            encoded_string = base64.b64encode(image_file.read()).decode("utf-8")
        
        client = InferenceClient(api_key=hf_token)
        
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/jpeg;base64,{encoded_string}"}
                    },
                    {
                        "type": "text",
                        "text": prompt
                    }
                ]
            }
        ]
        
        response = client.chat_completion(
            model="Qwen/Qwen2.5-VL-7B-Instruct",
            messages=messages,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        return f"Error analyzing image via Hugging Face API: {str(e)}"

def cleanup_vision_images():
    """Cleans up all temporary vision directories created during the run."""
    global _active_vision_dirs
    for td in _active_vision_dirs:
        try:
            td.cleanup()
        except:
            pass
    _active_vision_dirs = []
