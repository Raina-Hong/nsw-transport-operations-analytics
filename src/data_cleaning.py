"""
Data cleaning functions for the NSW Transport Operations Analytics project.

This module cleans:
1. NSW Opal monthly trip data
2. NSW train station entry/exit flow data
3. Sydney Airport BOM weather data
4. NSW public holiday data

The functions are designed to be reused by notebooks or scripts.
"""

from pathlib import Path
import pandas as pd
import numpy as np


def standardise_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Standardise column names into lower_snake_case.
    """
    df = df.copy()
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )
    return df


def clean_opal_trips(opal_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Clean NSW Opal monthly trips data.

    Expected raw columns include:
    - Year_Month
    - Card Type
    - Travel Mode
    - Trip

    Returns a clean monthly demand table with:
    - year_month
    - year
    - month
    - month_name
    - card_type
    - transport_mode
    - trip_count
    """
    opal = standardise_columns(opal_raw)

    opal["year_month"] = pd.to_datetime(opal["year_month"], format="%b-%Y", errors="coerce")

    opal["year"] = opal["year_month"].dt.year
    opal["month"] = opal["year_month"].dt.month
    opal["month_name"] = opal["year_month"].dt.month_name()

    opal["trip"] = (
        opal["trip"]
        .astype(str)
        .str.replace(",", "", regex=False)
        .astype(float)
    )

    opal = opal.rename(columns={
        "travel_mode": "transport_mode",
        "trip": "trip_count"
    })

    opal = opal[
        (opal["year"] >= 2020) &
        (opal["year"] <= 2025)
    ].copy()

    opal = opal[
        [
            "year_month",
            "year",
            "month",
            "month_name",
            "card_type",
            "transport_mode",
            "trip_count"
        ]
    ]

    return opal


