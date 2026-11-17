# PowerPlan Scheduler: Master Implementation Plan & Antigravity Specification

**Course:** CSC-471-L Artificial Intelligence (Lab Session 6 — Open-Ended Lab)

**Institution:** Iqra University, Department of Computer Science (BS Computer Science)

**Instructor:** Aimen Zafar | **Section:** Wednesday 2:30–5:20

**Student:** Dua Rehan (Roll No. 67238)

**Evaluation Metrics:** Bloom's Taxonomy `C3, P2` | Graduate Attributes `GA-2, GA-5`

## 1. Executive Copy-Paste Prompt for Antigravity

Copy and paste the prompt block below directly into **Antigravity** as your initial workspace mission instruction. Every subsequent section in this document serves as the technical blueprint that Antigravity should follow file-by-file.

```
You are an expert Python AI engineer building "PowerPlan Scheduler", a complete, production-grade Open-Ended Lab project for CSC-471-L Artificial Intelligence (Lab Session 6).

PROJECT GOAL:
Build an intelligent outage-aware household appliance scheduling system modeled as a deterministic state-space search problem in pure Python using Object-Oriented Programming (OOP). The agent allocates a fixed set of household appliances across discrete time slots subject to strict grid capacity limits, scheduled power outages, and fluctuating energy tariffs, comparing three classical AI search strategies:
1. Breadth-First Search (BFS) — FIFO Queue optimizing for earliest completion time (shallowest goal slot).
2. Depth-First Search (DFS) — LIFO Stack optimizing for the first computationally feasible schedule with minimal memory overhead.
3. A* Search (A-Star) — Priority Queue using f(n) = g(n) + h(n) with an admissible heuristic h(n) = Remaining Energy Units * Lowest Future Active Slot Tariff to optimize for minimum total energy cost.

REQUIRED OOP CLASSES (Strictly Required by Proposal):
- ApplianceJob: Represents an appliance task with job_id, name, power_per_slot (units/kW), duration_slots (default 1 or multi-slot), priority, and total energy requirement.
- PowerSlot: Represents a chronological time block with slot_index (1-based display, 0-based internal), label, is_outage (bool), capacity_limit (units), and unit_price ($ or PKR per energy unit).
- ScheduleState: Immutable, hashable state representation tracking current_slot_index, remaining_durations (tuple of remaining slots per job), assignments (tuple of tuples recording which jobs ran in each prior slot), g_cost (cumulative energy cost), and last_active_slot (for completion time tracking).
- SchedulingEnvironment: State-action transition model implementing get_initial_state(), is_goal_state(state), get_valid_actions(state) (forces IDLE during outages; otherwise generates all power-feasible combinations of unfinished jobs including the IDLE action so the agent can wait out expensive slots), apply_action(state, action), and get_min_future_price(from_slot_index).
- SchedulingAgent: Implements solve_bfs(), solve_dfs(), solve_astar(), and run_all_comparisons(), logging nodes_expanded, nodes_generated, max_frontier_size, execution_time_ms, total_energy_cost, completion_slot, and full step-by-step action path.

DELIVERABLES TO GENERATE & VERIFY:
1. Modular Python package (`powerplan/`) + standalone CLI entry point (`main.py`) + self-contained Jupyter Notebook (`PowerPlan_Lab6_Complete.ipynb`).
2. Publication-quality Matplotlib/Seaborn visual analytics saved to `outputs/`:
   - `schedule_heatmap.png`: 3-panel side-by-side schedule heatmap (BFS vs. DFS vs. A*) showing job allocations across slots, outage overlays, slot tariff headers, and slot load vs. capacity bars.
   - `algorithm_metrics_comparison.png`: 4-panel bar chart comparing Total Energy Cost, Completion Slot, Nodes Expanded, and Peak Frontier Memory across BFS, DFS, and A*.
   - `combinatorial_scaling_analysis.png`: Empirical branching & state-space pruning curve (3 to 7 appliances) demonstrating how A* prunes the combinatorial explosion compared to blind search.
3. Interactive Streamlit Web Dashboard (`app.py`) allowing live manipulation of appliance loads, slot tariffs, outage toggles, and capacity limits during the lab viva/demo.
4. Automated Pytest verification suite (`tests/test_powerplan.py`) proving heuristic admissibility, outage constraint enforcement, capacity compliance, and A* cost optimality.
5. Auto-generated experimental report (`outputs/Lab6_Experimental_Report.md` and `outputs/benchmark_results.csv`) populated with live execution metrics matching all 9 Deliverable sections of the lab proposal.

Execute the build systematically: create the directory structure, implement all modules with full type hints and docstrings, run the test suite, execute `main.py` to generate all plots and data files, and verify zero runtime warnings or errors.

```

## 2. Project Requirements Matrix Mapped to Proposal

Every element from the submitted proposal is mapped below to concrete software components and enhancements to maximize `C3` (Application), `P2` (Mechanism/Guided Response), `GA-2` (Problem Analysis), and `GA-5` (Modern Tool Usage) marks.

| Proposal Requirement | Exact Technical Implementation | High-Impact Enhancement Added | 
| ----- | ----- | ----- | 
| **OOP Architecture** (`ApplianceJob`, `PowerSlot`, `ScheduleState`, `SchedulingEnvironment`, `SchedulingAgent`) | Dedicated `powerplan/models.py`, `powerplan/environment.py`, and `powerplan/agent.py` modules with `@dataclass(frozen=True)` hashable states | Full type annotations, validation guards, and JSON/CSV serialization for custom test scenarios | 
| **Outage-Aware State Transition** (Flowchart in Deliverable 4) | If `slot.is_outage == True`, `get_valid_actions()` strictly returns `[()]` (Force `IDLE`); otherwise generates power-feasible subsets via `itertools.combinations` | Explicit option to remain `IDLE` even during active slots so A\* can intentionally skip high-tariff peak periods | 
| **BFS (Time Optimization)** | FIFO `collections.deque` exploring level-by-level with early goal detection and preference for non-idle progress | Tracks both slot-depth completion (`completion_slot`) and cumulative cost to prove the time-vs-cost trade-off | 
| **DFS (Memory-Efficient First Feasible Schedule)** | LIFO `list` stack with cycle/visited checking and deterministic ordering | Logs peak frontier size (`max_frontier_size`) alongside BFS and A\* to empirically prove DFS's low memory footprint | 
| **A* Search (Cost Optimization + Admissible Heuristic)*\* | `heapq` priority queue ordered by `(f_cost, h_cost, completion_slot, tie_breaker)` where $f(n) = g(n) + h(n)$ | Formal feasibility lookahead pruning: prunes branches immediately if remaining required energy exceeds total remaining active capacity | 
| **Bounded Simulation Data** (4 Jobs, 6 Slots) | Exact default scenario with Water Pump (2u), Washing Machine (3u), Dishwasher (2u), EV Charger (4u) across 6 slots with outages & varying prices | Adds Scenario 2 (Karachi K-Electric Load-Shedding + Peak/Off-Peak ToU) and Scenario 3 (Combinatorial Scaling Benchmark) | 
| **Visual Schedule Heatmap & Analytical Summary** | `powerplan/visualizer.py` rendering high-DPI heatmaps and comparative performance charts | Adds an interactive Streamlit UI (`app.py`) and Jupyter Notebook (`PowerPlan_Lab6_Complete.ipynb`) for live lab demonstration | 

