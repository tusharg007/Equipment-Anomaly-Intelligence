from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable
from urllib.error import URLError
from urllib.request import urlopen

import matplotlib.pyplot as plt
from matplotlib import gridspec
from matplotlib.patches import FancyBboxPatch
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parents[1]
ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"
PREDICTIONS_DIR = DATA_DIR / "predictions"
REPORTS_DIR = PROJECT_ROOT / "reports"
RAW_DIR = DATA_DIR / "raw"
API_DOCS_URL = "http://127.0.0.1:8000/docs"
FIGSIZE = (14, 8)
DPI = 100

PALETTE = {
    "navy": "#16324f",
    "blue": "#2a6f97",
    "teal": "#2a9d8f",
    "green": "#4c956c",
    "gold": "#e9c46a",
    "orange": "#f4a261",
    "red": "#e76f51",
    "slate": "#5c677d",
    "light": "#f7f9fc",
    "dark": "#1f2933",
}

plt.rcParams.update(
    {
        "figure.facecolor": "white",
        "axes.facecolor": "white",
        "axes.edgecolor": "#d9e2ec",
        "axes.labelcolor": PALETTE["dark"],
        "text.color": PALETTE["dark"],
        "xtick.color": PALETTE["dark"],
        "ytick.color": PALETTE["dark"],
        "font.size": 11,
        "axes.titlesize": 16,
        "axes.titleweight": "bold",
    }
)


def warn(message: str) -> None:
    print(f"WARNING: {message}")


def info(message: str) -> None:
    print(message)


def ensure_assets_dir() -> None:
    ASSETS_DIR.mkdir(parents=True, exist_ok=True)


def read_csv(path: Path) -> pd.DataFrame | None:
    if not path.exists():
        warn(f"Missing file: {path}")
        return None
    try:
        return pd.read_csv(path)
    except Exception as exc:
        warn(f"Failed to read {path.name}: {exc}")
        return None


def read_json(path: Path) -> dict | None:
    if not path.exists():
        warn(f"Missing file: {path}")
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception as exc:
        warn(f"Failed to read {path.name}: {exc}")
        return None


def numeric_series(df: pd.DataFrame, column: str) -> pd.Series:
    return pd.to_numeric(df[column], errors="coerce")


def save_figure(fig: plt.Figure, output_name: str) -> None:
    output_path = ASSETS_DIR / output_name
    fig.tight_layout()
    fig.savefig(output_path, dpi=DPI, bbox_inches="tight")
    plt.close(fig)
    info(f"Saved {output_path}")


def draw_kpi(ax: plt.Axes, title: str, value: str, accent: str) -> None:
    ax.set_axis_off()
    card = FancyBboxPatch(
        (0.02, 0.08),
        0.96,
        0.84,
        boxstyle="round,pad=0.02,rounding_size=18",
        facecolor=PALETTE["light"],
        edgecolor="#d9e2ec",
        linewidth=1.2,
        transform=ax.transAxes,
    )
    ax.add_patch(card)
    ax.text(0.08, 0.68, title, transform=ax.transAxes, fontsize=12, color=PALETTE["slate"], weight="bold")
    ax.text(0.08, 0.28, value, transform=ax.transAxes, fontsize=24, color=accent, weight="bold")


def style_barh(ax: plt.Axes, title: str, xlabel: str) -> None:
    ax.set_title(title, loc="left")
    ax.set_xlabel(xlabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="x", linestyle="--", alpha=0.25)


def style_bar(ax: plt.Axes, title: str, ylabel: str) -> None:
    ax.set_title(title, loc="left")
    ax.set_ylabel(ylabel)
    ax.spines[["top", "right"]].set_visible(False)
    ax.grid(axis="y", linestyle="--", alpha=0.25)


def generate_api_docs_screenshot() -> None:
    output_path = ASSETS_DIR / "api_docs.png"
    try:
        with urlopen(API_DOCS_URL, timeout=3):
            pass
    except URLError:
        print("Start API first using: uvicorn api.main:app --reload --host 0.0.0.0 --port 8000")
        return
    except Exception as exc:
        warn(f"Unable to reach FastAPI docs: {exc}")
        return

    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        warn("Playwright is not installed. Run `pip install playwright` and `python -m playwright install chromium` to capture api_docs.png.")
        return

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=1)
            page.goto(API_DOCS_URL, wait_until="networkidle", timeout=15000)
            page.screenshot(path=str(output_path), full_page=True)
            browser.close()
        info(f"Saved {output_path}")
    except Exception as exc:
        warn(f"Failed to capture API docs screenshot: {exc}")


