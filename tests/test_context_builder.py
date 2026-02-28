import pytest
from unittest.mock import patch, mock_open
from src.nodes.context_builder import build_context, get_dimension_by_id
from src.state import AgentState

@pytest.fixture
def sample_rubric_json():
    return """
    {
        "rubric_metadata": {"version": "1.0"},
        "dimensions": [
            {"id": "test_dim_1", "name": "Test Dimension 1"},
            {"id": "test_dim_2", "name": "Test Dimension 2"}
        ],
        "synthesis_rules": {"rule_1": "Description"}
    }
    """

def test_build_context_success(sample_rubric_json):
    """Test successful loading of rubric.json."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data=sample_rubric_json)):
            initial_state = {"repo_url": "test", "pdf_path": "test"}
            new_state = build_context(initial_state)
            
            assert new_state["rubric_metadata"] == {"version": "1.0"}
            assert len(new_state["rubric_dimensions"]) == 2
            assert new_state["rubric_dimensions"][0]["id"] == "test_dim_1"
            assert new_state["synthesis_rules"] == {"rule_1": "Description"}
            assert new_state["evidences"] == {}
            assert new_state["opinions"] == []
            assert new_state["final_report"] is None

def test_build_context_missing_file():
    """Test fallback when rubric.json is missing."""
    with patch("pathlib.Path.exists", return_value=False):
        initial_state = {"repo_url": "test", "pdf_path": "test"}
        new_state = build_context(initial_state)
        
        assert new_state["rubric_metadata"] == {}
        assert new_state["rubric_dimensions"] == []
        assert new_state["synthesis_rules"] == {}
        assert new_state["evidences"] == {}
        assert new_state["opinions"] == []
        assert new_state["final_report"] is None

def test_build_context_invalid_json():
    """Test fallback when rubric.json is malformed."""
    with patch("pathlib.Path.exists", return_value=True):
        with patch("builtins.open", mock_open(read_data="INVALID JSON")):
            initial_state = {"repo_url": "test", "pdf_path": "test"}
            new_state = build_context(initial_state)
            
            assert new_state["rubric_dimensions"] == []

def test_get_dimension_by_id():
    """Test utility to fetch dimension by ID."""
    state = {
        "rubric_dimensions": [
            {"id": "dim_a", "name": "A"},
            {"id": "dim_b", "name": "B"}
        ]
    }
    
    assert get_dimension_by_id(state, "dim_a") == {"id": "dim_a", "name": "A"}
    assert get_dimension_by_id(state, "dim_c") is None
