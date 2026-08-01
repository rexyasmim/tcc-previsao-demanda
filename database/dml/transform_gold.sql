DROP TABLE IF EXISTS gold.monthly_category_sales;

CREATE TABLE gold.monthly_category_sales AS
SELECT
    EXTRACT(YEAR FROM o.order_purchase_timestamp)::INT AS year,
    EXTRACT(MONTH FROM o.order_purchase_timestamp)::INT AS month,
    oi.product_category_name,
    COUNT(*) AS demand
FROM silver.orders o
JOIN silver.order_items oi ON oi.order_id = o.order_id
GROUP BY
    EXTRACT(YEAR FROM o.order_purchase_timestamp),
    EXTRACT(MONTH FROM o.order_purchase_timestamp),
    oi.product_category_name
ORDER BY
    year,
    month,
    product_category_name;