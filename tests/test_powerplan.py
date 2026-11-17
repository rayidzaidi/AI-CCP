"""PowerPlan Scheduler — Automated Pytest Verification Suite.

Comprehensive unit and integration tests verifying:
1. Outage enforcement (forces IDLE action strictly).
2. Capacity constraint filtering.
3. Admissible heuristic bounds (0 <= h(s) <= h*(s) for all reachable states, h(goal) == 0).
4. BFS earliest completion time (Slot 3).
5. A* global cost optimality ($64.00, matching exhaustive brute force).
6. DFS low memory footprint and feasibility.
7. Multi-slot Karachi ToU scenario.
8. Scaling environment generator (3 to 7 appliances).
9. Input validation and exception handling.
10. State immutability and hashability.
11. Lookahead feasibility pruning.
"""
from __future__ import annotations

import pytest
from typing import Dict, List, Set, Tuple

from powerplan.models import ApplianceJob, PowerSlot, ScheduleState, SearchResult
from powerplan.environment import SchedulingEnvironment
from powerplan.agent import SchedulingAgent
from powerplan.scenarios import (
    create_proposal_default_environment,
    create_karachi_kelectric_environment,
    create_scaling_environment,
)


# ==============================================================================
# Helper Functions for Verification
# ==============================================================================

def compute_h_star(
    env: SchedulingEnvironment,
    state: ScheduleState,
    memo: Dict[Tuple[int, Tuple[int, ...]], float] | None = None,
) -> float:
    """Computes exact optimal remaining cost h*(s) via exhaustive dynamic programming."""
    if memo is None:
        memo = {}
    if state.state_key in memo:
        return memo[state.state_key]

    if env.is_goal_state(state):
        return 0.0

    if state.current_slot_index >= len(env.slots):
        return float("inf")

    actions = env.get_valid_actions(state)
    if not actions:
        return float("inf")

    min_cost = float("inf")
    slot = env.slots[state.current_slot_index]

    for action in actions:
        next_state = env.apply_action(state, action)
        action_power = sum(env.job_map[jid].power_units for jid in action)
        step_cost = action_power * slot.unit_price

        future_cost = compute_h_star(env, next_state, memo)
        if future_cost != float("inf"):
            total_cost = step_cost + future_cost
            if total_cost < min_cost:
                min_cost = total_cost

    memo[state.state_key] = min_cost
    return min_cost


def collect_reachable_states(env: SchedulingEnvironment) -> Set[ScheduleState]:
    """Traverses the full reachable state space from the initial state."""
    initial = env.get_initial_state()
    visited: Set[ScheduleState] = set()
    frontier = [initial]

    while frontier:
        state = frontier.pop()
        if state in visited:
            continue
        visited.add(state)

        for action in env.get_valid_actions(state):
            next_state = env.apply_action(state, action)
            if next_state not in visited:
                frontier.append(next_state)

    return visited


# ==============================================================================
# 1. Outage Enforcement Test
# ==============================================================================

def test_outage_forces_idle_action() -> None:
    """Verify that calling get_valid_actions() during an outage strictly returns [()].

    During load-shedding, no appliances can be activated regardless of grid capacity.
    """
    env = create_proposal_default_environment()
    # Slot 2 (index 1) is a scheduled outage in the default proposal benchmark
    assert env.slots[1].is_outage is True
    assert env.slots[1].effective_capacity == 0

    # Advance to slot 2 with non-zero unfinished work
    initial_state = env.get_initial_state()
    # Schedule WP in slot 1
    state_at_slot_2 = env.apply_action(initial_state, ("WP",))
    assert state_at_slot_2.current_slot_index == 1

    actions = env.get_valid_actions(state_at_slot_2)
    assert actions == [()], (
        f"Outage slot MUST strictly return [()] (only the IDLE action), got: {actions}"
    )

    # Applying empty action in outage must succeed with 0 step cost
    next_state = env.apply_action(state_at_slot_2, ())
    assert next_state.current_slot_index == 2
    assert next_state.g_cost == state_at_slot_2.g_cost


