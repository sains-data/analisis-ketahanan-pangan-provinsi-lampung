"""
Silver Layer ETL: Price Data Cleaning Script

This script processes price data from the bronze layer, performs cleaning
and validation, and writes the cleaned data to the silver layer with proper
partitioning using functional programming approach.
"""

import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pyspark.sql.functions import col, when, regexp_replace, year, lit, split, size, trim, regexp_extract
from pyspark.sql.types import DoubleType, StringType

from config.settings import FILE_CONFIG, HDFS_CONFIG, HIVE_CONFIG
from utils.data_quality import clean_invalid_markers
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
    """Load price data from bronze layer"""
    logger.info("Loading price data from bronze layer")
    
    input_path = f"{str(HDFS_CONFIG['data_paths']['bronze'])}/harga_pangan.csv"
    filename = "harga_pangan.csv"
    
    df = read_csv_with_file_config(
        spark,
        input_path,
        filename,
        header=bool(FILE_CONFIG["header"]),
        infer_schema=False,  # We'll handle schema ourselves due to complex data
    )

    logger.info(f"Loaded {df.count()} rows from bronze layer")
    return df


def validate_input_data(df):
    """Validate input data quality"""
    logger.info("Validating input data quality")

    # Log available columns for debugging
    logger.info(f"Available columns: {df.columns}")
    
    # Check for corrupted records column (from PERMISSIVE mode)
    if "_corrupt_record" in df.columns:
        corrupt_count = df.filter(col("_corrupt_record").isNotNull()).count()
        logger.info(f"Found {corrupt_count} corrupted records")
        
        # Show sample corrupted records for debugging
        if corrupt_count > 0:
            logger.info("Sample corrupted records:")
            df.filter(col("_corrupt_record").isNotNull()).select("_corrupt_record").show(5, truncate=False)

    # Basic validation - check that we have the expected columns
    # Note: column mapping should have already converted "harga pangan" to "harga_pangan"
    expected_columns = ["komoditas", "tanggal", "harga_pangan"]
    missing_columns = set(expected_columns) - set(df.columns)
    
    if missing_columns:
        logger.error(f"Missing expected columns: {missing_columns}")
        logger.error(f"Available columns: {df.columns}")
        return False

    logger.info("Input data structure validation passed")
    return True


def clean_price_column(df):
    """Clean and parse price column with quoted numbers and commas"""
    return (df
            .withColumn("harga_pangan", regexp_replace(col("harga_pangan"), '"', ""))
            .withColumn("harga_pangan", regexp_replace(col("harga_pangan"), ",", ""))
            .withColumn("harga_pangan", trim(col("harga_pangan")))
            .withColumn("harga_pangan", 
                       when(col("harga_pangan") == "-", None)
                       .when(col("harga_pangan") == "", None)
                       .otherwise(col("harga_pangan")))
            .withColumn("harga_pangan", col("harga_pangan").cast(DoubleType())))


def extract_year_from_date(df):
    """Extract year from date column in DD/MM/YYYY format"""
    return df.withColumn(
        "tahun",
        year(
            when(
                col("tanggal").rlike(r"\d{2}/\d{2}/\d{4}"),
                regexp_replace(col("tanggal"), r"(\d{2})/(\d{2})/(\d{4})", "$3-$2-$1")
            ).otherwise(None).cast("date")
        )
    )


def add_missing_schema_columns(df):
    """Add missing columns to match expected schema"""
    return (df
            .withColumn("kabupaten_kota", lit("Lampung"))  # Province-wide data
            .withColumn("harga_produsen", col("harga_pangan"))
            .withColumn("harga_konsumen", col("harga_pangan")))


def filter_valid_records(df):
    """Filter out invalid records"""
    return df.filter(
        col("harga_pangan").isNotNull()
        & (col("harga_pangan") > 0)
        & col("tahun").isNotNull()
        & col("komoditas").isNotNull()
        & (col("tahun") >= 2000) 
        & (col("tahun") <= 2030)
        & (col("harga_pangan") <= 1000000000)  # Max 1B rupiah
    )


