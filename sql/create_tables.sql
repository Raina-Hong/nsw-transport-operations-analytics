
-- Create analytical tables in DuckDB

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