# ==============================================================================
# 2. Capacity Constraint Filtering Test
# ==============================================================================

def test_capacity_constraint_filtering() -> None:
    """Verify that combinations exceeding slot capacity limit are strictly filtered out."""
    env = create_proposal_default_environment()
    initial_state = env.get_initial_state()
    capacity = env.slots[0].capacity_limit  # 6 units

    valid_actions = env.get_valid_actions(initial_state)

    # All returned combinations must respect capacity
    for action in valid_actions:
        action_power = sum(env.job_map[jid].power_units for jid in action)
        assert action_power <= capacity, (
            f"Action {action} draws {action_power}u, exceeding capacity limit {capacity}u!"
        )

    # Combinations exceeding 6 units MUST NOT be present
    # EV (4u) + WM (3u) = 7u > 6u
    assert ("EV", "WM") not in valid_actions
    assert ("WM", "EV") not in valid_actions
    # EV (4u) + WM (3u) + WP (2u) = 9u > 6u
    assert ("EV", "WM", "WP") not in valid_actions
    # All 4 appliances = 11u > 6u
    assert ("EV", "WM", "WP", "DW") not in valid_actions

    # Valid combinations that should be included:
    # Single jobs: WP (2u), WM (3u), DW (2u), EV (4u)
    # Pairs <= 6u: WP+WM (5u), WP+DW (4u), WP+EV (6u), WM+DW (5u)
    # IDLE: ()
    assert () in valid_actions
    assert ("WP",) in valid_actions
    assert ("WM",) in valid_actions
    assert ("DW",) in valid_actions
    assert ("EV",) in valid_actions
    assert ("WP", "WM") in valid_actions or ("WM", "WP") in valid_actions
    assert ("WP", "EV") in valid_actions or ("EV", "WP") in valid_actions


# ==============================================================================
# 3. Heuristic Admissibility & Goal Condition Test
# ==============================================================================

def test_heuristic_admissibility() -> None:
    """Verify that 0 <= h(s) <= h*(s) for all reachable states and h(goal) == 0.

    Mathematical guarantee:
    h(s) = remaining_energy * min_future_active_price <= h*(s)
    Because relaxing capacity limits and buying all remaining energy at the single
    lowest future active tariff can never exceed the actual constrained cost.
    """
    env = create_proposal_default_environment()
    reachable_states = collect_reachable_states(env)

    assert len(reachable_states) > 0

    memo: Dict[Tuple[int, Tuple[int, ...]], float] = {}

    for state in reachable_states:
        h_val = env.calculate_heuristic(state)

        if env.is_goal_state(state):
            assert h_val == 0.0, f"Heuristic at goal state must be 0.0, got {h_val}"
            continue

        h_star = compute_h_star(env, state, memo)

        if h_star < float("inf"):
            assert h_val >= 0.0, f"Heuristic must be non-negative, got {h_val}"
            assert h_val <= h_star + 1e-6, (
                f"Heuristic violation at state {state.state_key}: "
                f"h(s) = {h_val} > h*(s) = {h_star} (overestimation violates admissibility!)"
            )
        else:
            # If state cannot reach goal before horizon ends, heuristic may be inf
            assert h_val == float("inf") or h_val >= 0.0


# ==============================================================================
# 4. BFS Earliest Completion Time Test
# ==============================================================================

def test_bfs_finds_earliest_completion() -> None:
    """Verify BFS finishes all jobs by Slot 3 (the earliest possible completion slot)."""
    env = create_proposal_default_environment()
    agent = SchedulingAgent(env)
    result = agent.solve_bfs()

    assert result.success is True, "BFS should successfully find a schedule."
    assert result.completion_slot == 3, (
        f"BFS must finish by Slot 3 (the shallowest goal slot), got Slot {result.completion_slot}"
    )
    assert result.total_cost == 135.0, (
        f"BFS total cost on proposal benchmark should be $135.00, got ${result.total_cost}"
    )

    # Verify job packing:
    # Slot 1 (capacity 6u): packs 6u (EV 4u + WP 2u or WM 3u + WP 2u...)
    assert result.slot_loads[1] == 6
    # Slot 2: Outage -> 0u
    assert result.slot_loads[2] == 0
    # Slot 3: Remaining 5u finished
    assert result.slot_loads[3] == 5


