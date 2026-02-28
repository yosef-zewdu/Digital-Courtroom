import os
from pathlib import Path

def load_prompt(prompt_name: str) -> str:
    """Loads a prompt template from the src/prompts directory."""
    prompt_path = Path(__file__).parent.parent / "prompts" / f"{prompt_name}.txt"
    if not prompt_path.exists():
        print(f"Warning: Prompt file {prompt_path} not found.")
        return ""
    return prompt_path.read_text(encoding="utf-8")
