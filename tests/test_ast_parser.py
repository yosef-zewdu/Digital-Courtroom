import pytest
from src.tools.ast_parser import analyze_graph_wiring

def test_analyze_graph_wiring_success(tmp_path):
    # Create a mock Python file with langgraph-like syntax
    code = """
from langgraph.graph import StateGraph
builder = StateGraph(State)
builder.add_node("node1", func1)
builder.add_edge("node1", "node2")
def my_func():
    pass
"""
    src_dir = tmp_path / "src"
    src_dir.mkdir()
    test_file = src_dir / "graph.py"
    test_file.write_text(code)
    
    result = analyze_graph_wiring.invoke({"repo_path": str(tmp_path)})
    
    assert "Detected edges" in result
    assert "fan-out" in result.lower()
    assert "node1" in result
    assert "node2" in result

def test_analyze_graph_wiring_file_not_found():
    result = analyze_graph_wiring.invoke({"repo_path": "/does/not/exist/"})
    assert result.startswith("Error:")
