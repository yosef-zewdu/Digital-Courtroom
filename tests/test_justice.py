import pytest
from unittest.mock import patch, MagicMock
from src.nodes.justice import synthesize_verdicts, generate_report_markdown
from src.state import JudicialOpinion, Evidence

@pytest.fixture
def mock_state_with_opinions():
    return {
        "repo_url": "https://github.com/example/repo",
        "rubric_dimensions": [
            {"id": "dim_1", "name": "Dimension 1", "target_artifact": "github_repo"}
        ],
        "opinions": [
            JudicialOpinion(judge="Prosecutor", criterion_id="dim_1", score=4, argument="Good", cited_evidence=[]),
            JudicialOpinion(judge="Defense", criterion_id="dim_1", score=5, argument="Excellent", cited_evidence=[]),
            JudicialOpinion(judge="TechLead", criterion_id="dim_1", score=4, argument="Solid", cited_evidence=[])
        ],
        "evidences": {
            "dim_1": [Evidence(goal="goal", found=True, location="test", rationale="Found it", confidence=1.0)]
        }
    }

@patch("src.nodes.justice.Path.mkdir")
@patch("builtins.open")
def test_synthesize_verdicts_base_case(mock_open, mock_mkdir, mock_state_with_opinions):
    """Test standard synthesis without triggering special rules."""
    result = synthesize_verdicts(mock_state_with_opinions)
    
    assert "final_report" in result
    report = result["final_report"]
    assert report.repo_url == "https://github.com/example/repo"
    assert len(report.criteria) == 1
    
    # Base score = (4 + 5 + 4) / 3 = 4.33, but TechLead score 4 pulls it up (Rule of Functionality)
    # (4.33 + 4) / 2 = 4.16 => rounded to 4
    assert report.criteria[0].final_score == 4

@patch("src.nodes.justice.Path.mkdir")
@patch("builtins.open")
def test_rule_of_security_cap(mock_open, mock_mkdir, mock_state_with_opinions):
    """Test that a security flaw reported by Prosecutor caps the score at 3."""
    mock_state_with_opinions["opinions"][0] = JudicialOpinion(
        judge="Prosecutor", criterion_id="dim_1", score=1, argument="Critical security vulnerability found.", cited_evidence=[]
    )
    
    result = synthesize_verdicts(mock_state_with_opinions)
    
    # Base score = (1 + 5 + 4) / 3 = 3.33
    # Rule of Security caps at 3.0
    assert result["final_report"].criteria[0].final_score == 3
    assert "Rule of Security" in result["final_report"].criteria[0].dissent_summary

@patch("src.nodes.justice.Path.mkdir")
@patch("builtins.open")
def test_rule_of_evidence_hallucination(mock_open, mock_mkdir, mock_state_with_opinions):
    """Test that Defense hallucinating a high score without missing evidence triggers a penalty."""
    # Defense claims 5, but evidence is actually missing
    mock_state_with_opinions["opinions"] = [
        JudicialOpinion(judge="Defense", criterion_id="dim_1", score=5, argument="Great", cited_evidence=[])
    ]
    mock_state_with_opinions["evidences"]["dim_1"][0].found = False
    
    result = synthesize_verdicts(mock_state_with_opinions)
    
    # Base score = 5.0. Missing evidence penalty = -1.5 => 3.5 => rounded to 4
    assert result["final_report"].criteria[0].final_score == 4
    # Wait, the rule says max 1.0, wait, it says max(1.0, final_score - 1.5). 5 - 1.5 = 3.5.
    
@patch("src.nodes.justice.Path.mkdir")
@patch("builtins.open")
def test_timestamped_report_generation(mock_open, mock_mkdir, mock_state_with_opinions):
    """Test that it tries to save the files with timestamping."""
    with patch("src.nodes.justice.datetime") as mock_datetime:
        mock_datetime.now.return_value.strftime.return_value = "20240101_120000"
        
        synthesize_verdicts(mock_state_with_opinions)
        
        # Check if the correct files were opened for writing
        # open is called twice: once for timestamped, once for standard name
        calls = mock_open.call_args_list
        assert any("audit_report_20240101_120000.md" in str(call) for call in calls)
        assert any("audit_report.md" in str(call) for call in calls)

def test_generate_report_markdown():
    """Test markdown rendering function."""
    from src.state import AuditReport, CriterionResult
    
    report = AuditReport(
        repo_url="test_repo",
        executive_summary="Summary",
        overall_score=4.5,
        criteria=[
            CriterionResult(dimension_id="dim_1", dimension_name="Dim 1", final_score=5, judge_opinions=[], remediation="None")
        ],
        remediation_plan="Fix bugs."
    )
    
    md = generate_report_markdown(report)
    
    assert "# Judicial Audit Report: test_repo" in md
    assert "Consolidated Score" in md
    assert "Fix bugs." in md
