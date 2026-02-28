import logging
from typing import Dict
from src.state import AgentState

logger = logging.getLogger(__name__)

def aggregate_evidence(state: AgentState) -> Dict:
    """
    Fan-in synchronization node (The Evidence Guard).
    
    This node acts as a barrier that ensures all parallel detective branches
    (RepoInvestigator, DocAnalyst, VisionInspector) have completed their work.
    It performs a final hygiene check on the collected JSON evidence before
    allowing the Judicial Layer to proceed.
    """
    evidences = state.get("evidences", {})
    rubric_dimensions = state.get("rubric_dimensions", [])
    
    # Check for missing evidence in required dimensions
    found_dimensions = list(evidences.keys())
    required_dimensions = [d["id"] for d in rubric_dimensions]
    
    missing = [d for d in required_dimensions if d not in found_dimensions]
    
    print(f"--- Evidence Aggregator (Fan-In) ---")
    print(f"Collected evidence for {len(found_dimensions)} dimensions.")
    
    if missing:
        print(f"Warning: No evidence collected for dimensions: {missing}")
    else:
        print("Success: All rubric dimensions have associated evidence.")

    # Log summary for debugging the fan-in merge
    for dim_id, items in evidences.items():
        count = len(items)
        found_count = sum(1 for item in items if item.found)
        print(f"  - [{dim_id}]: {count} items ({found_count} found)")

    # Return the evidences (operator.ior will handle the merge in state)
    return {"evidences": evidences}