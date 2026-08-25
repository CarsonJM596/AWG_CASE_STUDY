import logging
import os
import duckdb
import pandas as pd 

# Original set up for logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

def load_and_clean_product_catalog(filepath: str) -> pd.DataFrame:
    # Ingests and cleans the raw product catalog dataset 
    logging.info(f"Loading product catalog from {filepath}...")
    df = pd.read_csv(filepath)

    # 1. Clean column whitespace & string values
    df.columns = df.columns.str.strip().str.lower()
    for col in ["sku", "product_name", "category", "department"]:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip()

    # 2. Drop records missing critical PK (SKU)
    df = df.dropna(subset=["sku"])
    df = df[df["sku"] != ""]

    # 3. Handle numeric contraints 
    df["standard_unit_cost"] = pd.to_numeric(
        df["standard_unit_cost"], errors="coerce"
    ).fillna(0.0)

    logging.info(
        f"Product catalog sucessfully processed, "
    )
    return df

def load_and_clean_store_sales(filepath:str) -> pd.DataFrame:
    #Ingests and cleans the raw store sales dataset, handling date parsing
    logging.info(f"Loading store sales from {filepath}...")
    df = pd.read_csv(filepath)

    df.columns = df.columns.str.strip().str.lower()

    # 1. Drop records missing critical identifiers 
    initial_count = len(df)
    df = df.dropna(subset=["sku", "transaction_id", "store_id"])
    df= df[df["sku"].astype(str).str.strip() != ""]

    # 2. Clean invalid quantities (negative or returns errors)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce")
    df = df[df["quantity"] > 0]

    # 3. Standardize timestamps (handles mixed date formats)
    df["transaction_timestamp"] = pd.to_datetime(
        df["transaction_timestamp"], format="mixed", errors="coerce"
    )
    df = df.dropna(subset=["transaction_timestamp"])

    dropped_records = initial_count - len(df)
    logging.info(
        f"Store sales processed. Retained {len(df)} valid records (dropped {dropped_records} invalid/missing rows)."
    )
    return df

def transform_sales_data(
        df_sales: pd.DataFrame, df_catalog: pd.DataFrame
) -> pd.DataFrame:
    # Merges sales with catalog attributes, calculates total sales amount & estimated margin
    logging.info("Transforming sales data and calculating derived metrics...")

    # Left join to enrich sales records with product catalog cost data 
    merged_df = pd.merge(
        df_sales,
        df_catalog[["sku", "standard_unit_cost"]],
        on="sku",
        how="left",
    )
    merged_df["standard_unit_cost"] = merged_df["standard_unit_cost"].fillna(0.0)

    # Calculate derived financial metrics
    merged_df["total_sales_amount"] = (
        merged_df["quantity"] * merged_df["unit_price"]).round(2)
    merged_df["estimated_margin"] = (
        merged_df["total_sales_amount"]
        - (merged_df["quantity"]) * merged_df["standard_unit_cost"]).round(2)

    logging.info("Transformation complete")
    return merged_df

def export_data(
      df_transformed: pd.DataFrame, parquet_path: str, duckdb_path: str  
):
    # Exports transformed data to Parquet format and loads it into a local DuckDB table
    logging.info(f"Saving transformed data to parquet at {parquet_path}")
    df_transformed.to_parquet(parquet_path, index=False)

    logging.info(f"Loading transformed dataset into DuckDB database at {duckdb_path}...")
    con = duckdb.connect(duckdb_path)

    # Register pandas dataframe and write to DuckDB table
    con.register("df_transformed", df_transformed)
    con.execute(
        "CREATE OR REPLACE TABLE stg_sales AS SELECT * FROM df_transformed"
    )
    con.close()
    logging.info("Data export completed")

    

data_dir = "data"
catalog_path = os.path.join(data_dir, "raw_product_catalog.csv")
sales_path = os.path.join(data_dir, "raw_store_sales.csv")
parquet_output = os.path.join(data_dir, "processed_sales.parquet")
duckdb_output = os.path.join(data_dir, "awg_analytics.duckdb")

df_catalog = load_and_clean_product_catalog(catalog_path)
df_sales = load_and_clean_store_sales(sales_path)

df_transformed = transform_sales_data(df_sales, df_catalog)

export_data(df_transformed, parquet_output, duckdb_output)

print("\n--- Transformed Dataset Sample ---")
print(
    df_transformed[
        [
            "transaction_id",
            "store_id",
            "sku",
            "quantity",
            "unit_price",
            "total_sales_amount",
            "estimated_margin",
        ]
    ]
)