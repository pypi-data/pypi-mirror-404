WITH base AS (
  SELECT
    user_id,
    created_at,
    amount
  FROM purchases p
  WHERE created_at >= '2024-01-01'
),
agg AS (
  SELECT
    user_id,
    SUM(amount) AS total_amount
  FROM base
  GROUP BY user_id
)
SELECT
  a.user_id,
  a.total_amount
FROM agg a
WHERE a.total_amount > 0


