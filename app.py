"""PowerPlan Scheduler — Interactive State-Space Optimization Dashboard.

Professional Light Glassmorphism UI for CSC-471-L Artificial Intelligence (Lab Session 6).
Department of Computer Science, Iqra University.
Student: Dua Rehan (ID: 67238) | Instructor: Engr. Aimen Zafar.

Execute:
    streamlit run app.py
"""
from __future__ import annotations

import io
import os
import tempfile
from pathlib import Path
from typing import Dict, List

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
import streamlit as st

# Core package imports
from powerplan.models import ApplianceJob, PowerSlot, SearchResult
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


def clean_html(s: str) -> str:
    """Removes all leading and trailing whitespace from each line to prevent markdown code block triggers."""
    return "".join(line.strip() for line in s.splitlines())

# ---------------------------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="PowerPlan Scheduler — AI Search Benchmark",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Light Glassmorphism Global CSS Injection
# ---------------------------------------------------------------------------
GLASS_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
}

code, pre, .font-mono {
    font-family: 'JetBrains Mono', monospace !important;
}

/* Light Background Canvas */
.stApp {
    background: radial-gradient(circle at 10% 10%, #f8fafc 0%, #f1f5f9 100%);
    color: #0f172a;
}

/* Glassmorphism Containers */
.glass-panel {
    background: rgba(255, 255, 255, 0.85);
    backdrop-filter: blur(16px);
    -webkit-backdrop-filter: blur(16px);
    border: 1px solid rgba(226, 232, 240, 0.9);
    box-shadow: 0 10px 30px -10px rgba(0, 0, 0, 0.04), 0 1px 3px 0 rgba(0, 0, 0, 0.02);
    border-radius: 14px;
    padding: 1.25rem 1.5rem;
    margin-bottom: 1rem;
}

.glass-card {
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(14px);
    -webkit-backdrop-filter: blur(14px);
    border: 1px solid rgba(226, 232, 240, 0.85);
    box-shadow: 0 4px 14px -2px rgba(0, 0, 0, 0.03);
    border-radius: 12px;
    padding: 1rem 1.15rem;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1);
}

.glass-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 12px 24px -6px rgba(0, 0, 0, 0.06);
    border-color: rgba(203, 213, 225, 0.95);
}