def generate_manufacturing_overview() -> None:
    risk_df = read_csv(PREDICTIONS_DIR / "downtime_risk_scores.csv")
    anomaly_df = read_csv(PREDICTIONS_DIR / "anomaly_scores.csv")
    defect_df = read_csv(PREDICTIONS_DIR / "defect_predictions.csv")
    if risk_df is None or anomaly_df is None or defect_df is None:
        warn("Skipping manufacturing_overview.png because one or more source files are missing.")
        return

    risk_df["downtime_risk_score"] = numeric_series(risk_df, "downtime_risk_score")
    anomaly_df["anomaly_flag"] = numeric_series(anomaly_df, "anomaly_flag")
    defect_df["predicted_defect_flag"] = numeric_series(defect_df, "predicted_defect_flag")

    total_machines = int(risk_df["machine_id"].nunique())
    high_critical = int(risk_df["risk_band"].isin(["High", "Critical"]).sum())
    avg_risk = risk_df["downtime_risk_score"].mean()
    anomaly_count = int(anomaly_df["anomaly_flag"].fillna(0).sum())
    defect_count = int(defect_df["predicted_defect_flag"].fillna(0).sum())

    fig = plt.figure(figsize=FIGSIZE, dpi=DPI)
    gs = gridspec.GridSpec(2, 3, figure=fig, height_ratios=[1.0, 1.4])
    fig.suptitle("Manufacturing Overview", x=0.05, y=0.98, ha="left", fontsize=20, fontweight="bold")

    kpi_axes = [fig.add_subplot(gs[0, i]) for i in range(3)]
    draw_kpi(kpi_axes[0], "Machines in scoring set", f"{total_machines}", PALETTE["navy"])
    draw_kpi(kpi_axes[1], "High / Critical risk machines", f"{high_critical}", PALETTE["red"])
    draw_kpi(kpi_axes[2], "Average downtime risk score", f"{avg_risk:.1f}", PALETTE["orange"])

    kpi_axes_bottom = [fig.add_subplot(gs[1, i]) for i in range(3)]
    draw_kpi(kpi_axes_bottom[0], "Flagged anomaly windows", f"{anomaly_count}", PALETTE["teal"])
    draw_kpi(kpi_axes_bottom[1], "Predicted defect windows", f"{defect_count}", PALETTE["gold"])

    risk_band_counts = risk_df["risk_band"].value_counts().reindex(["Low", "Medium", "High", "Critical"], fill_value=0)
    ax = kpi_axes_bottom[2]
    colors = [PALETTE["green"], PALETTE["blue"], PALETTE["orange"], PALETTE["red"]]
    ax.bar(risk_band_counts.index, risk_band_counts.values, color=colors)
    style_bar(ax, "Downtime Risk Band Mix", "Machine count")

    save_figure(fig, "manufacturing_overview.png")


def generate_machine_health_dashboard() -> None:
    risk_df = read_csv(PREDICTIONS_DIR / "downtime_risk_scores.csv")
    if risk_df is None:
        warn("Skipping machine_health_dashboard.png because downtime_risk_scores.csv is missing.")
        return
    risk_df["downtime_risk_score"] = numeric_series(risk_df, "downtime_risk_score")
    top10 = risk_df.sort_values("downtime_risk_score", ascending=False).head(10).sort_values("downtime_risk_score")
    band_counts = risk_df["risk_band"].value_counts().reindex(["Low", "Medium", "High", "Critical"], fill_value=0)

    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE, dpi=DPI)
    fig.suptitle("Machine Health Dashboard", x=0.05, y=0.98, ha="left", fontsize=20, fontweight="bold")

    axes[0].barh(top10["machine_id"], top10["downtime_risk_score"], color=PALETTE["blue"])
    style_barh(axes[0], "Top 10 Machines by Downtime Risk Score", "Downtime risk score")

    colors = [PALETTE["green"], PALETTE["blue"], PALETTE["orange"], PALETTE["red"]]
    axes[1].bar(band_counts.index, band_counts.values, color=colors)
    style_bar(axes[1], "Risk Band Distribution", "Machine count")

    save_figure(fig, "machine_health_dashboard.png")


