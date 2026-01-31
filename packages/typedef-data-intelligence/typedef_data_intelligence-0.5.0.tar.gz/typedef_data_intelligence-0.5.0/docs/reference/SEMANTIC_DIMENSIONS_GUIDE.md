# Semantic Dimensions Guide

This document provides a comprehensive reference for all dimensions available across our semantic views. Dimensions are non-aggregated attributes that analysts can use to group, filter, and organize data in queries.

## Quick Reference

| Semantic View    | # of Dimensions | # of Time Dimensions |
| ---------------- | --------------- | -------------------- |
| SV_ARR_REPORTING | 4               | 1                    |
| SV_PIPELINE      | 4               | 1                    |
| **Total**        | **8**           | **2**                |

## SV_ARR_REPORTING

**Location**: `DEMO_AGENTS_DAVID.MARTS.SV_ARR_REPORTING`

**Description**: Monthly ARR metrics by account with geographic and segment breakdowns

This semantic view provides monthly ARR reporting with detailed breakdowns by customer characteristics and geography. Use these dimensions to analyze revenue trends, customer segments, and regional performance.

### Dimensions

#### Time Dimensions

| Dimension     | Data Type | Description                         | Granularity |
| ------------- | --------- | ----------------------------------- | ----------- |
| **MONTH_END** | DATE      | Month end date for reporting period | Day         |

#### Business Dimensions

| Dimension        | Data Type | Description                                             | Use Cases                                                                     |
| ---------------- | --------- | ------------------------------------------------------- | ----------------------------------------------------------------------------- |
| **COMPANY_TYPE** | STRING    | Company segment (Enterprise, Mid-Market, SMB)           | Segment analysis, pricing tier review, segment-specific growth trends         |
| **GEO**          | STRING    | Geographic region (North America, Europe, Asia Pacific) | Regional performance, market expansion, geographic revenue mix                |
| **TIER**         | STRING    | Customer tier classification (Tier 1, 2, 3)             | Tier-based revenue analysis, customer stratification, tier migration tracking |

### Associated Measures

The SV_ARR_REPORTING view includes the following measures that can be analyzed across these dimensions:

- **CHURN_ARR** - ARR lost from churned customers
- **CONTRACTION_ARR** - ARR lost from shrinking customers
- **ENDING_ARR** - Total ARR at month end
- **EXPANSION_ARR** - ARR from customer growth and upsells
- **NET_NEW_ARR** - Net change in ARR (new + expansion - churn - contraction)
- **NEW_ARR** - ARR from new customers

### Example Queries

**Analyze ARR by geography over time:**

```
Query SV_ARR_REPORTING with:
- Dimensions: MONTH_END, GEO
- Measures: ENDING_ARR, NET_NEW_ARR
```

**Compare tier performance:**

```
Query SV_ARR_REPORTING with:
- Dimensions: TIER, COMPANY_TYPE
- Measures: ENDING_ARR, EXPANSION_ARR, CHURN_ARR
```

---

## SV_PIPELINE

**Location**: `DEMO_AGENTS_DAVID.MARTS.SV_PIPELINE`

**Description**: Sales pipeline metrics with deal characteristics and probability weighting

This semantic view provides pipeline analysis with deal-level attributes and forecast categories. Use these dimensions to track pipeline progression, forecast accuracy, and deal composition.

### Dimensions

#### Time Dimensions

| Dimension       | Data Type | Description                          | Granularity |
| --------------- | --------- | ------------------------------------ | ----------- |
| **CLOSE_MONTH** | DATE      | Expected close month for opportunity | Day         |

#### Business Dimensions

| Dimension             | Data Type | Description                                     | Use Cases                                                      |
| --------------------- | --------- | ----------------------------------------------- | -------------------------------------------------------------- |
| **DEAL_TYPE**         | STRING    | Type of deal (New, Renewal, Expansion)          | Deal composition, new vs. existing business, growth analysis   |
| **FORECAST_CATEGORY** | STRING    | Forecast category (Commit, Best Case, Pipeline) | Pipeline forecast confidence, risk analysis, scenario planning |
| **STAGE_NAME**        | STRING    | Current sales stage of opportunity              | Sales funnel analysis, conversion rates, pipeline stage health |

### Associated Measures

The SV_PIPELINE view includes the following measures that can be analyzed across these dimensions:

