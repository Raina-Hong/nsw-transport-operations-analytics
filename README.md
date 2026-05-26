# NSW Transport Operations Analytics

## 1. Project Overview

This project analyses NSW public transport demand, station passenger flows, weather conditions and calendar effects to identify demand trends, station-level operational pressure, data quality risks and short-term demand forecasting opportunities.

The project was built as an end-to-end transport operations analytics workflow. It starts from raw public transport, GTFS, weather and calendar datasets, cleans and restructures them into analytical tables, uses DuckDB SQL to answer operational questions, builds a demand forecasting workflow, and prepares dashboard-ready datasets for Tableau.

The final output is designed for a transport operations or business analytics setting. The goal is not only to report historical demand, but also to understand where network pressure occurs, how demand changes over time, how weather and seasonality may relate to demand, and what data quality checks should be considered before using the results for planning decisions.

For a more detailed explanation of the methodology, analysis and findings, see the [Project Report](reports/project_report.md).

---

## 2. Business Problem

Public transport operators need reliable and repeatable analysis to support both daily monitoring and longer-term operational planning. Passenger demand changes by month, transport mode, station, weather conditions and calendar effects. At the same time, station-level congestion can create pressure even when overall network demand looks stable.

This project focuses on four business questions:

1. How has NSW public transport demand changed over time?
2. Which transport modes and passenger groups contribute most to total demand?
3. Which train stations show the highest passenger flow and peak-period pressure?
4. Can historical demand, calendar features and weather conditions support short-term demand forecasting?

The project also includes data quality checks because transport planning decisions depend heavily on consistent, complete and well-structured data.

---

## 3. Datasets Used

The project combines transport demand, station flow, GTFS reference data, weather observations and public holiday data.

| Dataset | File / Source Used in Project | Purpose |
|---|---|---|
| Opal trips by mode | `data/raw/NSW-2-Opal-trips-all-modes.csv` | Monthly public transport demand analysis by mode and card type |
| Train station entries and exits | `data/raw/NSW-train-station-entries-and-exits.csv` | Station flow, peak pressure and entry-exit imbalance analysis |
| GTFS static data | `data/raw/full_greater_sydney_gtfs_static_0/` | Station and route reference tables, mainly using `stops.txt` and `routes.txt` |
| Rainfall data | `data/raw/sydney_airport_daily_rainfall.csv` | Weather context for demand analysis |
| Temperature data | `data/raw/sydney_airport_daily_max_temp.csv`, `data/raw/sydney_airport_daily_min_temp.csv` | Monthly weather features for demand analysis and forecasting |
| NSW public holidays | `data/raw/nsw_public_holidays_2019_2023.csv` | Calendar and holiday features |

The raw datasets are transformed into cleaned and final analytical tables under `data/processed/` and `data/final/`.

Note: the 2025 Opal demand data is year-to-date rather than a complete calendar year. For this reason, annual growth analysis involving 2025 is treated as YTD YoY comparison.

---

## 4. Project Workflow

The project follows a standard analytics workflow:

```text
Raw data
   ↓
Data cleaning and standardisation
   ↓
Calendar, weather and GTFS feature engineering
   ↓
Fact and dimension table creation
   ↓
DuckDB SQL modelling and analysis
   ↓
Python visualisation and forecasting model development
   ↓
Tableau dashboard data export
   ↓
Business insights and recommendations
```

Main steps:

1. **Data loading**  
   Load Opal demand, station flow, weather, public holiday and GTFS files.

2. **Data cleaning**  
   Standardise column names, convert date fields, handle missing values, remove duplicates and prepare consistent analytical fields.

3. **Feature engineering**  
   Create calendar fields, holiday indicators, monthly weather features, lagged demand features and rolling average features.

4. **Data modelling**  
   Build fact and dimension tables, including monthly Opal trips, station flow, date, weather, station and route dimensions.

5. **SQL analysis**  
   Use DuckDB to run repeatable SQL queries for demand trends, station pressure, seasonality, YTD growth, weather-demand relationships and data quality checks.

6. **Forecasting model**  
   Build baseline, linear regression and random forest models to forecast monthly demand using lagged demand, rolling averages, calendar and weather features.

7. **Dashboard preparation**  
   Export clean dashboard-ready CSV files for Tableau.

8. **Business interpretation**  
   Summarise operational insights, data limitations and potential planning use cases.

---

## 5. Repository Structure