# ==============================================================================
# 5. A* Global Cost Optimality Test
# ==============================================================================

def test_astar_finds_global_minimum_cost() -> None:
    """Verify A* finds the global cost minimum ($64.00), exactly matching brute force."""
    env = create_proposal_default_environment()
    agent = SchedulingAgent(env)
    result = agent.solve_astar()

    assert result.success is True, "A* should successfully find a schedule."
    assert result.total_cost == 64.0, (
        f"A* total cost on proposal benchmark must be $64.00, got ${result.total_cost}"
    )

    # Brute-force verification
    brute_force_optimal_cost = compute_h_star(env, env.get_initial_state())
    assert result.total_cost == brute_force_optimal_cost, (
        f"A* cost ({result.total_cost}) does not match brute-force optimal ({brute_force_optimal_cost})!"
    )

    # A* avoids expensive slots (Slot 3: $15, Slot 5: $20) and uses Slot 4 ($8) and Slot 6 ($4)
    assert result.slot_loads[1] == 0  # Idle in Slot 1 ($10)
    assert result.slot_loads[2] == 0  # Outage
    assert result.slot_loads[3] == 0  # Idle in Slot 3 ($15 Peak)
    assert result.slot_loads[4] == 5  # 5u in Slot 4 ($8 Shoulder -> $40)
    assert result.slot_loads[5] == 0  # Idle in Slot 5 ($20 Super Peak)
    assert result.slot_loads[6] == 6  # 6u in Slot 6 ($4 Off-Peak -> $24)
    # Total = $40 + $24 = $64


# ==============================================================================
# 6. DFS Low Memory Feasibility Test
# ==============================================================================

def test_dfs_low_memory_feasibility() -> None:
    """Verify DFS succeeds, finishes all jobs, and demonstrates low expansion overhead."""
    env = create_proposal_default_environment()
    agent = SchedulingAgent(env)

    dfs_result = agent.solve_dfs()
    bfs_result = agent.solve_bfs()

    assert dfs_result.success is True, "DFS should successfully find a schedule."
    assert dfs_result.final_state is not None
    assert dfs_result.final_state.is_all_completed() is True, (
        "DFS must finish all appliance durations."
    )
    # DFS requires significantly fewer node expansions to reach a feasible schedule (5 vs 12)
    assert dfs_result.nodes_expanded < bfs_result.nodes_expanded, (
        f"DFS nodes expanded ({dfs_result.nodes_expanded}) must be strictly less "
        f"than BFS nodes expanded ({bfs_result.nodes_expanded})"
    )
    # Frontier memory remains compact and tightly bounded
    assert dfs_result.max_frontier_size <= 25, (
        f"DFS peak frontier ({dfs_result.max_frontier_size}) exceeded expected bound."
    )


# ==============================================================================
# 7. Multi-Slot Karachi Scenario Test
# ==============================================================================

def test_karachi_multi_duration_scenario() -> None:
    """Verify execution on Karachi 8-slot scenario with multi-duration appliances."""
    env = create_karachi_kelectric_environment()
    agent = SchedulingAgent(env)

    # Verify job multi-slot durations
    assert env.job_map["DW"].duration_slots == 2
    assert env.job_map["EV"].duration_slots == 2
    assert env.slots[1].is_outage is True  # Slot 2 outage
    assert env.slots[4].is_outage is True  # Slot 5 outage

    results = agent.run_all_comparisons()

    for algo_name, res in results.items():
        assert res.success is True, f"{algo_name} failed on Karachi scenario."
        assert res.final_state is not None
        assert res.final_state.is_all_completed() is True, (
            f"{algo_name} did not complete all multi-slot durations in Karachi scenario."
        )


# ==============================================================================
# 8. Combinatorial Scaling Generator Test
# ==============================================================================

