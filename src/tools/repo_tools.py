import ast
import json
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Optional
from src.state import Evidence

def verify_state_structure(repo_path: Path) -> Evidence:
    """Forensic Protocol A: State Structure Analysis."""
    state_py = repo_path / "src/state.py"
    graph_py = repo_path / "src/graph.py"
    
    exists = state_py.exists() or graph_py.exists()
    content = ""
    if state_py.exists():
        content = state_py.read_text()
    elif graph_py.exists():
        content = graph_py.read_text()
        
    has_pydantic = "BaseModel" in content
    has_typeddict = "TypedDict" in content
    has_evidence = "Evidence" in content
    has_opinion = "JudicialOpinion" in content
    
    rationale = []
    if not (state_py.exists() or graph_py.exists()):
        rationale.append("Neither src/state.py nor src/graph.py found.")
    else:
        rationale.append(f"Found state definitions. Pydantic: {has_pydantic}, TypedDict: {has_typeddict}.")
        if has_evidence and has_opinion:
            rationale.append("State maintains collections of Evidence and JudicialOpinion.")
        else:
            rationale.append("Missing Evidence or JudicialOpinion collections in state.")

    return Evidence(
        goal="Verify existence of typed state and rigor",
        found=exists and (has_pydantic or has_typeddict) and has_evidence and has_opinion,
        location="src/state.py",
        content=content[:1000] if exists else None,
        rationale=" ".join(rationale),
        confidence=1.0
    )

def analyze_git_narrative(repo_path: Path) -> Evidence:
    """Forensic Protocol C: Git Narrative Analysis."""
    try:
        # Command requested by PDF: git log --oneline --reverse
        result = subprocess.run(
            ["git", "-C", str(repo_path), "log", "--oneline", "--reverse"],
            capture_output=True,
            text=True,
            check=True
        )
        logs = result.stdout.strip().split("\n")
        
        num_commits = len(logs)
        # Check for progression keywords (simplified)
        progression_found = any("setup" in l.lower() or "env" in l.lower() for l in logs) and \
                            any("tool" in l.lower() or "ast" in l.lower() for l in logs) and \
                            any("graph" in l.lower() or "wire" in l.lower() or "node" in l.lower() for l in logs)
        
        is_monolithic = num_commits <= 1 or any("init" in logs[0].lower() and num_commits < 3 for l in logs)
        
        rationale = f"Detected {num_commits} commits."
        if is_monolithic:
            rationale += " Appears to be a monolithic or 'bulk upload' pattern."
        elif progression_found:
            rationale += " History shows clear progression: Environment -> Tooling -> Graph."
        else:
            rationale += " History appears iterative but specific progression keywords not found in all phases."

        return Evidence(
            goal="Analyze git history narrative for iterative progression",
            found=num_commits > 3 and not is_monolithic,
            location="git log",
            content="\n".join(logs),
            rationale=rationale,
            confidence=0.9
        )
    except Exception as e:
        return Evidence(
            goal="Analyze git history narrative",
            found=False,
            location="git log",
            content=str(e),
            rationale=f"Error extracting git log: {str(e)}",
            confidence=0.5
        )

def clone_repo_sandboxed(repo_url: str):
    """Safety: Clone to temporary directory."""
    temp_dir = tempfile.TemporaryDirectory()
    path = Path(temp_dir.name)

    try:
        subprocess.run(
            ["git", "clone", repo_url, str(path)],
            check=True,
            capture_output=True,
        )
        return path, temp_dir
    except Exception as e:
        # Return none if clone fails, but handle it in the node
        return None, temp_dir