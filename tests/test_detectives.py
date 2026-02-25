import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.nodes.detectives import repo_investigator_node, doc_analyst_node, vision_inspector_node
from src.state import AgentState, Evidence

@pytest.fixture
def mock_state():
    return {
        "repo_url": "https://github.com/example/repo.git",
        "pdf_path": "report.pdf",
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "final_report": None
    }

@patch("src.nodes.detectives.clone_repo_sandboxed")
@patch("src.nodes.detectives.verify_state_structure")
@patch("src.nodes.detectives.analyze_graph_wiring")
@patch("src.nodes.detectives.analyze_git_narrative")
def test_repo_investigator_node(mock_git, mock_wiring, mock_state_struct, mock_clone, mock_state):
    # Setup mocks
    mock_clone.return_value = (Path("/tmp/repo"), "/tmp/dir")
    mock_state_struct.return_value = Evidence(goal="test", found=True, location="test", rationale="test", confidence=1.0)
    mock_wiring.return_value = Evidence(goal="test", found=True, location="test", rationale="test", confidence=1.0)
    mock_git.return_value = Evidence(goal="test", found=True, location="test", rationale="test", confidence=1.0)
    
    # Run node
    result = repo_investigator_node(mock_state)
    
    # Assertions
    assert "evidences" in result
    assert "git_forensic_analysis" in result["evidences"]
    assert "state_management_rigor" in result["evidences"]
    assert "graph_orchestration" in result["evidences"]
    assert "safe_tool_engineering" in result["evidences"]
    assert len(result["evidences"]["git_forensic_analysis"]) == 1
    assert isinstance(result["evidences"]["git_forensic_analysis"][0], Evidence)

def test_doc_analyst_node_placeholder(mock_state):
    # Since current implementation of doc_analyst_node is mostly empty/placeholder
    result = doc_analyst_node(mock_state)
    assert "evidences" in result
    assert "theoretical_depth" in result["evidences"]
    assert "report_accuracy" in result["evidences"]

def test_vision_inspector_node(mock_state):
    result = vision_inspector_node(mock_state)
    assert "evidences" in result
    assert "swarm_visual" in result["evidences"]
    assert len(result["evidences"]["swarm_visual"]) == 1
    assert result["evidences"]["swarm_visual"][0].found is False