def test_scaling_environment_generator() -> None:
    """Verify scaling environments (3 to 7 appliances) are valid and solvable."""
    for n in range(3, 8):
        env = create_scaling_environment(n)
        assert len(env.jobs) == n, f"Expected {n} jobs, got {len(env.jobs)}"
        total_energy = sum(j.total_energy_units for j in env.jobs)
        assert total_energy == env.get_remaining_energy(env.get_initial_state())

        # Verify A* solves each scaling environment
        agent = SchedulingAgent(env)
        astar_res = agent.solve_astar()
        assert astar_res.success is True, f"A* failed to solve scaling env with {n} appliances"


# ==============================================================================
# 9. Input Validation and Exception Handling Tests
# ==============================================================================

def test_invalid_inputs_and_exceptions() -> None:
    """Verify validation guards on invalid appliance parameters and illegal actions."""
    # Invalid power_units <= 0
    with pytest.raises(ValueError, match="power_units must be positive"):
        ApplianceJob(job_id="BAD", name="Bad Appliance", power_units=0)

    # Invalid duration_slots <= 0
    with pytest.raises(ValueError, match="duration_slots must be positive"):
        ApplianceJob(job_id="BAD", name="Bad Appliance", power_units=2, duration_slots=0)

    # Empty jobs list
    slots = [PowerSlot(1, "S1", False, 6, 10.0)]
    with pytest.raises(ValueError, match="requires at least one ApplianceJob"):
        SchedulingEnvironment(jobs=[], slots=slots)

    # Empty slots list
    jobs = [ApplianceJob("WP", "Pump", 2)]
    with pytest.raises(ValueError, match="requires at least one PowerSlot"):
        SchedulingEnvironment(jobs=jobs, slots=[])

    # Attempting non-idle action during outage
    env = create_proposal_default_environment()
    state = env.get_initial_state()
    # Apply empty action in slot 1 to reach slot 2 (outage)
    state_outage = env.apply_action(state, ())
    assert env.slots[state_outage.current_slot_index].is_outage is True

    with pytest.raises(ValueError, match="during outage slot"):
        env.apply_action(state_outage, ("WP",))

    # Attempting action exceeding capacity
    with pytest.raises(ValueError, match="exceeds slot"):
        env.apply_action(state, ("EV", "WM"))  # 4u + 3u = 7u > 6u

    # Attempting to schedule already completed job
    # Complete WP first
    state_after_wp = env.apply_action(state, ("WP",))
    # Try to schedule WP again in next active slot (say slot 3)
    state_s3 = env.apply_action(state_after_wp, ())  # slot 2 outage
    with pytest.raises(ValueError, match="already completed"):
        env.apply_action(state_s3, ("WP",))


# ==============================================================================
# 10. State Immutability and Hashability Tests
# ==============================================================================

def test_state_immutability_and_hashability() -> None:
    """Verify that ScheduleState is immutable and correctly hashable for graph search."""
    env = create_proposal_default_environment()
    state1 = env.get_initial_state()
    state2 = env.get_initial_state()

    assert state1 == state2
    assert hash(state1) == hash(state2)

    state_set = {state1}
    assert state2 in state_set

    # Ensure state fields cannot be mutated directly
    with pytest.raises(Exception):
        state1.current_slot_index = 5  # type: ignore[misc]


# ==============================================================================
# 11. Lookahead Feasibility Pruning Tests
# ==============================================================================

def test_feasibility_lookahead_pruning() -> None:
    """Verify is_remaining_feasible and calculate_heuristic return False / inf when impossible."""
    env = create_proposal_default_environment()

    # Create a state at the last slot with more energy than slot capacity
    # Slot 6 has capacity 6u. Suppose remaining work requires 10u.
    impossible_state = ScheduleState(
        current_slot_index=5,  # slot 6 (index 5)
        remaining_durations=(2, 2, 0, 0),  # WP(2u)*2 + WM(3u)*2 = 10u
    )
    assert env.is_remaining_feasible(impossible_state) is False
    assert env.calculate_heuristic(impossible_state) == float("inf")