## 3. Target Repository Architecture

Instruct Antigravity to scaffold the following clean workspace layout:

```
powerplan_scheduler/
├── powerplan/
│   ├── __init__.py
│   ├── models.py          # ApplianceJob, PowerSlot, ScheduleState, SearchResult
│   ├── environment.py     # SchedulingEnvironment (state transitions, action generator, heuristic helper)
│   ├── agent.py           # SchedulingAgent (BFS, DFS, A* search implementations + instrumentation)
│   ├── scenarios.py       # Predefined datasets: Proposal 6-Slot, K-Electric 12-Slot, Scaling Suite
│   ├── visualizer.py      # Matplotlib/Seaborn heatmap, metrics comparison, and pruning plots
│   └── reporter.py        # Terminal table printer, CSV exporter, and Markdown Lab Report generator
├── tests/
│   └── test_powerplan.py  # Pytest suite verifying outage rules, capacity limits, and heuristic admissibility
├── outputs/               # Auto-populated charts, CSVs, and generated Lab 6 report
│   ├── schedule_heatmap.png
│   ├── algorithm_metrics_comparison.png
│   ├── combinatorial_scaling_analysis.png
│   ├── benchmark_results.csv
│   └── Lab6_Experimental_Report.md
├── app.py                 # Interactive Streamlit dashboard for live classroom/viva demonstration
├── main.py                # One-command CLI runner executing all scenarios, plots, and reports
├── PowerPlan_Lab6_Complete.ipynb  # Self-contained Jupyter Notebook for step-by-step lab grading
└── requirements.txt       # Dependencies: matplotlib, seaborn, numpy, pandas, tabulate, streamlit, pytest

```

## 4. Mathematical Formulation & State-Space Design

To ensure the algorithms behave meaningfully and distinctly on the 6-slot problem, the mathematical model must be rock-solid.

### 4.1 Flexible Job & Energy Representation

In the proposal's Data Collection section, the four appliances are defined as:

* **Water Pump:** 2 units

* **Washing Machine:** 3 units

* **Dishwasher:** 2 units

* **EV Charger:** 4 units

To support both **atomic single-slot jobs** (where each appliance needs 1 slot of operation drawing $P_i$ units of power) and **multi-slot jobs** (where an appliance requires $D_i$ slots of operation at $P_i$ power units per slot), `ApplianceJob` includes:

* `power_units: int` — Power/energy consumed per active slot (e.g., 2, 3, 2, 4 units), checked against `slot.capacity_limit`.

* `duration_slots: int` — Number of time slots required to complete the job (defaults to `1` in the standard 6-slot proposal benchmark so all 4 jobs total $2 + 3 + 2 + 4 = 11$ energy units, or configurable to multi-slot durations in extended scenarios).

### 4.2 State Tuple (`ScheduleState`)

Each state $s$ in the search tree is uniquely identified for graph-search visited/cost tracking by:

$$
\text{key}(s) = \left( t, \; (r_1, r_2, \dots, r_N) \right)
$$


where:

* $t \in \{0, 1, \dots, M\}$ is the current time slot index ($M = 6$ total slots).

* $r_i \in \{0, 1, \dots, D_i\}$ is the remaining number of slots needed for appliance $i$.

* Alongside the core state key, `ScheduleState` stores path metadata:

  * `assignments`: tuple of length $t$, where `assignments[k]` is the tuple of `job_id`s scheduled in slot $k$.

  * `g_cost`: cumulative energy cost incurred from slot $0$ to $t-1$:
    

    $$
    g(s) = \sum_{k=0}^{t-1} \left( \text{price}_k \times \sum_{i \in A_k} P_i \right)
    $$

  * `completion_slot`: the 1-based index of the last slot in which at least one appliance operated (0 if no jobs have completed yet).

### 4.3 Action Generation & Outage Branching (Exact Match to Proposal Flowchart)

At state $s$ with current slot index $t < M$ and unfinished jobs $U(s) = \{ i \mid r_i > 0 \}$:

1. **Goal Check (`All Jobs Completed?`):** If $U(s) = \emptyset$, the agent has completed all jobs! No further actions are needed (or remaining slots are padded as `IDLE` with $0$ cost for heatmap rendering).

2. **Horizon Exhausted Check:** If $t == M$ and $U(s) \neq \emptyset$, this branch is a dead end (returns empty action list `[]`).

3. **Outage Check (`Is Current Slot an Outage?`):**

   * If `slots[t].is_outage == True`: The only legal action is `IDLE`, represented as the empty tuple `()`.

   * If `slots[t].is_outage == False`: Generate all subsets $A \subseteq U(s)$ (from size $0$ up to $\vert{}U(s)\vert{}$) that satisfy the grid capacity constraint:
     

     $$
     \sum_{i \in A} P_i \le C_t
     $$

     
     where $C_t$ is `slots[t].capacity_limit`. Including $A = \emptyset$ (`IDLE`) during active slots is essential because it allows A\* to intentionally hold back appliances during high-tariff slots and schedule them in cheaper future slots.

### 4.4 Feasibility Lookahead & Admissible A\* Heuristic $h(n)$

For any state $s$ at slot $t$:

* **Remaining Energy Requirement:**
  

  $$
  E_{\text{rem}}(s) = \sum_{i=1}^{N} r_i \times P_i
  $$

* **Capacity Feasibility Pruning (Optional Guard):** Let $C_{\text{rem}}(t) = \sum_{k=t}^{M-1} (1 - \text{outage}_k) C_k$ be the total remaining active grid capacity across all future slots. If $E_{\text{rem}}(s) > C_{\text{rem}}(t)$ or $\max_{i: r_i > 0} r_i > \sum_{k=t}^{M-1} (1 - \text{outage}_k)$, the state cannot possibly finish all jobs before the horizon ends, so $h(s) = \infty$.

* **Admissible Cost Heuristic:** Let $p_{\min}(t)$ be the minimum `unit_price` among all active (non-outage) slots from index $t$ to $M-1$:
  

  $$
  p_{\min}(t) = \min_{\substack{k \in \{t, \dots, M-1\} \\ \text{outage}_k = \text{False}}} \text{price}_k
  $$

  
  Then:
  

  $$
  h(s) = E_{\text{rem}}(s) \times p_{\min}(t)
  $$

* **Proof of Admissibility (For Report Section 1 & 5):** Every remaining energy unit in $E_{\text{rem}}(s)$ must be scheduled in some active slot $k \ge t$ at a tariff $\text{price}_k \ge p_{\min}(t)$. By relaxing the grid capacity constraint $C_k$ and assuming all remaining energy can be bought at the single lowest future tariff $p_{\min}(t)$, $h(s) \le h^*(s)$ always holds. Therefore, $h(s)$ never overestimates the true minimum remaining cost $h^*(s)$, guaranteeing that A\* finds the globally cost-optimal schedule.

## 5. Calibrated Default Dataset (Guaranteeing Distinct BFS, DFS, and A\* Schedules)

A common pitfall in student implementations is choosing slot prices where Slot 1 is the cheapest—causing BFS and A\* to output the exact same schedule. To fulfill **Deliverable 6 (Results)** (*"distinctly showcasing BFS aggressively packing jobs in early slots, DFS producing arbitrary valid spreads, and A* actively bypassing high-tariff slots to minimize cost"\*), use the following calibrated 6-slot dataset as **Scenario 1 (Default Lab Benchmark)**:

