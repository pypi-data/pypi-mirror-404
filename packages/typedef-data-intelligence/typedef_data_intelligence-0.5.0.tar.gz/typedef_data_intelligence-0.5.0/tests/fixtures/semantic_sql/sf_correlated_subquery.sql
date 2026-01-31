SELECT
  o.order_id,
  o.customer_id,
  (
    SELECT MAX(p.payment_date)
    FROM payments p
    WHERE p.order_id = o.order_id
  ) AS last_payment_date
FROM orders o
WHERE EXISTS (
  SELECT 1
  FROM customers c
  WHERE c.id = o.customer_id
    AND c.status = 'active'
)


