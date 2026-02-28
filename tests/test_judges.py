import pytest
from unittest.mock import patch, MagicMock
from src.nodes.judges import judge_prosecutor, judge_defense, judge_techlead, JudicialOpinion
from src.state import Evidence

@pytest.fixture
def base_state_with_evidence():
    return {
        "rubric_dimensions": [
            {"id": "dim_1", "name": "Dimension 1", "forensic_instruction": "Test", "target_artifact": "pdf_report"}
        ],
        "evidences": {
            "dim_1": [Evidence(goal="Test goal", found=True, location="test.file", rationale="It exists", confidence=1.0)]
        },
        "opinions": []
    }

def mock_llm_response(judge_role):
    # Create a MagicMock to simulate the structured LLM
    mock_structured_llm = MagicMock()
    # When invoked, it returns a JudicialOpinion
    mock_structured_llm.invoke.return_value = JudicialOpinion(
        judge=judge_role,
        criterion_id="dim_1",
        score=3,
        argument=f"I am the {judge_role} and I score this a 3.",
        cited_evidence=["test.file"]
    )
    
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    return mock_llm

@patch("src.nodes.judges.get_llm")
def test_judge_prosecutor(mock_get_llm, base_state_with_evidence):
    mock_get_llm.return_value = mock_llm_response("Prosecutor")
    
    result = judge_prosecutor(base_state_with_evidence)
    
    assert "opinions" in result
    assert len(result["opinions"]) == 1
    assert result["opinions"][0].judge == "Prosecutor"
    assert result["opinions"][0].criterion_id == "dim_1"
    assert result["opinions"][0].score == 3
    assert "Prosecutor" in result["opinions"][0].argument

@patch("src.nodes.judges.get_llm")
def test_judge_defense(mock_get_llm, base_state_with_evidence):
    mock_get_llm.return_value = mock_llm_response("Defense")
    
    result = judge_defense(base_state_with_evidence)
    
    assert "opinions" in result
    assert len(result["opinions"]) == 1
    assert result["opinions"][0].judge == "Defense"

@patch("src.nodes.judges.get_llm")
def test_judge_techlead(mock_get_llm, base_state_with_evidence):
    mock_get_llm.return_value = mock_llm_response("TechLead")
    
    result = judge_techlead(base_state_with_evidence)
    
    assert "opinions" in result
    assert len(result["opinions"]) == 1
    assert result["opinions"][0].judge == "TechLead"

@patch("src.nodes.judges.get_llm")
def test_judge_handles_exception(mock_get_llm, base_state_with_evidence):
    # Simulate an error during LLM invocation
    mock_structured_llm = MagicMock()
    mock_structured_llm.invoke.side_effect = Exception("API Timeout")
    
    mock_llm = MagicMock()
    mock_llm.with_structured_output.return_value = mock_structured_llm
    mock_get_llm.return_value = mock_llm
    
    result = judge_prosecutor(base_state_with_evidence)
    
    assert "opinions" in result
    assert len(result["opinions"]) == 1
    # Fallback should kick in
    assert result["opinions"][0].score == 1
    assert "API Timeout" in result["opinions"][0].argument
