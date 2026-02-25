from typing import Dict
from pathlib import Path
from src.tools.repo_tools import (
    clone_repo_sandboxed,
    verify_state_structure,
    analyze_git_narrative,
)
from src.tools.ast_parser import analyze_graph_wiring
from src.state import AgentState, Evidence
from src.tools.docs_tools import ingest_pdf, DocumentRAG, extract_file_paths

def repo_investigator_node(state: AgentState) -> Dict:
    """Collects evidence from the repository."""
    repo_url = state.get("repo_url")
    if not repo_url: return {"evidences": {}}

    repo_path, temp_dir = clone_repo_sandboxed(repo_url)
    if not repo_path:
        return {"evidences": {"safe_tool_engineering": [Evidence(goal="Clone repo safely", found=False, location=repo_url, rationale="Clone failed", confidence=1.0)]}}

    state_ev = verify_state_structure(repo_path)
    wire_ev = analyze_graph_wiring(repo_path)
    git_ev = analyze_git_narrative(repo_path)
    
    tools_path = repo_path / "src/tools"
    has_temp = any("tempfile.TemporaryDirectory()" in f.read_text() for f in tools_path.glob("*.py")) if tools_path.exists() else False
    has_os = any("os.system(" in f.read_text() for f in tools_path.glob("*.py")) if tools_path.exists() else False
    
    safe_ev = Evidence(goal="Safe tool engineering", found=has_temp and not has_os, location="src/tools/", rationale=f"Tempfile: {has_temp}, os.system: {has_os}", confidence=1.0)

    return {"evidences": {"git_forensic_analysis": [git_ev], "state_management_rigor": [state_ev], "graph_orchestration": [wire_ev], "safe_tool_engineering": [safe_ev]}}

def doc_analyst_node(state: AgentState) -> Dict:
    """Collects evidence from the PDF report using RAG (Gemini/OpenRouter)."""
    pdf_path = state.get("pdf_path")
    if not pdf_path or not Path(pdf_path).exists():
        return {"evidences": {
            "theoretical_depth": [Evidence(goal="Analyze depth", found=False, location="Missing", rationale="No PDF found", confidence=1.0)],
            "report_accuracy": [Evidence(goal="Citation Check", found=False, location="Missing", rationale="No PDF found", confidence=1.0)]
        }}

    content = ingest_pdf(pdf_path)
    if not content:
        return {"evidences": {
            "theoretical_depth": [Evidence(goal="Analyze depth", found=False, location=pdf_path, rationale="Failed to parse PDF", confidence=1.0)],
            "report_accuracy": [Evidence(goal="Citation Check", found=False, location=pdf_path, rationale="Failed to parse PDF", confidence=1.0)]
        }}

    rag = DocumentRAG(content)
    
    # Analyze Depth using LLM
    depth_answer = rag.query("Does this report explain Dialectical Synthesis, Fan-In/Fan-Out, and Metacognition in detail? If so, provide a brief summary of its explanation.")
    found_depth = "Information not found" not in depth_answer and len(depth_answer) > 50
    
    depth_ev = Evidence(
        goal="Theoretical Depth", 
        found=found_depth, 
        location=pdf_path, 
        content=depth_answer[:1000], 
        rationale=depth_answer[:200], 
        confidence=0.9
    )
    
    # Citation Check
    paths = extract_file_paths(content)
    # We need a repo path to verify these. In a real run, RepoInvestigator would have set this.
    # For now, we'll assume the files are checked against the current CWD if repo_path is not in state
    # (Though RepoInvestigator should ideally pass it)
    hallucinated = [p for p in paths if not Path(p).exists()]
    
    accuracy_ev = Evidence(
        goal="Citation Check", 
        found=len(hallucinated) == 0 and len(paths) > 0, 
        location=pdf_path, 
        rationale=f"Verified {len(paths)-len(hallucinated)} paths. Hallucinated: {hallucinated}", 
        confidence=0.8
    )

    return {"evidences": {"theoretical_depth": [depth_ev], "report_accuracy": [accuracy_ev]}}

def vision_inspector_node(state: AgentState) -> Dict:
    return {"evidences": {"swarm_visual": [Evidence(goal="Analyze diagrams", found=False, location="N/A", rationale="Optional", confidence=1.0)]}}