```text
nsw-transport-operations-analytics/
│
├── README.md
├── transport_analytics_v2.duckdb
│
├── data/
│   ├── raw/
│   │   ├── NSW-2-Opal-trips-all-modes.csv
│   │   ├── NSW-train-station-entries-and-exits.csv
│   │   ├── nsw_public_holidays_2019_2023.csv
│   │   ├── sydney_airport_daily_rainfall.csv
│   │   ├── sydney_airport_daily_max_temp.csv
│   │   ├── sydney_airport_daily_min_temp.csv
│   │   └── full_greater_sydney_gtfs_static_0/
│   │       ├── stops.txt
│   │       └── routes.txt
│   │
│   ├── processed/
│   │   ├── clean_opal_trips.csv
│   │   ├── clean_station_flow.csv
│   │   └── clean_weather.csv
│   │
│   └── final/
│       ├── fact_monthly_opal_trips.csv
│       ├── fact_station_flow.csv
│       ├── dim_date.csv
│       ├── dim_weather.csv
│       ├── dim_station.csv
│       └── dim_route.csv
│
├── notebooks/
│   └── NSW_Transport_Operations_Analytics.ipynb
│
├── src/
│   ├── __init__.py
│   ├── data_cleaning.py
│   ├── feature_engineering.py
│   ├── forecasting.py
│   └── sql_utils.py
│
├── sql/
│   ├── create_tables.sql
│   ├── analysis_queries.sql
│   └── data_quality_checks.sql
│
├── outputs/
│   ├── charts/
│   ├── sql_exports/
│   └── model_results/
│
├── dashboard/
│   ├── dashboard_data/
│   ├── screenshots/
│   └── tableau/
│       ├── nsw_transport_dashboard.twbx
│       ├── NSW Transport Operations Overview.png
│       └── Demand Patterns and Forecasting Insights.png
│
└── reports/
    ├── project_report.md
    ├── project_summary.md
    └── business_recommendations.md
```

---

## 6. Key Outputs

### Processed and final analytical tables

The project creates cleaned datasets and final fact/dimension tables:

- `fact_monthly_opal_trips.csv`
- `fact_station_flow.csv`
- `dim_date.csv`
- `dim_weather.csv`
- `dim_station.csv`
- `dim_route.csv`

These tables are used for SQL analysis, forecasting and Tableau dashboard development.

### SQL exports

The SQL analysis results are exported under `outputs/sql_exports/`, including:

- `monthly_demand_trend.csv`
- `transport_mode_demand.csv`
- `card_type_demand.csv`
- `yearly_mode_demand.csv`
- `top_station_flow.csv`
- `peak_station_pressure.csv`
- `entry_exit_imbalance.csv`
- `yearly_station_flow_trend.csv`
- `monthly_demand_weather.csv`
- `yoy_mode_demand.csv`
- `monthly_seasonality.csv`
- `weather_demand_relationship.csv`
- `data_quality_summary.csv`

### Charts

Python-generated charts are saved under `outputs/charts/`, including:

- monthly demand trend;
- demand by transport mode;
- card type demand;
- yearly mode demand;
- top station flow;
- peak station pressure;
- entry-exit imbalance;
- weather and demand analysis;
- actual vs forecasted demand;
- feature importance;
- data quality overview.

### Model outputs

Forecasting outputs are saved under `outputs/model_results/`:

- `model_metrics.csv`
- `forecast_results.csv`
- `feature_importance.csv`

The model metrics include MAE, RMSE, Adjusted MAPE, WMAPE and R2. WMAPE is used as the main percentage-based error metric because it is more stable than standard MAPE for transport demand data with different demand volumes across modes.

---

## 7. SQL Analysis

DuckDB is used to create a lightweight analytical database for repeatable SQL analysis. The SQL layer makes the project closer to a real business analytics workflow, where cleaned tables are queried for reporting and operational monitoring.

The main SQL analysis covers:

### Monthly demand trend

This query tracks total public transport trips by year and month. It is used to identify long-term demand changes, seasonality and unusual demand drops or recoveries.

### Transport mode demand

This query compares total and average monthly trips across transport modes such as Train, Bus, Ferry, Metro and Light Rail. It helps show which modes carry the largest passenger volumes.

### Card type demand

This query analyses demand by passenger card type. It provides a high-level view of passenger composition, such as adult, concession, child/youth and senior/pensioner usage.

### Yearly mode demand

This query compares annual demand by transport mode. It is useful for understanding mode-level recovery patterns and long-term demand shifts.

### YTD YoY demand growth

This query calculates year-to-date YoY growth by transport mode. Since 2025 data is not a complete year, 2025 demand is compared with the same months in 2024 rather than with full-year 2024. This avoids misleading annual comparisons.

### Monthly seasonality

