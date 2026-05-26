"""
DuckDB utilities and SQL analysis queries for the NSW Transport Operations
Analytics project.

This module connects to DuckDB, loads final CSV tables, creates SQL tables,
runs reusable SQL analyses and exports results to CSV.
"""

from pathlib import Path
import pandas as pd
import duckdb


FINAL_TABLES = {
    "fact_monthly_opal_trips": "fact_monthly_opal_trips.csv",
    "fact_station_flow": "fact_station_flow.csv",
    "dim_date": "dim_date.csv",
    "dim_station": "dim_station.csv",
    "dim_route": "dim_route.csv",
    "dim_weather": "dim_weather.csv"
}


def connect_duckdb(db_path: str | Path) -> duckdb.DuckDBPyConnection:
    """Connect to a DuckDB database."""
    db_path = Path(db_path)
    db_path.parent.mkdir(parents=True, exist_ok=True)
    return duckdb.connect(database=str(db_path), read_only=False)


def load_final_tables(final_dir: str | Path) -> dict[str, pd.DataFrame]:
    """Load final fact and dimension CSV tables from data/final."""
    final_dir = Path(final_dir)
    tables = {}

    for table_name, file_name in FINAL_TABLES.items():
        file_path = final_dir / file_name

        if not file_path.exists():
            raise FileNotFoundError(f"Missing final table: {file_path}")

        df = pd.read_csv(file_path)

        if table_name == "fact_monthly_opal_trips" and "year_month" in df.columns:
            df["year_month"] = pd.to_datetime(df["year_month"], errors="coerce")

        if table_name in ["dim_date", "dim_weather"] and "date" in df.columns:
            df["date"] = pd.to_datetime(df["date"], errors="coerce")

        tables[table_name] = df

    return tables


def create_duckdb_tables(
    con: duckdb.DuckDBPyConnection,
    tables: dict[str, pd.DataFrame]
) -> None:
    """Register pandas DataFrames and create DuckDB physical tables."""
    for table_name, df in tables.items():
        con.register(f"{table_name}_df", df)

    create_tables_sql = """
    DROP TABLE IF EXISTS fact_monthly_opal_trips;
    DROP TABLE IF EXISTS fact_station_flow;
    DROP TABLE IF EXISTS dim_date;
    DROP TABLE IF EXISTS dim_station;
    DROP TABLE IF EXISTS dim_route;
    DROP TABLE IF EXISTS dim_weather;

    CREATE TABLE fact_monthly_opal_trips AS
    SELECT * FROM fact_monthly_opal_trips_df;

    CREATE TABLE fact_station_flow AS
    SELECT * FROM fact_station_flow_df;

    CREATE TABLE dim_date AS
    SELECT * FROM dim_date_df;

    CREATE TABLE dim_station AS
    SELECT * FROM dim_station_df;

    CREATE TABLE dim_route AS
    SELECT * FROM dim_route_df;

    CREATE TABLE dim_weather AS
    SELECT * FROM dim_weather_df;
    """

    con.execute(create_tables_sql)


def get_table_row_counts(
    con: duckdb.DuckDBPyConnection,
    table_names: list[str] | None = None
) -> pd.DataFrame:
    """Return row counts for core DuckDB tables."""
    if table_names is None:
        table_names = list(FINAL_TABLES.keys())

    row_counts = []

    for table in table_names:
        count = con.execute(
            f"SELECT COUNT(*) AS row_count FROM {table}"
        ).fetchone()[0]

        row_counts.append({
            "table_name": table,
            "row_count": count
        })

    return pd.DataFrame(row_counts)


