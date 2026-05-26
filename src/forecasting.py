"""
Forecasting utilities for the NSW Transport Operations Analytics project.

This module builds a monthly transport demand forecasting workflow using
lagged demand, rolling averages, weather features, calendar features and
transport mode indicators.
"""

from pathlib import Path
import pandas as pd
import numpy as np

from sklearn.compose import ColumnTransformer
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score


CATEGORICAL_FEATURES = ["transport_mode", "season"]

NUMERIC_FEATURES = [
    "year",
    "month_num",
    "quarter",
    "avg_rainfall_mm",
    "total_rainfall_mm",
    "rainy_days",
    "avg_max_temp",
    "avg_min_temp",
    "lag_1_demand",
    "lag_3_demand",
    "rolling_3m_avg",
    "rolling_6m_avg"
]

FEATURE_COLS = [
    "year",
    "month_num",
    "quarter",
    "transport_mode",
    "season",
    "avg_rainfall_mm",
    "total_rainfall_mm",
    "rainy_days",
    "avg_max_temp",
    "avg_min_temp",
    "lag_1_demand",
    "lag_3_demand",
    "rolling_3m_avg",
    "rolling_6m_avg"
]


def assign_season_from_month(month: int) -> str:
    """Assign Australian season from month number."""
    if month in [12, 1, 2]:
        return "Summer"
    if month in [3, 4, 5]:
        return "Autumn"
    if month in [6, 7, 8]:
        return "Winter"
    return "Spring"


def prepare_forecast_dataset(
    fact_monthly_opal_trips: pd.DataFrame,
    monthly_weather: pd.DataFrame
) -> pd.DataFrame:
    """
    Prepare monthly demand data for forecasting.

    The model predicts monthly trip_count by transport mode. Weather features
    are merged at month level.
    """
    fact = fact_monthly_opal_trips.copy()
    fact["year_month"] = pd.to_datetime(fact["year_month"], errors="coerce")

    forecast_df = (
        fact
        .groupby(
            ["year_month", "year", "month", "month_name", "transport_mode"],
            as_index=False
        )
        .agg(trip_count=("trip_count", "sum"))
    )

    forecast_df["month_id"] = (
        forecast_df["year"].astype(str)
        + "-"
        + forecast_df["month"].astype(str).str.zfill(2)
    )

    weather_features = monthly_weather[
        [
            "month_id",
            "avg_rainfall_mm",
            "total_rainfall_mm",
            "rainy_days",
            "avg_max_temp",
            "avg_min_temp"
        ]
    ].drop_duplicates()

    forecast_df = forecast_df.merge(weather_features, on="month_id", how="left")
    forecast_df = forecast_df.sort_values(["transport_mode", "year_month"]).reset_index(drop=True)

    return forecast_df


def create_forecasting_features(forecast_df: pd.DataFrame) -> pd.DataFrame:
    """Create calendar, seasonal, lag and rolling average features."""
    forecast_features = forecast_df.copy()
    forecast_features["year_month"] = pd.to_datetime(
        forecast_features["year_month"],
        errors="coerce"
    )

    forecast_features["quarter"] = forecast_features["year_month"].dt.quarter
    forecast_features["month_num"] = forecast_features["year_month"].dt.month
    forecast_features["season"] = forecast_features["month_num"].apply(assign_season_from_month)

    # Use lagged demand to avoid data leakage from the current month.
    forecast_features["lag_1_demand"] = (
        forecast_features
        .groupby("transport_mode")["trip_count"]
        .shift(1)
    )

    forecast_features["lag_3_demand"] = (
        forecast_features
        .groupby("transport_mode")["trip_count"]
        .shift(3)
    )

    forecast_features["rolling_3m_avg"] = (
        forecast_features
        .groupby("transport_mode")["trip_count"]
        .transform(lambda x: x.shift(1).rolling(window=3).mean())
    )

    forecast_features["rolling_6m_avg"] = (
        forecast_features
        .groupby("transport_mode")["trip_count"]
        .transform(lambda x: x.shift(1).rolling(window=6).mean())
    )

    forecast_features = forecast_features.dropna(subset=[
        "lag_1_demand",
        "lag_3_demand",
        "rolling_3m_avg",
        "rolling_6m_avg"
    ]).copy()

    return forecast_features


