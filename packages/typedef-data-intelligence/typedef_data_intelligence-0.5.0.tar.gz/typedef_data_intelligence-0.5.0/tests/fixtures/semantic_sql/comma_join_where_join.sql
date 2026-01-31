SELECT
  a.id,
  b.value
FROM a, b
WHERE a.id = b.a_id
  AND a.created_at >= '2024-01-01'