- **DEAL_COUNT** - Number of opportunities
- **TOTAL_ARR** - Total annual recurring revenue in pipeline
- **TOTAL_BOOKINGS** - Total bookings value
- **WEIGHTED_ARR** - Probability-weighted ARR based on stage

### Example Queries

**Pipeline forecast by stage:**

```
Query SV_PIPELINE with:
- Dimensions: STAGE_NAME, FORECAST_CATEGORY
- Measures: DEAL_COUNT, TOTAL_ARR, WEIGHTED_ARR
```

**Deal type analysis with close timeline:**

```
Query SV_PIPELINE with:
- Dimensions: CLOSE_MONTH, DEAL_TYPE
- Measures: TOTAL_BOOKINGS, DEAL_COUNT
```

---

## Dimension Attributes Summary

### All Time Dimensions

Time dimensions enable temporal analysis and trend tracking:

- **MONTH_END** (SV_ARR_REPORTING) - For month-over-month ARR tracking
- **CLOSE_MONTH** (SV_PIPELINE) - For pipeline forecast timing analysis

### All Business Dimensions

Business dimensions enable segmentation and filtering:

| Dimension         | Semantic View    | Possible Values                     | Analysis Applications                         |
| ----------------- | ---------------- | ----------------------------------- | --------------------------------------------- |
| COMPANY_TYPE      | SV_ARR_REPORTING | Enterprise, Mid-Market, SMB         | Segment-based revenue mix, pricing analysis   |
| GEO               | SV_ARR_REPORTING | North America, Europe, Asia Pacific | Regional performance, expansion strategy      |
| TIER              | SV_ARR_REPORTING | Tier 1, 2, 3                        | Customer stratification, upsell opportunities |
| DEAL_TYPE         | SV_PIPELINE      | New, Renewal, Expansion             | New vs. recurring revenue, growth composition |
| FORECAST_CATEGORY | SV_PIPELINE      | Commit, Best Case, Pipeline         | Forecast confidence, risk segmentation        |
| STAGE_NAME        | SV_PIPELINE      | (Sales stages)                      | Funnel analysis, conversion tracking          |

---

## How to Use This Guide

1. **Identify your analysis goal** - What business question are you trying to answer?
2. **Choose the appropriate semantic view** - SV_ARR_REPORTING for revenue analysis, SV_PIPELINE for deal tracking
3. **Select relevant dimensions** - Pick dimensions that align with your analysis goals
4. **Add measures** - Combine with measures to create your query
5. **Apply filters** - Use dimension values to narrow results (e.g., GEO = 'North America')

---

## Best Practices

### Dimension Selection

- Start with time dimensions for trend analysis
- Add 1-3 business dimensions to avoid query complexity
- Consider your audience when selecting dimensions for reports

### Common Dimension Combinations

**For Revenue Leadership:**

- GEO + COMPANY_TYPE (market positioning)
- TIER + COMPANY_TYPE (customer value distribution)
- MONTH_END + GEO (regional trends)

**For Sales Leadership:**

- STAGE_NAME + DEAL_TYPE (funnel composition)
- CLOSE_MONTH + FORECAST_CATEGORY (forecast timeline)
- DEAL_TYPE + STAGE_NAME (deal progression)

**For Financial Planning:**

- MONTH_END + TIER (revenue predictability)
- GEO + COMPANY_TYPE (revenue concentration)
- CLOSE_MONTH + FORECAST_CATEGORY (pipeline visibility)

---

## Frequently Asked Questions

**Q: Can I use dimensions from different semantic views together?**
A: No, each semantic view has its own set of dimensions. Select dimensions from the view that matches your data needs.

**Q: Are all dimension values equally granular?**
A: Most dimensions have relatively high-level categories (e.g., geographic regions, tier classifications). For more detailed analysis, consult with your data team.

**Q: How do time dimensions affect query performance?**
A: Time dimensions are optimized for efficient querying. They're recommended for trend analysis without performance concerns.

**Q: What if I need a dimension not listed here?**
A: Please submit a request to your analytics engineering team. New dimensions require semantic view updates.

---

## Related Documentation

- [Semantic Measures Guide](./SEMANTIC_MEASURES_GUIDE.md) - Learn about available measures
- [Query Semantic Views](./README_MCP.md) - How to query these views
- [Semantic Analysis Overview](./README_SEMANTIC.md) - Technical details about semantic metadata
