import pytest
import os
from unittest.mock import patch, MagicMock
from pathlib import Path
from src.tools.vision_tools import extract_images_from_pdf, analyze_image_with_vision, cleanup_vision_images, _active_vision_dirs

def test_extract_images_from_pdf_not_found():
    result = extract_images_from_pdf.invoke({"pdf_path": "/fake/not/exist.pdf"})
    assert result.startswith("Error: PDF not found")

@patch("src.tools.vision_tools.fitz.open")
def test_extract_images_from_pdf_success(mock_fitz_open, tmp_path):
    # Create an actual dummy file so the tool thinks it exists
    fake_pdf = tmp_path / "fake.pdf"
    fake_pdf.touch()
    
    mock_doc = MagicMock()
    mock_page = MagicMock()
    # Return one fake image on the first page
    mock_page.get_images.return_value = [("xref_mock",)]
    mock_doc.extract_image.return_value = {"image": b"fake_byte_data", "ext": "png"}
    
    # Doc has 1 page
    mock_doc.__len__.return_value = 1
    mock_doc.__getitem__.return_value = mock_page
    
    mock_fitz_open.return_value = mock_doc
    
    result = extract_images_from_pdf.invoke({"pdf_path": str(fake_pdf)})
    
    assert "page_1_img_1.png" in result
    assert "auditor_vision_" in result
    
    # Verify cleanup works
    import src.tools.vision_tools
    assert len(src.tools.vision_tools._active_vision_dirs) > 0
    cleanup_vision_images()
    assert len(src.tools.vision_tools._active_vision_dirs) == 0

def test_analyze_image_with_vision_not_found():
    result = analyze_image_with_vision.invoke({"image_path": "/fake/image.png", "prompt": "test"})
    assert result.startswith("Error: Image not found")

@patch("src.tools.vision_tools.InferenceClient")
def test_analyze_image_with_vision_success(mock_hf_client, tmp_path, monkeypatch):
    # Set a fake API key
    monkeypatch.setenv("HF_TOKEN", "fake_key")
    
    fake_img = tmp_path / "fake.png"
    fake_img.write_bytes(b"fake data")
    
    mock_client_instance = object()
    class FakeClient:
        def chat_completion(self, **kwargs):
            mock_response = MagicMock()
            mock_response.choices = [MagicMock()]
            mock_response.choices[0].message.content = "I see a diagram showing the architecture."
            return mock_response
    
    mock_hf_client.return_value = FakeClient()
    
    result = analyze_image_with_vision.invoke({"image_path": str(fake_img), "prompt": "Describe"})
    
    assert result == "I see a diagram showing the architecture."

def test_analyze_image_with_vision_missing_key(tmp_path, monkeypatch):
    # Ensure key is missing
    monkeypatch.delenv("HF_TOKEN", raising=False)
    
    fake_img = tmp_path / "fake.png"
    fake_img.touch()
    
    result = analyze_image_with_vision.invoke({"image_path": str(fake_img), "prompt": "test"})
    assert result.startswith("Error: HUGGING_FACE_KEY not found")