def generate_quality_risk_dashboard() -> None:
    defect_df = read_csv(PREDICTIONS_DIR / "defect_predictions.csv")
    feature_df = read_csv(PREDICTIONS_DIR / "feature_importance.csv")
    if defect_df is None or feature_df is None:
        warn("Skipping quality_risk_dashboard.png because one or more source files are missing.")
        return

    defect_df["predicted_defect_flag"] = numeric_series(defect_df, "predicted_defect_flag")
    defect_df["predicted_defect_probability"] = numeric_series(defect_df, "predicted_defect_probability")
    feature_df["importance"] = numeric_series(feature_df, "importance")

    bins = [0.0, 0.2, 0.4, 0.6, 0.8, 1.0]
    labels = ["0.0-0.2", "0.2-0.4", "0.4-0.6", "0.6-0.8", "0.8-1.0"]
    risk_buckets = pd.cut(defect_df["predicted_defect_probability"], bins=bins, labels=labels, include_lowest=True)
    bucket_counts = risk_buckets.value_counts().reindex(labels, fill_value=0)
    top_features = feature_df.sort_values("importance", ascending=False).head(8).sort_values("importance")

    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE, dpi=DPI)
    fig.suptitle("Quality Risk Dashboard", x=0.05, y=0.98, ha="left", fontsize=20, fontweight="bold")

    axes[0].bar(bucket_counts.index.astype(str), bucket_counts.values, color=PALETTE["gold"])
    style_bar(axes[0], "Predicted Defect Probability Distribution", "Prediction count")
    axes[0].tick_params(axis="x", rotation=20)

    axes[1].barh(top_features["feature"], top_features["importance"], color=PALETTE["teal"])
    style_barh(axes[1], "Top Feature Importance Drivers", "Importance")

    save_figure(fig, "quality_risk_dashboard.png")


def generate_downtime_risk_dashboard() -> None:
    risk_df = read_csv(PREDICTIONS_DIR / "downtime_risk_scores.csv")
    if risk_df is None:
        warn("Skipping downtime_risk_dashboard.png because downtime_risk_scores.csv is missing.")
        return

    risk_df["downtime_risk_score"] = numeric_series(risk_df, "downtime_risk_score")
    top_scores = risk_df.sort_values("downtime_risk_score", ascending=False).head(12).sort_values("downtime_risk_score")
    driver_counts = risk_df["top_risk_driver"].value_counts().head(8).sort_values()

    fig, axes = plt.subplots(1, 2, figsize=FIGSIZE, dpi=DPI)
    fig.suptitle("Downtime Risk Dashboard", x=0.05, y=0.98, ha="left", fontsize=20, fontweight="bold")

    axes[0].barh(top_scores["machine_id"], top_scores["downtime_risk_score"], color=PALETTE["red"])
    style_barh(axes[0], "Highest Downtime Risk Scores by Machine", "Downtime risk score")

    axes[1].barh(driver_counts.index, driver_counts.values, color=PALETTE["orange"])
    style_barh(axes[1], "Most Common Top Risk Drivers", "Machine count")

    save_figure(fig, "downtime_risk_dashboard.png")


def generate_maintenance_priority_dashboard() -> None:
    priority_df = read_csv(PREDICTIONS_DIR / "maintenance_priority.csv")
    risk_df = read_csv(PREDICTIONS_DIR / "downtime_risk_scores.csv")
    if priority_df is None:
        warn("Skipping maintenance_priority_dashboard.png because maintenance_priority.csv is missing.")
        return

    merged = priority_df.copy()
    if risk_df is not None and {"machine_id", "line_id", "downtime_risk_score"}.issubset(risk_df.columns):
        risk_subset = risk_df[["machine_id", "line_id", "downtime_risk_score"]].copy()
        risk_subset["downtime_risk_score"] = numeric_series(risk_subset, "downtime_risk_score")
        merged = merged.merge(risk_subset, on=["machine_id", "line_id"], how="left")
    priority_counts = merged["maintenance_priority_recommendation"].value_counts()

    fig = plt.figure(figsize=FIGSIZE, dpi=DPI)
    gs = gridspec.GridSpec(1, 2, figure=fig, width_ratios=[1.0, 1.3])
    fig.suptitle("Maintenance Priority Dashboard", x=0.05, y=0.98, ha="left", fontsize=20, fontweight="bold")

    ax0 = fig.add_subplot(gs[0, 0])
    ax0.bar(priority_counts.index, priority_counts.values, color=PALETTE["blue"])
    style_bar(ax0, "Maintenance Recommendation Counts", "Machine count")
    ax0.tick_params(axis="x", rotation=20)

    ax1 = fig.add_subplot(gs[0, 1])
    ax1.set_axis_off()
    table_df = merged.copy()
    if "downtime_risk_score" in table_df.columns:
        table_df = table_df.sort_values("downtime_risk_score", ascending=False)
    table_df = table_df[[col for col in ["machine_id", "line_id", "risk_band", "maintenance_priority_recommendation", "top_risk_driver", "downtime_risk_score"] if col in table_df.columns]].head(8)
    if "downtime_risk_score" in table_df.columns:
        table_df["downtime_risk_score"] = table_df["downtime_risk_score"].map(lambda x: f"{x:.1f}" if pd.notna(x) else "")
    ax1.set_title("Top High-Risk Machines", loc="left")
    table = ax1.table(
        cellText=table_df.values,
        colLabels=table_df.columns,
        cellLoc="left",
        colLoc="left",
        loc="center",
    )
    table.auto_set_font_size(False)
    table.set_fontsize(10)
    table.scale(1, 1.5)

    save_figure(fig, "maintenance_priority_dashboard.png")


