from typing import Dict, List
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from src.state import AgentState, Evidence
from src.llm_factory import get_llm
from src.tools.repo_tools import (
    clone_repository, 
    list_files, 
    read_file, 
    run_git_log, 
    grep_search, 
    cleanup_temp_dirs
)
from src.tools.ast_parser import analyze_graph_wiring
from src.tools.docs_tools import query_pdf_report, extract_paths_from_pdf

def _run_forensic_agent(llm, tools, instruction: str, goal: str) -> Evidence:
    """Runs a ReAct agent to collect evidence for a specific goal."""
    agent = create_react_agent(llm, tools)
    
    prompt = f"""
    You are a forensic detective. Your goal is to collect evidence for: {goal}
    
    Instruction: {instruction}
    
    Use the provided tools to verify the claim. 
    Once you have enough evidence, provide a final answer starting with 'EVIDENCE_FOUND:' or 'EVIDENCE_MISSING:'.
    Include:
    - Rationale: Why you reached this conclusion.
    - Location: Where you found it (file path, commit hash, etc).
    - Confidence: A float 0.0-1.0.
    """
    
    result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
    last_msg = result["messages"][-1].content
    
    # Simple parser for agent output
    found = "EVIDENCE_FOUND:" in last_msg
    rationale = last_msg.split("\n")[0] # First line as rationale summary
    
    return Evidence(
        goal=goal,
        found=found,
        content=last_msg,
        location="Analyzed via tools",
        rationale=rationale,
        confidence=0.9 # Default for agentic run
    )

def repo_investigator_node(state: AgentState) -> Dict:
    """Dynamic agent that audits the repository using tools."""
    llm = get_llm()
    tools = [clone_repository, list_files, read_file, run_git_log, grep_search, analyze_graph_wiring]
    
    repo_url = state.get("repo_url")
    dimensions = [d for d in state.get("rubric_dimensions", []) if d.get("target_artifact") == "github_repo"]
    
    evidences = {}
    for dim in dimensions:
        dim_id = dim["id"]
        instruction = dim["forensic_instruction"]
        # Include repo_url in the instruction so the LLM knows what to clone
        full_instruction = f"Repository URL: {repo_url}\n{instruction}"
        
        print(f"Agent investigating dimension: {dim_id}")
        ev = _run_forensic_agent(llm, tools, full_instruction, dim["name"])
        evidences[dim_id] = [ev]
    
    # Cleanup any temp dirs created during this node's run
    cleanup_temp_dirs()
    return {"evidences": evidences}

def doc_analyst_node(state: AgentState) -> Dict:
    """Dynamic agent that audits the PDF report using RAG and path extraction."""
    llm = get_llm()
    tools = [query_pdf_report, extract_paths_from_pdf]
    
    pdf_path = state.get("pdf_path")
    dimensions = [d for d in state.get("rubric_dimensions", []) if d.get("target_artifact") == "pdf_report"]
    
    evidences = {}
    for dim in dimensions:
        dim_id = dim["id"]
        instruction = dim["forensic_instruction"]
        full_instruction = f"PDF Path: {pdf_path}\n{instruction}"
        
        print(f"Agent investigating documentation: {dim_id}")
        ev = _run_forensic_agent(llm, tools, full_instruction, dim["name"])
        evidences[dim_id] = [ev]
        
    return {"evidences": evidences}

def vision_inspector_node(state: AgentState) -> Dict:
    """Dynamic agent that audits visual diagrams from the report."""
    # Placeholder for vision agent - in a real system, you'd add vision-capable tools
    return {"evidences": {"swarm_visual": [Evidence(goal="Analyze diagrams", found=False, location="N/A", rationale="Vision integration pending", confidence=1.0)]}}