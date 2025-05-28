"""
Silver Layer ETL: Food Security Index (IKP) Data Cleaning Script

This script processes IKP data from the bronze layer, performs cleaning
and validation, and writes the cleaned data to the silver layer with proper
partitioning using functional programming approach.
"""

import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pyspark.sql.functions import col, when, trim, split, regexp_extract
from pyspark.sql.types import DoubleType, IntegerType

from config.settings import FILE_CONFIG, HDFS_CONFIG, HIVE_CONFIG
from utils.data_quality import clean_invalid_markers, standardize_region_names
from utils.spark_utils import (
    SparkSessionManager,
    clean_text_column,
    create_hive_table,
    read_csv_with_file_config,
    validate_data_quality,
    write_parquet_to_hdfs,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def load_bronze_data(spark):
    """Load IKP data from bronze layer"""
    logger.info("Loading IKP data from bronze layer")
    
    input_path = f"{str(HDFS_CONFIG['data_paths']['bronze'])}/ikp.csv"
    filename = "ikp.csv"
    
    df = read_csv_with_file_config(
        spark,
        input_path,
        filename,
        header=bool(FILE_CONFIG["header"]),
        infer_schema=False,  # We'll handle schema ourselves
    )

    logger.info(f"Loaded {df.count()} rows from bronze layer")
    return df


def validate_input_data(df):
    """Validate input data quality"""
    logger.info("Validating input data quality")

    # Log available columns for debugging
    logger.info(f"Available columns: {df.columns}")
    
    # Show sample data for debugging
    logger.info("Sample raw data:")
    df.show(5, truncate=False)

    expected_columns = ["kabupaten_kota", "Tahun", "IKP", "kategori_ikp"]
    missing_columns = set(expected_columns) - set(df.columns)
    
    if missing_columns:
        logger.error(f"Missing expected columns: {missing_columns}")
        logger.error(f"Available columns: {df.columns}")
        return False

    logger.info("Input data structure validation passed")
    return True


def handle_malformed_ikp_data(df):
    """Handle malformed IKP CSV data where entire row data is in single column"""
    logger.info("Handling malformed IKP CSV data")
    
    # Check if we have the malformed single-column format
    single_col_name = df.columns[0]
    if ";" in single_col_name:
        logger.info(f"Detected malformed IKP data in single column: {single_col_name}")
        
        # Parse the malformed data by splitting on semicolons
        # Format: "97;18;Lampung;Lampung Barat;1804;Kabupaten;2018;77.43;110;6"
        df_fixed = (df
                   .withColumn("parts", split(col(single_col_name), ";"))
                   .withColumn("kabupaten_kota", col("parts")[3])  # Nama Kabupaten
                   .withColumn("tahun", col("parts")[6])           # Tahun
                   .withColumn("skor_ikp", col("parts")[7])        # IKP
                   .withColumn("kategori_ikp", col("parts")[9])    # KELOMPOK IKP
                   .select("kabupaten_kota", "tahun", "skor_ikp", "kategori_ikp"))
        
        logger.info(f"Successfully parsed {df_fixed.count()} IKP records from malformed data")
        logger.info("Sample parsed IKP data:")
        df_fixed.show(5, truncate=False)
        
        return df_fixed
    
    # If not malformed, proceed with normal column handling
    return (df
            .withColumnRenamed("Tahun", "tahun")
            .withColumnRenamed("IKP", "skor_ikp")
            .select("kabupaten_kota", "tahun", "skor_ikp", "kategori_ikp"))


def clean_numeric_columns(df):
    """Clean and convert numeric columns"""
    return (df
            .withColumn("tahun", col("tahun").cast(IntegerType()))
            .withColumn("skor_ikp", col("skor_ikp").cast(DoubleType()))
            .withColumn("kategori_ikp", col("kategori_ikp").cast(IntegerType())))


def filter_valid_records(df):
    """Filter out invalid records"""
    return df.filter(
        col("tahun").isNotNull()
        & col("kabupaten_kota").isNotNull()
        & col("skor_ikp").isNotNull()
        & col("kategori_ikp").isNotNull()
        & (col("skor_ikp") >= 0)
        & (col("skor_ikp") <= 100)
        & (col("kategori_ikp") >= 1)
        & (col("kategori_ikp") <= 6)
        & (col("tahun") >= 2000) 
        & (col("tahun") <= 2030)
        & (trim(col("kabupaten_kota")) != "")
    )


def clean_and_transform(df):
    """Apply cleaning and transformation rules using function composition"""
    logger.info("Starting data cleaning and transformation")

    # Function composition pipeline
    df_cleaned = (df
                  .transform(handle_malformed_ikp_data)
                  .transform(clean_invalid_markers)
                  .transform(clean_numeric_columns)
                  .transform(lambda df: standardize_region_names(df, "kabupaten_kota"))
                  .transform(lambda df: clean_text_column(df, "kabupaten_kota"))
                  .transform(filter_valid_records)
                  .dropDuplicates()
                  .select("kabupaten_kota", "skor_ikp", "kategori_ikp", "tahun"))

    logger.info(f"Cleaning completed. Rows after cleaning: {df_cleaned.count()}")
    
    # Show sample cleaned data for debugging
    if df_cleaned.count() > 0:
        logger.info("Sample cleaned data:")
        df_cleaned.show(5, truncate=False)
    
    return df_cleaned


def validate_output_data(df):
    """Validate cleaned data quality"""
    logger.info("Validating cleaned data quality")

    required_columns = ["kabupaten_kota", "skor_ikp", "kategori_ikp", "tahun"]
    validation_passed = validate_data_quality(df, required_columns, min_rows=50)

    if not validation_passed:
        raise ValueError("Output data validation failed")

    # Log data quality metrics
    low_ikp = df.filter(col("skor_ikp") < 60).count()
    high_ikp = df.filter(col("skor_ikp") > 80).count()
    
    logger.info(f"Records with IKP < 60 (low food security): {low_ikp}")
    logger.info(f"Records with IKP > 80 (high food security): {high_ikp}")

    # Check category distribution
    for category in range(1, 7):
        cat_count = df.filter(col("kategori_ikp") == category).count()
        logger.info(f"Category {category} records: {cat_count}")

    logger.info("Output data validation passed")
    return True


def save_to_silver(spark, df):
    """Save cleaned data to silver layer"""
    output_path = f"{str(HDFS_CONFIG['data_paths']['silver'])}/ikp"
    database = str(HIVE_CONFIG["databases"]["silver"])
    table_name = "ikp"
    
    logger.info(f"Saving cleaned data to silver layer: {output_path}")

    # Write parquet files partitioned by year
    write_parquet_to_hdfs(
        df,
        output_path,
        partition_by=str(FILE_CONFIG["partition_column"]),
        mode=str(FILE_CONFIG["write_mode"]),
    )

    # Define table schema
    columns = {
        "kabupaten_kota": "STRING",
        "skor_ikp": "DOUBLE",
        "kategori_ikp": "INT",
    }

    partition_columns = {"tahun": "INT"}

    # Create Hive table
    create_hive_table(
        spark,
        database,
        table_name,
        columns,
        partition_columns,
        output_path,
        "PARQUET",
    )

    logger.info(f"Successfully created Hive table: {database}.{table_name}")


def run_pipeline():
    """Execute the complete cleaning pipeline using functional composition"""
    spark = None
    try:
        logger.info("Starting IKP data cleaning pipeline")

        # Initialize Spark session
        spark = SparkSessionManager.get_session("CleanIKPData")

        # Execute pipeline
        df_bronze = load_bronze_data(spark)
        validate_input_data(df_bronze)
        df_silver = clean_and_transform(df_bronze)
        validate_output_data(df_silver)
        save_to_silver(spark, df_silver)

        logger.info("IKP data cleaning pipeline completed successfully")

        # Print summary statistics
        input_count = df_bronze.count()
        output_count = df_silver.count()
        reduction_pct = (input_count - output_count) / input_count * 100

        logger.info("Pipeline Summary:")
        logger.info(f"- Input rows: {input_count}")
        logger.info(f"- Output rows: {output_count}")
        logger.info(f"- Data reduction: {reduction_pct:.2f}%")

    except Exception as e:
        logger.error(f"Pipeline failed: {str(e)}")
        raise
    finally:
        if spark:
            SparkSessionManager.stop_session()


def main():
    """Main entry point"""
    run_pipeline()


if __name__ == "__main__":
    main()