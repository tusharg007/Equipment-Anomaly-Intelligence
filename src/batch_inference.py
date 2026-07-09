from __future__ import annotations

import argparse

import pandas as pd
from joblib import load

from config import settings
from train_defect_model import CATEGORICAL_FEATURES, NUMERIC_FEATURES
from utils import ensure_directories


def main() -> None:
    parser = argparse.ArgumentParser(description="Run batch defect risk inference on a CSV file.")
    parser.add_argument("--input", default=str(settings.processed_data_dir / "ml_training_dataset.csv"))
    parser.add_argument("--output", default=str(settings.predictions_dir / "batch_defect_predictions.csv"))
    args = parser.parse_args()

    ensure_directories()
    model_path = settings.defect_model_dir / "best_defect_model.joblib"
    if not model_path.exists():
        raise FileNotFoundError("Defect model artifact is missing. Run train_defect_model.py first.")

    data = pd.read_csv(args.input)
    model = load(model_path)
    probabilities = model.predict_proba(data[NUMERIC_FEATURES + CATEGORICAL_FEATURES])[:, 1]
    data["predicted_defect_probability"] = probabilities
    data["predicted_defect_flag"] = (probabilities >= 0.5).astype(int)
    data.to_csv(args.output, index=False)
    print(f"Saved batch predictions to {args.output}")


if __name__ == "__main__":
    main()
