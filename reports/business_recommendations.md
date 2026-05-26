
# Business Recommendations and Data Limitations

## Key Operational Insights

1. **Demand Monitoring**
   - Monthly demand trends can help transport operations teams monitor long-term passenger behaviour and identify abnormal demand periods.
   - Transport mode comparison supports mode-specific capacity planning and service review.

2. **Station Flow and Bottleneck Management**
   - Stations with high total passenger flow should be prioritised for operational monitoring.
   - Stations with high peak flow share may experience concentrated crowding pressure during morning and evening peak windows.
   - Entry-exit imbalance can help distinguish commuter origin stations from employment or activity-centre destination stations.

3. **Forecasting for Operational Planning**
   - Lagged demand and rolling average features provide useful signals for short-term public transport demand forecasting.
   - Forecasting outputs can support resource planning, demand monitoring and scenario analysis.

4. **Weather and Calendar Context**
   - Weather features such as rainfall and temperature provide useful external context for demand analysis.
   - Public holiday and seasonal features help explain non-regular demand changes.

## Data Quality and Risk Considerations

1. **Granularity Limitation**
   - Opal trips data is monthly and mode-level, while station entries/exits data is yearly and station-level.
   - Because of this difference in granularity, the project uses two fact tables instead of forcing all datasets into one table.

2. **Station Matching Limitation**
   - GTFS stop names and station entries/exits station names may not perfectly match.
   - Some stations may remain unmatched when enriching station flow data with coordinates or regions.

3. **Weather Proxy Limitation**
   - Sydney Airport weather observations are used as a proxy for Greater Sydney weather conditions.
   - This may not fully reflect local weather conditions around each station or region.

4. **Forecasting Limitation**
   - The forecasting model predicts monthly demand based on historical demand, calendar and weather features.
   - It does not include service disruptions, fare changes, major events or real-time operational conditions.

5. **Dashboard Interpretation Risk**
   - Dashboard insights should be interpreted as decision-support indicators, not as direct operational instructions.
   - Further validation with internal operational data would be required before real-world deployment.

## Future Improvements

- Add finer-grained daily or hourly Opal data if available.
- Improve station matching using fuzzy matching or geospatial joins.
- Add event data, service disruption data and population density features.
- Extend forecasting to station-level or region-level demand if granular demand data becomes available.
- Deploy the dashboard with automated data refresh and monitoring.
