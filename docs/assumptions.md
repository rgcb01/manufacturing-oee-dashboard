# Engineering Assumptions and Synthetic Ground Truth

This project uses synthetic data and was created as a professional portfolio project.

## Dataset Scope

- The dataset represents three manufacturing lines running three shifts per day.
- Planned production time is fixed at 480 minutes per shift.
- Production records include line, shift, product, planned time, downtime, ideal cycle time, total units, good units and scrap units.
- Downtime and scrap event tables include matching `date`, `line`, `shift` and `product` fields so filtered analyses remain consistent.
- No confidential company data, customer data or supplier data is used.

## Intentional Synthetic Patterns

The generator creates realistic, discoverable manufacturing patterns:

- `Line-B / Shift-2` has elevated scrap and quality holds.
- `Line-C` has higher downtime, especially around maintenance-related losses.
- `Sensor Mount` is more demanding from a cycle-performance perspective.
- `Connector` has a slightly higher scrap tendency.
- Days 12-16 include a temporary multi-day degradation.
- Days 22 onward include a later recovery period.

These patterns are intentionally moderate. The dashboard is expected to discover them through KPI aggregation, Pareto analysis, heatmaps and engineering insights.

## Data Consistency

- Production `downtime_minutes` is designed to match the sum of corresponding downtime events.
- Production `scrap_units` is designed to match the sum of corresponding scrap events.
- Consistency is validated by tests in `tests/test_data_generator.py`.

## KPI Assumptions

- OEE is calculated as `Availability x Performance x Quality`.
- Aggregate OEE is calculated from summed time and output values, not from averaging row-level OEE.
- Performance is weighted by ideal production time, so products with different ideal cycle times aggregate correctly.
- Scrap rate is calculated as `scrap_units / total_units`.

## Limitations

- This is a portfolio diagnostic tool, not certified plant reporting software.
- Cp/Cpk is intentionally not calculated because the current dataset does not include continuous dimensional measurements with LSL/USL.
- SPC-style monitoring uses daily KPI trends, mean lines and target references instead of unsupported capability claims.
