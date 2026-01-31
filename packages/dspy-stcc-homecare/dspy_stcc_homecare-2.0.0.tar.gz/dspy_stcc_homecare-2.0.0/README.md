# STCC Triage Agent - DSPy Extension (v2.0.0)

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![DSPy](https://img.shields.io/badge/DSPy-Optimized-green.svg)](https://github.com/stanfordnlp/dspy)

**Professional medical triage system powered by DSPy and DeepSeek, with 10 specialized nurse agents.**

> **⚠️ IMPORTANT**: Educational and research use only. NOT approved for clinical use.

---

## Demo

![Demo](docs/demo.gif)

> Interactive triage system with 10 specialized nurse agents. [Watch full video](docs/demo.mp4)

---

## What's New in v2.0.0

This is now a **professional DSPy extension** that users can install locally:

- 📦 **Installable package**: `pip install -e .`
- 🚀 **CLI commands**: `stcc-ui`, `stcc-optimize`, `stcc-api`
- 🏗️ **Clean structure**: All code in `stcc_triage/` package
- 📚 **Bundled protocols**: STCC-chinese protocols (~2MB) included
- 💾 **User data separation**: Compiled agents in `user_data/` (gitignored)
- 🔄 **Breaking changes**: Clean v2.0.0 release (no backward compatibility)

---

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/chenhaodev/dspy-stcc-homecare.git
cd dspy-stcc-homecare
```

### 2. Install Dependencies

```bash
# Install with pip (editable mode)
pip install -e .

# Or install with uv (recommended - faster)
uv pip install -e .

# Install with API support
pip install -e ".[api]"
```

### 3. Configure API Key

```bash
cp .env.example .env
# Edit .env and add: DEEPSEEK_API_KEY=your_key_here
```

### 4. Parse Protocols (First Time Only)

```bash
stcc-parse-protocols
```

This parses 225 STCC protocols from `stcc_triage/data/protocols/STCC-chinese/` and generates `protocols/protocols.json`.

---

## Quick Start

### Launch Web UI

```bash
stcc-ui
# Opens at http://localhost:8501
```

**Features:**
- 🏥 Select from 10 specialized nurses
- 💬 Interactive chat interface
- 🎨 Color-coded triage levels
- 🔍 View reasoning steps
- 🔧 Check optimization status

### Python API

```python
from stcc_triage import STCCTriageAgent
from stcc_triage.nurses import WoundCareNurse

# Use baseline agent
agent = STCCTriageAgent()
result = agent.triage("55-year-old with severe chest pain and shortness of breath")

print(f"Triage Level: {result.triage_level}")
print(f"Justification: {result.clinical_justification}")

# Use specialized nurse (requires compilation first)
nurse = WoundCareNurse()
result = nurse.triage("deep laceration with bleeding")
```

---

## Specialized Nurses

Instead of one generic agent, this system provides **10 specialized nurses**, each optimized for their domain:

| Nurse | Specialization | Protocol Count | Example Cases |
|-------|---------------|----------------|---------------|
| **Wound Care** | Trauma, burns, bleeding | 24 | Deep laceration, severe burn |
| **OB/Maternal** | Pregnancy, labor | 13 | Contractions at 32 weeks, bleeding |
| **Pediatric** | Children/infants | 12 | Infant fever, child vomiting |
| **Neuro** | Stroke, seizure | 7 | Sudden weakness, worst headache |
| **GI** | Abdominal, digestive | 6 | Severe abdominal pain, GI bleeding |
| **Respiratory** | Breathing, asthma | 6 | COPD exacerbation, wheezing |
| **Mental Health** | Behavioral crises | 5 | Suicide risk, panic attack |
| **CHF** | Heart failure | 4 | Dyspnea, edema, chest pain |
| **ED** | Emergency/acute | All | Multi-trauma, critical |
| **PreOp** | Pre-surgical | 2 | Surgical clearance |

**Each nurse is optimized with domain-specific training data using DSPy's BootstrapFewShot.**

---

## Optimize Nurses

### Optimize a Specific Nurse

```bash
stcc-optimize --role wound_care_nurse

# Other roles: ob_nurse, pediatric_nurse, neuro_nurse, gi_nurse,
# respiratory_nurse, mental_health_nurse, chf_nurse, ed_nurse, preop_nurse
```

**Output:**
```
Compiling Specialized Agent: Wound Care Nurse
Training set: 16 specialized cases
Distribution:
  emergency: 4 cases
  home_care: 4 cases
  moderate: 4 cases
  urgent: 4 cases

Optimizing for Wound Care Nurse...
This may take 5-10 minutes...

✓ Compiled Wound Care Nurse agent saved to:
  user_data/compiled/compiled_wound_care_nurse_agent.json
```

### Optimize All Nurses

```bash
stcc-optimize
```

This compiles all 10 specialized nurses (takes ~1 hour).

---

## Launch API Server

```bash
# Launch FastAPI server
stcc-api

# With auto-reload for development
stcc-api --reload

# Custom host/port
stcc-api --host 127.0.0.1 --port 8080
```

Visit `http://localhost:8000/docs` for interactive API documentation.

**Example API Usage:**

```bash
# Basic triage
curl -X POST "http://localhost:8000/triage" \
  -H "Content-Type: application/json" \
  -d '{"symptoms": "severe chest pain for 30 minutes"}'

# Specialized nurse triage
curl -X POST "http://localhost:8000/triage/specialized" \
  -H "Content-Type: application/json" \
  -d '{"symptoms": "deep laceration with active bleeding", "nurse_role": "wound_care_nurse"}'
```

---

## Architecture

### Package Structure

```
dspy-stcc-homecare/
├── stcc_triage/              # Main package
│   ├── core/                 # Core triage logic
│   │   ├── agent.py          # STCCTriageAgent
│   │   ├── signatures.py     # DSPy signatures
│   │   ├── settings.py       # DeepSeek config
│   │   └── paths.py          # Path management
│   │
│   ├── nurses/               # Specialized nurses
│   │   ├── roles.py          # NurseRole enum
│   │   └── specialized.py    # WoundCareNurse, OBNurse, etc.
│   │
│   ├── datasets/             # Dataset generation
│   │   ├── schema.py         # PatientCase schema
│   │   ├── generator.py      # Dataset generator
│   │   └── cases/            # Case definitions
│   │
│   ├── optimizers/           # Optimization logic
│   │   ├── metric.py         # Safety metrics
│   │   ├── optimizer.py      # BootstrapFewShot config
│   │   └── compiler.py       # Compilation logic
│   │
│   ├── protocols/            # Protocol handling
│   │   ├── parser.py         # Protocol parser
│   │   └── context.py        # Context enrichment
│   │
│   ├── ui/                   # Streamlit UI
│   │   ├── app.py            # Main app
│   │   └── components/       # UI components
│   │
│   ├── api/                  # FastAPI deployment
│   │   ├── app.py            # FastAPI app
│   │   └── models.py         # API models
│   │
│   ├── cli/                  # CLI commands
│   │   ├── ui.py             # stcc-ui
│   │   ├── optimize.py       # stcc-optimize
│   │   ├── api.py            # stcc-api
│   │   └── parse.py          # stcc-parse-protocols
│   │
│   └── data/                 # Bundled data
│       └── protocols/        # STCC protocols (~2MB)
│
├── user_data/                # User-generated (gitignored)
│   ├── compiled/             # Compiled nurses
│   └── datasets/             # Generated datasets
│
└── protocols/                # Generated protocols.json
```

### How It Works

1. **Protocol Context**: Enriches patient symptoms with relevant STCC protocol guidelines
2. **DSPy ChainOfThought**: Structured reasoning with transparent decision-making
3. **DeepSeek R1**: Advanced reasoning engine with medical knowledge
4. **BootstrapFewShot**: Automatic optimization with domain-specific examples
5. **Safety Metrics**: Prevents under-triage (missing emergencies = score 0.0)

---

## CLI Reference

```bash
# Launch Web UI
stcc-ui

# Optimize nurses
stcc-optimize                           # All nurses
stcc-optimize --role wound_care_nurse   # Specific nurse
stcc-optimize --regenerate-data         # Force regenerate training data

# Launch API server
stcc-api                                # Default: 0.0.0.0:8000
stcc-api --host 127.0.0.1 --port 8080   # Custom host/port
stcc-api --reload                       # Auto-reload for dev

# Parse protocols
stcc-parse-protocols                    # Parse STCC markdown to JSON
```

---

## Python API Reference

```python
# Core imports
from stcc_triage import STCCTriageAgent, TriageSignature, FollowUpSignature

# Specialized nurses
from stcc_triage.nurses import (
    WoundCareNurse,
    OBNurse,
    PediatricNurse,
    NeuroNurse,
    GINurse,
    RespiratoryNurse,
    MentalHealthNurse,
    CHFNurse,
    EDNurse,
    PreOpNurse,
    GeneralNurse,
    NurseRole,
)

# Optimization
from stcc_triage.optimizers import optimize_nurse, load_compiled_nurse

# Dataset generation
from stcc_triage.datasets import generate_all_specialized_datasets

# Protocol parsing
from stcc_triage.protocols import parse_all_protocols
```

---

## Development

### Run Tests

```bash
pytest tests/
```

### Code Quality

```bash
# Format code
ruff format .

# Lint code
ruff check .

# Type checking
mypy stcc_triage/
```

---

## Troubleshooting

### "protocols.json not found"

```bash
stcc-parse-protocols
```

### "Compiled agent not found"

```bash
stcc-optimize --role wound_care_nurse
```

### Import errors after installation

```bash
pip install -e .  # Reinstall in editable mode
```

---

## License

MIT License - See [LICENSE](LICENSE)

---

## Contributing

Contributions welcome! This is an educational project demonstrating DSPy optimization for domain-specific agents.

---

## Citation

If you use this project in research:

```bibtex
@software{stcc_triage_agent,
  title = {STCC Triage Agent: DSPy Extension for Medical Triage},
  author = {STCC Triage Agent Contributors},
  year = {2025},
  url = {https://github.com/chenhaodev/dspy-stcc-homecare}
}
```

---

## Acknowledgments

- **STCC Protocols**: Schmitt-Thompson Clinical Content (225 protocols)
- **DSPy**: Stanford NLP's programming framework for LMs
- **DeepSeek**: Advanced reasoning engine with medical knowledge

---

**Built with DSPy • Optimized for Safety • Educational Use Only**
