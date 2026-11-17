"""PowerPlan Scheduler — Predefined Benchmark Scenarios.

Provides three scenario constructors covering the exact bounded lab proposal,
a Karachi K-Electric multi-duration extension, and a combinatorial scaling
generator for empirical state-space analysis.
"""
from __future__ import annotations

from typing import List

from powerplan.environment import SchedulingEnvironment
from powerplan.models import ApplianceJob, PowerSlot


def create_proposal_default_environment() -> SchedulingEnvironment:
    """Scenario 1: Exact 4-Appliance, 6-Slot Bounded Simulation from the Lab 6 Proposal.

    Grid capacity = 6 units per active slot.
    Slot 2 is a scheduled outage ($0). Tariffs fluctuate between $4 and $20.

    Expected behavioural contrast:
        - BFS completes by Slot 3 at $135  (earliest completion time).
        - A* completes by Slot 6 at $64    (minimum total energy cost).
        - DFS produces an arbitrary feasible spread with low memory usage.
    """
    jobs: List[ApplianceJob] = [
        ApplianceJob(
            job_id="WP", name="Water Pump", power_units=2,
            duration_slots=1, priority=1,
        ),
        ApplianceJob(
            job_id="WM", name="Washing Machine", power_units=3,
            duration_slots=1, priority=2,
        ),
        ApplianceJob(
            job_id="DW", name="Dishwasher", power_units=2,
            duration_slots=1, priority=3,
        ),
        ApplianceJob(
            job_id="EV", name="EV Charger", power_units=4,
            duration_slots=1, priority=1,
        ),
    ]
    slots: List[PowerSlot] = [
        PowerSlot(
            slot_index=1, label="Slot 1 (Morning)", is_outage=False,
            capacity_limit=6, unit_price=10.0,
        ),
        PowerSlot(
            slot_index=2, label="Slot 2 (Outage)", is_outage=True,
            capacity_limit=6, unit_price=0.0,
        ),
        PowerSlot(
            slot_index=3, label="Slot 3 (Peak)", is_outage=False,
            capacity_limit=6, unit_price=15.0,
        ),
        PowerSlot(
            slot_index=4, label="Slot 4 (Shoulder)", is_outage=False,
            capacity_limit=6, unit_price=8.0,
        ),
        PowerSlot(
            slot_index=5, label="Slot 5 (Super Peak)", is_outage=False,
            capacity_limit=6, unit_price=20.0,
        ),
        PowerSlot(
            slot_index=6, label="Slot 6 (Off-Peak)", is_outage=False,
            capacity_limit=6, unit_price=4.0,
        ),
    ]
    return SchedulingEnvironment(
        jobs=jobs, slots=slots, name="Proposal_6Slot_Benchmark"
    )


def create_karachi_kelectric_environment() -> SchedulingEnvironment:
    """Scenario 2: Multi-Duration Household Load Shifting under Local Load-Shedding (8 Slots).

    Demonstrates appliances that require multiple slots of execution
    (e.g., EV Charger 2 slots, Dishwasher 2 slots) under Karachi
    K-Electric Time-of-Use tariffs with two scheduled outage windows.
    """
    jobs: List[ApplianceJob] = [
        ApplianceJob(job_id="WP", name="Water Pump", power_units=2, duration_slots=1),
        ApplianceJob(job_id="WM", name="Washing Machine", power_units=3, duration_slots=1),
        ApplianceJob(job_id="DW", name="Dishwasher", power_units=2, duration_slots=2),
        ApplianceJob(job_id="EV", name="EV Charger", power_units=4, duration_slots=2),
    ]
    slots: List[PowerSlot] = [
        PowerSlot(slot_index=1, label="08:00-10:00", is_outage=False, capacity_limit=6, unit_price=12.0),
        PowerSlot(slot_index=2, label="10:00-12:00 (Outage)", is_outage=True, capacity_limit=6, unit_price=0.0),
        PowerSlot(slot_index=3, label="12:00-14:00", is_outage=False, capacity_limit=6, unit_price=14.0),
        PowerSlot(slot_index=4, label="14:00-16:00", is_outage=False, capacity_limit=6, unit_price=9.0),
        PowerSlot(slot_index=5, label="16:00-18:00 (Outage)", is_outage=True, capacity_limit=6, unit_price=0.0),
        PowerSlot(slot_index=6, label="18:00-20:00 (Peak)", is_outage=False, capacity_limit=6, unit_price=22.0),
        PowerSlot(slot_index=7, label="20:00-22:00 (Peak)", is_outage=False, capacity_limit=6, unit_price=18.0),
        PowerSlot(slot_index=8, label="22:00-00:00 (Off-Peak)", is_outage=False, capacity_limit=6, unit_price=5.0),
    ]
    return SchedulingEnvironment(
        jobs=jobs, slots=slots, name="Karachi_MultiSlot_ToU"
    )


def create_scaling_environment(num_appliances: int) -> SchedulingEnvironment:
    """Scenario 3: Combinatorial State-Space Scaling Generator (Deliverable 5).

    Creates ``num_appliances`` single-slot jobs (3 to 7) across 6 slots with
    capacity 7 to benchmark node expansion growth for BFS, DFS, and A*.

    Args:
        num_appliances: Number of appliances to include (selects from a
            fixed catalog of 7 appliances with varied power draws).
    """
    catalog: List[tuple[str, str, int]] = [
        ("WP", "Water Pump", 2),
        ("WM", "Washing Machine", 3),
        ("DW", "Dishwasher", 2),
        ("EV", "EV Charger", 4),
        ("IH", "Induction Heater", 2),
        ("DR", "Clothes Dryer", 3),
        ("PP", "Pool Filtration Pump", 2),
    ]
    selected = catalog[:num_appliances]
    jobs: List[ApplianceJob] = [
        ApplianceJob(
            job_id=jid, name=name, power_units=pwr, duration_slots=1
        )
        for jid, name, pwr in selected
    ]
    slots: List[PowerSlot] = [
        PowerSlot(slot_index=1, label="Slot 1", is_outage=False, capacity_limit=7, unit_price=10.0),
        PowerSlot(slot_index=2, label="Slot 2 (Outage)", is_outage=True, capacity_limit=7, unit_price=0.0),
        PowerSlot(slot_index=3, label="Slot 3", is_outage=False, capacity_limit=7, unit_price=15.0),
        PowerSlot(slot_index=4, label="Slot 4", is_outage=False, capacity_limit=7, unit_price=8.0),
        PowerSlot(slot_index=5, label="Slot 5", is_outage=False, capacity_limit=7, unit_price=20.0),
        PowerSlot(slot_index=6, label="Slot 6", is_outage=False, capacity_limit=7, unit_price=4.0),
    ]
    return SchedulingEnvironment(
        jobs=jobs, slots=slots, name=f"Scaling_{num_appliances}_Appliances"
    )
