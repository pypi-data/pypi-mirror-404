(
  SELECT user_id
  FROM active_users
  EXCEPT
  SELECT user_id
  FROM banned_users
)
INTERSECT
(
  SELECT user_id
  FROM eligible_users
)