def train_test_split_by_year(
    forecast_features: pd.DataFrame,
    test_year: int = 2025
):
    """
    Split forecasting data by year.

    Training uses records before the test year, while testing uses the test
    year. This avoids random splitting for time-series style forecasting.
    """
    target_col = "trip_count"

    base_cols = ["year_month", "month_id", "transport_mode", target_col]
    model_cols = list(dict.fromkeys(base_cols + FEATURE_COLS))
    model_data = forecast_features[model_cols].copy()

    train_data = model_data[model_data["year"] < test_year].copy()
    test_data = model_data[model_data["year"] == test_year].copy()

    X_train = train_data[FEATURE_COLS]
    y_train = train_data[target_col]

    X_test = test_data[FEATURE_COLS]
    y_test = test_data[target_col]

    return train_data, test_data, X_train, X_test, y_train, y_test


def mean_absolute_percentage_error(y_true, y_pred, min_actual: float = 1000) -> float:
    """
    Calculate adjusted MAPE while excluding very small actual demand values.

    Standard MAPE can become unstable when actual demand is close to zero.
    This adjusted version only calculates MAPE for observations where actual
    demand is greater than min_actual.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    valid_mask = y_true > min_actual

    if valid_mask.sum() == 0:
        return np.nan

    return np.mean(
        np.abs((y_true[valid_mask] - y_pred[valid_mask]) / y_true[valid_mask])
    ) * 100


def weighted_mean_absolute_percentage_error(y_true, y_pred) -> float:
    """
    Calculate Weighted Mean Absolute Percentage Error.

    WMAPE measures total absolute forecast error as a percentage of total
    actual demand. It is more stable than standard MAPE for transport demand
    data where different modes can have very different passenger volumes.
    """
    y_true = np.array(y_true)
    y_pred = np.array(y_pred)

    denominator = np.sum(np.abs(y_true))

    if denominator == 0:
        return np.nan

    return np.sum(np.abs(y_true - y_pred)) / denominator * 100


def evaluate_model(model_name: str, y_true, y_pred) -> dict:
    """
    Evaluate a forecasting model using absolute and percentage-based metrics.
    """
    mae = mean_absolute_error(y_true, y_pred)
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    adjusted_mape = mean_absolute_percentage_error(y_true, y_pred, min_actual=1000)
    wmape = weighted_mean_absolute_percentage_error(y_true, y_pred)
    r2 = r2_score(y_true, y_pred)

    return {
        "model": model_name,
        "MAE": mae,
        "RMSE": rmse,
        "Adjusted_MAPE": adjusted_mape,
        "WMAPE": wmape,
        "R2": r2
    }


def build_preprocessor() -> ColumnTransformer:
    """Build preprocessing pipeline for categorical and numeric features."""
    return ColumnTransformer(
        transformers=[
            ("cat", OneHotEncoder(handle_unknown="ignore"), CATEGORICAL_FEATURES),
            ("num", "passthrough", NUMERIC_FEATURES)
        ]
    )


def train_baseline_model(test_data: pd.DataFrame, y_test) -> tuple[np.ndarray, dict]:
    """Train a naive baseline using previous month demand."""
    baseline_pred = test_data["lag_1_demand"].values

    baseline_metrics = evaluate_model(
        "Naive Baseline",
        y_test,
        baseline_pred
    )

    return baseline_pred, baseline_metrics


def train_linear_regression(X_train, y_train, X_test, y_test):
    """Train a Linear Regression model."""
    linear_model = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("model", LinearRegression())
        ]
    )

    linear_model.fit(X_train, y_train)
    linear_pred = linear_model.predict(X_test)

    linear_metrics = evaluate_model(
        "Linear Regression",
        y_test,
        linear_pred
    )

    return linear_model, linear_pred, linear_metrics


def train_random_forest(X_train, y_train, X_test, y_test):
    """Train a Random Forest forecasting model."""
    rf_model = Pipeline(
        steps=[
            ("preprocessor", build_preprocessor()),
            ("model", RandomForestRegressor(
                n_estimators=300,
                max_depth=8,
                random_state=42
            ))
        ]
    )

    rf_model.fit(X_train, y_train)
    rf_pred = rf_model.predict(X_test)

    rf_metrics = evaluate_model(
        "Random Forest",
        y_test,
        rf_pred
    )

    return rf_model, rf_pred, rf_metrics


def create_forecast_results(
    test_data: pd.DataFrame,
    baseline_pred,
    linear_pred,
    rf_pred
) -> pd.DataFrame:
    """Create a model output table for dashboarding and reporting."""
    forecast_results = test_data[
        [
            "year_month",
            "month_id",
            "transport_mode",
            "trip_count",
            "lag_1_demand"
        ]
    ].copy()

    forecast_results = forecast_results.rename(columns={
        "trip_count": "actual_demand",
        "lag_1_demand": "baseline_prediction"
    })

    forecast_results["linear_regression_prediction"] = linear_pred
    forecast_results["random_forest_prediction"] = rf_pred

    forecast_results["rf_error"] = (
        forecast_results["actual_demand"] -
        forecast_results["random_forest_prediction"]
    )

    forecast_results["rf_abs_error"] = forecast_results["rf_error"].abs()

    forecast_results["rf_abs_percentage_error"] = np.where(
        forecast_results["actual_demand"] > 1000,
        forecast_results["rf_abs_error"] / forecast_results["actual_demand"] * 100,
        np.nan
    )

    return forecast_results


def get_random_forest_feature_importance(rf_model: Pipeline) -> pd.DataFrame:
    """Extract feature importance from the fitted Random Forest pipeline."""
    preprocessor_fitted = rf_model.named_steps["preprocessor"]
    rf_fitted = rf_model.named_steps["model"]

    cat_feature_names = (
        preprocessor_fitted
        .named_transformers_["cat"]
        .get_feature_names_out(CATEGORICAL_FEATURES)
    )

    all_feature_names = list(cat_feature_names) + NUMERIC_FEATURES

    feature_importance = pd.DataFrame({
        "feature": all_feature_names,
        "importance": rf_fitted.feature_importances_
    })

    return feature_importance.sort_values("importance", ascending=False)


def run_forecasting_workflow(
    fact_monthly_opal_trips: pd.DataFrame,
    monthly_weather: pd.DataFrame,
    output_dir: str | Path | None = None,
    test_year: int = 2025
) -> dict:
    """
    Run the full forecasting workflow and optionally export model outputs.
    """
    forecast_df = prepare_forecast_dataset(
        fact_monthly_opal_trips=fact_monthly_opal_trips,
        monthly_weather=monthly_weather
    )

    forecast_features = create_forecasting_features(forecast_df)

    train_data, test_data, X_train, X_test, y_train, y_test = train_test_split_by_year(
        forecast_features,
        test_year=test_year
    )

    baseline_pred, baseline_metrics = train_baseline_model(test_data, y_test)

    linear_model, linear_pred, linear_metrics = train_linear_regression(
        X_train, y_train, X_test, y_test
    )

    rf_model, rf_pred, rf_metrics = train_random_forest(
        X_train, y_train, X_test, y_test
    )

    model_metrics = pd.DataFrame([
        baseline_metrics,
        linear_metrics,
        rf_metrics
    ]).sort_values("RMSE")

    forecast_results = create_forecast_results(
        test_data=test_data,
        baseline_pred=baseline_pred,
        linear_pred=linear_pred,
        rf_pred=rf_pred
    )

    feature_importance = get_random_forest_feature_importance(rf_model)

    if output_dir is not None:
        output_dir = Path(output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)

        model_metrics.to_csv(output_dir / "model_metrics.csv", index=False)
        forecast_results.to_csv(output_dir / "forecast_results.csv", index=False)
        feature_importance.to_csv(output_dir / "feature_importance.csv", index=False)

    return {
        "model_metrics": model_metrics,
        "forecast_results": forecast_results,
        "feature_importance": feature_importance,
        "linear_model": linear_model,
        "random_forest_model": rf_model
    }
