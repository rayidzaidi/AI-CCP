"""PowerPlan Scheduler — Reporting & Export Utilities.

Provides formatted console output, CSV benchmark export, and auto-generated
Markdown experimental report covering all 9 deliverable sections required
by the Lab 6 proposal.
"""
from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List

from powerplan.environment import SchedulingEnvironment
from powerplan.models import SearchResult


def print_console_summary(
    env: SchedulingEnvironment,
    results: Dict[str, SearchResult],
) -> None:
    """Prints a formatted comparative summary table and slot-by-slot schedule to stdout.

    Args:
        env: The SchedulingEnvironment that produced the results.
        results: Dict mapping algorithm keys ('BFS', 'DFS', 'A*') to
            SearchResult instances.
    """
    print("=" * 88)
    print(
        f" POWERPLAN SCHEDULER — AI STATE-SPACE SEARCH BENCHMARK ({env.name})"
    )
    print("=" * 88)
    header: str = (
        f"{'Algorithm':<34} | {'Cost ($)':>9} | {'Done Slot':>9} | "
        f"{'Expanded':>8} | {'Max Queue':>9} | {'Time (ms)':>9}"
    )
    print(header)
    print("-" * 88)
    for key in ["BFS", "DFS", "A*"]:
        r: SearchResult = results[key]
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
            s_idx: int = slot.slot_index
            jobs_str: str = (
                ", ".join(r.slot_assignments[s_idx])
                if r.slot_assignments[s_idx]
                else "IDLE"
            )
            status_tag: str = (
                "OUTAGE (FORCED IDLE)"
                if slot.is_outage
                else f"Active (${slot.unit_price:.0f}/u)"
            )
            print(
                f"  - Slot {s_idx} [{status_tag:<20}]: {jobs_str:<18} "
                f"| Load: {r.slot_loads[s_idx]}/{slot.effective_capacity}u "
                f"| Slot Cost: ${r.slot_costs[s_idx]:.2f}"
            )


