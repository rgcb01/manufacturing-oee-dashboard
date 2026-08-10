# KPI Definitions

This project uses synthetic data and was created as a professional portfolio project.

## OEE

Overall Equipment Effectiveness is calculated as:

```txt
OEE = Availability x Performance x Quality
```

## Availability

```txt
Availability = Operating Time / Planned Production Time
Operating Time = Planned Production Time - Downtime
```

## Performance

```txt
Performance = Ideal Production Time / Operating Time
Ideal Production Time = Ideal Cycle Time x Total Units
```

## Quality

```txt
Quality = Good Units / Total Units
```

## Scrap Rate

```txt
Scrap Rate = Scrap Units / Total Units
```

## Aggregation Rule

Aggregate OEE is not calculated by averaging row-level OEE values. The dashboard first sums planned time, downtime, operating time, units and good units across the selected scope, then recalculates Availability, Performance and Quality from those totals.

This matters when comparing products with different ideal cycle times.

## Default Targets

```txt
OEE: 85%
Availability: 90%
Performance: 95%
Quality: 99%
Scrap Rate: maximum 2%
```

The dashboard reports target deltas in percentage points.
