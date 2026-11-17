"""PowerPlan Scheduler Package.

An intelligent outage-aware household appliance scheduling system modeled
as a deterministic state-space search problem in Python using Object-Oriented
Programming (OOP).
"""

from powerplan.models import (
    ApplianceJob,
    PowerSlot,
    ScheduleState,
    SearchResult,
)
from powerplan.environment import SchedulingEnvironment
from powerplan.agent import SchedulingAgent
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

__all__ = [
    "ApplianceJob",
    "PowerSlot",
    "ScheduleState",
    "SearchResult",
    "SchedulingEnvironment",
    "SchedulingAgent",
    "create_proposal_default_environment",
    "create_karachi_kelectric_environment",
    "create_scaling_environment",
    "render_schedule_heatmap",
    "render_metrics_comparison",
    "render_scaling_analysis",
    "print_console_summary",
    "export_benchmark_csv",
    "generate_experimental_report_markdown",
]
