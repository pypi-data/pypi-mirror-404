SELECT
  customer_id,
  order_date,
  SUM(order_total) AS total_revenue,
  COUNT(*) AS order_count
FROM orders o
JOIN customers c ON o.customer_id = c.id
WHERE order_date >= '2024-01-01'
GROUP BY customer_id, order_date
ORDER BY total_revenue DESC
LIMIT 100


