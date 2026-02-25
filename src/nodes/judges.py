from __future__ import annotations
from typing import Any, Dict, List, Literal
from src.state import AgentState, Evidence, JudicialOpinion

# LLM client wrapper placeholder
class LLMClient:
    def __init__(self, model_name: str = "gpt-4", temperature: float = 0.0):
        self.model_name = model_name
        self.temperature = temperature
    
    def generate_structured_opinion(
        self,
        prompt: str,
        criterion_id: str,
        judge_role: Literal["Prosecutor", "Defense", "TechLead"],
    ) -> JudicialOpinion:
        # Placeholder: In a real system, this would call an LLM with structured output
        # For now, we return a mock opinion based on the prompt/role
        score = 3
        if judge_role == "Prosecutor":
            score = 2
        elif judge_role == "Defense":
            score = 4
        
        return JudicialOpinion(
            judge=judge_role,
            criterion_id=criterion_id,
            score=score,
            argument=f"Mock opinion for {criterion_id} by {judge_role}. LLM integration pending.",
            cited_evidence=[] # In real use, this would be filled by the LLM
        )

def _get_evidence_for_dimension(state: AgentState, dimension_id: str) -> List[Evidence]:
    """Get all evidence items for a specific dimension."""
    return state.get("evidences", {}).get(dimension_id, [])

def _build_judge_prompt(
    dimension: Dict[str, Any],
    evidence_items: List[Evidence],
    judge_role: Literal["Prosecutor", "Defense", "TechLead"],
) -> str:
    """Build judge-specific prompt with persona instructions from PDF."""
    dimension_name = dimension.get("name", "")
    forensic_instruction = dimension.get("forensic_instruction", "")
    success_pattern = dimension.get("success_pattern", "")
    failure_pattern = dimension.get("failure_pattern", "")
    
    evidence_summary = "\n".join([
        f"- Location: {ev.location}\n  Rationale: {ev.rationale}\n  Content: {str(ev.content)[:200]}"
        for ev in evidence_items
    ])
    
    if judge_role == "Prosecutor":
        system_prompt = "You are the Prosecutor. Trust No One. Assume 'Vibe Coding'. Scrutinize evidence for gaps, security flaws, and laziness."
    elif judge_role == "Defense":
        system_prompt = "You are the Defense Attorney. Reward Effort and Intent. Look for the 'Spirit of the Law'. Highlight creative workarounds and deep thought."
    else: # TechLead
        system_prompt = "You are the Tech Lead. Pragmatic lens. 'Does it actually work? Is it maintainable?' Evaluate architectural soundness and code cleanliness."
    
    user_prompt = f"""Assess: {dimension_name}
Forensic Protocol: {forensic_instruction}
Success Pattern: {success_pattern}
Failure Pattern: {failure_pattern}

Evidence Collected:
{evidence_summary}

Provide your JudicialOpinion with score (1-5), arguments, and cited evidence IDs."""
    
    return f"{system_prompt}\n\n{user_prompt}"

def judge_prosecutor(state: AgentState) -> Dict:
    return _judge_dimensions(state, "Prosecutor")

def judge_defense(state: AgentState) -> Dict:
    return _judge_dimensions(state, "Defense")

def judge_techlead(state: AgentState) -> Dict:
    return _judge_dimensions(state, "TechLead")

def _judge_dimensions(
    state: AgentState,
    judge_role: Literal["Prosecutor", "Defense", "TechLead"],
) -> Dict:
    """Common logic for all judge nodes."""
    rubric_dimensions = state.get("rubric_dimensions", [])
    opinions = []
    
    llm_client = LLMClient()
    
    for dimension in rubric_dimensions:
        dimension_id = dimension.get("id")
        evidence_items = _get_evidence_for_dimension(state, dimension_id)
        
        prompt = _build_judge_prompt(dimension, evidence_items, judge_role)
        
        opinion = llm_client.generate_structured_opinion(
            prompt=prompt,
            criterion_id=dimension_id,
            judge_role=judge_role,
        )
        opinions.append(opinion)
    
    return {"opinions": opinions}
