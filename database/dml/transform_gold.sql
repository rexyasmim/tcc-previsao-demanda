DROP TABLE IF EXISTS gold.monthly_category_sales;

CREATE TABLE gold.monthly_category_sales AS (
WITH month_grid AS (
    SELECT generate_series(
        date_trunc('month', (
            SELECT MIN(order_purchase_timestamp)
            FROM silver.orders
        )),
        date_trunc('month', (
            SELECT MAX(order_purchase_timestamp)
            FROM silver.orders
        )),
        interval '1 month'
    ) AS month_date

),
category_list AS (
SELECT DISTINCT product_category_name 
FROM silver.order_items oi 
),
full_grid AS (
    SELECT
        EXTRACT(YEAR FROM mg.month_date)::INT AS year,
        EXTRACT(MONTH FROM mg.month_date)::INT AS month,
        cl.product_category_name
    FROM month_grid mg
    CROSS JOIN category_list cl
),
demand_agg AS (
    SELECT
        EXTRACT(YEAR FROM o.order_purchase_timestamp)::INT AS year,
        EXTRACT(MONTH FROM o.order_purchase_timestamp)::INT AS month,
        oi.product_category_name,
        COUNT(*) AS demand
    FROM silver.orders o
    JOIN silver.order_items oi
        ON oi.order_id = o.order_id
    GROUP BY
        1,2,3
)
SELECT
    fg.year,
    fg.month,
    fg.product_category_name,
    COALESCE(da.demand, 0) AS demand
FROM full_grid fg
LEFT JOIN demand_agg da
       ON da.year = fg.year
      AND da.month = fg.month
      AND da.product_category_name = fg.product_category_name
ORDER BY
    fg.year,
    fg.month,
    fg.product_category_name
)