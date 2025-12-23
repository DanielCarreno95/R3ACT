# R3ACT: Resilience, Reaction and Recovery Analysis of Critical Transitions

## SkillCorner X PySport Analytics Cup - Research Track

A comprehensive system for objectively measuring individual and collective response capabilities to critical errors in elite football using tracking data and enriched events.

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

### Running the Analysis

The system is executed through the `submission.ipynb` notebook:

```python
from src.r3act_system import R3ACTSystem

# Initialize system
r3act = R3ACTSystem(time_window='medium')  # 'short', 'medium', or 'long'

# Process all matches
results_df = r3act.process_all_matches(load_tracking=True)
```

### Running the Dashboard

To launch the interactive Streamlit dashboard:

```bash
streamlit run streamlit_app.py
```

The dashboard provides:
- Interactive visualizations of R3ACT metrics
- Configurable critical event weights
- Temporal window selection (2/5/10 minutes)
- Filtering by match, team, player, and period
- League average comparisons
- Export capabilities

## Project Structure

```
analytics_cup_research-main/
├── src/
│   ├── __init__.py
│   ├── data_loader.py          # Loads data from GitHub
│   ├── event_detector.py       # Detects critical events
│   ├── baseline_calculator.py  # Calculates baseline state
│   ├── metrics_calculator.py  # Calculates CRT, TSI, GIRI
│   └── r3act_system.py         # Main system
├── submission.ipynb            # Main notebook
├── streamlit_app.py            # Interactive dashboard
├── requirements.txt            # Dependencies
├── ABSTRACT.md                 # Research abstract
└── README.md                   # This file
```

## Features

- **Automatic critical event detection**: Possession losses, failed passes, goals, defensive errors, interceptions
- **Global baseline state**: Calculated across all matches (not per-match)
- **Configurable temporal windows**: 2, 5, or 10 minutes (symmetric pre/post)
- **Weighting system**: Configurable weights for critical events
- **Direct GitHub loading**: No local large data files required
- **Interactive dashboard**: Streamlit application for visualization and analysis

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

## Notes

- Complete calculation may take several minutes due to tracking data loading
- For quick testing, use `load_tracking=False` (will only detect events, without calculating metrics requiring tracking)
- The dashboard requires an initial data load which may take time on first run

## Methodology

### Critical Event Detection

The system automatically detects six types of critical events from `dynamic_events.csv`:
1. Possession losses (classified by field zone)
2. Failed passes (with danger context)
3. Goals (scored and conceded)
4. Defensive errors
5. Conceded interceptions

Each event type has configurable weights for tactical prioritization.

### Metrics Calculation

**CRT**: Uses Mahalanobis distance and EWMA to identify recovery. Compares post-error physical metrics (velocity, position, distance) with player baseline.

**TSI**: Combines three components:
- Physical proximity of team to error-committing player
- Change in possession frequency
- Defensive structure changes (compactness)

**GIRI**: Measures tactical changes post-goal (block height, velocity, compactness).

### Baseline Calculation

Baseline states are calculated as averages across **all matches** (10 matches), not per-match. This ensures consistent and scalable comparisons.

## License

MIT License

## Citation

If you use this work, please cite:

```
R3ACT: Resilience, Reaction and Recovery Analysis of Critical Transitions
SkillCorner X PySport Analytics Cup - Research Track
```

## Contact

For questions or feedback, please refer to the competition guidelines or open an issue in the repository.