SQL_QUERIES = {
    "monthly_demand_trend": """
        SELECT
            year,
            month,
            month_name,
            SUM(trip_count) AS total_trips
        FROM fact_monthly_opal_trips
        GROUP BY year, month, month_name
        ORDER BY year, month;
    """,

    "transport_mode_demand": """
        SELECT
            transport_mode,
            SUM(trip_count) AS total_trips,
            AVG(trip_count) AS avg_monthly_trips
        FROM fact_monthly_opal_trips
        GROUP BY transport_mode
        ORDER BY total_trips DESC;
    """,

    "card_type_demand": """
        SELECT
            card_type,
            SUM(trip_count) AS total_trips,
            AVG(trip_count) AS avg_monthly_trips
        FROM fact_monthly_opal_trips
        GROUP BY card_type
        ORDER BY total_trips DESC;
    """,

    "yearly_mode_demand": """
        SELECT
            year,
            transport_mode,
            SUM(trip_count) AS total_trips
        FROM fact_monthly_opal_trips
        GROUP BY year, transport_mode
        ORDER BY year, total_trips DESC;
    """,

    "top_station_flow": """
        SELECT
            station_name,
            SUM(total_entries) AS total_entries,
            SUM(total_exits) AS total_exits,
            SUM(total_flow) AS total_flow,
            AVG(bottleneck_score) AS avg_bottleneck_score
        FROM fact_station_flow
        GROUP BY station_name
        ORDER BY total_flow DESC
        LIMIT 20;
    """,

    "peak_station_pressure": """
        SELECT
            station_name,
            SUM(morning_total_flow) AS morning_peak_flow,
            SUM(evening_total_flow) AS evening_peak_flow,
            SUM(peak_total_flow) AS total_peak_flow,
            SUM(total_flow) AS total_flow,
            CASE
                WHEN SUM(total_flow) = 0 THEN 0
                ELSE SUM(peak_total_flow) * 1.0 / SUM(total_flow)
            END AS peak_flow_share
        FROM fact_station_flow
        GROUP BY station_name
        HAVING SUM(total_flow) > 0
        ORDER BY peak_flow_share DESC, total_peak_flow DESC
        LIMIT 20;
    """,

    "entry_exit_imbalance": """
        SELECT
            station_name,
            SUM(total_entries) AS total_entries,
            SUM(total_exits) AS total_exits,
            SUM(entry_exit_imbalance) AS net_entry_exit_imbalance,
            ABS(SUM(entry_exit_imbalance)) AS abs_imbalance,
            SUM(total_flow) AS total_flow
        FROM fact_station_flow
        GROUP BY station_name
        HAVING SUM(total_flow) > 0
        ORDER BY abs_imbalance DESC
        LIMIT 20;
    """,

    "yearly_station_flow_trend": """
        SELECT
            year,
            SUM(total_entries) AS total_entries,
            SUM(total_exits) AS total_exits,
            SUM(total_flow) AS total_flow,
            AVG(bottleneck_score) AS avg_bottleneck_score
        FROM fact_station_flow
        GROUP BY year
        ORDER BY year;
    """,

    "monthly_demand_weather": """
        SELECT
            f.year,
            f.month,
            f.month_name,
            CAST(f.year AS VARCHAR) || '-' || LPAD(CAST(f.month AS VARCHAR), 2, '0') AS month_id,
            SUM(f.trip_count) AS total_trips,
            AVG(w.rainfall_mm) AS avg_rainfall_mm,
            SUM(w.rainfall_mm) AS total_rainfall_mm,
            SUM(CASE WHEN w.is_rainy THEN 1 ELSE 0 END) AS rainy_days,
            AVG(w.max_temp) AS avg_max_temp,
            AVG(w.min_temp) AS avg_min_temp
        FROM fact_monthly_opal_trips f
        LEFT JOIN dim_weather w
            ON STRFTIME(w.date, '%Y-%m') = STRFTIME(f.year_month, '%Y-%m')
        GROUP BY f.year, f.month, f.month_name
        ORDER BY f.year, f.month;
    """,
        "weather_demand_relationship": """
        WITH monthly_weather AS (
            SELECT
                STRFTIME(date, '%Y-%m') AS month_id,
                AVG(rainfall_mm) AS avg_rainfall_mm,
                SUM(rainfall_mm) AS total_rainfall_mm,
                SUM(CASE WHEN is_rainy THEN 1 ELSE 0 END) AS rainy_days,
                AVG(max_temp) AS avg_max_temp,
                AVG(min_temp) AS avg_min_temp
            FROM dim_weather
            GROUP BY STRFTIME(date, '%Y-%m')
        ),

        monthly_demand AS (
            SELECT
                STRFTIME(year_month, '%Y-%m') AS month_id,
                year,
                month,
                month_name,
                transport_mode,
                SUM(trip_count) AS total_trips
            FROM fact_monthly_opal_trips
            GROUP BY
                STRFTIME(year_month, '%Y-%m'),
                year,
                month,
                month_name,
                transport_mode
        )

        SELECT
            d.month_id,
            d.year,
            d.month,
            d.month_name,
            d.transport_mode,
            d.total_trips,
            w.avg_rainfall_mm,
            w.total_rainfall_mm,
            w.rainy_days,
            w.avg_max_temp,
            w.avg_min_temp,
            CASE
                WHEN w.rainy_days >= 15 THEN 'High Rainfall Month'
                WHEN w.rainy_days >= 8 THEN 'Moderate Rainfall Month'
                ELSE 'Low Rainfall Month'
            END AS rainfall_month_category
        FROM monthly_demand d
        LEFT JOIN monthly_weather w
            ON d.month_id = w.month_id
        ORDER BY d.year, d.month, d.transport_mode;
    """,

    
    "data_quality_summary": """
        SELECT
            'fact_monthly_opal_trips' AS dataset,
            COUNT(*) AS row_count,
            COUNT(*) - COUNT(DISTINCT month_id || card_type || transport_mode) AS duplicate_count,
            SUM(CASE WHEN trip_count IS NULL THEN 1 ELSE 0 END) AS missing_key_metric_count
        FROM fact_monthly_opal_trips

        UNION ALL

        SELECT
            'fact_station_flow' AS dataset,
            COUNT(*) AS row_count,
            COUNT(*) - COUNT(DISTINCT station_flow_id) AS duplicate_count,
            SUM(CASE WHEN total_flow IS NULL THEN 1 ELSE 0 END) AS missing_key_metric_count
        FROM fact_station_flow

        UNION ALL

        SELECT
            'dim_date' AS dataset,
            COUNT(*) AS row_count,
            COUNT(*) - COUNT(DISTINCT date) AS duplicate_count,
            SUM(CASE WHEN date IS NULL THEN 1 ELSE 0 END) AS missing_key_metric_count
        FROM dim_date

        UNION ALL

        SELECT
            'dim_station' AS dataset,
            COUNT(*) AS row_count,
            COUNT(*) - COUNT(DISTINCT station_id_gtfs) AS duplicate_count,
            SUM(CASE WHEN station_id_gtfs IS NULL THEN 1 ELSE 0 END) AS missing_key_metric_count
        FROM dim_station

        UNION ALL

        SELECT
            'dim_route' AS dataset,
            COUNT(*) AS row_count,
            COUNT(*) - COUNT(DISTINCT route_id) AS duplicate_count,
            SUM(CASE WHEN route_id IS NULL THEN 1 ELSE 0 END) AS missing_key_metric_count
        FROM dim_route

        UNION ALL

        SELECT
            'dim_weather' AS dataset,
            COUNT(*) AS row_count,
            COUNT(*) - COUNT(DISTINCT date) AS duplicate_count,
            SUM(CASE WHEN rainfall_mm IS NULL OR max_temp IS NULL OR min_temp IS NULL THEN 1 ELSE 0 END) AS missing_key_metric_count
        FROM dim_weather;
    """,
        "yoy_mode_demand": """
        WITH monthly_mode_demand AS (
            SELECT
                year,
                month,
                CASE
                    WHEN LOWER(transport_mode) = 'bus' THEN 'Bus'
                    WHEN LOWER(transport_mode) = 'train' THEN 'Train'
                    WHEN LOWER(transport_mode) = 'ferry' THEN 'Ferry'
                    WHEN LOWER(transport_mode) = 'metro' THEN 'Metro'
                    WHEN LOWER(transport_mode) = 'light rail' THEN 'Light Rail'
                    ELSE 'Other'
                END AS transport_mode_clean,
                SUM(trip_count) AS monthly_trips
            FROM fact_monthly_opal_trips
            GROUP BY
                year,
                month,
                CASE
                    WHEN LOWER(transport_mode) = 'bus' THEN 'Bus'
                    WHEN LOWER(transport_mode) = 'train' THEN 'Train'
                    WHEN LOWER(transport_mode) = 'ferry' THEN 'Ferry'
                    WHEN LOWER(transport_mode) = 'metro' THEN 'Metro'
                    WHEN LOWER(transport_mode) = 'light rail' THEN 'Light Rail'
                    ELSE 'Other'
                END
        ),

        latest_data_cutoff AS (
            SELECT
                MAX(year) AS latest_year,
                MAX(month) AS latest_available_month
            FROM monthly_mode_demand
            WHERE year = (
                SELECT MAX(year)
                FROM monthly_mode_demand
            )
        ),

        comparable_ytd_demand AS (
            SELECT
                m.year,
                m.transport_mode_clean,
                SUM(m.monthly_trips) AS total_trips
            FROM monthly_mode_demand m
            CROSS JOIN latest_data_cutoff c
            WHERE m.month <= c.latest_available_month
            GROUP BY
                m.year,
                m.transport_mode_clean
        ),

        ytd_growth AS (
            SELECT
                year,
                transport_mode_clean,
                total_trips,
                LAG(total_trips) OVER (
                    PARTITION BY transport_mode_clean
                    ORDER BY year
                ) AS previous_year_trips
            FROM comparable_ytd_demand
        )

        SELECT
            year,
            transport_mode_clean AS transport_mode,
            total_trips,
            previous_year_trips,
            total_trips - previous_year_trips AS yoy_change,
            CASE
                WHEN previous_year_trips IS NULL OR previous_year_trips = 0 THEN NULL
                ELSE (total_trips - previous_year_trips) * 100.0 / previous_year_trips
            END AS yoy_growth_pct
        FROM ytd_growth
        WHERE transport_mode_clean <> 'Other'
        ORDER BY year, transport_mode_clean;
    """,

    "monthly_seasonality": """
        SELECT
            month,
            month_name,
            transport_mode,
            AVG(trip_count) AS avg_monthly_trips
        FROM fact_monthly_opal_trips
        GROUP BY month, month_name, transport_mode
        ORDER BY transport_mode, month;
    """
}


