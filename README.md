# 🤖 LLM Agent Trace & Reliability Analyzer

An observability, tracing, and reliability analysis system for tool-using LLM agents.

---

## Problem Statement

Modern AI agents rely on tools—such as calculators, web search engines, and databases—to execute complex multi-step reasoning tasks. When an agent produces an incorrect response or fails completely, traditional application logs (`ERROR 500: Execution failed`) fail to provide system-level visibility:

- *Which specific step or tool call originated the failure?*
- *Was the issue caused by wrong tool selection, invalid arguments, network timeouts, or bad outputs?*
- *Did transient retry mechanisms successfully recover the agent, or did they introduce excessive latency?*
- *How does trajectory step length impact reliability and overall task completion?*

This project bridges this observability gap by wrapping a structured instrumentation layer around a tool-using AI agent. It records granular execution traces across multi-step trajectories and visualizes reliability metrics, failure taxonomies, and step-by-step logs through an interactive Streamlit dashboard.

---

## Architecture & Data Flow

                     ┌─────────────────┐
                     │      USER       │
                     └────────┬────────┘
                              │ prompt
                              ▼
                     ┌─────────────────┐
                     │    AgentLoop    │
                     └────────┬────────┘
                              │
                              ▼
                     ┌─────────────────┐
                     │    LLMClient    │
                     │      (ABC)      │
                     └────────┬────────┘
                              │
                ┌─────────────┴─────────────┐
                ▼                           ▼
         MockLLMProvider            RealLLMProvider
                │                           │
                └─────────────┬─────────────┘
                              │ Structured Decision
                              ▼
                     ┌─────────────────┐
                     │ Tool Dispatcher │
                     └───────┬─────────┘
                             │
          ┌──────────────────┼──────────────────┐
          ▼                  ▼                  ▼
      CalculatorTool       SearchTool       DatabaseTool
          │                  │                  │
          └──────────────────┼──────────────────┘
                             ▼
                        ToolResult
                             │
                ┌────────────┴────────────┐
                │                         │
                ▼                         ▼
              Tracer                 Observation
                │                         │
                ▼                         ▼
         TraceRepository             AgentLoop
                │                         │
                ▼                         │
              SQLite ◄────────────────────┘
                │
                ▼
      ┌──────────────────────┐
      │ ReliabilityAnalyzer  │
      │       Pandas         │
      └──────────┬───────────┘
                 │
      ┌──────────┴──────────┐
      ▼                     ▼
   Reliability Metrics    Failure Analysis
        │                     │
        └──────────┬──────────┘
                   ▼
          Streamlit Dashboard

### Execution Flow
1. **User Prompt Submission:** The user or benchmark runner submits a query to `AgentLoop`.
2. **Decision Cycle:** `AgentLoop` queries `LLMClient` (`MockLLMProvider` or `RealLLMProvider`), receiving a structured `LLMAction`.
3. **Instrumentation:** Every decision, action selection, and state transition emits a `TraceEvent` logged by `Tracer`.
4. **Tool Execution & Retries:** `Tool Dispatcher` routes arguments to `CalculatorTool`, `SearchTool`, or `DatabaseTool`. Transient errors (e.g., timeouts) trigger automatic retry cycles.
5. **Observation & Persistence:** Execution outcomes (`ToolResult`) format into observations fed back into the LLM context, while `TraceRepository` persists events to SQLite.
6. **Analysis & Dashboard:** `ReliabilityAnalyzer` computes Pandas-based aggregate metrics and failure taxonomies visualized in Streamlit.

---

## Experimental Results & Benchmark Evaluation

Using the automated benchmark suite (`scripts/run_experiment.py`), the system evaluated 17 multi-category test cases. Below are the key baseline metrics generated from the execution traces:

| Metric Category | Metric Name | Value | Description |
| :--- | :--- | :--- | :--- |
| **System Overview** | **Total Historical Runs** | `82` | Total agent trajectories recorded in storage |
| | **Task Success Rate** | `95.12%` | Percentage of agent runs reaching successful completion |
| | **Failure Rate** | `4.88%` | Percentage of unrecoverable or terminated runs |
| | **Average Latency** | `62.87 ms` | Mean end-to-end execution latency per trajectory |
| | **Average Trajectory Steps** | `1.51` | Mean step count per query trajectory |
| | **Retry Rate** | `7.32%` | Proportion of runs invoking transient recovery retries |
| **Tool Selection** | **Tool Selection Accuracy** | `54.92%` | Ground-truth expected tool vs. selected tool accuracy |
| **Tool Latency** | **Calculator Average Latency** | `0.15 ms` | Mean execution time for AST arithmetic operations |
| | **Database Average Latency** | `2.15 ms` | Mean execution time for parameterized SQLite lookups |
| | **Search Average Latency** | `0.06 ms` | Mean execution time for local knowledge search queries |
| **Failure Taxonomy** | **Primary Failure Cause** | `MAX_STEPS_EXCEEDED` | Trajectories terminated due to step-budget constraints (4 runs) |

