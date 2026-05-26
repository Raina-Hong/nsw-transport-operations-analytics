"""
Feature engineering and table-building functions for the NSW Transport
Operations Analytics project.

This module creates:
1. Date dimension table
2. GTFS station dimension table
3. GTFS route dimension table
4. Final fact and dimension tables
5. Monthly weather features for modelling and dashboard analysis
"""

from pathlib import Path
import pandas as pd
import numpy as np


def assign_season(month: int) -> str:
    """
    Assign Australian season based on month.
    """
    if month in [12, 1, 2]:
        return "Summer"
    elif month in [3, 4, 5]:
        return "Autumn"
    elif month in [6, 7, 8]:
        return "Winter"
    else:
        return "Spring"


def create_date_dimension(
    start_date: str = "2020-01-01",
    end_date: str = "2025-12-31",
    holidays: pd.DataFrame | None = None
) -> pd.DataFrame:
    """
    Create a daily date dimension table.

    If a cleaned public holiday table is provided, the date dimension
    will include is_holiday and holiday_name fields.
    """
    date_range = pd.date_range(
        start=start_date,
        end=end_date,
        freq="D"
    )

    dim_date = pd.DataFrame({"date": date_range})

    dim_date["year"] = dim_date["date"].dt.year
    dim_date["quarter"] = dim_date["date"].dt.quarter
    dim_date["month"] = dim_date["date"].dt.month
    dim_date["month_name"] = dim_date["date"].dt.month_name()
    dim_date["day"] = dim_date["date"].dt.day
    dim_date["weekday"] = dim_date["date"].dt.weekday
    dim_date["weekday_name"] = dim_date["date"].dt.day_name()
    dim_date["is_weekend"] = dim_date["weekday"].isin([5, 6])
    dim_date["season"] = dim_date["month"].apply(assign_season)

    if holidays is not None and not holidays.empty:
        holidays = holidays.copy()
        holidays["date"] = pd.to_datetime(holidays["date"], errors="coerce")

        dim_date = dim_date.merge(
            holidays[["date", "holiday_name", "is_holiday"]],
            on="date",
            how="left"
        )

        dim_date["is_holiday"] = dim_date["is_holiday"].fillna(False)
        dim_date["holiday_name"] = dim_date["holiday_name"].fillna("Non-Holiday")
    else:
        dim_date["is_holiday"] = False
        dim_date["holiday_name"] = "Non-Holiday"

    dim_date["year_month"] = dim_date["date"].dt.to_period("M").astype(str)

    dim_date = dim_date[
        [
            "date",
            "year",
            "quarter",
            "month",
            "month_name",
            "day",
            "weekday",
            "weekday_name",
            "is_weekend",
            "is_holiday",
            "holiday_name",
            "season",
            "year_month"
        ]
    ]

    return dim_date


def assign_sydney_region(lat: float, lon: float) -> str:
    """
    Assign a simplified Greater Sydney operational region based on coordinates.

    This is not an official administrative boundary. It is used only as a
    lightweight dashboard grouping feature.
    """
    if pd.isna(lat) or pd.isna(lon):
        return "Unknown"

    if (-33.90 <= lat <= -33.84) and (151.18 <= lon <= 151.23):
        return "Sydney CBD"

    if lon < 151.05:
        return "Western Sydney"
    elif lon > 151.23:
        return "Eastern Sydney"
    elif lat < -33.82:
        return "Northern Sydney"
    elif lat > -33.96:
        return "Southern Sydney"
    else:
        return "Inner Sydney"


