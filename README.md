# R3ACT: Resilience, Reaction and Recovery Analysis of Critical Transitions

## SkillCorner X PySport Analytics Cup - Research Track

A system for objectively measuring individual and collective response capabilities to critical errors in elite football using tracking data and enriched events.

**Abstract**: See `ABSTRACT.md` for the complete abstract (maximum 500 words).

## Description

R3ACT analyzes the resilience, reaction, and recovery of players and teams following critical events through three main metrics:

- **CRT (Cognitive Reset Time)**: Individual physical/cognitive recovery time post-error
- **TSI (Team Support Index)**: Collective team response (proximity, possession, defensive structure)
- **GIRI (Goal Impact Response Index)**: Tactical change post-goal

## Installation

```bash
pip install -r requirements.txt
```

## Usage

The system is executed through the `submission.ipynb` notebook:

```python
from src.r3act_system import R3ACTSystem

# Initialize system
r3act = R3ACTSystem(time_window='medium')  # 'short', 'medium', or 'long'

# Process all matches
results_df = r3act.process_all_matches(load_tracking=True)
```

## Project Structure

```
├── src/
│   ├── __init__.py
│   ├── data_loader.py          # Loads data from GitHub
│   ├── event_detector.py       # Detects critical events
│   ├── baseline_calculator.py  # Calculates baseline state
│   ├── metrics_calculator.py  # Calculates CRT, TSI, GIRI
│   └── r3act_system.py         # Main system
├── submission.ipynb            # Main notebook
├── streamlit_app.py            # Interactive dashboard (optional)
├── requirements.txt            # Dependencies
├── ABSTRACT.md                 # Research abstract
└── README.md                   # This file
```

## Features

- Automatic critical event detection from `dynamic_events.csv`
- Global baseline calculation across all matches
- Configurable temporal windows (2, 5, 10 minutes)
- Parametrizable event weighting system
- Data loads directly from SkillCorner GitHub repository

## Requirements

- Python 3.8+
- pandas >= 2.0.0
- numpy >= 1.24.0
- scipy >= 1.10.0
- requests >= 2.31.0
- streamlit >= 1.28.0 (for dashboard)
- plotly >= 5.17.0 (for dashboard)

## Data Source

All data is loaded directly from the [SkillCorner Open Data Repository](https://github.com/SkillCorner/opendata). No local data files are required.

## License

MIT License
