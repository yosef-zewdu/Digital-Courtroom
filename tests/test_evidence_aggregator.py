import pytest
from src.nodes.evidence_aggregator import aggregate_evidence
from src.state import Evidence

@pytest.fixture
def base_state():
    return {
        "rubric_dimensions": [
            {"id": "dim_1"},
            {"id": "dim_2"}
        ],
        "evidences": {}
    }

def test_aggregate_evidence_all_present(base_state):
    """Test standard behavior when all dimensions have evidence."""
    base_state["evidences"] = {
        "dim_1": [Evidence(goal="goal1", found=True, location="test", rationale="test", confidence=1.0)],
        "dim_2": [Evidence(goal="goal2", found=False, location="test", rationale="test", confidence=1.0)]
    }
    
    result = aggregate_evidence(base_state)
    
    # Aggregator should pass through the evidences unchanged for the reducer to handle
    assert "evidences" in result
    assert "dim_1" in result["evidences"]
    assert "dim_2" in result["evidences"]

def test_aggregate_evidence_missing_dimension(base_state, capfd):
    """Test behavior when a dimension is missing (should flag warning)."""
    base_state["evidences"] = {
        "dim_1": [Evidence(goal="goal1", found=True, location="test", rationale="test", confidence=1.0)]
        # dim_2 is missing
    }
    
    result = aggregate_evidence(base_state)
    
    # Capture print output to verify warning was logged
    out, err = capfd.readouterr()
    assert "Warning: No evidence collected for dimensions: ['dim_2']" in out
    
    assert "evidences" in result
    assert "dim_1" in result["evidences"]
    assert "dim_2" not in result["evidences"]

def test_aggregate_evidence_empty_state_and_rubric():
    """Test edge case with completely empty state."""
    state = {"rubric_dimensions": [], "evidences": {}}
    result = aggregate_evidence(state)
    
    assert "evidences" in result
    assert result["evidences"] == {}
