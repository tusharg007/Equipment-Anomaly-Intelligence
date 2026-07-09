from __future__ import annotations

import os
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
PREDICTIONS_DIR = DATA_DIR / "predictions"
REPORTS_DIR = PROJECT_ROOT / "reports"
MODELS_DIR = PROJECT_ROOT / "models"


def ensure_directories() -> None:
    for directory in [RAW_DATA_DIR, PROCESSED_DATA_DIR, PREDICTIONS_DIR, REPORTS_DIR, MODELS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def get_database_url() -> str:
    host = os.getenv("POSTGRES_HOST", "localhost")
    port = os.getenv("POSTGRES_PORT", "5432")
    database = os.getenv("POSTGRES_DB", "manufacturing")
    user = os.getenv("POSTGRES_USER", "manufacturing")
    password = os.getenv("POSTGRES_PASSWORD", "manufacturing")
    return f"postgresql+psycopg2://{user}:{password}@{host}:{port}/{database}"


def get_engine():
    from sqlalchemy import create_engine

    return create_engine(get_database_url(), pool_pre_ping=True)


def write_markdown_table(df: pd.DataFrame, index: bool = False) -> str:
    if df.empty:
        return "_No rows available._"
    try:
        return df.to_markdown(index=index)
    except ImportError:
        display_df = df.copy()
        if index:
            display_df = display_df.reset_index()
        columns = list(display_df.columns)
        header = "| " + " | ".join(str(column) for column in columns) + " |"
        divider = "| " + " | ".join(["---"] * len(columns)) + " |"
        rows = [
            "| " + " | ".join(str(value) for value in row) + " |"
            for row in display_df.itertuples(index=False, name=None)
        ]
        return "\n".join([header, divider, *rows])


def safe_divide(numerator: Iterable[float], denominator: Iterable[float]) -> np.ndarray:
    numerator_array = np.asarray(numerator, dtype=float)
    denominator_array = np.asarray(denominator, dtype=float)
    return np.divide(
        numerator_array,
        denominator_array,
        out=np.zeros_like(numerator_array, dtype=float),
        where=denominator_array != 0,
    )
