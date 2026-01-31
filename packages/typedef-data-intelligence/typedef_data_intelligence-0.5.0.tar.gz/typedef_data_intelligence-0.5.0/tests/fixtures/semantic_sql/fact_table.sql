SELECT
  fct.order_id,
  fct.order_date,
  fct.customer_id,
  fct.unit_price,
  fct.quantity,
  fct.discount_amount,
  c.first_name,
  c.last_name,
  c.email,
  p.product_name,
  p.category
FROM fct_orders fct
JOIN dim_customers c ON fct.customer_id = c.customer_id
JOIN dim_products p ON fct.product_id = p.product_id
WHERE fct.order_date >= '2024-01-01'


