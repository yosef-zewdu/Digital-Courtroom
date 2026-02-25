from src.state import AgentState

def aggregate_evidence(state: AgentState) -> AgentState:
    """
    Fan-in barrier: ensures all parallel detective evidence is collected.
    Since operator.ior handles merging, this node primarily acts as a checkpoint.
    """
    # We could perform validation here if needed
    return state