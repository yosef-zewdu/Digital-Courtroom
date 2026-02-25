import sys
import os
sys.path.append(os.getcwd())

from src.graph import build_graph
from src.state import AgentState
# from src.nodes.justice import generate_report_markdown

def main():
    graph = build_graph()

    initial_state: AgentState = {
        "repo_url": "https://github.com/yosef-zewdu/Digital-Courtroom.git",
        "pdf_path": "report/interim_report.pdf",
        "rubric_dimensions": [],
        "evidences": {},
        "opinions": [],
        "final_report": None
    }

    
    
    # png_data = graph.get_graph().draw_mermaid_png()

    # # Save it to a file
    # with open("graph.png", "wb") as f:
    #     f.write(png_data)
    #     print("Graph saved to graph.png")
        
    print("--- Running The Automaton Auditor ---")
    final_state = graph.invoke(initial_state)

    print(final_state.keys())
    print("\n")
    # print(final_state['repo_url'])
    # print("\n")
    # print(final_state['pdf_path'])
    # print("\n")
    # print(final_state['rubric_dimensions'])
    # print("\n")
    print(final_state['evidences'])
    # print("\n")
    # print(final_state['opinions'])
    # print("\n")
    # print(final_state['final_report'])
    
    # if final_state.get("final_report"):
    #     report_md = generate_report_markdown(final_state["final_report"])
        
    #     # Save to file
    #     output_path = "audit/report_bypeer_generated/audit_report.md"
    #     with open(output_path, "w") as f:
    #         f.write(report_md)
        
    #     print(f"--- Audit Report Generated: {output_path} ---")
    #     print(report_md[:1000] + "...")
    # else:
    #     print("--- Error: No report generated ---")

if __name__ == "__main__":
    main()
