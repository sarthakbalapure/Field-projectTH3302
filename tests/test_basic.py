"""
Automated Unit and Integration Tests for AI-Powered IT Incident Process Intelligence.
"""

import os
import sys
import pytest
import pandas as pd
import numpy as np

# Ensure root directory is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.data_generator import generate_incident_dataset, save_dataset
from src.preprocessing import (
    load_and_validate_dataset,
    aggregate_cases,
    extract_transitions,
    get_transition_summary,
    REQUIRED_COLUMNS,
)
from src.process_analysis import (
    discover_process_with_pm4py,
    get_process_variants,
    get_bottleneck_analysis,
    get_team_metrics,
    compare_happy_vs_inefficient_paths,
    generate_sankey_data,
)
from src.model import (
    train_and_evaluate_model,
    save_model,
    load_model,
    predict_incident_risk,
    CATEGORICAL_FEATURES,
    NUMERICAL_FEATURES,
)
from src.recommendations import generate_process_recommendations


@pytest.fixture(scope="session")
def sample_data():
    """Generate a quick synthetic dataset for test execution."""
    df = generate_incident_dataset(n_cases=150, seed=123)
    case_df = aggregate_cases(df)
    transitions_df = extract_transitions(df)
    return {
        "raw_df": df,
        "case_df": case_df,
        "transitions_df": transitions_df,
    }


def test_data_generator(sample_data):
    """Test synthetic dataset generator properties and schema."""
    df = sample_data["raw_df"]
    assert len(df) > 500, "Event count should be greater than 500 for 150 cases"
    assert df["incident_id"].nunique() == 150, "Should generate exactly 150 unique incident cases"
    
    for col in REQUIRED_COLUMNS:
        assert col in df.columns, f"Missing required column: {col}"

    assert df["incident_id"].isnull().sum() == 0, "incident_id must not have nulls"
    assert df["activity"].isnull().sum() == 0, "activity must not have nulls"
    assert df["timestamp"].isnull().sum() == 0, "timestamp must not have nulls"


def test_case_aggregation(sample_data):
    """Test case-level aggregation and leak-free feature engineering."""
    case_df = sample_data["case_df"]
    assert len(case_df) == 150
    assert "sla_breached" in case_df.columns
    assert set(case_df["sla_breached"].unique()).issubset({0, 1})
    assert (case_df["resolution_time_hours"] > 0).all()
    
    # Verify no leak: resolution_time_hours is not in early feature lists
    assert "resolution_time_hours" not in CATEGORICAL_FEATURES
    assert "resolution_time_hours" not in NUMERICAL_FEATURES
    assert "sla_breached" not in NUMERICAL_FEATURES


def test_transitions_and_bottlenecks(sample_data):
    """Test transition extraction and bottleneck ranking."""
    trans_df = sample_data["transitions_df"]
    assert not trans_df.empty
    assert "source_activity" in trans_df.columns
    assert "target_activity" in trans_df.columns
    assert "duration_hours" in trans_df.columns

    bottlenecks = get_bottleneck_analysis(trans_df)
    assert not bottlenecks.empty
    assert "mean_delay_hours" in bottlenecks.columns
    assert bottlenecks.iloc[0]["mean_delay_hours"] >= bottlenecks.iloc[-1]["mean_delay_hours"]


def test_process_variants_and_pm4py(sample_data):
    """Test variant discovery and PM4Py discovery."""
    case_df = sample_data["case_df"]
    variants = get_process_variants(case_df, top_n=5)
    assert not variants.empty
    assert "variant" in variants.columns
    assert variants.iloc[0]["case_count"] >= variants.iloc[-1]["case_count"]

    pm_res = discover_process_with_pm4py(sample_data["raw_df"])
    assert pm_res["status"] in ["success", "unavailable"]

    sankey = generate_sankey_data(sample_data["transitions_df"])
    assert "labels" in sankey
    assert "sources" in sankey
    assert "targets" in sankey


def test_model_training_and_prediction(sample_data, tmp_path):
    """Test ML pipeline training, evaluation, saving, and inference."""
    case_df = sample_data["case_df"]
    metrics, pipeline = train_and_evaluate_model(case_df, test_size=0.25, random_state=42)
    
    assert "accuracy" in metrics
    assert "precision" in metrics
    assert "recall" in metrics
    assert "f1_score" in metrics
    assert 0.0 <= metrics["accuracy"] <= 1.0

    test_model_path = str(tmp_path / "test_model.joblib")
    save_model(pipeline, metrics, test_model_path)
    assert os.path.exists(test_model_path)

    loaded = load_model(test_model_path)
    assert "pipeline" in loaded

    sample_incident = {
        "incident_type": "Database Performance",
        "priority": "P1 - Critical",
        "severity": "Critical",
        "assigned_team": "Database Admin",
        "source": "Monitoring Alert",
        "initial_assessment_hours": 0.8,
        "time_to_assignment_hours": 1.2,
        "created_hour": 14,
        "created_dayofweek": 2,
        "is_weekend": 0,
        "is_offhours": 0,
    }
    pred = predict_incident_risk(loaded, sample_incident)
    assert "breach_probability" in pred
    assert 0.0 <= pred["breach_probability"] <= 1.0
    assert pred["risk_level"] in ["Low Risk", "Moderate Risk", "High Risk", "Critical Risk"]


def test_recommendation_engine(sample_data):
    """Test AI-assisted recommendation engine."""
    case_df = sample_data["case_df"]
    trans_df = sample_data["transitions_df"]
    bottlenecks = get_bottleneck_analysis(trans_df)
    team_metrics = get_team_metrics(case_df)

    recs = generate_process_recommendations(case_df, trans_df, bottlenecks, team_metrics)
    assert len(recs) > 0
    for r in recs:
        assert "id" in r
        assert "title" in r
        assert "finding" in r
        assert "actionable_recommendation" in r
        assert "supporting_metrics" in r