def handle_malformed_data(df):
    """Handle malformed CSV data where entire row data is in komoditas column"""
    logger.info("Checking for malformed data patterns")
    
    # Identify malformed rows - these have commas in komoditas and null values in other columns
    malformed_rows = df.filter(col("komoditas").contains(",") & col("tanggal").isNull())
    normal_rows = df.filter(col("tanggal").isNotNull())
    
    malformed_count = malformed_rows.count()
    normal_count = normal_rows.count()
    
    logger.info(f"Found {malformed_count} malformed rows and {normal_count} normal rows")
    
    if malformed_count > 0:
        # Simple parsing: Extract komoditas, tanggal, and price from malformed rows
        # Format: "Beras,02/01/2018,"12,000""
        fixed_rows = (malformed_rows
                     .withColumn("original_data", col("komoditas"))
                     .withColumn("komoditas", regexp_extract(col("original_data"), '^([^,]+)', 1))
                     .withColumn("tanggal", regexp_extract(col("original_data"), ',([0-9/]+),', 1))
                     .withColumn("harga_pangan", regexp_extract(col("original_data"), ',"([0-9,]+)"', 1))
                     .filter(col("komoditas") != "")
                     .select("komoditas", "tanggal", "harga_pangan"))
        
        fixed_count = fixed_rows.count()
        logger.info(f"Successfully parsed {fixed_count} malformed rows")
        
        if fixed_count > 0:
            logger.info("Sample fixed rows:")
            fixed_rows.show(5, truncate=False)
        
        # Union normal and fixed rows
        return normal_rows.union(fixed_rows)
    
    return df


def clean_and_transform(df):
    """Apply cleaning and transformation rules using function composition"""
    logger.info("Starting data cleaning and transformation")

    # Show sample data for debugging
    logger.info("Sample raw data:")
    df.show(5, truncate=False)

    # Function composition pipeline with persistence to avoid code generation issues
    # Note: Column mapping should have already handled "harga pangan" -> "harga_pangan"
    df_step1 = (df
                .transform(handle_malformed_data)
                .transform(clean_invalid_markers)
                .transform(clean_price_column))
    
    # Persist after major transformation to break execution plan
    df_step1.persist()
    logger.info(f"After parsing and price cleaning: {df_step1.count()} rows")
    
    df_cleaned = (df_step1
                  .withColumn("tanggal", col("tanggal").cast(StringType()))
                  .transform(extract_year_from_date)
                  .transform(add_missing_schema_columns)
                  .transform(lambda df: clean_text_column(df, "komoditas"))
                  .transform(lambda df: clean_text_column(df, "kabupaten_kota"))
                  .transform(filter_valid_records)
                  .dropDuplicates()
                  .select("kabupaten_kota", "komoditas", "harga_produsen", 
                         "harga_konsumen", "tahun", "tanggal"))

    # Persist final result and unpersist intermediate
    df_cleaned.persist()
    df_step1.unpersist()

    logger.info(f"Cleaning completed. Rows after cleaning: {df_cleaned.count()}")
    
    # Show sample cleaned data for debugging
    if df_cleaned.count() > 0:
        logger.info("Sample cleaned data:")
        df_cleaned.show(5, truncate=False)
    
    return df_cleaned


def validate_output_data(df):
    """Validate cleaned data quality"""
    logger.info("Validating cleaned data quality")

    required_columns = ["kabupaten_kota", "komoditas", "harga_produsen", "tahun"]
    validation_passed = validate_data_quality(df, required_columns, min_rows=100)

    if not validation_passed:
        raise ValueError("Output data validation failed")

    # Log data quality metrics
    zero_prices = df.filter(
        (col("harga_produsen") <= 0) | (col("harga_konsumen") <= 0)
    ).count()

    if zero_prices > 0:
        logger.warning(f"Found {zero_prices} records with zero or negative prices")

    high_prices = df.filter(col("harga_produsen") > 500000).count()
    if high_prices > 0:
        logger.info(f"Found {high_prices} records with prices above 500,000")

    logger.info("Output data validation passed")
    return True


def save_to_silver(spark, df):
    """Save cleaned data to silver layer"""
    output_path = f"{str(HDFS_CONFIG['data_paths']['silver'])}/harga_pangan"
    database = str(HIVE_CONFIG["databases"]["silver"])
    table_name = "harga_pangan"
    
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
        "komoditas": "STRING",
        "harga_produsen": "DOUBLE",
        "harga_konsumen": "DOUBLE",
        "tanggal": "STRING",
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
        logger.info("Starting price data cleaning pipeline")

        # Initialize Spark session with code generation disabled
        spark = SparkSessionManager.get_session("CleanHargaData")
        spark.conf.set("spark.sql.codegen.wholeStage", "false")
        spark.conf.set("spark.sql.codegen.factoryMode", "NO_CODEGEN")

        # Execute pipeline
        df_bronze = load_bronze_data(spark)
        validate_input_data(df_bronze)
        df_silver = clean_and_transform(df_bronze)
        validate_output_data(df_silver)
        save_to_silver(spark, df_silver)

        logger.info("Price data cleaning pipeline completed successfully")

        # Print summary statistics
        input_count = df_bronze.count()
        output_count = df_silver.count()
        reduction_pct = (input_count - output_count) / input_count * 100

        logger.info("Pipeline Summary:")
        logger.info(f"- Input rows: {input_count}")
        logger.info(f"- Output rows: {output_count}")
        logger.info(f"- Data reduction: {reduction_pct:.2f}%")

        # Clean up
        df_silver.unpersist()

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