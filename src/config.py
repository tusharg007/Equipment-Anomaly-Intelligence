from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from dotenv import load_dotenv


PROJECT_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(PROJECT_ROOT / ".env")


@dataclass(frozen=True)
class Settings:
    project_root: Path = PROJECT_ROOT
    data_dir: Path = PROJECT_ROOT / "data"
    raw_data_dir: Path = PROJECT_ROOT / "data" / "raw"
    processed_data_dir: Path = PROJECT_ROOT / "data" / "processed"
    predictions_dir: Path = PROJECT_ROOT / "data" / "predictions"
    reports_dir: Path = PROJECT_ROOT / "reports"
    models_dir: Path = PROJECT_ROOT / "models"
    defect_model_dir: Path = PROJECT_ROOT / "models" / "defect_model"
    anomaly_model_dir: Path = PROJECT_ROOT / "models" / "anomaly_model"
    api_dir: Path = PROJECT_ROOT / "api"
    tests_dir: Path = PROJECT_ROOT / "tests"
    postgres_host: str = os.getenv("POSTGRES_HOST", "localhost")
    postgres_port: str = os.getenv("POSTGRES_PORT", "5432")
    postgres_db: str = os.getenv("POSTGRES_DB", "manufacturing")
    postgres_user: str = os.getenv("POSTGRES_USER", "manufacturing")
    postgres_password: str = os.getenv("POSTGRES_PASSWORD", "manufacturing")
    api_host: str = os.getenv("API_HOST", "0.0.0.0")
    api_port: int = int(os.getenv("API_PORT", "8000"))

    @property
    def database_url(self) -> str:
        return (
            f"postgresql+psycopg2://{self.postgres_user}:{self.postgres_password}"
            f"@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"
        )

    @property
    def required_directories(self) -> list[Path]:
        return [
            self.raw_data_dir,
            self.processed_data_dir,
            self.predictions_dir,
            self.reports_dir,
            self.models_dir,
            self.defect_model_dir,
            self.anomaly_model_dir,
            self.api_dir,
            self.tests_dir,
        ]


settings = Settings()
