"""PowerPlan Scheduler — Intelligent Search Agent.

Implements BFS, DFS, and A* search strategies over the SchedulingEnvironment
state space, with full instrumentation (nodes expanded, nodes generated,
max frontier size, execution time, step-by-step trace).
"""
from __future__ import annotations

import heapq
import itertools
import time
from collections import deque
from typing import Dict, List, Optional, Set, Tuple

from powerplan.environment import SchedulingEnvironment
from powerplan.models import ScheduleState, SearchResult


class SchedulingAgent:
    """Intelligent scheduling agent implementing BFS, DFS, and A* search strategies.

    Attributes:
        env: The SchedulingEnvironment instance to search over.
    """

    def __init__(self, env: SchedulingEnvironment) -> None:
        self.env: SchedulingEnvironment = env

    # ------------------------------------------------------------------
    # Internal helper: build a SearchResult from raw metrics
    # ------------------------------------------------------------------

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
        """Packages raw search metrics and the goal state into a SearchResult."""
        elapsed_ms: float = round((time.perf_counter() - start_time) * 1000.0, 3)

        slot_assignments: Dict[int, List[str]] = {}
        slot_loads: Dict[int, int] = {}
        slot_costs: Dict[int, float] = {}

        for slot in self.env.slots:
            s_idx: int = slot.slot_index
            if final_state is not None and (s_idx - 1) < len(final_state.assignments):
                assigned: List[str] = list(final_state.assignments[s_idx - 1])
            else:
                assigned = []
            load: int = sum(
                self.env.job_map[jid].power_units for jid in assigned
            )
            cost: float = round(load * slot.unit_price, 2)
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

    # ------------------------------------------------------------------
    # BFS — Breadth-First Search (FIFO Queue)
    # ------------------------------------------------------------------

    def solve_bfs(self) -> SearchResult:
        """Breadth-First Search (FIFO Queue).

        Optimizes for Earliest Completion Time (shallowest slot depth where
        all jobs finish). Orders single-slot actions from highest energy packed
        to IDLE so full packing is explored first.
        """
        start_time: float = time.perf_counter()
        initial_state: ScheduleState = self.env.get_initial_state()

        if self.env.is_goal_state(initial_state):
            return self._build_result(
                "BFS (Breadth-First Search)",
                "Earliest Completion Time",
                initial_state,
                0, 1, 1,
                start_time,
                [],
            )

        frontier: deque[ScheduleState] = deque([initial_state])
        visited: Set[Tuple[int, Tuple[int, ...]]] = {initial_state.state_key}
        nodes_expanded: int = 0
        nodes_generated: int = 1
        max_frontier_size: int = 1
        trace: List[Dict[str, object]] = []

        while frontier:
            max_frontier_size = max(max_frontier_size, len(frontier))
            state: ScheduleState = frontier.popleft()
            nodes_expanded += 1

            # Sort actions by descending total energy packed so BFS
            # prioritizes earliest work completion
            actions: List[Tuple[str, ...]] = self.env.get_valid_actions(state)
            actions.sort(
                key=lambda act: (
                    sum(self.env.job_map[jid].power_units for jid in act),
                    len(act),
                ),
                reverse=True,
            )

            for action in actions:
                next_state: ScheduleState = self.env.apply_action(state, action)
                nodes_generated += 1

                if not self.env.is_remaining_feasible(next_state):
                    continue

                if self.env.is_goal_state(next_state):
                    trace.append(
                        {
                            "step": nodes_expanded,
                            "slot": state.current_slot_index + 1,
                            "action": action,
                            "g_cost": next_state.g_cost,
                            "event": "GOAL_FOUND",
                        }
                    )
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

    # ------------------------------------------------------------------
    # DFS — Depth-First Search (LIFO Stack)
    # ------------------------------------------------------------------

    def solve_dfs(self) -> SearchResult:
        """Depth-First Search (LIFO Stack).

        Optimizes for finding the first computationally feasible schedule with
        minimal memory overhead. Pushes actions so modest single/pair allocations
        are explored at the top of the LIFO stack, producing a realistic
        multi-slot DFS spread distinct from BFS and A*.
        """
        start_time: float = time.perf_counter()
        initial_state: ScheduleState = self.env.get_initial_state()

        stack: List[ScheduleState] = [initial_state]
        visited: Set[Tuple[int, Tuple[int, ...]]] = set()
        nodes_expanded: int = 0
        nodes_generated: int = 1
        max_frontier_size: int = 1
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
            # Push IDLE first and moderate single-appliance actions last
            # (so they pop first from LIFO)
            actions.sort(
                key=lambda act: (
                    len(act) == 1,
                    len(act) > 1,
                    -sum(self.env.job_map[jid].power_units for jid in act),
                ),
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

    # ------------------------------------------------------------------
    # A* Search (Priority Queue with admissible heuristic)
    # ------------------------------------------------------------------

    def solve_astar(self) -> SearchResult:
        """A* Search (Priority Queue ordered by f(n) = g(n) + h(n)).

        Uses the admissible heuristic h(n) = Remaining Energy × Lowest Future
        Active Price to guarantee the minimum total energy cost schedule.

        Priority tuple: (f_cost, h_cost, completion_slot, tie_breaker, state)
        """
        start_time: float = time.perf_counter()
        initial_state: ScheduleState = self.env.get_initial_state()
        counter = itertools.count()

        init_h: float = self.env.calculate_heuristic(initial_state)
        # Priority tuple: (f_cost, h_cost, completion_slot, tie_breaker, state)
        frontier: List[Tuple[float, float, int, int, ScheduleState]] = [
            (init_h, init_h, 0, next(counter), initial_state)
        ]
        best_g: Dict[Tuple[int, Tuple[int, ...]], float] = {
            initial_state.state_key: 0.0
        }

        nodes_expanded: int = 0
        nodes_generated: int = 1
        max_frontier_size: int = 1
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

            # Skip stale priority queue entries if a cheaper path was found
            if state.g_cost > best_g.get(state.state_key, float("inf")):
                continue

            nodes_expanded += 1

            for action in self.env.get_valid_actions(state):
                next_state: ScheduleState = self.env.apply_action(state, action)
                nodes_generated += 1

                h_next: float = self.env.calculate_heuristic(next_state)
                if h_next == float("inf"):
                    continue  # Pruned by feasibility / admissible heuristic bound

                g_next: float = next_state.g_cost
                f_next: float = round(g_next + h_next, 6)

                # Goal states use canonical key so all goal paths compete
                # strictly on g_cost
                canonical_key: Tuple[int, Tuple[int, ...]] = (
                    (-1, next_state.remaining_durations)
                    if next_state.is_all_completed()
                    else next_state.state_key
                )

                if g_next < best_g.get(canonical_key, float("inf")):
                    best_g[canonical_key] = g_next
                    heapq.heappush(
                        frontier,
                        (
                            f_next,
                            h_next,
                            next_state.completion_slot,
                            next(counter),
                            next_state,
                        ),
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

    # ------------------------------------------------------------------
    # Convenience runner
    # ------------------------------------------------------------------

    def run_all_comparisons(self) -> Dict[str, SearchResult]:
        """Executes BFS, DFS, and A* on the same environment and returns results."""
        return {
            "BFS": self.solve_bfs(),
            "DFS": self.solve_dfs(),
            "A*": self.solve_astar(),
        }
