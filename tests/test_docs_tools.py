import pytest
from unittest.mock import patch, MagicMock
from src.tools.docs_tools import query_pdf_report, extract_paths_from_pdf

@patch("src.tools.docs_tools.get_rag")
def test_query_pdf_report_success(mock_get_rag):
    mock_rag = MagicMock()
    mock_rag.query.return_value = "This is a test document containing information about architecture."
    mock_get_rag.return_value = mock_rag
    
    result = query_pdf_report.invoke({"pdf_path": "fake.pdf", "question": "architecture"})
    
    assert "architecture" in result

@patch("src.tools.docs_tools.get_llm")
@patch("src.tools.docs_tools.get_rag")
def test_extract_paths_from_pdf_success(mock_get_rag, mock_get_llm):
    mock_rag = MagicMock()
    mock_rag.document_text = "Check out /src/main.py and also config.json."
    mock_get_rag.return_value = mock_rag
    
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "['/src/main.py', 'config.json']"
    mock_llm.invoke.return_value = mock_response
    mock_get_llm.return_value = mock_llm
    
    result = extract_paths_from_pdf.invoke({"pdf_path": "fake.pdf"})
    
    assert "/src/main.py" in result
    assert "config.json" in result
    assert "Error" not in result
