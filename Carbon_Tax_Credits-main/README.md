# Industrial Decarbonization & Carbon Credit Intelligence Platform ("EcoPulse AI")

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![OpenRouter API](https://img.shields.io/badge/OpenRouter%20API-Gemini%20%2F%20GPT-purple.svg)](https://openrouter.ai/)
[![Framework](https://img.shields.io/badge/Architecture-5--Stage%20Multi--Agent-green.svg)](#architecture--5-agent-pipeline)
[![Frontend](https://img.shields.io/badge/Frontend-React%2019%20%2B%20Tailwind-blueviolet.svg)](./frontend)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

**EcoPulse AI** is an autonomous, deterministic industrial AI framework designed to evaluate carbon reduction potentials, audit regulatory policy compliance via Retrieval-Augmented Generation (RAG), screen green tax incentive eligibility, and quantify monetizable carbon credit units from raw factory telemetry logs. It integrates OpenRouter API for flexible LLM inference and Jinja2 prompt rendering.

---

## Architecture & 5-Agent Pipeline

The system strictly executes a sequential **5-Stage Industrial Agent Pipeline**, chaining data seamlessly from raw machine telemetry through compliance auditing down to audit-ready executive reports and interactive dashboard payloads.

```
┌──────────────────────────────────────────────────────────────────────────┐
│                         Industrial Data Sources                          │
│   Energy Data  │  Fuel Data  │  Production Data  │  Machine Data         │
└────────────────────────────────────┬─────────────────────────────────────┘
                                     │
                                     ▼
                          ┌─────────────────────┐
                          │ Data Preprocessing  │
                          └──────────┬──────────┘
                                     │
┌────────────────────────────────────┼─────────────────────────────────────┐
│                        AGENTIC AI FRAMEWORK                              │
│                                    ▼                                     │
│                     ┌───────────────────────────┐                        │
│                     │ Emission Assessment Agent │ (Agent 1)              │
│                     └──────────────┬────────────┘                        │
│                                    ▼                                     │
│                     ┌───────────────────────────┐                        │
│                     │ Carbon Credit Agent       │ (Agent 2)              │
│                     └──────────────┬────────────┘                        │
│                                    ▼                                     │
│ ┌───────────────────────┐   ┌───────────────────┐                        │
│ │ Carbon Policies KB    ├──►│ Policy RAG Agent  │ (Agent 3)              │
│ └───────────────────────┘   └──────────┬────────┘                        │
│                                        ▼                                 │
│                     ┌───────────────────────────┐                        │
│                     │ Tax Incentive Agent       │ (Agent 4)              │
│                     └──────────────┬────────────┘                        │
│                                    ▼                                     │
│                     ┌───────────────────────────┐                        │
│                     │ Report Generation Agent   │ (Agent 5)              │
│                     └──────────────┬────────────┘                        │
└────────────────────────────────────┼─────────────────────────────────────┘
                                     │
                                     ▼
                         Decision Support Dashboard
             (executive_report_output.json & executive_summary.md)
```

### Agent Pipeline Details

#### 1. Agent 1: Emission Assessment Agent (`agents/emission_assessment_agent.py`)
- **Responsibility**: Ingests raw telemetry and computes weighted energy allocation shares $W_{i,t}$, daily line carbon emissions $C_{i,t}$, and carbon intensity per product $CI_{i,t}$.
- **Key Formulation**:
  $$W_{i,t} = 0.40 \cdot \left(\frac{h_{i,t}}{H_{\text{total},t}}\right) + 0.35 \cdot \left(\frac{Q_{i,t}}{\sum Q_{i,t}}\right) + 0.25 \cdot \left(\frac{\text{OEE}_{i,t}}{\sum \text{OEE}_{i,t}}\right)$$
  $$C_{i,t} = E_{i,t} \cdot \text{EF}_{\text{grid}}$$
- **Guardrail**: Caps confidence score strictly at $\le 0.45$ and flags status as `ESTIMATED_PROXY` for unmetered data.

#### 2. Agent 2: Carbon Credit Assessment Agent (`agents/carbon_credit_assessment_agent.py`)
- **Responsibility**: Evaluates 7-day initial operating baselines ($\bar{C}_{i,\text{base}}$), active period net reductions ($\Delta C_i$), and potential credit quantities ($PC_i$) in $\text{tCO}_2\text{e}$.
- **Key Formulation**:
  $$\bar{C}_{i,\text{base}} = \frac{1}{7} \sum_{\tau=1}^{7} C_{i,\tau}$$
  $$PC_i = \frac{\max(0, \bar{C}_{i,\text{base}} - C_{\text{current}}) \cdot D_{\text{observed}}}{1000}$$
- **Guardrail**: Negative reductions default strictly to $0.0$. Missing methodology flags set status to `REQUIRES_METHODOLOGY`.

#### 3. Agent 3: Policy & Compliance Agent RAG (`agents/policy_compliance_agent.py`)
- **Responsibility**: Vectorizes operational contexts, queries the local `Carbon Policies Knowledge Base` via cosine similarity search, and enforces legal compliance gates.
- **Key Formulation**:
  $$\text{Score}(q, p) = \frac{\mathbf{v}_q \cdot \mathbf{v}_p}{\|\mathbf{v}_q\| \cdot \|\mathbf{v}_p\|}$$
- **Guardrail**: Cosine similarity $< 0.70$ flags `OUT_OF_DOMAIN_POLICY`. Proxy data sets compliance posture to `PENDING_PLANT_SUBMETER_AUDIT`.

#### 4. Agent 4: Tax Incentive Optimization Agent (`agents/tax_incentive_agent.py`)
- **Responsibility**: Maximizes green tax rebate objective functions based on OEE efficiency and carbon intensity benchmarks.
- **Key Formulation**:
  $$\max F = \sum_{i} \left( Q_i \cdot \text{Rebate\_Rate} \cdot \mathbb{I}(\text{OEE}_i \ge 85\%) \cdot \mathbb{I}(CI_i < \mu_{\text{plant}}) \right)$$
- **Guardrail**: Missing plant location (`UNKNOWN`) sets jurisdiction status to `REQUIRES_LOCATION_CONFIRMATION` and blocks automated rebate payouts.

#### 5. Agent 5: Report Generation Agent (`agents/report_generation_agent.py`)
- **Responsibility**: Synthesizes findings from Agents 1–4, computes composite confidence scores $CS_{\text{composite}}$, verifies data lineage, and outputs audit-ready JSON and Markdown reports.
- **Key Formulation**:
  $$CS_{\text{composite}} = 0.4 \cdot C_{\text{Energy}} + 0.4 \cdot C_{\text{Production}} + 0.2 \cdot C_{\text{Policy}}$$
  $$\text{Capped } CS_{\text{composite}} = \min(CS_{\text{composite}}, 0.45) \quad \text{for unmetered proxy telemetry}$$

---

## Project Directory Structure

```
carbon_credits/
├── main.py                              # Primary top-level framework orchestrator & sync engine
├── run_agent.py                         # CLI wrapper entry point
├── llm_service.py                       # OpenRouter LLM & .env key management service
├── download_knowledge_base.py           # Document downloader & PDF/text parser script
├── .env                                 # Environment configuration & OpenRouter API key
├── .env.example                         # Safe environment template
├── requirements.txt                     # Python dependencies list
├── agents/                              # 5-Stage Multi-Agent Industrial AI Package
│   ├── __init__.py                      # Package initializer exporting all 5 agents
│   ├── emission_assessment_agent.py     # Agent 1 (Emission Assessment)
│   ├── carbon_credit_assessment_agent.py# Agent 2 (Carbon Credit Assessment)
│   ├── policy_compliance_agent.py       # Agent 3 (Policy RAG Compliance)
│   ├── tax_incentive_agent.py           # Agent 4 (Tax Incentive Optimization)
│   ├── report_generation_agent.py      # Agent 5 (Report Generation)
│   └── pipeline.py                      # 5-stage sequential pipeline orchestrator
├── prompts/                             # Jinja2 prompt templates
│   ├── emission_agent.j2                # Agent 1 prompt template
│   ├── credit_agent.j2                  # Agent 2 prompt template
│   ├── policy_agent.j2                  # Agent 3 prompt template
│   ├── tax_agent.j2                     # Agent 4 prompt template
│   └── report_agent.j2                  # Agent 5 prompt template
├── knowledge_base/                      # Carbon Policies RAG document store
│   ├── cea_grid_baseline_2026.txt       # CEA All-India Grid Emission Factor 2026
│   ├── green_tax_incentives_act.txt    # National Green Manufacturing Act 2025
│   ├── carbon_credit_registry_rules.txt# Verra / CDM Registration Rules v4.4
│   └── pdfs/                            # Directory for PDF policy documents
├── input_data/                          # Raw manufacturing telemetry datasets
│   ├── Production.csv                   # Daily line production quantities & runtime hours
│   ├── Energy_Estimated_Proxy.csv       # Unmetered plant machine power logs
│   ├── Dashboard_KPI.csv                # Aggregated line OEE & downtime KPIs
│   └── Validation_Report.csv            # Automated validation report checks
├── test_agent.py                        # 18-test automated unit & integration test suite
└── frontend/                            # React.js Executive Dashboard Frontend
    ├── public/data/                     # Auto-synced agent output JSONs & executive_summary.md
    └── src/
        ├── lib/ecopulse-data.ts         # Data model & loader for agent output payloads
        └── components/ecopulse/
            ├── KpiCards.tsx             # Plant total KPI metrics & confidence badges
            ├── TelemetrySection.tsx     # 26 production lines telemetry & search filters
            ├── RagInspector.tsx         # Vector similarity search & document citations
            ├── IncentivePanel.tsx       # Financial rebate optimization math & disclaimers
            └── ReportSection.tsx        # Executive markdown summary & JSON audit payload tabs
```

---

## Tech Stack

| Domain | Technology / Library | Purpose |
| :--- | :--- | :--- |
| **Language & Core** | `Python 3.11+` | Core agent business logic & mathematical formulations |
| **LLM Inference** | `OpenRouter API` (`google/gemini-flash-1.5`) | AI completions & structured reasoning via OpenRouter |
| **Prompt Engineering** | `Jinja2` | Deterministic prompt templates (`prompts/*.j2`) |
| **RAG & Vector Search** | `Cosine Similarity Math` & `pypdf` | Vector similarity ranking & PDF document parsing |
| **Data Processing** | `pandas`, `numpy`, `requests` | Telemetry processing & API HTTP client |
| **Frontend Framework**| `React 19`, `Vite` | Fast executive dashboard interface |
| **Styling & Icons** | `Tailwind CSS v4`, `Lucide React` | Modern dark-mode UI aesthetics |
| **Visualization** | `Recharts` | Bar charts, composed charts & pie charts for telemetry |

---

## Getting Started & Installation

### Prerequisites
- **Python**: Version 3.11 or higher
- **Node.js**: Version 18.0 or higher (`npm` / `bun`)

### Step 1: Clone the Repository
```bash
git clone https://github.com/your-org/carbon_credits.git
cd carbon_credits
```

### Step 2: Set Up Python Virtual Environment
```bash
# Create virtual environment
python -m venv venv

# Activate on Windows (PowerShell)
.\venv\Scripts\Activate.ps1

# Activate on Windows (Command Prompt)
.\venv\Scripts\activate.bat

# Activate on Linux / macOS
source venv/bin/activate
```

### Step 3: Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### Step 4: Configure OpenRouter API Key
Copy `.env.example` to `.env` and set your OpenRouter API key:
```bash
cp .env.example .env
```
Edit `.env`:
```env
OPENROUTER_API_KEY=sk-or-v1-your_openrouter_api_key_here
OPENROUTER_MODEL=google/gemini-flash-1.5
GRID_EMISSION_FACTOR=0.716
LOG_LEVEL=INFO
```

### Step 5: Initialize Knowledge Base & Policy Documents
Run the document downloader and PDF parser:
```bash
python download_knowledge_base.py
```

### Step 6: Execute the Multi-Agent Pipeline
Run the primary orchestrator to execute all 5 agents and sync output files to `frontend/public/data/`:
```bash
python main.py
```
*Alternatively, run via the CLI wrapper:*
```bash
python run_agent.py --grid-ef 0.716
```

### Step 7: Run Automated Test Suite
Verify that all 18 unit, integration, RAG vector retrieval, and Jinja rendering tests pass:
```bash
python test_agent.py
```

### Step 8: Launch the React Dashboard Frontend
Navigate to the `frontend/` directory and start the Vite dev server:
```bash
cd frontend
npm run dev
```
Open your browser at `http://localhost:3000` to view the **EcoPulse AI Executive Dashboard**.

---

## Output Payloads & Audit Reports

When `main.py` is executed, the following audit-ready files are generated and auto-synced:
- `emission_assessment_output.json`: Agent 1 daily telemetry emission records.
- `carbon_credit_assessment_output.json`: Agent 2 baseline reductions & credit quantification.
- `policy_compliance_output.json`: Agent 3 RAG policy compliance & document citations.
- `tax_incentive_output.json`: Agent 4 tax incentive objective optimization screening.
- `executive_report_output.json`: Agent 5 composite confidence score & executive JSON payload.
- `executive_summary.md`: Agent 5 executive Markdown audit report.

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
