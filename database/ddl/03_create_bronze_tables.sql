/*
==============================================================================
Projeto   : Previsão de Demanda no Varejo
Autor     : Yasmim Fernandes
Arquivo   : 03_create_bronze_tables.sql
Objetivo  : Criação das tabelas da camada Bronze da Arquitetura Medalhão.
Descrição : As tabelas desta camada armazenam os dados em seu estado original,
            preservando a estrutura do dataset Olist para posterior tratamento
            nas camadas Silver e Gold.
==============================================================================
*/

CREATE TABLE bronze.orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    order_status TEXT NOT NULL,
    order_purchase_timestamp TIMESTAMP NOT NULL,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP NOT NULL
);


CREATE TABLE bronze.order_items (
    order_id TEXT NOT NULL, --Pode ser uma fk
    order_item_id INT NOT NULL,
    product_id TEXT NOT NULL, --pode ser uma fk
    seller_id TEXT NOT NULL, --pode ser uma fk
    shipping_limit_date TIMESTAMP NOT NULL,
    price NUMERIC(10,2) NOT NULL,
    freight_value NUMERIC(10,2) NOT NULL,

    PRIMARY KEY (order_id, order_item_id)
);


CREATE TABLE bronze.products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_name_lenght INT,
    product_description_lenght INT,
    product_photos_qty INT,
    product_weight_g  NUMERIC,
    product_length_cm NUMERIC,
    product_height_cm NUMERIC,
    product_width_cm NUMERIC
);


CREATE TABLE bronze.product_category_name_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);
