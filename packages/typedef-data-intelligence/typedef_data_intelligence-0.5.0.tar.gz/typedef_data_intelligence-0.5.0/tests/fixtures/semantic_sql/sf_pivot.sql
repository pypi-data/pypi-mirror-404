SELECT
  store_id,
  "2024-01" AS amt_2024_01,
  "2024-02" AS amt_2024_02,
  "2024-03" AS amt_2024_03
FROM (
  SELECT
    store_id,
    month,
    amount
  FROM sales_facts
) s
PIVOT (
  SUM(amount) FOR month IN ('2024-01', '2024-02', '2024-03')
) p


