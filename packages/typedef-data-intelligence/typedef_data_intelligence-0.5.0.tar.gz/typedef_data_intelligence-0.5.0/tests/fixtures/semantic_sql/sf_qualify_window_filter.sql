SELECT
  user_id,
  event_ts,
  event_name
FROM events
QUALIFY ROW_NUMBER() OVER (PARTITION BY user_id ORDER BY event_ts DESC) = 1


