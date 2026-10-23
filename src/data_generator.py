"""
Synthetic IT Incident Event Log Generator.

Generates realistic ITIL incident lifecycle event logs with configurable
variations, delays, escalations, reopenings, and SLA performance metrics.
"""

import os
from datetime import datetime, timedelta
import numpy as np
import pandas as pd


# SLA Targets by Priority (in hours)
SLA_TARGETS = {
    "P1 - Critical": 4.0,
    "P2 - High": 12.0,
    "P3 - Medium": 24.0,
    "P4 - Low": 72.0,
}

INCIDENT_TYPES = [
    "Infrastructure Outage",
    "Database Performance",
    "Software Bug",
    "Access & Identity",
    "Network Connectivity",
    "Security Alert",
]

PRIORITIES = ["P1 - Critical", "P2 - High", "P3 - Medium", "P4 - Low"]
PRIORITY_PROBS = [0.12, 0.28, 0.42, 0.18]

SEVERITIES = ["Critical", "Major", "Moderate", "Minor"]

TEAMS = [
    "Service Desk",
    "Network Ops",
    "Cloud Infra",
    "Database Admin",
    "SecOps",
    "App Support",
]

SOURCES = [
    "Monitoring Alert",
    "User Portal",
    "Email",
    "Phone Call",
    "Automated Script",
]


