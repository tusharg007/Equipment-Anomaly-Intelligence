from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable

import joblib
import numpy as np
import pandas as pd

from src.config import settings


def ensure_directories() -> None:
    for directory in settings.required_directories:
        directory.mkdir(parents=True, exist_ok=True)


def safe_divide(numerator: Iterable[float], denominator: Iterable[float]) -> np.ndarray:
    numerator_array = np.asarray(numerator, dtype=float)
    denominator_array = np.asarray(denominator, dtype=float)
    return np.divide(
        numerator_array,
        denominator_array,
        out=np.zeros_like(numerator_array, dtype=float),
        where=denominator_array != 0,
    )


def write_markdown_table(df: pd.DataFrame, index: bool = False) -> str:
    if df.empty:
        return "_No rows available._"
    try:
        return df.to_markdown(index=index)
    except ImportError:
        display_df = df.reset_index() if index else df.copy()
        columns = list(display_df.columns)
        header = "| " + " | ".join(str(column) for column in columns) + " |"
        divider = "| " + " | ".join(["---"] * len(columns)) + " |"
        rows = [
            "| " + " | ".join(str(value) for value in row) + " |"
            for row in display_df.itertuples(index=False, name=None)
        ]
        return "\n".join([header, divider, *rows])


def read_csv_if_exists(file_path: Path) -> pd.DataFrame | None:
    if not file_path.exists():
        return None
    return pd.read_csv(file_path)


def save_json(payload: dict, file_path: Path) -> None:
    file_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def save_joblib(payload, file_path: Path) -> None:
    file_path.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(payload, file_path)