def run_sql_query(
    con: duckdb.DuckDBPyConnection,
    query: str
) -> pd.DataFrame:
    """Run a SQL query and return a DataFrame."""
    return con.execute(query).fetchdf()


def run_named_query(
    con: duckdb.DuckDBPyConnection,
    query_name: str
) -> pd.DataFrame:
    """Run one of the predefined project SQL queries."""
    if query_name not in SQL_QUERIES:
        raise ValueError(
            f"Unknown query name: {query_name}. "
            f"Available queries: {list(SQL_QUERIES.keys())}"
        )

    return run_sql_query(con, SQL_QUERIES[query_name])


def export_sql_results(
    con: duckdb.DuckDBPyConnection,
    output_dir: str | Path,
    query_names: list[str] | None = None
) -> dict[str, pd.DataFrame]:
    """Run selected SQL analyses and export each result to CSV."""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if query_names is None:
        query_names = list(SQL_QUERIES.keys())

    results = {}

    for query_name in query_names:
        result = run_named_query(con, query_name)
        result.to_csv(output_dir / f"{query_name}.csv", index=False)
        results[query_name] = result

    return results


def setup_database_from_final_tables(
    final_dir: str | Path,
    db_path: str | Path
) -> duckdb.DuckDBPyConnection:
    """
    Connect to DuckDB, load final CSV tables and create analytical tables.
    """
    con = connect_duckdb(db_path)
    tables = load_final_tables(final_dir)
    create_duckdb_tables(con, tables)
    return con


def write_sql_file(
    output_path: str | Path,
    queries: dict[str, str] | None = None
) -> None:
    """Export all project SQL queries into a .sql file for GitHub review."""
    if queries is None:
        queries = SQL_QUERIES

    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, "w", encoding="utf-8") as file:
        for query_name, query in queries.items():
            file.write(f"-- {query_name}\n")
            file.write(query.strip())
            file.write("\n\n")