---

## Technology Stack

- **Language:** Python 3.11+
- **Data Analysis & Processing:** Pandas, NumPy
- **Database & Storage:** SQLite3 (with timeout handling & context managers)
- **Dashboard & Visualization:** Streamlit, Plotly Express
- **Validation & Settings:** Pydantic V2, Pydantic-Settings
- **Testing Suite:** Pytest
- **Containerization:** Docker, Docker Compose

---

## Quickstart & Setup Guide

### Prerequisites
* Python 3.10 or higher installed, **OR**
* Docker Desktop running on Windows/Mac/Linux

---

### Option A: Local Python Environment Setup

1. **Clone Repository & Install Dependencies:**
   ```bash
   git clone [https://github.com/YOUR_USERNAME/llm-agent-reliability-analyzer.git](https://github.com/YOUR_USERNAME/llm-agent-reliability-analyzer.git)
   cd llm-agent-reliability-analyzer
   pip install -r requirements.txt

2. **Initialize SQLite Storage:**

   ```bash
   python -c "from storage.database import init_db; init_db()"

3. **Run Benchmark Experiments:**

   ```bash
   python scripts/run_experiment.py

4. **Launch Streamlit Observability Dashboard:**

   ```bash
   streamlit run dashboard/app.py

5. **Access Dashboard:**
  Open http://localhost:8501 in your web browser.

### Option B: Docker Container Setup

1. **Ensure Docker Desktop is running.**

2. **Build & Start Container:**

   ```bash
   docker compose up --build

3. **Populate Benchmark Traces inside Container:**
Open a secondary terminal window and execute:

   ```bash
   docker compose exec app python scripts/run_experiment.py

```

4. **Access Dashboard**
Navigate to http://localhost:8501 and refresh the page.

---

## Testing Suite

Execute the comprehensive unit and end-to-end integration test suite using Pytest:

   ```bash
   # Run all unit and integration tests
   python -m pytest

   # Run a specific module test
   python -m pytest tests/test_end_to_end.py

```

## Repository Structure

```text
llm-agent-reliability-analyzer/
│
├── agent/                  # Core Agent, LLM Abstraction & Factory
│   ├── __init__.py
│   ├── agent.py            # Main Agent Loop & Tool Dispatcher
│   ├── factory.py          # Provider Factory Loader
│   ├── llm_client.py       # Abstract Base Provider
│   ├── mock_llm.py         # Deterministic Offline Rule-Based LLM
│   └── real_llm.py         # OpenAI Structured API Provider
│
├── tools/                  # Executable Tools Layer
│   ├── __init__.py
│   ├── base.py             # BaseTool Class & ToolResult Schema
│   ├── calculator.py       # Safe AST Math Evaluator
│   ├── database.py         # SQLite Search Tool
│   └── search.py           # Mock Search Tool with Failure Injection
│
├── tracing/                # Instrumentation & Event Logging
│   ├── __init__.py
│   ├── events.py           # Enums (TraceEventType, ErrorType, RunStatus)
│   ├── models.py           # Pydantic Schemas (AgentRun, TraceEvent, LLMAction)
│   └── tracer.py           # Event Logger
│
├── storage/                # Persistence & Database Access
│   ├── __init__.py
│   ├── database.py         # SQLite Schema Initialization & Connection Pool
│   └── repositories.py     # TraceRepository Persistence Layer
│
├── analysis/               # Reliability Analysis Engine
│   ├── __init__.py
│   └── reliability.py      # Pandas Metrics Computation
│
├── evaluation/             # Benchmarks & Experimentation
│   ├── __init__.py
│   ├── dataset.json        # 50+ Ground-Truth Benchmark Queries
│   ├── evaluator.py        # Dataset Loader
│   └── experiment_runner.py# Batch Experiment Runner
│
├── dashboard/              # Streamlit Web Application
│   └── app.py              # Interactive Visual Dashboard & Trace Viewer
│
├── scripts/                # Utility & Execution Scripts
│   └── run_experiment.py   # CLI Experiment Suite Runner
│
├── tests/                  # Unit & End-to-End Integration Tests
│   ├── test_agent.py
│   ├── test_analysis.py
│   ├── test_end_to_end.py
│   ├── test_evaluation.py
│   ├── test_experiment_runner.py
│   ├── test_llm_provider.py
│   ├── test_retry.py
│   ├── test_storage.py
│   ├── test_tools.py
│   └── test_tracing.py
│
├── config.py               # Central Settings & Environment Variables
├── Dockerfile              # Docker Application Container Definition
├── docker-compose.yml      # Docker Multi-Container Configuration
├── requirements.txt        # Python Dependencies
├── .gitignore              # Git Exclusion Rules
└── README.md               # System Documentation
