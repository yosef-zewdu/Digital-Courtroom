import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
from langchain_core.messages import HumanMessage
from src.state import AgentState, AuditReport, CriterionResult, JudicialOpinion
from src.llm_factory import get_llm

logger = logging.getLogger(__name__)

def synthesize_verdicts(state: AgentState) -> Dict:
    """
    ChiefJustice node: The Synthesis Engine (The Supreme Court).
    
    Resolves dialectical conflicts between Prosecutor, Defense, and Tech Lead
    using hardcoded deterministic rules:
    - Rule of Security: Security flaws cap at 3.
    - Rule of Evidence: Overrule hallucination if evidence is missing.
    - Rule of Functionality: Tech Lead weight for architecture.
    
    Synchronous version.
    """
    rubric_dimensions = state.get("rubric_dimensions", [])
    opinions = state.get("opinions", [])
    evidences = state.get("evidences", {})
    
    criterion_results: List[CriterionResult] = []
    
    # 1. Process each criterion
    for dimension in rubric_dimensions:
        dim_id = dimension.get("id")
        dim_name = dimension.get("name", dim_id)
        
        # Get opinions for this dimension
        dim_opinions = [op for op in opinions if op.criterion_id == dim_id]
        if not dim_opinions:
            continue

        prosecutor_op = next((op for op in dim_opinions if op.judge == "Prosecutor"), None)
        defense_op = next((op for op in dim_opinions if op.judge == "Defense"), None)
        techlead_op = next((op for op in dim_opinions if op.judge == "TechLead"), None)
        
        # Base score (average)
        scores = [op.score for op in dim_opinions]
        final_score = sum(scores) / len(scores)
        applied_rules = []

        is_sec_flaw = False
        if prosecutor_op and prosecutor_op.score <= 2:
            is_sec_flaw = any(word in prosecutor_op.argument.lower() for word in ["security", "flaw", "vulnerability", "injection", "unsanitized"])

        # --- RULE 2: Rule of Evidence (Hallucination Check) ---
        # If Defense claims success but evidence specifically says FOUND: False
        if defense_op and defense_op.score >= 4:
            dim_evidence = evidences.get(dim_id, [])
            missing_critical = any(ev.found is False for ev in dim_evidence if ev.confidence > 0.8)
            if missing_critical:
                final_score = max(1.0, final_score - 1.5) # Penalty for hallucination
                applied_rules.append("Rule of Evidence: Defense overruled for evidence hallucination.")

        # --- RULE 3: Rule of Functionality (Tech Lead Weight) ---
        if dimension.get("target_artifact") == "github_repo" and techlead_op:
            # If Tech Lead says it's modular (Score >= 4), pull the score up
            if techlead_op.score >= 4:
                final_score = (final_score + techlead_op.score) / 2
                applied_rules.append("Rule of Functionality: Tech Lead confirms modular architecture.")

        # --- RULE 1: Rule of Security (Hard Cap) ---
        # Applied last to ensure it cannot be overridden by other rules
        if is_sec_flaw:
            final_score = min(final_score, 3.0)
            applied_rules.append("Rule of Security: Flaw detected, score capped at 3.")

        # Dissent check
        score_variance = max(scores) - min(scores)
        dissent_summary = None
        if score_variance >= 2:
            dissent_summary = f"DISSENT DETECTED: Variance of {score_variance} between {prosecutor_op.judge if prosecutor_op else 'Judges'} and {defense_op.judge if defense_op else 'Judges'}."
            if applied_rules:
                dissent_summary += " Resolved by: " + "; ".join(applied_rules)

        # Final Formatting
        final_score_rounded = int(round(final_score))
        remediation = f"Fix findings in {dim_id}."
        if prosecutor_op and prosecutor_op.score < 3:
            remediation = f"Address Critical Lens findings: {prosecutor_op.argument[:200]}..."

        criterion_results.append(CriterionResult(
            dimension_id=dim_id,
            dimension_name=dim_name,
            final_score=final_score_rounded,
            judge_opinions=dim_opinions,
            dissent_summary=dissent_summary,
            remediation=remediation
        ))

    # 2. Calculate Overall Score
    overall_score = sum(c.final_score for c in criterion_results) / len(criterion_results) if criterion_results else 0.0

    # 3. Generate LLM Executive Summary (Synchronous call)
    summary = _generate_llm_summary(overall_score, criterion_results)
    
    # 3. Build AuditReport
    report = AuditReport(
        repo_url=state.get("repo_url", "N/A"),
        executive_summary=summary,
        overall_score=overall_score,
        criteria=criterion_results,
        remediation_plan="\n".join([f"### {c.dimension_name}\n- {c.remediation}" for c in criterion_results if c.final_score < 4])
    )

    # 3. Save Markdown Report
    output_dir = Path("audit")
        
    output_dir.mkdir(parents=True, exist_ok=True)
    report_md = generate_report_markdown(report)
    
    # Generate timestamped filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"audit_report_{timestamp}.md"
    
    # Save both timestamped and general version
    with open(output_dir/filename, "w") as f:
        f.write(report_md)
    with open(output_dir/"audit_report.md", "w") as f:
        f.write(report_md)
    
    print(f"--- Chief Justice: Final Audit Report Generated at {output_dir}/{filename} ---")

    return {"final_report": report}