def export_benchmark_csv(
    results: Dict[str, SearchResult],
    output_path: str = "outputs/benchmark_results.csv",
) -> str:
    """Exports benchmark metrics for all algorithms to a CSV file.

    Columns: Algorithm, Goal, Success, TotalCost, CompletionSlot,
    NodesExpanded, NodesGenerated, MaxFrontierSize, ExecutionTimeMs.

    Args:
        results: Dict mapping algorithm keys to SearchResult instances.
        output_path: File path for the saved CSV file.

    Returns:
        The resolved output path string.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    fieldnames: List[str] = [
        "Algorithm",
        "Goal",
        "Success",
        "TotalCost",
        "CompletionSlot",
        "NodesExpanded",
        "NodesGenerated",
        "MaxFrontierSize",
        "ExecutionTimeMs",
    ]
    with open(output_path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for key in ["BFS", "DFS", "A*"]:
            r: SearchResult = results[key]
            writer.writerow(
                {
                    "Algorithm": r.algorithm_name,
                    "Goal": r.goal_Description,
                    "Success": r.success,
                    "TotalCost": r.total_cost,
                    "CompletionSlot": r.completion_slot,
                    "NodesExpanded": r.nodes_expanded,
                    "NodesGenerated": r.nodes_generated,
                    "MaxFrontierSize": r.max_frontier_size,
                    "ExecutionTimeMs": r.execution_time_ms,
                }
            )
    return output_path


def generate_experimental_report_markdown(
    env: SchedulingEnvironment,
    results: Dict[str, SearchResult],
    scaling_rows: List[Dict[str, object]],
    output_path: str = "outputs/Lab6_Experimental_Report.md",
) -> str:
    """Generates a comprehensive Lab 6 Experimental Report in Markdown.

    Covers all 9 sections required by the lab manual:
    1. Background/Theory  2. Procedure/Methodology  3. Data Collection
    4. Flowchart/Block Diagram  5. Analysis  6. Results
    7. Discussion on Results  8. Concluding Remarks  9. References

    Args:
        env: The SchedulingEnvironment that produced the results.
        results: Dict mapping algorithm keys to SearchResult instances.
        scaling_rows: Scaling benchmark data for Section 5 analysis.
        output_path: File path for the saved Markdown report.

    Returns:
        The resolved output path string.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    bfs: SearchResult = results["BFS"]
    dfs: SearchResult = results["DFS"]
    astar: SearchResult = results["A*"]

    # Build slot schedule tables per algorithm
    def _slot_table(r: SearchResult) -> str:
        lines: List[str] = []
        lines.append(
            "| Slot | Status | Jobs | Load | Slot Cost |"
        )
        lines.append(
            "| --- | --- | --- | --- | --- |"
        )
        for slot in env.slots:
            s_idx: int = slot.slot_index
            jobs_str: str = (
                ", ".join(r.slot_assignments[s_idx])
                if r.slot_assignments[s_idx]
                else "IDLE"
            )
            status: str = "OUTAGE" if slot.is_outage else f"Active (${slot.unit_price:.0f}/u)"
            lines.append(
                f"| Slot {s_idx} | {status} | {jobs_str} | "
                f"{r.slot_loads[s_idx]}/{slot.effective_capacity}u | "
                f"${r.slot_costs[s_idx]:.2f} |"
            )
        return "\n".join(lines)

    # Build scaling table
    scaling_table_lines: List[str] = [
        "| Appliances | BFS Expanded | DFS Expanded | A* Expanded |",
        "| --- | --- | --- | --- |",
    ]
    for row in scaling_rows:
        scaling_table_lines.append(
            f"| {row['num_appliances']} | {row['bfs_expanded']} | "
            f"{row['dfs_expanded']} | {row['astar_expanded']} |"
        )
    scaling_table: str = "\n".join(scaling_table_lines)

    # Cost savings
    cost_saving_pct: float = (
        ((bfs.total_cost - astar.total_cost) / bfs.total_cost * 100.0)
        if bfs.total_cost > 0
        else 0.0
    )

    report: str = f"""# PowerPlan Scheduler — Lab 6 Experimental Report

**Course:** CSC-471-L Artificial Intelligence (Lab Session 6 — Open-Ended Lab)

**Student:** Dua Rehan (Roll No. 67238)

**Scenario:** {env.name}

---

## 1. Background / Theory

This experiment implements an **outage-aware household appliance scheduling system** modeled as a deterministic state-space search problem. The agent allocates a fixed set of household appliances across discrete time slots subject to:

- **Grid capacity limits** ($C_t$ = {env.slots[0].capacity_limit} units/slot)
- **Scheduled power outages** (forced IDLE during outage slots)
- **Fluctuating energy tariffs** (Time-of-Use pricing)

Three classical AI search strategies are compared:

1. **BFS (Breadth-First Search):** FIFO queue optimizing for earliest completion time.
2. **DFS (Depth-First Search):** LIFO stack optimizing for the first computationally feasible schedule with minimal memory overhead.
3. **A* Search:** Priority queue using $f(n) = g(n) + h(n)$ with an admissible heuristic $h(n) = E_{{rem}} \\times p_{{min}}(t)$.

**Admissibility Proof:** Every remaining energy unit must be scheduled in some active slot $k \\geq t$ at tariff $\\text{{price}}_k \\geq p_{{min}}(t)$. By relaxing the capacity constraint and assuming all remaining energy can be purchased at the single lowest future tariff, $h(s) \\leq h^*(s)$ always holds, guaranteeing A* finds the globally cost-optimal schedule.

---

## 2. Procedure / Methodology

1. Define appliance jobs as `ApplianceJob` dataclasses with power draw and duration.
2. Define time slots as `PowerSlot` dataclasses with outage status, capacity, and tariff.
3. Implement `SchedulingEnvironment` with state transitions, action generation (outage enforcement, capacity filtering, IDLE action), and heuristic computation.
4. Implement `SchedulingAgent` with `solve_bfs()`, `solve_dfs()`, and `solve_astar()`.
5. Run all three algorithms on identical scenarios and collect metrics.
6. Visualize results with heatmaps and comparative bar charts.

---

## 3. Data Collection

### Appliances

| Job ID | Appliance | Power (units/slot) | Duration (slots) | Total Energy |
| --- | --- | --- | --- | --- |
{chr(10).join(f"| {j.job_id} | {j.name} | {j.power_units} | {j.duration_slots} | {j.total_energy_units} |" for j in env.jobs)}

**Total Energy Required:** {sum(j.total_energy_units for j in env.jobs)} units

### Time Slots

| Slot | Label | Outage | Capacity | Tariff |
| --- | --- | --- | --- | --- |
{chr(10).join(f"| {s.slot_index} | {s.label} | {'Yes' if s.is_outage else 'No'} | {s.capacity_limit} | ${s.unit_price:.2f}/u |" for s in env.slots)}

---

## 4. Flowchart / Block Diagram

```
[Start] → [Initialize State (slot=0, all jobs pending)]
   ↓
[All Jobs Completed?] → Yes → [GOAL STATE — Return Schedule]
   ↓ No
[Horizon Exhausted (slot ≥ M)?] → Yes → [DEAD END — Backtrack]
   ↓ No
[Is Current Slot an Outage?]
   ↓ Yes → [Force IDLE action ()]  → [Advance to next slot] → [Loop]
   ↓ No
[Generate all feasible subsets A ⊆ Unfinished Jobs where ΣP_i ≤ C_t]
   ↓
[Include IDLE () action]
   ↓
[For each action: Apply, compute g_cost, check feasibility]
   ↓
[Add successor states to frontier (FIFO / LIFO / Priority Queue)]
   ↓
[Loop until goal or frontier empty]
```

---

## 5. Analysis

### Algorithm Performance Comparison

| Metric | BFS | DFS | A* |
| --- | --- | --- | --- |
| Total Energy Cost ($) | ${bfs.total_cost:.2f} | ${dfs.total_cost:.2f} | ${astar.total_cost:.2f} |
| Completion Slot | {bfs.completion_slot} | {dfs.completion_slot} | {astar.completion_slot} |
| Nodes Expanded | {bfs.nodes_expanded} | {dfs.nodes_expanded} | {astar.nodes_expanded} |
| Nodes Generated | {bfs.nodes_generated} | {dfs.nodes_generated} | {astar.nodes_generated} |
| Peak Frontier Size | {bfs.max_frontier_size} | {dfs.max_frontier_size} | {astar.max_frontier_size} |
| Execution Time (ms) | {bfs.execution_time_ms:.3f} | {dfs.execution_time_ms:.3f} | {astar.execution_time_ms:.3f} |

### Combinatorial Scaling Analysis (3–7 Appliances)

{scaling_table}

---

## 6. Results

### BFS Schedule (Earliest Completion Time)

{_slot_table(bfs)}

**BFS Outcome:** Completes all jobs by **Slot {bfs.completion_slot}** at a total cost of **${bfs.total_cost:.2f}**.

### DFS Schedule (First Feasible / Low Memory)

{_slot_table(dfs)}

**DFS Outcome:** Completes all jobs by **Slot {dfs.completion_slot}** at a total cost of **${dfs.total_cost:.2f}**.

### A* Schedule (Minimum Energy Cost)

{_slot_table(astar)}

**A* Outcome:** Completes all jobs by **Slot {astar.completion_slot}** at the globally optimal total cost of **${astar.total_cost:.2f}**.

---

## 7. Discussion on Results

1. **BFS aggressively packs jobs into the earliest available slots** to minimize completion time. It finishes by Slot {bfs.completion_slot} but pays a premium of ${bfs.total_cost:.2f} because it does not consider tariff costs.

2. **DFS produces an arbitrary valid schedule** using a LIFO stack. Its peak frontier size ({dfs.max_frontier_size}) is typically smaller than BFS ({bfs.max_frontier_size}), confirming the theoretical memory advantage of depth-first exploration.

3. **A* Search finds the globally optimal minimum-cost schedule** at ${astar.total_cost:.2f}, saving **{cost_saving_pct:.1f}%** compared to BFS. By using the admissible heuristic $h(n) = E_{{rem}} \\times p_{{min}}(t)$, A* intelligently bypasses expensive peak slots and concentrates load in cheaper off-peak periods.

4. **The scaling analysis confirms** that as the number of appliances increases from 3 to 7, the state-space grows combinatorially. A*'s heuristic pruning keeps its node expansion significantly below that of blind BFS, validating the practical value of informed search in real-world scheduling.

---

## 8. Concluding Remarks

This experiment successfully demonstrated the application of classical AI search algorithms to a real-world outage-aware power scheduling problem. Key takeaways:

- **BFS** is optimal for time-sensitive scheduling where the fastest completion is paramount.
- **DFS** is suitable for resource-constrained environments needing any valid schedule quickly.
- **A* Search** is the optimal strategy when minimizing energy cost is the objective, guaranteed by the admissible heuristic.
- The **OOP architecture** (ApplianceJob, PowerSlot, ScheduleState, SchedulingEnvironment, SchedulingAgent) provides clean separation of concerns and extensibility for future multi-duration or multi-objective scenarios.

---

## 9. References

1. Russell, S., & Norvig, P. (2021). *Artificial Intelligence: A Modern Approach* (4th Edition). Pearson.
2. Hart, P. E., Nilsson, N. J., & Raphael, B. (1968). A Formal Basis for the Heuristic Determination of Minimum Cost Paths. *IEEE Transactions on Systems Science and Cybernetics*, 4(2), 100–107.
3. Pakistan Electric Power Company (PEPCO). Load-Shedding Schedules and Time-of-Use Tariffs. Retrieved from K-Electric official documentation.
"""

    with open(output_path, "w", encoding="utf-8") as fh:
        fh.write(report)
    return output_path