### 5.1 Appliances (`ApplianceJob` Instances)

| Job ID | Appliance Name | Power Units ($P_i$) | Duration Slots ($D_i$) | Total Energy Units | 
| ----- | ----- | ----- | ----- | ----- | 
| `WP` | Water Pump | 2 units | 1 slot | 2 units | 
| `WM` | Washing Machine | 3 units | 1 slot | 3 units | 
| `DW` | Dishwasher | 2 units | 1 slot | 2 units | 
| `EV` | EV Charger | 4 units | 1 slot | 4 units | 

*Total Energy Required:* $2 + 3 + 2 + 4 = 11\text{ units}$.

### 5.2 Time Slots (`PowerSlot` Instances — Grid Capacity $C_t = 6\text{ units/slot}$)

| Slot Index | Slot Label | Status (`is_outage`) | Capacity Limit ($C_t$) | Unit Tariff (`unit_price`) | Role in Demonstrating AI Behavior | 
| ----- | ----- | ----- | ----- | ----- | ----- | 
| **Slot 1** | `Slot 1 (Morning)` | Active (`False`) | 6 units | **\$10 / unit** | Moderate tariff; BFS packs maximum load (6u) here immediately | 
| **Slot 2** | `Slot 2 (Mid-Morning)` | **OUTAGE (`True`)** | 0 units (6u nominal) | **\$0 / unit** | Forced `IDLE` due to scheduled outage | 
| **Slot 3** | `Slot 3 (Afternoon Peak)` | Active (`False`) | 6 units | **\$15 / unit** | High tariff; BFS finishes remaining 5u here (early completion at Slot 3!), whereas A\* skips or minimizes it | 
| **Slot 4** | `Slot 4 (Evening Shoulder)` | Active (`False`) | 6 units | **\$8 / unit** | Cheaper shoulder tariff; A\* shifts 5u/6u here | 
| **Slot 5** | `Slot 5 (Night Peak)` | Active (`False`) | 6 units | **\$20 / unit** | Expensive peak slot; A\* completely avoids this slot (`IDLE`) | 
| **Slot 6** | `Slot 6 (Late-Night Off-Peak)` | Active (`False`) | 6 units | **\$4 / unit** | Lowest tariff of the week; A\* packs maximum 6u here! | 

### 5.3 Expected Behavioral Contrast on Scenario 1

1. **BFS (Earliest Completion Time):**

   * Orders actions in each active slot from largest job count / energy load down to `IDLE` so the shallowest goal state is reached first.

   * **Schedule:** Packs **6 units** in **Slot 1** (e.g., `EV` 4u + `WP` 2u = 6u at \$10/u = $60), forces **IDLE** in **Slot 2 (Outage)**, and packs the remaining **5 units** in **Slot 3** (`WM` 3u + `DW` 2u = 5u at \$15/u = $75).

   * **Outcome:** Completes all jobs by **Slot 3** (earliest possible slot!) at a Total Cost of **\$135**.

2. **DFS (First Feasible Schedule / Low Memory):**

   * Uses a LIFO stack, diving deep down a single branch before backtracking. Depending on action push order, produces an arbitrary valid spread across later slots (e.g., spreading jobs across Slots 1, 4, 5, 6 or 3, 4, 6) with minimal frontier memory (`max_frontier_size` much smaller than BFS).

