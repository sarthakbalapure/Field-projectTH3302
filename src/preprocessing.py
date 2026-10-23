"""
Data Preprocessing and Feature Engineering Module.

Handles loading, validating, case-level aggregation, transition extraction,
and leak-free feature extraction for machine learning.
"""

from typing import Tuple, List, Dict
import pandas as pd
import numpy as np


REQUIRED_COLUMNS = [
    "incident_id",
    "activity",
    "timestamp",
    "incident_type",
    "priority",
    "severity",
    "assigned_team",
    "source",
    "status",
    "resolution_time_hours",
    "sla_target_hours",
    "reopened",
    "escalation_count",
]


def load_and_validate_dataset(filepath: str = "data/sample_incidents.csv") -> pd.DataFrame:
    """
    Load raw event log CSV and validate required columns and timestamps.

    Args:
        filepath: Path to the incidents CSV.

    Returns:
        pd.DataFrame with parsed datetime timestamps.
    """
    df = pd.read_csv(filepath)
    missing_cols = [col for col in REQUIRED_COLUMNS if col not in df.columns]
    if missing_cols:
        raise ValueError(f"Dataset missing required columns: {missing_cols}")

    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["incident_id", "timestamp"]).reset_index(drop=True)
    return df


def aggregate_cases(df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate event-level logs into case-level summaries.
    Computes variant sequences, duration, and leak-free early-stage features.

    Args:
        df: Event-level DataFrame.

    Returns:
        pd.DataFrame with 1 row per incident case.
    """
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    cases = []

    for incident_id, group in df.groupby("incident_id", sort=False):
        group = group.sort_values("timestamp")
        first_row = group.iloc[0]
        last_row = group.iloc[-1]

        start_time = group["timestamp"].min()
        end_time = group["timestamp"].max()
        actual_duration = round((end_time - start_time).total_seconds() / 3600.0, 2)
        sla_target = float(first_row["sla_target_hours"])
        sla_breached = 1 if actual_duration > sla_target else 0

        activities_list = group["activity"].tolist()
        variant_str = " -> ".join(activities_list)

        # Early stage feature calculation (Preventing Data Leakage)
        created_time = start_time
        created_hour = created_time.hour
        created_dayofweek = created_time.weekday()
        is_weekend = 1 if created_dayofweek >= 5 else 0
        is_offhours = 1 if (created_hour < 8 or created_hour >= 18) else 0

        # Assessment delay
        assess_events = group[group["activity"] == "Initial Assessment"]
        if not assess_events.empty:
            assess_delay = max(
                0.01,
                (assess_events.iloc[0]["timestamp"] - created_time).total_seconds() / 3600.0,
            )
        else:
            assess_delay = 0.5

        # Assignment delay
        assign_events = group[group["activity"] == "Team Assignment"]
        if not assign_events.empty:
            assign_delay = max(
                0.01,
                (assign_events.iloc[0]["timestamp"] - created_time).total_seconds() / 3600.0,
            )
        else:
            assign_delay = assess_delay + 0.3

        cases.append({
            "incident_id": incident_id,
            "incident_type": first_row["incident_type"],
            "priority": first_row["priority"],
            "severity": first_row["severity"],
            "assigned_team": first_row["assigned_team"],
            "source": first_row["source"],
            "start_time": start_time,
            "end_time": end_time,
            "resolution_time_hours": actual_duration,
            "sla_target_hours": sla_target,
            "sla_breached": sla_breached,
            "sla_compliance": "Breached" if sla_breached == 1 else "Met",
            "reopened": int(first_row["reopened"]),
            "escalation_count": int(first_row["escalation_count"]),
            "event_count": len(group),
            "variant": variant_str,
            # Features available at early stage:
            "initial_assessment_hours": round(assess_delay, 2),
            "time_to_assignment_hours": round(assign_delay, 2),
            "created_hour": created_hour,
            "created_dayofweek": created_dayofweek,
            "is_weekend": is_weekend,
            "is_offhours": is_offhours,
        })

    return pd.DataFrame(cases)


def extract_transitions(df: pd.DataFrame) -> pd.DataFrame:
    """
    Extract step-by-step activity transitions and compute transition durations.

    Args:
        df: Event-level DataFrame.

    Returns:
        pd.DataFrame containing transition records.
    """
    df = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df["timestamp"]):
        df["timestamp"] = pd.to_datetime(df["timestamp"])

    transitions = []
    
    for incident_id, group in df.groupby("incident_id"):
        group = group.sort_values("timestamp")
        activities = group["activity"].values
        timestamps = group["timestamp"].values
        priority = group["priority"].iloc[0]
        team = group["assigned_team"].iloc[0]

        for i in range(len(activities) - 1):
            src_act = activities[i]
            tgt_act = activities[i + 1]
            t_src = pd.to_datetime(timestamps[i])
            t_tgt = pd.to_datetime(timestamps[i + 1])
            duration_hours = max(0.001, (t_tgt - t_src).total_seconds() / 3600.0)

            transitions.append({
                "incident_id": incident_id,
                "source_activity": src_act,
                "target_activity": tgt_act,
                "transition": f"{src_act} -> {tgt_act}",
                "duration_hours": round(duration_hours, 2),
                "priority": priority,
                "assigned_team": team,
            })

    return pd.DataFrame(transitions)


def get_transition_summary(transitions_df: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate transitions to compute frequencies and duration metrics.

    Args:
        transitions_df: Output from extract_transitions().

    Returns:
        pd.DataFrame sorted by transition frequency.
    """
    summary = transitions_df.groupby(["source_activity", "target_activity", "transition"]).agg(
        frequency=("incident_id", "count"),
        mean_duration_hours=("duration_hours", "mean"),
        median_duration_hours=("duration_hours", "median"),
        p90_duration_hours=("duration_hours", lambda x: np.percentile(x, 90)),
        max_duration_hours=("duration_hours", "max"),
    ).reset_index()

    summary["mean_duration_hours"] = summary["mean_duration_hours"].round(2)
    summary["median_duration_hours"] = summary["median_duration_hours"].round(2)
    summary["p90_duration_hours"] = summary["p90_duration_hours"].round(2)
    summary["max_duration_hours"] = summary["max_duration_hours"].round(2)
    
    return summary.sort_values(by="frequency", ascending=False).reset_index(drop=True)


if __name__ == "__main__":
    df = load_and_validate_dataset()
    case_df = aggregate_cases(df)
    print(f"Aggregated {len(case_df)} cases.")
    print(f"Overall SLA breach rate: {case_df['sla_breached'].mean():.2%}")
    trans_df = extract_transitions(df)
    summary = get_transition_summary(trans_df)
    print(f"Top transitions:\n{summary.head(5)}")
