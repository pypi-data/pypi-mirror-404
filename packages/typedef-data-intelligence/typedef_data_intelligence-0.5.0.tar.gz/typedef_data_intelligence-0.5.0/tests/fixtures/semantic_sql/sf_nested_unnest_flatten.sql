WITH src AS (
  SELECT
    1 AS id,
    PARSE_JSON('[{\"k\":\"a\",\"vals\":[1,2]},{\"k\":\"b\",\"vals\":[3]}]') AS payload
)
SELECT
  id,
  f.value:"k"::STRING AS k,
  v.value::INT AS val
FROM src,
LATERAL FLATTEN(input => payload) f,
LATERAL FLATTEN(input => f.value:"vals") v


