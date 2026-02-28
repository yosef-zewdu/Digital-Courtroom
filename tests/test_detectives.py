import pytest
from unittest.mock import MagicMock, patch
from pathlib import Path
from src.nodes.detectives import repo_investigator_node, doc_analyst_node, vision_inspector_node
from src.state import AgentState, Evidence

@pytest.fixture
def mock_state():
    return {
        "repo_url": "https://github.com/example/repo",
        "pdf_path": "report.pdf",
        "rubric_dimensions": [
            {"id": "git_forensic_analysis", "target_artifact": "github_repo", "name": "Git Analysis", "forensic_instruction": "test"},
            {"id": "theoretical_depth", "target_artifact": "pdf_report", "name": "Theoretical Depth", "forensic_instruction": "test"},
            {"id": "swarm_visual", "target_artifact": "vision_report", "name": "Visual Analysis", "forensic_instruction": "test"}
        ],
        "evidences": {},
        "opinions": [],
        "final_report": None
    }

@patch("src.nodes.detectives.get_llm")
@patch("src.nodes.detectives.clone_repository")
@patch("src.nodes.detectives._run_forensic_agent")
def test_repo_investigator_node(mock_run_agent, mock_clone, mock_get_llm, mock_state):
    # Setup mocks
    mock_get_llm.return_value = MagicMock()
    mock_clone.invoke.return_value = "/tmp/fake_repo"
    mock_run_agent.return_value = Evidence(goal="test", found=True, location="test", rationale="test", confidence=1.0)
    
    # Run node
    result = repo_investigator_node(mock_state)
    
    # Assertions
    assert "evidences" in result
    assert "git_forensic_analysis" in result["evidences"]
    assert len(result["evidences"]["git_forensic_analysis"]) == 1
    assert isinstance(result["evidences"]["git_forensic_analysis"][0], Evidence)

@patch("src.nodes.detectives.get_llm")
@patch("src.nodes.detectives._run_forensic_agent")
def test_doc_analyst_node(mock_run_agent, mock_get_llm, mock_state):
    mock_get_llm.return_value = MagicMock()
    # Mock the LLM agent output
    mock_run_agent.return_value = Evidence(goal="test docs", found=True, location="report.pdf", rationale="Found in docs", confidence=0.8)
    
    result = doc_analyst_node(mock_state)
    
    assert "evidences" in result
    assert "theoretical_depth" in result["evidences"]
    assert len(result["evidences"]["theoretical_depth"]) == 1
    assert result["evidences"]["theoretical_depth"][0].found is True

@patch("src.nodes.detectives.get_llm")
@patch("src.nodes.detectives._run_forensic_agent")
def test_vision_inspector_node(mock_run_agent, mock_get_llm, mock_state):
    mock_get_llm.return_value = MagicMock()
    # Mock the LLM agent output
    mock_run_agent.return_value = Evidence(goal="test vision", found=True, location="/tmp/image.png", rationale="Found diagram", confidence=0.9)
    
    result = vision_inspector_node(mock_state)
    
    assert "evidences" in result
    assert "swarm_visual" in result["evidences"]
    assert len(result["evidences"]["swarm_visual"]) == 1
    assert result["evidences"]["swarm_visual"][0].found is True
