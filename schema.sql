-- AWG Data Warehouse Prototype - Star Schema DDL & Aggregation Pipeline

--------------------------------------------------------------------------------
-- 1. Dimension: dim_product
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_product(
    product_key             INTEGER PRIMARY KEY,
    sku                     VARCHAR UNIQUE NOT NULL,
    product_name            VARCHAR NOT NULL,
    category                VARCHAR,
    department              VARCHAR,
    standard_unit_cost      DECIMAL(10, 2)
);

--------------------------------------------------------------------------------
-- 2. Dimension: dim_store
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS dim_store(
    store_key              INTEGER PRIMARY KEY,
    store_id               VARCHAR UNIQUE NOT NULL
);

--------------------------------------------------------------------------------
-- 3. Fact Table: fact_daily_sales
-- Grain: Daily Store-Product Level
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS fact_daily_sales(
    sales_date_key          DATE NOT NULL,
    store_key               INTEGER NOT NULL,
    product_key             INTEGER NOT NULL,
    total_quantity_sold     INTEGER NOT NULL,
    total_revenue           DECIMAL (12, 2) NOT NULL,
    total_margin            DECIMAL (12, 2) NOT NULL,
    PRIMARY KEY (sales_date_key, store_key, product_key),
    FOREIGN KEY (product_key) REFERENCES dim_product(product_key),
    FOREIGN KEY (store_key) REFERENCES dim_store(store_key)
);