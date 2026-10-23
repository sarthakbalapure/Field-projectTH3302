"""
AI-Powered IT Incident Process Intelligence
Interactive Streamlit Application
"""

import os
import sys
from datetime import datetime
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# Add repository root to system path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from src.data_generator import generate_incident_dataset, save_dataset, SLA_TARGETS
from src.preprocessing import (
    load_and_validate_dataset,
    aggregate_cases,
    extract_transitions,
    get_transition_summary,
)
from src.process_analysis import (
    discover_process_with_pm4py,
    get_process_variants,
    get_bottleneck_analysis,
    get_team_metrics,
    compare_happy_vs_inefficient_paths,
    generate_sankey_data,
    PM4PY_AVAILABLE,
)
from src.model import (
    train_and_evaluate_model,
    save_model,
    load_model,
    predict_incident_risk,
    MODEL_PATH,
)
from src.recommendations import generate_process_recommendations

DATA_PATH = "data/sample_incidents.csv"

# Page Configuration
st.set_page_config(
    page_title="IT Incident Process Intelligence",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom Styling
st.markdown("""
<style>
    .metric-card {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 18px 22px;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.25);
    }
    .metric-title {
        color: #94a3b8;
        font-size: 0.85rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.05em;
        margin-bottom: 6px;
    }
    .metric-val {
        color: #f8fafc;
        font-size: 1.85rem;
        font-weight: 700;
    }
    .metric-sub {
        color: #38bdf8;
        font-size: 0.80rem;
        margin-top: 4px;
    }
    .rec-card {
        background-color: #0f172a;
        border-radius: 10px;
        border-left: 5px solid #38bdf8;
        padding: 16px 20px;
        margin-bottom: 16px;
    }
    .rec-card-critical {
        border-left-color: #ef4444;
        background-color: #1e1b24;
    }
    .rec-card-high {
        border-left-color: #f97316;
        background-color: #1c1917;
    }
    .rec-card-medium {
        border-left-color: #38bdf8;
        background-color: #0f172a;
    }
    .badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 9999px;
        font-size: 0.75rem;
        font-weight: 600;
    }
    .badge-critical { background-color: #ef4444; color: white; }
    .badge-high { background-color: #f97316; color: white; }
    .badge-medium { background-color: #0284c7; color: white; }
    .stTabs [data-baseweb="tab-list"] {
        gap: 12px;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 10px 18px;
        border-radius: 8px;
        font-weight: 500;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_data(show_spinner=False)
def load_data():
    """Load or generate the incident lifecycle dataset."""
    if not os.path.exists(DATA_PATH):
        df_gen = generate_incident_dataset(n_cases=1200, seed=42)
        save_dataset(df_gen, DATA_PATH)
    raw_df = load_and_validate_dataset(DATA_PATH)
    case_df = aggregate_cases(raw_df)
    transitions_df = extract_transitions(raw_df)
    return raw_df, case_df, transitions_df


@st.cache_resource(show_spinner=False)
def get_or_train_model(case_df: pd.DataFrame):
    """Load or train the SLA risk prediction model."""
    if os.path.exists(MODEL_PATH):
        try:
            return load_model(MODEL_PATH)
        except Exception:
            pass
    metrics, pipeline = train_and_evaluate_model(case_df)
    save_model(pipeline, metrics, MODEL_PATH)
    return load_model(MODEL_PATH)


# Initialize Data & Models
raw_df, case_df, transitions_df = load_data()
model_bundle = get_or_train_model(case_df)

# Sidebar Filters
st.sidebar.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=64)
st.sidebar.title("IT Incident Intelligence")
st.sidebar.caption("Process Mining & Predictive SLA Intelligence")

st.sidebar.markdown("---")
st.sidebar.subheader("🎯 Global Filters")

# Priority filter
all_priorities = sorted(case_df["priority"].unique())
selected_priorities = st.sidebar.multiselect(
    "Priority",
    options=all_priorities,
    default=all_priorities,
)

# Assigned Team filter
all_teams = sorted(case_df["assigned_team"].unique())
selected_teams = st.sidebar.multiselect(
    "Assigned Team",
    options=all_teams,
    default=all_teams,
)

# Incident Type filter
all_types = sorted(case_df["incident_type"].unique())
selected_types = st.sidebar.multiselect(
    "Incident Type",
    options=all_types,
    default=all_types,
)

# SLA Status filter
sla_options = ["All", "SLA Breached", "SLA Met"]
sla_filter = st.sidebar.selectbox("SLA Status", options=sla_options, index=0)

# Filtered DataFrame
filtered_cases = case_df[
    (case_df["priority"].isin(selected_priorities)) &
    (case_df["assigned_team"].isin(selected_teams)) &
    (case_df["incident_type"].isin(selected_types))
].copy()

if sla_filter == "SLA Breached":
    filtered_cases = filtered_cases[filtered_cases["sla_breached"] == 1]
elif sla_filter == "SLA Met":
    filtered_cases = filtered_cases[filtered_cases["sla_breached"] == 0]

filtered_case_ids = set(filtered_cases["incident_id"])
filtered_raw = raw_df[raw_df["incident_id"].isin(filtered_case_ids)].copy()
filtered_transitions = transitions_df[transitions_df["incident_id"].isin(filtered_case_ids)].copy()

st.sidebar.markdown("---")
st.sidebar.subheader("⚙️ System Status")
st.sidebar.markdown(f"**PM4Py Engine:** {'🟢 Enabled (v2.7+)' if PM4PY_AVAILABLE else '🟡 Pandas Fallback'}")
st.sidebar.markdown(f"**Active Cases:** `{len(filtered_cases):,} / {len(case_df):,}`")
st.sidebar.markdown(f"**Total Events:** `{len(filtered_raw):,}`")

if st.sidebar.button("🔄 Regenerate Dataset"):
    df_new = generate_incident_dataset(n_cases=1200, seed=int(datetime.now().timestamp()) % 1000)
    save_dataset(df_new, DATA_PATH)
    st.cache_data.clear()
    st.cache_resource.clear()
    st.rerun()

if st.sidebar.button("🧠 Retrain ML Model"):
    metrics_new, pipeline_new = train_and_evaluate_model(case_df)
    save_model(pipeline_new, metrics_new, MODEL_PATH)
    st.cache_resource.clear()
    st.sidebar.success("Model retrained successfully!")
    st.rerun()

# Main Application Header
col_header_1, col_header_2 = st.columns([3, 1])
with col_header_1:
    st.title("⚡ AI-Powered IT Incident Process Intelligence")
    st.markdown(
        "End-to-end incident lifecycle process mining, bottleneck diagnostics, "
        "predictive SLA breach modeling, and operational recommendations."
    )
with col_header_2:
    st.markdown("<br>", unsafe_allow_html=True)
    t_min = str(raw_df["timestamp"].min())[:10]
    t_max = str(raw_df["timestamp"].max())[:10]
    st.info(f"📅 Log Window: {t_min} to {t_max}")

tab_options = [
    "📊 Executive Overview",
    "🔄 Process Analysis",
    "⏳ Bottleneck Analysis",
    "🤖 SLA Risk Prediction",
    "💡 AI Recommendations",
    "🔍 Incident Explorer",
]

# Support direct tab deep-linking via ?tab= query parameter
qp_tab = st.query_params.get("tab", None)
default_idx = 0
if qp_tab is not None:
    try:
        val = int(qp_tab)
        if 0 <= val < len(tab_options):
            default_idx = val
    except ValueError:
        for idx, opt_name in enumerate(tab_options):
            if qp_tab.lower() in opt_name.lower():
                default_idx = idx
                break

selected_tab = st.radio(
    "Navigation Tabs",
    options=tab_options,
    index=default_idx,
    horizontal=True,
    label_visibility="collapsed",
)

st.markdown("<hr style='margin-top: 4px; margin-bottom: 20px; border-color: #334155;'>", unsafe_allow_html=True)

# -------------------------------------------------------------
# TAB 1: EXECUTIVE OVERVIEW
# -------------------------------------------------------------
if selected_tab == tab_options[0]:
    st.subheader("Executive KPI Summary")
    
    if filtered_cases.empty:
        st.warning("No incidents match the selected filters. Please expand your filter criteria.")
    else:
        total_inc = len(filtered_cases)
        avg_res = filtered_cases["resolution_time_hours"].mean()
        breach_rate = filtered_cases["sla_breached"].mean() * 100
        reopen_rate = filtered_cases["reopened"].mean() * 100
        escalation_rate = (filtered_cases["escalation_count"] > 0).mean() * 100

        k1, k2, k3, k4, k5 = st.columns(5)
        with k1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Total Incidents</div>
                <div class="metric-val">{total_inc:,}</div>
                <div class="metric-sub">{len(filtered_raw):,} lifecycle events</div>
            </div>
            """, unsafe_allow_html=True)
        with k2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Avg Resolution</div>
                <div class="metric-val">{avg_res:.1f}h</div>
                <div class="metric-sub">Median: {filtered_cases['resolution_time_hours'].median():.1f}h</div>
            </div>
            """, unsafe_allow_html=True)
        with k3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">SLA Compliance</div>
                <div class="metric-val">{(100 - breach_rate):.1f}%</div>
                <div class="metric-sub">{breach_rate:.1f}% breach rate</div>
            </div>
            """, unsafe_allow_html=True)
        with k4:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Reopened Rate</div>
                <div class="metric-val">{reopen_rate:.1f}%</div>
                <div class="metric-sub">{filtered_cases['reopened'].sum()} reopened cases</div>
            </div>
            """, unsafe_allow_html=True)
        with k5:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-title">Escalation Rate</div>
                <div class="metric-val">{escalation_rate:.1f}%</div>
                <div class="metric-sub">{(filtered_cases['escalation_count'] > 0).sum()} escalated cases</div>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<br>", unsafe_allow_html=True)
        row2_col1, row2_col2 = st.columns([1, 1])

        with row2_col1:
            st.markdown("#### SLA Compliance by Incident Type")
            comp_by_type = filtered_cases.groupby("incident_type").agg(
                Met=("sla_breached", lambda x: (x == 0).sum()),
                Breached=("sla_breached", lambda x: (x == 1).sum()),
            ).reset_index()
            fig_type = px.bar(
                comp_by_type,
                x="incident_type",
                y=["Met", "Breached"],
                barmode="stack",
                color_discrete_map={"Met": "#10b981", "Breached": "#ef4444"},
                title="Resolution Outcomes Across Incident Types",
            )
            fig_type.update_layout(xaxis_title="", yaxis_title="Number of Incidents", template="plotly_dark", height=380)
            st.plotly_chart(fig_type, use_container_width=True)

        with row2_col2:
            st.markdown("#### Priority Distribution & SLA Target Compliance")
            prio_summary = filtered_cases.groupby("priority").agg(
                total=("incident_id", "count"),
                breach_pct=("sla_breached", lambda x: round(x.mean() * 100, 1)),
            ).reset_index()
            fig_prio = px.pie(
                prio_summary,
                values="total",
                names="priority",
                hole=0.45,
                color_discrete_sequence=px.colors.sequential.Plasma,
                title="Incident Share by Priority Tier",
            )
            fig_prio.update_layout(template="plotly_dark", height=380)
            st.plotly_chart(fig_prio, use_container_width=True)

        # Team Performance Snapshot
        st.markdown("#### Team Operational Benchmark")
        team_bench = get_team_metrics(filtered_cases)
        st.dataframe(
            team_bench.rename(columns={
                "assigned_team": "Team",
                "total_incidents": "Volume",
                "avg_resolution_hours": "Avg Turnaround (Hrs)",
                "sla_compliance_pct": "SLA Met %",
                "sla_breach_pct": "SLA Breached %",
                "escalation_pct": "Escalated %",
                "reopened_pct": "Reopened %",
            }),
            use_container_width=True,
            hide_index=True,
        )

# -------------------------------------------------------------
# TAB 2: PROCESS ANALYSIS
# -------------------------------------------------------------
elif selected_tab == tab_options[1]:
    st.subheader("Process Discovery & Variant Intelligence")
    st.markdown(
        "Analyze discovered process flows, identify deviations from standard operating procedures, "
        "and track activity transition frequencies."
    )

    if filtered_transitions.empty:
        st.warning("Insufficient transitions under current filter selection.")
    else:
        # Comparison Banner
        comp = compare_happy_vs_inefficient_paths(filtered_cases)
        if comp:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.info(f"**Happy Path Share:** {comp['happy_path_share_pct']}% ({comp['happy_path_count']} cases)\n\nAvg Resolution: **{comp['happy_avg_resolution_hours']}h** | SLA Breach: **{comp['happy_sla_breach_pct']}%**")
            with c2:
                st.error(f"**Deviant / Inefficient Share:** {comp['deviant_share_pct']}% ({comp['deviant_count']} cases)\n\nAvg Resolution: **{comp['deviant_avg_resolution_hours']}h** | SLA Breach: **{comp['deviant_sla_breach_pct']}%**")
            with c3:
                st.warning(f"**Inefficiency Penalty:**\n\nDeviant paths take **{comp['resolution_time_multiplier']}x** longer to resolve than the standard happy path workflow.")

        # Interactive Sankey Flow Diagram
        st.markdown("#### Process Flow Map (Directly-Follows Transition Flow)")
        sankey_data = generate_sankey_data(filtered_transitions, min_frequency=2)
        
        if sankey_data["labels"]:
            fig_sankey = go.Figure(data=[go.Sankey(
                node=dict(
                    pad=18,
                    thickness=24,
                    line=dict(color="#000", width=0.5),
                    label=sankey_data["labels"],
                    color="#38bdf8",
                ),
                link=dict(
                    source=sankey_data["sources"],
                    target=sankey_data["targets"],
                    value=sankey_data["values"],
                    customdata=sankey_data["custom_labels"],
                    hovertemplate="%{customdata}<extra></extra>",
                    color="rgba(56, 189, 248, 0.25)",
                )
            )])
            fig_sankey.update_layout(
                title_text="Incident Lifecycle Activity Transitions (Flow Volume & Waiting Times)",
                font_size=12,
                template="plotly_dark",
                height=480,
            )
            st.plotly_chart(fig_sankey, use_container_width=True)

        # Process Variants Breakdown
        st.markdown("#### Discovered Process Variants")
        variants_df = get_process_variants(filtered_cases, top_n=8)
        st.dataframe(
            variants_df.rename(columns={
                "variant_id": "Variant",
                "case_count": "Cases",
                "percentage_share": "Share %",
                "avg_resolution_hours": "Avg Turnaround (h)",
                "median_resolution_hours": "Median (h)",
                "sla_breach_pct": "SLA Breach %",
                "reopened_pct": "Reopen %",
                "avg_escalations": "Avg Escalations",
                "variant": "Lifecycle Activity Sequence",
            }),
            use_container_width=True,
            hide_index=True,
        )

# -------------------------------------------------------------
# TAB 3: BOTTLENECK ANALYSIS
# -------------------------------------------------------------
elif selected_tab == tab_options[2]:
    st.subheader("Process Bottlenecks & Turnaround Latency Diagnostics")
    st.markdown(
        "Identify high-latency transitions where incidents spend the most time waiting in queues, "
        "examine resolution time distributions, and isolate escalation delays."
    )

    if filtered_transitions.empty:
        st.warning("Insufficient transitions under current filter selection.")
    else:
        bottlenecks = get_bottleneck_analysis(filtered_transitions)
        
        b_col1, b_col2 = st.columns([3, 2])
        with b_col1:
            st.markdown("#### Top Activity Transition Bottlenecks (Mean Delay)")
            top_b = bottlenecks.head(7)
            fig_bottle = px.bar(
                top_b,
                x="mean_delay_hours",
                y="transition",
                orientation="h",
                color="mean_delay_hours",
                color_continuous_scale="Reds",
                title="Longest Average Transition Waiting Times (Hours)",
                text="mean_delay_hours",
            )
            fig_bottle.update_layout(
                yaxis={"categoryorder": "total ascending", "title": ""},
                xaxis_title="Average Delay (Hours)",
                template="plotly_dark",
                height=400,
            )
            st.plotly_chart(fig_bottle, use_container_width=True)

        with b_col2:
            st.markdown("#### Bottleneck Summary Table")
            st.dataframe(
                bottlenecks.head(6)[["transition", "frequency", "mean_delay_hours", "p90_delay_hours", "total_delay_hours"]].rename(columns={
                    "transition": "Transition",
                    "frequency": "Occurrences",
                    "mean_delay_hours": "Avg Delay (h)",
                    "p90_delay_hours": "P90 (h)",
                    "total_delay_hours": "Total Wait (h)",
                }),
                use_container_width=True,
                hide_index=True,
            )

        st.markdown("<br>", unsafe_allow_html=True)
        dist_col1, dist_col2 = st.columns(2)
        with dist_col1:
            st.markdown("#### Resolution Time Distribution by Assigned Team")
            fig_box_team = px.box(
                filtered_cases,
                x="assigned_team",
                y="resolution_time_hours",
                color="assigned_team",
                points="outliers",
                title="Resolution Time Spread Across Teams",
            )
            fig_box_team.update_layout(
                xaxis_title="",
                yaxis_title="Resolution Time (Hours)",
                template="plotly_dark",
                showlegend=False,
                height=380,
            )
            st.plotly_chart(fig_box_team, use_container_width=True)

        with dist_col2:
            st.markdown("#### Impact of Escalation Count on Turnaround Time")
            fig_esc = px.box(
                filtered_cases,
                x="escalation_count",
                y="resolution_time_hours",
                color="escalation_count",
                title="Turnaround vs Escalation Count",
            )
            fig_esc.update_layout(
                xaxis_title="Escalations Count",
                yaxis_title="Resolution Time (Hours)",
                template="plotly_dark",
                showlegend=False,
                height=380,
            )
            st.plotly_chart(fig_esc, use_container_width=True)

# -------------------------------------------------------------
# TAB 4: SLA RISK PREDICTION
# -------------------------------------------------------------
elif selected_tab == tab_options[3]:
    st.subheader("Machine Learning SLA Breach Risk Engine")
    st.markdown(
        "Predict whether incoming IT incidents are likely to breach SLA targets using an explainable "
        "Random Forest model trained strictly on early-lifecycle indicators to prevent data leakage."
    )

    metrics = model_bundle["metrics"]

    # Evaluation KPI row
    m1, m2, m3, m4, m5 = st.columns(5)
    with m1:
        st.metric("Test Accuracy", f"{metrics['accuracy']:.2%}")
    with m2:
        st.metric("Precision", f"{metrics['precision']:.2%}")
    with m3:
        st.metric("Recall", f"{metrics['recall']:.2%}")
    with m4:
        st.metric("F1-Score", f"{metrics['f1_score']:.2%}")
    with m5:
        st.metric("ROC-AUC", f"{metrics['roc_auc']:.2%}")

    st.markdown("<br>", unsafe_allow_html=True)
    m_col1, m_col2 = st.columns([1, 1])

    with m_col1:
        st.markdown("#### Confusion Matrix (Test Set: N = 240)")
        cm = np.array(metrics["confusion_matrix"])
        fig_cm = px.imshow(
            cm,
            labels=dict(x="Predicted Class", y="Actual Class", color="Incidents"),
            x=["Met SLA (0)", "Breached SLA (1)"],
            y=["Met SLA (0)", "Breached SLA (1)"],
            text_auto=True,
            color_continuous_scale="Blues",
            title="Model Confusion Matrix",
        )
        fig_cm.update_layout(template="plotly_dark", height=380)
        st.plotly_chart(fig_cm, use_container_width=True)

    with m_col2:
        st.markdown("#### Key Predictive Features (Top Early Indicators)")
        feat_df = pd.DataFrame(metrics["feature_importances"][:8])
        fig_imp = px.bar(
            feat_df,
            x="importance",
            y="feature",
            orientation="h",
            color="importance",
            color_continuous_scale="Teal",
            title="Random Forest Feature Importance",
        )
        fig_imp.update_layout(
            yaxis={"categoryorder": "total ascending", "title": ""},
            xaxis_title="Relative Feature Weight",
            template="plotly_dark",
            height=380,
        )
        st.plotly_chart(fig_imp, use_container_width=True)

    st.markdown("---")
    st.markdown("### 🎯 Live Incident SLA Risk Simulator")
    st.caption("Input incident attributes to predict the probability of SLA breach in real time.")

    sim_col1, sim_col2, sim_col3 = st.columns(3)
    with sim_col1:
        sim_priority = st.selectbox("Priority", options=sorted(case_df["priority"].unique()), index=0)
        sim_severity = st.selectbox("Severity", options=["Critical", "Major", "Moderate", "Minor"], index=0)
        sim_type = st.selectbox("Incident Type", options=sorted(case_df["incident_type"].unique()), index=1)
    with sim_col2:
        sim_team = st.selectbox("Assigned Team", options=sorted(case_df["assigned_team"].unique()), index=3)
        sim_source = st.selectbox("Reporting Source", options=sorted(case_df["source"].unique()), index=0)
        sim_hour = st.slider("Creation Hour (0-23)", min_value=0, max_value=23, value=14)
    with sim_col3:
        sim_assess_delay = st.slider("Initial Assessment Duration (Hours)", min_value=0.1, max_value=8.0, value=0.75, step=0.1)
        sim_assign_delay = st.slider("Time to Assignment (Hours)", min_value=0.1, max_value=8.0, value=1.2, step=0.1)
        sim_weekend = st.radio("Is Weekend?", options=[0, 1], format_func=lambda x: "Yes" if x == 1 else "No", horizontal=True)

    is_offhours = 1 if (sim_hour < 8 or sim_hour >= 18) else 0

    input_payload = {
        "incident_type": sim_type,
        "priority": sim_priority,
        "severity": sim_severity,
        "assigned_team": sim_team,
        "source": sim_source,
        "initial_assessment_hours": sim_assess_delay,
        "time_to_assignment_hours": sim_assign_delay,
        "created_hour": sim_hour,
        "created_dayofweek": 5 if sim_weekend == 1 else 2,
        "is_weekend": sim_weekend,
        "is_offhours": is_offhours,
    }

    pred_res = predict_incident_risk(model_bundle, input_payload)
    prob_pct = pred_res["breach_probability"] * 100

    st.markdown("<br>", unsafe_allow_html=True)
    gauge_col, desc_col = st.columns([1, 1])

    with gauge_col:
        fig_gauge = go.Figure(go.Indicator(
            mode="gauge+number",
            value=prob_pct,
            title={'text': "Predicted SLA Breach Probability (%)"},
            gauge={
                'axis': {'range': [0, 100]},
                'bar': {'color': "#ef4444" if prob_pct > 65 else ("#f97316" if prob_pct > 40 else "#10b981")},
                'steps': [
                    {'range': [0, 40], 'color': "rgba(16, 185, 129, 0.2)"},
                    {'range': [40, 65], 'color': "rgba(249, 115, 22, 0.2)"},
                    {'range': [65, 100], 'color': "rgba(239, 68, 68, 0.2)"},
                ],
                'threshold': {
                    'line': {'color': "white", 'width': 4},
                    'thickness': 0.75,
                    'value': 50,
                }
            }
        ))
        fig_gauge.update_layout(template="plotly_dark", height=280)
        st.plotly_chart(fig_gauge, use_container_width=True)

    with desc_col:
        st.markdown("<br>", unsafe_allow_html=True)
        risk_color = "red" if prob_pct > 65 else ("orange" if prob_pct > 40 else "green")
        st.markdown(f"### Predicted Risk Level: :{risk_color}[{pred_res['risk_level']}]")
        st.markdown(f"**Target SLA Window:** `{SLA_TARGETS.get(sim_priority, 24)} hours`")
        if pred_res["predicted_breach"] == 1:
            st.error(
                "⚠️ **High Probability of SLA Violation.** This incident exhibits risk factors "
                "such as high priority target constraints, queue wait times, and bottlenecked team allocation. "
                "Immediate fast-track routing or senior engineer escalation is advised."
            )
        else:
            st.success(
                "✅ **Low Breach Probability.** Incident attributes match standard operational parameters. "
                "Standard queue handling is expected to meet the SLA deadline."
            )

# -------------------------------------------------------------
# TAB 5: AI RECOMMENDATIONS
# -------------------------------------------------------------
elif selected_tab == tab_options[4]:
    st.subheader("💡 Explainable AI Operational Recommendations")
    st.markdown(
        "Transparent, data-backed optimization insights generated directly from process mining delays, "
        "reopening statistics, and team bottlenecks."
    )

    recs = generate_process_recommendations(
        filtered_cases,
        filtered_transitions,
        get_bottleneck_analysis(filtered_transitions),
        get_team_metrics(filtered_cases),
    )

    if not recs:
        st.info("No critical process violations found under current filtered segment.")
    else:
        sev_filter = st.selectbox("Filter Recommendations by Severity", ["All", "Critical", "High", "Medium"])
        displayed_recs = [r for r in recs if sev_filter == "All" or r["severity"] == sev_filter]

        for r in displayed_recs:
            sev_class = r["severity"].lower()
            badge_class = f"badge-{sev_class}"
            card_class = f"rec-card-{sev_class}"

            st.markdown(f"""
            <div class="rec-card {card_class}">
                <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                    <span style="font-weight: 700; font-size: 1.15rem; color: #f8fafc;">{r['title']}</span>
                    <span class="badge {badge_class}">{r['severity'].upper()} PRIORITY</span>
                </div>
                <div style="color: #cbd5e1; font-size: 0.85rem; margin-bottom: 12px;"><strong>Category:</strong> {r['category']} | <strong>ID:</strong> {r['id']}</div>
                <div style="margin-bottom: 8px; color: #e2e8f0;"><strong>🔍 Observed Metric:</strong> {r['finding']}</div>
                <div style="margin-bottom: 8px; color: #38bdf8;"><strong>🛠️ Recommended Action:</strong> {r['actionable_recommendation']}</div>
                <div style="color: #34d399; font-weight: 500;"><strong>📈 Expected Impact:</strong> {r['expected_impact']}</div>
            </div>
            """, unsafe_allow_html=True)

            with st.expander(f"📊 View Supporting Quantitative Metrics for {r['id']}"):
                m_cols = st.columns(len(r["supporting_metrics"]))
                for col, (k, v) in zip(m_cols, r["supporting_metrics"].items()):
                    with col:
                        st.metric(k, v)

# -------------------------------------------------------------
# TAB 6: INCIDENT EXPLORER
# -------------------------------------------------------------
elif selected_tab == tab_options[5]:
    st.subheader("🔍 IT Incident Lifecycle Explorer")
    st.markdown("Search individual incidents, inspect detailed chronological event histories, and review audit trails.")

    search_id = st.text_input("🔎 Search by Incident ID (e.g., INC-10042)", "").strip()
    
    if search_id:
        table_cases = filtered_cases[filtered_cases["incident_id"].str.contains(search_id, case=False)]
    else:
        table_cases = filtered_cases

    st.markdown(f"Showing **{len(table_cases):,}** matching incidents:")
    
    st.dataframe(
        table_cases[[
            "incident_id", "priority", "severity", "incident_type", "assigned_team",
            "sla_compliance", "resolution_time_hours", "sla_target_hours", "reopened", "escalation_count"
        ]].rename(columns={
            "incident_id": "Incident ID",
            "priority": "Priority",
            "severity": "Severity",
            "incident_type": "Type",
            "assigned_team": "Team",
            "sla_compliance": "SLA Status",
            "resolution_time_hours": "Duration (h)",
            "sla_target_hours": "Target (h)",
            "reopened": "Reopened",
            "escalation_count": "Escalations",
        }),
        use_container_width=True,
        hide_index=True,
    )

    st.markdown("---")
    st.markdown("#### 📜 Incident Lifecycle Timeline Inspector")

    selected_inc_id = st.selectbox(
        "Select an Incident to Inspect Detailed Event History:",
        options=table_cases["incident_id"].head(50).tolist() if not table_cases.empty else [],
    )

    if selected_inc_id:
        inc_events = raw_df[raw_df["incident_id"] == selected_inc_id].sort_values("timestamp")
        inc_meta = filtered_cases[filtered_cases["incident_id"] == selected_inc_id].iloc[0]

        meta_c1, meta_c2, meta_c3, meta_c4 = st.columns(4)
        meta_c1.metric("Priority", inc_meta["priority"])
        meta_c2.metric("Turnaround Time", f"{inc_meta['resolution_time_hours']} hrs")
        meta_c3.metric("SLA Status", inc_meta["sla_compliance"])
        meta_c4.metric("Lifecycle Events", len(inc_events))

        st.markdown("**Chronological Event Trace:**")
        st.dataframe(
            inc_events[["timestamp", "activity", "status", "assigned_team"]].rename(columns={
                "timestamp": "Timestamp",
                "activity": "Activity Name",
                "status": "Ticket Status",
                "assigned_team": "Acting Team",
            }),
            use_container_width=True,
            hide_index=True,
        )
