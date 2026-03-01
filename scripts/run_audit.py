import sys
import os
sys.path.append(os.getcwd())

from src.graph import build_graph
from src.state import AgentState

def main():
    graph = build_graph()

    initial_state: AgentState = {
        "repo_url": "https://github.com/yosef-zewdu/Digital-Courtroom.git",
        "pdf_path": "reports/Architecture_Report.md.pdf",
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "final_report": None
    }

    print("--- Running The Automaton Auditor (Synchronous) ---")
    final_state = graph.invoke(initial_state)

    print("\n" + "="*50)
    print("      THE DIGITAL COURTROOM: TRIAL LOG")
    print("="*50)

    rubric_dims = {d['id']: d for d in final_state.get('rubric_dimensions', [])}
    evidences = final_state.get('evidences', {})
    opinions = final_state.get('opinions', [])

    for dim_id, dimension in rubric_dims.items():
        print(f"\n>>> CRITERION: {dimension['name']} ({dim_id})")
        print(f"    Protocol: {dimension['forensic_instruction'][:100]}...")
        
        # 1. Show Detective Evidence
        print(f"\n    [FORENSIC EVIDENCE]")
        dim_evidences = evidences.get(dim_id, [])
        if not dim_evidences:
            print("    - No evidence items found.")
        for ev in dim_evidences:
            status = "✅ FOUND" if ev.found else "❌ MISSING"
            print(f"    - {status} at {ev.location}")
            print(f"      Rationale: {ev.rationale}")
            if ev.content:
                snippet = str(ev.content).strip()[:200].replace('\n', ' ')
                print(f"      Data: {snippet}...")

        # 2. Show Judicial Opinions
        print(f"\n    [JUDICIAL DEBATE]")
        dim_opinions = [op for op in opinions if op.criterion_id == dim_id]
        if not dim_opinions:
            print("    - No opinions rendered.")
        for op in dim_opinions:
            # Color/Label the judges
            label = f"[{op.judge.upper()}]"
            print(f"    - {label:<12} Score: {op.score}/5")
            print(f"      Argument: {op.argument}")
            if op.cited_evidence:
                print(f"      Citations: {op.cited_evidence}")
        
        print("-" * 50)

    if final_state.get("final_report"):
        print("\n" + "="*50)
        print("      FINAL AUDIT VERDICT")
        print("="*50)
        print(f"Overall Score: {final_state['final_report'].overall_score}")
        print(f"Summary: {final_state['final_report'].executive_summary[:500]}...")

if __name__ == "__main__":
    main()