def generate_incident_dataset(n_cases: int = 1200, seed: int = 42) -> pd.DataFrame:
    """
    Generate a synthetic IT incident dataset with event log granularity.

    Args:
        n_cases: Number of unique incident cases to generate (default: 1200).
        seed: Random seed for reproducibility.

    Returns:
        pd.DataFrame containing event log records.
    """
    np.random.seed(seed)
    records = []

    # Timeline span: incidents created across past 90 days
    base_start_date = datetime(2026, 7, 1, 8, 0, 0)
    max_days_offset = 80

    for i in range(1, n_cases + 1):
        incident_id = f"INC-{10000 + i}"
        
        # Incident Attributes
        priority = np.random.choice(PRIORITIES, p=PRIORITY_PROBS)
        sla_target_hours = SLA_TARGETS[priority]

        # Correlate severity with priority
        if priority == "P1 - Critical":
            severity = np.random.choice(["Critical", "Major"], p=[0.75, 0.25])
        elif priority == "P2 - High":
            severity = np.random.choice(["Critical", "Major", "Moderate"], p=[0.20, 0.65, 0.15])
        elif priority == "P3 - Medium":
            severity = np.random.choice(["Major", "Moderate", "Minor"], p=[0.10, 0.70, 0.20])
        else:
            severity = np.random.choice(["Moderate", "Minor"], p=[0.25, 0.75])

        incident_type = np.random.choice(INCIDENT_TYPES)
        source = np.random.choice(SOURCES, p=[0.35, 0.30, 0.15, 0.12, 0.08])

        # Team affinity by incident type
        if incident_type == "Database Performance":
            assigned_team = np.random.choice(["Database Admin", "Cloud Infra", "App Support"], p=[0.70, 0.20, 0.10])
        elif incident_type == "Infrastructure Outage":
            assigned_team = np.random.choice(["Cloud Infra", "Network Ops", "Database Admin"], p=[0.60, 0.30, 0.10])
        elif incident_type == "Network Connectivity":
            assigned_team = np.random.choice(["Network Ops", "Cloud Infra", "Service Desk"], p=[0.75, 0.15, 0.10])
        elif incident_type == "Security Alert":
            assigned_team = np.random.choice(["SecOps", "Cloud Infra", "App Support"], p=[0.80, 0.10, 0.10])
        elif incident_type == "Access & Identity":
            assigned_team = np.random.choice(["Service Desk", "SecOps", "App Support"], p=[0.65, 0.25, 0.10])
        else:  # Software Bug
            assigned_team = np.random.choice(["App Support", "Cloud Infra", "Service Desk"], p=[0.65, 0.20, 0.15])

        # Incident Creation Timestamp
        created_day_offset = np.random.uniform(0, max_days_offset)
        created_hour_offset = np.random.uniform(0, 24)
        incident_created_time = base_start_date + timedelta(days=created_day_offset, hours=created_hour_offset)
        is_weekend = incident_created_time.weekday() >= 5
        is_night = incident_created_time.hour < 7 or incident_created_time.hour > 19

        # Process Path Variation Determination
        rand_path = np.random.rand()
        has_reopen = False
        escalation_count = 0

        # Paths:
        # 1: Standard Happy Path (55%)
        # 2: Single Escalation (22%)
        # 3: Multi Escalation (8%)
        # 4: Reopened Incident (11%)
        # 5: Quick Resolution (4%)
        if rand_path < 0.55:
            path_type = "standard"
        elif rand_path < 0.77:
            path_type = "single_escalation"
            escalation_count = 1
        elif rand_path < 0.85:
            path_type = "multi_escalation"
            escalation_count = np.random.choice([2, 3], p=[0.8, 0.2])
        elif rand_path < 0.96:
            path_type = "reopened"
            has_reopen = True
            escalation_count = np.random.choice([0, 1], p=[0.6, 0.4])
        else:
            path_type = "quick_resolution"

        # Construct activities sequence with realistic durations
        current_time = incident_created_time
        events = []

        # 1. Incident Created
        events.append({
            "activity": "Incident Created",
            "timestamp": current_time,
            "status": "New",
            "assigned_team": assigned_team,
        })

        # Duration to Initial Assessment (hours)
        assess_delay = np.random.lognormal(mean=-0.8, sigma=0.5)  # median ~0.45h
        if is_weekend or is_night:
            assess_delay *= 2.2  # off-hours triage lag
        if priority == "P1 - Critical":
            assess_delay *= 0.35  # urgent priority triage is accelerated
        current_time += timedelta(hours=assess_delay)

        # 2. Initial Assessment
        events.append({
            "activity": "Initial Assessment",
            "timestamp": current_time,
            "status": "In Progress",
            "assigned_team": assigned_team,
        })

        if path_type == "quick_resolution":
            # Direct resolution after assessment (e.g. password reset / fast fix)
            quick_res_delay = np.random.uniform(0.2, 1.5)
            current_time += timedelta(hours=quick_res_delay)
            events.append({
                "activity": "Resolution",
                "timestamp": current_time,
                "status": "Resolved",
                "assigned_team": assigned_team,
            })
            close_delay = np.random.uniform(0.5, 4.0)
            current_time += timedelta(hours=close_delay)
            events.append({
                "activity": "Incident Closed",
                "timestamp": current_time,
                "status": "Closed",
                "assigned_team": assigned_team,
            })
        else:
            # 3. Team Assignment
            assign_delay = np.random.lognormal(mean=-1.0, sigma=0.6)  # median ~0.37h
            current_time += timedelta(hours=assign_delay)
            events.append({
                "activity": "Team Assignment",
                "timestamp": current_time,
                "status": "In Progress",
                "assigned_team": assigned_team,
            })

            # 4. Investigation
            # Investigation duration depends on team and complexity
            base_inv_hours = {
                "P1 - Critical": 2.2,
                "P2 - High": 6.5,
                "P3 - Medium": 14.0,
                "P4 - Low": 32.0,
            }[priority]

            # Team-specific delay factors (bottlenecks)
            team_delay_mult = {
                "Database Admin": 1.55,  # Known bottleneck
                "Cloud Infra": 1.35,     # Known bottleneck
                "App Support": 1.15,
                "Network Ops": 1.05,
                "SecOps": 1.00,
                "Service Desk": 0.85,
            }.get(assigned_team, 1.0)

            inv_duration = np.random.gamma(shape=2.5, scale=(base_inv_hours * team_delay_mult) / 2.5)
            current_time += timedelta(hours=inv_duration)
            events.append({
                "activity": "Investigation",
                "timestamp": current_time,
                "status": "In Progress",
                "assigned_team": assigned_team,
            })

            # Escalations
            for esc_step in range(escalation_count):
                esc_delay = np.random.uniform(1.2, 5.0) * team_delay_mult
                current_time += timedelta(hours=esc_delay)
                events.append({
                    "activity": "Escalation",
                    "timestamp": current_time,
                    "status": "Escalated",
                    "assigned_team": assigned_team,
                })
                # Post-escalation secondary investigation
                post_esc_inv = np.random.gamma(shape=2.0, scale=3.5)
                current_time += timedelta(hours=post_esc_inv)
                events.append({
                    "activity": "Investigation",
                    "timestamp": current_time,
                    "status": "In Progress",
                    "assigned_team": assigned_team,
                })

            # 5. Resolution
            res_delay = np.random.uniform(0.3, 2.5)
            current_time += timedelta(hours=res_delay)
            events.append({
                "activity": "Resolution",
                "timestamp": current_time,
                "status": "Resolved",
                "assigned_team": assigned_team,
            })

            # 6. Incident Closed
            close_delay = np.random.uniform(1.0, 8.0)
            current_time += timedelta(hours=close_delay)
            events.append({
                "activity": "Incident Closed",
                "timestamp": current_time,
                "status": "Closed",
                "assigned_team": assigned_team,
            })

            # 7. Reopened Lifecycle (if applicable)
            if has_reopen:
                reopen_gap = np.random.uniform(2.0, 24.0)
                current_time += timedelta(hours=reopen_gap)
                events.append({
                    "activity": "Incident Reopened",
                    "timestamp": current_time,
                    "status": "In Progress",
                    "assigned_team": assigned_team,
                })

                reinv_delay = np.random.gamma(shape=2.0, scale=4.0)
                current_time += timedelta(hours=reinv_delay)
                events.append({
                    "activity": "Investigation",
                    "timestamp": current_time,
                    "status": "In Progress",
                    "assigned_team": assigned_team,
                })

                re_res_delay = np.random.uniform(0.5, 3.0)
                current_time += timedelta(hours=re_res_delay)
                events.append({
                    "activity": "Resolution",
                    "timestamp": current_time,
                    "status": "Resolved",
                    "assigned_team": assigned_team,
                })

                final_close_delay = np.random.uniform(1.0, 6.0)
                current_time += timedelta(hours=final_close_delay)
                events.append({
                    "activity": "Incident Closed",
                    "timestamp": current_time,
                    "status": "Closed",
                    "assigned_team": assigned_team,
                })

        # Calculate total resolution time (hours)
        total_resolution_time = (current_time - incident_created_time).total_seconds() / 3600.0

        for ev in events:
            records.append({
                "incident_id": incident_id,
                "activity": ev["activity"],
                "timestamp": ev["timestamp"].strftime("%Y-%m-%d %H:%M:%S"),
                "incident_type": incident_type,
                "priority": priority,
                "severity": severity,
                "assigned_team": ev["assigned_team"],
                "source": source,
                "status": ev["status"],
                "resolution_time_hours": round(total_resolution_time, 2),
                "sla_target_hours": sla_target_hours,
                "reopened": 1 if has_reopen else 0,
                "escalation_count": escalation_count,
            })

    df = pd.DataFrame(records)
    # Sort chronologically
    df["timestamp"] = pd.to_datetime(df["timestamp"])
    df = df.sort_values(by=["incident_id", "timestamp"]).reset_index(drop=True)
    df["timestamp"] = df["timestamp"].dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def save_dataset(df: pd.DataFrame, filepath: str = "data/sample_incidents.csv") -> str:
    """Save dataset to specified filepath, creating directories if needed."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    return filepath


if __name__ == "__main__":
    print("Generating synthetic IT incident dataset...")
    df = generate_incident_dataset(n_cases=1200, seed=42)
    save_path = save_dataset(df, "data/sample_incidents.csv")
    print(f"Generated {len(df)} event logs across {df['incident_id'].nunique()} unique cases.")
    print(f"Dataset successfully saved to: {save_path}")