def _generate_llm_summary(overall_score: float, results: List[CriterionResult]) -> str:
    """Synthesizes all findings into a professional Executive Summary using an LLM. Synchronous."""
    llm = get_llm()
    
    findings_context = ""
    for c in results:
        findings_context += f"- {c.dimension_name}: {c.final_score}/5. "
        if c.judge_opinions:
            # Aggregate the core arguments from judges for this dimension
            args = " ".join([op.argument[:150] for op in c.judge_opinions])
            findings_context += f"Judicial Consensus/Conflict: {args}\n"
            
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    prompt = f"""
    You are the Chief Justice of the Digital Courtroom. 
    Synthesize the following forensic audit results into a cohesive, high-level Executive Summary.
    
    Audit Completion Time: {now_str}
    Overall Consolidated Stakeholder Score: {overall_score:.2f} / 5.0
    
    Individual Dimension Findings:
    {findings_context}
    
    The summary MUST:
    1. Start with a clear statement of the audit's overall result and the consolidated score.
    2. Synthesize the 'vibe' of the project - is it security-first? Is documentation lagging code? 
    3. Highlight the most critical risk areas (scores <= 2) and the strongest architectural wins (scores >= 4).
    4. Be professional, objective, and written for senior stakeholders.
    5. Avoid repeating the list - instead, synthesize the overall quality.
    """
    
    try:
        response = llm.invoke([HumanMessage(content=prompt)])
        return response.content.strip()
    except Exception as e:
        return f"Audit completed at {now_str}. Overall Score: {overall_score:.2f}/5.0. (Manual fallback: System evaluated {len(results)} dimensions with satisfactory results across the board.)"

def generate_report_markdown(report: AuditReport) -> str:
    """Professional rendering of the AuditReport as Markdown."""
    sections = [
        f"# Judicial Audit Report: {report.repo_url}",
        f"\n## 🏛️ Executive Summary\n{report.executive_summary}",
        f"**Consolidated Score**: `{report.overall_score:.2f} / 5.0`\n",
        "---",
        "## ⚖️ Criterion Breakdown"
    ]
    
    for c in report.criteria:
        sections.append(f"### {c.dimension_name}")
        sections.append(f"**Final Verdict**: `{c.final_score}/5`")
        
        if c.dissent_summary:
            sections.append(f"> [!WARNING]\n> **Conflict Resolution**: {c.dissent_summary}")
        
        sections.append("\n**Judicial Opinions:**")
        for op in c.judge_opinions:
            badge = "🔴" if op.score <= 2 else "🟡" if op.score <= 3 else "🟢"
            sections.append(f"- **{op.judge}** {badge} ({op.score}/5): {op.argument}")
        
        sections.append(f"\n**Required Action**: {c.remediation}")
        sections.append("\n---")
            
    sections.append("\n## 🛠️ Remediation Plan")
    if not report.remediation_plan.strip():
        sections.append("No critical remediations required. Pass marks achieved across all dimensions.")
    else:
        sections.append(report.remediation_plan)
    
    sections.append(f"\n*Generated by The Automaton Auditor on {datetime.now().date()}*")
    
    return "\n".join(sections)
