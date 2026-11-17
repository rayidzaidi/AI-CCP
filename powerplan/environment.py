"""PowerPlan Scheduler — State-Action Transition Environment.

Deterministic, fully observable environment that models outage enforcement,
grid capacity filtering, cost accumulation, and admissible heuristic bounds
for the household appliance scheduling problem.
"""
from __future__ import annotations

from itertools import combinations
from typing import Dict, List, Tuple

from powerplan.models import ApplianceJob, PowerSlot, ScheduleState


class SchedulingEnvironment:
    """Deterministic, fully observable state-action transition environment for PowerPlan.

    Models outage enforcement, grid capacity filtering, cost accumulation,
    and heuristic bounds.

    Attributes:
        name: Human-readable scenario name.
        jobs: Tuple of ApplianceJob instances.
        slots: Tuple of PowerSlot instances.
        job_map: Mapping from job_id to ApplianceJob.
        job_index_map: Mapping from job_id to positional index in ``jobs``.
    """

    def __init__(
        self,
        jobs: List[ApplianceJob],
        slots: List[PowerSlot],
        name: str = "Default",
    ) -> None:
        if not jobs:
            raise ValueError("SchedulingEnvironment requires at least one ApplianceJob.")
        if not slots:
            raise ValueError("SchedulingEnvironment requires at least one PowerSlot.")
        self.name: str = name
        self.jobs: Tuple[ApplianceJob, ...] = tuple(jobs)
        self.slots: Tuple[PowerSlot, ...] = tuple(slots)
        self.job_map: Dict[str, ApplianceJob] = {job.job_id: job for job in self.jobs}
        self.job_index_map: Dict[str, int] = {
            job.job_id: idx for idx, job in enumerate(self.jobs)
        }

    # ------------------------------------------------------------------
    # State construction
    # ------------------------------------------------------------------

    def get_initial_state(self) -> ScheduleState:
        """Constructs the root ScheduleState at slot index 0 with full job durations."""
        initial_remaining: Tuple[int, ...] = tuple(
            job.duration_slots for job in self.jobs
        )
        return ScheduleState(
            current_slot_index=0,
            remaining_durations=initial_remaining,
            assignments=tuple(),
            g_cost=0.0,
            completion_slot=0,
        )

    # ------------------------------------------------------------------
    # Goal & feasibility tests
    # ------------------------------------------------------------------

    def is_goal_state(self, state: ScheduleState) -> bool:
        """Goal test: returns True as soon as all jobs have 0 remaining duration."""
        return state.is_all_completed()

    def get_remaining_energy(self, state: ScheduleState) -> int:
        """Calculates total remaining energy units required across all unfinished jobs.

        Formula: E_rem(s) = sum_i ( r_i * P_i )
        """
        return sum(
            rem * self.jobs[idx].power_units
            for idx, rem in enumerate(state.remaining_durations)
        )

    def is_remaining_feasible(self, state: ScheduleState) -> bool:
        """Lookahead feasibility check.

        Verifies whether remaining active slots have enough aggregate capacity
        and active slot count to finish all remaining work.

        Returns:
            True if the remaining work can still be completed before the
            horizon ends; False otherwise.
        """
        if state.is_all_completed():
            return True
        if state.current_slot_index >= len(self.slots):
            return False

        remaining_slots = self.slots[state.current_slot_index:]
        active_slots = [s for s in remaining_slots if not s.is_outage]

        # Any single job needing more active slots than available?
        max_needed_slots: int = max(state.remaining_durations)
        if max_needed_slots > len(active_slots):
            return False

        # Aggregate capacity check
        total_remaining_capacity: int = sum(
            s.effective_capacity for s in active_slots
        )
        if self.get_remaining_energy(state) > total_remaining_capacity:
            return False

        return True

    # ------------------------------------------------------------------
    # Action generation  (matches proposal flowchart exactly)
    # ------------------------------------------------------------------

    def get_valid_actions(self, state: ScheduleState) -> List[Tuple[str, ...]]:
        """Generates all valid appliance combinations for the current slot.

        Rules (exact match to proposal flowchart):
        - If all jobs are already completed or horizon is reached, returns [].
        - If current slot is an OUTAGE, forces IDLE: returns [()].
        - Otherwise, generates all subsets of unfinished jobs whose combined
          power_units do not exceed slot.capacity_limit, including () (IDLE).
        """
        if state.is_all_completed() or state.current_slot_index >= len(self.slots):
            return []

        current_slot: PowerSlot = self.slots[state.current_slot_index]

        # Flowchart Rule: Is Current Slot an Outage? -> Yes -> Action: Force IDLE
        if current_slot.is_outage:
            return [tuple()]

        # Identify unfinished job indices
        unfinished_indices: List[int] = [
            idx for idx, rem in enumerate(state.remaining_durations) if rem > 0
        ]

        valid_actions: List[Tuple[str, ...]] = [tuple()]  # Always include IDLE action ()
        capacity: int = current_slot.capacity_limit

        for r in range(1, len(unfinished_indices) + 1):
            for combo_indices in combinations(unfinished_indices, r):
                combo_power: int = sum(
                    self.jobs[i].power_units for i in combo_indices
                )
                if combo_power <= capacity:
                    action: Tuple[str, ...] = tuple(
                        self.jobs[i].job_id for i in combo_indices
                    )
                    valid_actions.append(action)

        return valid_actions

    # ------------------------------------------------------------------
    # State transition
    # ------------------------------------------------------------------

    def apply_action(
        self, state: ScheduleState, action: Tuple[str, ...]
    ) -> ScheduleState:
        """Applies a valid action (tuple of job_ids) in the current slot.

        Returns the successor ScheduleState with updated remaining durations,
        accumulated cost, and assignment record.

        Raises:
            ValueError: If the action violates outage or capacity constraints.
        """
        slot: PowerSlot = self.slots[state.current_slot_index]

        if slot.is_outage and len(action) > 0:
            raise ValueError(
                f"Cannot schedule jobs {action} during outage slot {slot.slot_index}."
            )

        action_power: int = sum(self.job_map[jid].power_units for jid in action)
        if action_power > slot.effective_capacity:
            raise ValueError(
                f"Action {action} power ({action_power}u) exceeds slot "
                f"{slot.slot_index} capacity ({slot.effective_capacity}u)."
            )

        new_remaining: List[int] = list(state.remaining_durations)
        for jid in action:
            idx: int = self.job_index_map[jid]
            if new_remaining[idx] <= 0:
                raise ValueError(f"Job {jid} is already completed.")
            new_remaining[idx] -= 1

        step_cost: float = action_power * slot.unit_price
        next_slot_number: int = slot.slot_index  # 1-based slot number
        new_completion_slot: int = (
            next_slot_number if len(action) > 0 else state.completion_slot
        )

        return ScheduleState(
            current_slot_index=state.current_slot_index + 1,
            remaining_durations=tuple(new_remaining),
            assignments=state.assignments + (action,),
            g_cost=round(state.g_cost + step_cost, 6),
            completion_slot=new_completion_slot,
        )

    # ------------------------------------------------------------------
    # A* admissible heuristic
    # ------------------------------------------------------------------

    def calculate_heuristic(self, state: ScheduleState) -> float:
        """Admissible A* heuristic: h(n) = E_rem(s) × p_min(t).

        Where:
            E_rem(s) = sum of (remaining_duration_i * power_units_i) for all jobs
            p_min(t) = min unit_price among all future active (non-outage) slots

        Returns float('inf') if remaining jobs cannot possibly be completed
        in future slots (capacity or horizon infeasibility).

        Proof of Admissibility:
            Every remaining energy unit must be scheduled in some active slot
            k >= t at tariff price_k >= p_min(t). By relaxing the capacity
            constraint and assuming all remaining energy can be bought at the
            single lowest future tariff p_min(t), h(s) <= h*(s) always holds.
        """
        if state.is_all_completed():
            return 0.0

        if not self.is_remaining_feasible(state):
            return float("inf")

        future_active_prices: List[float] = [
            s.unit_price
            for s in self.slots[state.current_slot_index:]
            if not s.is_outage
        ]
        if not future_active_prices:
            return float("inf")

        min_future_price: float = min(future_active_prices)
        remaining_energy: int = self.get_remaining_energy(state)
        return round(remaining_energy * min_future_price, 6)
