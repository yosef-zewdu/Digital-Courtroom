from typing import Dict, List
from pathlib import Path
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
import time
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
from src.tools.vision_tools import extract_images_from_pdf, analyze_image_with_vision, cleanup_vision_images


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
    max_retries = 3
    result = None
    for attempt in range(max_retries):
        try:
            result = agent.invoke({"messages": [HumanMessage(content=prompt)]})
            break
        except Exception as e:
            if attempt == max_retries - 1:
                print(f"Failed to investigate {goal} after {max_retries} attempts: {e}")
                return Evidence(
                    goal=goal,
                    found=False,
                    content=f"EVIDENCE_MISSING: Agent encountered API error: {e}",
                    location="API Failure",
                    rationale="API failed to process request.",
                    confidence=0.0
                )
            print(f"API Error during {goal} investigation (attempt {attempt+1}/{max_retries}): {e}. Retrying in 5 seconds...")
            time.sleep(5)
            
    last_msg = result["messages"][-1].content
    
    # Robust parser for agent output
    upper_msg = last_msg.upper()
    found = "EVIDENCE_FOUND" in upper_msg and (
        "EVIDENCE_MISSING" not in upper_msg or 
        upper_msg.find("EVIDENCE_FOUND") < upper_msg.find("EVIDENCE_MISSING")
    )
    
    # Extract robust rationale (skip markdown headers)
    lines = [line.strip() for line in last_msg.split("\n") if line.strip()]
    rationale = "Evidence reviewed."
    for line in lines:
        upper_line = line.upper()
        if "EVIDENCE_FOUND" in upper_line or "EVIDENCE_MISSING" in upper_line or line.startswith("#"):
            continue
        if upper_line.startswith("RATIONALE:"):
            rationale = line[10:].strip()
        else:
            rationale = line
        if rationale:
            break
            
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
    import os
    # Use key 1 for Repo
    key = os.getenv("OPENROUTER_API_KEY")
    llm = get_llm(api_key=key)
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
    
    return {"evidences": evidences}

def doc_analyst_node(state: AgentState) -> Dict:
    """Dynamic agent that audits the PDF report using RAG tools."""
    import os
    # Use key 2 for Docs
    key = os.getenv("OPENROUTER_API_KEY_2") or os.getenv("OPENROUTER_API_KEY")
    llm = get_llm(api_key=key)
    # Also provide repo tools so the doc analyst can cross-reference file paths!
    tools = [query_pdf_report, extract_paths_from_pdf, clone_repository, list_files, read_file]
    
    pdf_path = state.get("pdf_path")
    repo_url = state.get("repo_url")
    dimensions = [d for d in state.get("rubric_dimensions", []) if d.get("target_artifact") == "pdf_report"]
    
    evidences = {}
    for dim in dimensions:
        dim_id = dim["id"]
        instruction = dim["forensic_instruction"]
        full_instruction = f"Repository URL: {repo_url}\nPDF Path: {pdf_path}\n{instruction}"
        
        print(f"Agent investigating documentation: {dim_id}")
        ev = _run_forensic_agent(llm, tools, full_instruction, dim["name"])
        evidences[dim_id] = [ev]
        
    return {"evidences": evidences}

def vision_inspector_node(state: AgentState) -> Dict:
    """Dynamic agent that audits visual diagrams using Qwen2.5-VL via Hugging Face."""
    import os
    # Use key 3 for Vision
    key = os.getenv("OPENROUTER_API_KEY_3") or os.getenv("OPENROUTER_API_KEY")
    llm = get_llm(api_key=key)
    # Note: tools are bound to the agent
    tools = [extract_images_from_pdf, analyze_image_with_vision]
    
    pdf_path = state.get("pdf_path")
    
    dimensions = [d for d in state.get("rubric_dimensions", []) if d.get("target_artifact") == "vision_report"]
    
    if not dimensions:
        dimensions = [d for d in state.get("rubric_dimensions", []) if "diagram" in d.get("name", "").lower() or d.get("id") == "swarm_visual"]

    evidences = {}
    for dim in dimensions:
        dim_id = dim["id"]
        instruction = dim["forensic_instruction"]
        # Explicitly tell the agent which model to use for vision tasks via tool description or instruction
        full_instruction = f"PDF Path: {pdf_path}\nUSE Qwen2.5-VL for visual analysis.\n{instruction}"
        
        print(f"Agent investigating visuals: {dim_id}")
        ev = _run_forensic_agent(llm, tools, full_instruction, dim["name"])
        evidences[dim_id] = [ev]
    
    return {"evidences": evidences}