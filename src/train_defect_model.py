from __future__ import annotations

import json

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix, f1_score, precision_score, recall_score, roc_auc_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from config import settings
from utils import ensure_directories, save_joblib, save_json, write_markdown_table

try:
    from xgboost import XGBClassifier
except ImportError:
    XGBClassifier = None


FEATURE_FILE = settings.processed_data_dir / "ml_training_dataset.csv"
CONFUSION_MATRIX_FILE = settings.reports_dir / "confusion_matrix.csv"
CLASSIFICATION_REPORT_FILE = settings.reports_dir / "classification_report.json"
METRICS_JSON_FILE = settings.reports_dir / "metrics.json"
MODEL_FILE = settings.defect_model_dir / "best_defect_model.joblib"

NUMERIC_FEATURES = [
    "avg_temperature",
    "avg_vibration",
    "avg_pressure",
    "avg_cycle_time",
    "avg_energy_consumption",
    "pressure_instability",
    "anomaly_signal",
    "machine_age_years",
    "days_since_maintenance",
    "previous_downtime_minutes",
    "downtime_event_count",
    "cycle_time_drift",
    "pressure_deviation",
    "maintenance_recency_score",
    "quality_risk_index",
    "anomaly_count_24h",
    "baseline_health_score",
]
CATEGORICAL_FEATURES = ["line_id", "shift"]


def load_training_data() -> pd.DataFrame:
    if FEATURE_FILE.exists():
        data = pd.read_csv(FEATURE_FILE)
        source = "processed_csv"
    else:
        from sqlalchemy import create_engine

        engine = create_engine(settings.database_url, pool_pre_ping=True)
        data = pd.read_sql("select * from public.ml_training_dataset", engine)
        source = "postgres"
    if data["defect_flag"].nunique() < 2:
        raise ValueError("Training data must contain both defect classes.")
    print(f"Loaded training data from {source}: {len(data)} rows")
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


def evaluate_model(name: str, pipeline: Pipeline, x_test: pd.DataFrame, y_test: pd.Series) -> tuple[dict, pd.DataFrame]:
    probabilities = pipeline.predict_proba(x_test)[:, 1]
    predictions = (probabilities >= 0.5).astype(int)
    matrix = confusion_matrix(y_test, predictions)
    tn, fp, fn, tp = matrix.ravel()
    result = {
        "model": name,
        "roc_auc": float(roc_auc_score(y_test, probabilities)),
        "precision": float(precision_score(y_test, predictions, zero_division=0)),
        "recall": float(recall_score(y_test, predictions, zero_division=0)),
        "f1": float(f1_score(y_test, predictions, zero_division=0)),
        "composite_score": 0.6 * float(roc_auc_score(y_test, probabilities)) + 0.4 * float(f1_score(y_test, predictions, zero_division=0)),
        "tn": int(tn),
        "fp": int(fp),
        "fn": int(fn),
        "tp": int(tp),
    }
    matrix_df = pd.DataFrame(matrix, index=["actual_0", "actual_1"], columns=["predicted_0", "predicted_1"])
    return result, matrix_df


def extract_feature_importance(model_pipeline: Pipeline) -> pd.DataFrame:
    feature_names = model_pipeline.named_steps["preprocessor"].get_feature_names_out()
    estimator = model_pipeline.named_steps["model"]
    if hasattr(estimator, "feature_importances_"):
        importance = estimator.feature_importances_
    elif hasattr(estimator, "coef_"):
        importance = abs(estimator.coef_[0])
    else:
        importance = [0.0] * len(feature_names)
    return pd.DataFrame({"feature": feature_names, "importance": importance}).sort_values("importance", ascending=False)


