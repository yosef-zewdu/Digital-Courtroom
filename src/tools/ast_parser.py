import ast
from pathlib import Path
from src.state import Evidence

def analyze_graph_wiring(repo_path: Path) -> Evidence:
    """Forensic Protocol B: Graph Wiring Analysis."""
    graph_path = repo_path / "src/graph.py"
    if not graph_path.exists():
        return Evidence(
            goal="Analyze graph wiring for parallelism",
            found=False,
            location="src/graph.py",
            content=None,
            rationale="src/graph.py not found.",
            confidence=1.0
        )
    
    try:
        tree = ast.parse(graph_path.read_text())
        fan_out_detected = False
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

        # Simple fan-out detection: multiple edges from the same source
        sources = [e[0] for e in edges if e[0]]
        for s in set(sources):
            if sources.count(s) > 1:
                fan_out_detected = True
                break
        
        return Evidence(
            goal="Analyze graph wiring for parallelism",
            found=fan_out_detected,
            location="src/graph.py",
            content=str(edges),
            rationale=f"Detected edges: {edges}. Fan-out detected: {fan_out_detected}.",
            confidence=1.0
        )
    except Exception as e:
        return Evidence(
            goal="Analyze graph wiring for parallelism",
            found=False,
            location="src/graph.py",
            content=str(e),
            rationale=f"Error parsing graph.py: {str(e)}",
            confidence=0.5
        )