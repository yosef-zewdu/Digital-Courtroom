import os
import sys
from typing import Dict, List

# Ensure src is in path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langgraph.graph import StateGraph, START, END
from src.state import AgentState
from src.nodes.context_builder import build_context
from src.nodes.detectives import (
    repo_investigator_node,
    doc_analyst_node,
    vision_inspector_node,
)
from src.nodes.evidence_aggregator import aggregate_evidence
from src.nodes.judges import judge_prosecutor, judge_defense, judge_techlead
from src.nodes.justice import synthesize_verdicts, generate_report_markdown

def build_graph():
    builder = StateGraph(AgentState)

    # Add Nodes
    builder.add_node("ContextBuilder", build_context)
    builder.add_node("RepoInvestigator", repo_investigator_node)
    builder.add_node("DocAnalyst", doc_analyst_node)
    builder.add_node("VisionInspector", vision_inspector_node)
    builder.add_node("EvidenceAggregator", aggregate_evidence)
    builder.add_node("Prosecutor", judge_prosecutor)
    builder.add_node("Defense", judge_defense)
    builder.add_node("TechLead", judge_techlead)
    builder.add_node("ChiefJustice", synthesize_verdicts)

    # START -> ContextBuilder
    builder.add_edge(START, "ContextBuilder")

    # ContextBuilder -> Detectives (Parallel Fan-out)
    builder.add_edge("ContextBuilder", "RepoInvestigator")
    builder.add_edge("ContextBuilder", "DocAnalyst")
    builder.add_edge("ContextBuilder", "VisionInspector")

    # Detectives -> Aggregator (Fan-in)
    builder.add_edge("RepoInvestigator", "EvidenceAggregator")
    builder.add_edge("DocAnalyst", "EvidenceAggregator")
    builder.add_edge("VisionInspector", "EvidenceAggregator")

    # Aggregator -> Judges (Parallel Fan-out)
    builder.add_edge("EvidenceAggregator", "Prosecutor")
    builder.add_edge("EvidenceAggregator", "Defense")
    builder.add_edge("EvidenceAggregator", "TechLead")

    # Judges -> ChiefJustice (Fan-in)
    builder.add_edge("Prosecutor", "ChiefJustice")
    builder.add_edge("Defense", "ChiefJustice")
    builder.add_edge("TechLead", "ChiefJustice")

    # Final result
    builder.add_edge("ChiefJustice", END)

    return builder.compile()