def main() -> None:
    ensure_directories()
    data = load_training_data()
    X = data[NUMERIC_FEATURES + CATEGORICAL_FEATURES]
    y = data["defect_flag"]
    x_train, x_test, y_train, y_test = train_test_split(
        X, y, test_size=0.25, random_state=42, stratify=y
    )

    model_specs = {
        "LogisticRegression": LogisticRegression(max_iter=1000, class_weight="balanced"),
        "RandomForest": RandomForestClassifier(
            n_estimators=240,
            max_depth=8,
            min_samples_leaf=3,
            class_weight="balanced",
            random_state=42,
        ),
    }
    if XGBClassifier is not None:
        model_specs["XGBoost"] = XGBClassifier(
            n_estimators=220,
            max_depth=5,
            learning_rate=0.07,
            subsample=0.9,
            colsample_bytree=0.9,
            eval_metric="logloss",
            random_state=42,
        )

    metrics = []
    matrices = {}
    trained_models = {}
    preprocessor = build_preprocessor()
    for name, estimator in model_specs.items():
        pipeline = Pipeline([("preprocessor", preprocessor), ("model", estimator)])
        pipeline.fit(x_train, y_train)
        metric_row, matrix_df = evaluate_model(name, pipeline, x_test, y_test)
        metrics.append(metric_row)
        matrices[name] = matrix_df
        trained_models[name] = pipeline

    metrics_df = pd.DataFrame(metrics).sort_values(["composite_score", "roc_auc"], ascending=False).reset_index(drop=True)
    best_model_name = metrics_df.iloc[0]["model"]
    best_model = trained_models[best_model_name]
    best_matrix = matrices[best_model_name]

    probabilities = best_model.predict_proba(X)[:, 1]
    predicted_flags = (probabilities >= 0.5).astype(int)
    feature_importance = extract_feature_importance(best_model)
    predictions_df = data[["machine_id", "line_id", "timestamp", "shift"]].copy()
    predictions_df["predicted_defect_probability"] = probabilities
    predictions_df["predicted_defect_flag"] = predicted_flags
    predictions_df["actual_defect_flag"] = data["defect_flag"]

    predictions_df.to_csv(settings.predictions_dir / "defect_predictions.csv", index=False)
    feature_importance.to_csv(settings.predictions_dir / "feature_importance.csv", index=False)
    best_matrix.to_csv(CONFUSION_MATRIX_FILE)

    report_dict = classification_report(y_test, (best_model.predict_proba(x_test)[:, 1] >= 0.5).astype(int), output_dict=True, zero_division=0)
    save_json(report_dict, CLASSIFICATION_REPORT_FILE)
    save_json(
        {
            "selected_model": best_model_name,
            "metrics": metrics_df.to_dict(orient="records"),
        },
        METRICS_JSON_FILE,
    )
    save_joblib(best_model, MODEL_FILE)

    summary_lines = [
        "# Defect Model Evaluation",
        "",
        "This production-oriented prototype compares baseline and tree-based quality prediction models on synthetic manufacturing data.",
        "",
        "## Model Comparison",
        "",
        write_markdown_table(metrics_df[["model", "roc_auc", "precision", "recall", "f1", "composite_score"]].round(4)),
        "",
        "## Selected Model",
        "",
        f"`{best_model_name}` was selected using a blend of ROC-AUC and F1 to balance ranking quality and actionable classification performance.",
        "",
        "## Confusion Matrix",
        "",
        write_markdown_table(best_matrix, index=True),
        "",
        "## Top Feature Importance",
        "",
        write_markdown_table(feature_importance.head(10).round(4)),
        "",
        "## Notes",
        "",
        "- The dataset is synthetic and designed for manufacturing analytics prototyping rather than plant-validated deployment.",
        "- XGBoost is optional and only evaluated if the dependency is installed.",
        "- Outputs include metrics JSON, classification report JSON, confusion matrix CSV, feature importance, predictions, and a joblib model artifact.",
    ]
    (settings.reports_dir / "model_evaluation.md").write_text("\n".join(summary_lines), encoding="utf-8")
    print(metrics_df.round(4).to_string(index=False))


if __name__ == "__main__":
    main()
