SELECT
  user_id,
  created_at,
  event_type
FROM (
  SELECT
    e.*,
    ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY created_at DESC) AS rn
  FROM events e
  WHERE created_at >= '2024-01-01'
) t
WHERE rn = 1