/* Top Accent Line Cards */
.card-emerald { border-top: 3.5px solid #10b981; }
.card-blue { border-top: 3.5px solid #3b82f6; }
.card-amber { border-top: 3.5px solid #f59e0b; }
.card-violet { border-top: 3.5px solid #8b5cf6; }

/* Hazard Striping for Outage States */
.hazard-stripe-light {
    background: repeating-linear-gradient(
        45deg,
        #fef2f2,
        #fef2f2 10px,
        #fee2e2 10px,
        #fee2e2 20px
    ) !important;
    border: 1px solid #fca5a5 !important;
}

/* Badges and Technical Chips */
.tech-pill {
    display: inline-flex;
    align-items: center;
    padding: 0.2rem 0.55rem;
    border-radius: 6px;
    font-size: 0.72rem;
    font-weight: 600;
    letter-spacing: 0.02em;
    border: 1px solid;
}
.pill-emerald { background: #ecfdf5; color: #047857; border-color: #a7f3d0; }
.pill-blue { background: #eff6ff; color: #1d4ed8; border-color: #bfdbfe; }
.pill-amber { background: #fffbeb; color: #b45309; border-color: #fde68a; }
.pill-rose { background: #fff1f2; color: #be123c; border-color: #fecdd3; }
.pill-slate { background: #f8fafc; color: #334155; border-color: #e2e8f0; }

/* --------------------------------------------------------------------------
   Linear / Vercel Style Segmented Tab Bar (Pill Capsule)
   -------------------------------------------------------------------------- */
div[data-testid="stTabs"] [data-baseweb="tab-border"],
div[data-testid="stTabs"] [data-baseweb="tab-highlight"],
div[data-baseweb="tab-border"],
div[data-baseweb="tab-highlight"] {
    display: none !important;
}

div[data-testid="stTabs"] [data-baseweb="tab-list"],
div[data-baseweb="tab-list"] {
    background: #f1f5f9 !important;
    border: 1px solid #e2e8f0 !important;
    border-radius: 12px !important;
    padding: 5px !important;
    gap: 6px !important;
    display: inline-flex !important;
    box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.03) !important;
    margin-bottom: 1.25rem !important;
}

div[data-testid="stTabs"] button[role="tab"],
button[data-baseweb="tab"] {
    border-radius: 8px !important;
    padding: 8px 20px !important;
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif !important;
    font-size: 0.85rem !important;
    font-weight: 600 !important;
    color: #64748b !important;
    background: transparent !important;
    border: 1px solid transparent !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stTabs"] button[role="tab"]:hover,
button[data-baseweb="tab"]:hover {
    color: #0f172a !important;
    background: rgba(255, 255, 255, 0.6) !important;
}

div[data-testid="stTabs"] button[role="tab"][aria-selected="true"],
button[data-baseweb="tab"][aria-selected="true"] {
    background: #ffffff !important;
    color: #0284c7 !important;
    font-weight: 700 !important;
    box-shadow: 0 2px 8px -2px rgba(0, 0, 0, 0.08), 0 1px 2px 0 rgba(0, 0, 0, 0.04) !important;
    border: 1px solid rgba(226, 232, 240, 0.9) !important;
}

/* Streamlit Button Styling */
div.stButton > button {
    background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
    color: #ffffff;
    font-weight: 600;
    border-radius: 9px;
    border: 1px solid #0f172a;
    padding: 0.55rem 1.25rem;
    box-shadow: 0 4px 12px rgba(15, 23, 42, 0.12);
    transition: all 0.2s ease;
}

div.stButton > button:hover {
    background: linear-gradient(135deg, #334155 0%, #1e293b 100%);
    color: #ffffff;
    border-color: #1e293b;
    box-shadow: 0 6px 18px rgba(15, 23, 42, 0.18);
    transform: translateY(-1px);
}

/* Sidebar Customization */
section[data-testid="stSidebar"] {
    background: rgba(255, 255, 255, 0.75);
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border-right: 1px solid rgba(226, 232, 240, 0.85);
}

/* Hide Streamlit Default Decoration */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}
</style>
"""
st.markdown(GLASS_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Frosted Hero Header
# ---------------------------------------------------------------------------
HERO_HTML = """
<div class="glass-panel" style="margin-top: -1rem; padding: 1.4rem 1.75rem;">
    <div style="display: flex; justify-content: space-between; align-items: flex-start; flex-wrap: wrap; gap: 1rem;">
        <div>
            <div style="display: flex; align-items: center; gap: 0.6rem; margin-bottom: 0.35rem;">
                <span class="tech-pill pill-blue">LAB SESSION 6</span>
                <span class="tech-pill pill-slate">OPEN-ENDED LAB</span>
                <span class="tech-pill pill-emerald">DETERMINISTIC STATE-SPACE OPTIMIZATION</span>
            </div>
            <h1 style="font-size: 1.65rem; font-weight: 800; color: #0f172a; margin: 0; letter-spacing: -0.025em;">
                PowerPlan Scheduler
            </h1>
            <p style="font-size: 0.9rem; color: #475569; margin: 0.25rem 0 0 0; line-height: 1.4;">
                Autonomous Outage-Aware Load Shifting & Comparative Search Analytics: BFS vs. DFS vs. A*
            </p>
        </div>
        <div style="text-align: right; min-width: 260px;">
            <div style="display: flex; flex-direction: column; gap: 0.25rem; font-size: 0.78rem; color: #334155;">
                <div><span style="color: #64748b; font-weight: 500;">Candidate:</span> <strong style="color: #0f172a;">Dua Rehan (Roll No. 67238)</strong></div>
                <div><span style="color: #64748b; font-weight: 500;">Course:</span> <strong>CSC-471-L Artificial Intelligence</strong></div>
                <div><span style="color: #64748b; font-weight: 500;">Instructor:</span> <strong>Engr. Aimen Zafar</strong></div>
                <div><span style="color: #64748b; font-weight: 500;">Institution:</span> <strong>Iqra University — Department of CS</strong></div>
            </div>
            <div style="margin-top: 0.45rem; display: flex; gap: 0.35rem; justify-content: flex-end;">
                <span class="tech-pill pill-slate" style="font-size: 0.68rem;">Bloom: C3, P2</span>
                <span class="tech-pill pill-slate" style="font-size: 0.68rem;">GA-2 / GA-5</span>
            </div>
        </div>
    </div>
</div>
"""
st.markdown(clean_html(HERO_HTML), unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Sidebar Configuration & Telemetry
# ---------------------------------------------------------------------------
with st.sidebar:
    st.markdown(
        clean_html("""
        <div style="padding: 0.2rem 0 0.8rem 0; border-bottom: 1px solid #e2e8f0; margin-bottom: 1rem;">
            <div style="font-size: 0.75rem; font-weight: 700; text-transform: uppercase; letter-spacing: 0.05em; color: #64748b;">
                System Configuration
            </div>
            <div style="font-size: 1.1rem; font-weight: 800; color: #0f172a;">
                Simulation Parameters
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    scenario_choice = st.selectbox(
        "Scenario Preset",
        [
            "Proposal 6-Slot Benchmark",
            "Karachi K-Electric 8-Slot",
            "Custom Configuration",
        ],
        index=0,
    )

    grid_capacity = st.slider(
        "Grid Capacity Limit (kW / slot)",
        min_value=4,
        max_value=12,
        value=6,
        step=1,
        help="Maximum simultaneous energy units supported by the feeder without tripping.",
    )

    # Dynamic custom inputs
    custom_jobs: List[ApplianceJob] = []
    custom_slots: List[PowerSlot] = []

    if scenario_choice == "Custom Configuration":
        st.markdown("---")
        st.markdown("##### Temporal Slot Vector")
        num_slots = st.number_input("Slot Count", min_value=3, max_value=10, value=6, step=1)
        
        custom_outages: List[bool] = []
        custom_tariffs: List[float] = []
        for s_idx in range(1, int(num_slots) + 1):
            col_a, col_b = st.columns([1, 1])
            with col_a:
                is_outage = st.checkbox(f"S{s_idx} Outage", value=(s_idx == 2), key=f"outage_s{s_idx}")
                custom_outages.append(is_outage)
            with col_b:
                tariff = st.number_input(
                    f"S{s_idx} Tariff ($)",
                    min_value=0.0,
                    max_value=50.0,
                    value=10.0 if not is_outage else 0.0,
                    step=1.0,
                    key=f"tariff_s{s_idx}",
                )
                custom_tariffs.append(tariff)

        st.markdown("##### Appliance Demand Profile")
        num_apps = st.number_input("Appliance Count", min_value=2, max_value=6, value=4, step=1)
        default_apps = [
            ("WP", "Water Pump", 2, 1),
            ("WM", "Washing Machine", 3, 1),
            ("DW", "Dishwasher", 2, 1),
            ("EV", "EV Charger", 4, 1),
            ("IH", "Induction Heater", 2, 1),
            ("AC", "Air Conditioner", 3, 1),
        ]
        for a_idx in range(int(num_apps)):
            col_p, col_d = st.columns([1, 1])
            app_meta = default_apps[a_idx] if a_idx < len(default_apps) else (f"J{a_idx+1}", f"Load {a_idx+1}", 2, 1)
            with col_p:
                pwr = st.number_input(f"{app_meta[0]} Power (kW)", min_value=1, max_value=8, value=app_meta[2], key=f"pwr_{a_idx}")
            with col_d:
                dur = st.number_input(f"{app_meta[0]} Duration", min_value=1, max_value=4, value=app_meta[3], key=f"dur_{a_idx}")
            custom_jobs.append(ApplianceJob(job_id=app_meta[0], name=app_meta[1], power_units=int(pwr), duration_slots=int(dur)))

    st.markdown("---")
    run_benchmark = st.button("EXECUTE SEARCH STRATEGIES", use_container_width=True, type="primary")

    # Appliance Specification Summary Table in Sidebar
    st.markdown("---")
    st.markdown(
        clean_html("""
        <div style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #64748b; margin-bottom: 0.4rem;">
            Appliance Fleet Demand (Fixed)
        </div>
        """),
        unsafe_allow_html=True,
    )
    fleet_data = [
        {"Job ID": "WP", "Appliance": "Water Pump", "Power": "2 kW", "Duration": "1 slot", "Energy": "2 kWh"},
        {"Job ID": "WM", "Appliance": "Washing Machine", "Power": "3 kW", "Duration": "1 slot", "Energy": "3 kWh"},
        {"Job ID": "DW", "Appliance": "Dishwasher", "Power": "2 kW", "Duration": "1 slot", "Energy": "2 kWh"},
        {"Job ID": "EV", "Appliance": "EV Charger", "Power": "4 kW", "Duration": "1 slot", "Energy": "4 kWh"},
    ]
    st.dataframe(pd.DataFrame(fleet_data), hide_index=True, use_container_width=True)
    st.caption("Total Inflexible Demand = 11.0 kWh across active slots.")


# ---------------------------------------------------------------------------
# Helper: Environment Instantiation
# ---------------------------------------------------------------------------
def resolve_environment() -> SchedulingEnvironment:
    if scenario_choice == "Proposal 6-Slot Benchmark":
        env = create_proposal_default_environment()
        if grid_capacity != 6:
            new_slots = [
                PowerSlot(
                    slot_index=s.slot_index,
                    label=s.label,
                    is_outage=s.is_outage,
                    capacity_limit=grid_capacity,
                    unit_price=s.unit_price,
                )
                for s in env.slots
            ]
            env = SchedulingEnvironment(list(env.jobs), new_slots, name=env.name)
        return env

    if scenario_choice == "Karachi K-Electric 8-Slot":
        env = create_karachi_kelectric_environment()
        if grid_capacity != 6:
            new_slots = [
                PowerSlot(
                    slot_index=s.slot_index,
                    label=s.label,
                    is_outage=s.is_outage,
                    capacity_limit=grid_capacity,
                    unit_price=s.unit_price,
                )
                for s in env.slots
            ]
            env = SchedulingEnvironment(list(env.jobs), new_slots, name=env.name)
        return env

    # Custom
    slots = [
        PowerSlot(
            slot_index=i + 1,
            label=f"Slot {i + 1}",
            is_outage=custom_outages[i],
            capacity_limit=grid_capacity,
            unit_price=custom_tariffs[i],
        )
        for i in range(len(custom_outages))
    ]
    return SchedulingEnvironment(custom_jobs, slots, name="Custom_Simulation")


# ---------------------------------------------------------------------------
# Execution Engine & State Management
# ---------------------------------------------------------------------------
env = resolve_environment()
agent = SchedulingAgent(env)

# Always run or cache the benchmark results
if "results" not in st.session_state or run_benchmark:
    with st.spinner("Executing State-Space Search Models (BFS, DFS, A*)..."):
        st.session_state.results = agent.run_all_comparisons()
        st.session_state.current_env = env

results: Dict[str, SearchResult] = st.session_state.results
current_env: SchedulingEnvironment = st.session_state.current_env

bfs_res = results["BFS"]
dfs_res = results["DFS"]
astar_res = results["A*"]

savings_amount = bfs_res.total_cost - astar_res.total_cost
savings_pct = (savings_amount / bfs_res.total_cost * 100.0) if bfs_res.total_cost > 0 else 0.0


# ---------------------------------------------------------------------------
# Executive KPI Row (4 Glassmorphic Metric Cards)
# ---------------------------------------------------------------------------
kpi_cols = st.columns(4)

with kpi_cols[0]:
    st.markdown(
        clean_html(f"""
        <div class="glass-card card-emerald">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em;">
                    Cost Optimization
                </span>
                <span class="tech-pill pill-emerald">-{savings_pct:.1f}% SAVINGS</span>
            </div>
            <div style="margin-top: 0.4rem; display: flex; align-items: baseline; gap: 0.5rem;">
                <span class="font-mono" style="font-size: 1.85rem; font-weight: 800; color: #047857;">
                    ${astar_res.total_cost:.2f}
                </span>
                <span class="font-mono" style="font-size: 0.85rem; color: #94a3b8; text-decoration: line-through;">
                    ${bfs_res.total_cost:.2f}
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #475569; margin-top: 0.35rem;">
                Net Cost Reduction: <strong>${savings_amount:.2f}</strong> vs. BFS baseline
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

with kpi_cols[1]:
    st.markdown(
        clean_html(f"""
        <div class="glass-card card-blue">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em;">
                    Time-to-Completion
                </span>
                <span class="tech-pill pill-blue">DEPTH {astar_res.completion_slot}</span>
            </div>
            <div style="margin-top: 0.4rem; display: flex; align-items: baseline; gap: 0.4rem;">
                <span class="font-mono" style="font-size: 1.85rem; font-weight: 800; color: #0f172a;">
                    Slot {astar_res.completion_slot}
                </span>
                <span class="font-mono" style="font-size: 0.85rem; color: #64748b;">
                    / {len(current_env.slots)}
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #475569; margin-top: 0.35rem;">
                A* delays to cheap slots (BFS completes at Slot {bfs_res.completion_slot})
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

with kpi_cols[2]:
    st.markdown(
        clean_html(f"""
        <div class="glass-card card-violet">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em;">
                    Frontier Expansion
                </span>
                <span class="tech-pill pill-slate">{astar_res.execution_time_ms:.2f} ms</span>
            </div>
            <div style="margin-top: 0.4rem; display: flex; align-items: baseline; gap: 0.4rem;">
                <span class="font-mono" style="font-size: 1.85rem; font-weight: 800; color: #0f172a;">
                    {astar_res.nodes_expanded}
                </span>
                <span class="font-mono" style="font-size: 0.85rem; color: #64748b;">
                    / {astar_res.nodes_generated} generated
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #475569; margin-top: 0.35rem;">
                Peak Priority Queue size: <strong>{astar_res.max_frontier_size} nodes</strong>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

with kpi_cols[3]:
    st.markdown(
        clean_html(f"""
        <div class="glass-card card-amber">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <span style="font-size: 0.72rem; font-weight: 700; text-transform: uppercase; color: #64748b; letter-spacing: 0.05em;">
                    Heuristic Integrity
                </span>
                <span class="tech-pill pill-amber">ADMISSIBLE</span>
            </div>
            <div style="margin-top: 0.4rem; display: flex; align-items: baseline; gap: 0.4rem;">
                <span class="font-mono" style="font-size: 1.35rem; font-weight: 800; color: #0f172a;">
                    h(n) &le; h*(n)
                </span>
            </div>
            <div style="font-size: 0.78rem; color: #475569; margin-top: 0.45rem;">
                Guaranteeing global cost-optimality without overestimation
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

st.markdown("<div style='height: 0.75rem;'></div>", unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Main Analytical Workspace (Segmented Pill Capsule Navigation)
# ---------------------------------------------------------------------------
tab_heatmap, tab_matrix, tab_telemetry, tab_scaling, tab_report = st.tabs([
    "Schedule Heatmap",
    "Dispatch Matrix",
    "Search Telemetry",
    "Scaling Benchmark",
    "Experimental Report",
])


# ---- TAB 1: Visual Schedule Heatmap ----
with tab_heatmap:
    st.markdown("#### Side-by-Side Allocation Matrix (BFS vs. DFS vs. A*)")
    st.caption("Displays exact appliance assignment per slot alongside scheduled grid outages and load-to-capacity metrics.")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="outputs") as tmp:
        heatmap_path = render_schedule_heatmap(current_env, results, output_path=tmp.name)
    st.image(heatmap_path, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Comparative Algorithmic Telemetry Charts")
    st.caption("Side-by-side performance bars comparing Total Energy Cost, Completion Slot Depth, Nodes Expanded, and Memory Footprint.")

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="outputs") as tmp:
        metrics_path = render_metrics_comparison(results, output_path=tmp.name)
    st.image(metrics_path, use_container_width=True)


# ---- TAB 2: Interactive Dispatch Matrix ----
with tab_matrix:
    st.markdown(
        clean_html("""
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.6rem;">
            <div>
                <span style="font-size: 1rem; font-weight: 700; color: #0f172a;">
                    Chronological Time-Slot Dispatch Timeline
                </span>
                <span style="font-size: 0.82rem; color: #64748b; margin-left: 0.5rem;">
                    Feeder Capacity Limit: 6 kW
                </span>
            </div>
        </div>
        """),
        unsafe_allow_html=True,
    )

    # Selector for which algorithm's schedule to display in the dispatch matrix
    selected_algo_key = st.radio(
        "Active Strategy Schedule Inspector",
        ["A* Search (Minimum Energy Cost)", "BFS (Earliest Completion)", "DFS (Low-Memory First Feasible)"],
        index=0,
        horizontal=True,
        label_visibility="collapsed",
    )

    active_algo_map = {
        "A* Search (Minimum Energy Cost)": astar_res,
        "BFS (Earliest Completion)": bfs_res,
        "DFS (Low-Memory First Feasible)": dfs_res,
    }
    active_res = active_algo_map[selected_algo_key]

    # Render 6 Slot Cards horizontally
    slot_cols = st.columns(len(current_env.slots))

    for idx, slot in enumerate(current_env.slots):
        s_num = slot.slot_index
        load = active_res.slot_loads.get(s_num, 0)
        cap = slot.effective_capacity
        cost = active_res.slot_costs.get(s_num, 0.0)
        assigned_jobs = active_res.slot_assignments.get(s_num, [])

        with slot_cols[idx]:
            if slot.is_outage:
                outage_card = f"""
                <div class="glass-card hazard-stripe-light" style="min-height: 205px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="font-size: 0.82rem; color: #991b1b;">Slot {s_num}</strong>
                            <span class="tech-pill pill-rose" style="font-size: 0.65rem;">OUTAGE</span>
                        </div>
                        <div style="font-size: 0.72rem; color: #b91c1c; margin-top: 0.2rem;">{slot.label}</div>
                    </div>
                    <div style="text-align: center; padding: 0.8rem 0;">
                        <div style="font-weight: 800; font-size: 0.85rem; color: #991b1b; letter-spacing: 0.05em;">FORCED IDLE</div>
                        <div style="font-size: 0.7rem; color: #7f1d1d; margin-top: 0.15rem;">Grid Feeder Disabled</div>
                    </div>
                    <div style="border-top: 1px dashed #fca5a5; padding-top: 0.4rem; font-size: 0.72rem; display: flex; justify-content: space-between;">
                        <span style="color: #7f1d1d;">Load: 0/0 kW</span>
                        <span class="font-mono" style="font-weight: 700; color: #991b1b;">$0.00</span>
                    </div>
                </div>
                """
                st.markdown(clean_html(outage_card), unsafe_allow_html=True)
            else:
                is_active = len(assigned_jobs) > 0
                card_class = "glass-card"
                if is_active:
                    if active_res == astar_res:
                        card_class = "glass-card card-emerald"
                    elif active_res == bfs_res:
                        card_class = "glass-card card-blue"
                    else:
                        card_class = "glass-card card-amber"

                chips_html = ""
                if assigned_jobs:
                    for jid in assigned_jobs:
                        job_obj = current_env.job_map[jid]
                        chips_html += f"""
                        <div style="background: rgba(241, 245, 249, 0.95); border: 1px solid #cbd5e1; border-radius: 6px; padding: 0.25rem 0.45rem; margin-bottom: 0.25rem; display: flex; justify-content: space-between; align-items: center; font-size: 0.72rem;">
                            <span style="font-weight: 600; color: #1e293b; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;">{job_obj.name}</span>
                            <span class="font-mono" style="font-size: 0.68rem; font-weight: 700; color: #0284c7;">{job_obj.power_units} kW</span>
                        </div>
                        """
                else:
                    chips_html = """
                    <div style="text-align: center; padding: 0.9rem 0; color: #94a3b8; font-size: 0.75rem;">
                        <em>No Load (Idle)</em>
                    </div>
                    """

                load_pct = min(100, int((load / cap) * 100)) if cap > 0 else 0
                meter_color = "#10b981" if load == cap else "#3b82f6"

                card_content = f"""
                <div class="{card_class}" style="min-height: 205px; display: flex; flex-direction: column; justify-content: space-between;">
                    <div>
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <strong style="font-size: 0.82rem; color: #0f172a;">Slot {s_num}</strong>
                            <span class="tech-pill pill-slate font-mono">${slot.unit_price:.0f}/u</span>
                        </div>
                        <div style="font-size: 0.7rem; color: #64748b; margin-top: 0.15rem;">{slot.label}</div>
                    </div>
                    <div style="margin: 0.4rem 0;">
                        {chips_html}
                    </div>
                    <div>
                        <div style="display: flex; justify-content: space-between; font-size: 0.7rem; color: #475569; margin-bottom: 0.25rem;">
                            <span>Load: <strong>{load}/{cap} kW</strong></span>
                            <span class="font-mono" style="font-weight: 700; color: #047857;">${cost:.2f}</span>
                        </div>
                        <div style="background: #e2e8f0; height: 5px; border-radius: 9999px; overflow: hidden;">
                            <div style="background: {meter_color}; width: {load_pct}%; height: 100%; border-radius: 9999px;"></div>
                        </div>
                    </div>
                </div>
                """
                st.markdown(clean_html(card_content), unsafe_allow_html=True)


# ---- TAB 3: Search Telemetry ----
with tab_telemetry:
    st.markdown("#### Search Strategy Benchmark Summary")
    st.caption("Empirical trade-offs across total energy expenditure, completion slot depth, node generation, and peak memory.")

    # Detailed Comparison Table
    summary_data = []
    for key in ["BFS", "DFS", "A*"]:
        r = results[key]
        summary_data.append({
            "Search Algorithm": r.algorithm_name,
            "Primary Objective": r.goal_Description,
            "Total Cost ($)": f"${r.total_cost:.2f}",
            "Completion Slot": f"Slot {r.completion_slot}",
            "Nodes Expanded": r.nodes_expanded,
            "Nodes Generated": r.nodes_generated,
            "Peak Queue (Nodes)": r.max_frontier_size,
            "Runtime (ms)": f"{r.execution_time_ms:.3f}",
        })
    st.dataframe(pd.DataFrame(summary_data), hide_index=True, use_container_width=True)

    st.markdown("---")
    st.markdown("#### Step-by-Step Search Frontier Telemetry & Transitions")
    st.caption("Inspect exact state transitions, action subsets, and evaluation functions at every expansion step.")

    for algo_key in ["A*", "BFS", "DFS"]:
        res = results[algo_key]
        with st.expander(f"Search Trace: {res.algorithm_name} (Cost: ${res.total_cost:.2f} | Completed: Slot {res.completion_slot})", expanded=(algo_key == "A*")):
            if res.search_trace:
                trace_df = pd.DataFrame(res.search_trace)
                st.dataframe(trace_df, use_container_width=True, hide_index=True)
            else:
                st.info(f"Full expansion telemetry for {algo_key}: {res.nodes_expanded} states evaluated in level/depth order.")

            # Slot-by-Slot Action Breakdown
            breakdown_rows = []
            for slot in current_env.slots:
                s_idx = slot.slot_index
                assigned = res.slot_assignments.get(s_idx, [])
                breakdown_rows.append({
                    "Slot Index": f"Slot {s_idx}",
                    "Temporal Label": slot.label,
                    "Feeder State": "OUTAGE (FORCED IDLE)" if slot.is_outage else f"Active (${slot.unit_price:.0f}/u)",
                    "Dispatched Appliances": ", ".join(assigned) if assigned else "IDLE",
                    "Slot Load (kW)": f"{res.slot_loads.get(s_idx, 0)} / {slot.effective_capacity} kW",
                    "Slot Expenditure ($)": f"${res.slot_costs.get(s_idx, 0.0):.2f}",
                })
            st.dataframe(pd.DataFrame(breakdown_rows), hide_index=True, use_container_width=True)


# ---- TAB 4: Combinatorial Scaling Analysis ----
with tab_scaling:
    st.markdown("#### Combinatorial State-Space Scaling Analysis (3 to 7 Appliances)")
    st.caption("Demonstrating exponential growth of uninformed branching versus heuristic pruning under admissibility.")

    scaling_rows: List[Dict[str, object]] = []
    scaling_progress = st.progress(0, text="Benchmarking state-space branching (3 to 7 appliances)...")

    for idx, n_apps in enumerate(range(3, 8)):
        scale_env = create_scaling_environment(n_apps)
        scale_agent = SchedulingAgent(scale_env)
        scale_res = scale_agent.run_all_comparisons()
        scaling_rows.append({
            "num_appliances": n_apps,
            "bfs_expanded": scale_res["BFS"].nodes_expanded,
            "dfs_expanded": scale_res["DFS"].nodes_expanded,
            "astar_expanded": scale_res["A*"].nodes_expanded,
            "bfs_cost": scale_res["BFS"].total_cost,
            "dfs_cost": scale_res["DFS"].total_cost,
            "astar_cost": scale_res["A*"].total_cost,
        })
        scaling_progress.progress((idx + 1) / 5)

    with tempfile.NamedTemporaryFile(suffix=".png", delete=False, dir="outputs") as tmp:
        scaling_plot_path = render_scaling_analysis(scaling_rows, output_path=tmp.name)
    st.image(scaling_plot_path, use_container_width=True)

    st.markdown("##### Empirical Node Expansion Table")
    st.dataframe(pd.DataFrame(scaling_rows), hide_index=True, use_container_width=True)


# ---- TAB 5: Experimental Lab Report ----
with tab_report:
    st.markdown("#### Laboratory Report Documentation")
    report_file = Path("outputs/Lab6_Experimental_Report.md")
    if report_file.exists():
        st.markdown(report_file.read_text(encoding="utf-8"), unsafe_allow_html=True)
    else:
        st.warning("outputs/Lab6_Experimental_Report.md not found. Run main.py to generate live experimental report.")


# ---------------------------------------------------------------------------
# Footer
# ---------------------------------------------------------------------------
st.markdown("---")
st.markdown(
    clean_html("""
    <div style="text-align: center; color: #94a3b8; font-size: 0.8rem; padding: 0.5rem 0 1rem 0;">
        PowerPlan Scheduler &bull; CSC-471-L Artificial Intelligence &bull; Iqra University &bull; Candidate Dua Rehan (67238)
    </div>
    """),
    unsafe_allow_html=True,
)
