import logging
import os
import duckdb

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


def build_star_schema(db_path: str, schema_file: str):
    conn = duckdb.connect(db_path)

    # 1. Execute DDL from schema.sql
    logging.info("Executing DDL statements from schema.sql...")
    with open(schema_file, "r") as f:
        sql_script = f.read()
    conn.execute(sql_script)

    # Clear existing tables to ensure clean reload
    conn.execute("TRUNCATE TABLE fact_daily_sales;")
    conn.execute("TRUNCATE TABLE dim_product;")
    conn.execute("TRUNCATE TABLE dim_store;")

    # 2. Populate dim_product
    logging.info("Populating dim_product...")
    catalog_path = os.path.join("data", "raw_product_catalog.csv")
    conn.execute(f"""
        INSERT INTO dim_product (product_key, sku, product_name, category, department, standard_unit_cost)
        SELECT 
            ROW_NUMBER() OVER (ORDER BY sku) AS product_key,
            TRIM(sku) AS sku,
            TRIM(product_name) AS product_name,
            TRIM(category) AS category,
            TRIM(department) AS department,
            CAST(standard_unit_cost AS DECIMAL(10,2)) AS standard_unit_cost
        FROM read_csv_auto('{catalog_path}')
        WHERE sku IS NOT NULL AND TRIM(sku) != '';
    """)

    # 3. Populate dim_store
    logging.info("Populating dim_store...")
    conn.execute("""
        INSERT INTO dim_store (store_key, store_id)
        SELECT 
            ROW_NUMBER() OVER (ORDER BY store_id) AS store_key,
            store_id
        FROM (SELECT DISTINCT store_id FROM stg_sales);
    """)

    # 4. Populate fact_daily_sales (Daily Store-Product Aggregation)
    logging.info(
        "Populating fact_daily_sales aggregated at Daily Store-Product grain..."
    )
    conn.execute("""
        INSERT INTO fact_daily_sales (
            sales_date_key,
            store_key,
            product_key,
            total_quantity_sold,
            total_revenue,
            total_margin
        )
        SELECT 
            CAST(s.transaction_timestamp AS DATE) AS sales_date_key,
            st.store_key,
            p.product_key,
            SUM(s.quantity) AS total_quantity_sold,
            SUM(s.total_sales_amount) AS total_revenue,
            SUM(s.estimated_margin) AS total_margin
        FROM stg_sales s
        JOIN dim_store st ON s.store_id = st.store_id
        JOIN dim_product p ON s.sku = p.sku
        GROUP BY 
            CAST(s.transaction_timestamp AS DATE),
            st.store_key,
            p.product_key;
    """)

    logging.info("Star Schema build complete.")

    print("\n--- Fact Table Preview (fact_daily_sales) ---")
    print(conn.execute("SELECT * FROM fact_daily_sales").fetchdf())

    conn.close()

build_star_schema("data/awg_analytics.duckdb", "schema.sql")