import pytest
from unittest.mock import patch, mock_open
from src.tools.prompt_loader import load_prompt

def test_load_prompt_success():
    fake_prompt_content = "You are a Prosecutor..."
    with patch("src.tools.prompt_loader.Path.exists", return_value=True):
        with patch("src.tools.prompt_loader.Path.read_text", return_value=fake_prompt_content):
            result = load_prompt("prosecutor")
            assert result == fake_prompt_content

def test_load_prompt_fallback():
    # When file doesn't exist, it should return a fallback string
    with patch("src.tools.prompt_loader.Path.exists", return_value=False):
        result = load_prompt("missing_persona")
        assert result == ""