def clean_station_flow(station_flow_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Clean NSW train station entries and exits data.

    The source file has long time-window column names, so this function
    renames them into cleaner operational fields and creates station-level
    pressure indicators.

    Returns:
    - yearly station entries/exits
    - total flow
    - peak flow
    - entry-exit imbalance
    - bottleneck score
    """
    station_flow = station_flow_raw.copy()

    station_flow = station_flow.rename(columns={
        "YEAR": "year",
        "STATION": "station_name",
        "Entries 06:00 to 10:00": "morning_entries",
        "Exits 06:00 to 10:00": "morning_exits",
        "Entries 10:00 to 15:00": "midday_entries",
        "Exits 10:00 to 15:00": "midday_exits",
        "Entries 15:00 to 19:00": "evening_entries",
        "Exits 15:00 to 19:00": "evening_exits",
        "Entries 19:00  to 06:00": "night_entries",
        "Exits 19:00  to 06:00": "night_exits",
        "Entries 24 hours": "total_entries",
        "Exits 24 hours": "total_exits"
    })

    station_flow["year"] = pd.to_numeric(station_flow["year"], errors="coerce")
    station_flow = station_flow.dropna(subset=["year"]).copy()
    station_flow["year"] = station_flow["year"].astype(int)

    numeric_cols = [
        "morning_entries", "morning_exits",
        "midday_entries", "midday_exits",
        "evening_entries", "evening_exits",
        "night_entries", "night_exits",
        "total_entries", "total_exits"
    ]

    for col in numeric_cols:
        station_flow[col] = (
            station_flow[col]
            .astype(str)
            .str.replace(",", "", regex=False)
            .str.replace("-", "0", regex=False)
            .str.strip()
        )
        station_flow[col] = pd.to_numeric(station_flow[col], errors="coerce").fillna(0)

    station_flow["station_name"] = (
        station_flow["station_name"]
        .astype(str)
        .str.strip()
    )

    station_flow = station_flow[
        (station_flow["year"] >= 2020) &
        (station_flow["year"] <= 2025)
    ].copy()

    station_flow["total_flow"] = (
        station_flow["total_entries"] +
        station_flow["total_exits"]
    )

    station_flow["morning_total_flow"] = (
        station_flow["morning_entries"] +
        station_flow["morning_exits"]
    )

    station_flow["midday_total_flow"] = (
        station_flow["midday_entries"] +
        station_flow["midday_exits"]
    )

    station_flow["evening_total_flow"] = (
        station_flow["evening_entries"] +
        station_flow["evening_exits"]
    )

    station_flow["night_total_flow"] = (
        station_flow["night_entries"] +
        station_flow["night_exits"]
    )

    station_flow["entry_exit_imbalance"] = (
        station_flow["total_entries"] -
        station_flow["total_exits"]
    )

    station_flow["peak_total_flow"] = (
        station_flow["morning_total_flow"] +
        station_flow["evening_total_flow"]
    )

    station_flow["bottleneck_score"] = np.where(
        station_flow["total_flow"] > 0,
        station_flow["peak_total_flow"] / station_flow["total_flow"],
        0
    )

    station_flow["station_id"] = (
        station_flow["station_name"]
        .str.lower()
        .str.replace(" station", "", regex=False)
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    station_flow = station_flow[
        [
            "year",
            "station_id",
            "station_name",
            "morning_entries",
            "morning_exits",
            "midday_entries",
            "midday_exits",
            "evening_entries",
            "evening_exits",
            "night_entries",
            "night_exits",
            "total_entries",
            "total_exits",
            "total_flow",
            "morning_total_flow",
            "midday_total_flow",
            "evening_total_flow",
            "night_total_flow",
            "peak_total_flow",
            "entry_exit_imbalance",
            "bottleneck_score"
        ]
    ]

    return station_flow


def create_date_from_bom(df: pd.DataFrame) -> pd.DataFrame:
    """
    Create a date column from BOM Year, Month and Day columns.
    """
    df = df.copy()
    df["date"] = pd.to_datetime(
        df[["Year", "Month", "Day"]],
        errors="coerce"
    )
    return df


def clean_weather_data(
    rainfall_raw: pd.DataFrame,
    max_temp_raw: pd.DataFrame,
    min_temp_raw: pd.DataFrame
) -> pd.DataFrame:
    """
    Clean and merge daily weather data from BOM.

    Inputs:
    - daily rainfall
    - daily maximum temperature
    - daily minimum temperature

    Returns a daily weather dimension with rainfall, temperature,
    rainy-day flag and simple weather category.
    """
    rainfall = create_date_from_bom(rainfall_raw)
    rainfall = rainfall.rename(columns={
        "Rainfall amount (millimetres)": "rainfall_mm"
    })
    rainfall = rainfall[["date", "rainfall_mm", "Quality"]].rename(columns={
        "Quality": "rainfall_quality"
    })

    max_temp = create_date_from_bom(max_temp_raw)
    max_temp = max_temp.rename(columns={
        "Maximum temperature (Degree C)": "max_temp"
    })
    max_temp = max_temp[["date", "max_temp", "Quality"]].rename(columns={
        "Quality": "max_temp_quality"
    })

    min_temp = create_date_from_bom(min_temp_raw)
    min_temp = min_temp.rename(columns={
        "Minimum temperature (Degree C)": "min_temp"
    })
    min_temp = min_temp[["date", "min_temp", "Quality"]].rename(columns={
        "Quality": "min_temp_quality"
    })

    weather = (
        rainfall
        .merge(max_temp, on="date", how="outer")
        .merge(min_temp, on="date", how="outer")
    )

    weather = weather[
        (weather["date"] >= "2020-01-01") &
        (weather["date"] <= "2025-12-31")
    ].copy()

    weather = weather.sort_values("date").reset_index(drop=True)

    weather["rainfall_mm"] = weather["rainfall_mm"].fillna(0)
    weather["is_rainy"] = weather["rainfall_mm"] > 0

    weather["weather_category"] = weather.apply(classify_weather, axis=1)

    weather = weather[
        [
            "date",
            "rainfall_mm",
            "max_temp",
            "min_temp",
            "is_rainy",
            "weather_category",
            "rainfall_quality",
            "max_temp_quality",
            "min_temp_quality"
        ]
    ]

    return weather


def classify_weather(row: pd.Series) -> str:
    """
    Classify daily weather into a simple operational category.
    """
    if row["rainfall_mm"] >= 10:
        return "Heavy Rain"
    elif row["rainfall_mm"] > 0:
        return "Rainy"
    elif pd.notna(row["max_temp"]) and row["max_temp"] >= 30:
        return "Hot"
    elif pd.notna(row["max_temp"]) and row["max_temp"] <= 15:
        return "Cool"
    else:
        return "Clear / Mild"


def clean_public_holidays(holidays_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Clean NSW public holiday data.

    The notebook uses the public holiday table to enrich the date dimension.
    This function standardises the date field and keeps the holiday name.
    """
    holidays = holidays_raw.copy()
    holidays.columns = (
        holidays.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    date_col_candidates = ["date", "holiday_date"]
    name_col_candidates = ["holiday_name", "name", "holiday"]

    date_col = next((col for col in date_col_candidates if col in holidays.columns), None)
    name_col = next((col for col in name_col_candidates if col in holidays.columns), None)

    if date_col is None:
        raise ValueError("No valid date column found in public holidays data.")

    holidays["date"] = pd.to_datetime(holidays[date_col], errors="coerce")

    if name_col is None:
        holidays["holiday_name"] = "Public Holiday"
    else:
        holidays["holiday_name"] = holidays[name_col].astype(str).str.strip()

    holidays = holidays.dropna(subset=["date"]).copy()
    holidays["is_holiday"] = True

    holidays = holidays[
        (holidays["date"] >= "2020-01-01") &
        (holidays["date"] <= "2025-12-31")
    ].copy()

    holidays = holidays[["date", "holiday_name", "is_holiday"]].drop_duplicates()

    return holidays


def export_cleaned_datasets(
    opal: pd.DataFrame,
    station_flow: pd.DataFrame,
    weather: pd.DataFrame,
    output_dir: str | Path
) -> None:
    """
    Export cleaned datasets to data/processed.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    opal.to_csv(output_dir / "clean_opal_trips.csv", index=False)
    station_flow.to_csv(output_dir / "clean_station_flow.csv", index=False)
    weather.to_csv(output_dir / "clean_weather.csv", index=False)