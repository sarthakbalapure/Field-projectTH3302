"""
AI-Assisted Explainable Recommendation Engine.

Analyzes empirical process mining metrics, bottleneck statistics,
and SLA risk trends to generate actionable, transparent recommendations
for IT operations teams.
"""

from typing import List, Dict, Any
import pandas as pd
import numpy as np


def generate_process_recommendations(
    case_df: pd.DataFrame,
    transitions_df: pd.DataFrame,
    bottlenecks_df: pd.DataFrame,
    team_metrics_df: pd.DataFrame,
) -> List[Dict[str, Any]]:
    """
    Generate rule-based, transparent, and data-backed recommendations.

    Args:
        case_df: Case-level aggregated DataFrame.
        transitions_df: Granular transition DataFrame.
        bottlenecks_df: Ranked bottleneck transitions DataFrame.
        team_metrics_df: Team performance metrics DataFrame.

    Returns:
        List of structured recommendation dictionaries.
    """
    recommendations = []
    rec_id = 1

    # 1. Bottleneck Delay Analysis
    top_bottlenecks = bottlenecks_df.head(3)
    for _, row in top_bottlenecks.iterrows():
        if row["mean_delay_hours"] >= 3.0:
            recommendations.append({
                "id": f"REC-{rec_id:03d}",
                "category": "Bottleneck Optimization",
                "severity": "Critical" if row["mean_delay_hours"] > 8.0 else "High",
                "title": f"Mitigate Long Queue Lag in '{row['transition']}'",
                "finding": (
                    f"Transition '{row['transition']}' exhibits an average wait time of "
                    f"{row['mean_delay_hours']:.1f} hours across {row['frequency']} incident occurrences, "
                    f"with 90th percentile reaching {row['p90_delay_hours']:.1f} hours."
                ),
                "actionable_recommendation": (
                    f"Implement automated assignment routing and pre-flight diagnostic checklists "
                    f"before handoff to '{row['target_activity']}'. Establish automated alert triggers "
                    f"when tickets remain pending for over {row['median_delay_hours']:.1f} hours."
                ),
                "supporting_metrics": {
                    "Transition": row["transition"],
                    "Frequency": int(row["frequency"]),
                    "Mean Delay": f"{row['mean_delay_hours']:.1f} hrs",
                    "P90 Delay": f"{row['p90_delay_hours']:.1f} hrs",
                    "Cumulative Wait": f"{row['total_delay_hours']:.0f} hrs",
                },
                "expected_impact": "Estimated 20-35% reduction in total cycle time for delayed tickets.",
            })
            rec_id += 1

    # 2. Team SLA Performance Analysis
    high_breach_teams = team_metrics_df[team_metrics_df["sla_breach_pct"] > 55.0]
    for _, row in high_breach_teams.iterrows():
        recommendations.append({
            "id": f"REC-{rec_id:03d}",
            "category": "Resource & Workload Balancing",
            "severity": "High",
            "title": f"Rebalance Workload for {row['assigned_team']} (SLA Breach Rate: {row['sla_breach_pct']}%)",
            "finding": (
                f"{row['assigned_team']} has a high SLA breach rate of {row['sla_breach_pct']}% "
                f"across {row['total_incidents']} cases with an average resolution time of "
                f"{row['avg_resolution_hours']:.1f} hours."
            ),
            "actionable_recommendation": (
                f"Review staffing allocation during peak hours for {row['assigned_team']}. "
                f"Deploy standard operating procedures (SOPs) and Tier-1 self-healing scripts "
                f"to deflect routine workload from this team."
            ),
            "supporting_metrics": {
                "Team": row["assigned_team"],
                "Total Cases": int(row["total_incidents"]),
                "SLA Breach Rate": f"{row['sla_breach_pct']}%",
                "Avg Resolution": f"{row['avg_resolution_hours']} hrs",
                "Escalation Rate": f"{row['escalation_pct']}%",
            },
            "expected_impact": "Targeted reduction of 15-25% in team SLA breaches.",
        })
        rec_id += 1

    # 3. Reopened Incident Prevention
    reopened_cases = case_df[case_df["reopened"] == 1]
    reopen_rate = len(reopened_cases) / len(case_df) * 100
    if reopen_rate > 5.0:
        top_reopened_type = reopened_cases["incident_type"].value_counts().index[0]
        reopened_type_count = reopened_cases["incident_type"].value_counts().iloc[0]
        
        recommendations.append({
            "id": f"REC-{rec_id:03d}",
            "category": "Quality Assurance & Resolution Verification",
            "severity": "Medium",
            "title": f"Address Reopened Tickets in '{top_reopened_type}' Incidents",
            "finding": (
                f"{reopen_rate:.1f}% of overall incidents were reopened after initial closure. "
                f"'{top_reopened_type}' had the highest reopening count ({reopened_type_count} cases). "
                f"Reopened cases had a {reopened_cases['sla_breached'].mean()*100:.1f}% SLA breach rate."
            ),
            "actionable_recommendation": (
                "Introduce mandatory automated post-resolution health checks and user confirmation "
                "before moving incidents from 'Resolved' to 'Closed' status. Conduct root cause reviews "
                "on frequently recurring reopened ticket categories."
            ),
            "supporting_metrics": {
                "Overall Reopen Rate": f"{reopen_rate:.1f}%",
                "Top Affected Type": top_reopened_type,
                "Cases Reopened": int(reopened_type_count),
                "Reopened SLA Breach": f"{reopened_cases['sla_breached'].mean()*100:.1f}%",
            },
            "expected_impact": "Projected 40% decrease in repeat incident reopenings.",
        })
        rec_id += 1

    # 4. Off-Hours & Weekend Initial Triage Delay
    offhours_cases = case_df[case_df["is_offhours"] == 1]
    workhours_cases = case_df[case_df["is_offhours"] == 0]
    
    if not offhours_cases.empty and not workhours_cases.empty:
        off_assess_mean = offhours_cases["initial_assessment_hours"].mean()
        work_assess_mean = workhours_cases["initial_assessment_hours"].mean()
        
        if off_assess_mean > work_assess_mean * 1.3:
            recommendations.append({
                "id": f"REC-{rec_id:03d}",
                "category": "Triage & Shift Coverage",
                "severity": "Medium",
                "title": "Automate Triage for Off-Hours and Night Shifts",
                "finding": (
                    f"Initial assessment takes {off_assess_mean:.2f} hours during off-hours compared to "
                    f"{work_assess_mean:.2f} hours during standard business hours "
                    f"({off_assess_mean / work_assess_mean:.1f}x slower)."
                ),
                "actionable_recommendation": (
                    "Deploy automated NLP classification and AI triage rules to instantly categorize "
                    "and dispatch after-hours incidents without waiting for manual dispatcher shifts. "
                    "Ensure on-call engineers are paged immediately for P1/P2 incidents."
                ),
                "supporting_metrics": {
                    "Off-Hours Triage Delay": f"{off_assess_mean:.2f} hrs",
                    "Business Hours Triage": f"{work_assess_mean:.2f} hrs",
                    "Off-Hours Incident Count": int(len(offhours_cases)),
                },
                "expected_impact": "Accelerate initial triage by up to 60% during off-peak hours.",
            })
            rec_id += 1

    # 5. Escalation Path Streamlining
    escalated_cases = case_df[case_df["escalation_count"] > 0]
    if not escalated_cases.empty:
        esc_breach_rate = escalated_cases["sla_breached"].mean() * 100
        non_esc_breach_rate = case_df[case_df["escalation_count"] == 0]["sla_breached"].mean() * 100
        
        recommendations.append({
            "id": f"REC-{rec_id:03d}",
            "category": "Escalation Management",
            "severity": "High",
            "title": "Streamline Tier-1 to Tier-2 Escalation Protocols",
            "finding": (
                f"Incidents requiring escalations suffer a {esc_breach_rate:.1f}% SLA breach rate, "
                f"compared to {non_esc_breach_rate:.1f}% for non-escalated cases. "
                f"Average resolution time rises from "
                f"{case_df[case_df['escalation_count'] == 0]['resolution_time_hours'].mean():.1f}h to "
                f"{escalated_cases['resolution_time_hours'].mean():.1f}h."
            ),
            "actionable_recommendation": (
                "Refine initial routing rules so incidents matching high-severity infrastructure or database "
                "signatures bypass Level 1 helpdesk and route directly to specialized engineering teams."
            ),
            "supporting_metrics": {
                "Escalated Cases": int(len(escalated_cases)),
                "Escalated Breach Rate": f"{esc_breach_rate:.1f}%",
                "Non-Escalated Breach Rate": f"{non_esc_breach_rate:.1f}%",
            },
            "expected_impact": "Eliminate 4 to 8 hours of handoff overhead for complex tickets.",
        })

    return recommendations


if __name__ == "__main__":
    from src.preprocessing import load_and_validate_dataset, aggregate_cases, extract_transitions
    from src.process_analysis import get_bottleneck_analysis, get_team_metrics

    df = load_and_validate_dataset()
    cases = aggregate_cases(df)
    trans = extract_transitions(df)
    bottlenecks = get_bottleneck_analysis(trans)
    team_metrics = get_team_metrics(cases)

    recs = generate_process_recommendations(cases, trans, bottlenecks, team_metrics)
    print(f"Generated {len(recs)} process recommendations:")
    for r in recs:
        print(f"[{r['severity']}] {r['id']}: {r['title']}")
