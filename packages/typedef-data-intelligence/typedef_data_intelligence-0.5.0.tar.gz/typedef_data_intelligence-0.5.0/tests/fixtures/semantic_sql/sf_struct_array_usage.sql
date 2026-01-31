WITH src AS (
  SELECT
    1 AS id,
    ARRAY_CONSTRUCT(
      OBJECT_CONSTRUCT('k', 'a', 'v', 10),
      OBJECT_CONSTRUCT('k', 'b', 'v', 20)
    ) AS items
)
SELECT
  id,
  items[0]:"k"::STRING AS first_key,
  items[0]:"v"::INT AS first_val,
  ARRAY_SIZE(items) AS item_count
FROM src


