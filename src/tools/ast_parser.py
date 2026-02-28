import ast
from pathlib import Path
from langchain_core.tools import tool

@tool
def analyze_graph_wiring(repo_path: str) -> str:
    """
    Analyzes the LangGraph StateGraph wiring in src/graph.py using AST.
    Returns a textual description of the edges and detects parallel fan-out.
    """
    path = Path(repo_path) / "src/graph.py"
    if not path.exists():
        return "Error: src/graph.py not found."
    
    try:
        tree = ast.parse(path.read_text())
        edges = []
        
        for node in ast.walk(tree):
            if isinstance(node, ast.Call):
                if isinstance(node.func, ast.Attribute) and node.func.attr == "add_edge":
                    if len(node.args) >= 2:
                        src = ""
                        if isinstance(node.args[0], ast.Constant):
                            src = node.args[0].value
                        dst = ""
                        if isinstance(node.args[1], ast.Constant):
                            dst = node.args[1].value
                        
                        edges.append((src, dst))

        # Simple fan-out detection
        sources = [e[0] for e in edges if e[0]]
        fan_out_sources = [s for s in set(sources) if sources.count(s) > 1]
        
        report = f"Detected edges: {edges}\n"
        if fan_out_sources:
            report += f"Fan-out detected from nodes: {fan_out_sources}"
        else:
            report += "No parallel fan-out detected (purely linear flow)."
            
        return report
    except Exception as e:
        return f"Error parsing graph.py: {str(e)}"