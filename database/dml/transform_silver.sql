DROP TABLE IF EXISTS silver.orders;

CREATE TABLE silver.orders AS
SELECT
    order_id,
    customer_id,
    order_status,
    order_purchase_timestamp,
    order_approved_at,
    order_delivered_carrier_date,
    order_delivered_customer_date,
    order_estimated_delivery_date
FROM bronze.orders
WHERE order_status = 'delivered';



DROP TABLE IF EXISTS silver.order_items;

CREATE TABLE silver.order_items AS 
SELECT oi.order_id,
       order_item_id,
       p.product_id,
       seller_id,
       shipping_limit_date,
       price,
       freight_value,
       COALESCE(p.product_category_name,'categoria_desconhecida') AS product_category_name,
       COALESCE(t.product_category_name_english,'unknown') AS product_category_name_english
FROM bronze.order_items oi 
JOIN silver.orders o ON o.order_id = oi.order_id
LEFT JOIN bronze.products p ON oi.product_id = p.product_id
LEFT JOIN bronze.product_category_name_translation t ON t.product_category_name = p.product_category_name;
