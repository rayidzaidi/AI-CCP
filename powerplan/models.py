"""PowerPlan Scheduler — Core Data Models.

Frozen dataclasses representing appliance jobs, power grid time slots,
immutable schedule states, and search result telemetry containers.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple


@dataclass(frozen=True)
class ApplianceJob:
    """Represents a household appliance task requiring power allocation.

    Attributes:
        job_id: Unique short identifier (e.g., 'WP', 'EV').
        name: Human-readable appliance name.
        power_units: Power drawn per active slot (kW or abstract units).
        duration_slots: Number of slots required to finish the job.
        priority: Optional tie-breaking priority (1 = highest).
    """

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
    """Represents a discrete chronological time block in the power grid schedule.

    Attributes:
        slot_index: 1-based chronological slot number (1..M).
        label: Human-readable slot description.
        is_outage: True if scheduled load-shedding / outage.
        capacity_limit: Maximum simultaneous power units allowed in this slot.
        unit_price: Tariff per energy unit in this slot ($ or PKR).
    """

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
    """Immutable state representation in the scheduling state space.

    Attributes:
        current_slot_index: 0-based index into the environment's slots list.
        remaining_durations: Tuple of remaining slot counts for each job
            (aligned with env.jobs).
        assignments: Tuple of tuples, where assignments[t] holds job_ids
            scheduled in slot t.
        g_cost: Cumulative energy cost incurred up to current_slot_index.
        completion_slot: 1-based slot number where the final appliance
            completed (0 if incomplete).
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
    """Encapsulates the solution schedule and telemetry metrics for a search run.

    Attributes:
        algorithm_name: Display name of the search algorithm.
        goal_Description: Short description of the optimization objective.
        success: Whether a valid goal state was found.
        final_state: The terminal ScheduleState (None if no solution).
        total_cost: Cumulative energy cost of the schedule.
        completion_slot: 1-based slot where the last job finished.
        nodes_expanded: Number of states popped from the frontier.
        nodes_generated: Number of successor states created.
        max_frontier_size: Peak memory usage of the frontier data structure.
        execution_time_ms: Wall-clock solve time in milliseconds.
        slot_assignments: 1-based slot_index -> list of job_ids scheduled.
        slot_loads: 1-based slot_index -> total power units used.
        slot_costs: 1-based slot_index -> cost incurred in that slot.
        search_trace: Optional list of step-by-step trace dictionaries.
    """

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
