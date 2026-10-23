"""
Process Mining and Process Intelligence Analysis Module.

Integrates PM4Py process discovery and comprehensive Pandas-based workflow
analytics, variant discovery, bottleneck detection, and path comparisons.
"""

from typing import Dict, Any, Tuple, List
import pandas as pd
import numpy as np

# PM4Py conditional import
try:
    import pm4py
    PM4PY_AVAILABLE = True
except ImportError:
    PM4PY_AVAILABLE = False


def discover_process_with_pm4py(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Use PM4Py to discover the process model (Directly-Follows Graph).
    Falls back gracefully if PM4Py is not installed.

    Args:
        df: Event-level incident DataFrame.

    Returns:
        Dict with DFG frequencies, start activities, end activities, and status.
    """
    if not PM4PY_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "PM4Py is not installed. Falling back to native Pandas process mining engine.",
            "dfg": {},
            "start_activities": {},
            "end_activities": {},
        }

    try:
        df_pm = pm4py.format_dataframe(
            df.copy(),
            case_id="incident_id",
            activity_key="activity",
            timestamp_key="timestamp",
        )
        dfg, start_activities, end_activities = pm4py.discover_dfg(df_pm)
        # Convert tuple keys to string representation for serialization
        dfg_serialized = {f"{k[0]} -> {k[1]}": v for k, v in dfg.items()}
        return {
            "status": "success",
            "message": "PM4Py process discovery executed successfully.",
            "dfg": dfg_serialized,
            "start_activities": dict(start_activities),
            "end_activities": dict(end_activities),
        }
    except Exception as e:
        return {
            "status": "error",
            "message": f"PM4Py discovery encountered an error: {str(e)}",
            "dfg": {},
            "start_activities": {},
            "end_activities": {},
        }


def get_process_variants(case_df: pd.DataFrame, top_n: int = 10) -> pd.DataFrame:
    """
    Analyze process variants from case-level DataFrame.

    Args:
        case_df: Output from aggregate_cases().
        top_n: Number of top variants to return.

    Returns:
        pd.DataFrame containing variant breakdown.
    """
    total_cases = len(case_df)
    variants = case_df.groupby("variant").agg(
        case_count=("incident_id", "count"),
        avg_resolution_hours=("resolution_time_hours", "mean"),
        median_resolution_hours=("resolution_time_hours", "median"),
        sla_breach_rate=("sla_breached", "mean"),
        reopened_rate=("reopened", "mean"),
        avg_escalations=("escalation_count", "mean"),
    ).reset_index()

    variants["percentage_share"] = (variants["case_count"] / total_cases * 100).round(2)
    variants["avg_resolution_hours"] = variants["avg_resolution_hours"].round(2)
    variants["median_resolution_hours"] = variants["median_resolution_hours"].round(2)
    variants["sla_breach_pct"] = (variants["sla_breach_rate"] * 100).round(2)
    variants["reopened_pct"] = (variants["reopened_rate"] * 100).round(2)
    variants["avg_escalations"] = variants["avg_escalations"].round(2)

    variants = variants.sort_values(by="case_count", ascending=False).reset_index(drop=True)
    variants["variant_id"] = [f"Variant #{i+1}" for i in range(len(variants))]
    
    # Reorder columns
    cols = [
        "variant_id",
        "case_count",
        "percentage_share",
        "avg_resolution_hours",
        "median_resolution_hours",
        "sla_breach_pct",
        "reopened_pct",
        "avg_escalations",
        "variant",
    ]
    return variants[cols].head(top_n)


def get_bottleneck_analysis(transitions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Identify process bottlenecks by ranking transitions based on duration.

    Args:
        transitions_df: Output from extract_transitions().

    Returns:
        pd.DataFrame of top bottleneck transitions.
    """
    bottlenecks = transitions_df.groupby(["source_activity", "target_activity", "transition"]).agg(
        frequency=("incident_id", "count"),
        mean_delay_hours=("duration_hours", "mean"),
        median_delay_hours=("duration_hours", "median"),
        p90_delay_hours=("duration_hours", lambda x: np.percentile(x, 90)),
        total_delay_hours=("duration_hours", "sum"),
    ).reset_index()

    bottlenecks["mean_delay_hours"] = bottlenecks["mean_delay_hours"].round(2)
    bottlenecks["median_delay_hours"] = bottlenecks["median_delay_hours"].round(2)
    bottlenecks["p90_delay_hours"] = bottlenecks["p90_delay_hours"].round(2)
    bottlenecks["total_delay_hours"] = bottlenecks["total_delay_hours"].round(2)

    # Calculate bottleneck score: mean_delay * log1p(frequency)
    bottlenecks["bottleneck_score"] = (
        bottlenecks["mean_delay_hours"] * np.log1p(bottlenecks["frequency"])
    ).round(2)

    return bottlenecks.sort_values(by="mean_delay_hours", ascending=False).reset_index(drop=True)


def get_team_metrics(case_df: pd.DataFrame) -> pd.DataFrame:
    """
    Compute process intelligence metrics grouped by assigned team.

    Args:
        case_df: Output from aggregate_cases().

    Returns:
        pd.DataFrame of team performance metrics.
    """
    team_metrics = case_df.groupby("assigned_team").agg(
        total_incidents=("incident_id", "count"),
        avg_resolution_hours=("resolution_time_hours", "mean"),
        sla_breach_rate=("sla_breached", "mean"),
        escalation_rate=("escalation_count", lambda x: (x > 0).mean()),
        reopened_rate=("reopened", "mean"),
    ).reset_index()

    team_metrics["sla_compliance_pct"] = ((1 - team_metrics["sla_breach_rate"]) * 100).round(2)
    team_metrics["sla_breach_pct"] = (team_metrics["sla_breach_rate"] * 100).round(2)
    team_metrics["avg_resolution_hours"] = team_metrics["avg_resolution_hours"].round(2)
    team_metrics["escalation_pct"] = (team_metrics["escalation_rate"] * 100).round(2)
    team_metrics["reopened_pct"] = (team_metrics["reopened_rate"] * 100).round(2)

    return team_metrics.sort_values(by="sla_breach_pct", ascending=False).reset_index(drop=True)


def compare_happy_vs_inefficient_paths(case_df: pd.DataFrame) -> Dict[str, Any]:
    """
    Compare the primary standard Happy Path against deviated/inefficient paths.

    Args:
        case_df: Output from aggregate_cases().

    Returns:
        Dict with comparative statistics.
    """
    variants = case_df["variant"].value_counts()
    if variants.empty:
        return {}

    happy_variant = variants.index[0]
    happy_cases = case_df[case_df["variant"] == happy_variant]
    deviant_cases = case_df[case_df["variant"] != happy_variant]

    return {
        "happy_path_sequence": happy_variant,
        "happy_path_count": len(happy_cases),
        "happy_path_share_pct": round(len(happy_cases) / len(case_df) * 100, 2),
        "happy_avg_resolution_hours": round(happy_cases["resolution_time_hours"].mean(), 2),
        "happy_sla_breach_pct": round(happy_cases["sla_breached"].mean() * 100, 2),
        "deviant_count": len(deviant_cases),
        "deviant_share_pct": round(len(deviant_cases) / len(case_df) * 100, 2),
        "deviant_avg_resolution_hours": round(deviant_cases["resolution_time_hours"].mean(), 2),
        "deviant_sla_breach_pct": round(deviant_cases["sla_breached"].mean() * 100, 2),
        "resolution_time_multiplier": round(
            deviant_cases["resolution_time_hours"].mean() / max(0.1, happy_cases["resolution_time_hours"].mean()), 2
        ),
    }


def generate_sankey_data(transitions_df: pd.DataFrame, min_frequency: int = 5) -> Dict[str, Any]:
    """
    Prepare nodes and links data for Plotly Sankey diagram.

    Args:
        transitions_df: Output from extract_transitions().
        min_frequency: Threshold to filter out rare transitions.

    Returns:
        Dict ready for go.Sankey(node=..., link=...).
    """
    summary = transitions_df.groupby(["source_activity", "target_activity"]).agg(
        frequency=("incident_id", "count"),
        avg_delay=("duration_hours", "mean"),
    ).reset_index()

    filtered = summary[summary["frequency"] >= min_frequency]

    activities = sorted(list(set(filtered["source_activity"]).union(set(filtered["target_activity"]))))
    act_to_idx = {act: i for i, act in enumerate(activities)}

    sources = [act_to_idx[s] for s in filtered["source_activity"]]
    targets = [act_to_idx[t] for t in filtered["target_activity"]]
    values = filtered["frequency"].tolist()
    custom_labels = [
        f"{s} → {t}<br>Freq: {f} | Avg Delay: {d:.1f}h"
        for s, t, f, d in zip(
            filtered["source_activity"],
            filtered["target_activity"],
            filtered["frequency"],
            filtered["avg_delay"],
        )
    ]

    return {
        "labels": activities,
        "sources": sources,
        "targets": targets,
        "values": values,
        "custom_labels": custom_labels,
    }


if __name__ == "__main__":
    from src.preprocessing import load_and_validate_dataset, aggregate_cases, extract_transitions
    df = load_and_validate_dataset()
    cases = aggregate_cases(df)
    trans = extract_transitions(df)

    pm_res = discover_process_with_pm4py(df)
    print("PM4Py Discovery Status:", pm_res["status"])
    print("Top 3 Variants:\n", get_process_variants(cases, top_n=3))
    print("Top 3 Bottlenecks:\n", get_bottleneck_analysis(trans).head(3))
    print("Comparison:\n", compare_happy_vs_inefficient_paths(cases))
