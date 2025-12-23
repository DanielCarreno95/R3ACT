# R3ACT: Resilience, Reaction and Recovery Analysis of Critical Transitions

## Abstract

### Introduction

Football matches are characterized by critical transitions—moments where errors or disruptive events can significantly impact match outcomes. Understanding how players and teams respond to these critical moments is essential for performance analysis and tactical decision-making. However, existing metrics focus primarily on successful actions, leaving a gap in quantifying resilience and recovery capabilities.

This research introduces R3ACT (Resilience, Reaction and Recovery Analysis of Critical Transitions), a novel framework that objectively measures individual and collective response capabilities following critical errors using broadcast tracking data and enriched event data from SkillCorner. The system addresses three fundamental questions: (1) How quickly do players recover physically and cognitively after committing errors? (2) How do teams collectively respond to support players who err? (3) How do teams tactically adapt following goals?

### Methods

R3ACT processes tracking and event data from 10 A-League matches (2024/2025 season). The system automatically detects six types of critical events: possession losses (classified by field zone), failed passes (with danger context), goals (scored and conceded), defensive errors, and interceptions conceded. Each event type has configurable weights, allowing tactical prioritization.

The framework calculates three core metrics:

**CRT (Cognitive Reset Time)**: Measures individual recovery time using Mahalanobis distance and Exponentially Weighted Moving Average (EWMA). Player physical metrics (velocity, position, distance traveled) post-error are compared against a global baseline calculated across all matches, identifying when players return to baseline performance.

**TSI (Team Support Index)**: Evaluates collective response through three components: (1) physical proximity of teammates to the error-committing player, (2) change in team possession frequency, and (3) defensive structure changes (compactness). Components are weighted (40%, 30%, 30%) and combined into a single index.

**GIRI (Goal Impact Response Index)**: Quantifies tactical changes post-goal by measuring shifts in block height, team velocity, and compactness. Pre- and post-goal windows are symmetric (2, 5, or 10 minutes) for fair comparison.

Baseline states are calculated as averages across all matches (not per-match), ensuring consistent and scalable comparisons. The system supports configurable temporal windows and event weighting, making it adaptable to different tactical philosophies.

### Results

The system successfully processed all 10 matches, detecting and analyzing critical events across multiple categories. Preliminary analysis reveals significant variation in recovery times (CRT) and team support patterns (TSI) depending on event type and field location. Events in defensive zones show higher TSI values, suggesting stronger collective response in critical areas. GIRI analysis demonstrates measurable tactical adaptations following goals, with teams showing distinct response patterns.

The framework's parametrizable design allows staff to customize event weights and temporal windows according to team-specific needs, enhancing practical applicability.

### Conclusion

R3ACT provides an objective, scalable framework for analyzing resilience in football. By quantifying recovery and response capabilities, the system offers actionable insights for performance analysis, player development, and tactical planning. The parametrizable architecture ensures adaptability across different contexts and datasets, making it a valuable tool for football analytics.

Future work will expand event detection capabilities, incorporate additional pressure metrics, and develop more sophisticated temporal pattern analysis to further enhance the system's analytical depth.

---

**Word count: 498 words**

