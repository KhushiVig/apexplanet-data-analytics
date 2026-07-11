"""
automate_pipeline.py

End to end automation script for the ApexPlanet Superstore analytics project.

This script performs the four stages required for Task 5 (Day 41-42):

    1. Extract   - reads the raw Superstore source file
    2. Transform - applies the same cleaning rules used in Task 1
    3. Analyse   - recomputes core KPIs, category and customer summaries,
                   and refreshes the churn classification model
    4. Export    - writes results to CSV and a multi-sheet Excel workbook,
                   and optionally emails a summary report

It is designed to be run on a schedule (see the Automation section of the
README for GitHub Actions, Windows Task Scheduler, and Airflow options),
so every stage is idempotent and safe to re-run.

Usage
-----
    python scripts/automate_pipeline.py
    python scripts/automate_pipeline.py --send-email

Environment variables (only required if --send-email is used)
----------------------------------------------------------------
    SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, REPORT_RECIPIENT
"""

import argparse
import logging
import os
import smtplib
import sqlite3
import sys
from datetime import datetime
from email.message import EmailMessage
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler

# ---------------------------------------------------------------------------
# Paths and logging
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parent.parent
RAW_PATH = ROOT_DIR / "data" / "raw" / "sample_-_superstore.xlsx"
PROCESSED_PATH = ROOT_DIR / "data" / "processed" / "cleaned_superstore.csv"
DB_PATH = ROOT_DIR / "superstore.db"
EXPORT_DIR = ROOT_DIR / "outputs" / "pipeline_exports"
LOG_PATH = ROOT_DIR / "outputs" / "pipeline_run.log"

EXPORT_DIR.mkdir(parents=True, exist_ok=True)
LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[logging.FileHandler(LOG_PATH), logging.StreamHandler(sys.stdout)],
)
log = logging.getLogger("apexplanet_pipeline")


# ---------------------------------------------------------------------------
# 1. Extract
# ---------------------------------------------------------------------------

def extract_data(source_path: Path = RAW_PATH) -> pd.DataFrame:
    """Read the raw Superstore dataset from its source file.

    Falls back to the already processed CSV if the raw source is not
    available, so the pipeline can still run in environments where only
    the cleaned dataset was checked in.
    """
    if source_path.exists():
        log.info("Extracting data from raw source: %s", source_path)
        df = pd.read_excel(source_path)
    elif PROCESSED_PATH.exists():
        log.warning("Raw source not found, falling back to processed dataset: %s", PROCESSED_PATH)
        df = pd.read_csv(PROCESSED_PATH)
    else:
        raise FileNotFoundError("Neither the raw source nor the processed dataset could be found.")
    log.info("Extracted %d rows and %d columns.", *df.shape)
    return df


# ---------------------------------------------------------------------------
# 2. Transform
# ---------------------------------------------------------------------------

