# AWG_CASE_STUDY
Lightweight prototype ETL pipeline that ingests raw transactional data, transforms it into a structured dimensional model, and loads it into a target analytics database.

# AWG Data Engineering Case Study: Store Sales & Analytics Pipeline

## Overview
This repository contains a lightweight, production-grade prototype ETL pipeline designed to ingest, cleanse, transform, and model store sales and product catalog data for Associated Wholesale Grocers (AWG). 

The pipeline transforms landing-zone CSV files into a structured **Star Schema** optimized for downstream Business Intelligence and analytics tools like Power BI.

---

## Technical Stack & Architecture
- **Language:** Python 3.11+ (Pandas, PyArrow)
- **Storage & Modeling:** Local DuckDB, Apache Parquet
- **Target Data Architecture:** Medallion Architecture (Bronze $\rightarrow$ Silver $\rightarrow$ Gold)

---

## Pipeline Walkthrough

### 1. Ingestion & Data Quality (Silver Layer)
`etl_pipeline.py` executes the following ELT transformations:
- **Null & Missing Handling:** Filters out transactions lacking critical primary/foreign keys (`sku`, `store_id`).
- **Data Validation:** Strips out invalid transactions with non-positive quantities ($quantity \le 0$).
- **Timestamp Standardization:** Standardizes mixed datetime string formats into standard ISO timestamps.
- **Metric Calculations:**
  $$\text{Total Sales Amount} = \text{Quantity} \times \text{Unit Price}$$
  $$\text{Estimated Margin} = \text{Total Sales Amount} - (\text{Quantity} \times \text{Standard Unit Cost})$$

### 2. Dimensional Modeling (Gold Layer)
`load_star_schema.py` and `schema.sql` model the cleaned data into a classic Star Schema:
- **`dim_product`**: Unique dimension table for product attributes.
- **`dim_store`**: Unique dimension table for store locations.
- **`fact_daily_sales`**: Fact table aggregated at the **Daily Store-Product** grain (`sales_date_key`, `store_key`, `product_key`). Metrics include `total_quantity_sold`, `total_revenue`, and `total_margin`.

---

## Local Setup & Instructions

### 1. Prerequisites
Ensure you have Python installed and create a virtual environment:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate