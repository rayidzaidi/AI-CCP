"""PowerPlan Scheduler — CLI Driver and Benchmark Runner.

Executes:
1. Scenario 1: Proposal 6-Slot Benchmark (Water Pump, Washing Machine, Dishwasher, EV Charger).
   - Solves with BFS, DFS, and A*.
   - Displays formatted console summary.
   - Generates 'outputs/schedule_heatmap.png'.
   - Generates 'outputs/algorithm_metrics_comparison.png'.
   - Exports 'outputs/benchmark_results.csv'.
2. Scenario 2: Karachi K-Electric 8-Slot Multi-Duration Household Load Shifting.
   - Solves with BFS, DFS, and A*.
   - Displays formatted console summary.
3. Scenario 3: Combinatorial State-Space Scaling Benchmark (3 to 7 appliances).
   - Evaluates search tree pruning vs. combinatorial explosion.
   - Generates 'outputs/combinatorial_scaling_analysis.png'.
4. Auto-generates full 9-section academic Markdown report:
   - 'outputs/Lab6_Experimental_Report.md'.
"""
from __future__ import annotations

import sys
import time
from pathlib import Path
from typing import Dict, List

from powerplan.agent import SchedulingAgent
from powerplan.models import SearchResult
from powerplan.scenarios import (
    create_proposal_default_environment,
    create_karachi_kelectric_environment,
    create_scaling_environment,
)
from powerplan.visualizer import (
    render_schedule_heatmap,
    render_metrics_comparison,
    render_scaling_analysis,
)
from powerplan.reporter import (
    print_console_summary,
    export_benchmark_csv,
    generate_experimental_report_markdown,
)


def run_scenario_1() -> Dict[str, SearchResult]:
    """Executes Scenario 1: Proposal 6-Slot Default Benchmark."""
    print("\n" + "=" * 88)
    print(" >>> RUNNING SCENARIO 1: PROPOSAL 6-SLOT BENCHMARK")
    print("=" * 88)

    env = create_proposal_default_environment()
    agent = SchedulingAgent(env)

    results = agent.run_all_comparisons()
    print_console_summary(env, results)

    # Render visualizations
    heatmap_path = render_schedule_heatmap(
        env, results, output_path="outputs/schedule_heatmap.png"
    )
    print(f"\n[Artifact Created] Schedule Heatmap: {heatmap_path}")

    metrics_path = render_metrics_comparison(
        results, output_path="outputs/algorithm_metrics_comparison.png"
    )
    print(f"[Artifact Created] Algorithm Metrics Chart: {metrics_path}")

    # Export CSV benchmark
    csv_path = export_benchmark_csv(
        results, output_path="outputs/benchmark_results.csv"
    )
    print(f"[Artifact Created] Benchmark Results CSV: {csv_path}")

    return results


def run_scenario_2() -> Dict[str, SearchResult]:
    """Executes Scenario 2: Karachi K-Electric 8-Slot Multi-Duration Load Shifting."""
    print("\n" + "=" * 88)
    print(" >>> RUNNING SCENARIO 2: KARACHI K-ELECTRIC 8-SLOT MULTI-DURATION LOAD SHIFTING")
    print("=" * 88)

    env = create_karachi_kelectric_environment()
    agent = SchedulingAgent(env)

    results = agent.run_all_comparisons()
    print_console_summary(env, results)

    return results


def run_scenario_3() -> List[Dict[str, object]]:
    """Executes Scenario 3: Combinatorial Scaling Benchmark (3 to 7 Appliances)."""
    print("\n" + "=" * 88)
    print(" >>> RUNNING SCENARIO 3: COMBINATORIAL SCALING BENCHMARK (3 TO 7 APPLIANCES)")
    print("=" * 88)

    scaling_rows: List[Dict[str, object]] = []

    print(f"{'Appliances':<12} | {'BFS Nodes':>10} | {'DFS Nodes':>10} | {'A* Nodes':>10} | {'A* Pruning (%)':>15}")
    print("-" * 68)

    for n in range(3, 8):
        env = create_scaling_environment(n)
        agent = SchedulingAgent(env)
        results = agent.run_all_comparisons()

        bfs_exp = results["BFS"].nodes_expanded
        dfs_exp = results["DFS"].nodes_expanded
        astar_exp = results["A*"].nodes_expanded

        # Compute pruning efficiency of A* relative to BFS
        pruning_pct = round(max(0.0, (1.0 - astar_exp / max(bfs_exp, 1)) * 100.0), 1)

        row = {
            "num_appliances": n,
            "bfs_expanded": bfs_exp,
            "dfs_expanded": dfs_exp,
            "astar_expanded": astar_exp,
            "bfs_time": results["BFS"].execution_time_ms,
            "dfs_time": results["DFS"].execution_time_ms,
            "astar_time": results["A*"].execution_time_ms,
            "bfs_cost": results["BFS"].total_cost,
            "dfs_cost": results["DFS"].total_cost,
            "astar_cost": results["A*"].total_cost,
        }
        scaling_rows.append(row)

        print(
            f"{n:<12d} | {bfs_exp:>10d} | {dfs_exp:>10d} | {astar_exp:>10d} | {pruning_pct:>14.1f}%"
        )

    scaling_plot_path = render_scaling_analysis(
        scaling_rows, output_path="outputs/combinatorial_scaling_analysis.png"
    )
    print(f"\n[Artifact Created] Combinatorial Scaling Plot: {scaling_plot_path}")

    return scaling_rows


def main() -> int:
    """Master entry point for PowerPlan Scheduler."""
    start_time = time.perf_counter()

    Path("outputs").mkdir(parents=True, exist_ok=True)

    print("\n" + "#" * 88)
    print(" POWERPLAN SCHEDULER — LAB 6 OPEN-ENDED LAB CLI DRIVER")
    print(" Course: CSC-471-L Artificial Intelligence | Iqra University")
    print(" Student: Dua Rehan (67238) | Instructor: Aimen Zafar")
    print("#" * 88)

    # 1. Run Scenario 1 (Proposal Benchmark)
    scenario_1_env = create_proposal_default_environment()
    scenario_1_results = run_scenario_1()

    # 2. Run Scenario 2 (Karachi Load-Shedding Multi-Duration)
    run_scenario_2()

    # 3. Run Scenario 3 (Scaling Benchmark 3-7 Appliances)
    scaling_rows = run_scenario_3()

    # 4. Generate Comprehensive 9-Section Lab Report
    print("\n" + "=" * 88)
    print(" >>> GENERATING FULL 9-SECTION LAB 6 EXPERIMENTAL REPORT")
    print("=" * 88)
    report_path = generate_experimental_report_markdown(
        scenario_1_env,
        scenario_1_results,
        scaling_rows,
        output_path="outputs/Lab6_Experimental_Report.md",
    )
    print(f"[Artifact Created] Lab Report Markdown: {report_path}")

    total_duration = round(time.perf_counter() - start_time, 2)
    print("\n" + "#" * 88)
    print(f" ALL TASKS COMPLETED SUCCESSFULLY IN {total_duration}s")
    print(" All charts, CSVs, and markdown reports generated under 'outputs/' directory.")
    print("#" * 88 + "\n")

    return 0


if __name__ == "__main__":
    sys.exit(main())
