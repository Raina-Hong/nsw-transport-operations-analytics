
-- Example data quality checks

SELECT COUNT(*) AS row_count
FROM fact_monthly_opal_trips;

SELECT COUNT(*) AS row_count
FROM fact_station_flow;

SELECT COUNT(*) - COUNT(DISTINCT station_flow_id) AS duplicate_station_flow_records
FROM fact_station_flow;

SELECT COUNT(*) - COUNT(DISTINCT date) AS duplicate_weather_dates
FROM dim_weather;
