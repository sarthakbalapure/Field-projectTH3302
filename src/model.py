"""
Machine Learning SLA Risk Prediction Module.

Trains and evaluates a leak-free Random Forest classification model
to predict whether an IT incident will breach its SLA target.
"""

import os
import sys
from typing import Dict, Any, Tuple, List
import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (
    accuracy_score,
    precision_score,
    recall_score,
    f1_score,
    roc_auc_score,
    confusion_matrix,
    classification_report,
)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

# Add project root to sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


CATEGORICAL_FEATURES = [
    "incident_type",
    "priority",
    "severity",
    "assigned_team",
    "source",
]

NUMERICAL_FEATURES = [
    "initial_assessment_hours",
    "time_to_assignment_hours",
    "created_hour",
    "created_dayofweek",
    "is_weekend",
    "is_offhours",
]

MODEL_PATH = "models/sla_risk_model.joblib"


def build_pipeline() -> Pipeline:
    """
    Construct a scikit-learn preprocessing and classification pipeline.

    Returns:
        Pipeline instance.
    """
    preprocessor = ColumnTransformer(
        transformers=[
            (
                "cat",
                OneHotEncoder(handle_unknown="ignore", sparse_output=False),
                CATEGORICAL_FEATURES,
            ),
            (
                "num",
                StandardScaler(),
                NUMERICAL_FEATURES,
            ),
        ]
    )

    clf = RandomForestClassifier(
        n_estimators=120,
        max_depth=12,
        min_samples_split=5,
        min_samples_leaf=2,
        class_weight="balanced",
        random_state=42,
    )

    return Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", clf),
    ])


def train_and_evaluate_model(
    case_df: pd.DataFrame,
    test_size: float = 0.2,
    random_state: int = 42,
) -> Tuple[Dict[str, Any], Pipeline]:
    """
    Train model using early-stage features and evaluate test performance.

    Args:
        case_df: Aggregated case-level DataFrame.
        test_size: Fraction of data for testing (default: 0.2).
        random_state: Seed for reproducibility.

    Returns:
        Tuple of (evaluation_metrics_dict, trained_pipeline).
    """
    feature_cols = CATEGORICAL_FEATURES + NUMERICAL_FEATURES
    X = case_df[feature_cols].copy()
    y = case_df["sla_breached"].astype(int).values

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_size, random_state=random_state, stratify=y
    )

    pipeline = build_pipeline()
    pipeline.fit(X_train, y_train)

    y_pred = pipeline.predict(X_test)
    y_prob = pipeline.predict_proba(X_test)[:, 1]

    # Metrics
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred, zero_division=0)
    f1 = f1_score(y_test, y_pred, zero_division=0)
    roc_auc = roc_auc_score(y_test, y_prob)
    cm = confusion_matrix(y_test, y_pred).tolist()

    # Extract Feature Importances
    preprocessor = pipeline.named_steps["preprocessor"]
    classifier = pipeline.named_steps["classifier"]
    
    cat_feature_names = preprocessor.named_transformers_["cat"].get_feature_names_out(CATEGORICAL_FEATURES).tolist()
    all_feature_names = cat_feature_names + NUMERICAL_FEATURES
    importances = classifier.feature_importances_

    feat_imp = sorted(
        [{"feature": name, "importance": round(float(imp), 4)} for name, imp in zip(all_feature_names, importances)],
        key=lambda x: x["importance"],
        reverse=True,
    )

    metrics = {
        "accuracy": round(float(acc), 4),
        "precision": round(float(prec), 4),
        "recall": round(float(rec), 4),
        "f1_score": round(float(f1), 4),
        "roc_auc": round(float(roc_auc), 4),
        "confusion_matrix": cm,
        "classification_report": classification_report(y_test, y_pred, output_dict=True),
        "feature_importances": feat_imp,
        "test_sample_count": len(y_test),
        "train_sample_count": len(y_train),
    }

    return metrics, pipeline


def save_model(pipeline: Pipeline, metrics: Dict[str, Any], filepath: str = MODEL_PATH) -> str:
    """Save trained pipeline bundle along with evaluation metadata."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    bundle = {
        "pipeline": pipeline,
        "metrics": metrics,
        "features": {
            "categorical": CATEGORICAL_FEATURES,
            "numerical": NUMERICAL_FEATURES,
        },
    }
    joblib.dump(bundle, filepath)
    return filepath


def load_model(filepath: str = MODEL_PATH) -> Dict[str, Any]:
    """Load model bundle from disk."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Model file not found at {filepath}")
    return joblib.load(filepath)


def predict_incident_risk(
    model_bundle: Dict[str, Any],
    input_data: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Predict SLA breach risk for a single incident or DataFrame.

    Args:
        model_bundle: Loaded bundle containing 'pipeline'.
        input_data: Dict containing required feature keys.

    Returns:
        Dict with predicted breach probability, binary prediction, and risk category.
    """
    pipeline = model_bundle["pipeline"]
    df_input = pd.DataFrame([input_data])
    
    # Fill defaults for missing numericals if needed
    for num_col in NUMERICAL_FEATURES:
        if num_col not in df_input.columns:
            df_input[num_col] = 0.5

    prob = float(pipeline.predict_proba(df_input)[:, 1][0])
    is_breach_predicted = int(prob >= 0.5)

    if prob >= 0.75:
        risk_level = "Critical Risk"
    elif prob >= 0.50:
        risk_level = "High Risk"
    elif prob >= 0.30:
        risk_level = "Moderate Risk"
    else:
        risk_level = "Low Risk"

    return {
        "breach_probability": round(prob, 4),
        "predicted_breach": is_breach_predicted,
        "risk_level": risk_level,
    }


if __name__ == "__main__":
    from src.preprocessing import load_and_validate_dataset, aggregate_cases

    print("Loading dataset for model training...")
    df = load_and_validate_dataset()
    cases = aggregate_cases(df)

    print("Training Random Forest SLA Breach Risk Predictor...")
    metrics, pipeline = train_and_evaluate_model(cases)

    saved_path = save_model(pipeline, metrics)
    print(f"Model saved to {saved_path}")
    print(f"Test Accuracy:  {metrics['accuracy']:.2%}")
    print(f"Test Precision: {metrics['precision']:.2%}")
    print(f"Test Recall:    {metrics['recall']:.2%}")
    print(f"Test F1-Score:  {metrics['f1_score']:.2%}")
    print(f"Test ROC-AUC:   {metrics['roc_auc']:.2%}")
    print(f"Confusion Matrix: {metrics['confusion_matrix']}")
    print("Top 5 Features:")
    for f in metrics["feature_importances"][:5]:
        print(f"  {f['feature']}: {f['importance']}")
