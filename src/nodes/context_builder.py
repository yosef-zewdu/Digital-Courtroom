import json
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.state import AgentState

def build_context(state: AgentState) -> AgentState:
    """Initialize the agent state with rubric dimensions and synthesis rules from rubric/rubric.json."""
    rubric_path = Path("rubric/rubric.json")
    
    if not rubric_path.exists():
        print(f"Warning: {rubric_path} not found. Initializing with empty rubric.")
        return {
            "rubric_metadata": {},
            "rubric_dimensions": [],
            "synthesis_rules": {},
            "evidences": {},
            "opinions": [],
            "final_report": None
        }

    try:
        with open(rubric_path, "r") as f:
            rubric_spec = json.load(f)
            
        return {
            "rubric_metadata": rubric_spec.get("rubric_metadata", {}),
            "rubric_dimensions": rubric_spec.get("dimensions", []),
            "synthesis_rules": rubric_spec.get("synthesis_rules", {}),
            "evidences": {},
            "opinions": [],
            "final_report": None
        }
    except Exception as e:
        print(f"Error loading rubric: {e}")
        return {
            "rubric_metadata": {},
            "rubric_dimensions": [],
            "synthesis_rules": {},
            "evidences": {},
            "opinions": [],
            "final_report": None
        }

def get_dimension_by_id(state: AgentState, dimension_id: str) -> Optional[Dict]:
    """Utility to fetch a dimension's metadata by its ID from the state."""
    for dim in state.get("rubric_dimensions", []):
        if dim.get("id") == dimension_id:
            return dim
    return None
