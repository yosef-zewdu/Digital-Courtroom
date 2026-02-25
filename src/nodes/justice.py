from datetime import datetime
from typing import Dict, List, Optional
from src.state import AgentState, AuditReport, CriterionResult, JudicialOpinion

def synthesize_verdicts(state: AgentState) -> Dict:
    """
    ChiefJustice node: deterministic synthesis of judicial opinions.
    Applies rules from the PDF: Security, Evidence, Functionality.
    """
    rubric_dimensions = state.get("rubric_dimensions", [])
    opinions = state.get("opinions", [])
    evidences = state.get("evidences", {})
    
    criterion_results: List[CriterionResult] = []
    
    for dimension in rubric_dimensions:
        dim_id = dimension.get("id")
        dim_name = dimension.get("name", dim_id)
        
        # Get opinions for this dimension
        dim_opinions = [op for op in opinions if op.criterion_id == dim_id]
        
        prosecutor_op = next((op for op in dim_opinions if op.judge == "Prosecutor"), None)
        defense_op = next((op for op in dim_opinions if op.judge == "Defense"), None)
        techlead_op = next((op for op in dim_opinions if op.judge == "TechLead"), None)
        
        # Rules logic
        scores = [op.score for op in dim_opinions]
        avg_score = sum(scores) / len(scores) if scores else 1.0
        final_score = avg_score
        
        applied_rules = []
        
        # Rule of Security
        if prosecutor_op and prosecutor_op.score <= 2 and "security" in prosecutor_op.argument.lower():
            # Check if there is actual evidence for security flaw
            has_security_evidence = any(
                ev.found is False and "security" in ev.goal.lower() 
                for ev_list in evidences.values() for ev in ev_list
            ) # Simplified check
            if has_security_evidence:
                final_score = min(final_score, 3.0)
                applied_rules.append("Rule of Security")
        
        # Rule of Evidence (Hallucination check)
        if defense_op:
            # If defense claims something that evidence says is missing
            # Simplified: check if any cited evidence was actually NOT found
            any_hallucination = any(
                ev.found is False for dim_ev in evidences.values() for ev in dim_ev 
                if ev.goal.lower() in defense_op.argument.lower() # Rough check
            )
            if any_hallucination:
                final_score = max(1.0, final_score - 1.0)
                applied_rules.append("Rule of Evidence (Hallucination)")

        # Rule of Functionality
        if dim_id == "graph_orchestration" and techlead_op:
            if techlead_op.score >= 4:
                final_score = max(final_score, techlead_op.score)
                applied_rules.append("Rule of Functionality")

        # Dissent check
        score_variance = max(scores) - min(scores) if len(scores) > 1 else 0
        dissent_summary = None
        if score_variance > 2:
            dissent_summary = f"High variance ({score_variance}) detected between judges."
            if prosecutor_op and defense_op:
                dissent_summary += f" Prosecutor: {prosecutor_op.score}, Defense: {defense_op.score}."

        final_score_int = int(round(final_score))
        
        # Remediation
        remediation = f"Fix concerns raised by judges for {dim_name}."
        if prosecutor_op and prosecutor_op.score < 3:
            remediation += f" Prosecutor concerns: {prosecutor_op.argument[:100]}"
        
        criterion_results.append(CriterionResult(
            dimension_id=dim_id,
            dimension_name=dim_name,
            final_score=final_score_int,
            judge_opinions=dim_opinions,
            dissent_summary=dissent_summary,
            remediation=remediation
        ))

    # Build AuditReport
    overall_score = sum(c.final_score for c in criterion_results) / len(criterion_results) if criterion_results else 0.0
    
    audit_report = AuditReport(
        repo_url=state.get("repo_url", ""),
        executive_summary=f"Audit completed on {datetime.now().isoformat()}. Overall Grade: {overall_score:.2f}/5.0",
        overall_score=overall_score,
        criteria=criterion_results,
        remediation_plan="\n".join([f"- {c.dimension_name}: {c.remediation}" for c in criterion_results if c.final_score < 4])
    )
    
    return {"final_report": audit_report}

def generate_report_markdown(report: AuditReport) -> str:
    """Renders the AuditReport as Markdown."""
    sections = [
        f"# Audit Report: {report.repo_url}",
        f"\n## Executive Summary\n{report.executive_summary}",
        f"**Overall Score**: {report.overall_score:.2f}/5.0",
        "\n## Criterion Breakdown"
    ]
    
    for c in report.criteria:
        sections.append(f"### {c.dimension_name}")
        sections.append(f"**Final Score**: {c.final_score}/5")
        if c.dissent_summary:
            sections.append(f"> **Dissent**: {c.dissent_summary}")
        sections.append(f"**Remediation**: {c.remediation}")
        sections.append("\nOpinions:")
        for op in c.judge_opinions:
            sections.append(f"- **{op.judge}** ({op.score}/5): {op.argument}")
            
    sections.append("\n## Remediation Plan")
    sections.append(report.remediation_plan)
    
    return "\n".join(sections)