def clean_data(df: pd.DataFrame) -> pd.DataFrame:
    """Apply the same cleaning rules used in Task 1 (EDA_Task1.ipynb).

    Steps: drop exact duplicate rows, parse date columns, cast categorical
    columns to the category dtype, and confirm there are no missing values
    in the core numeric fields the KPIs depend on.
    """
    log.info("Cleaning dataset.")
    before = len(df)
    df = df.drop_duplicates()
    dropped = before - len(df)
    if dropped:
        log.info("Removed %d duplicate rows.", dropped)

    for col in ["Order Date", "Ship Date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col])

    for col in ["Ship Mode", "Segment", "Region", "Category", "Sub-Category"]:
        if col in df.columns:
            df[col] = df[col].astype("category")

    core_cols = ["Sales", "Quantity", "Discount", "Profit"]
    missing = df[core_cols].isna().sum()
    if missing.sum() > 0:
        log.warning("Missing values found, filling with column medians: %s", missing[missing > 0].to_dict())
        df[core_cols] = df[core_cols].fillna(df[core_cols].median(numeric_only=True))
    else:
        log.info("No missing values found in core numeric columns.")

    df.to_csv(PROCESSED_PATH, index=False)
    log.info("Saved cleaned dataset to %s", PROCESSED_PATH)
    return df


def load_to_database(df: pd.DataFrame, db_path: Path = DB_PATH) -> None:
    """Refresh the SQLite database used by the Task 2 SQL layer."""
    log.info("Loading cleaned data into SQLite database: %s", db_path)
    conn = sqlite3.connect(db_path)
    df.to_sql("superstore", conn, if_exists="replace", index=False)
    conn.close()
    log.info("Database refresh complete.")


# ---------------------------------------------------------------------------
# 3. Analyse
# ---------------------------------------------------------------------------

def compute_kpis(df: pd.DataFrame) -> pd.DataFrame:
    """Recompute the headline KPIs shown on the executive dashboard."""
    total_orders = df["Order ID"].nunique() if "Order ID" in df.columns else len(df)
    total_customers = df["Customer Name"].nunique() if "Customer Name" in df.columns else np.nan
    total_sales = df["Sales"].sum()
    total_profit = df["Profit"].sum()
    mean_profit = df["Profit"].mean()
    discount_profit_corr = df["Discount"].corr(df["Profit"])

    if "Customer Name" in df.columns and "Order ID" in df.columns:
        orders_per_customer = df.groupby("Customer Name")["Order ID"].nunique()
        retention_rate = (orders_per_customer > 1).mean() * 100
    else:
        retention_rate = np.nan

    kpis = pd.DataFrame([{
        "Metric": "Total Records", "Value": len(df)},
        {"Metric": "Total Orders", "Value": total_orders},
        {"Metric": "Total Customers", "Value": total_customers},
        {"Metric": "Total Sales", "Value": round(total_sales, 2)},
        {"Metric": "Total Profit", "Value": round(total_profit, 2)},
        {"Metric": "Mean Profit per Order", "Value": round(mean_profit, 2)},
        {"Metric": "Discount-Profit Correlation", "Value": round(discount_profit_corr, 4)},
        {"Metric": "Customer Retention Rate (%)", "Value": round(retention_rate, 2)},
        {"Metric": "Pipeline Run Timestamp", "Value": datetime.now().strftime("%Y-%m-%d %H:%M:%S")},
    ])
    log.info("KPI summary computed. Total Sales = %.2f, Total Profit = %.2f", total_sales, total_profit)
    return kpis


def compute_category_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Sales and profit rolled up by product category."""
    summary = (
        df.groupby("Category", observed=True)
        .agg(Total_Sales=("Sales", "sum"), Total_Profit=("Profit", "sum"), Orders=("Order ID", "nunique"))
        .round(2)
        .sort_values("Total_Profit", ascending=False)
        .reset_index()
    )
    return summary


def compute_top_customers(df: pd.DataFrame, n: int = 10) -> pd.DataFrame:
    """Top N customers by total revenue."""
    summary = (
        df.groupby("Customer Name")["Sales"]
        .sum()
        .round(2)
        .sort_values(ascending=False)
        .head(n)
        .reset_index()
        .rename(columns={"Sales": "Total_Revenue"})
    )
    return summary


def compute_monthly_trend(df: pd.DataFrame) -> pd.DataFrame:
    """Monthly sales trend, aggregated across the full date range."""
    trend = df.copy()
    trend["Month"] = trend["Order Date"].dt.to_period("M").astype(str)
    monthly = trend.groupby("Month")["Sales"].sum().round(2).reset_index()
    monthly = monthly.rename(columns={"Sales": "Total_Sales"})
    return monthly


def refresh_churn_model(df: pd.DataFrame) -> dict:
    """Retrain the recency based churn classifier on the latest data.

    This mirrors the Task 4 churn model (a recency based proxy label, with
    Frequency, Monetary, and Discount features) so the pipeline keeps the
    model current as new orders are added, without requiring a full
    notebook re-run.
    """
    log.info("Refreshing churn classification model.")
    snapshot_date = df["Order Date"].max()
    customer_features = df.groupby("Customer Name").agg(
        Recency=("Order Date", lambda x: (snapshot_date - x.max()).days),
        Frequency=("Order ID", "nunique"),
        Monetary=("Sales", "sum"),
        AvgDiscount=("Discount", "mean"),
        TotalProfit=("Profit", "sum"),
    )
    customer_features["Churned"] = (customer_features["Recency"] > 180).astype(int)

    features = ["Frequency", "Monetary", "AvgDiscount", "TotalProfit"]
    X = StandardScaler().fit_transform(customer_features[features])
    y = customer_features["Churned"]

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=42, stratify=y)
    model = LogisticRegression(max_iter=1000)
    model.fit(X_train, y_train)
    preds = model.predict(X_test)

    metrics = {
        "Accuracy": round(accuracy_score(y_test, preds), 4),
        "Precision": round(precision_score(y_test, preds, zero_division=0), 4),
        "Recall": round(recall_score(y_test, preds, zero_division=0), 4),
        "Churned_Customers": int(customer_features["Churned"].sum()),
        "Active_Customers": int((customer_features["Churned"] == 0).sum()),
    }
    log.info("Churn model refreshed. Accuracy = %.4f, Recall = %.4f", metrics["Accuracy"], metrics["Recall"])
    return metrics


# ---------------------------------------------------------------------------
# 4. Export
# ---------------------------------------------------------------------------

def export_reports(kpis: pd.DataFrame, category_summary: pd.DataFrame, top_customers: pd.DataFrame,
                    monthly_trend: pd.DataFrame, churn_metrics: dict) -> Path:
    """Write every KPI table to CSV and to a single multi-sheet Excel workbook."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    kpis.to_csv(EXPORT_DIR / f"kpi_summary_{timestamp}.csv", index=False)
    category_summary.to_csv(EXPORT_DIR / f"category_summary_{timestamp}.csv", index=False)
    top_customers.to_csv(EXPORT_DIR / f"top_customers_{timestamp}.csv", index=False)
    monthly_trend.to_csv(EXPORT_DIR / f"monthly_trend_{timestamp}.csv", index=False)

    churn_df = pd.DataFrame([churn_metrics])

    workbook_path = EXPORT_DIR / f"apexplanet_pipeline_report_{timestamp}.xlsx"
    with pd.ExcelWriter(workbook_path, engine="openpyxl") as writer:
        kpis.to_excel(writer, sheet_name="KPI Summary", index=False)
        category_summary.to_excel(writer, sheet_name="Category Performance", index=False)
        top_customers.to_excel(writer, sheet_name="Top 10 Customers", index=False)
        monthly_trend.to_excel(writer, sheet_name="Monthly Sales Trend", index=False)
        churn_df.to_excel(writer, sheet_name="Churn Model Refresh", index=False)

    log.info("Exported KPI report workbook to %s", workbook_path)
    return workbook_path


def send_email_report(workbook_path: Path, kpis: pd.DataFrame) -> None:
    """Optional step: email the KPI workbook to a configured recipient.

    Disabled unless --send-email is passed and the required SMTP
    environment variables are set. Credentials are read from the
    environment only, never hardcoded, so this is safe to commit.
    """
    required_vars = ["SMTP_HOST", "SMTP_PORT", "SMTP_USER", "SMTP_PASSWORD", "REPORT_RECIPIENT"]
    missing = [v for v in required_vars if not os.getenv(v)]
    if missing:
        log.warning("Email step skipped, missing environment variables: %s", ", ".join(missing))
        return

    msg = EmailMessage()
    msg["Subject"] = f"ApexPlanet Superstore Pipeline Report, {datetime.now().strftime('%Y-%m-%d')}"
    msg["From"] = os.environ["SMTP_USER"]
    msg["To"] = os.environ["REPORT_RECIPIENT"]

    kpi_lines = "\n".join(f"{row.Metric}: {row.Value}" for row in kpis.itertuples())
    msg.set_content(f"The latest ApexPlanet Superstore pipeline run has completed.\n\n{kpi_lines}")

    with open(workbook_path, "rb") as f:
        msg.add_attachment(
            f.read(), maintype="application",
            subtype="vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            filename=workbook_path.name,
        )

    with smtplib.SMTP(os.environ["SMTP_HOST"], int(os.environ["SMTP_PORT"])) as server:
        server.starttls()
        server.login(os.environ["SMTP_USER"], os.environ["SMTP_PASSWORD"])
        server.send_message(msg)

    log.info("Report emailed to %s", os.environ["REPORT_RECIPIENT"])


# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def run_pipeline(send_email: bool = False) -> Path:
    log.info("Pipeline run started.")
    raw_df = extract_data()
    clean_df = clean_data(raw_df)
    load_to_database(clean_df)

    kpis = compute_kpis(clean_df)
    category_summary = compute_category_summary(clean_df)
    top_customers = compute_top_customers(clean_df)
    monthly_trend = compute_monthly_trend(clean_df)
    churn_metrics = refresh_churn_model(clean_df)

    workbook_path = export_reports(kpis, category_summary, top_customers, monthly_trend, churn_metrics)

    if send_email:
        send_email_report(workbook_path, kpis)

    log.info("Pipeline run completed successfully.")
    return workbook_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="ApexPlanet Superstore analytics automation pipeline.")
    parser.add_argument("--send-email", action="store_true", help="Email the KPI workbook after the run.")
    return parser.parse_args()


if __name__ == "__main__":
    args = parse_args()
    run_pipeline(send_email=args.send_email)
