"""
Silver Layer ETL: Food Consumption Data Cleaning Script

This script processes food consumption data from the bronze layer, performs cleaning
and validation, and writes the cleaned data to the silver layer with proper
partitioning using functional programming approach.
"""

import logging
import sys
from pathlib import Path

# Add src to Python path
sys.path.append(str(Path(__file__).parent.parent.parent))

from pyspark.sql.functions import col, regexp_replace, trim
from pyspark.sql.types import DoubleType, IntegerType

from config.settings import FILE_CONFIG, HDFS_CONFIG, HIVE_CONFIG
from utils.data_quality import clean_invalid_markers, standardize_region_names
from utils.spark_utils import (
    SparkSessionManager,
    clean_text_column,
    create_hive_table,
    read_csv_from_hdfs,
    validate_data_quality,
    write_parquet_to_hdfs,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger(__name__)


def load_bronze_data(spark):
    """Load food consumption data from bronze layer"""
    logger.info("Loading food consumption data from bronze layer")
    
    input_path = f"{str(HDFS_CONFIG['data_paths']['bronze'])}/konsumsi_pangan.csv"
    
    df = read_csv_from_hdfs(
        spark,
        input_path,
        separator=";",  # konsumsi_pangan.csv uses semicolon separator
        header=bool(FILE_CONFIG["header"]),
        infer_schema=False,  # We'll handle schema ourselves
    )

    logger.info(f"Loaded {df.count()} rows from bronze layer")
    return df


def validate_input_data(df):
    """Validate input data quality"""
    logger.info("Validating input data quality")

    expected_columns = ["Tahun", "Kabupaten_Kota", "Komoditas", "Konsumsi Pangan"]
    missing_columns = set(expected_columns) - set(df.columns)
    
    if missing_columns:
        logger.error(f"Missing expected columns: {missing_columns}")
        return False

    logger.info("Input data structure validation passed")
    return True


def normalize_column_names(df):
    """Normalize column names to match expected schema"""
    return (df
            .withColumnRenamed("Tahun", "tahun")
            .withColumnRenamed("Kabupaten_Kota", "kabupaten_kota")
            .withColumnRenamed("Komoditas", "komoditas")
            .withColumnRenamed("Konsumsi Pangan", "konsumsi_per_kapita"))


def fix_decimal_commas(df):
    """Convert decimal commas to decimal points"""
    return df.withColumn(
        "konsumsi_per_kapita",
        regexp_replace(col("konsumsi_per_kapita"), ",", ".")
    )


def clean_numeric_columns(df):
    """Clean and convert numeric columns"""
    return (df
            .withColumn("tahun", col("tahun").cast(IntegerType()))
            .withColumn("konsumsi_per_kapita", col("konsumsi_per_kapita").cast(DoubleType())))


def filter_valid_records(df):
    """Filter out invalid records"""
    return df.filter(
        col("tahun").isNotNull()
        & col("kabupaten_kota").isNotNull()
        & col("komoditas").isNotNull()
        & col("konsumsi_per_kapita").isNotNull()
        & (col("konsumsi_per_kapita") >= 0)
        & (col("tahun") >= 2000) 
        & (col("tahun") <= 2030)
        & (trim(col("kabupaten_kota")) != "")
        & (trim(col("komoditas")) != "")
    )


def clean_and_transform(df):
    """Apply cleaning and transformation rules using function composition"""
    logger.info("Starting data cleaning and transformation")

    # Function composition pipeline
    df_cleaned = (df
                  .transform(normalize_column_names)
                  .transform(clean_invalid_markers)
                  .transform(fix_decimal_commas)
                  .transform(clean_numeric_columns)
                  .transform(lambda df: standardize_region_names(df, "kabupaten_kota"))
                  .transform(lambda df: clean_text_column(df, "kabupaten_kota"))
                  .transform(lambda df: clean_text_column(df, "komoditas"))
                  .transform(filter_valid_records)
                  .dropDuplicates()
                  .select("kabupaten_kota", "komoditas", "konsumsi_per_kapita", "tahun"))

    logger.info(f"Cleaning completed. Rows after cleaning: {df_cleaned.count()}")
    return df_cleaned


def validate_output_data(df):
    """Validate cleaned data quality"""
    logger.info("Validating cleaned data quality")

    required_columns = ["kabupaten_kota", "komoditas", "konsumsi_per_kapita", "tahun"]
    validation_passed = validate_data_quality(df, required_columns, min_rows=50)

    if not validation_passed:
        raise ValueError("Output data validation failed")

    # Log data quality metrics
    zero_consumption = df.filter(col("konsumsi_per_kapita") == 0).count()
    high_consumption = df.filter(col("konsumsi_per_kapita") > 500).count()
    
    logger.info(f"Records with zero consumption: {zero_consumption}")
    logger.info(f"Records with consumption > 500 kg/capita/year: {high_consumption}")

    # Check for extreme values
    extreme_consumption = df.filter(col("konsumsi_per_kapita") > 1000).count()
    if extreme_consumption > 0:
        logger.warning(f"Found {extreme_consumption} records with extremely high consumption > 1000")

    logger.info("Output data validation passed")
    return True


def save_to_silver(spark, df):
    """Save cleaned data to silver layer"""
    output_path = f"{str(HDFS_CONFIG['data_paths']['silver'])}/konsumsi_pangan"
    database = str(HIVE_CONFIG["databases"]["silver"])
    table_name = "konsumsi_pangan"
    
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
        "konsumsi_per_kapita": "DOUBLE",
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
        logger.info("Starting food consumption data cleaning pipeline")

        # Initialize Spark session
        spark = SparkSessionManager.get_session("CleanKonsumsiPanganData")

        # Execute pipeline
        df_bronze = load_bronze_data(spark)
        validate_input_data(df_bronze)
        df_silver = clean_and_transform(df_bronze)
        validate_output_data(df_silver)
        save_to_silver(spark, df_silver)

        logger.info("Food consumption data cleaning pipeline completed successfully")

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