def generate_model_evaluation_summary() -> None:
    metrics_payload = read_json(REPORTS_DIR / "metrics.json")
    feature_df = read_csv(PREDICTIONS_DIR / "feature_importance.csv")
    if metrics_payload is None:
        warn("Skipping model_evaluation_summary.png because metrics.json is missing.")
        return

    metrics_df = pd.DataFrame(metrics_payload.get("metrics", []))
    if metrics_df.empty:
        warn("Skipping model_evaluation_summary.png because metrics.json has no model metrics.")
        return
    selected_model = metrics_payload.get("selected_model", "Selected Model")
    selected_row = metrics_df.loc[metrics_df["model"] == selected_model]
    if selected_row.empty:
        selected_row = metrics_df.head(1)
    selected = selected_row.iloc[0]

    confusion_df = read_csv(REPORTS_DIR / "confusion_matrix.csv")
    if confusion_df is not None and confusion_df.shape[1] >= 3:
        confusion_df.columns = ["actual_label", "predicted_0", "predicted_1"]
        matrix = confusion_df[["predicted_0", "predicted_1"]].apply(pd.to_numeric, errors="coerce").to_numpy()
        row_labels = confusion_df["actual_label"].tolist()
    else:
        matrix = None
        row_labels = []

    if feature_df is not None:
        feature_df["importance"] = numeric_series(feature_df, "importance")
        top_features = feature_df.sort_values("importance", ascending=False).head(6).sort_values("importance")
    else:
        top_features = None

    fig = plt.figure(figsize=FIGSIZE, dpi=DPI)
    gs = gridspec.GridSpec(2, 4, figure=fig, height_ratios=[0.85, 1.45])
    fig.suptitle(f"Model Evaluation Summary: {selected_model}", x=0.05, y=0.98, ha="left", fontsize=20, fontweight="bold")

    metric_titles = [
        ("ROC-AUC", float(selected["roc_auc"]), PALETTE["navy"]),
        ("Precision", float(selected["precision"]), PALETTE["blue"]),
        ("Recall", float(selected["recall"]), PALETTE["teal"]),
        ("F1 Score", float(selected["f1"]), PALETTE["green"]),
    ]
    for index, (title, value, color) in enumerate(metric_titles):
        ax = fig.add_subplot(gs[0, index])
        draw_kpi(ax, title, f"{value:.3f}", color)

    if matrix is not None:
        ax_cm = fig.add_subplot(gs[1, 0:2])
        im = ax_cm.imshow(matrix, cmap="Blues")
        ax_cm.set_title("Confusion Matrix", loc="left")
        ax_cm.set_xticks([0, 1], labels=["Pred 0", "Pred 1"])
        ax_cm.set_yticks(range(len(row_labels)), labels=row_labels)
        for i in range(matrix.shape[0]):
            for j in range(matrix.shape[1]):
                ax_cm.text(j, i, int(matrix[i, j]), ha="center", va="center", color=PALETTE["dark"], fontsize=11, weight="bold")
        fig.colorbar(im, ax=ax_cm, fraction=0.046, pad=0.04)
    else:
        ax_cm = fig.add_subplot(gs[1, 0:2])
        ax_cm.set_axis_off()
        ax_cm.text(0.05, 0.6, "Confusion matrix unavailable", fontsize=14, weight="bold")

    ax_features = fig.add_subplot(gs[1, 2:4])
    if top_features is not None and not top_features.empty:
        ax_features.barh(top_features["feature"], top_features["importance"], color=PALETTE["orange"])
        style_barh(ax_features, "Top Feature Importance Drivers", "Importance")
    else:
        ax_features.set_axis_off()
        ax_features.text(0.05, 0.6, "Feature importance unavailable", fontsize=14, weight="bold")

    save_figure(fig, "model_evaluation_summary.png")


def run_all() -> None:
    ensure_assets_dir()
    generate_api_docs_screenshot()
    for generator in [
        generate_manufacturing_overview,
        generate_machine_health_dashboard,
        generate_quality_risk_dashboard,
        generate_downtime_risk_dashboard,
        generate_maintenance_priority_dashboard,
        generate_model_evaluation_summary,
    ]:
        try:
            generator()
        except Exception as exc:
            warn(f"{generator.__name__} failed: {exc}")


if __name__ == "__main__":
    run_all()
