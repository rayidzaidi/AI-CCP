# PowerPlan Scheduler: Outage-Aware Household Power Dispatch & Tariffs Optimization

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![Tests Passing](https://img.shields.io/badge/tests-11%2F11%20passing-brightgreen.svg)]()
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

**Course:** CSC-471-L Artificial Intelligence — Lab Session 6 (Open-Ended Lab)  
**Institution:** Iqra University, Department of Computer Science  
**Candidate:** Dua Rehan (Roll No. 67238)  
**Instructor:** Engr. Aimen Zafar  
**Evaluation:** Bloom's Taxonomy: `C3 (Applying), P2 (Mechanism)` | Graduate Attributes: `GA-2 (Problem Analysis), GA-5 (Modern Tool Usage)`

---

## 1. Executive Summary & Problem Formulation

In modern power grids with rolling blackouts (load shedding) and Time-of-Use (ToU) dynamic pricing tariffs, households face a combinatorial optimization challenge: **dispatching an inflexible set of appliances across discrete temporal slots to minimize cost while strictly adhering to feeder capacity bounds and grid outage windows.**

PowerPlan models this challenge as a **deterministic state-space graph search problem**, comparatively evaluating:
1. **Breadth-First Search (BFS):** FIFO queue exploration minimizing completion slot depth (greedy earliest finish).
2. **Depth-First Search (DFS):** LIFO stack exploration offering minimal memory footprint ($O(b \cdot m)$).
3. **A\* Search:** Priority Queue heuristic exploration with $f(n) = g(n) + h(n)$ using an **admissible and consistent heuristic**:
   $$h(n) = E_{\text{rem}} \cdot \min_{s \in \text{future active slots}} (\text{price}_s)$$
   guaranteeing mathematical cost-optimality without overestimating the remaining expenditure.

---

## 2. Experimental Benchmark Results

Evaluated on the standard 6-slot benchmark (6 kW feeder capacity limit, Slot 2 Outage, peak tariff up to $20/u):

| Search Algorithm | Objective Function | Total Cost ($) | Completion Slot | Nodes Expanded | Peak Memory (Queue) | Optimality Guarantee |
| :--- | :--- | :---: | :---: | :---: | :---: | :---: |
| **A\* Search** | $\min \sum \text{Cost}(s)$ | **$64.00** | Slot 6 | 22 | 56 | **Globally Cost-Optimal** |
| **BFS** | $\min \text{Depth}$ | **$135.00** | Slot 3 | 14 | 14 | Earliest Completion |
| **DFS** | First Feasible | **$154.00** | Slot 5 | 5 | 5 | Memory Efficient |

> **Key Finding:** A\* achieves a **52.6% net cost reduction** (\$71.00 saved vs. BFS) by strategically bypassing high-tariff peak slots (Slot 3 @ \$15/u and Slot 5 @ \$20/u) and shifting flexible demand into shoulder (\$8/u) and off-peak (\$4/u) periods.

---

## 3. Project Structure

```
├── app.py                             # Interactive Streamlit dashboard (Light Glassmorphic UI)
├── main.py                            # CLI benchmark driver & report generator
├── requirements.txt                   # Dependency specifications
├── pytest.ini                         # Test runner configuration
├── PowerPlan_Lab6_Complete.ipynb      # Academic Jupyter Notebook (19 cells)
├── powerplan/                         # Core Python package
│   ├── __init__.py                    # Public API exports
│   ├── models.py                      # Immutable data structures (ApplianceJob, PowerSlot, etc.)
│   ├── environment.py                 # SchedulingEnvironment & state transition models
│   ├── agent.py                       # SchedulingAgent (BFS, DFS, A* implementations)
│   ├── scenarios.py                   # Standard 6-Slot & Karachi 8-Slot scenario generators
│   ├── visualizer.py                  # Publication-ready Matplotlib heatmap & chart renderers
│   └── reporter.py                    # Markdown & CSV experimental report generator
├── tests/
│   └── test_powerplan.py              # Pytest verification suite (11 unit tests)
└── outputs/                           # Pre-rendered evaluation artifacts
    ├── schedule_heatmap.png           # Visual dispatch heatmap
    ├── algorithm_metrics_comparison.png # Side-by-side performance bar charts
    ├── combinatorial_scaling_analysis.png # State-space growth curves (3 to 7 jobs)
    ├── benchmark_results.csv          # Machine-readable metric exports
    └── Lab6_Experimental_Report.md    # Full laboratory report document
```

---

## 4. Installation & Quick Start

### Prerequisites
- Python 3.10 or higher
- Git

### Setup
```bash
# Clone the repository
git clone https://github.com/rayidzaidi/AI-CCP.git
cd AI-CCP

# Install dependencies
pip install -r requirements.txt
```

### Running the CLI Benchmark
```bash
python main.py
```
Executes all three algorithms across scenarios and regenerates all figures in `outputs/`.

### Running Unit Tests
```bash
pytest -v
```
Runs 11 test cases covering heuristic admissibility, outage enforcement, capacity pruning, and search optimality.

### Launching the Interactive Dashboard
```bash
streamlit run app.py
```
Opens the web dashboard at `http://localhost:8501` featuring:
- **Visual Schedule Heatmap:** Side-by-side color-coded appliance matrices.
- **Chronological Dispatch Timeline:** Interactive slot cards with live load meters.
- **State-Space Telemetry:** Full step-by-step search frontier transition inspector.
- **Combinatorial Scaling Benchmark:** State-space explosion analysis from 3 to 7 appliances.

---

## 5. Algorithmic Formulation

### Admissible Heuristic Proof
For any search state $n = (\text{slot}, \text{completed\_jobs})$:
1. $E_{\text{rem}} = \sum_{j \notin \text{completed\_jobs}} \text{energy}(j)$ is the exact inflexible remaining energy demand.
2. Let $p_{\min}^* = \min \{ \text{price}_s \mid s \in \text{future slots}, \text{capacity}_s > 0 \}$.
3. For any valid completion path from $n$, the actual future cost $h^*(n)$ must satisfy:
   $$h^*(n) = \sum_{j} \text{energy}(j) \cdot \text{price}_{\text{dispatched\_slot}} \ge \sum_{j} \text{energy}(j) \cdot p_{\min}^* = h(n)$$
4. Hence, $h(n) \le h^*(n)$ for all states $n$, proving **strict admissibility**. By the admissibility theorem of A\*, the returned schedule is guaranteed to have the minimum possible total electricity expenditure.

---

## 6. Author Information
- **Student Name:** Dua Rehan
- **Student ID:** 67238
- **Degree:** BS Computer Science
- **Department:** Department of Computer Science, Iqra University
