# Changelog

## [2.0.0] - 2025-01-31

### Breaking Changes

This is a complete reorganization of the package into a professional DSPy extension with a clean v2.0.0 release. No backward compatibility with v1.x.

### Added

- **Professional Package Structure**: Reorganized into `stcc_triage/` package
- **CLI Commands**: 
  - `stcc-ui` - Launch Streamlit UI
  - `stcc-optimize` - Optimize specialized nurses
  - `stcc-api` - Launch FastAPI server
  - `stcc-parse-protocols` - Parse STCC protocols
- **Installable Package**: Users can now install with `pip install -e .`
- **Bundled Protocols**: STCC-chinese protocols (~2MB, 225 files) included in package data
- **User Data Separation**: User-generated files (compiled agents, datasets) stored in `user_data/` (gitignored)
- **Path Management**: Centralized path handling in `stcc_triage/core/paths.py`
- **Public API**: Clean exports from `stcc_triage` package
- **Specialized Nurse Classes**: Convenience classes for each specialization

### Changed

- **Package Name**: Renamed from `stcc-triage-agent` to `dspy-stcc-homecare`
- **Module Paths**: All modules moved to `stcc_triage/` package
  - `agent/*` → `stcc_triage/core/`
  - `dataset/*` → `stcc_triage/datasets/` and `stcc_triage/nurses/`
  - `optimization/*` → `stcc_triage/optimizers/`
  - `protocols/*` → `stcc_triage/protocols/`
  - `ui/*` → `stcc_triage/ui/`
  - `deployment/*` → `stcc_triage/api/`
- **Import Paths**: Updated all imports to use `stcc_triage.*`
- **Data Locations**: 
  - Protocols: `stcc_triage/data/protocols/STCC-chinese/` (bundled)
  - Compiled agents: `user_data/compiled/` (user-generated)
  - Generated datasets: `user_data/datasets/` (user-generated)
- **Installation**: Now requires `pip install -e .` instead of direct script execution

### Removed

- Old directory structure: `agent/`, `dataset/`, `optimization/`, `ui/`, `deployment/`, `scripts/`
- Direct script execution (replaced with CLI commands)

### Migration Guide (v1.x to v2.0.0)

**Old (v1.x):**
```bash
uv run python ui/streamlit_app.py
uv run python optimization/compile_specialized.py
```

**New (v2.0.0):**
```bash
pip install -e .
stcc-ui
stcc-optimize
```

**Old (v1.x) imports:**
```python
from agent.triage_agent import STCCTriageAgent
from dataset.nurse_roles import NurseRole
```

**New (v2.0.0) imports:**
```python
from stcc_triage import STCCTriageAgent
from stcc_triage.nurses import NurseRole, WoundCareNurse
```

## [1.0.0] - 2025-01-30

Initial release with specialized nurse agents and DSPy optimization.
