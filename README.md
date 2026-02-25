# The Automaton Auditor ⚖️🤖

**The Automaton Auditor** is a sophisticated LangGraph-based forensic agent designed to audit code repositories against technical rubrics. It employs a hierarchical multi-agent architecture to ensure objective, evidence-based evaluations.

## 🚀 Key Features

*   **Hierarchical Multi-Agent Graph**: Orchestrated with LangGraph, featuring parallel fan-out/fan-in for Detectives and Judges.
*   **Multi-LLM Elasticity**: A central `llm_factory.py` allows seamless switching between **Google Gemini (2.0 Flash)** and **OpenRouter (Trinity Large)** backends.
*   **Quota-Resistant RAG**: Uses **Local HuggingFace Embeddings** (`all-MiniLM-L6-v2`) and an In-Memory Vector Store to bypass API quota limits during document analysis.
*   **Forensic AST Extraction**: High-precision file path extraction using LLM-aided **Python AST parsing**, eliminating the fragility of regular expressions.
*   **Deterministic Judicial Synthesis**: A Chief Justice node that applies hardcoded constitutional rules (e.g., Security Capping, Evidence Necessity) to ensure fair and consistent final reports.

## 🏗️ Architecture

The system follows a structured pipeline:
1.  **Context Builder**: Loads the technical rubric and initializes the audit state.
2.  **Detectives (Parallel)**:
    *   **RepoInvestigator**: Analyzes AST, Git history, and tool safety.
    *   **DocAnalyst**: Performs RAG-based analysis on PDF reports to check for theoretical depth and citation accuracy.
3.  **Judges (Parallel)**: Three distinct personas (**Prosecutor**, **Defense**, **Tech Lead**) evaluate the collected evidence from different perspectives.
4.  **Chief Justice**: Synthesizes opinions into a final deterministic `AuditReport.md`.
    
## 📂 Folder Structure

```text
.
├── .github/                # GitHub Actions (CI/CD)
├── audit/                  # Audit logs and reports
├── rubric/                 # Technical rubric definitions
│   └── rubric.json         # Source of truth for audit rules
├── scripts/                # Utility scripts (audit runner, RAG verification)
├── src/                    # Main source code
│   ├── nodes/              # LangGraph node implementations (Detectives, Judges, Justice)
│   ├── tools/              # Specialized tools (RAG, AST parsing, Git)
│   ├── graph.py            # LangGraph orchestration
│   ├── llm_factory.py      # LLM abstraction layer
│   └── state.py            # Agent state definitions
├── tests/                  # Unit and integration tests
├── .gitignore              # Git exclusion rules
├── Dockerfile              # Containerization instructions
├── pyproject.toml          # Dependency and project config
└── README.md
```

## 🛠️ Installation

This project uses `uv` for lightning-fast dependency management.

```bash
# Clone the repository
git clone https://github.com/yosef-zewdu/Digital-Courtroom.git
cd Digital-Courtroom

# Install dependencies and sync environment
uv sync --all-extras --dev
```

## ⚙️ Configuration

Create a `.env` file in the root directory:

```env
# LLM Provider: 'gemini' or 'openrouter'
LLM_PROVIDER=openrouter

# API Keys
GOOGLE_API_KEY=your_gemini_key
OPENROUTER_API_KEY=your_openrouter_key

# Optional Model Overrides
# GEMINI_MODEL=gemini-2.0-flash
# OPENROUTER_MODEL=arcee-ai/trinity-large-preview:free
```

## 📋 Usage

### Run a Full Audit
To audit a repository and a corresponding PDF report:

```bash
uv run python scripts/run_audit.py
```

## 🧪 Testing

Run the test suite using `pytest`:

```bash
uv run pytest
```

---