def clean_gtfs_stops(stops_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Clean GTFS stops.txt and create a station dimension table.

    The station_id is created from the stop name so that it can be matched
    with the station flow table where possible.
    """
    stops = stops_raw.copy()

    stops.columns = (
        stops.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    station_cols = [
        "stop_id",
        "stop_name",
        "stop_lat",
        "stop_lon",
        "location_type",
        "parent_station",
        "wheelchair_boarding"
    ]

    available_station_cols = [col for col in station_cols if col in stops.columns]
    stops = stops[available_station_cols].copy()

    stops["stop_name"] = stops["stop_name"].astype(str).str.strip()

    stops = stops.dropna(subset=["stop_lat", "stop_lon"]).copy()

    stops = stops[
        (stops["stop_lat"].between(-38, -28)) &
        (stops["stop_lon"].between(140, 154))
    ].copy()

    stops["station_name_clean"] = (
        stops["stop_name"]
        .str.lower()
        .str.replace(" station", "", regex=False)
        .str.replace(r"[^a-z0-9]+", "_", regex=True)
        .str.strip("_")
    )

    stops["region"] = stops.apply(
        lambda row: assign_sydney_region(row["stop_lat"], row["stop_lon"]),
        axis=1
    )

    dim_station = stops.rename(columns={
        "stop_id": "station_id_gtfs",
        "stop_name": "station_name",
        "station_name_clean": "station_id"
    })

    dim_station = dim_station[
        [
            "station_id",
            "station_id_gtfs",
            "station_name",
            "stop_lat",
            "stop_lon",
            "region"
        ]
    ].drop_duplicates()

    return dim_station


def clean_gtfs_routes(routes_raw: pd.DataFrame) -> pd.DataFrame:
    """
    Clean GTFS routes.txt and create a route dimension table.
    """
    routes = routes_raw.copy()

    routes.columns = (
        routes.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_", regex=False)
    )

    route_type_mapping = {
        0: "Tram / Light Rail",
        1: "Subway / Metro",
        2: "Rail",
        3: "Bus",
        4: "Ferry",
        7: "Funicular",
        100: "Railway Service",
        109: "Suburban Railway",
        700: "Bus Service",
        714: "Rail Replacement Bus",
        900: "Tram Service",
        1000: "Ferry Service"
    }

    routes["transport_mode"] = routes["route_type"].map(route_type_mapping).fillna("Other")

    dim_route = routes[
        [
            "route_id",
            "agency_id",
            "route_short_name",
            "route_long_name",
            "route_type",
            "transport_mode"
        ]
    ].drop_duplicates()

    return dim_route


def create_fact_monthly_opal_trips(opal: pd.DataFrame) -> pd.DataFrame:
    """
    Create the final monthly Opal trips fact table.
    """
    fact_monthly_opal_trips = opal.copy()

    fact_monthly_opal_trips["month_id"] = (
        fact_monthly_opal_trips["year"].astype(str)
        + "-"
        + fact_monthly_opal_trips["month"].astype(str).str.zfill(2)
    )

    fact_monthly_opal_trips = fact_monthly_opal_trips[
        [
            "month_id",
            "year_month",
            "year",
            "month",
            "month_name",
            "card_type",
            "transport_mode",
            "trip_count"
        ]
    ]

    return fact_monthly_opal_trips


def create_fact_station_flow(station_flow: pd.DataFrame) -> pd.DataFrame:
    """
    Create the final station flow fact table.
    """
    fact_station_flow = station_flow.copy()

    fact_station_flow["station_flow_id"] = (
        fact_station_flow["year"].astype(str)
        + "_"
        + fact_station_flow["station_id"]
    )

    fact_station_flow = fact_station_flow[
        [
            "station_flow_id",
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

    return fact_station_flow


def create_dim_weather(weather: pd.DataFrame) -> pd.DataFrame:
    """
    Create the weather dimension table used for dashboarding and modelling.
    """
    dim_weather = weather.copy()

    dim_weather = dim_weather[
        [
            "date",
            "rainfall_mm",
            "max_temp",
            "min_temp",
            "is_rainy",
            "weather_category"
        ]
    ]

    return dim_weather


def create_monthly_weather_features(dim_weather: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate daily weather data into monthly weather features.

    These features are used for:
    - SQL / dashboard weather-demand analysis
    - forecasting model input
    """
    weather = dim_weather.copy()
    weather["date"] = pd.to_datetime(weather["date"], errors="coerce")

    weather["year"] = weather["date"].dt.year
    weather["month"] = weather["date"].dt.month
    weather["month_id"] = (
        weather["year"].astype(str)
        + "-"
        + weather["month"].astype(str).str.zfill(2)
    )

    monthly_weather = (
        weather
        .groupby(["year", "month", "month_id"], as_index=False)
        .agg(
            avg_rainfall_mm=("rainfall_mm", "mean"),
            total_rainfall_mm=("rainfall_mm", "sum"),
            rainy_days=("is_rainy", "sum"),
            avg_max_temp=("max_temp", "mean"),
            avg_min_temp=("min_temp", "mean")
        )
    )

    return monthly_weather


def create_monthly_demand_weather(
    monthly_demand: pd.DataFrame,
    dim_weather: pd.DataFrame
) -> pd.DataFrame:
    """
    Merge monthly demand trend with monthly weather features.
    """
    monthly_weather = create_monthly_weather_features(dim_weather)

    monthly_demand_weather = monthly_demand.copy()

    monthly_demand_weather["month_id"] = (
        monthly_demand_weather["year"].astype(str)
        + "-"
        + monthly_demand_weather["month"].astype(str).str.zfill(2)
    )

    monthly_demand_weather = monthly_demand_weather.merge(
        monthly_weather,
        on=["year", "month", "month_id"],
        how="left"
    )

    return monthly_demand_weather


def export_final_tables(
    fact_monthly_opal_trips: pd.DataFrame,
    fact_station_flow: pd.DataFrame,
    dim_date: pd.DataFrame,
    dim_station: pd.DataFrame,
    dim_route: pd.DataFrame,
    dim_weather: pd.DataFrame,
    output_dir: str | Path
) -> None:
    """
    Export final fact and dimension tables to data/final.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    fact_monthly_opal_trips.to_csv(output_dir / "fact_monthly_opal_trips.csv", index=False)
    fact_station_flow.to_csv(output_dir / "fact_station_flow.csv", index=False)
    dim_date.to_csv(output_dir / "dim_date.csv", index=False)
    dim_station.to_csv(output_dir / "dim_station.csv", index=False)
    dim_route.to_csv(output_dir / "dim_route.csv", index=False)
    dim_weather.to_csv(output_dir / "dim_weather.csv", index=False)