This query calculates average monthly trips by transport mode. It is used to identify recurring monthly patterns that may support service planning, staffing assumptions and demand review cycles.

### Weather-demand relationship

This query combines monthly transport demand with rainfall, rainy days and temperature features. It is used to explore whether rainy months show different demand patterns across transport modes.

### Top station flow

This query ranks stations by total entries and exits. High-flow stations such as Town Hall, Central and Wynyard can be treated as key network pressure points for operational monitoring.

### Peak station pressure

This query calculates how much station flow is concentrated during peak periods. A high peak-flow share suggests that the station may require more attention during morning and evening commuting windows.

### Entry-exit imbalance

This query compares total entries and exits at each station. It helps identify stations that behave more like origin stations, destination stations or balanced interchange locations.

### Data quality checks

The data quality summary checks row counts, missing key metrics and duplicate records across the main analytical tables. This step is included to make the analysis more transparent and risk-aware.

---

## 8. Forecasting Model

The forecasting section predicts monthly public transport demand using historical demand, calendar and weather features.

### Features used

The model uses:

- year and month;
- quarter and season;
- transport mode;
- average rainfall;
- total rainfall;
- average maximum temperature;
- average minimum temperature;
- number of rainy days;
- `lag_1_demand`;
- `lag_3_demand`;
- `rolling_3m_avg`;
- `rolling_6m_avg`.

The time-series split uses historical data for training and later-period data for testing. This avoids random splitting, which would not be appropriate for time-dependent demand forecasting.

### Models compared

Three models are compared:

| Model | Purpose |
|---|---|
| Naive baseline | Uses previous-month demand as the prediction |
| Linear regression | Provides a simple interpretable statistical benchmark |
| Random forest | Captures non-linear relationships and supports feature importance analysis |

### Evaluation metrics

| Metric | Interpretation |
|---|---|
| MAE | Average absolute forecast error in passenger trips |
| RMSE | Penalises larger forecast errors more strongly |
| Adjusted MAPE | Percentage error calculated after excluding very small actual demand values |
| WMAPE | Total absolute error as a percentage of total actual demand |
| R2 | Share of demand variation explained by the model |

Standard MAPE was not used as the main metric because public transport demand varies significantly across transport modes. When actual demand is very small, MAPE can become unstable and produce misleadingly large percentage errors. WMAPE is therefore used as the main percentage-based metric for comparing forecasting performance.

### Model interpretation

The naive baseline performs strongly because monthly transport demand has strong temporal persistence. In simple terms, this month’s demand is often close to last month’s demand. This is common in transport demand forecasting and makes the baseline a useful benchmark.

The random forest feature importance output shows that `lag_1_demand` is the most important predictor, followed by rolling average demand features. This suggests that recent historical demand is more predictive than weather variables in the current monthly-level dataset.

This result is useful from an operations perspective. It shows that a simple rolling demand monitoring workflow can already provide a strong benchmark before more complex forecasting models are introduced.

---

## 9. Tableau Dashboard

The Tableau workbook contains two interactive dashboards:

1. **Operations Overview**  
   Summarises public transport demand trends, demand by transport mode, station passenger flow, entry-exit comparison and data coverage.

2. **Demand Patterns and Forecasting Insights**  
   Provides deeper analysis of monthly seasonality, YTD YoY demand growth, weather-demand relationships and forecasting model performance.

