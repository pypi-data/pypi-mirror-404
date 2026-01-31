SELECT
  d.d_year,
  d.d_month,
  s.s_store_name,
  SUM(ss.ss_net_profit) AS profit,
  COUNT(DISTINCT ss.ss_ticket_number) AS ticket_count
FROM store_sales ss
JOIN date_dim d ON ss.ss_sold_date_sk = d.d_date_sk
JOIN store s ON ss.ss_store_sk = s.s_store_sk
WHERE d.d_year BETWEEN 2020 AND 2022
GROUP BY d.d_year, d.d_month, s.s_store_name
ORDER BY d.d_year, d.d_month


