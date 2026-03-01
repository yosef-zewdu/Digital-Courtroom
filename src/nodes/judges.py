from typing import Any, Dict, List, Literal, Optional
import time
from langchain_core.messages import SystemMessage, HumanMessage
from src.state import AgentState, Evidence, JudicialOpinion
from src.llm_factory import get_llm
from src.tools.prompt_loader import load_prompt

def _get_evidence_for_dimension(state: AgentState, dimension_id: str) -> List[Evidence]:
    """Get all evidence items for a specific dimension."""
    return state.get("evidences", {}).get(dimension_id, [])

def _run_judge_persona(
    state: AgentState, 
    persona_name: str, 
    judge_role: Literal["Prosecutor", "Defense", "TechLead"],
    api_key: Optional[str] = None
) -> Dict:
    """Common engine for all Judicial personas."""
    llm = get_llm(api_key=api_key)
    # Bind structured output to the JudicialOpinion model
    structured_llm = llm.with_structured_output(JudicialOpinion)
    
    system_prompt_content = load_prompt(persona_name)
    rubric_dimensions = state.get("rubric_dimensions", [])
    all_opinions = []
    max_retries = 3
    
    for dimension in rubric_dimensions:
        dim_id = dimension.get("id")
        dim_name = dimension.get("name", dim_id)
        evidence_items = _get_evidence_for_dimension(state, dim_id)
        
        # Prepare evidence summary for the judge
        evidence_summary = ""
        if not evidence_items:
            evidence_summary = "NO EVIDENCE COLLECTED."
        else:
            for i, ev in enumerate(evidence_items):
                evidence_summary += f"\n--- Evidence Item {i} ---\n"
                evidence_summary += f"Goal: {ev.goal}\n"
                evidence_summary += f"Found: {ev.found}\n"
                evidence_summary += f"Location: {ev.location}\n"
                evidence_summary += f"Rationale: {ev.rationale}\n"
                evidence_summary += f"Content Snippet: {str(ev.content)[:1000]}\n"

        user_prompt = f"""
        Rubric Dimension: {dim_name}
        Forensic Protocol: {dimension.get('forensic_instruction')}
        Success Pattern: {dimension.get('success_pattern')}
        Failure Pattern: {dimension.get('failure_pattern')}
        
        Collected Forensic Evidence:
        {evidence_summary}
        
        Evaluate this evidence against the rubric dimension using your specific lens.
        Your output MUST include:
        - judge: "{judge_role}"
        - criterion_id: "{dim_id}"
        - score: 1-5
        - argument: Detailed reasoning based on the evidence.
        - cited_evidence: List of evidence locations or IDs you relied on.
        """
        
        print(f"Judge ({judge_role}) analyzing dimension: {dim_id}...")
        
        max_retries = 3
        opinion = None
        for attempt in range(max_retries):
            try:
                opinion = structured_llm.invoke([
                    SystemMessage(content=system_prompt_content),
                    HumanMessage(content=user_prompt)
                ])
                break
            except Exception as e:
                if attempt == max_retries - 1:
                    print(f"Error invoking judge {judge_role} for {dim_id} after {max_retries} retries: {e}")
                    # Fallback for malformed output: force a failure score or retry logic
                    opinion = JudicialOpinion(
                        judge=judge_role,
                        criterion_id=dim_id,
                        score=1,
                        argument=f"JUDICIAL_FAILURE: Judge encountered exception after {max_retries} attempts: {str(e)}",
                        cited_evidence=[]
                    )
                else:
                    print(f"API Error during {judge_role} analysis for {dim_id} (attempt {attempt+1}/{max_retries}): {e}. Retrying in 5 seconds...")
                    time.sleep(5)

        # Ensure the judge and criterion_id are explicitly set if not returned correctly
        opinion.judge = judge_role
        opinion.criterion_id = dim_id
        all_opinions.append(opinion)
            
    return {"opinions": all_opinions}

def judge_prosecutor(state: AgentState) -> Dict:
    """The Prosecutor: Scrutinizes for gaps and security flaws."""
    # Use key 1 or default
    import os
    key = os.getenv("OPENROUTER_API_KEY")
    return _run_judge_persona(state, "prosecutor", "Prosecutor", api_key=key)

def judge_defense(state: AgentState) -> Dict:
    """The Defense: Highlights effort and creative workarounds."""
    # Use key 2 or fall back to default
    import os
    key = os.getenv("OPENROUTER_API_KEY_2")
    return _run_judge_persona(state, "defense", "Defense", api_key=key)

def judge_techlead(state: AgentState) -> Dict:
    """The Tech Lead: Evaluates architectural soundness and pragmatic viability."""
    # Use key 3 or fall back to default
    import os
    key = os.getenv("OPENROUTER_API_KEY_3") 
    return _run_judge_persona(state, "tech_lead", "TechLead", api_key=key)
