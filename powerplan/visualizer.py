"""PowerPlan Scheduler — Publication-Quality Visual Analytics.

Renders Matplotlib/Seaborn charts for schedule heatmaps, algorithm metrics
comparison, and combinatorial scaling analysis.  All outputs are saved at
300 DPI for publication / lab report inclusion.
"""
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
    """Renders a 3-panel side-by-side Schedule Heatmap comparing BFS, DFS, and A*.

    Shows job allocations across time slots, highlighting scheduled outages,
    slot tariffs, and power unit consumption.  Each cell is annotated with
    ON (Xu) or OUTAGE (IDLE).  A bottom strip shows load / capacity.

    Args:
        env: The SchedulingEnvironment that produced the results.
        results: Dict mapping algorithm keys ('BFS', 'DFS', 'A*') to
            SearchResult instances.
        output_path: File path for the saved PNG image.

    Returns:
        The resolved output path string.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    algo_keys: List[str] = ["BFS", "DFS", "A*"]
    num_jobs: int = len(env.jobs)
    num_slots: int = len(env.slots)

    fig, axes = plt.subplots(1, 3, figsize=(18, 6.2), sharey=True)
    fig.suptitle(
        f"PowerPlan Schedule Heatmap Comparison — {env.name}\n"
        "(Cell Value = Power Units Allocated | Red Column = Outage Slot)",
        fontsize=14,
        fontweight="bold",
        y=0.98,
    )

    job_labels: List[str] = [
        f"{j.name}\n({j.job_id}: {j.power_units}u)" for j in env.jobs
    ]
    slot_labels: List[str] = [
        f"S{s.slot_index}\n{'OUTAGE' if s.is_outage else f'${s.unit_price:.0f}/u'}"
        for s in env.slots
    ]

    for ax_idx, algo_key in enumerate(algo_keys):
        ax = axes[ax_idx]
        res: SearchResult = results[algo_key]
        matrix = np.zeros((num_jobs, num_slots), dtype=float)

        for j_idx, job in enumerate(env.jobs):
            for s_idx, slot in enumerate(env.slots):
                if slot.is_outage:
                    matrix[j_idx, s_idx] = -1.0  # Sentinel for outage shading
                elif job.job_id in res.slot_assignments.get(slot.slot_index, []):
                    matrix[j_idx, s_idx] = float(job.power_units)

        # Custom colour mapping:
        #   -1 = Outage (soft coral)
        #    0 = Idle (light slate)
        #   >0 = Active (teal/navy gradient)
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
                    ax.text(
                        c, r, "OUTAGE\n(IDLE)",
                        ha="center", va="center", fontsize=8.5,
                        color="#8B1E1E", fontweight="bold",
                    )
                elif val == 0:
                    ax.text(
                        c, r, "—",
                        ha="center", va="center", fontsize=11,
                        color="#7A869A",
                    )
                else:
                    ax.text(
                        c, r, f"ON\n({int(val)}u)",
                        ha="center", va="center", fontsize=9.5,
                        color="white", fontweight="bold",
                    )

        # Axis labels
        ax.set_xticks(np.arange(num_slots))
        ax.set_xticklabels(slot_labels, fontsize=9.5, fontweight="bold")
        ax.set_yticks(np.arange(num_jobs))
        if ax_idx == 0:
            ax.set_yticklabels(job_labels, fontsize=10, fontweight="bold")

        # Bottom summary strip per slot: Load / Capacity
        for s_idx, slot in enumerate(env.slots):
            load: int = res.slot_loads.get(slot.slot_index, 0)
            cap: int = slot.effective_capacity
            ax.text(
                s_idx,
                num_jobs - 0.52,
                f"Load: {load}/{cap}u",
                ha="center",
                va="bottom",
                fontsize=8,
                color="#1E293B" if not slot.is_outage else "#8B1E1E",
                bbox=dict(
                    boxstyle="round,pad=0.18",
                    facecolor="white",
                    alpha=0.85,
                    edgecolor="none",
                ),
            )

        ax.set_title(
            f"{algo_key}: {res.goal_Description}\n"
            f"Total Cost: ${res.total_cost:.2f} | Completed: Slot "
            f"{res.completion_slot} | Expanded: {res.nodes_expanded} nodes",
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
    """Renders a 4-panel bar chart comparing search strategy performance.

    Panels: Total Energy Cost ($), Completion Time (Slot #), Nodes Expanded,
    and Peak Frontier Size across BFS, DFS, and A*.

    Args:
        results: Dict mapping algorithm keys to SearchResult instances.
        output_path: File path for the saved PNG image.

    Returns:
        The resolved output path string.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)
    algos: List[str] = ["BFS", "DFS", "A*"]
    colors: List[str] = ["#2563EB", "#D97706", "#059669"]

    metrics: List[tuple[str, List[float], str]] = [
        (
            "Total Energy Cost ($)",
            [results[k].total_cost for k in algos],
            "${:.1f}",
        ),
        (
            "Completion Time (Slot #)",
            [float(results[k].completion_slot) for k in algos],
            "Slot {:.0f}",
        ),
        (
            "Nodes Expanded (Count)",
            [float(results[k].nodes_expanded) for k in algos],
            "{:.0f}",
        ),
        (
            "Peak Frontier Size (Nodes)",
            [float(results[k].max_frontier_size) for k in algos],
            "{:.0f}",
        ),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(16, 4.5))
    fig.suptitle(
        "PowerPlan Search Strategy Performance Trade-Offs",
        fontsize=14,
        fontweight="bold",
        y=1.02,
    )

    for idx, (title, values, fmt) in enumerate(metrics):
        ax = axes[idx]
        bars = ax.bar(
            algos, values, color=colors,
            width=0.55, edgecolor="#1E293B", linewidth=1.0,
        )
        ax.set_title(title, fontsize=11, fontweight="bold")
        ax.grid(axis="y", linestyle="--", alpha=0.4)
        max_val: float = max(values) if max(values) > 0 else 1.0
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
    """Plots Nodes Expanded vs. Number of Appliances (3–7).

    Illustrates state-space branching explosion and heuristic pruning
    efficiency as the number of household appliances increases.

    Args:
        scaling_rows: List of dicts with keys 'num_appliances',
            'bfs_expanded', 'dfs_expanded', 'astar_expanded'.
        output_path: File path for the saved PNG image.

    Returns:
        The resolved output path string.
    """
    Path(output_path).parent.mkdir(parents=True, exist_ok=True)

    counts: List[int] = [int(r["num_appliances"]) for r in scaling_rows]
    bfs_nodes: List[int] = [int(r["bfs_expanded"]) for r in scaling_rows]
    dfs_nodes: List[int] = [int(r["dfs_expanded"]) for r in scaling_rows]
    astar_nodes: List[int] = [int(r["astar_expanded"]) for r in scaling_rows]

    fig, ax = plt.subplots(figsize=(9, 5))
    ax.plot(
        counts, bfs_nodes,
        marker="o", linewidth=2.4, color="#2563EB",
        label="BFS (Uninformed FIFO)",
    )
    ax.plot(
        counts, dfs_nodes,
        marker="s", linewidth=2.4, color="#D97706",
        label="DFS (Uninformed LIFO)",
    )
    ax.plot(
        counts, astar_nodes,
        marker="^", linewidth=2.4, color="#059669",
        label="A* Search (Admissible Heuristic)",
    )

    ax.set_title(
        "Combinatorial Explosion & Heuristic Tree Pruning (3 to 7 Appliances)",
        fontsize=13,
        fontweight="bold",
    )
    ax.set_xlabel(
        "Number of Household Appliances Scheduled",
        fontsize=11, fontweight="bold",
    )
    ax.set_ylabel(
        "Nodes Expanded Before Goal",
        fontsize=11, fontweight="bold",
    )
    ax.set_xticks(counts)
    ax.grid(True, linestyle="--", alpha=0.45)
    ax.legend(fontsize=10.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close(fig)
    return output_path
