import subprocess
import tempfile
import os
from pathlib import Path
from typing import List, Optional
from langchain_core.tools import tool

# Global list to keep track of temporary directories during a run
# In a production system, this would be managed more strictly (e.g. per-session)
_active_temp_dirs = []

@tool
def clone_repository(repo_url: str) -> str:
    """
    Clones a GitHub repository into a sandboxed temporary directory.
    Returns the absolute path to the cloned repository.
    """
    temp_dir = tempfile.TemporaryDirectory()
    _active_temp_dirs.append(temp_dir)
    path = Path(temp_dir.name)

    try:
        subprocess.run(
            ["git", "clone", repo_url, str(path)],
            check=True,
            capture_output=True,
            timeout=120
        )
        return str(path)
    except Exception as e:
        return f"Error cloning repository: {str(e)}"

@tool
def list_files(repo_path: str, recursive: bool = True) -> str:
    """
    Lists files in the repository. Use this to understand the project structure.
    """
    path = Path(repo_path)
    if not path.exists():
        return "Error: Path does not exist."
    
    try:
        ignored = [".git", ".venv", "__pycache__", ".pytest_cache", "node_modules", ".gemini", "audit", ".specify"]
        if recursive:
            files = []
            for f in path.rglob("*"):
                if f.is_file():
                    # Check if any part of the path is in ignored list
                    if not any(ig in f.parts for ig in ignored):
                        files.append(str(f.relative_to(path)))
        else:
            files = [f.name for f in path.iterdir() if f.is_file() and f.name not in ignored]
            
        output = "\n".join(files)
        if len(output) > 8000:
            return output[:8000] + "\n... [LIST TRUNCATED FOR CONTEXT SAFETY] ..."
        return output
    except Exception as e:
        return f"Error listing files: {str(e)}"

@tool
def read_file(repo_path: str, file_path: str) -> str:
    """
    Reads the content of a specific file in the repository.
    """
    full_path = Path(repo_path) / file_path
    if not full_path.exists():
        return f"Error: File {file_path} not found."
    
    try:
        content = full_path.read_text(errors="replace")
        if len(content) > 6000:
            return content[:6000] + "\n... [FILE TRUNCATED FOR CONTEXT SAFETY] ..."
        return content
    except Exception as e:
        return f"Error reading file: {str(e)}"

@tool
def run_git_log(repo_path: str, limit: int = 10) -> str:
    """
    Returns the git commit history of the repository (oneline format).
    """
    try:
        result = subprocess.run(
            ["git", "-C", repo_path, "log", "--oneline", "--reverse", "-n", str(limit)],
            capture_output=True,
            text=True,
            check=True
        )
        return result.stdout
    except Exception as e:
        return f"Error running git log: {str(e)}"

@tool
def grep_search(repo_path: str, pattern: str) -> str:
    """
    Searches for a pattern in all files within the repository.
    """
    try:
        result = subprocess.run(
            ["grep", "-r", "--exclude-dir=.git", "--exclude-dir=.venv", "--exclude-dir=node_modules", "--exclude-dir=.gemini", "--exclude-dir=audit", "--exclude-dir=.specify", pattern, repo_path],
            capture_output=True,
            text=True,
            timeout=30
        )
        return result.stdout[:2000] # Limit output
    except Exception as e:
        return f"Error running grep: {str(e)}"

def cleanup_temp_dirs():
    """Cleans up all temporary directories created during the run."""
    global _active_temp_dirs
    for td in _active_temp_dirs:
        try:
            td.cleanup()
        except:
            pass
    _active_temp_dirs = []