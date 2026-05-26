# NSW Transport Operations Analytics

## Project Overview

This project analyses NSW public transport demand, station passenger flows, weather conditions and calendar effects to identify demand trends, station-level operational pressure, data quality risks and short-term demand forecasting opportunities.

The project was built as an end-to-end analytics workflow: raw transport, GTFS, weather and calendar datasets were cleaned with Python, transformed into analytical fact and dimension tables, queried with DuckDB SQL, modelled for short-term demand forecasting, and visualised through Tableau dashboards.

The final outputs are designed for a transport operations or business analytics setting, where stakeholders need to monitor demand changes, identify station pressure points, understand seasonal patterns and evaluate forecasting performance.

For a detailed explanation of the methodology and findings, see the [Project Report](reports/project_report.md).

---

## Business Questions

This project focuses on four practical questions:

1. How has NSW public transport demand changed over time?
2. Which transport modes and passenger groups contribute most to total demand?
3. Which stations show the highest passenger flow and operational pressure?
4. Can historical demand, calendar features and weather conditions support short-term demand forecasting?

---

## Tech Stack

- **Python**: data cleaning, feature engineering, forecasting, visualisation
- **Pandas / NumPy**: data transformation and analysis
- **DuckDB / SQL**: analytical querying and reporting outputs
- **Scikit-learn**: baseline, linear regression and random forest forecasting models
- **Tableau**: interactive dashboard development
- **Git / GitHub**: project version control and portfolio presentation

---

## Datasets Used

| Dataset | Purpose |
|---|---|
| NSW Opal monthly trips | Monthly demand analysis by transport mode and card type |
| Train station entries and exits | Station flow, peak pressure and entry-exit imbalance analysis |
| GTFS static data | Station and route reference tables |
| Weather observations | Rainfall, temperature and rainy-day features |
| NSW public holidays | Calendar and holiday features |

Note: the 2025 Opal demand data is year-to-date rather than a complete calendar year. Annual growth analysis involving 2025 is therefore treated as YTD YoY comparison.

---

## Project Workflow

```text
Raw data
   ↓
Data cleaning and standardisation
   ↓
Feature engineering
   ↓
Fact and dimension table creation
   ↓
DuckDB SQL analysis
   ↓
Forecasting model development
   ↓
Tableau dashboard design
   ↓
Business insights and recommendations
```

The workflow is modularised under the `src/` folder:

```text
src/
├── data_cleaning.py
├── feature_engineering.py
├── forecasting.py
└── sql_utils.py
```

---

## Repository Structure

```text
nsw-transport-operations-analytics/
│
├── README.md
├── notebooks/
│   └── NSW_Transport_Operations_Analytics.ipynb
│
├── src/
│   ├── data_cleaning.py
│   ├── feature_engineering.py
│   ├── forecasting.py
│   └── sql_utils.py
│
├── data/
│   ├── raw/
│   ├── processed/
│   └── final/
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
│   └── tableau/
│
└── reports/
    ├── project_report.md
    ├── project_summary.md
    └── business_recommendations.md
```

---

## Key Outputs

### Final analytical tables

The cleaned data is transformed into fact and dimension tables:

- `fact_monthly_opal_trips.csv`
- `fact_station_flow.csv`
- `dim_date.csv`
- `dim_weather.csv`
- `dim_station.csv`
- `dim_route.csv`

### SQL analysis outputs

DuckDB SQL queries are used to generate repeatable reporting outputs, including:

- monthly demand trend
- transport mode demand
- card type demand
- top station flow
- peak station pressure
- entry-exit imbalance
- monthly seasonality
- YTD YoY demand growth
- weather-demand relationship
- data quality summary

Full SQL queries are available in [`sql/analysis_queries.sql`](sql/analysis_queries.sql).

### Forecasting outputs

The forecasting workflow compares:

| Model | Purpose |
|---|---|
| Naive baseline | Uses previous-month demand as a simple benchmark |
| Linear regression | Provides an interpretable statistical model |
| Random forest | Captures non-linear patterns and supports feature importance analysis |

Model performance is evaluated using:

- MAE
- RMSE
- Adjusted MAPE
- WMAPE
- R2

WMAPE is used as the main percentage-based error metric because it is more stable than standard MAPE when demand volumes differ across transport modes.

---

## Tableau Dashboards

The Tableau workbook contains two dashboards.

### 1. Operations Overview

This dashboard summarises:

- monthly public transport demand trend
- demand by transport mode
- top stations by passenger flow
- station entries vs exits
- data coverage summary

### 2. Demand Patterns and Forecasting Insights

This dashboard provides deeper analysis of:

- monthly demand seasonality
- YTD YoY demand growth
- weather-demand relationship
- actual vs forecasted demand
- random forest feature importance
- model performance metrics

[View Interactive Tableau Workbook](https://public.tableau.com/views/nsw_transport/NSWTransportOperationsOverview?:language=zh-CN&:sid=&:redirect=auth&:display_count=n&:origin=viz_share_link)

### Operations Overview

![NSW Transport Operations Overview](dashboard/tableau/NSW%20Transport%20Operations%20Overview.png)

### Demand Patterns and Forecasting Insights

![Demand Patterns and Forecasting Insights](dashboard/tableau/Demand%20Patterns%20and%20Forecasting%20Insights.png)

---

## Key Insights

### 1. Train and Bus dominate overall demand

Train and Bus carry the largest share of public transport trips. These modes should be prioritised in recurring demand monitoring and network-level reporting.

### 2. Major CBD stations are key pressure points

Stations such as Town Hall, Central and Wynyard show high passenger flow. These stations should be monitored closely for crowding, station capacity and peak-period pressure.

### 3. Monthly seasonality matters

Demand changes across months and transport modes. Monthly seasonality analysis can support service planning, staffing assumptions and demand review cycles.

### 4. 2025 growth should be interpreted as YTD YoY

Since 2025 demand data is incomplete, the project compares 2025 demand with the same months in 2024. This avoids misleading full-year comparisons.

### 5. Recent demand is the strongest forecasting signal

The forecasting results show that lagged demand, especially previous-month demand, is the most important predictor. This suggests that rolling demand monitoring can already provide a strong short-term planning benchmark.

### 6. Data quality checks are part of the analytics workflow

The project includes row count, missing value and duplicate checks to make the analysis more transparent and reliable before dashboarding or modelling.

---

## Notes and Limitations

This project uses monthly-level Opal demand data, so it cannot capture daily or hourly travel patterns. Station flow data is useful for identifying high-volume stations, but it does not fully describe platform-level crowding or real-time disruptions.

Weather observations are based on Sydney Airport data and are used as a proxy for broader Greater Sydney conditions. The forecasting model does not include major events, service disruptions, fare changes, school terms or real-time operations data.

More detailed methodology, assumptions and limitations are discussed in the [Project Report](reports/project_report.md).

---