3. **A* Search (Minimum Energy Cost):*\*

   * Guided by $f(n) = g(n) + h(n)$, A\* recognizes that Slot 3 (\$15/u) and Slot 5 ($20/u) are expensive compared to Slot 4 ($8/u) and Slot 6 ($4/u).

   * **Schedule:** Remains **IDLE** in Slot 1 (\$10), Slot 2 (Outage), Slot 3 ($15), and Slot 5 ($20); schedules **5 units** in **Slot 4** (\$8/u $\times 5 = \$40$) and **6 units** in **Slot 6** (\$4/u $\times 6 = \$24$).

   * **Outcome:** Completes at **Slot 6** with the globally optimal Total Cost of **\$64** (saving **52.6%** compared to BFS's \$135!).

## 6. Complete Module-by-Module Reference Implementation

Provide the following complete, production-ready code specifications to Antigravity so it writes every file cleanly without placeholders.

### 6.1 `powerplan/models.py`

```
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ApplianceJob:
    """Represents a household appliance task requiring power allocation."""
    job_id: str
    name: str
    power_units: int          # Power drawn per active slot (e.g., kW or abstract units)
    duration_slots: int = 1   # Number of slots required to finish the job
    priority: int = 1         # Optional tie-breaking priority (1 = highest)

    def __post_init__(self) -> None:
        if self.power_units <= 0:
            raise ValueError(f"Appliance {self.name} power_units must be positive.")
        if self.duration_slots <= 0:
            raise ValueError(f"Appliance {self.name} duration_slots must be positive.")

    @property
    def total_energy_units(self) -> int:
        """Total energy units required across the entire duration of the job."""
        return self.power_units * self.duration_slots


@dataclass(frozen=True)
class PowerSlot:
    """Represents a discrete chronological time block in the power grid schedule."""
    slot_index: int           # 1-based chronological slot number (1..M)
    label: str                # Human-readable slot description
    is_outage: bool           # True if scheduled load-shedding / outage
    capacity_limit: int       # Maximum simultaneous power units allowed in this slot
    unit_price: float         # Tariff per energy unit in this slot ($ or PKR)

    @property
    def effective_capacity(self) -> int:
        """Returns 0 during an outage, otherwise capacity_limit."""
        return 0 if self.is_outage else self.capacity_limit


@dataclass(frozen=True)
class ScheduleState:
    """
    Immutable state representation in the scheduling state space.
    - current_slot_index: 0-based index into the environment's slots list.
    - remaining_durations: tuple of remaining slot counts for each job (aligned with env.jobs).
    - assignments: tuple of tuples, where assignments[t] holds job_ids scheduled in slot t.
    - g_cost: cumulative energy cost incurred up to current_slot_index.
    - completion_slot: 1-based slot number where the final appliance completed (0 if incomplete).
    """
    current_slot_index: int
    remaining_durations: Tuple[int, ...]
    assignments: Tuple[Tuple[str, ...], ...] = field(default_factory=tuple)
    g_cost: float = 0.0
    completion_slot: int = 0

    @property
    def state_key(self) -> Tuple[int, Tuple[int, ...]]:
        """Canonical graph-search key identifying the Markovian state."""
        return (self.current_slot_index, self.remaining_durations)

    def is_all_completed(self) -> bool:
        """Returns True when every appliance has 0 remaining duration."""
        return all(rem == 0 for rem in self.remaining_durations)


@dataclass
class SearchResult:
    """Encapsulates the solution schedule and telemetry metrics for a search run."""
    algorithm_name: str
    goal_Description: str
    success: bool
    final_state: Optional[ScheduleState]
    total_cost: float
    completion_slot: int
    nodes_expanded: int
    nodes_generated: int
    max_frontier_size: int
    execution_time_ms: float
    slot_assignments: Dict[int, List[str]]          # 1-based slot_index -> list of job_ids
    slot_loads: Dict[int, int]                      # 1-based slot_index -> total power units used
    slot_costs: Dict[int, float]                    # 1-based slot_index -> cost incurred in slot
    search_trace: List[Dict[str, object]] = field(default_factory=list)

```

### 6.2 `powerplan/environment.py`

```
from __future__ import annotations
from itertools import combinations
from typing import Dict, List, Tuple
from powerplan.models import ApplianceJob, PowerSlot, ScheduleState


class SchedulingEnvironment:
    """
    Deterministic, fully observable state-action transition environment for PowerPlan.
    Models outage enforcement, grid capacity filtering, cost accumulation, and heuristic bounds.
    """

    def __init__(self, jobs: List[ApplianceJob], slots: List[PowerSlot], name: str = "Default") -> None:
        if not jobs:
            raise ValueError("SchedulingEnvironment requires at least one ApplianceJob.")
        if not slots:
            raise ValueError("SchedulingEnvironment requires at least one PowerSlot.")
        self.name = name
        self.jobs: Tuple[ApplianceJob, ...] = tuple(jobs)
        self.slots: Tuple[PowerSlot, ...] = tuple(slots)
        self.job_map: Dict[str, ApplianceJob] = {job.job_id: job for job in self.jobs}
        self.job_index_map: Dict[str, int] = {job.job_id: idx for idx, job in enumerate(self.jobs)}

    def get_initial_state(self) -> ScheduleState:
        """Constructs the root ScheduleState at slot index 0 with full job durations."""
        initial_remaining = tuple(job.duration_slots for job in self.jobs)
        return ScheduleState(
            current_slot_index=0,
            remaining_durations=initial_remaining,
            assignments=tuple(),
            g_cost=0.0,
            completion_slot=0,
        )

    def is_goal_state(self, state: ScheduleState) -> bool:
        """Goal test: returns True as soon as all jobs have 0 remaining duration."""
        return state.is_all_completed()

    def get_remaining_energy(self, state: ScheduleState) -> int:
        """Calculates total remaining energy units required across all unfinished jobs."""
        return sum(
            rem * self.jobs[idx].power_units
            for idx, rem in enumerate(state.remaining_durations)
        )

    def is_remaining_feasible(self, state: ScheduleState) -> bool:
        """
        Lookahead feasibility check: verifies whether remaining active slots have enough
        aggregate capacity and active slot count to finish all remaining work.
        """
        if state.is_all_completed():
            return True
        if state.current_slot_index >= len(self.slots):
            return False

        remaining_slots = self.slots[state.current_slot_index:]
        active_slots = [s for s in remaining_slots if not s.is_outage]

        max_needed_slots = max(state.remaining_durations)
        if max_needed_slots > len(active_slots):
            return False

        total_remaining_capacity = sum(s.effective_capacity for s in active_slots)
        if self.get_remaining_energy(state) > total_remaining_capacity:
            return False

        return True

    def get_valid_actions(self, state: ScheduleState) -> List[Tuple[str, ...]]:
        """
        Generates all valid appliance combinations for the current slot:
        - If all jobs are already completed or horizon is reached, returns [].
        - If current slot is an OUTAGE, forces IDLE: returns [()].
        - Otherwise, generates all subsets of unfinished jobs whose combined power_units
          do not exceed slot.capacity_limit, including () (IDLE).
        """
        if state.is_all_completed() or state.current_slot_index >= len(self.slots):
            return []

        current_slot = self.slots[state.current_slot_index]

        # Flowchart Rule: Is Current Slot an Outage? -> Yes -> Action: Force IDLE
        if current_slot.is_outage:
            return [tuple()]

        # Identify unfinished job indices
        unfinished_indices = [
            idx for idx, rem in enumerate(state.remaining_durations) if rem > 0
        ]

        valid_actions: List[Tuple[str, ...]] = [tuple()]  # Always include IDLE action ()
        capacity = current_slot.capacity_limit

        for r in range(1, len(unfinished_indices) + 1):
            for combo_indices in combinations(unfinished_indices, r):
                combo_power = sum(self.jobs[i].power_units for i in combo_indices)
                if combo_power <= capacity:
                    action = tuple(self.jobs[i].job_id for i in combo_indices)
                    valid_actions.append(action)

        return valid_actions

    def apply_action(self, state: ScheduleState, action: Tuple[str, ...]) -> ScheduleState:
        """
        Applies a valid action (tuple of job_ids) in the current slot and returns the next ScheduleState.
        """
        slot = self.slots[state.current_slot_index]
        if slot.is_outage and len(action) > 0:
            raise ValueError(f"Cannot schedule jobs {action} during outage slot {slot.slot_index}.")

        action_power = sum(self.job_map[jid].power_units for jid in action)
        if action_power > slot.effective_capacity:
            raise ValueError(
                f"Action {action} power ({action_power}u) exceeds slot {slot.slot_index} "
                f"capacity ({slot.effective_capacity}u)."
            )

        new_remaining = list(state.remaining_durations)
        for jid in action:
            idx = self.job_index_map[jid]
            if new_remaining[idx] <= 0:
                raise ValueError(f"Job {jid} is already completed.")
            new_remaining[idx] -= 1

        step_cost = action_power * slot.unit_price
        next_slot_number = slot.slot_index  # 1-based slot number
        new_completion_slot = (
            next_slot_number if len(action) > 0 else state.completion_slot
        )

        return ScheduleState(
            current_slot_index=state.current_slot_index + 1,
            remaining_durations=tuple(new_remaining),
            assignments=state.assignments + (action,),
            g_cost=round(state.g_cost + step_cost, 6),
            completion_slot=new_completion_slot,
        )

    def calculate_heuristic(self, state: ScheduleState) -> float:
        """
        Admissible A* heuristic:
        h(n) = Remaining Energy Units * Lowest Future Active Slot Unit Price.
        Returns float('inf') if remaining jobs cannot possibly be completed in future slots.
        """
        if state.is_all_completed():
            return 0.0

        if not self.is_remaining_feasible(state):
            return float("inf")

        future_active_prices = [
            s.unit_price
            for s in self.slots[state.current_slot_index:]
            if not s.is_outage
        ]
        if not future_active_prices:
            return float("inf")

        min_future_price = min(future_active_prices)
        remaining_energy = self.get_remaining_energy(state)
        return round(remaining_energy * min_future_price, 6)

```

### 6.3 `powerplan/agent.py`

```
from __future__ import annotations
from collections import deque
import heapq
import itertools
import time
from typing import Dict, List, Optional, Set, Tuple
from powerplan.environment import SchedulingEnvironment
from powerplan.models import ScheduleState, SearchResult


class SchedulingAgent:
    """
    Intelligent scheduling agent implementing BFS, DFS, and A* search strategies
    over the SchedulingEnvironment state space.
    """

    def __init__(self, env: SchedulingEnvironment) -> None:
        self.env = env

    def _build_result(
        self,
        algorithm_name: str,
        goal_description: str,
        final_state: Optional[ScheduleState],
        nodes_expanded: int,
        nodes_generated: int,
        max_frontier_size: int,
        start_time: float,
        search_trace: List[Dict[str, object]],
    ) -> SearchResult:
        elapsed_ms = round((time.perf_counter() - start_time) * 1000.0, 3)
        slot_assignments: Dict[int, List[str]] = {}
        slot_loads: Dict[int, int] = {}
        slot_costs: Dict[int, float] = {}

        for slot in self.env.slots:
            s_idx = slot.slot_index
            if final_state is not None and (s_idx - 1) < len(final_state.assignments):
                assigned = list(final_state.assignments[s_idx - 1])
            else:
                assigned = []
            load = sum(self.env.job_map[jid].power_units for jid in assigned)
            cost = round(load * slot.unit_price, 2)
            slot_assignments[s_idx] = assigned
            slot_loads[s_idx] = load
            slot_costs[s_idx] = cost

        return SearchResult(
            algorithm_name=algorithm_name,
            goal_Description=goal_description,
            success=final_state is not None,
            final_state=final_state,
            total_cost=round(final_state.g_cost, 2) if final_state else float("inf"),
            completion_slot=final_state.completion_slot if final_state else -1,
            nodes_expanded=nodes_expanded,
            nodes_generated=nodes_generated,
            max_frontier_size=max_frontier_size,
            execution_time_ms=elapsed_ms,
            slot_assignments=slot_assignments,
            slot_loads=slot_loads,
            slot_costs=slot_costs,
            search_trace=search_trace,
        )

    def solve_bfs(self) -> SearchResult:
        """
        Breadth-First Search (FIFO Queue).
        Optimizes for Earliest Completion Time (shallowest slot depth where all jobs finish).
        Orders single-slot actions from highest energy packed to IDLE so full packing is explored first.
        """
        start_time = time.perf_counter()
        initial_state = self.env.get_initial_state()
        if self.env.is_goal_state(initial_state):
            return self._build_result(
                "BFS (Breadth-First Search)",
                "Earliest Completion Time",
                initial_state, 0, 1, 1, start_time, []
            )

        frontier: deque[ScheduleState] = deque([initial_state])
        visited: Set[Tuple[int, Tuple[int, ...]]] = {initial_state.state_key}
        nodes_expanded = 0
        nodes_generated = 1
        max_frontier_size = 1
        trace: List[Dict[str, object]] = []

        while frontier:
            max_frontier_size = max(max_frontier_size, len(frontier))
            state = frontier.popleft()
            nodes_expanded += 1

            # Sort actions by descending total energy packed so BFS prioritizes earliest work completion
            actions = self.env.get_valid_actions(state)
            actions.sort(
                key=lambda act: (
                    sum(self.env.job_map[jid].power_units for jid in act),
                    len(act),
                ),
                reverse=True,
            )

            for action in actions:
                next_state = self.env.apply_action(state, action)
                nodes_generated += 1

                if not self.env.is_remaining_feasible(next_state):
                    continue

                if self.env.is_goal_state(next_state):
                    trace.append({
                        "step": nodes_expanded,
                        "slot": state.current_slot_index + 1,
                        "action": action,
                        "g_cost": next_state.g_cost,
                        "event": "GOAL_FOUND",
                    })
                    return self._build_result(
                        "BFS (Breadth-First Search)",
                        "Earliest Completion Time",
                        next_state,
                        nodes_expanded,
                        nodes_generated,
                        max_frontier_size,
                        start_time,
                        trace,
                    )

                if next_state.state_key not in visited:
                    visited.add(next_state.state_key)
                    frontier.append(next_state)

        return self._build_result(
            "BFS (Breadth-First Search)",
            "Earliest Completion Time",
            None,
            nodes_expanded,
            nodes_generated,
            max_frontier_size,
            start_time,
            trace,
        )

    def solve_dfs(self) -> SearchResult:
        """
        Depth-First Search (LIFO Stack).
        Optimizes for finding the first computationally feasible schedule with minimal memory overhead.
        Pushes actions so modest single/pair allocations are explored at the top of the LIFO stack,
        producing a realistic multi-slot DFS spread distinct from BFS and A*.
        """
        start_time = time.perf_counter()
        initial_state = self.env.get_initial_state()
        stack: List[ScheduleState] = [initial_state]
        visited: Set[Tuple[int, Tuple[int, ...]]] = set()
        nodes_expanded = 0
        nodes_generated = 1
        max_frontier_size = 1
        trace: List[Dict[str, object]] = []

        while stack:
            max_frontier_size = max(max_frontier_size, len(stack))
            state = stack.pop()

            if self.env.is_goal_state(state):
                return self._build_result(
                    "DFS (Depth-First Search)",
                    "First Feasible Schedule (Low Memory)",
                    state,
                    nodes_expanded,
                    nodes_generated,
                    max_frontier_size,
                    start_time,
                    trace,
                )

            if state.state_key in visited:
                continue
            visited.add(state.state_key)
            nodes_expanded += 1

            actions = self.env.get_valid_actions(state)
            # Push IDLE first and moderate single-appliance actions last (so they pop first from LIFO)
            actions.sort(
                key=lambda act: (
                    len(act) == 1,
                    len(act) > 1,
                    -sum(self.env.job_map[jid].power_units for jid in act),
                )
            )

            for action in actions:
                next_state = self.env.apply_action(state, action)
                nodes_generated += 1
                if (
                    next_state.state_key not in visited
                    and self.env.is_remaining_feasible(next_state)
                ):
                    stack.append(next_state)

        return self._build_result(
            "DFS (Depth-First Search)",
            "First Feasible Schedule (Low Memory)",
            None,
            nodes_expanded,
            nodes_generated,
            max_frontier_size,
            start_time,
            trace,
        )

    def solve_astar(self) -> SearchResult:
        """
        A* Search (Priority Queue ordered by f(n) = g(n) + h(n)).
        Uses the admissible heuristic h(n) = Remaining Energy * Lowest Future Active Price
        to guarantee the minimum total energy cost schedule.
        """
        start_time = time.perf_counter()
        initial_state = self.env.get_initial_state()
        counter = itertools.count()

        init_h = self.env.calculate_heuristic(initial_state)
        # Priority tuple: (f_cost, h_cost, completion_slot, tie_breaker, state)
        frontier: List[Tuple[float, float, int, int, ScheduleState]] = [
            (init_h, init_h, 0, next(counter), initial_state)
        ]
        best_g: Dict[Tuple[int, Tuple[int, ...]], float] = {initial_state.state_key: 0.0}

        nodes_expanded = 0
        nodes_generated = 1
        max_frontier_size = 1
        trace: List[Dict[str, object]] = []

        while frontier:
            max_frontier_size = max(max_frontier_size, len(frontier))
            f_cost, h_cost, _, _, state = heapq.heappop(frontier)

            if self.env.is_goal_state(state):
                return self._build_result(
                    "A* Search (Heuristic Cost-Optimal)",
                    "Minimum Total Energy Cost",
                    state,
                    nodes_expanded,
                    nodes_generated,
                    max_frontier_size,
                    start_time,
                    trace,
                )

            # Skip stale priority queue entries if a cheaper path to state_key was already found
            if state.g_cost > best_g.get(state.state_key, float("inf")):
                continue

            nodes_expanded += 1

            for action in self.env.get_valid_actions(state):
                next_state = self.env.apply_action(state, action)
                nodes_generated += 1

                h_next = self.env.calculate_heuristic(next_state)
                if h_next == float("inf"):
                    continue  # Pruned by feasibility/admissible heuristic bound

                g_next = next_state.g_cost
                f_next = round(g_next + h_next, 6)

                # Goal states have canonical key (-1, (0,...,0)) so all goal paths compete strictly on g_cost
                canonical_key = (
                    (-1, next_state.remaining_durations)
                    if next_state.is_all_completed()
                    else next_state.state_key
                )

                if g_next < best_g.get(canonical_key, float("inf")):
                    best_g[canonical_key] = g_next
                    heapq.heappush(
                        frontier,
                        (f_next, h_next, next_state.completion_slot, next(counter), next_state),
                    )

        return self._build_result(
            "A* Search (Heuristic Cost-Optimal)",
            "Minimum Total Energy Cost",
            None,
            nodes_expanded,
            nodes_generated,
            max_frontier_size,
            start_time,
            trace,
        )

    def run_all_comparisons(self) -> Dict[str, SearchResult]:
        """Executes BFS, DFS, and A* on the same initialized environment and returns results."""
        return {
            "BFS": self.solve_bfs(),
            "DFS": self.solve_dfs(),
            "A*": self.solve_astar(),
        }

```

### 6.4 `powerplan/scenarios.py`

Include three built-in scenarios so the project covers both the exact bounded lab specification and real-world local load-shedding extensions:

```
from __future__ import annotations
from typing import List
from powerplan.environment import SchedulingEnvironment
from powerplan.models import ApplianceJob, PowerSlot


def create_proposal_default_environment() -> SchedulingEnvironment:
    """
    Scenario 1: Exact 4-Appliance, 6-Slot Bounded Simulation from the Lab 6 Proposal.
    Grid capacity = 6 units per active slot.
    Slot 2 is a scheduled outage ($0). Tariffs fluctuate between $4 and $20.
    """
    jobs = [
        ApplianceJob(job_id="WP", name="Water Pump", power_units=2, duration_slots=1, priority=1),
        ApplianceJob(job_id="WM", name="Washing Machine", power_units=3, duration_slots=1, priority=2),
        ApplianceJob(job_id="DW", name="Dishwasher", power_units=2, duration_slots=1, priority=3),
        ApplianceJob(job_id="EV", name="EV Charger", power_units=4, duration_slots=1, priority=1),
    ]
    slots = [
        PowerSlot(slot_index=1, label="Slot 1 (Morning)", is_outage=False, capacity_limit=6, unit_price=10.0),
        PowerSlot(slot_index=2, label="Slot 2 (Outage)", is_outage=True, capacity_limit=6, unit_price=0.0),
        PowerSlot(slot_index=3, label="Slot 3 (Peak)", is_outage=False, capacity_limit=6, unit_price=15.0),
        PowerSlot(slot_index=4, label="Slot 4 (Shoulder)", is_outage=False, capacity_limit=6, unit_price=8.0),
        PowerSlot(slot_index=5, label="Slot 5 (Super Peak)", is_outage=False, capacity_limit=6, unit_price=20.0),
        PowerSlot(slot_index=6, label="Slot 6 (Off-Peak)", is_outage=False, capacity_limit=6, unit_price=4.0),
    ]
    return SchedulingEnvironment(jobs=jobs, slots=slots, name="Proposal_6Slot_Benchmark")


def create_karachi_kelectric_environment() -> SchedulingEnvironment:
    """
    Scenario 2: Multi-Duration Household Load Shifting under Local Load-Shedding (8 Slots).
    Demonstrates appliances that require multiple slots of execution (e.g., EV Charger 2 slots, AC/Pump).
    """
    jobs = [
        ApplianceJob(job_id="WP", name="Water Pump", power_units=2, duration_slots=1),
        ApplianceJob(job_id="WM", name="Washing Machine", power_units=3, duration_slots=1),
        ApplianceJob(job_id="DW", name="Dishwasher", power_units=2, duration_slots=2),
        ApplianceJob(job_id="EV", name="EV Charger", power_units=4, duration_slots=2),
    ]
    slots = [
        PowerSlot(slot_index=1, label="08:00-10:00", is_outage=False, capacity_limit=6, unit_price=12.0),
        PowerSlot(slot_index=2, label="10:00-12:00 (Outage)", is_outage=True, capacity_limit=6, unit_price=0.0),
        PowerSlot(slot_index=3, label="12:00-14:00", is_outage=False, capacity_limit=6, unit_price=14.0),
        PowerSlot(slot_index=4, label="14:00-16:00", is_outage=False, capacity_limit=6, unit_price=9.0),
        PowerSlot(slot_index=5, label="16:00-18:00 (Outage)", is_outage=True, capacity_limit=6, unit_price=0.0),
        PowerSlot(slot_index=6, label="18:00-20:00 (Peak)", is_outage=False, capacity_limit=6, unit_price=22.0),
        PowerSlot(slot_index=7, label="20:00-22:00 (Peak)", is_outage=False, capacity_limit=6, unit_price=18.0),
        PowerSlot(slot_index=8, label="22:00-00:00 (Off-Peak)", is_outage=False, capacity_limit=6, unit_price=5.0),
    ]
    return SchedulingEnvironment(jobs=jobs, slots=slots, name="Karachi_MultiSlot_ToU")


def create_scaling_environment(num_appliances: int) -> SchedulingEnvironment:
    """
    Scenario 3: Combinatorial State-Space Scaling Generator (for Deliverable 5 Analysis).
    Creates `num_appliances` jobs (3 to 7) across 6 slots to benchmark node expansion growth.
    """
    catalog = [
        ("WP", "Water Pump", 2),
        ("WM", "Washing Machine", 3),
        ("DW", "Dishwasher", 2),
        ("EV", "EV Charger", 4),
        ("IH", "Induction Heater", 2),
        ("DR", "Clothes Dryer", 3),
        ("PP", "Pool Filtration Pump", 2),
    ]
    selected = catalog[:num_appliances]
    jobs = [ApplianceJob(job_id=jid, name=name, power_units=pwr, duration_slots=1) for jid, name, pwr in selected]
    slots = [
        PowerSlot(slot_index=1, label="Slot 1", is_outage=False, capacity_limit=7, unit_price=10.0),
        PowerSlot(slot_index=2, label="Slot 2 (Outage)", is_outage=True, capacity_limit=7, unit_price=0.0),
        PowerSlot(slot_index=3, label="Slot 3", is_outage=False, capacity_limit=7, unit_price=15.0),
        PowerSlot(slot_index=4, label="Slot 4", is_outage=False, capacity_limit=7, unit_price=8.0),
        PowerSlot(slot_index=5, label="Slot 5", is_outage=False, capacity_limit=7, unit_price=20.0),
        PowerSlot(slot_index=6, label="Slot 6", is_outage=False, capacity_limit=7, unit_price=4.0),
    ]
    return SchedulingEnvironment(jobs=jobs, slots=slots, name=f"Scaling_{num_appliances}_Appliances")

```

### 6.5 `powerplan/visualizer.py`

This module produces the visual schedule heatmap required in **Deliverable 4, 6, and Lab Activity**, plus two analytical plots for **Deliverable 5 (Analysis)** and **Deliverable 7 (Discussion on Results)**:

```
from __future__ import annotations
from pathlib import Path
from typing import Dict, List
import matplotlib.pyplot as plt
import numpy as np
from powerplan.environment import SchedulingEnvironment
from powerplan.models import SearchResult


def render_schedule_heatmap(
    env: SchedulingEnvironment,
    results: Dict[str, SearchResult],
    output_path: str = "outputs/schedule_heatmap.png",
) -> str:
    """
    Renders a 3-panel side-by-side Schedule Heatmap comparing BFS, DFS, and A* job allocations
    across time slots, highlighting scheduled outages, slot tariffs, and power unit consumption.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    algo_keys = ["BFS", "DFS", "A*"]
    num_jobs = len(env.jobs)
    num_slots = len(env.slots)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6.2), sharey=True)
    fig.suptitle(
        f"PowerPlan Schedule Heatmap Comparison — {env.name}\n"
        "(Cell Value = Power Units Allocated | Red Column = Outage Slot)",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    job_labels = [f"{j.name}\n({j.job_id}: {j.power_units}u)" for j in env.jobs]
    slot_labels = [
        f"S{s.slot_index}\n{'OUTAGE' if s.is_outage else f'${s.unit_price:.0f}/u'}"
        for s in env.slots
    ]

    for ax_idx, algo_key in enumerate(algo_keys):
        ax = axes[ax_idx]
        res = results[algo_key]
        matrix = np.zeros((num_jobs, num_slots), dtype=float)

        for j_idx, job in enumerate(env.jobs):
            for s_idx, slot in enumerate(env.slots):
                if slot.is_outage:
                    matrix[j_idx, s_idx] = -1.0  # Sentinel for outage shading
                elif job.job_id in res.slot_assignments.get(slot.slot_index, []):
                    matrix[j_idx, s_idx] = float(job.power_units)

        # Custom color mapping: -1 = Outage (soft coral), 0 = Idle (light slate), >0 = Active (teal/navy)
        display_rgb = np.zeros((num_jobs, num_slots, 3), dtype=float)
        for r in range(num_jobs):
            for c in range(num_slots):
                val = matrix[r, c]
                if val < 0:
                    display_rgb[r, c] = (0.96, 0.82, 0.82)  # Outage column tint
                elif val == 0:
                    display_rgb[r, c] = (0.95, 0.96, 0.98)  # Idle cell
                else:
                    # Darker teal for higher power draw
                    intensity = min(val / 4.5, 1.0)
                    display_rgb[r, c] = (
                        0.12 * (1 - intensity) + 0.05,
                        0.55 * (1 - 0.3 * intensity) + 0.15,
                        0.68 * (1 - 0.2 * intensity) + 0.20,
                    )

        ax.imshow(display_rgb, aspect="auto")

        # Annotate each cell
        for r in range(num_jobs):
            for c in range(num_slots):
                val = matrix[r, c]
                if val < 0:
                    ax.text(c, r, "OUTAGE\n(IDLE)", ha="center", va="center", fontsize=8.5, color="#8B1E1E", fontweight="bold")
                elif val == 0:
                    ax.text(c, r, "—", ha="center", va="center", fontsize=11, color="#7A869A")
                else:
                    ax.text(c, r, f"ON\n({int(val)}u)", ha="center", va="center", fontsize=9.5, color="white", fontweight="bold")

        # Draw grid lines
        ax.set_xticks(np.arange(num_slots))
        ax.set_xticklabels(slot_labels, fontsize=9.5, fontweight="bold")
        ax.set_yticks(np.arange(num_jobs))
        if ax_idx == 0:
            ax.set_yticklabels(job_labels, fontsize=10, fontweight="bold")

        # Bottom summary strip per slot: Load / Capacity
        for s_idx, slot in enumerate(env.slots):
            load = res.slot_loads.get(slot.slot_index, 0)
            cap = slot.effective_capacity
            ax.text(
                s_idx,
                num_jobs - 0.52,
                f"Load: {load}/{cap}u",
                ha="center",
                va="bottom",
                fontsize=8,
                color="#1E293B" if not slot.is_outage else "#8B1E1E",
                bbox=dict(boxstyle="round,pad=0.18", facecolor="white", alpha=0.85, edgecolor="none"),
            )

        ax.set_title(
            f"{algo_key}: {res.goal_Description}\n"
            f"Total Cost: ${res.total_cost:.2f} | Completed: Slot {res.completion_slot} | "
            f"Expanded: {res.nodes_expanded} nodes",
            fontsize=10.5,
            fontweight="bold",
            pad=10,
        )

    plt.tight_layout(rect=[0, 0, 1, 0.91])
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def render_metrics_comparison(
    results: Dict[str, SearchResult],
    output_path: str = "outputs/algorithm_metrics_comparison.png",
) -> str:
    """
    Renders a 4-panel bar chart comparing Total Energy Cost ($), Completion Slot,
    Nodes Expanded, and Peak Frontier Memory across BFS, DFS, and A*.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    algos = ["BFS", "DFS", "A*"]
    colors = ["#2563EB", "#D97706", "#059669"]

    metrics = [
        ("Total Energy Cost ($)", [results[k].total_cost for k in algos], "${:.1f}"),
        ("Completion Time (Slot #)", [results[k].completion_slot for k in algos], "Slot {:.0f}"),
        ("Nodes Expanded (Count)", [results[k].nodes_expanded for k in algos], "{:.0f}"),
        ("Peak Frontier Size (Nodes)", [results[k].max_frontier_size for k in algos], "{:.0f}"),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))
    fig.suptitle("PowerPlan Search Strategy Performance Trade-Offs", fontsize=14, fontweight="bold", y=1.02)

    for idx, (title, values, fmt) in enumerate(metrics):
        ax = axes[idx]
        bars = ax.bar(algos, values, color=colors, width=0.55, edgecolor="#1E293B", linewidth=1.0)
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        max_val = max(values) if max(values) > 0 else 1
        ax.set_ylim(0, max_val * 1.22)
        for bar, val in zip(bars, values):
            ax.text(
                bar.get_x() + bar.get_width() / 2.0,
                bar.get_height() + max_val * 0.03,
                fmt.format(val),
                ha="center",
                va="bottom",
                fontsize=9.5,
                fontweight="bold",
            )

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path


def render_scaling_analysis(
    scaling_rows: List[Dict[str, object]],
    output_path: str = "outputs/combinatorial_scaling_analysis.png",
) -> str:
    """
    Plots Nodes Expanded vs. Number of Appliances (3 to 7) to illustrate state-space
    branching explosion and heuristic pruning efficiency.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    counts = [int(r["num_appliances"]) for r in scaling_rows]
    bfs_nodes = [int(r["bfs_expanded"]) for r in scaling_rows]
    dfs_nodes = [int(r["dfs_expanded"]) for r in scaling_rows]
    astar_nodes = [int(r["astar_expanded"]) for r in scaling_rows]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(counts, bfs_nodes, marker="o", linewidth=2.4, color="#2563EB", label="BFS (Uninformed FIFO)")
    ax.plot(counts, dfs_nodes, marker="s", linewidth=2.4, color="#D97706", label="DFS (Uninformed LIFO)")
    ax.plot(counts, astar_nodes, marker="^", linewidth=2.4, color="#059669", label="A* Search (Admissible Heuristic)")

    ax.set_title("Combinatorial Explosion & Heuristic Tree Pruning (3 to 7 Appliances)", fontsize=13, fontweight="bold")
    ax.set_xlabel("Number of Household Appliances Scheduled", fontsize=11, fontweight="bold")
    ax.set_ylabel("Nodes Expanded Before Goal", fontsize=11, fontweight="bold")
    ax.set_xticks(counts)
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(fontsize=10.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path

```

### 6.6 `powerplan/reporter.py` & `main.py`

`powerplan/reporter.py` formats the console output, writes `outputs/benchmark_results.csv`, and generates `outputs/Lab6_Experimental_Report.md` containing all 9 sections required by the lab manual (Background/Theory, Procedure/Methodology, Data Collection, Flowchart/Block Diagram, Analysis, Results, Discussion on Results, Concluding Remarks, and Reference) populated with the exact runtime metrics.

```
from __future__ import annotations
import csv
from pathlib import Path
from typing import Dict, List
from powerplan.environment import SchedulingEnvironment
from powerplan.models import SearchResult


def print_console_summary(env: SchedulingEnvironment, results: Dict[str, SearchResult]) -> None:
    """Prints a formatted comparative summary table and slot-by-slot schedule to stdout."""
    print("=" * 88)
    print(f" POWERPLAN SCHEDULER — AI STATE-SPACE SEARCH BENCHMARK ({env.name})")
    print("=" * 88)
    header = (
        f"{'Algorithm':<34} | {'Cost ($)':>9} | {'Done Slot':>9} | "
        f"{'Expanded':>8} | {'Max Queue':>9} | {'Time (ms)':>9}"
    )
    print(header)
    print("-" * 88)
    for key in ["BFS", "DFS", "A*"]:
        r = results[key]
        print(
            f"{r.algorithm_name:<34} | {r.total_cost:>9.2f} | "
            f"{'Slot ' + str(r.completion_slot):>9} | {r.nodes_expanded:>8d} | "
            f"{r.max_frontier_size:>9d} | {r.execution_time_ms:>9.3f}"
        )
    print("=" * 88)

    for key in ["BFS", "DFS", "A*"]:
        r = results[key]
        print(f"\n[{key}] Detailed Slot Schedule ({r.goal_Description}):")
        for slot in env.slots:
            s_idx = slot.slot_index
            jobs_str = ", ".join(r.slot_assignments[s_idx]) if r.slot_assignments[s_idx] else "IDLE"
            status_tag = "OUTAGE (FORCED IDLE)" if slot.is_outage else f"Active (${slot.unit_price:.0f}/u)"
            print(
                f"  - Slot {s_idx} [{status_tag:<20}]: {jobs_str:<18} "
                f"| Load: {r.slot_loads[s_idx]}/{slot.effective_capacity}u "
                f"| Slot Cost: ${r.slot_costs[s_idx]:.2f}"
            )

```

## 7. Interactive Classroom Demo Dashboard (`app.py`)

To earn top marks under **GA-5 (Modern Tool Usage)** and **P2 (Mechanism)** during the lab demonstration, include a single-file **Streamlit GUI (`app.py`)** that lets the instructor or student adjust parameters live:

1. **Sidebar Controls:**

   * Preset selector: *Proposal 6-Slot Benchmark*, *Karachi K-Electric Load-Shedding (8-Slot Multi-Duration)*, or *Custom Configuration*.

   * Slider for **Grid Capacity Limit (**$C_t$**)** (from 4 units to 12 units).

   * Interactive checkboxes to toggle **Outage Status** on any of the 6 slots.

   * Number inputs for each slot's **Unit Tariff (\$/unit)** and each appliance's **Power Units (**$P_i$**)** and **Duration (**$D_i$**)**.

2. **Main Dashboard Tabs:**

   * **Tab 1 — Visual Schedule Heatmap:** Renders the 3-panel Matplotlib heatmap live and highlights cost savings of A\* vs. BFS in KPI metric cards (`st.metric`).

   * **Tab 2 — Search Tree & Step-by-Step Trace:** Displays the exact state-action transitions and $f(n) = g(n) + h(n)$ evaluations at each expanded node.

   * **Tab 3 — Combinatorial Scaling Lab Analysis:** Runs the 3-to-7 appliance benchmark live and displays the empirical state-space growth chart.

## 8. Automated Verification & Unit Test Suite (`tests/test_powerplan.py`)

Instruct Antigravity to create and run `pytest` on the following 6 core test cases before declaring the build complete:

| Test Function | What It Verifies | Expected Assertion | 
| ----- | ----- | ----- | 
| `test_outage_forces_idle_action` | Calling `get_valid_actions()` on Slot 2 (`is_outage=True`) | Strictly returns `[()]` (only the empty `IDLE` tuple) | 
| `test_capacity_constraint_filtering` | Calling `get_valid_actions()` on active slots with `capacity_limit=6` | Every returned action satisfies $\sum P_i \le 6$; combinations summing to $>6$ (e.g., `EV` 4u + `WM` 3u = 7u) are excluded | 
| `test_heuristic_admissibility` | Compares $h(s)$ against true optimal remaining cost $h^*(s)$ for all reachable states | $0 \le h(s) \le h^*(s)$ for every valid state, and $h(\text{goal}) == 0.0$ | 
| `test_bfs_finds_earliest_completion` | Runs `solve_bfs()` on the 6-slot benchmark | Completes all 4 jobs by **Slot 3** (`completion_slot == 3`), the earliest mathematically possible completion slot | 
| `test_astar_finds_global_minimum_cost` | Compares `solve_astar().total_cost` against an exhaustive brute-force minimum over all valid schedules | `astar_result.total_cost == 64.0` and equals the exact brute-force global minimum cost | 
| `test_dfs_low_memory_feasibility` | Runs `solve_dfs()` on the 6-slot benchmark | `dfs_result.success is True`, all 4 jobs reach `remaining == 0`, and `max_frontier_size < bfs_result.max_frontier_size` | 

## 9. Step-by-Step Execution Sequence for Antigravity

When Antigravity runs this plan, it should execute these exact 5 sequential milestones:

1. **Milestone 1 — Workspace Scaffolding & Dependencies:** Create the `powerplan/`, `tests/`, and `outputs/` directories, write `requirements.txt`, and verify Python environment packages (`matplotlib`, `numpy`, `pytest`, `streamlit`).

2. **Milestone 2 — Core OOP Engine (`models.py`, `environment.py`, `agent.py`, `scenarios.py`):** Implement all 5 required classes from the proposal (`ApplianceJob`, `PowerSlot`, `ScheduleState`, `SchedulingEnvironment`, `SchedulingAgent`) plus the three benchmark scenarios.

3. **Milestone 3 — Automated Verification (`tests/test_powerplan.py`):** Run `pytest -v` and confirm all 6 unit tests pass with 100% compliance on outage handling, capacity filtering, heuristic admissibility, and optimal cost/time separation.

4. **Milestone 4 — Visual Analytics & Report Generation (`visualizer.py`, `reporter.py`, `main.py`):** Execute `python main.py` to generate `outputs/schedule_heatmap.png`, `outputs/algorithm_metrics_comparison.png`, `outputs/combinatorial_scaling_analysis.png`, `outputs/benchmark_results.csv`, and `outputs/Lab6_Experimental_Report.md`.

5. **Milestone 5 — Interactive Demo & Notebook Packaging (`app.py`, `PowerPlan_Lab6_Complete.ipynb`):** Build the Streamlit dashboard and the self-contained Jupyter Notebook containing all theory, code cells, inline plots, and discussion answers ready for lab submission.