
-- Monthly demand trend

SELECT
    year,
    month,
    month_name,
    SUM(trip_count) AS total_trips
FROM fact_monthly_opal_trips
GROUP BY year, month, month_name
ORDER BY year, month;


-- Demand by transport mode

SELECT
    transport_mode,
    SUM(trip_count) AS total_trips,
    AVG(trip_count) AS avg_monthly_trips
FROM fact_monthly_opal_trips
GROUP BY transport_mode
ORDER BY total_trips DESC;


-- Card type demand

SELECT
    card_type,
    SUM(trip_count) AS total_trips,
    AVG(trip_count) AS avg_monthly_trips
FROM fact_monthly_opal_trips
GROUP BY card_type
ORDER BY total_trips DESC;


-- Yearly demand by transport mode

SELECT
    year,
    transport_mode,
    SUM(trip_count) AS total_trips
FROM fact_monthly_opal_trips
GROUP BY year, transport_mode
ORDER BY year, total_trips DESC;


-- Top stations by total flow

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


-- Peak period station pressure

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


-- Entry-exit imbalance

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


-- Yearly station flow trend

SELECT
    year,
    SUM(total_entries) AS total_entries,
    SUM(total_exits) AS total_exits,
    SUM(total_flow) AS total_flow,
    AVG(bottleneck_score) AS avg_bottleneck_score
FROM fact_station_flow
GROUP BY year
ORDER BY year;

