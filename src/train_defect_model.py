from __future__ import annotations

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from utils import MODELS_DIR, PREDICTIONS_DIR, PROCESSED_DATA_DIR, REPORTS_DIR, ensure_directories, write_markdown_table

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None


FEATURE_FILE = PROCESSED_DATA_DIR / "model_features.csv"


NUMERIC_FEATURES = [
    "avg_temperature",
    "avg_vibration",
    "avg_pressure",
    "avg_cycle_time",
    "avg_energy_consumption",
    "pressure_instability",
    "anomaly_signal",
    "machine_age_years",
    "last_maintenance_days_ago",
    "previous_downtime_minutes",
    "cycle_time_drift",
    "pressure_deviation",
    "maintenance_recency_score",
    "quality_risk_index",
]

CATEGORICAL_FEATURES = ["line_id", "shift"]


def load_training_data() -> pd.DataFrame:
    if not FEATURE_FILE.exists():
        raise FileNotFoundError("Run generate_synthetic_data.py before training.")
    data = pd.read_csv(FEATURE_FILE)
    if data["defect_flag"].nunique() < 2:
        raise ValueError("Training data must include both defect classes.")
    return data


def build_preprocessor() -> ColumnTransformer:
    numeric_pipeline = Pipeline(
        steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]
    )
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("encoder", OneHotEncoder(handle_unknown="ignore")),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("num", numeric_pipeline, NUMERIC_FEATURES),
            ("cat", categorical_pipeline, CATEGORICAL_FEATURES),
        ]
    )


def extract_feature_importance(model_pipeline: Pipeline) -> pd.DataFrame:
    feature_names = model_pipeline.named_steps["preprocessor"].get_feature_names_out()
    estimator = model_pipeline.named_steps["model"]

    if hasattr(estimator, "feature_importances_"):
        importance = estimator.feature_importances_
    elif hasattr(estimator, "coef_"):
        importance = abs(estimator.coef_[0])
    else:
        importance = [0.0] * len(feature_names)

    return (
        pd.DataFrame({"feature": feature_names, "importance": importance})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def evaluate_model(name: str, model: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> dict:
    probabilities = model.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    tn, fp, fn, tp = confusion_matrix(y_test, predictions).ravel()
    return {
        "model": name,
        "roc_auc": roc_auc_score(y_test, probabilities),
        "precision": precision_score(y_test, predictions, zero_division=0),
        "recall": recall_score(y_test, predictions, zero_division=0),
        "f1": f1_score(y_test, predictions, zero_division=0),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }


def main() -> None:
    ensure_directories()
    data = load_training_data()
    X = data[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = data["defect_flag"]

    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    preprocessor = build_preprocessor()
    model_specs = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "RandomForest": RandomForestClassifier(
            n_estimators=220, max_depth=8, min_samples_leaf=3, class_weight="balanced", random_state=42
        ),
    }
    if XGBClassifier is not None:
        model_specs["XGBoost"] = XGBClassifier(
            n_estimators=180,
            max_depth=5,
            learning_rate=0.07,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=42,
        )

    metrics = []
    trained_models = {}
    for name, estimator in model_specs.items():
        pipeline = Pipeline(
            steps=[
                ("preprocessor", preprocessor),
                ("model", estimator),
            ]
        )
        pipeline.fit(x_train, y_train)
        metrics.append(evaluate_model(name, pipeline, x_test, y_test))
        trained_models[name] = pipeline

    metrics_df = pd.DataFrame(metrics).sort_values("roc_auc", ascending=False).reset_index(drop=True)
    best_model_name = metrics_df.iloc[0]["model"]
    best_model = trained_models[best_model_name]

    full_probabilities = best_model.predict_proba(X)[:, 1]
    predictions = data[["machine_id", "line_id", "timestamp", "shift"]].copy()
    predictions["predicted_defect_probability"] = full_probabilities
    predictions["predicted_defect_flag"] = (full_probabilities >= 0.5).astype(int)
    predictions.to_csv(PREDICTIONS_DIR / "defect_predictions.csv", index=False)

    feature_importance = extract_feature_importance(best_model)
    feature_importance.to_csv(PREDICTIONS_DIR / "feature_importance.csv", index=False)
    joblib.dump(best_model, MODELS_DIR / "best_defect_model.joblib")

    summary_lines = [
        "# Defect Model Evaluation",
        "",
        "This prototype compares baseline defect classification approaches using synthetic manufacturing data.",
        "",
        "## Model Comparison",
        "",
        write_markdown_table(metrics_df.round(4)),
        "",
        f"## Selected Model",
        "",
        f"`{best_model_name}` was selected based on highest ROC-AUC on the holdout split.",
        "",
        "## Top Feature Importance",
        "",
        write_markdown_table(feature_importance.head(10).round(4)),
        "",
        "## Notes",
        "",
        "- The dataset is synthetic and designed to simulate manufacturing relationships rather than represent plant truth.",
        "- Thresholds are kept at 0.5 for simplicity in the prototype.",
        "- XGBoost is optional; the script safely falls back to baseline models if it is unavailable.",
    ]
    (REPORTS_DIR / "model_evaluation.md").write_text("\n".join(summary_lines), encoding="utf-8")

    print(metrics_df.round(4).to_string(index=False))
    print(f"Saved predictions to {PREDICTIONS_DIR / 'defect_predictions.csv'}")


if __name__ == "__main__":
    main()