[View Interactive Tableau Workbook](https://public.tableau.com/views/nsw_transport/NSWTransportOperationsOverview?:language=zh-CN&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

### Operations Overview

![NSW Transport Operations Overview](dashboard/tableau/NSW%20Transport%20Operations%20Overview.png)

### Demand Patterns and Forecasting Insights

![Demand Patterns and Forecasting Insights](dashboard/tableau/Demand%20Patterns%20and%20Forecasting%20Insights.png)

---

## 10. Key Insights

### 1. Public transport demand shows clear time-based variation

Monthly demand changes over time and is affected by seasonality, calendar effects and broader travel behaviour. Looking only at total annual demand would hide these monthly changes.

### 2. Demand should be monitored by transport mode

Different transport modes contribute different levels of demand and may follow different recovery or usage patterns. Mode-level analysis is more useful than only reporting total network demand.

### 3. A small number of stations carry a large share of passenger flow

Stations such as Town Hall, Central and Wynyard show high total passenger flow. These stations should be prioritised for operational monitoring because disruption or crowding at these locations can affect the broader network.

### 4. Peak-period pressure is different from total station volume

A station does not need to have the highest total annual flow to create operational pressure. If a high share of passenger movement occurs during peak windows, the station may still require targeted crowd management.

### 5. Entry-exit imbalance can support station role analysis

Entry-exit imbalance helps describe whether a station is mainly an origin station, a destination station or a more balanced interchange point. This can support planning for staffing, signage and passenger flow management.

### 6. Monthly seasonality supports planning

Monthly seasonality analysis shows that demand varies across months and transport modes. This can help operations teams think about planning cycles, staffing assumptions and service monitoring in a more structured way.

### 7. 2025 annual comparison should be treated as YTD comparison

The 2025 demand data is incomplete, so comparing 2025 directly with full-year 2024 would be misleading. The project therefore uses YTD YoY comparison, comparing 2025 demand with the same months in 2024.

### 8. Recent demand is the strongest forecasting signal

The forecasting model shows that lagged demand, especially previous-month demand, is the strongest predictor. This means rolling demand monitoring can be useful for short-term operational planning.

### 9. Data quality checks should be part of transport analytics delivery

The project includes row count, missing value and duplicate checks to make the analysis more reliable. For operational use, data quality monitoring should be extended to coverage gaps, inconsistent category labels and delayed data updates.

---

## 11. Data Limitations

This project is designed as a portfolio analytics project and has several limitations:

1. **Aggregated demand level**  
   The Opal demand data is aggregated at a monthly level, so it cannot capture daily or hourly travel patterns.

2. **Limited station flow granularity**  
   Station entries and exits are useful for identifying major stations and pressure points, but they do not fully describe platform-level or service-level crowding.

3. **Weather data location**  
   Weather observations are based on Sydney Airport weather files. They may not fully represent weather conditions across all NSW transport areas.

4. **GTFS static data limitation**  
   GTFS static files provide route and stop reference information, but they do not represent real-time delays, cancellations or service disruptions.

5. **Incomplete 2025 data**  
   The 2025 Opal demand data is year-to-date rather than a complete calendar year. Any annual comparison involving 2025 should therefore be interpreted as YTD comparison.

6. **Forecasting scope**  
   The forecasting model predicts demand using historical, calendar and weather features. It does not include special events, fare changes, service disruptions, school terms or broader economic variables.

7. **Category consistency**  
   Some categorical fields required additional standardisation before dashboarding, such as inconsistent capitalisation in transport mode labels.

---

## 12. How to Reproduce

### 1. Clone the repository

```bash
git clone https://github.com/Raina-Hong/nsw-transport-operations-analytics.git
cd nsw-transport-operations-analytics
```

### 2. Create a Python environment

```bash
conda create -n nsw-transport python=3.10
conda activate nsw-transport
```

### 3. Install required packages

```bash
pip install pandas numpy matplotlib scikit-learn duckdb jupyter
```

If a `requirements.txt` file is available, use:

```bash
pip install -r requirements.txt
```

### 4. Check raw data placement

Place the raw datasets under:

```text
data/raw/
```

The expected raw data structure is:

```text
data/raw/
├── NSW-2-Opal-trips-all-modes.csv
├── NSW-train-station-entries-and-exits.csv
├── nsw_public_holidays_2019_2023.csv
├── sydney_airport_daily_rainfall.csv
├── sydney_airport_daily_max_temp.csv
├── sydney_airport_daily_min_temp.csv
└── full_greater_sydney_gtfs_static_0/
    ├── stops.txt
    └── routes.txt
```

### 5. Run the notebook

```bash
jupyter notebook notebooks/NSW_Transport_Operations_Analytics.ipynb
```

Run all cells from top to bottom. The notebook will generate cleaned data, final analytical tables, SQL exports, model outputs, charts and Tableau-ready CSV files.

### 6. Open Tableau dashboard

The Tableau workbook is stored under:

```text
dashboard/tableau/
```

The dashboard data files are stored under:

```text
dashboard/dashboard_data/
```

Refresh the Tableau data sources if the CSV files are regenerated.

---

## 13. Resume Bullet Points

- Built an end-to-end transport operations analytics workflow using NSW Opal trips, station entries/exits, GTFS, weather and calendar data to monitor demand trends, station flow pressure and forecasting opportunities.
- Cleaned and transformed raw datasets into fact and dimension tables using Python and DuckDB, enabling repeatable SQL analysis of monthly demand, station flow, peak pressure, entry-exit imbalance, seasonality and YTD YoY growth.
- Developed a forecasting workflow using lagged demand, rolling averages, weather and calendar features, and evaluated baseline, linear regression and random forest models using MAE, RMSE, WMAPE and R2.
- Created two Tableau dashboards to communicate operations overview, demand seasonality, YTD growth, weather-demand relationships, model performance and data quality indicators for stakeholder-facing reporting.
